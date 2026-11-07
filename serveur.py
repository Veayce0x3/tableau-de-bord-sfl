#!/usr/bin/env python3
"""Petit serveur local pour le tableau de bord (uniquement sur ton ordinateur).

- Sert les fichiers du dossier sur http://127.0.0.1:8765/
- POST /actualiser : lance le relevé, puis le tableau de bord se recharge.

Usage : python3 serveur.py   (les lanceurs le font pour toi)
"""
import http.server
import json
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 8765
URL = f"http://127.0.0.1:{PORT}/tableau_de_bord.html"
_lock = threading.Lock()


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT), **k)

    def log_message(self, *a):  # silencieux
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_POST(self):
        if self.path != "/actualiser":
            self.send_error(404)
            return
        if not _lock.acquire(blocking=False):
            return self._json(409, {"ok": False, "message": "Un relevé est déjà en cours."})
        try:
            r = subprocess.run([sys.executable, "-I", str(ROOT / "releve_hebdo.py")],
                               cwd=ROOT, capture_output=True, text=True, timeout=600)
            ok = r.returncode == 0
            msg = "Données mises à jour." if ok else (r.stderr.strip().splitlines() or ["Erreur inconnue"])[-1]
            self._json(200 if ok else 500, {"ok": ok, "message": msg})
        except subprocess.TimeoutExpired:
            self._json(504, {"ok": False, "message": "Le relevé a pris trop de temps, réessaie plus tard."})
        finally:
            _lock.release()

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    try:
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        # Déjà lancé : on ouvre juste la page.
        webbrowser.open(URL)
        return
    print(f"Tableau de bord : {URL}\n(ferme cette fenêtre pour arrêter)")
    if "--sans-navigateur" not in sys.argv:
        webbrowser.open(URL)
    srv.serve_forever()


if __name__ == "__main__":
    main()
