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

    def do_GET(self):
        # Pas encore de tableau de bord (relevé raté) : on explique pourquoi au lieu d'une page d'erreur.
        if self.path.split("?")[0] in ("/", "/tableau_de_bord.html") and not (ROOT / "tableau_de_bord.html").exists():
            try:
                journal = (ROOT / "journal.txt").read_text(errors="replace")[-3000:]
            except FileNotFoundError:
                journal = "(pas de journal)"
            import html
            body = f"""<!doctype html><meta charset="utf-8"><title>Ferme SFL</title>
<body style="font-family:system-ui;max-width:720px;margin:40px auto;padding:0 16px;background:#faf8f2;color:#222">
<h1>🌻 Le premier relevé n'a pas marché</h1>
<p>Vérifie ton <b>numéro de ferme</b> dans <code>ma_ferme.json</code> (seulement des chiffres, entre guillemets) et ta connexion internet, puis clique :</p>
<p><button onclick="this.disabled=true;this.textContent='Relevé en cours… (30 s à 1 min)';fetch('/actualiser',{{method:'POST'}}).then(r=>r.json()).then(j=>{{if(j.ok)location.reload();else{{alert(j.message);location.reload()}}}})" style="font-size:18px;padding:10px 18px">🔄 Réessayer</button></p>
<p>Message de l'outil (à envoyer si ça ne marche toujours pas) :</p><pre style="white-space:pre-wrap;background:#eee;padding:12px">{html.escape(journal)}</pre></body>""".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/":
            self.path = "/tableau_de_bord.html"
        return super().do_GET()

    def do_POST(self):
        if self.path != "/actualiser":
            self.send_error(404)
            return
        if not _lock.acquire(blocking=False):
            return self._json(409, {"ok": False, "message": "Un relevé est déjà en cours."})
        try:
            if (ROOT / "maj.py").exists():  # récupère d'abord la dernière version de l'outil
                subprocess.run([sys.executable, "-I", str(ROOT / "maj.py")], cwd=ROOT, capture_output=True, timeout=120)
            r = subprocess.run([sys.executable, "-I", str(ROOT / "releve_hebdo.py")],
                               cwd=ROOT, capture_output=True, text=True, timeout=600)
            ok = r.returncode == 0
            (ROOT / "journal.txt").write_text(r.stdout[-5000:] + "\n" + r.stderr[-5000:])
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
