#!/bin/bash
# Installe (ou répare) le tableau de bord Sunflower Land sur Mac, sans blocage de macOS.
# Usage : bash -c "$(curl -fsSL https://raw.githubusercontent.com/Veayce0x3/tableau-de-bord-sfl/main/installer.sh)"
set -e
DEST="${DEST:-$HOME/Documents/Tableau-de-bord-SFL}"
ZIP_URL="https://github.com/Veayce0x3/tableau-de-bord-sfl/archive/refs/heads/main.zip"

echo "🌻 Installation du tableau de bord Sunflower Land"
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ Python 3 n'est pas installé. Installe-le depuis python.org, puis relance cette commande."
  exit 1
fi

mkdir -p "$DEST"
TMP="$DEST/.installation"
rm -rf "$TMP" && mkdir -p "$TMP"
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
chmod +x "$DEST/Lancer le relevé.command"

# Numéro de ferme
CUR="$(python3 -c "import json;print(json.load(open('$DEST/ma_ferme.json')).get('numero_de_ferme',''))" 2>/dev/null || true)"
if ! [[ "$CUR" =~ ^[0-9]+$ ]]; then
  while true; do
    read -r -p "👉 Ton numéro de ferme (le long nombre dans ton profil du jeu) : " NUM </dev/tty
    NUM="$(echo "$NUM" | tr -cd '0-9')"
    [ -n "$NUM" ] && break
    echo "Il faut seulement des chiffres, réessaie."
  done
  python3 - "$DEST/ma_ferme.json" "$NUM" <<'PY'
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

# Raccourci sur le Bureau
LANCEUR="$HOME/Desktop/Ferme SFL.command"
cat > "$LANCEUR" <<EOF
#!/bin/bash
cd "$DEST" && ./"Lancer le relevé.command"
EOF
chmod +x "$LANCEUR"

echo
echo "✅ Installé dans : $DEST"
echo "✅ Raccourci sur ton Bureau : « Ferme SFL » (double-clic chaque jour)"
echo
[ -n "$NOLAUNCH" ] && exit 0
echo "Premier relevé en cours…"
cd "$DEST" && ./"Lancer le relevé.command"
