@echo off
cd /d "%~dp0"
python maj.py
python releve_hebdo.py
echo.
echo Ouverture du tableau de bord... (garde cette fenetre ouverte pour que le bouton Actualiser marche)
python serveur.py
