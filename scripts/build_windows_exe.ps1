$ErrorActionPreference = 'Stop'

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Write-Host 'Python runtime environment prepared.'
Write-Host 'Run local AIA with: python scripts/run_local_aia.py'
