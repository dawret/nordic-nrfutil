from .util import check_command_return
from pathlib import Path
from platformio.proc import exec_command
import json
import shutil


class NrfUtilSdk:
    def __init__(self, nrfutil, version, env, sdk_path, toolchain_path):
        self.nrfutil = nrfutil
        self.version = version
        self.env = env
        self.sdk_path = Path(sdk_path)
        self.toolchain_path = Path(toolchain_path)


class NrfUtil:
    def __init__(self, nrfutil: Path, sdk_install_location: Path):
        if not nrfutil.exists():
            raise FileNotFoundError(
                "nrfutil is not installed. Please run the install script."
            )
        self.executable = nrfutil
        self.default_args = ["--json"]
        self.sdk_install_location = sdk_install_location
        self.sdk_default_args = ["--install-dir", sdk_install_location]

    def run_subcommand(self, name, args):
        cmd = [self.executable, name] + args
        ret = exec_command(cmd)
        check_command_return(ret, f"nrfutil {name} command failed")
        return ret["out"]

    def install_sdk(self, version):
        args = (
            [self.executable, "sdk-manager", "install", version]
            + self.sdk_default_args
            + self.default_args
        )
        ret = exec_command(args)
        check_command_return(ret, f"Failed to install SDK version {version}")
        shutil.rmtree(self.sdk_install_location / "downloads", ignore_errors=True)
        print(
            f"SDK version {version} installed successfully at {self.sdk_install_location}."
        )
        return NrfUtilSdk(
            nrfutil=self,
            version=version,
            env=self.get_sdk_env(version),
            sdk_path=self.get_sdk_path(version),
            toolchain_path=self.get_toolchain_path(version),
        )

    def _list_sdks(self):
        args = [self.executable, "sdk-manager", "list" ] + self.sdk_default_args + self.default_args
        ret = exec_command(args)
        check_command_return(ret, "Failed to list SDK versions")
        data = json.loads(ret["out"])["data"]
        return data["versions"]

    def get_toolchain_path(self, version):
        for v in self._list_sdks():
            if v["version"] == version and v["toolchainStatus"] == "installed":
                return v["toolchainPath"]
        raise RuntimeError(f"Toolchain version {version} not found.")
    
    def get_sdk_path(self, version):
        for v in self._list_sdks():
            if v["version"] == version and v["toolchainStatus"] == "installed":
                if len(v["dirNames"]) != 1:
                    raise RuntimeError(
                        f"Multiple SDK directories found for version {version}: {v['dirNames']}"
                    )
                return v["dirNames"][0]
        raise RuntimeError(f"SDK version {version} not found.")


    def get_sdk_env(self, version):
        args = (
            [self.executable, "sdk-manager", "toolchain", "env", "--ncs-version", version]
            + self.sdk_default_args
            + self.default_args
        )
        ret = exec_command(args)
        check_command_return(ret, f"Failed to get SDK environment for version {version}")
        data = json.loads(ret["out"])["data"]
        return {e["key"] : e["value"] for e in data["env_variables"]}
