import time
from typing import Callable, Any
import httpx
import docker
from docker.types import Mount
from docker.errors import APIError, BuildError, NotFound
import sys
from threading import Thread
import os
from config import *
import inspect
from core.base_detector import BaseDetector


def _get_payload_from_args(method, *args, **kwargs) -> dict:
    # Get the signature of the method
    sig = inspect.signature(method)
    # Bind the arguments to the signature
    bound_args = sig.bind(*args, **kwargs)
    bound_args.apply_defaults()
    payload = bound_args.arguments
    payload.pop("self", None)
    payload.pop("cls", None)
    if "kwargs" in payload:
        payload.update(payload.pop("kwargs"))
    # Return as a dictionary
    return payload


def _stream_logs(container):
    for line in container.logs(stream=True, follow=True):
        decoded = line.decode("utf-8")
        sys.stdout.write(decoded)


class DockerizedDetector(BaseDetector):
    name: str
    implementation_module: str
    implementation_class: str
    image_tag: str | None = None

    def __init__(self, *args, **kwargs) -> None:

        os.environ[DOCKERIZED] = "1"

        self._docker = docker.from_env()
        self._container_id = None
        self._client = None

        self._module_dir = Path(inspect.getfile(
            self.__class__)).parent.resolve()
        sys.path.append(str(self._module_dir))
        self._workspace = HOST_SHARED_RW_DATA / self.name
        self._workspace.mkdir(parents=True, exist_ok=True)

        self._ensure_image_sdk()
        self._start_container()

        self._post(self.__init__, *args, **kwargs)

    def _start_container(self) -> None:
        command = self._build_bootstrap_command()

        module_path = str(self._module_dir.relative_to(
            PROJECT_ROOT) / self.implementation_module).replace(
            os.sep, ".")
        implementation_class = (
            f"{module_path}:{self.implementation_class}")

        env = {
            DOCKERIZED: "1",
            RUNNING_IN_CONTAINER: "1",
            DETECTOR_CLASS: implementation_class
        }

        HOST_SHARED_RO_DATA.mkdir(parents=True, exist_ok=True)
        mount = Mount(
            target=CONTAINER_SHARED_RO_DATA,
            source=str(HOST_SHARED_RO_DATA),
            type="bind",
            read_only=True
        )

        container_name = f"{self.name}-{id(self)}"

        ports = {f"8000/tcp": None}

        volumes = {
            str(self._workspace): {"bind": CONTAINER_SHARED_RW_DATA, "mode": "rw"},
        }

        try:
            container = self._docker.containers.run(
                image=self.image_tag,
                command=command,
                auto_remove=True,
                detach=True,
                environment=env,
                mounts=[mount],
                name=container_name,
                ports=ports,
                volumes=volumes,
                working_dir="/app",
                tty=False,
            )
            log_thread = Thread(
                target=_stream_logs, args=(container,), daemon=True)
            log_thread.start()

        except APIError as e:
            raise RuntimeError(f"Docker run failed: {e.explanation}") from e

        self._container_id = container.id

        container.reload()
        ports = container.attrs["NetworkSettings"]["Ports"]
        mapping = ports.get("8000/tcp")
        if not mapping:
            raise RuntimeError("Container did not expose port 8000/tcp.")
        self._port = int(mapping[0]["HostPort"])
        self._api_base = f"http://127.0.0.1:{self._port}"
        self._client = httpx.Client(base_url=self._api_base, timeout=120.0)

        deadline = time.time() + 90.0
        while time.time() < deadline:
            try:
                r = self._client.get("/health")
                if r.status_code == 200:
                    break
            except:
                pass
            time.sleep(0.2)
        else:
            self._teardown_container()
            raise TimeoutError(
                "Detector container did not become healthy in time.")

    def train(self, *args, **kwargs):
        return self._post(self.train, *args, **kwargs)

    def classify(self, *args, **kwargs):
        return self._post(self.classify, *args, **kwargs)

    def save(self, *args, **kwargs):
        self._post(self.save, *args, **kwargs)

    def load(self, *args, **kwargs):
        self._post(self.load, *args, **kwargs)

    def __del__(self) -> None:
        self._teardown_container()

    def _teardown_container(self) -> None:
        if self._client:
            try:
                self._client.post("/shutdown", json={})
            except Exception:
                pass
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

        if self._container_id:
            try:
                cont = self._docker.containers.get(self._container_id)
                # c.stop(timeout=3)
                cont.remove(force=True)
            except NotFound:
                pass
            except Exception:
                pass
            self._container_id = None
            self._api_base = None
            self._host_port = None

    def _post(
        self,
        method_ref: Callable,
        *args,
        **kwargs
    ) -> Any:
        assert self._client is not None

        path = f"/{method_ref.__name__}"
        payload = _get_payload_from_args(method_ref, *args, **kwargs)

        r = self._client.post(path, json=payload)
        try:
            r.raise_for_status()
        except:
            try:
                print(r.json())
            except:
                pass
            raise

        if r.content and r.json():
            response = r.json()
            if isinstance(response, dict):
                return tuple(dict.values())
            elif isinstance(response, (list, tuple, set)):
                return tuple(response)
            else:
                return response
        return None

    def _ensure_image_sdk(self) -> None:
        try:
            _, logs = self._docker.images.build(
                path=str(PROJECT_ROOT),
                dockerfile=str(self._module_dir / "Dockerfile"),
                tag=self.image_tag,
                rm=True,
            )
            for log in logs:
                if "stream" in log:
                    print(log.get("stream", "").strip())
            self._docker.images.prune(filters={"dangling": True})
        except BuildError as e:
            for line in e.build_log:
                if "stream" in line:
                    print(line.get("stream", "").strip())
            raise RuntimeError(f"Docker image build failed: {e.msg}") from e
        except APIError as e:
            raise RuntimeError(
                f"Docker image build failed: {e.explanation}") from e

    def _build_bootstrap_command(
        self,
    ) -> list[str]:
        py_code = (
            f"import sys, uvicorn, importlib\n"
            f"sys.path.append('/app/src')\n"
            f"app = importlib.import_module('core.server').app\n"
            f"uvicorn.run(app, host='0.0.0.0', port=8000)\n"
        )
        return ["python", "-c", py_code]
