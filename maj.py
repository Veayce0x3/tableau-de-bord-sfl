"""Mise à jour automatique de l'outil depuis GitHub.

Remplace seulement les fichiers du programme. Ne touche jamais à tes données
(dossier donnees/, releves/) ni à tes réglages (ma_ferme.json, objectifs.json).
Sans internet ou si GitHub ne répond pas, l'outil continue avec la version actuelle.
"""
import json
import sys
import urllib.request
from pathlib import Path

DEPOT = "https://raw.githubusercontent.com/Veayce0x3/tableau-de-bord-sfl/main/"
ICI = Path(__file__).resolve().parent
JAMAIS = {"ma_ferme.json", "objectifs.json"}


def lire(url):
    req = urllib.request.Request(url, headers={"User-Agent": "tableau-de-bord-sfl"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def main():
    try:
        locale = json.loads((ICI / "version.json").read_text()).get("version", "")
    except Exception:
        locale = ""
    try:
        distante = json.loads(lire(DEPOT + "version.json"))
    except Exception:
        print("(Mise à jour : impossible de vérifier, on continue avec la version actuelle.)")
        return
    if distante.get("version") == locale:
        print(f"Outil à jour (version {locale}).")
        return
    nouveaux = {}
    try:
        for nom in distante.get("fichiers", []):
            if nom in JAMAIS or "/" in nom or "\\" in nom or nom.startswith("."):
                continue
            nouveaux[nom] = lire(DEPOT + urllib.request.quote(nom))
    except Exception:
        print("(Mise à jour interrompue, rien n'a été changé.)")
        return
    for nom, contenu in nouveaux.items():  # tout est téléchargé avant de remplacer quoi que ce soit
        tmp = ICI / (nom + ".tmp")
        tmp.write_bytes(contenu)
        cible = ICI / nom
        if cible.exists():
            tmp.chmod(cible.stat().st_mode)  # garde le double-clic possible sur Mac
        elif nom.endswith(".command"):
            tmp.chmod(0o755)
        tmp.replace(cible)
    (ICI / "version.json").write_text(json.dumps(distante, ensure_ascii=False, indent=1))
    print(f"✅ Outil mis à jour : version {distante.get('version')}. {distante.get('nouveautes', '')}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"(Mise à jour ignorée : {e})", file=sys.stderr)
