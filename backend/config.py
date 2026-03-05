import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
SERVICES_FILE = os.path.join(BASE_DIR, "services.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
ICONS_DIR = os.path.join(UPLOADS_DIR, "icons")
BACKGROUNDS_DIR = os.path.join(UPLOADS_DIR, "backgrounds")
FAVICONS_DIR = os.path.join(UPLOADS_DIR, "favicons")
LOG_DIR = os.path.join(BASE_DIR, "log")
APP_LOG_FILE = os.path.join(LOG_DIR, "app.log")
ACCESS_LOG_FILE = os.path.join(LOG_DIR, "access.log")
HOST = "0.0.0.0"
PORT = 8080

DEFAULT_SETTINGS = {
    "background": {
        "mode": "preset",
        "preset": "midnight",
        "image_url": "",
        "saved_images": [],
    },
    "branding": {
        "page_title": "Bedmah.Local",
        "hero_title": "Bedmah.local",
        "hero_symbol": "✻",
        "favicon_url": "",
    },
}

ALLOWED_PRESETS = {"midnight", "obsidian", "graphite", "deepsea"}
