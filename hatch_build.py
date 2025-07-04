from __future__ import annotations

import os
import platform
import re
import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import Any
from urllib import request

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

# key 为 pypi 分发的系统和架构组合
BUILD_TARGET = {
    ("musllinux_1_2", "x86_64"): {"download_file": ("linux", "x86_64")},
    ("musllinux_1_2", "aarch64"): {"download_file": ("linux", "arm64")},
    ("manylinux_2_17", "x86_64"): {"download_file": ("linux", "x86_64")},
    ("manylinux_2_17", "aarch64"): {"download_file": ("linux", "arm64")},
    ("macosx_10_9", "x86_64"): {"download_file": ("darwin", "x86_64")},
    ("macosx_11_0", "arm64"): {"download_file": ("darwin", "arm64")},
    ("win", "amd64"): {"download_file": ("windows", "x86_64")},
    ("win", "arm64"): {"download_file": ("windows", "arm64")},
}

# 运行时平台到下载目标的映射（用于开发环境）
RUNTIME_PLATFORM_MAP = {
    ("Linux", "x86_64"): ("linux", "x86_64"),
    ("Linux", "aarch64"): ("linux", "arm64"),
    ("Darwin", "x86_64"): ("darwin", "x86_64"),
    ("Darwin", "arm64"): ("darwin", "arm64"),
    ("Windows", "AMD64"): ("windows", "x86_64"),
    ("Windows", "ARM64"): ("windows", "arm64"),
}


class SpecialBuildHook(BuildHookInterface):
    BIN_NAME = "yamlfmt"
    YAMLFMT_REPO = "https://github.com/google/yamlfmt/releases/download/v{version}/yamlfmt_{version}_{target_os_info}_{target_arch}.tar.gz"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.temp_dir = Path(tempfile.mkdtemp())

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        # 执行此逻辑用于 wheel 构建和 editable 安装
        if self.target_name not in ["wheel", "editable"]:
            return

        target_arch = os.environ.get("CIBW_ARCHS", None)
        target_os_info = os.environ.get("CIBW_PLATFORM", None)

        # 如果设置了 CIBW 环境变量，使用它们（CI/CD 环境）
        if target_arch is not None and target_os_info is not None:
            if (target_os_info, target_arch) not in BUILD_TARGET:
                raise ValueError(f"Unsupported target: {target_os_info}, {target_arch}")
            
            download_target = BUILD_TARGET[(target_os_info, target_arch)]["download_file"]
            # 构建完整的 Wheel 标签（仅对 wheel 构建）
            if self.target_name == "wheel":
                full_wheel_tag = f"py3-none-{target_os_info}_{target_arch}"
                build_data["tag"] = full_wheel_tag
        else:
            # 开发环境：根据当前运行时平台自动检测
            current_system = platform.system()
            current_machine = platform.machine()
            
            if (current_system, current_machine) not in RUNTIME_PLATFORM_MAP:
                raise ValueError(f"Unsupported runtime platform: {current_system}, {current_machine}")
            
            download_target = RUNTIME_PLATFORM_MAP[(current_system, current_machine)]

        # 下载 yamlfmt 可执行文件
        tar_gz_file = self.download_yamlfmt(download_target[0], download_target[1])

        # 解压缩文件
        with tarfile.open(tar_gz_file, "r:gz") as tar:
            if download_target[0] == "windows":
                # Windows 上的文件名是 yamlfmt.exe
                assert f"{self.BIN_NAME}.exe" in tar.getnames()
                tar.extract(f"{self.BIN_NAME}.exe", path=self.temp_dir)
                # 重命名为 yamlfmt
                (self.temp_dir / f"{self.BIN_NAME}.exe").rename(self.temp_dir / self.BIN_NAME)
            else:
                assert self.BIN_NAME in tar.getnames()
                tar.extract(self.BIN_NAME, path=self.temp_dir)

        # TODO: 加一个 sum 校验
        bin_path = self.temp_dir / self.BIN_NAME
        assert bin_path.is_file(), f"{self.BIN_NAME} not found"
        build_data["force_include"][f"{bin_path.resolve()}"] = f"yamlfmt/{self.BIN_NAME}"

    def download_yamlfmt(self, target_os: str, target_arch: str) -> None:
        """Download the yamlfmt binary for the specified OS and architecture."""
        file_path = self.temp_dir / f"{self.BIN_NAME}_{target_os}_{target_arch}.tar.gz"
        request.urlretrieve(
            self.YAMLFMT_REPO.format(
                version=re.sub(
                    r"(?:a|b|rc)\d+|\.post\d+|\.dev\d+$", "", self.metadata.version
                ),  # 去掉版本号中的后缀, alpha/beta/rc/post/dev
                target_os_info=target_os,
                target_arch=target_arch,
            ),
            file_path,
        )
        return file_path

    def finalize(self, version, build_data, artifact_path):
        # 清理临时目录
        shutil.rmtree(self.temp_dir)
        super().finalize(version, build_data, artifact_path)
