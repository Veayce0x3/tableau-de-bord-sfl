# Installe (ou repare) le tableau de bord Sunflower Land sur Windows.
# Usage (une ligne, dans PowerShell) :
#   irm https://raw.githubusercontent.com/Veayce0x3/tableau-de-bord-sfl/main/installer.ps1 | iex
# Textes sans accents : PowerShell les affiche mal selon les PC.

& {
  $ErrorActionPreference = 'Stop'
  $ProgressPreference = 'SilentlyContinue'   # telechargements beaucoup plus rapides
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

  $PyVersion = '3.12.8'
  $PyUrl = "https://www.python.org/ftp/python/$PyVersion/python-$PyVersion-amd64.exe"
  $ZipUrl = 'https://github.com/Veayce0x3/tableau-de-bord-sfl/archive/refs/heads/main.zip'
  $Docs = [Environment]::GetFolderPath('MyDocuments')
  $Dest = Join-Path $Docs 'Tableau-de-bord-SFL'

  # Un Python qui marche vraiment (le "python" de Windows ouvre souvent juste le Microsoft Store)
  function Trouver-Python {
    $cands = @(
      "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
      "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
      "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
      "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
      "$env:ProgramFiles\Python313\python.exe",
      "$env:ProgramFiles\Python312\python.exe",
      "$env:ProgramFiles\Python311\python.exe"
    )
    foreach ($c in $cands) {
      if (Test-Path $c) { return $c }
    }
    foreach ($cmd in @('py', 'python')) {
      try {
        $exe = & $cmd -c "import sys; print(sys.executable if sys.version_info >= (3, 9) else '')" 2>$null
        if ($LASTEXITCODE -eq 0 -and $exe -and (Test-Path $exe.Trim())) { return $exe.Trim() }
      } catch {}
    }
    return $null
  }

  Write-Host ''
  Write-Host '=== Installation du tableau de bord Sunflower Land ===' -ForegroundColor Yellow

  $Py = Trouver-Python
  if (-not $Py) {
    Write-Host ''
    Write-Host 'Python n est pas encore sur ce PC : telechargement (environ 25 Mo)...'
    $exe = Join-Path $env:TEMP "python-$PyVersion.exe"
    Invoke-WebRequest -Uri $PyUrl -OutFile $exe -UseBasicParsing
    Write-Host 'Installation de Python (1 a 2 minutes, rien a cliquer)...'
    $p = Start-Process -FilePath $exe -ArgumentList '/quiet', 'InstallAllUsers=0', 'PrependPath=1', 'Include_launcher=1', 'InstallLauncherAllUsers=0', 'Include_test=0' -Wait -PassThru
    Remove-Item $exe -ErrorAction SilentlyContinue
    $Py = Trouver-Python
    if (-not $Py) {
      Write-Host "Python n a pas pu s installer (code $($p.ExitCode)). Installe-le depuis python.org (coche 'Add Python to PATH'), puis relance la meme ligne." -ForegroundColor Red
      return
    }
    Write-Host 'Python est installe.' -ForegroundColor Green
  }

  Write-Host 'Telechargement de l outil...'
  New-Item -ItemType Directory -Force -Path $Dest | Out-Null
  $Tmp = Join-Path $env:TEMP ('sfl-' + [guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
  $Zip = Join-Path $Tmp 'outil.zip'
  Invoke-WebRequest -Uri $ZipUrl -OutFile $Zip -UseBasicParsing
  Expand-Archive -Path $Zip -DestinationPath $Tmp -Force
  $Src = Get-ChildItem -Path $Tmp -Directory | Where-Object { $_.Name -like 'tableau-de-bord-sfl-*' } | Select-Object -First 1
  foreach ($f in Get-ChildItem -Path $Src.FullName -Force) {
    # Ne jamais ecraser tes reglages s ils existent deja
    if (($f.Name -eq 'ma_ferme.json' -or $f.Name -eq 'objectifs.json') -and (Test-Path (Join-Path $Dest $f.Name))) { continue }
    Copy-Item -Path $f.FullName -Destination $Dest -Recurse -Force
  }
  Remove-Item $Tmp -Recurse -Force -ErrorAction SilentlyContinue
  # Fichiers venus d internet : on enleve le blocage de Windows
  Get-ChildItem -Path $Dest -Recurse -File | Unblock-File -ErrorAction SilentlyContinue

  # Numero de ferme
  $Cfg = Join-Path $Dest 'ma_ferme.json'
  $Cur = ''
  try { $Cur = [string](Get-Content $Cfg -Raw -Encoding UTF8 | ConvertFrom-Json).numero_de_ferme } catch {}
  if ($Cur -notmatch '^[0-9]+$') {
    $Num = ''
    while (-not $Num) {
      Write-Host ''
      $Num = (Read-Host 'Ton numero de ferme (le long nombre dans ton profil du jeu), puis Entree') -replace '[^0-9]', ''
      if (-not $Num) { Write-Host 'Il faut seulement des chiffres, reessaie.' }
    }
    $Script = Join-Path $env:TEMP 'sfl_numero.py'
    Set-Content -Path $Script -Encoding ASCII -Value @'
import json, sys
p, n = sys.argv[1], sys.argv[2]
try:
    c = json.load(open(p, encoding="utf-8"))
except Exception:
    c = {}
c["numero_de_ferme"] = n
c.setdefault("nft_a_suivre", [])
json.dump(c, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
'@
    & $Py $Script $Cfg $Num
    Remove-Item $Script -ErrorAction SilentlyContinue
  }

  # Raccourci "Ferme SFL" sur le Bureau
  $Bat = Get-ChildItem -Path $Dest -Filter 'Lancer le relev*.bat' | Select-Object -First 1
  $Desktop = [Environment]::GetFolderPath('Desktop')
  $Lnk = Join-Path $Desktop 'Ferme SFL.lnk'
  $sh = New-Object -ComObject WScript.Shell
  $s = $sh.CreateShortcut($Lnk)
  $s.TargetPath = $Bat.FullName
  $s.WorkingDirectory = $Dest
  $s.Description = 'Tableau de bord Sunflower Land'
  $s.Save()

  Write-Host ''
  Write-Host "Installe dans : $Dest" -ForegroundColor Green
  Write-Host 'Raccourci sur ton Bureau : "Ferme SFL" (double-clic chaque jour)' -ForegroundColor Green
  Write-Host ''
  Write-Host 'Premier releve en cours : une fenetre noire s ouvre, puis le tableau de bord dans ton navigateur (30 s a 1 min).'
  Write-Host 'Laisse la fenetre noire ouverte tant que tu utilises le tableau de bord.'
  Start-Process -FilePath $Bat.FullName -WorkingDirectory $Dest
}
