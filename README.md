# Geek Magic Vibe

Dashboard pixel art pour écran **GeekMagic** (240x240, firmware GeekMagicClock / SmallTV-Ultra), piloté depuis un PC par Python, avec un backoffice local pour tout régler sans toucher au code.

*English: a pixel-art dashboard generator and local web backoffice for GeekMagic 240x240 smart displays (crypto cards, animated weather scenes, HTC Sense style clock). Not affiliated with GeekMagic.*

## Ce que ça affiche

- **Cryptos** : une card animée par token (pièce, variation 24 h, prix, sparkline réelle en fond, plus bas et plus haut du jour). Données Binance, secours CoinGecko.
- **Météo** : une scène pixel art plein cadre par lieu, qui change chaque jour parmi 12 décors du quotidien (ville, café, marché, pont, parc, aire de jeux, pique-nique, lac, montagnes, ferme, port, plage) et s'adapte au moment de la journée, à la météo et à la saison. Données Open-Meteo, aucune clé.
- **Horloge** style HTC Sense : tuiles à volets, date, météo animée dessous, effet d'entrée aléatoire.

## Démarrage rapide (Windows)

Prérequis : Python 3.11+, l'écran et le PC sur le même réseau local.

```bash
pip install -r requirements.txt
python scripts/setup_fonts.py              # polices pixel libres (OFL), 1re fois
copy config.example.json config.json       # puis renseignez l'IP de l'écran
python scripts/find_device.py --subnet 192.168.1   # retrouve l'écran et met config.json à jour
python scripts/send_test.py                # affiche "TEST OK" sur l'écran
```

Backoffice : double-cliquez sur `Lancer le backoffice.bat` (ou `python backoffice/server.py`), puis ouvrez http://localhost:8780. Il écoute aussi sur le réseau local (téléphone) et n'a **pas d'authentification** : ne l'exposez pas sur Internet.

## Mise à jour automatique

Deux tâches planifiées Windows (exemples) :

```bash
schtasks /Create /SC MINUTE /MO 9 /TN GeekMagicDashRefresh /TR "pythonw \"C:\chemin\geekmagic-dashboard\scripts\refresh_all.py\""
schtasks /Create /SC MINUTE /MO 1 /TN GeekMagicClock /TR "pythonw \"C:\chemin\geekmagic-dashboard\scripts\send_clock.py\""
```

`refresh_all.py` met à jour cryptos et météo selon la cadence et les créneaux du backoffice ; `send_clock.py` garde l'horloge à l'heure. Un verrou (`logs/device.lock`) évite que deux envois se chevauchent.

## Configuration

Tout est dans `config.json` (non versionné). `config.example.json` donne le schéma : écran (IP, cadence), tokens, lieux météo (3 max) et scènes actives, horloge (fuseau, mode nuit, effet), ordre et créneaux horaires de chaque card.

## Architecture

```
backoffice/        serveur FastAPI + interface HTML/JS sans build
geekmagic/
  client.py        client HTTP de l'écran (upload, thème, album, statut)
  pipeline.py      config -> GIF des cards actives -> écran (nettoyage inclus)
  settings.py      défauts, migration, validation, créneaux
  render.py        cards crypto et météo ; clock_sense.py : horloge
  scenes.py        moteur de scènes (ciel, particules, acteurs)
  places*.py       les 12 lieux ; transitions.py : effets d'entrée
scripts/           send_*.py, refresh_all.py, find_device.py, setup_fonts.py
```

## Ce qu'il faut savoir sur le matériel

- JPG et GIF uniquement, 240x240. Pas de PNG.
- Un GIF de même nom n'est **pas** écrasé par un nouvel upload : les fichiers alternent entre `…1.gif` et `…2.gif`.
- L'écran est mono-tâche : pas d'envois simultanés. Comptez environ une minute pour un envoi complet.
- Le préfixe numérique des fichiers (`01ck_…`, `03tk_…`) fixe l'ordre de rotation ; l'ordre de lecture par le firmware est à vérifier sur votre modèle.
- Mémoire limitée (environ 3 Mo) : chaque card météo ou horloge pèse environ 200 Ko.

## Crédits

- Protocole de l'écran : travaux communautaires [HelloCubic-Lite](https://github.com/GeekMagicClock/HelloCubic-Lite) et [smalltv](https://github.com/qurle/smalltv).
- Polices pixel : Press Start 2P et Silkscreen (SIL Open Font License), téléchargées par `setup_fonts.py`.
- Données : Binance, CoinGecko, Open-Meteo.

Licence MIT, voir `LICENSE`.
