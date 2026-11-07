#!/bin/bash
# Fait le relevé du jour, puis ouvre le tableau de bord avec le bouton « Actualiser » actif.
cd "$(dirname "$0")" || exit 1
python3 -I maj.py
python3 -I releve_hebdo.py 2>&1 | tee journal.txt
echo
echo "Ouverture du tableau de bord… (garde cette fenêtre ouverte pour que le bouton Actualiser marche)"
python3 -I serveur.py
