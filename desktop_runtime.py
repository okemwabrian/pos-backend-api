import os
from pathlib import Path


def get_data_dir():
    configured = os.environ.get("CHIWAS_DATA_DIR")
    if configured:
        return Path(configured)
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "FREE HOUSE POS"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "free-house-pos"


def get_venv_dir():
    return get_data_dir() / "venv"


def get_venv_python():
    executable = "python.exe" if os.name == "nt" else "python"
    return get_venv_dir() / ("Scripts" if os.name == "nt" else "bin") / executable
