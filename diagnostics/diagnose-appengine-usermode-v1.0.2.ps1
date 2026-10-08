param(
  [Parameter(Mandatory=$true)][string]$ResultPath,
  [Parameter(Mandatory=$true)][string]$ToolVersion,
  [Parameter(Mandatory=$true)][string]$MeasurementStamp
)
$ErrorActionPreference='Stop'
$started=Get-Date
$moduleId='RHC.DIAG.APPENGINE.USERMODE'
$moduleVersion='1.0.2'

function Write-JsonFile([string]$Path,$Obj){
  $json=$Obj | ConvertTo-Json -Depth 12
  [IO.File]::WriteAllText($Path,$json,(New-Object Text.UTF8Encoding($false)))
}
function Norm([string]$p){ if(-not $p){return ''}; try{return [IO.Path]::GetFullPath([Environment]::ExpandEnvironmentVariables($p)).TrimEnd('\')}catch{return $p.Trim().Trim('"').TrimEnd('\')} }
function Parse-Run([string]$raw){
  if($raw -match '^\s*"(?<exe>[^"]+)"\s*(?<args>.*)$'){return @{exe=(Norm $Matches.exe);args=$Matches.args.Trim()}}
  if($raw -match '^\s*(?<exe>\S+\.exe)\s*(?<args>.*)$'){return @{exe=(Norm $Matches.exe);args=$Matches.args.Trim()}}
  return $null
}
function Sig([string]$p){
  try{$s=Get-AuthenticodeSignature -LiteralPath $p -ErrorAction Stop; return @{status=[string]$s.Status;subject=$(if($s.SignerCertificate){[string]$s.SignerCertificate.Subject}else{''})}}catch{return @{status='READ_ERROR';subject='';error=$_.Exception.Message}}
}

$errors=@()
$runRaw='';$runExe='';$runArgs='';$engineRoot='';$runValid=$false;$runSig=$null
try{
  $r=Get-ItemProperty -LiteralPath 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run' -Name 'RazerAppEngine' -ErrorAction Stop
  $runRaw=[string]$r.RazerAppEngine
  $parsed=Parse-Run $runRaw
  if($parsed){
    $runExe=$parsed.exe;$runArgs=$parsed.args;$engineRoot=Norm (Split-Path -Parent $runExe)
    $runSig=Sig $runExe
    $runValid=(Test-Path -LiteralPath $runExe -PathType Leaf) -and ([IO.Path]::GetFileName($runExe) -ieq 'RazerAppEngine.exe') -and ($runArgs -match '(?i)--url-params=apps=synapse,chroma-app') -and ($runArgs -match '(?i)--launch-force-hidden=synapse,chroma-app') -and ($runArgs -match '(?i)--autoStart=1') -and ($runSig.status -eq 'Valid') -and ($runSig.subject -match '(?i)Razer')
  }
}catch{$errors+=('RunContract: '+$_.Exception.Message)}

$rows=@()
try{
  $all=@(Get-CimInstance Win32_Process -Filter "Name='RazerAppEngine.exe'" -Property Name,ProcessId,ParentProcessId,ExecutablePath,CommandLine,CreationDate -ErrorAction Stop)
  foreach($p in $all){
    $path=Norm ([string]$p.ExecutablePath); if(-not $path){continue}
    if($engineRoot -and -not $path.StartsWith($engineRoot+'\',[StringComparison]::OrdinalIgnoreCase) -and -not $path.Equals($runExe,[StringComparison]::OrdinalIgnoreCase)){continue}
    $parent=Split-Path -Parent $path;$dir=[IO.Path]::GetFileName($parent)
    $kind='OTHER';if($path.Equals($runExe,[StringComparison]::OrdinalIgnoreCase)){$kind='LAUNCHER'}elseif($dir -match '^app-[0-9A-Za-z._-]+$'){$kind='VERSIONED_RUNTIME'}
    $cmd=[string]$p.CommandLine
    $page='';if($cmd -match '(?i)--razer-page-name=([^\s]+)'){$page=$Matches[1].Trim('"')}
    $rows+=[pscustomobject]@{Name=[string]$p.Name;ProcessId=[int]$p.ProcessId;ParentProcessId=[int]$p.ParentProcessId;ExecutablePath=$path;CommandLine=$cmd;CreationDate=[string]$p.CreationDate;Kind=$kind;PageName=$page;IsHelper=[bool]($cmd -match '(?i)(^|\s)--type=')}
  }
}catch{$errors+=('Processes: '+$_.Exception.Message)}

$versioned=@($rows|?{$_.Kind -eq 'VERSIONED_RUNTIME'})
$runtimePaths=@($versioned|%{$_.ExecutablePath}|sort -Unique)
$main=@($versioned|?{-not $_.IsHelper -and $_.CommandLine -match '(?i)--url-params='})
$pages=@($versioned|%{$_.PageName}|?{$_}|sort -Unique)
$runtimeState='NOT_RUNNING';$runtimeExe='';$mainPid=0;$mainArgs='';$runtimeSig=$null
if($runtimePaths.Count -gt 1 -or $main.Count -gt 1){$runtimeState='AMBIGUOUS'}
elseif($runtimePaths.Count -eq 1 -and $main.Count -eq 1){
  $runtimeExe=$runtimePaths[0];$mainPid=[int]$main[0].ProcessId;$mainArgs=[string]$main[0].CommandLine;$runtimeSig=Sig $runtimeExe
  # Persistent background-runtime evidence is normative for HEALTHY. Dashboard
  # renderers (win-synapse / win-chroma-app) are transient UI evidence only and
  # may legitimately disappear while mappings, tray and Chroma remain healthy.
  $systray=[bool](@($pages|?{$_ -match '(?i)^win-systray'}).Count -gt 0)
  $backgroundManager=[bool](@($pages|?{$_ -eq 'win-background-manager'}).Count -gt 0)
  $lightingEngine=[bool](@($pages|?{$_ -eq 'win-lighting-engine'}).Count -gt 0)
  $deviceMiddleware=[bool](@($pages|?{$_ -match '(?i)^win-usb_.*_mw$'}).Count -gt 0)
  $synapse=[bool](@($pages|?{$_ -in @('win-synapse','synapse')}).Count -gt 0)
  $chroma=[bool](@($pages|?{$_ -in @('win-chroma-app','chroma-app')}).Count -gt 0)
  $contractMain=[bool]($mainArgs -match '(?i)--url-params=apps=synapse,chroma-app')
  if($runValid -and $contractMain -and $systray -and $backgroundManager -and $lightingEngine -and $deviceMiddleware){$runtimeState='HEALTHY'}else{$runtimeState='INCOMPLETE'}
}
elseif($rows.Count -gt 0){$runtimeState='AMBIGUOUS'}

$systrayPresent=[bool](@($pages|?{$_ -match '(?i)^win-systray'}).Count -gt 0)
$backgroundManagerPresent=[bool](@($pages|?{$_ -eq 'win-background-manager'}).Count -gt 0)
$lightingEnginePresent=[bool](@($pages|?{$_ -eq 'win-lighting-engine'}).Count -gt 0)
$deviceMiddlewarePresent=[bool](@($pages|?{$_ -match '(?i)^win-usb_.*_mw$'}).Count -gt 0)
$synapsePresent=[bool](@($pages|?{$_ -in @('win-synapse','synapse')}).Count -gt 0)
$chromaPresent=[bool](@($pages|?{$_ -in @('win-chroma-app','chroma-app')}).Count -gt 0)
# Compatibility alias retained for existing consumers; this is generic device middleware, not a PID/class inference.
$keyboardMiddlewarePresent=$deviceMiddlewarePresent

$result=[ordered]@{
  SchemaVersion=1;ModuleId=$moduleId;ModuleVersion=$moduleVersion;ToolVersion=$ToolVersion;MeasurementStamp=$MeasurementStamp;
  Started=$started.ToString('o');Completed=(Get-Date).ToString('o');Elevated=([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator);ReadOnly=$true;
  Status=$(if($errors.Count){'PARTIAL'}else{'OK'});Errors=$errors;
  RuntimeState=$runtimeState;RunContractValid=$runValid;RunContract=$runRaw;LauncherExecutable=$runExe;LauncherArguments=$runArgs;LauncherSignature=$runSig;
  RuntimeExecutable=$runtimeExe;RuntimeMainPid=$mainPid;RuntimeMainArguments=$mainArgs;RuntimeSignature=$runtimeSig;ProcessCount=$rows.Count;Pages=$pages;
  SystrayPresent=$systrayPresent;BackgroundManagerPresent=$backgroundManagerPresent;LightingEnginePresent=$lightingEnginePresent;DeviceMiddlewarePresent=$deviceMiddlewarePresent;
  SynapsePresent=$synapsePresent;ChromaPresent=$chromaPresent;KeyboardMiddlewarePresent=$keyboardMiddlewarePresent;
  Processes=$rows
}
Write-JsonFile $ResultPath $result
if($runtimeState -eq 'AMBIGUOUS'){exit 2}
exit 0
