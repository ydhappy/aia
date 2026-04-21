$ErrorActionPreference = 'Stop'

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
pyinstaller build/aia_windows.spec --clean --noconfirm
Write-Host 'Build complete. Output is under dist/'
