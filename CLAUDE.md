# Geek Magic Vibe

Dashboard pixel art 240x240 pour écran GeekMagic (HTTP local uniquement), piloté par Python, avec backoffice FastAPI. Voir `README.md` et `docs/DESIGN.md`.

## Règles de travail

- Config unique : `config.json` (non versionné). Schéma, migration et validation dans `geekmagic/settings.py`. Ne jamais committer de config réelle : partir de `config.example.json`.
- Tout envoi passe par `geekmagic/pipeline.py` (verrou inter-processus, nettoyage des fichiers périmés). Les scripts `send_*.py` et `refresh_all.py` en sont des wrappers.
- Erreurs réseau de l'écran : toujours encapsulées dans `GeekMagicError`.
- L'écran est mono-tâche : ne pas le sonder pendant un envoi.
- Après modification du rendu, générer un aperçu (`scripts/prev_clock.py`, ou les endpoints `/api/preview/...`) et le regarder avant d'envoyer.
- Aucune donnée personnelle dans le dépôt : IP, coordonnées, SSID, mots de passe, clés API restent dans `config.json` ou l'environnement.

## Matériel

- JPG et GIF uniquement, 240x240. Un GIF de même nom n'est pas écrasé : noms alternés `…1.gif` / `…2.gif`.
- `/delete` répond parfois `Fail` alors que la suppression a lieu : vérifier via `/filelist` (cache d'environ 1 s).
- Pour toute question d'API sans doc officielle : s'appuyer sur les dépôts communautaires HelloCubic-Lite et qurle/smalltv.
