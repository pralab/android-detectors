#!/usr/bin/env python3

import argparse
import ast
from pathlib import Path
import re
from typing import Dict, Optional, Tuple, List, Union


TARGET_METHODS = ["__init__", "train", "load", "save", "classify"]


class StubGenError(Exception):
    pass


# =========================
# I/O + AST helpers
# =========================

import re


def camel_to_snake(s):
    if s.isupper():
        return s.lower()

    # Replace transitions from lowercase to uppercase with underscore
    # but preserve acronyms (e.g., SVM stays together)
    parts = re.findall(r'[A-Z]+(?=[A-Z][a-z]|$)|[A-Z]?[a-z]+', s)
    return '_'.join(part.lower() for part in parts)


def ensure_unparse_available():
    if not hasattr(ast, "unparse"):
        raise StubGenError("Python 3.9+ is required (ast.unparse is unavailable).")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        raise StubGenError(f"Failed to read file '{path}': {e}")


def parse_module(path: Path) -> Tuple[ast.Module, str]:
    src = read_text(path)
    try:
        return ast.parse(src, filename=str(path)), src
    except SyntaxError as e:
        raise StubGenError(f"Failed to parse '{path}': {e}") from e


def collect_classes(mod: ast.Module) -> Dict[str, ast.ClassDef]:
    return {n.name: n for n in mod.body if isinstance(n, ast.ClassDef)}


def find_classdef_deep(node: ast.AST, class_name: str) -> Optional[ast.ClassDef]:
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef) and child.name == class_name:
            return child
        found = find_classdef_deep(child, class_name)
        if found:
            return found
    return None


# =========================
# Import index (static)
# =========================

class ImportIndex:
    """
    Top-level imports for static base resolution:

    - import pkg.mod [as alias]            -> modules_by_alias['alias'] = 'pkg.mod'
    - from pkg.mod import Class [as Alias] -> names_by_alias['Alias']  = ('pkg.mod', 'Class')
    - from pkg import mod                  -> names_by_alias['mod']    = ('pkg', 'mod')  # module-as-name
    """
    def __init__(self) -> None:
        self.modules_by_alias: Dict[str, str] = {}
        self.names_by_alias: Dict[str, Tuple[str, str]] = {}

    def add_import(self, node: ast.Import):
        for a in node.names:
            alias = a.asname or a.name.split(".")[0]
            self.modules_by_alias[alias] = a.name

    def add_from_import(self, node: ast.ImportFrom, module_name: str):
        for a in node.names:
            alias = a.asname or a.name
            self.names_by_alias[alias] = (module_name, a.name)


class ModuleInfo:
    def __init__(self, path: Path, mod_ast: ast.Module, src: str):
        self.path = path
        self.ast = mod_ast
        self.src = src
        self.classes = collect_classes(mod_ast)
        self.imports = ImportIndex()

    def index_imports(self, resolver: "ModuleResolver"):
        for n in self.ast.body:
            if isinstance(n, ast.Import):
                self.imports.add_import(n)
            elif isinstance(n, ast.ImportFrom):
                base_name = resolver.resolve_from_module_name(n, self.path)
                self.imports.add_from_import(n, base_name)


# =========================
# Filesystem-based module resolver
# =========================

class ModuleResolver:
    """
    Resolve module name -> file path WITHOUT importing.

    Roots (in order):
      - any --search-path entries (first wins)
      - input dir
      - its parents up to --max-upward
    """

    def __init__(self, input_file: Path, search_paths: List[Path], max_upward: int = 3):
        roots: List[Path] = []
        roots.extend([Path(p).resolve() for p in search_paths])
        cur = input_file.parent.resolve()
        roots.append(cur)
        for _ in range(max_upward):
            if cur.parent == cur:
                break
            cur = cur.parent
            roots.append(cur)

        self.roots: List[Path] = []
        seen = set()
        for r in roots:
            if r not in seen:
                self.roots.append(r)
                seen.add(r)

    def _package_segments_for_file(self, file_path: Path) -> List[str]:
        segs: List[str] = []
        cur = file_path.parent
        while True:
            init_file = cur / "__init__.py"
            if not init_file.exists():
                break
            segs.insert(0, cur.name)
            if cur.parent == cur:
                break
            cur = cur.parent
        return segs

    def resolve_from_module_name(self, node: ast.ImportFrom, current_file: Path) -> str:
        level = node.level or 0
        tail = node.module or ""
        if level == 0:
            return tail
        pkg_segs = self._package_segments_for_file(current_file)
        base_segs = pkg_segs[:-level] if level <= len(pkg_segs) else []
        if tail:
            base_segs.extend(tail.split("."))
        return ".".join(base_segs)

    def find_module_file(self, module_name: str) -> Optional[Path]:
        parts = module_name.split(".")
        for root in self.roots:
            cand_py = root.joinpath(*parts).with_suffix(".py")
            if cand_py.exists():
                return cand_py
            cand_pkg = root.joinpath(*parts, "__init__.py")
            if cand_pkg.exists():
                return cand_pkg
        return None


class ASTProject:
    def __init__(self, resolver: ModuleResolver):
        self.resolver = resolver
        self.cache: Dict[Path, ModuleInfo] = {}

    def load_module_info_from_file(self, path: Path) -> ModuleInfo:
        path = path.resolve()
        if path in self.cache:
            return self.cache[path]
        mod_ast, src = parse_module(path)
        mi = ModuleInfo(path, mod_ast, src)
        mi.index_imports(self.resolver)
        self.cache[path] = mi
        return mi

    def load_module_info_from_module_name(self, module_name: str) -> ModuleInfo:
        fpath = self.resolver.find_module_file(module_name)
        if not fpath:
            raise StubGenError(
                f"Cannot locate module '{module_name}' on disk. Add its root with --search-path."
            )
        return self.load_module_info_from_file(fpath)


# =========================
# Static base + method resolution
# =========================

def dotted_parts(expr: ast.expr) -> Optional[List[str]]:
    """
    Convert Name/Attribute chain (and Subscript.value thereof) to parts.
    'pkg.mod.Base' -> ['pkg','mod','Base'], 'Base[T]' -> ['Base']
    """
    if isinstance(expr, ast.Subscript):
        expr = expr.value
    parts: List[str] = []
    cur = expr
    while True:
        if isinstance(cur, ast.Name):
            parts.insert(0, cur.id)
            break
        if isinstance(cur, ast.Attribute):
            parts.insert(0, cur.attr)
            cur = cur.value
            continue
        return None
    return parts


def resolve_base_to_class(
    base_expr: ast.expr, cur_mod: ModuleInfo, project: ASTProject
) -> Optional[Tuple[ast.ClassDef, ModuleInfo]]:
    # Name case
    if isinstance(base_expr, ast.Name):
        name = base_expr.id
        if name in cur_mod.classes:
            return cur_mod.classes[name], cur_mod
        if name in cur_mod.imports.names_by_alias:
            mod_name, orig = cur_mod.imports.names_by_alias[name]
            try:
                modinfo = project.load_module_info_from_module_name(mod_name)
                cls = modinfo.classes.get(orig) or find_classdef_deep(modinfo.ast, orig)
                if cls:
                    return cls, modinfo
            except StubGenError:
                pass
        return None

    # Dotted / Subscript
    parts = dotted_parts(base_expr)
    if not parts or len(parts) == 1:
        return None

    first, rest = parts[0], parts[1:]

    # import pkg.mod as alias -> alias.Class
    if first in cur_mod.imports.modules_by_alias:
        mod_name = cur_mod.imports.modules_by_alias[first]
        if len(rest) > 1:
            mod_name = ".".join([mod_name] + rest[:-1])
        class_name = rest[-1]
        modinfo = project.load_module_info_from_module_name(mod_name)
        cls = modinfo.classes.get(class_name) or find_classdef_deep(modinfo.ast, class_name)
        return (cls, modinfo) if cls else None

    # from pkg import mod  -> mod.Class
    if first in cur_mod.imports.names_by_alias:
        base_mod, orig_sym = cur_mod.imports.names_by_alias[first]  # e.g., ('pkg', 'mod')
        mod_name = ".".join([base_mod, orig_sym]) if base_mod else orig_sym
        if len(rest) > 1:
            mod_name = ".".join([mod_name] + rest[:-1])
        class_name = rest[-1]
        modinfo = project.load_module_info_from_module_name(mod_name)
        cls = modinfo.classes.get(class_name) or find_classdef_deep(modinfo.ast, class_name)
        return (cls, modinfo) if cls else None

    # direct absolute path: pkg.mod.Class
    mod_name = ".".join(parts[:-1])
    class_name = parts[-1]
    modinfo = project.load_module_info_from_module_name(mod_name)
    cls = modinfo.classes.get(class_name) or find_classdef_deep(modinfo.ast, class_name)
    return (cls, modinfo) if cls else None


def method_in_class_ast(
    cls_node: ast.ClassDef, name: str
) -> Optional[Union[ast.FunctionDef, ast.AsyncFunctionDef]]:
    for n in cls_node.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    return None


def resolve_method_static_mro(
    cls_node: ast.ClassDef,
    modinfo: ModuleInfo,
    project: ASTProject,
    method: str,
    visited: Optional[set] = None,
) -> Optional[Tuple[Union[ast.FunctionDef, ast.AsyncFunctionDef], ModuleInfo]]:
    if visited is None:
        visited = set()
    key = (modinfo.path, cls_node.name)
    if key in visited:
        return None
    visited.add(key)

    m = method_in_class_ast(cls_node, method)
    if m:
        return m, modinfo

    for b in cls_node.bases:
        resolved = resolve_base_to_class(b, modinfo, project)
        if not resolved:
            continue
        b_cls, b_mod = resolved
        found = resolve_method_static_mro(b_cls, b_mod, project, method, visited)
        if found:
            return found

    return None


# =========================
# Code generation
# =========================

def decorators_lines(func: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> List[str]:
    if not func.decorator_list:
        return []
    return [f"@{ast.unparse(d)}" for d in func.decorator_list]


def decorator_kind(func: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> str:
    """
    'staticmethod' | 'classmethod' | 'instance'
    """
    def token(d: ast.AST) -> Optional[str]:
        if isinstance(d, ast.Name): return d.id
        if isinstance(d, ast.Attribute): return d.attr
        if isinstance(d, ast.Call):
            f = d.func
            if isinstance(f, ast.Name): return f.id
            if isinstance(f, ast.Attribute): return f.attr
        return None

    kind = "instance"
    for d in func.decorator_list:
        t = token(d)
        if t == "staticmethod":
            return "staticmethod"
        if t == "classmethod":
            kind = "classmethod"
    return kind


def function_header(func: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Tuple[str, bool]:
    """
    Build a well-formed header line with guaranteed parentheses in the parameter list.
    """
    is_async = isinstance(func, ast.AsyncFunctionDef)
    args_text = ast.unparse(func.args)  # includes parentheses in Py3.9+, but enforce just in case
    s = args_text.strip()
    if not (s.startswith("(") and s.endswith(")")):
        args_text = f"({s})"
    ret_ann = f" -> {ast.unparse(func.returns)}" if func.returns else ""
    head = f"{'async ' if is_async else ''}def {func.name}{args_text}{ret_ann}:"
    return head, is_async


def iter_positional_names(args: ast.arguments) -> List[str]:
    names: List[str] = []
    names.extend([a.arg for a in args.posonlyargs])
    names.extend([a.arg for a in args.args])
    return names


def delegate_call_args(args: ast.arguments, omit_first: bool) -> str:
    pos = iter_positional_names(args)
    if omit_first and pos:
        pos = pos[1:]

    parts: List[str] = []
    parts.extend(pos)

    if args.vararg is not None:
        parts.append(f"*{args.vararg.arg}")

    for a in args.kwonlyargs:
        parts.append(f"{a.arg}={a.arg}")

    if args.kwarg is not None:
        parts.append(f"**{args.kwarg.arg}")

    return ", ".join(parts)


def docstring_literal_from_node(node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef], module_source: str) -> Optional[str]:
    """
    Return the exact docstring literal when the first statement is a string literal.
    Preserves original quote style/prefix (via ast.get_source_segment), else safe fallback.
    IMPORTANT: We return a SINGLE token string containing the whole triple-quoted literal;
               the caller will indent ONLY the first line to avoid re-indenting content.
    """
    if not node.body:
        return None
    first = node.body[0]
    if isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), ast.Constant) and isinstance(first.value.value, str):
        try:
            seg = ast.get_source_segment(module_source, first.value)
            if seg and isinstance(seg, str):
                return seg
        except Exception:
            pass
        val = first.value.value
        safe = val.replace('"""', '\\"""')
        return f'"""' + safe + '"""'
    return None


def build_method_block(
    method_name: str,
    method_node: Optional[Union[ast.FunctionDef, ast.AsyncFunctionDef]],
    module_source: Optional[str],
    fallback: bool = False,
) -> List[str]:
    """
    Build a FULLY INDENTED method block (each code line prefixed by 4 spaces for the class body).
    The docstring literal is emitted as a single token placed on a line indented to the
    METHOD BODY (8 spaces). We do NOT re-indent internal lines of the triple-quoted literal.
    """
    CLASS_IND = "    "        # 4 spaces
    BODY_IND  = "        "    # 8 spaces (method body indentation)
    lines: List[str] = []

    if fallback or method_node is None:
        if method_name == "__init__":
            lines.append(f"{CLASS_IND}def __init__(*args, **kwargs):")
            lines.append(f"{BODY_IND}# FALLBACK: exact signature/decorators/docstring unavailable; delegating")
            lines.append(f"{BODY_IND}super().__init__(*args, **kwargs)")
            return lines
        else:
            lines.append(f"{CLASS_IND}def {method_name}(*args, **kwargs):")
            lines.append(f"{BODY_IND}# FALLBACK: exact signature/decorators/docstring unavailable; delegating")
            lines.append(f"{BODY_IND}return super().{method_name}(*args, **kwargs)")
            return lines

    # decorators at class body indentation (4 spaces)
    for d in decorators_lines(method_node):
        lines.append(CLASS_IND + d)

    # def header (4 spaces)
    head, is_async = function_header(method_node)
    lines.append(CLASS_IND + head)

    # docstring at method body indentation (8 spaces)
    doc_lit = docstring_literal_from_node(method_node, module_source) if module_source else None
    if doc_lit:
        lines.append(BODY_IND + doc_lit)

    kind = decorator_kind(method_node)

    if method_name == "__init__":
        # __init__ MUST NOT return anything
        call = delegate_call_args(method_node.args, omit_first=True)  # drop self
        lines.append(f"{BODY_IND}super().__init__({call})" if call else f"{BODY_IND}super().__init__()")
        return lines

    if kind == "staticmethod":
        call = delegate_call_args(method_node.args, omit_first=False)
        call_expr = f"DockerizedDetector.{method_name}({call})"
        lines.append(f"{BODY_IND}return await {call_expr}" if is_async else f"{BODY_IND}return {call_expr}")
    elif kind == "classmethod":
        call = delegate_call_args(method_node.args, omit_first=True)   # drop cls
        call_expr = f"super().{method_name}({call})"
        lines.append(f"{BODY_IND}return await {call_expr}" if is_async else f"{BODY_IND}return {call_expr}")
    else:
        call = delegate_call_args(method_node.args, omit_first=True)   # drop self
        call_expr = f"super().{method_name}({call})"
        lines.append(f"{BODY_IND}return await {call_expr}" if is_async else f"{BODY_IND}return {call_expr}")

    return lines


def render_class(
    class_name: str,
    impl_module_stem: str,
    display_name: str,
    class_doc_lit: Optional[str],
    method_blocks: List[List[str]],
) -> str:
    lines: List[str] = [
        "# Auto-generated stub.",
        "from pydantic import validate_call",
        "from core.dockerized_detector import DockerizedDetector",
        "from core.types import *",
        "",
        "",
        f"class {class_name}(DockerizedDetector):"
    ]

    # Class docstring (single token line, indent only the first line)
    if class_doc_lit:
        lines.append(f"    {class_doc_lit}")

    # Class attributes
    lines.append(f"    name = \"{display_name}\"")
    lines.append(f"    implementation_module = \"{impl_module_stem}\"")
    lines.append(f"    implementation_class = \"{class_name}\"")
    lines.append(f"    image_tag = \"{display_name}:latest\"")
    lines.append("")

    # Methods
    if not method_blocks:
        lines.append("    pass")
    else:
        first = True
        for block in method_blocks:
            if not first:
                lines.append("")
            lines.extend(block)
            first = False

    return "\n".join(lines).rstrip() + "\n"


# =========================
# CLI + driver
# =========================

def pick_target_class(modinfo: ModuleInfo, prefer_name: Optional[str]) -> ast.ClassDef:
    if prefer_name:
        c = modinfo.classes.get(prefer_name)
        if not c:
            raise StubGenError(
                f"Class '{prefer_name}' not found in {modinfo.path}. "
                f"Available: {', '.join(modinfo.classes) or '(none)'}"
            )
        return c
    if len(modinfo.classes) == 0:
        raise StubGenError(f"No classes found in {modinfo.path}.")
    if len(modinfo.classes) == 1:
        return next(iter(modinfo.classes.values()))
    raise StubGenError(
        f"Multiple classes in {modinfo.path}. Use --class to select one."
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate a DockerizedDetector stub (static, no imports).")
    parser.add_argument("input", type=str, help="Path to the Python file containing the class.")
    parser.add_argument("--class", dest="class_name", type=str, default=None,
                        help="Class to stub (required if multiple classes in file).")
    parser.add_argument("--search-path", dest="search_paths", action="append", default=[],
                        help="Add project root(s) to resolve modules (repeatable).")
    parser.add_argument("--max-upward", dest="max_upward", type=int, default=3,
                        help="Parent dir levels to add as roots (default: 3).")
    args = parser.parse_args(argv)

    ensure_unparse_available()

    in_path = Path(args.input).resolve()
    if not in_path.exists():
        print(f"Error: input file not found: {in_path}")
        return 2

    resolver = ModuleResolver(in_path, args.search_paths, max_upward=args.max_upward)
    project = ASTProject(resolver)

    try:
        in_modinfo = project.load_module_info_from_file(in_path)
    except StubGenError as e:
        print(f"Error: {e}")
        return 2

    try:
        target_cls = pick_target_class(in_modinfo, args.class_name)
    except StubGenError as e:
        print(f"Error: {e}")
        return 2

    # Class docstring (copied from the target class, not from bases)
    class_doc_lit = docstring_literal_from_node(target_cls, in_modinfo.src)

    # Methods: resolve across static MRO; build indented blocks
    method_blocks: List[List[str]] = []
    for name in TARGET_METHODS:
        found = resolve_method_static_mro(target_cls, in_modinfo, project, name)
        if found:
            func_node, def_modinfo = found
            method_blocks.append(build_method_block(name, func_node, def_modinfo.src))
        else:
            # keep stub valid and explicit
            method_blocks.append(build_method_block(name, None, None, fallback=True))

    impl_module = in_path.stem
    display_name = camel_to_snake(target_cls.name)
    out_src = render_class(
        target_cls.name,
        impl_module,
        display_name,
        class_doc_lit,
        method_blocks,
    )

    out_path = in_path.parent / f"{in_path.stem}_api.py"
    try:
        out_path.write_text(out_src, encoding="utf-8")
    except Exception as e:
        print(f"Error writing '{out_path}': {e}")
        return 2

    print(f"Stub generated: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
