"""Client HTTP pour les écrans GeekMagic (SmallTV-Ultra, firmware Crypto-V15).

Endpoints validés sur le device réel (2026-10-28) :

- POST /doUpload?dir=/image   (multipart, champ "file")  -> upload (JPG/GIF seulement, PAS de PNG)
- GET  /set?theme=3                                       -> basculer sur le thème Photo Album
- GET  /set?autoplay=1&i_i=5                               -> cycle album toutes les 5 s
- GET  /delete?file=image/<NOM>                            -> suppression (répond parfois 'Fail' alors que ça marche — toujours vérifier /filelist)
- GET  /filelist?dir=/image                                -> liste (HTML)
- GET  /space.json                                         -> espace libre {"total","free"}
- GET  /config.json                                        -> {"a": SSID, "p": "****"} (sonde de présence)
- GET  /album.json, /app.json, /v.json                     -> état album / thème / version

Affichage : ce firmware n'a PAS de /set?img= (répond FAIL). L'écran affiche
les fichiers de /image via le cycle automatique du thème 3 (Photo Album).
Pusher une image = upload JPG écrasant un nom constant ; l'écran la recharge
au cycle suivant (i_i secondes).
"""

from __future__ import annotations

import os

import requests


class GeekMagicError(RuntimeError):
    """Erreur de communication avec l'écran GeekMagic."""


class GeekMagicClient:
    def __init__(self, ip: str, timeout: float = 10.0):
        self.base = f"http://{ip}"
        self.timeout = timeout

    # ---------------------------------------------------------------- infra

    def _get(self, path: str, **kwargs) -> requests.Response:
        try:
            r = requests.get(self.base + path, timeout=self.timeout, **kwargs)
        except requests.RequestException as exc:
            raise GeekMagicError(f"Injoignable {self.base}{path} : {exc}") from exc
        if r.status_code != 200:
            raise GeekMagicError(f"HTTP {r.status_code} sur {path} : {r.text[:200]}")
        return r

    def reachable(self) -> bool:
        """True si l'écran répond (ping HTTP léger).

        /spaces.json n'existe pas sur tous les firmwares (404 observé) ;
        /config.json est servi par le nôtre.
        """
        try:
            self._get("/config.json")
            return True
        except GeekMagicError:
            return False

    # --------------------------------------------------------------- images

    def upload(self, filepath: str, directory: str = "/image", name: str | None = None) -> str:
        """Upload un fichier (image ou GIF) sur l'écran. Retourne le nom distant.

        NB : le firmware renvoie parfois deux Content-Length incohérents ->
        http.client brut au lieu de requests (qui lève InvalidHeader).
        """
        import http.client
        import uuid
        name = name or os.path.basename(filepath)
        with open(filepath, "rb") as fh:
            data = fh.read()
        boundary = uuid.uuid4().hex
        body = (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
            f'filename="{name}"\r\nContent-Type: application/octet-stream\r\n\r\n'
        ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
        host = self.base.split("//", 1)[1]
        try:
            conn = http.client.HTTPConnection(host, timeout=self.timeout)
            conn.request(
                "POST", f"{directory and '/doUpload?dir=' + directory}",
                body=body,
                headers={
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                    "Content-Length": str(len(body)),
                },
            )
            resp = conn.getresponse()
            text = resp.read().decode("utf-8", "replace")
            status = resp.status
            conn.close()
        except OSError as exc:
            raise GeekMagicError(f"Upload impossible vers {self.base} : {exc}") from exc
        if status != 200 or "FAIL" in text.upper():
            raise GeekMagicError(f"Upload refused (HTTP {status}): {text[:200]}")
        return name

    def set_theme(self, n: int) -> None:
        """Change le thème (3 = Photo Album, requis pour afficher nos images)."""
        r = self._get("/set", params={"theme": n})
        if "OK" not in r.text.upper():
            raise GeekMagicError(f"Theme change {n} refused: {r.text[:100]}")

    def set_album(self, autoplay: bool = True, interval_s: int = 5) -> None:
        """Configure le cycle du Photo Album."""
        r = self._get("/set", params={"autoplay": int(autoplay), "i_i": interval_s})
        if "OK" not in r.text.upper():
            raise GeekMagicError(f"Album configuration refused: {r.text[:100]}")

    def delete(self, name: str, directory: str = "image") -> None:
        """Supprime un fichier. NB : réponse 'Fail' peu fiable — vérifier /filelist."""
        self._get("/delete", params={"file": f"{directory}/{name}"})

    def push_image(self, filepath: str, name: str = "dashboard.jpg") -> None:
        """Upload un JPG (écrase le nom donné) — l'écran l'affiche au cycle suivant.

        Le PNG n'est pas supporté par le firmware ; convertir avant si besoin.
        """
        if filepath.lower().endswith(".png"):
            raise GeekMagicError("PNG is not supported by the firmware: convert to JPG first.")
        self.upload(filepath, "/image", name)

    # ---------------------------------------------------------------- statut

    def free_space(self) -> dict:
        """Espace disque du device : {"total": ..., "free": ...} (octets)."""
        r = self._get("/space.json")
        try:
            return r.json()
        except ValueError as exc:
            raise GeekMagicError(f"Non-JSON response from /space.json: {r.text[:200]}") from exc

    def status(self, key: str = "config") -> dict:
        """Lit un des fichiers d'état (/config.json, /spaces.json, ...)."""
        r = self._get(f"/{key}.json")
        try:
            return r.json()
        except ValueError as exc:
            raise GeekMagicError(f"Non-JSON response from /{key}.json: {r.text[:200]}") from exc

    def list_images(self) -> str:
        """Liste les images présentes (réponse HTML brute du firmware)."""
        return self._get("/filelist", params={"dir": "/image"}).text
