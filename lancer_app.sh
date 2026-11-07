#!/bin/bash
# Lancé par l'appli « Ferme SFL » : pas de fenêtre Terminal.
cd "$(dirname "$0")" || exit 1
URL="http://127.0.0.1:8765/tableau_de_bord.html"
PY="$(command -v python3 || echo /usr/bin/python3)"
# Serveur déjà lancé (depuis la dernière fois) : on ouvre juste la page.
if curl -fs -o /dev/null "$URL" 2>/dev/null; then
  open "$URL"; exit 0
fi
osascript -e 'display notification "Relevé de ta ferme en cours (30 s à 1 min)…" with title "Ferme SFL"' 2>/dev/null
"$PY" -I maj.py > journal.txt 2>&1
"$PY" -I releve_hebdo.py >> journal.txt 2>&1
nohup "$PY" -I serveur.py --sans-navigateur > /dev/null 2>&1 &
for i in 1 2 3 4 5 6 7 8 9 10; do
  curl -fs -o /dev/null "$URL" 2>/dev/null && break
  sleep 0.5
done
open "$URL"
