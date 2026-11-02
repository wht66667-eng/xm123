$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
Push-Location -LiteralPath $taskRoot
try {
  python -m pip install -r desktop/requirements.txt
  if ($LASTEXITCODE -ne 0) { throw 'Dependencies failed' }
  pyinstaller --noconfirm --distpath desktop --workpath test-artifacts/pet-build desktop/fox-pet.spec
  if ($LASTEXITCODE -ne 0) { throw 'Desktop build failed' }
  python test/frozen-check.py
  if ($LASTEXITCODE -ne 0) { throw 'Packaged EXE verification failed' }
  npx --yes @vscode/vsce package --allow-missing-repository --no-dependencies
  if ($LASTEXITCODE -ne 0) { throw 'VSIX build failed' }
} finally { Pop-Location }
