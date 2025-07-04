from __future__ import annotations

import importlib.resources as pkg_resources
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from urllib import request

from yamlfmt import BIN_NAME


def download_yamlfmt_binary():
    """Download yamlfmt binary for current platform if not found."""
    # 运行时平台到下载目标的映射
    RUNTIME_PLATFORM_MAP = {
        ("Linux", "x86_64"): ("linux", "x86_64"),
        ("Linux", "aarch64"): ("linux", "arm64"),
        ("Darwin", "x86_64"): ("darwin", "x86_64"),
        ("Darwin", "arm64"): ("darwin", "arm64"),
        ("Windows", "AMD64"): ("windows", "x86_64"),
        ("Windows", "ARM64"): ("windows", "arm64"),
    }
    
    current_system = platform.system()
    current_machine = platform.machine()
    
    if (current_system, current_machine) not in RUNTIME_PLATFORM_MAP:
        raise ValueError(f"Unsupported runtime platform: {current_system}, {current_machine}")
    
    download_target = RUNTIME_PLATFORM_MAP[(current_system, current_machine)]
    
    # Create yamlfmt package directory if it doesn't exist
    yamlfmt_dir = Path(__file__).parent
    binary_path = yamlfmt_dir / BIN_NAME
    
    if binary_path.exists():
        return binary_path
    
    # Download binary to temporary location first
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Get version from package metadata
        try:
            from yamlfmt import __version__
            version = re.sub(r"(?:a|b|rc)\d+|\.post\d+|\.dev\d+$", "", __version__)
        except ImportError:
            version = "0.16.0"  # fallback version
        
        # Download URL
        yamlfmt_repo = "https://github.com/google/yamlfmt/releases/download/v{version}/yamlfmt_{version}_{target_os}_{target_arch}.tar.gz"
        download_url = yamlfmt_repo.format(
            version=version,
            target_os=download_target[0],
            target_arch=download_target[1],
        )
        
        tar_gz_file = temp_dir_path / f"yamlfmt_{download_target[0]}_{download_target[1]}.tar.gz"
        
        try:
            request.urlretrieve(download_url, tar_gz_file)
        except Exception as e:
            raise RuntimeError(f"Failed to download yamlfmt binary from {download_url}: {e}")
        
        # Extract binary
        with tarfile.open(tar_gz_file, "r:gz") as tar:
            if download_target[0] == "windows":
                # Windows 上的文件名是 yamlfmt.exe
                if f"{BIN_NAME}.exe" not in tar.getnames():
                    raise RuntimeError(f"{BIN_NAME}.exe not found in downloaded archive")
                tar.extract(f"{BIN_NAME}.exe", path=temp_dir_path)
                extracted_path = temp_dir_path / f"{BIN_NAME}.exe"
            else:
                if BIN_NAME not in tar.getnames():
                    raise RuntimeError(f"{BIN_NAME} not found in downloaded archive")
                tar.extract(BIN_NAME, path=temp_dir_path)
                extracted_path = temp_dir_path / BIN_NAME
        
        # Move binary to yamlfmt package directory
        shutil.move(str(extracted_path), str(binary_path))
        
        # Make executable on Unix-like systems
        if platform.system() != "Windows":
            binary_path.chmod(binary_path.stat().st_mode | 0o111)
    
    return binary_path


def get_executable_path():
    try:
        with pkg_resources.as_file(pkg_resources.files("yamlfmt").joinpath(f"./{BIN_NAME}")) as p:
            executable_path = p
    except (FileNotFoundError, AttributeError):
        # Binary not found in package, try to download it
        executable_path = download_yamlfmt_binary()

    if platform.system() != "Windows":
        if not os.access(executable_path, os.X_OK):
            current_mode = executable_path.stat().st_mode
            executable_path.chmod(current_mode | 0o111)

    return executable_path


def main():
    executable_path = get_executable_path()
    result = subprocess.run([executable_path] + sys.argv[1:], check=False)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
