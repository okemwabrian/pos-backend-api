import subprocess
import sys
import venv
from pathlib import Path

from desktop_runtime import get_data_dir, get_venv_dir, get_venv_python


PROJECT_DIR = Path(__file__).resolve().parent


def main():
    if sys.version_info < (3, 12):
        raise SystemExit("Python 3.12 or newer is required to set up FREE HOUSE POS.")

    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    environment_dir = get_venv_dir()
    if not get_venv_python().exists():
        print(f"Creating the private Python environment in {environment_dir}")
        venv.EnvBuilder(with_pip=True).create(environment_dir)

    print("Installing Django POS requirements. Internet access is needed for this step.")
    subprocess.run(
        [
            str(get_venv_python()),
            "-m",
            "pip",
            "install",
            "-r",
            str(PROJECT_DIR / "requirements.txt"),
        ],
        check=True,
    )

    subprocess.run(
        [str(get_venv_python()), str(PROJECT_DIR / "run_django_pos.py")],
        check=True,
    )


if __name__ == "__main__":
    main()
