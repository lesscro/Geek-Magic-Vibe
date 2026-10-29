# Geek Magic Vibe

**English** | [Français](README.fr.md)

A pixel-art dashboard for **GeekMagic** 240x240 smart displays (GeekMagicClock / SmallTV-Ultra firmware), driven from a PC with Python, plus a local web backoffice to configure everything without touching code. Not affiliated with GeekMagic.

## Mini screens

Real rendering of the cards on the 240x240 display (looping animations):

<table>
<tr>
<td align="center"><img src="docs/screenshots/anim/crypto-btc.gif" width="200" alt="Crypto: BTC"><br><sub>Crypto: BTC</sub></td>
<td align="center"><img src="docs/screenshots/anim/weather-city.gif" width="200" alt="City, full daylight"><br><sub>City, full daylight</sub></td>
<td align="center"><img src="docs/screenshots/anim/weather-cafe-night.gif" width="200" alt="Café at night"><br><sub>Café at night</sub></td>
<td align="center"><img src="docs/screenshots/anim/weather-park-snow.gif" width="200" alt="Park in the snow"><br><sub>Park in the snow</sub></td>
</tr>
<tr>
<td align="center"><img src="docs/screenshots/anim/weather-harbor-rain.gif" width="200" alt="Harbor in the rain"><br><sub>Harbor in the rain</sub></td>
<td align="center"><img src="docs/screenshots/anim/weather-beach.gif" width="200" alt="Sunny beach"><br><sub>Sunny beach</sub></td>
<td align="center"><img src="docs/screenshots/anim/weather-bridge-dusk.gif" width="200" alt="Bridge at dusk"><br><sub>Bridge at dusk</sub></td>
<td align="center"><img src="docs/screenshots/anim/clock.gif" width="200" alt="HTC Sense clock"><br><sub>HTC Sense clock</sub></td>
</tr>
</table>

## What it shows

- **Crypto**: one animated card per token (spinning coin, 24 h change, price, a real sparkline as background, day low and high). Data from Binance, CoinGecko as fallback.
- **Weather**: a full-frame pixel-art scene per place, changing every day among 12 everyday settings (city, café, market, bridge, park, playground, picnic, lake, mountains, farm, harbor, beach), adapted to the time of day, the weather and the season. Data from Open-Meteo, no API key.
- **Clock**, HTC Sense style: flip tiles, date, animated weather below, random entry effect.

## Screenshots

Cards as they appear on the display (shown at 2x):

![Crypto cards](docs/screenshots/cards-crypto.png)

![Daytime weather scenes](docs/screenshots/cards-weather-day.png)

![Weather scenes by time of day and weather](docs/screenshots/cards-weather-moments.png)

![HTC Sense clock](docs/screenshots/card-clock.png)

The backoffice (available in English and French):

![Backoffice, overview](docs/screenshots/backoffice-overview.png)

![Backoffice, crypto](docs/screenshots/backoffice-crypto.png)

![Backoffice, weather and simulator](docs/screenshots/backoffice-weather.png)

![Backoffice, clock](docs/screenshots/backoffice-clock.png)

To regenerate the screenshots and mini screens: `python scripts/make_screenshots.py`, then `python scripts/make_screenshots.py --gifs`.

## Install in 3 steps (Windows)

Requirements: [Python 3.11+](https://www.python.org/downloads/) (tick "Add Python to PATH"), Git, and the display powered on and connected to the same Wi-Fi or Ethernet network as the PC.

```bash
git clone https://github.com/lesscro/Geek-Magic-Vibe.git
cd Geek-Magic-Vibe
Installer.bat          # or: python setup.py
```

The installer does everything: virtual environment, dependencies, free pixel fonts, `config.json`, automatic discovery of the display on your network, and (if you accept) the scheduled update tasks. At the end it offers to open the backoffice.

Day to day: double-click **`Lancer le backoffice.bat`**, then open http://localhost:8780. Set your tokens, places and time slots, check the preview, click **Send to screen**.

macOS and Linux: `python setup.py --no-scan`, then `.venv/bin/python backoffice/server.py` (scheduled tasks are Windows-only).

If the display is not found, enter its IP in the backoffice (Screen and schedule page) or run `python scripts/find_device.py`. The display must be on the same subnet as the PC.

The backoffice and the texts drawn on the display are available in **English (default) and French**: change the language on the Screen and schedule page. To add a language, see [Translating](#translating).

## What each item is for

| Item | Purpose |
|---|---|
| `Installer.bat`, `setup.py` | Guided install, run once. |
| `Lancer le backoffice.bat` | Starts the local server and opens the interface. |
| `config.example.json` | Configuration template. `config.json` (your copy, never committed) holds your IP, tokens and places. |
| `backoffice/` | The web interface (FastAPI server + plain HTML/JS page). |
| `geekmagic/` | The engine: card drawing, weather scenes, clock, sending to the display. |
| `scripts/` | Commands: send cards, automatic update, discover the display, test, fonts. |
| `fonts/`, `output/`, `logs/`, `.venv/` | Created at install or use, not committed. |
| `docs/` | Design notes (`DESIGN.md`, `PRODUCT.md`, French versions with `.fr`). |
| `CLAUDE.md` | Guidance for contributors using Claude Code (optional, no effect on usage). |

## Automatic updates

Two Windows scheduled tasks:

```bash
# done by the installer; by hand (adapt the path):
schtasks /Create /SC MINUTE /MO 9 /TN GeekMagicDashRefresh /TR "\"C:\path\.venv\Scripts\pythonw.exe\" \"C:\path\scripts\refresh_all.py\""
schtasks /Create /SC MINUTE /MO 1 /TN GeekMagicClock /TR "\"C:\path\.venv\Scripts\pythonw.exe\" \"C:\path\scripts\send_clock.py\""
```

`refresh_all.py` updates crypto and weather according to the pace and time slots set in the backoffice; `send_clock.py` keeps the clock on time. A lock (`logs/device.lock`) prevents two sends from overlapping.

## Configuration

Everything lives in `config.json` (not committed). `config.example.json` shows the schema: language, display (IP, pace), tokens, weather places (3 max) and active scenes, clock (time zone, night mode, effect), order and time slots of each card.

## Architecture

```
backoffice/        FastAPI server + plain HTML/JS interface (no build step)
  static/i18n/     interface translations (fr.json, en.json)
geekmagic/
  client.py        HTTP client for the display (upload, theme, album, status)
  pipeline.py      config -> GIFs of the active cards -> display (with cleanup)
  settings.py      defaults, migration, validation, time slots
  i18n.py          texts drawn on the display (conditions, dates)
  render.py        crypto and weather cards; clock_sense.py: clock
  scenes.py        scene engine (sky, particles, actors)
  places*.py       the 12 places; transitions.py: entry effects
scripts/           send_*.py, refresh_all.py, find_device.py, setup_fonts.py
setup.py           guided install
```

## Translating

- **Backoffice**: English is the source language. Copy `backoffice/static/i18n/fr.json` to `<code>.json` and translate the values (the keys are the English texts, `{name}`-style placeholders must stay).
- **Texts on the display**: add your language code to `LANGS` in `geekmagic/i18n.py` and fill the condition, day and month tables. Press Start 2P has no accents, so card labels are uppercase without accents.
- Add the language to the chooser in `pageScreen()` (`backoffice/static/app.js`) and to `validate()` in `geekmagic/settings.py`.

## Hardware notes

- JPG and GIF only, 240x240. No PNG.
- A GIF with the same name is **not** overwritten by a new upload: files alternate between `…1.gif` and `…2.gif`.
- The display handles one request at a time: no simultaneous sends. A full send takes about a minute.
- The numeric prefix of file names (`01ck_…`, `03tk_…`) sets the rotation order; check the playback order on your model.
- Limited memory (about 3 MB): each weather or clock card is about 200 KB.

## Credits

- Display protocol: community work from [HelloCubic-Lite](https://github.com/GeekMagicClock/HelloCubic-Lite) and [smalltv](https://github.com/qurle/smalltv).
- Pixel fonts: Press Start 2P and Silkscreen (SIL Open Font License), downloaded by `setup_fonts.py`.
- Data: Binance, CoinGecko, Open-Meteo.

MIT license, see `LICENSE`.
