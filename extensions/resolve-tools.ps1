function Resolve-EditingNode([string]$ExplicitPath) {
 if($ExplicitPath){return (Get-Item -LiteralPath $ExplicitPath -ErrorAction Stop).FullName}
 if($env:TALKING_HEAD_NODE){return (Get-Item -LiteralPath $env:TALKING_HEAD_NODE -ErrorAction Stop).FullName}
 $bundled=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
 if(Test-Path -LiteralPath $bundled){return $bundled}
 return (Get-Command node -ErrorAction Stop).Source
}
function Resolve-EditingNpm([string]$ExplicitPath, [string]$ResolvedNode) {
 if($ExplicitPath){return (Get-Item -LiteralPath $ExplicitPath -ErrorAction Stop).FullName}
 $candidates=@((Join-Path (Split-Path -Parent $ResolvedNode) 'node_modules\npm\bin\npm-cli.js'))
 $npmCommand=Get-Command npm.cmd -ErrorAction SilentlyContinue
 if($npmCommand){$candidates+=(Join-Path (Split-Path -Parent $npmCommand.Source) 'node_modules\npm\bin\npm-cli.js')}
 foreach($candidate in $candidates){if(Test-Path -LiteralPath $candidate){return $candidate}}
 throw 'npm-cli.js not found. Install Node/npm or pass -NpmCli explicitly.'
}
