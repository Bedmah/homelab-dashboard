# Homelab Dashboard

Minimal self-hosted dashboard with web admin panel.

## Features

- Python backend (`python app.py`)
- Dashboard with grouped service cards
- Search by name / group / tags
- Tags, open in new tab option
- Admin panel on `/admin`
- Add / edit / delete services
- Drag & drop sorting
- Raw JSON editor for `services.json`
- Background settings (preset or image)
- Branding settings (title, symbol, favicon)
- Upload icons/backgrounds/favicons
- Detailed logging with in-app log viewer

## Requirements

- Python 3.9+
- Windows / Linux / macOS

## Run

```bash
python app.py
```

Open:

- Dashboard: `http://localhost:8080`
- Admin: `http://localhost:8080/admin`

For LAN access use:

- `http://<server-ip>:8080`

## Project structure

```text
app.py
backend/
frontend/
services.json
settings.json
uploads/
log/
```

## API

- `GET/POST /api/services`
- `PUT/DELETE /api/services/<id>`
- `POST /api/reorder`
- `GET/POST /api/raw`
- `POST /api/upload-icon`
- `GET/POST /api/settings`
- `POST /api/upload-background`
- `POST /api/upload-favicon`
- `GET /api/logs`

## Data files

- `services.json` — services list
- `settings.json` — dashboard/admin settings
- `uploads/` — user uploaded files
- `log/` — application and access logs

## License

MIT License. See [LICENSE](LICENSE).
