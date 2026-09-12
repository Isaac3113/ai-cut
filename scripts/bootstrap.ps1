param([switch]$ASR, [string]$Python)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $Python) {
    $bundled = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $bundled) { $Python = $bundled }
    else { $Python = (Get-Command python -ErrorAction Stop).Source }
}
& $Python -X utf8 (Join-Path $PSScriptRoot 'bootstrap_runtime.py') --root $projectRoot
if ($LASTEXITCODE -ne 0) { throw 'Runtime bootstrap failed' }
$venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
& $venvPython -m pip install --disable-pip-version-check -e $projectRoot
if ($LASTEXITCODE -ne 0) { throw 'Core dependency install failed' }
if ($ASR) {
    & $venvPython -m pip install --disable-pip-version-check -r (Join-Path $projectRoot 'requirements.lock.txt') --extra-index-url https://download.pytorch.org/whl/cu128
    if ($LASTEXITCODE -ne 0) { throw 'ASR dependency install failed' }
}
& $venvPython -m talking_head_editor.cli doctor
if ($LASTEXITCODE -ne 0) { throw 'Doctor failed' }
