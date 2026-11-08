"""Lanceur Windows (raccourci « Ferme SFL » du Bureau).

Mise à jour de l'outil, relevé du jour, puis ouverture du tableau de bord.
Affiche chaque étape ; en cas de problème, la fenêtre reste ouverte avec le message.
"""
import subprocess
import sys
import traceback
import urllib.request
import webbrowser
from pathlib import Path

ICI = Path(__file__).resolve().parent
PY = [sys.executable, "-I", "-X", "utf8"]
URL = "http://127.0.0.1:8765/tableau_de_bord.html"


def deja_lance():
    try:
        urllib.request.urlopen(URL, timeout=2)
        return True
    except Exception:
        return False


def attendre_entree():
    try:
        input("\nAppuie sur Entrée pour fermer cette fenêtre.")
    except Exception:
        pass


def main():
    print("=== Ferme SFL ===\n")
    if deja_lance():
        print("Le tableau de bord tourne déjà : mise à jour de tes données (30 s à 1 min)…")
        subprocess.run(PY + [str(ICI / "maj.py")], cwd=ICI)
        try:
            req = urllib.request.Request("http://127.0.0.1:8765/actualiser", data=b"", method="POST")
            urllib.request.urlopen(req, timeout=600)
        except Exception:
            pass
        webbrowser.open(URL)
        return
    print("1/3 Recherche d'une nouvelle version…")
    subprocess.run(PY + [str(ICI / "maj.py")], cwd=ICI)
    print("\n2/3 Relevé de ta ferme (30 s à 1 min, ne ferme pas cette fenêtre)…")
    r = subprocess.run(PY + [str(ICI / "releve_hebdo.py")], cwd=ICI)
    if r.returncode != 0:
        print("\n⚠️ Le relevé a eu un problème (message ci-dessus).")
    if not (ICI / "tableau_de_bord.html").exists():
        print("❌ Le tableau de bord n'a pas pu être créé. Fais une capture de cette fenêtre et envoie-la.")
        attendre_entree()
        return
    print("\n3/3 Ouverture du tableau de bord dans ton navigateur…")
    print("👉 Laisse cette fenêtre ouverte tant que tu utilises le tableau de bord (bouton 🔄 Actualiser).\n")
    s = subprocess.run(PY + [str(ICI / "serveur.py")], cwd=ICI)
    if s.returncode != 0:
        print("\n❌ Le serveur s'est arrêté (message ci-dessus). Fais une capture de cette fenêtre et envoie-la.")
        attendre_entree()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        print("\n❌ Erreur. Fais une capture de cette fenêtre et envoie-la.")
        attendre_entree()
