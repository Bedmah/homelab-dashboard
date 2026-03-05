import json
import logging
import os
import re
import uuid

from .config import (
    ALLOWED_PRESETS,
    BACKGROUNDS_DIR,
    DEFAULT_SETTINGS,
    FAVICONS_DIR,
    ICONS_DIR,
    LOG_DIR,
    SERVICES_FILE,
    SETTINGS_FILE,
)
from .logging_utils import app_log


def ensure_storage():
    os.makedirs(ICONS_DIR, exist_ok=True)
    os.makedirs(BACKGROUNDS_DIR, exist_ok=True)
    os.makedirs(FAVICONS_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(SERVICES_FILE):
        with open(SERVICES_FILE, "w", encoding="utf-8") as file_obj:
            json.dump([], file_obj, ensure_ascii=False, indent=2)
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as file_obj:
            json.dump(DEFAULT_SETTINGS, file_obj, ensure_ascii=False, indent=2)


def normalize_tags(tags):
    if isinstance(tags, list):
        return [str(tag).strip() for tag in tags if str(tag).strip()]
    if isinstance(tags, str):
        return [tag.strip() for tag in tags.split(",") if tag.strip()]
    return []


def normalize_service(payload, current_id=None):
    if not isinstance(payload, dict):
        raise ValueError("Данные сервиса должны быть объектом")
    name = str(payload.get("name", "")).strip()
    url = str(payload.get("url", "")).strip()
    if not name or not url:
        raise ValueError("Поля 'name' и 'url' обязательны")

    return {
        "id": str(current_id or payload.get("id") or uuid.uuid4().hex),
        "name": name,
        "url": url,
        "icon": str(payload.get("icon", "")).strip(),
        "group": str(payload.get("group", "Общее")).strip() or "Общее",
        "tags": normalize_tags(payload.get("tags", [])),
        "new_tab": bool(payload.get("new_tab", False)),
    }


def normalize_settings(payload):
    background = payload.get("background", {}) if isinstance(payload, dict) else {}
    branding = payload.get("branding", {}) if isinstance(payload, dict) else {}
    mode = str(background.get("mode", "preset")).strip().lower()
    preset = str(background.get("preset", "midnight")).strip().lower()
    image_url = str(background.get("image_url", "")).strip()
    saved_images_raw = background.get("saved_images", [])

    if mode not in {"preset", "image"}:
        mode = "preset"
    if preset not in ALLOWED_PRESETS:
        preset = "midnight"
    if not isinstance(saved_images_raw, list):
        saved_images_raw = []

    saved_images = []
    for item in saved_images_raw:
        url = str(item).strip()
        if not url:
            continue
        if url not in saved_images:
            saved_images.append(url)

    if image_url and image_url not in saved_images:
        saved_images.insert(0, image_url)

    page_title = str(branding.get("page_title", "Bedmah.Local")).strip() or "Bedmah.Local"
    hero_title = str(branding.get("hero_title", "Bedmah.local")).strip() or "Bedmah.local"
    hero_symbol = str(branding.get("hero_symbol", "✻")).strip() or "✻"
    favicon_url = str(branding.get("favicon_url", "")).strip()

    return {
        "background": {
            "mode": mode,
            "preset": preset,
            "image_url": image_url,
            "saved_images": saved_images[:50],
        },
        "branding": {
            "page_title": page_title[:120],
            "hero_title": hero_title[:120],
            "hero_symbol": hero_symbol[:8],
            "favicon_url": favicon_url,
        },
    }


def load_services():
    try:
        with open(SERVICES_FILE, "r", encoding="utf-8") as file_obj:
            data = json.load(file_obj)
        if isinstance(data, list):
            return data
    except Exception as error:
        app_log(logging.ERROR, "services.load.error", error=repr(error), file=SERVICES_FILE)
    return []


def save_services(data):
    with open(SERVICES_FILE, "w", encoding="utf-8") as file_obj:
        json.dump(data, file_obj, ensure_ascii=False, indent=2)
    app_log(logging.INFO, "services.save", total=len(data), file=SERVICES_FILE)


def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file_obj:
            data = json.load(file_obj)
        if isinstance(data, dict):
            settings = normalize_settings(data)
            discovered = []
            if os.path.isdir(BACKGROUNDS_DIR):
                for name in sorted(os.listdir(BACKGROUNDS_DIR), reverse=True):
                    full = os.path.join(BACKGROUNDS_DIR, name)
                    if os.path.isfile(full):
                        discovered.append(f"/uploads/backgrounds/{name}")
            for url in discovered:
                if url not in settings["background"]["saved_images"]:
                    settings["background"]["saved_images"].append(url)
            return settings
    except Exception as error:
        app_log(logging.ERROR, "settings.load.error", error=repr(error), file=SETTINGS_FILE)
    return normalize_settings(DEFAULT_SETTINGS)


def save_settings(data):
    normalized = normalize_settings(data)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as file_obj:
        json.dump(normalized, file_obj, ensure_ascii=False, indent=2)
    app_log(
        logging.INFO,
        "settings.save.file",
        file=SETTINGS_FILE,
        mode=normalized.get("background", {}).get("mode"),
        preset=normalized.get("background", {}).get("preset"),
        image_url=normalized.get("background", {}).get("image_url"),
        saved_images=len(normalized.get("background", {}).get("saved_images", [])),
        page_title=normalized.get("branding", {}).get("page_title"),
    )


def safe_name(name):
    base = os.path.basename(name)
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    return base or "file"


def parse_multipart_file(content_type, body):
    match = re.search(r"boundary=(.+)", content_type)
    if not match:
        return None
    boundary = match.group(1).strip().strip('"').encode("utf-8")
    parts = body.split(b"--" + boundary)
    for part in parts:
        part = part.strip()
        if not part or part == b"--":
            continue
        if part.startswith(b"--"):
            part = part[2:]
        headers, sep, content = part.partition(b"\r\n\r\n")
        if not sep:
            continue
        headers_text = headers.decode("utf-8", errors="ignore")
        disp_match = re.search(r'Content-Disposition:.*filename="([^"]+)"', headers_text, re.IGNORECASE)
        if not disp_match:
            continue
        return {
            "filename": safe_name(disp_match.group(1)),
            "content": content.rstrip(b"\r\n"),
        }
    return None
