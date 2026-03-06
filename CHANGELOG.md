# Changelog

## v2.2.0

### Added

- New page `/pass` for Active Directory password change.
- New backend endpoint `POST /api/pass`.
- Dashboard link `Сменить пароль` next to `Админка`.
- `Главная` button on password page.

### Changed

- Default bind host switched to `127.0.0.1` for safer IIS reverse-proxy deployment.
- `README.md` updated with deployment and security guidance.

### Security / Privacy

- `services.json` reset to an empty list before publication.
- Runtime/user data remains excluded by `.gitignore` (`uploads/`, `log/`, `server.log`).
