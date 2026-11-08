#!/bin/bash
# Installe (ou répare) le tableau de bord Sunflower Land sur Mac, sans blocage de macOS.
# Usage (une ligne, dans Terminal) :
#   curl -fsSL https://raw.githubusercontent.com/Veayce0x3/tableau-de-bord-sfl/main/installer.sh | bash
# Tout est dans main() : bash lit le script en entier avant de le lancer.

PY_VERSION="3.12.8"
PY_PKG_URL="https://www.python.org/ftp/python/$PY_VERSION/python-$PY_VERSION-macos11.pkg"

# Un python3 qui marche vraiment (sur un Mac neuf, /usr/bin/python3 est une coquille vide
# tant que les outils Apple ne sont pas installés).
trouver_python() {
  local p
  for p in /usr/local/bin/python3 /opt/homebrew/bin/python3 \
           /Library/Frameworks/Python.framework/Versions/Current/bin/python3; do
    if [ -x "$p" ] && "$p" -c 'import sys; sys.exit(sys.version_info < (3, 9))' >/dev/null 2>&1; then
      echo "$p"; return 0
    fi
  done
  # Le python3 d'Apple, seulement si ses outils sont installés (sinon il ouvre une fenêtre)
  if xcode-select -p >/dev/null 2>&1 && /usr/bin/python3 -c 'import sys; sys.exit(sys.version_info < (3, 9))' >/dev/null 2>&1; then
    echo /usr/bin/python3; return 0
  fi
  return 1
}

installer_python() {
  echo
  echo "🐍 Python n'est pas encore sur ton Mac : je le télécharge (≈ 45 Mo)…"
  local pkg="$HOME/Downloads/python-$PY_VERSION.pkg"
  mkdir -p "$HOME/Downloads"
  if ! curl -fL --progress-bar "$PY_PKG_URL" -o "$pkg"; then
    echo "❌ Téléchargement impossible. Vérifie ta connexion internet, puis relance la même ligne."
    exit 1
  fi
  open "$pkg"
  echo
  echo "👉 Une fenêtre « Installer Python » vient de s'ouvrir."
  echo "   Clique sur Continuer → Continuer → Accepter → Installer (ton mot de passe du Mac est demandé)."
  echo "   Quand c'est fini, ferme cette fenêtre (tu peux mettre le fichier à la corbeille)."
  echo
  echo "⏳ J'attends la fin de l'installation de Python…"
  local i
  for i in $(seq 1 600); do
    PY="$(trouver_python)" && { echo "✅ Python est installé."; rm -f "$pkg"; return 0; }
    sleep 2
  done
  echo "❌ Python n'a pas été installé. Relance la même ligne pour réessayer."
  exit 1
}

main() {
  set -e
  DEST="${DEST:-$HOME/Documents/Tableau-de-bord-SFL}"
  ZIP_URL="https://github.com/Veayce0x3/tableau-de-bord-sfl/archive/refs/heads/main.zip"

  echo "🌻 Installation du tableau de bord Sunflower Land"
  PY="$(trouver_python)" || installer_python

  mkdir -p "$DEST"
  TMP="$DEST/.installation"
  rm -rf "$TMP" && mkdir -p "$TMP"
  echo "📦 Téléchargement de l'outil…"
  curl -fsSL "$ZIP_URL" -o "$TMP/outil.zip"
  ditto -x -k "$TMP/outil.zip" "$TMP"
  SRC="$(find "$TMP" -maxdepth 1 -type d -name 'tableau-de-bord-sfl-*' | head -1)"
  for f in "$SRC"/*; do
    name="$(basename "$f")"
    # Ne jamais écraser tes réglages s'ils existent déjà
    if [ "$name" = "ma_ferme.json" ] || [ "$name" = "objectifs.json" ]; then
      [ -e "$DEST/$name" ] && continue
    fi
    cp -R "$f" "$DEST/"
  done
  rm -rf "$TMP"
  chmod +x "$DEST/Lancer le relevé.command" "$DEST/lancer_app.sh"

  # Numéro de ferme
  CUR="$("$PY" -c "import json,sys;print(json.load(open(sys.argv[1])).get('numero_de_ferme',''))" "$DEST/ma_ferme.json" 2>/dev/null || true)"
  if ! [[ "$CUR" =~ ^[0-9]+$ ]]; then
    NUM="$(echo "${NUMERO:-}" | tr -cd '0-9')"
    while [ -z "$NUM" ]; do
      echo
      read -r -p "👉 Ton numéro de ferme (le long nombre dans ton profil du jeu), puis Entrée : " NUM </dev/tty
      NUM="$(echo "$NUM" | tr -cd '0-9')"
      [ -z "$NUM" ] && echo "Il faut seulement des chiffres, réessaie."
    done
    "$PY" - "$DEST/ma_ferme.json" "$NUM" <<'PY'
import json, sys
p, n = sys.argv[1], sys.argv[2]
try:
    c = json.load(open(p))
except Exception:
    c = {}
c["numero_de_ferme"] = n
c.setdefault("nft_a_suivre", [])
json.dump(c, open(p, "w"), ensure_ascii=False, indent=2)
PY
  fi

  # Appli « Ferme SFL » sur le Bureau : double-clic, pas de Terminal
  mkdir -p "$HOME/Desktop"
  rm -f "$HOME/Desktop/Ferme SFL.command"
  APP="$HOME/Desktop/Ferme SFL.app"
  rm -rf "$APP"
  osacompile -o "$APP" -e "do shell script quoted form of \"$DEST/lancer_app.sh\" & \" > /dev/null 2>&1 &\"" >/dev/null 2>&1

  echo
  echo "✅ Installé dans : $DEST"
  echo "✅ Appli sur ton Bureau : « Ferme SFL » (double-clic chaque jour, pas besoin du Terminal)"
  echo
  [ -n "${NOLAUNCH:-}" ] && exit 0
  echo "Premier relevé en cours… le tableau de bord va s'ouvrir dans ton navigateur (30 s à 1 min)."
  "$DEST/lancer_app.sh" </dev/null
  echo "✅ Terminé. Tu peux fermer cette fenêtre. La prochaine fois : double-clic sur « Ferme SFL » sur ton Bureau."
}

main "$@"
