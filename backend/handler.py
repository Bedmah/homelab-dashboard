import json
import logging
import mimetypes
import os
import re
import time
import uuid
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from .config import (
    ACCESS_LOG_FILE,
    APP_LOG_FILE,
    BACKGROUNDS_DIR,
    FAVICONS_DIR,
    FRONTEND_DIR,
    ICONS_DIR,
    SERVICES_FILE,
    UPLOADS_DIR,
)
from .logging_utils import ACCESS_LOGGER, app_log, kv_dump, read_log_tail
from .storage import (
    load_services,
    load_settings,
    normalize_service,
    normalize_settings,
    parse_multipart_file,
    save_services,
    save_settings,
)


def _read_frontend_file(filename):
    full = os.path.abspath(os.path.join(FRONTEND_DIR, filename))
    if not full.startswith(os.path.abspath(FRONTEND_DIR)):
        return None
    if not os.path.isfile(full):
        return None
    with open(full, "r", encoding="utf-8") as file_obj:
        return file_obj.read()


class Handler(BaseHTTPRequestHandler):
    server_version = "BedmahLocal/2.1"

    def _request_meta(self):
        parsed = urlparse(self.path)
        return {
            "rid": getattr(self, "_rid", "-"),
            "method": self.command,
            "path": parsed.path,
            "query": parsed.query,
            "client": f"{self.client_address[0]}:{self.client_address[1]}",
            "ua": self.headers.get("User-Agent", ""),
        }

    def _begin_request(self):
        self._rid = uuid.uuid4().hex[:8]
        self._started_at = time.time()
        self._last_status = 500
        meta = self._request_meta()
        ACCESS_LOGGER.info(f"request.begin | {kv_dump(**meta)}")
        app_log(logging.INFO, "request.begin", **meta)

    def _end_request(self, status):
        meta = self._request_meta()
        elapsed_ms = int((time.time() - getattr(self, "_started_at", time.time())) * 1000)
        ACCESS_LOGGER.info(f"request.end | {kv_dump(status=status, elapsed_ms=elapsed_ms, **meta)}")
        app_log(logging.INFO, "request.end", status=status, elapsed_ms=elapsed_ms, **meta)

    def log_message(self, fmt, *args):
        msg = fmt % args
        meta = self._request_meta() if hasattr(self, "_rid") else {
            "rid": "-",
            "method": getattr(self, "command", "-"),
            "path": getattr(self, "path", "-"),
            "client": f"{self.client_address[0]}:{self.client_address[1]}",
        }
        ACCESS_LOGGER.info(f"http.server | {msg} | {kv_dump(**meta)}")

    def _send_json(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._last_status = code
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html):
        body = html.encode("utf-8")
        self._last_status = 200
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        return self.rfile.read(length) if length else b""

    def _read_json(self):
        raw = self._read_body()
        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            app_log(logging.ERROR, "request.json.invalid", rid=getattr(self, "_rid", "-"), path=urlparse(self.path).path)
            raise ValueError("Invalid JSON payload")

    def _serve_upload(self, path):
        rel = path[len("/uploads/"):]
        full = os.path.abspath(os.path.join(UPLOADS_DIR, rel.replace("/", os.sep)))
        if not full.startswith(os.path.abspath(UPLOADS_DIR)):
            self._send_json(403, {"error": "Forbidden"})
            return
        if not os.path.isfile(full):
            self._send_json(404, {"error": "File not found"})
            return
        ctype, _ = mimetypes.guess_type(full)
        with open(full, "rb") as file_obj:
            body = file_obj.read()
        self._last_status = 200
        self.send_response(200)
        self.send_header("Content-Type", ctype or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_upload(self, dest_dir, prefix):
        ctype = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in ctype:
            self._send_json(400, {"error": "Content-Type must be multipart/form-data"})
            return
        file_data = parse_multipart_file(ctype, self._read_body())
        if not file_data:
            self._send_json(400, {"error": "No file in request"})
            return

        _, ext = os.path.splitext(file_data["filename"])
        ext = (ext or ".bin")[:10]
        fname = f"{prefix}_{uuid.uuid4().hex}{ext}"
        out = os.path.join(dest_dir, fname)
        with open(out, "wb") as file_obj:
            file_obj.write(file_data["content"])

        rel = os.path.relpath(out, UPLOADS_DIR).replace("\\", "/")
        app_log(
            logging.INFO,
            "upload.saved",
            rid=getattr(self, "_rid", "-"),
            original=file_data.get("filename"),
            stored=fname,
            bytes=len(file_data.get("content", b"")),
            folder=dest_dir,
            url=f"/uploads/{rel}",
        )
        self._send_json(200, {"url": f"/uploads/{rel}"})

    def do_GET(self):
        self._begin_request()
        try:
            path = urlparse(self.path).path

            if path == "/":
                html = _read_frontend_file("dashboard.html")
                if html is None:
                    self._send_json(500, {"error": "frontend/dashboard.html not found"})
                else:
                    self._send_html(html)
                return
            if path == "/admin":
                html = _read_frontend_file("admin.html")
                if html is None:
                    self._send_json(500, {"error": "frontend/admin.html not found"})
                else:
                    self._send_html(html)
                return
            if path.startswith("/uploads/"):
                self._serve_upload(path)
                return
            if path == "/api/services":
                data = load_services()
                app_log(logging.INFO, "services.list", rid=getattr(self, "_rid", "-"), total=len(data))
                self._send_json(200, data)
                return
            if path == "/api/raw":
                with open(SERVICES_FILE, "r", encoding="utf-8") as file_obj:
                    raw = file_obj.read()
                app_log(logging.INFO, "services.raw.read", rid=getattr(self, "_rid", "-"), size=len(raw))
                self._send_json(200, {"raw": raw})
                return
            if path == "/api/settings":
                settings = load_settings()
                app_log(
                    logging.INFO,
                    "settings.read",
                    rid=getattr(self, "_rid", "-"),
                    mode=settings.get("background", {}).get("mode"),
                    preset=settings.get("background", {}).get("preset"),
                    saved_images=len(settings.get("background", {}).get("saved_images", [])),
                    page_title=settings.get("branding", {}).get("page_title"),
                )
                self._send_json(200, settings)
                return
            if path == "/api/logs":
                query = parse_qs(urlparse(self.path).query)
                file_name = (query.get("file", ["app.log"])[0] or "app.log").strip()
                lines_raw = (query.get("lines", ["400"])[0] or "400").strip()
                allowed = {"app.log": APP_LOG_FILE, "access.log": ACCESS_LOG_FILE}
                path_to_read = allowed.get(file_name, APP_LOG_FILE)
                try:
                    lines = int(lines_raw)
                except Exception:
                    lines = 400
                payload = {
                    "files": list(allowed.keys()),
                    "selected": file_name if file_name in allowed else "app.log",
                    "lines": read_log_tail(path_to_read, lines),
                }
                app_log(
                    logging.INFO,
                    "logs.read",
                    rid=getattr(self, "_rid", "-"),
                    file=payload["selected"],
                    lines_requested=lines,
                    lines_returned=len(payload["lines"]),
                )
                self._send_json(200, payload)
                return
            self._send_json(404, {"error": "Not found"})
        except Exception as error:
            app_log(logging.ERROR, "request.get.unhandled", rid=getattr(self, "_rid", "-"), error=repr(error), path=self.path)
            self._send_json(500, {"error": "Internal server error"})
        finally:
            self._end_request(getattr(self, "_last_status", 500))

    def do_POST(self):
        self._begin_request()
        try:
            path = urlparse(self.path).path

            if path == "/api/services":
                try:
                    service = normalize_service(self._read_json())
                    data = load_services()
                    data.append(service)
                    save_services(data)
                    app_log(
                        logging.INFO,
                        "service.create",
                        rid=getattr(self, "_rid", "-"),
                        service_id=service.get("id"),
                        name=service.get("name"),
                        group=service.get("group"),
                        tags=len(service.get("tags", [])),
                    )
                    self._send_json(201, service)
                except ValueError as error:
                    app_log(logging.WARNING, "service.create.validation", rid=getattr(self, "_rid", "-"), error=str(error))
                    self._send_json(400, {"error": str(error)})
                return

            if path == "/api/reorder":
                try:
                    payload = self._read_json()
                    ids = payload.get("ids")
                    if not isinstance(ids, list):
                        raise ValueError("Field 'ids' must be array")
                    data = load_services()
                    index = {item.get("id"): item for item in data}
                    ordered = [index[sid] for sid in ids if sid in index]
                    ordered += [item for item in data if item.get("id") not in ids]
                    save_services(ordered)
                    app_log(logging.INFO, "service.reorder", rid=getattr(self, "_rid", "-"), total=len(ordered), ids_sent=len(ids))
                    self._send_json(200, ordered)
                except ValueError as error:
                    app_log(logging.WARNING, "service.reorder.validation", rid=getattr(self, "_rid", "-"), error=str(error))
                    self._send_json(400, {"error": str(error)})
                return

            if path == "/api/raw":
                try:
                    payload = self._read_json()
                    raw = payload.get("raw", "")
                    if not isinstance(raw, str):
                        raise ValueError("Field 'raw' must be string")
                    parsed = json.loads(raw)
                    if not isinstance(parsed, list):
                        raise ValueError("services.json must be JSON array")
                    normalized = [normalize_service(item, current_id=item.get("id")) for item in parsed]
                    save_services(normalized)
                    app_log(logging.INFO, "services.raw.save", rid=getattr(self, "_rid", "-"), total=len(normalized), raw_size=len(raw))
                    self._send_json(200, {"ok": True})
                except ValueError as error:
                    app_log(logging.WARNING, "services.raw.validation", rid=getattr(self, "_rid", "-"), error=str(error))
                    self._send_json(400, {"error": str(error)})
                except json.JSONDecodeError as error:
                    app_log(logging.WARNING, "services.raw.parse_error", rid=getattr(self, "_rid", "-"), error=str(error))
                    self._send_json(400, {"error": f"JSON parse error: {error}"})
                return

            if path == "/api/settings":
                try:
                    payload = self._read_json()
                    current = load_settings()
                    incoming_bg = payload.get("background", {}) if isinstance(payload, dict) else {}
                    incoming_brand = payload.get("branding", {}) if isinstance(payload, dict) else {}
                    merged = {
                        "background": {
                            **(current.get("background", {}) if isinstance(current, dict) else {}),
                            **(incoming_bg if isinstance(incoming_bg, dict) else {}),
                        },
                        "branding": {
                            **(current.get("branding", {}) if isinstance(current, dict) else {}),
                            **(incoming_brand if isinstance(incoming_brand, dict) else {}),
                        },
                    }
                    settings = normalize_settings(merged)
                    save_settings(settings)
                    app_log(
                        logging.INFO,
                        "settings.save",
                        rid=getattr(self, "_rid", "-"),
                        bg_mode=settings.get("background", {}).get("mode"),
                        bg_preset=settings.get("background", {}).get("preset"),
                        bg_url=settings.get("background", {}).get("image_url"),
                        saved_images=len(settings.get("background", {}).get("saved_images", [])),
                        page_title=settings.get("branding", {}).get("page_title"),
                        hero_title=settings.get("branding", {}).get("hero_title"),
                        hero_symbol=settings.get("branding", {}).get("hero_symbol"),
                        favicon_url=settings.get("branding", {}).get("favicon_url"),
                    )
                    self._send_json(200, settings)
                except ValueError as error:
                    app_log(logging.WARNING, "settings.save.validation", rid=getattr(self, "_rid", "-"), error=str(error))
                    self._send_json(400, {"error": str(error)})
                return

            if path == "/api/upload-icon":
                self._handle_upload(ICONS_DIR, "icon")
                return
            if path == "/api/upload-background":
                self._handle_upload(BACKGROUNDS_DIR, "bg")
                return
            if path == "/api/upload-favicon":
                self._handle_upload(FAVICONS_DIR, "fav")
                return

            self._send_json(404, {"error": "Not found"})
        except Exception as error:
            app_log(logging.ERROR, "request.post.unhandled", rid=getattr(self, "_rid", "-"), error=repr(error), path=self.path)
            self._send_json(500, {"error": "Internal server error"})
        finally:
            self._end_request(getattr(self, "_last_status", 500))

    def do_PUT(self):
        self._begin_request()
        try:
            path = urlparse(self.path).path
            match = re.fullmatch(r"/api/services/([^/]+)", path)
            if not match:
                self._send_json(404, {"error": "Not found"})
                return

            sid = match.group(1)
            data = load_services()
            idx = next((i for i, item in enumerate(data) if str(item.get("id")) == sid), -1)
            if idx < 0:
                self._send_json(404, {"error": "Service not found"})
                return
            try:
                data[idx] = normalize_service(self._read_json(), current_id=sid)
                save_services(data)
                app_log(
                    logging.INFO,
                    "service.update",
                    rid=getattr(self, "_rid", "-"),
                    service_id=sid,
                    name=data[idx].get("name"),
                    group=data[idx].get("group"),
                    tags=len(data[idx].get("tags", [])),
                )
                self._send_json(200, data[idx])
            except ValueError as error:
                app_log(logging.WARNING, "service.update.validation", rid=getattr(self, "_rid", "-"), service_id=sid, error=str(error))
                self._send_json(400, {"error": str(error)})
        except Exception as error:
            app_log(logging.ERROR, "request.put.unhandled", rid=getattr(self, "_rid", "-"), error=repr(error), path=self.path)
            self._send_json(500, {"error": "Internal server error"})
        finally:
            self._end_request(getattr(self, "_last_status", 500))

    def do_DELETE(self):
        self._begin_request()
        try:
            path = urlparse(self.path).path
            match = re.fullmatch(r"/api/services/([^/]+)", path)
            if not match:
                self._send_json(404, {"error": "Not found"})
                return

            sid = match.group(1)
            data = load_services()
            new_data = [item for item in data if str(item.get("id")) != sid]
            if len(new_data) == len(data):
                self._send_json(404, {"error": "Service not found"})
                return
            save_services(new_data)
            app_log(logging.INFO, "service.delete", rid=getattr(self, "_rid", "-"), service_id=sid)
            self._send_json(200, {"ok": True})
        except Exception as error:
            app_log(logging.ERROR, "request.delete.unhandled", rid=getattr(self, "_rid", "-"), error=repr(error), path=self.path)
            self._send_json(500, {"error": "Internal server error"})
        finally:
            self._end_request(getattr(self, "_last_status", 500))
