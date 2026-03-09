# Changelog

## v0.1.3

### Changed

- Redesigned `/pass` page: improved layout, typography, controls, and mobile responsiveness.
- Added theme synchronization on `/pass` using shared `localStorage` key `bedmah_theme`.
- Added settings sync on `/pass` via `/api/settings`:
  - Background preset/image now follows admin panel settings.
  - Branding (`page_title`, `hero_title`, `hero_symbol`, `favicon_url`) now follows admin panel settings.
- Improved password form UX on `/pass`:
  - Optional `domain` field.
  - Password strength hint text.
  - Clearer validation and status messages.
  - Quick navigation buttons to dashboard and admin page.

## v1.1.0

### Added

- New page `/pass` for Active Directory password change.
- New backend endpoint `POST /api/pass`.
- Dashboard link `Сменить пароль` next to `Админка`.
- `Главная` button on password page.

### Changed

- Default bind host switched to `127.0.0.1` for safer IIS reverse-proxy deployment.
- `README.md` updated with deployment and security guidance.
