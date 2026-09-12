param(
  [ValidateSet('Install','Doctor','Check','Snapshot','Render')][string]$Action='Check',
  [string]$NodePath='',
  [string]$NpmCli='',
  [string]$FfmpegDirectory='',
  [string]$OutputPath=''
)
$ErrorActionPreference='Stop'
. (Join-Path (Split-Path -Parent $PSScriptRoot) 'resolve-tools.ps1')
$NodePath=Resolve-EditingNode $NodePath
$NpmCli=Resolve-EditingNpm $NpmCli $NodePath
Push-Location $PSScriptRoot
try {
  if(!$FfmpegDirectory){
    $ffCommand=Get-Command ffmpeg -ErrorAction SilentlyContinue
    if($ffCommand){$FfmpegDirectory=Split-Path -Parent $ffCommand.Source}
    else {$candidate=Join-Path $env:USERPROFILE '.chatcut\cache\ffmpeg\8.1\win32-x64'; if(Test-Path -LiteralPath $candidate){$FfmpegDirectory=$candidate}}
  }
  $nodeVersion=& $NodePath --version
  if([int]($nodeVersion.TrimStart('v').Split('.')[0]) -lt 22){throw 'HyperFrames requires Node >=22.'}
  $env:PATH=(Split-Path -Parent $NodePath)+';'+$FfmpegDirectory+';'+$env:PATH
  $env:HYPERFRAMES_SKIP_SKILLS='1'
  $env:HYPERFRAMES_RUN_ID='teaching-'+(Get-Date -Format 'yyyyMMddHHmmss')
  $prefix=@('exec','--yes','--package=hyperframes@0.8.35','--','hyperframes')
  if($Action -eq 'Render'){
    if(!$OutputPath){$OutputPath="renders/customer-status-$(Get-Date -Format 'yyyyMMdd-HHmmss').mp4"}
    if(Test-Path -LiteralPath $OutputPath){throw 'Output exists; choose a new path to preserve prior renders.'}
  }
  if($Action -eq 'Install'){
    New-Item -ItemType Directory -Force -Path 'assets' | Out-Null
    if(!(Test-Path -LiteralPath 'assets/gsap.min.js')){Invoke-WebRequest -Uri 'https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js' -OutFile 'assets/gsap.min.js'}
    if(!(Test-Path -LiteralPath 'assets/NotoSansSC.ttf')){Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf' -OutFile 'assets/NotoSansSC.ttf'}
    foreach($entry in (Get-Content -LiteralPath 'source-manifest.json' -Raw | ConvertFrom-Json).sources){
      if($entry.file -in @('assets/gsap.min.js','assets/NotoSansSC.ttf')){
        $actual=(Get-FileHash -LiteralPath $entry.file -Algorithm SHA256).Hash.ToLowerInvariant()
        if($actual -ne $entry.sha256){throw ('Dependency hash mismatch: '+$entry.file+'. Preserve file and recheck upstream; do not silently accept a new version.')}
      }
    }
    Write-Output 'Assets installed and hash checked; engine readiness is checked separately with Doctor.'
    return
  }
  $hfArgs=switch($Action){
    'Doctor' {@('doctor','--json')}
    'Check' {@('check','.','--samples','15','--caption-zone','x0=0;y0=.824;x1=1;y1=1;severity=error;seek=.25,1','--strict','--snapshots','--json')}
    'Snapshot' {@('snapshot','.','--at','0.5,1.2,2.2,3.8,5.6,6.6')}
    'Render' {@('render','.','--fps','30','--quality','high','--format','mp4','--output',$OutputPath)}
  }
  & $NodePath $NpmCli @prefix @hfArgs
  if($LASTEXITCODE -ne 0){throw "HyperFrames $Action failed with code $LASTEXITCODE. Preserve the current logs before repairing."}
} finally {Pop-Location}
