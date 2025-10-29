import time
from typing import Type
import httpx
import docker
from docker.types import Mount
from docker.errors import APIError, BuildError, NotFound
from pathlib import Path
from pydantic import BaseModel
import tempfile
import inspect
import sys
from threading import Thread
import os
from core.detector_interface import DetectorInterface
from core.pydantic_models import *


def _stream_logs(container):
    for line in container.logs(stream=True, follow=True):
        decoded = line.decode("utf-8")
        sys.stdout.write(decoded)


class BaseDetector(DetectorInterface):
    name: str
    implementation_module: str
    implementation_class: str
    init_args: Type[BaseInit] = BaseInit
    train_args: Type[BaseTrain] = BaseTrain
    train_response: Type[BaseTrainResponse] = BaseTrainResponse
    classify_args: Type[BaseClassify] = BaseClassify
    classify_response: Type[BaseClassifyResponse] = BaseClassifyResponse
    save_args: Type[BaseSave] = BaseSave
    load_args: Type[BaseLoad] = BaseLoad
    image_tag: str | None = None

    def __init__(self, init_args: BaseInit) -> None:

        self._docker = docker.from_env()
        self._container_id = None
        self._client = None

        if not self.image_tag:
            self.image_tag = f"{self.name}:latest"

        self._project_root = Path(__file__).parent.parent.parent
        self._module_dir = Path(inspect.getfile(
            self.__class__)).parent.resolve()
        sys.path.append(str(self._module_dir))
        self._workspace = self._project_root.parent / "data" / self.name
        self._workspace.mkdir(parents=True, exist_ok=True)

        self._ensure_image_sdk()
        self._start_container()

        self._post("/init", init_args)

    def _start_container(self) -> None:
        command = self._build_bootstrap_command()

        main_class = f"{self.__class__.__module__}:{self.__class__.__name__}"
        module_path = str(self._module_dir.relative_to(
            self._project_root) / self.implementation_module).replace(
            os.sep, ".")
        implementation_class = (
            f"{module_path}:{self.implementation_class}")

        env = {
            "RUNNING_IN_DETECTOR_CONTAINER": "1",
            "DETECTOR_MAIN_CLASS": main_class,
            "DETECTOR_IMPLEMENTATION_CLASS": implementation_class
        }

        tmp_data_dir = Path(tempfile.gettempdir()) / "android-detectors_shared"
        tmp_data_dir.mkdir(parents=True, exist_ok=True)
        mount = Mount(
            target="/shared",
            source=str(tmp_data_dir),
            type="bind",
            read_only=True
        )

        container_name = f"{self.name}-{id(self)}"

        ports = {f"8000/tcp": None}

        volumes = {
            str(self._workspace): {"bind": "/data", "mode": "rw"},
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

    def train(
        self,
        train_args: train_args,
    ) -> train_response:
        response = self._post("/train", train_args)
        return self.train_response.model_validate(response)

    def classify(
        self,
        classify_args: classify_args,
    ) -> classify_response:
        response = self._post("/classify", classify_args)
        return self.classify_response.model_validate(response)

    def save(
        self,
        save_args: save_args,
    ) -> None:
        self._post("/save", save_args)

    def load(
        self,
        load_args: load_args,
    ) -> None:
        self._post("/load", load_args)

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
        path: str,
        payload: BaseModel
    ) -> dict:
        assert self._client is not None
        r = self._client.post(path, json=payload.model_dump())
        try:
            r.raise_for_status()
        except:
            try:
                print(r.json())
            except:
                pass
            raise
        if r.content:
            return r.json()
        return {}

    def _ensure_image_sdk(self) -> None:
        try:
            _, logs = self._docker.images.build(
                path=str(self._project_root),
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
