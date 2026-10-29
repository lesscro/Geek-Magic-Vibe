"""Textes affichés sur l'écran selon la langue (config.json > language).

Pour ajouter une langue : ajouter son code à LANGS et une entrée dans chaque
table ci-dessous (conditions, jours, mois, format de date). Les textes de
l'interface web sont dans backoffice/static/i18n/<langue>.json.

Press Start 2P n'a pas les accents : les libellés des cards sont en majuscules
sans accents.
"""

from __future__ import annotations

LANGS = ("en", "fr")
DEFAULT = "en"

_lang = DEFAULT


def use(lang: str | None) -> str:
    """Choisit la langue des textes rendus (appelé par le pipeline et les aperçus)."""
    global _lang
    _lang = lang if lang in LANGS else DEFAULT
    return _lang


def current() -> str:
    return _lang


CONDITIONS = {
    "en": {"SUN": "SUNNY", "MOON": "CLEAR NIGHT", "PARTLY": "PARTLY CLOUDY", "CLOUD": "OVERCAST",
           "RAIN": "RAIN", "STORM": "STORM", "SNOW": "SNOW", "FOG": "FOG"},
    "fr": {"SUN": "ENSOLEILLE", "MOON": "NUIT CLAIRE", "PARTLY": "ECLAIRCIES", "CLOUD": "COUVERT",
           "RAIN": "PLUIE", "STORM": "ORAGE", "SNOW": "NEIGE", "FOG": "BROUILLARD"},
}

DAYS = {
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "fr": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
}
MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
           "septembre", "octobre", "novembre", "décembre"],
}


def condition(icon: str) -> str:
    return CONDITIONS[_lang].get(icon, icon)


def date_label(now) -> str:
    """« Thursday, October 29 » / « jeudi 29 octobre »."""
    day, month = DAYS[_lang][now.weekday()], MONTHS[_lang][now.month - 1]
    return f"{day}, {month} {now.day}" if _lang == "en" else f"{day} {now.day} {month}"
