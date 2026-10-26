param(
 [ValidateSet('Check','List','Render','Still','Preview')][string]$Action='List',
 [ValidatePattern('^[a-zA-Z0-9_-]+$')][string]$TemplateId='library-bar-zh',
 [string]$NodePath='',
 [string]$BrowserPath='C:\Program Files\Google\Chrome\Application\chrome.exe',
 [string]$OutputPath='',
 [string]$PropsPath='',
 [int]$Frame=45
)
$ErrorActionPreference='Stop'
. (Join-Path (Split-Path -Parent $PSScriptRoot) 'resolve-tools.ps1')
$NodePath=Resolve-EditingNode $NodePath
if($PropsPath){$PropsPath=(Get-Item -LiteralPath $PropsPath).FullName}
if($OutputPath){$OutputPath=$ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputPath)}
Push-Location $PSScriptRoot
try {
 $cli='node_modules/@remotion/cli/remotion-cli.js'
 if(!(Test-Path -LiteralPath $cli)){throw 'Missing locked dependencies. Install this extension with its existing package-lock.json first.'}
 if($Action -eq 'Check'){
  & $NodePath 'node_modules/typescript/bin/tsc' --project tsconfig.library.json --noEmit
  if($LASTEXITCODE -ne 0){throw 'Template library type check failed'}
  & $NodePath 'node_modules/eslint/bin/eslint.js' 'src/template-library' --ignore-pattern '**/upstream/**'
 } else {
  $renderArgs=@('--browser-executable='+$BrowserPath)
  $propsArgs=@()
  if($PropsPath){$propsArgs+=('--props='+$PropsPath); $renderArgs+=$propsArgs}
  if($Action -eq 'List'){& $NodePath $cli compositions 'src/template-library/index.ts' @renderArgs}
  elseif($Action -eq 'Preview'){& $NodePath $cli studio 'src/template-library/index.ts' --no-open @propsArgs}
  else {
   if($TemplateId -like 'library-*' -and !(Test-Path -LiteralPath 'public/NotoSansSC.ttf')){throw 'Missing local Noto Sans SC font; see TEMPLATE_LIBRARY.md'}
   if(!$OutputPath){$extension=if($Action -eq 'Still'){'png'}else{'mp4'}; $OutputPath="out/template-library/$TemplateId-$(Get-Date -Format 'yyyyMMdd-HHmmss').$extension"}
   if(Test-Path -LiteralPath $OutputPath){throw 'Output exists; use a new path to preserve previous renders'}
   if($Action -eq 'Still'){& $NodePath $cli still 'src/template-library/index.ts' $TemplateId $OutputPath "--frame=$Frame" @renderArgs}
   else {& $NodePath $cli render 'src/template-library/index.ts' $TemplateId $OutputPath --codec=h264 --crf=18 --concurrency=4 @renderArgs}
  }
 }
 if($LASTEXITCODE -ne 0){throw 'Template library command failed; preserve the error output'}
} finally {Pop-Location}
