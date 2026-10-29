# Geek Magic Vibe

Pixel-art dashboard for GeekMagic 240x240 displays (local HTTP only), driven by Python, with a FastAPI backoffice. See `README.md` and `docs/DESIGN.md`.

## Working rules

- Single config: `config.json` (not committed). Schema, migration and validation live in `geekmagic/settings.py`. Never commit a real config: start from `config.example.json`.
- Every send goes through `geekmagic/pipeline.py` (cross-process lock, cleanup of stale files). `send_*.py` and `refresh_all.py` are thin wrappers around it.
- Network errors from the display are always wrapped in `GeekMagicError`.
- The display handles one request at a time: do not probe it during a send.
- After changing rendering, generate a preview (`scripts/prev_clock.py`, or the `/api/preview/...` endpoints) and look at it before sending.
- No personal data in the repository: IPs, coordinates, SSIDs, passwords and API keys stay in `config.json` or the environment.
- Languages: English is the source language. Backoffice texts go through `t('English text')` with translations in `backoffice/static/i18n/<lang>.json`; texts drawn on the display come from `geekmagic/i18n.py`. Code comments may be in French or English.

## Hardware

- JPG and GIF only, 240x240. A GIF with the same name is not overwritten: alternate names `…1.gif` / `…2.gif`.
- `/delete` sometimes answers `Fail` although the deletion happened: verify through `/filelist` (about 1 s cache).
- For API questions without official docs, rely on the community repositories HelloCubic-Lite and qurle/smalltv.
