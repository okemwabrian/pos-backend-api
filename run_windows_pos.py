"""Launch the local Chiwas POS server on Windows."""

import os
from pathlib import Path
import secrets
import threading
import webbrowser


def main():
    if os.name != "nt":
        raise SystemExit("This launcher is intended for Windows.")

    data_dir = Path(
        os.environ.get(
            "LOCALAPPDATA", str(Path.home() / "AppData" / "Local")
        )
    ) / "Chiwas Liquor POS"
    data_dir.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    os.environ["CHIWAS_DATABASE_PATH"] = str(data_dir / "db.sqlite3")
    os.environ["CHIWAS_MEDIA_PATH"] = str(data_dir / "media")
    Path(os.environ["CHIWAS_MEDIA_PATH"]).mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")
    os.environ["DJANGO_DEBUG"] = "false"
    secret_file = data_dir / "django-secret-key.txt"
    if secret_file.exists():
        os.environ["DJANGO_SECRET_KEY"] = secret_file.read_text(encoding="utf-8").strip()
    else:
        secret = secrets.token_urlsafe(48)
        secret_file.write_text(secret, encoding="utf-8")
        os.environ["DJANGO_SECRET_KEY"] = secret

    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from django.core.management import call_command
    from django.core.wsgi import get_wsgi_application
    from waitress import serve

    call_command("migrate", interactive=False, verbosity=1)
    application = StaticFilesHandler(get_wsgi_application())
    url = "http://127.0.0.1:8765/"
    threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    serve(application, host="127.0.0.1", port=8765, threads=8)


if __name__ == "__main__":
    main()
