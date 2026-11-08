@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Tout est dans un bloc : la mise a jour peut remplacer ce fichier sans casser la suite.
(
  set "PY=py -3"
  py -3 -c "" >nul 2>&1 || set "PY=python"
  call :verifier
  call %%PY%% -X utf8 maj.py
  call %%PY%% -X utf8 releve_hebdo.py
  echo.
  echo Ouverture du tableau de bord... garde cette fenetre ouverte pour que le bouton Actualiser marche.
  call %%PY%% -X utf8 serveur.py
  exit /b
)
:verifier
%PY% -c "" >nul 2>&1 && exit /b 0
echo Python est introuvable. Relance la commande d'installation dans PowerShell.
pause
exit
