#!/bin/bash
# Lancé par l'appli « Ferme SFL » : pas de fenêtre Terminal.
cd "$(dirname "$0")" || exit 1
URL="http://127.0.0.1:8765/tableau_de_bord.html"
# Un python3 qui marche vraiment (sur un Mac neuf, /usr/bin/python3 est vide sans les outils Apple)
PY=""
for p in /usr/local/bin/python3 /opt/homebrew/bin/python3 /Library/Frameworks/Python.framework/Versions/Current/bin/python3; do
  [ -x "$p" ] && "$p" -c '' >/dev/null 2>&1 && { PY="$p"; break; }
done
if [ -z "$PY" ]; then
  if xcode-select -p >/dev/null 2>&1; then PY=/usr/bin/python3
  else
    osascript -e 'display alert "Ferme SFL" message "Python est introuvable. Relance dans Terminal la commande donnée pour installer."' 2>/dev/null
    exit 1
  fi
fi
# Serveur déjà lancé (depuis la dernière fois) : on ouvre juste la page.
if curl -fs -o /dev/null "$URL" 2>/dev/null; then
  # Déjà lancé : mise à jour de l'outil + nouveau relevé, puis on ouvre la page
  osascript -e 'display notification "Mise à jour de tes données (30 s à 1 min)…" with title "Ferme SFL"' 2>/dev/null
  "$PY" -I maj.py > journal.txt 2>&1
  curl -fs -X POST "http://127.0.0.1:8765/actualiser" -o /dev/null --max-time 600
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
