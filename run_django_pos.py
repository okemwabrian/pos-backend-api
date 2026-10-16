import os
import secrets
import threading
import webbrowser

from desktop_runtime import get_data_dir


def _get_secret_key(data_dir):
    secret_file = data_dir / "django-secret-key.txt"
    try:
        with secret_file.open("x", encoding="utf-8") as secret:
            secret.write(secrets.token_urlsafe(48))
    except FileExistsError:
        pass
    if os.name != "nt":
        secret_file.chmod(0o600)
    return secret_file.read_text(encoding="utf-8").strip()


def main():
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    media_dir = data_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    os.environ["DJANGO_SETTINGS_MODULE"] = "core.settings"
    os.environ["CHIWAS_DATABASE_PATH"] = str(data_dir / "db.sqlite3")
    os.environ["CHIWAS_MEDIA_PATH"] = str(media_dir)
    os.environ["DJANGO_SECRET_KEY"] = _get_secret_key(data_dir)
    os.environ["DJANGO_ALLOWED_HOSTS"] = "127.0.0.1,localhost"
    os.environ["DJANGO_DEBUG"] = "false"

    import django
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from django.core.management import call_command
    from django.core.wsgi import get_wsgi_application
    from waitress import serve

    django.setup()
    call_command("migrate", interactive=False)
    application = StaticFilesHandler(get_wsgi_application())
    port = int(os.environ.get("CHIWAS_PORT", "8000"))
    url = f"http://127.0.0.1:{port}/"
    threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    print(f"FREE HOUSE POS is running locally at {url}. Close this window to stop it.")
    serve(application, host="127.0.0.1", port=port, threads=8)


if __name__ == "__main__":
    main()
