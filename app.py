import logging
from http.server import ThreadingHTTPServer

from backend.config import ACCESS_LOG_FILE, APP_LOG_FILE, HOST, PORT
from backend.handler import Handler
from backend.logging_utils import app_log, setup_logging
from backend.storage import ensure_storage


def main():
    ensure_storage()
    setup_logging()
    app_log(logging.INFO, "app.start", host=HOST, port=PORT, app_log=APP_LOG_FILE, access_log=ACCESS_LOG_FILE)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Bedmah.Local запущен: http://localhost:{PORT}")
    print("Админка: http://localhost:8080/admin")
    print("Для локальной сети: http://<IP_сервера>:8080")
    server.serve_forever()


if __name__ == "__main__":
    main()
