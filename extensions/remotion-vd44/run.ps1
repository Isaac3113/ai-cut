param(
 [ValidateSet('Install','Check','Render','Preview')][string]$Action='Check',
 [ValidateSet('CustomerJourney','PresenterEnding')][string]$Composition='CustomerJourney',
 [string]$NodePath='',
 [string]$NpmCli='',
 [string]$BrowserPath='C:\Program Files\Google\Chrome\Application\chrome.exe',
 [string]$OutputPath=''
)
$ErrorActionPreference='Stop'
. (Join-Path (Split-Path -Parent $PSScriptRoot) 'resolve-tools.ps1')
$NodePath=Resolve-EditingNode $NodePath
$NpmCli=Resolve-EditingNpm $NpmCli $NodePath
Push-Location $PSScriptRoot
try {
 $env:PATH=(Split-Path -Parent $NodePath)+';'+$env:PATH
 if($Action -eq 'Install'){
  & $NodePath $NpmCli ci
  if($LASTEXITCODE -ne 0){throw 'npm ci failed'}
  New-Item -ItemType Directory -Force -Path 'public' | Out-Null
  if(!(Test-Path -LiteralPath 'public/NotoSansSC.ttf')){Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf' -OutFile 'public/NotoSansSC.ttf'}
 } elseif($Action -eq 'Check'){
  & $NodePath 'node_modules/eslint/bin/eslint.js' src
  if($LASTEXITCODE -ne 0){throw 'ESLint failed'}
  & $NodePath 'node_modules/typescript/bin/tsc' --noEmit
  if($LASTEXITCODE -ne 0){throw 'Type checking failed'}
 } else {
  if(!(Test-Path -LiteralPath 'public/NotoSansSC.ttf')){throw 'Missing licensed font: run Install first'}
  if($Composition -eq 'PresenterEnding' -and !(Test-Path -LiteralPath 'public/presenter.jpg')){throw 'Provide real source-derived presenter.jpg; do not invent a portrait'}
  if($Action -eq 'Preview'){& $NodePath 'node_modules/@remotion/cli/remotion-cli.js' studio --no-open}
  else {
   if(!$OutputPath){$OutputPath="out/$Composition-$(Get-Date -Format 'yyyyMMdd-HHmmss').mp4"}
   if(Test-Path -LiteralPath $OutputPath){throw 'Output exists; choose a new path to preserve prior renders'}
   & $NodePath 'node_modules/@remotion/cli/remotion-cli.js' render $Composition $OutputPath --codec=h264 --crf=17 --concurrency=4 "--browser-executable=$BrowserPath"
  }
  if($LASTEXITCODE -ne 0){throw 'Remotion failed; preserve the log before repair'}
 }
} finally {Pop-Location}
