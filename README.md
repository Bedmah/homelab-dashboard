# Homelab Dashboard

Минималистичная self-hosted веб-панель с админкой.

## Что нового

- Добавлена страница смены пароля AD: `/pass`
- Добавлен API для смены пароля AD: `POST /api/pass`
- На дашборд добавлена кнопка `Сменить пароль`
- На странице смены пароля добавлена кнопка `Главная`
- По умолчанию backend привязан к `127.0.0.1` (удобно для схемы IIS reverse proxy)

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

## Быстрый запуск

```bash
python app.py
```

Открыть:

- Дашборд: `http://localhost:8080`
- Админка: `http://localhost:8080/admin`
- Смена пароля AD (Windows): `http://localhost:8080/pass`

## Прод-схема с IIS (рекомендовано для Windows Server)

1. Оставить backend на `127.0.0.1:8080`
2. IIS публикует сайт на `80/443`
3. Включить auth на IIS (`Windows Authentication`)
4. Настроить reverse proxy на `http://127.0.0.1:8080`

Так пользователи не ходят напрямую на `:8080`, а проходят через IIS-авторизацию.

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
- `POST /api/pass` — смена пароля AD (Windows)

## Файлы данных

- `services.json` — список сервисов
- `settings.json` — настройки дашборда и админки
- `uploads/` — загруженные пользователем файлы
- `log/` — логи приложения и доступа

## Лицензия

MIT, см. [LICENSE](LICENSE).
