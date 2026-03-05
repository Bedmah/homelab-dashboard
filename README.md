# Homelab Dashboard

Минималистичная self-hosted веб-панель с админкой.

## Возможности

- Backend на Python (`python app.py`)
- Дашборд с карточками сервисов и группировкой
- Поиск по названию / группе / тегам
- Теги и открытие сервиса в новой вкладке
- Админка на `/admin`
- Добавление / редактирование / удаление сервисов
- Drag & drop сортировка
- Редактор сырого JSON для `services.json`
- Настройки фона (пресет или изображение)
- Настройки брендинга (заголовки, символ, favicon)
- Загрузка иконок / фонов / favicon
- Подробные логи и просмотр логов через админку

## Требования

- Python 3.9+
- Windows / Linux / macOS

## Запуск

```bash
python app.py
```

Открыть:

- Дашборд: `http://localhost:8080`
- Админка: `http://localhost:8080/admin`

Для локальной сети:

- `http://<ip-сервера>:8080`

## Структура проекта

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

## Файлы данных

- `services.json` — список сервисов
- `settings.json` — настройки дашборда и админки
- `uploads/` — загруженные пользователем файлы
- `log/` — логи приложения и доступа

## Лицензия

MIT, см. [LICENSE](LICENSE).
