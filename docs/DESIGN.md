# DESIGN

[English](DESIGN.md) | [Français](DESIGN.fr.md)

Principle: **information first, scenery second.** Every card reads in under two seconds; the pixel art gives character without ever getting in front of the message.

## Display constraints

| Constraint | Consequence |
|---|---|
| 240x240 LED | Legible text from 8 px (labels), 16 to 24 px for values, 40 px for a hero. |
| Quantized GIF (64 to 128 colors) | Gradients in sharp bands, short palettes per area. |
| Card shown about 10 s per rotation | One hero per card, everything else aligns around it. |
| Pixel perfect | Integer zoom, nearest neighbor, no anti-aliasing on sprites. |
| Memory (about 3 MB) | Crypto cards 10 KB, weather and clock about 200 KB each. |

## Cards

- **Crypto**: small centered coin and name, 24 h change as the hero, price right below, a real sparkline as a gradient area in the background, day low and high at the bottom with a dark outline for legibility.
- **Weather**: full-frame scene in perspective (sky, setting, animated actors), icon, condition and a giant temperature in the center with an outline. The scene depends on the day (rotation), the time of day, the weather and the season.
- **Clock**: HTC Sense style, glossy black flip tiles, date, animated weather. Non-looping GIF: entry effect, flip of the digit that changes, a discreet glint, then the final frame is held.

## Animation

All loops are closed (sine, ping-pong, modulo scroll) so nothing jumps when the GIF restarts. The firmware applies its own fade between album images; entry effects are therefore baked into the GIF and reserved for non-looping GIFs.

## Languages

English by default, French included. Texts on the display come from `geekmagic/i18n.py`, the interface from `backoffice/static/i18n/`. See the README, section Translating.

## Backoffice

Product context in `docs/PRODUCT.md`. Dark cockpit, Material 3 Expressive: very rounded shapes, neutrals tinted toward midnight blue, amber as the primary action, faithful preview before every send.
