param(
    [Parameter(Mandatory=$true)][string]$ResultPath,
    [Parameter(Mandatory=$true)][string]$LogPath,
    [Parameter(Mandatory=$true)][string]$RepairId,
    [Parameter(Mandatory=$true)][string]$ToolVersion,
    [Parameter(Mandatory=$true)][string]$ProblemId,
    [Parameter(Mandatory=$true)][string]$RecipeId
)

$ErrorActionPreference = 'Stop'
$RepairVersion = '1.0.0'
$Started = Get-Date
$TargetGate = 1
$sb = [System.Text.StringBuilder]::new()
$actions = @()
$before = @()
$after = @()
$runtimeBefore = $null
$runtimeAfter = $null
$actionMode = ''
$status = 'FAILED'
$message = ''
$exitCode = 1

function Add-Log([string]$Text='') { [void]$sb.AppendLine(((Get-Date).ToString('o')) + ' ' + $Text) }
function Normalize-Path([string]$Path) {
    if (-not $Path) { return '' }
    try { return [IO.Path]::GetFullPath([Environment]::ExpandEnvironmentVariables($Path)).TrimEnd('\') }
    catch { return $Path.Trim().Trim('"').TrimEnd('\') }
}
function Parse-RunCommand([string]$Raw) {
    if ($Raw -match '^\s*"(?<exe>[^"]+)"\s*(?<args>.*)$') { return [pscustomobject]@{Executable=(Normalize-Path $Matches.exe);Arguments=$Matches.args.Trim()} }
    if ($Raw -match '^\s*(?<exe>\S+\.exe)\s*(?<args>.*)$') { return [pscustomobject]@{Executable=(Normalize-Path $Matches.exe);Arguments=$Matches.args.Trim()} }
    return $null
}
function Assert-RazerSignature([string]$Path) {
    $sig = Get-AuthenticodeSignature -LiteralPath $Path -ErrorAction Stop
    $subject = if ($sig.SignerCertificate) { [string]$sig.SignerCertificate.Subject } else { '' }
    if ([string]$sig.Status -ne 'Valid' -or $subject -notmatch '(?i)Razer') { throw "Signature validation failed: $Path [$($sig.Status)]" }
    return [pscustomobject]@{Status=[string]$sig.Status;SignerSubject=$subject}
}
function Get-AppEngineProcesses([string]$Root,[string]$Launcher) {
    $out = @()
    $all = @(Get-CimInstance Win32_Process -Filter "Name='RazerAppEngine.exe'" -Property Name,ProcessId,ParentProcessId,ExecutablePath,CommandLine,CreationDate -ErrorAction Stop)
    foreach ($p in $all) {
        $path = Normalize-Path ([string]$p.ExecutablePath)
        if (-not $path) { continue }
        if (-not $path.StartsWith($Root+'\',[StringComparison]::OrdinalIgnoreCase) -and -not $path.Equals($Launcher,[StringComparison]::OrdinalIgnoreCase)) { continue }
        $parent = Split-Path -Parent $path
        $dir = [IO.Path]::GetFileName($parent)
        $kind = 'OTHER'
        if ($path.Equals($Launcher,[StringComparison]::OrdinalIgnoreCase)) { $kind='LAUNCHER' }
        elseif ($dir -match '^app-[0-9A-Za-z._-]+$') { $kind='VERSIONED_RUNTIME' }
        $cmd = [string]$p.CommandLine
        $page = ''
        if ($cmd -match '(?i)--razer-page-name=([^\s]+)') { $page=$Matches[1].Trim('"') }
        $out += [pscustomobject][ordered]@{
            ProcessId=[int]$p.ProcessId; ParentProcessId=[int]$p.ParentProcessId; ExecutablePath=$path;
            CommandLine=$cmd; Kind=$kind; PageName=$page; IsHelper=[bool]($cmd -match '(?i)(^|\s)--type=')
        }
    }
    return @($out)
}

Add-Log '=== RAZER APPENGINE CONTROLLED RUNTIME RECOVERY ==='
Add-Log ("RepairId: $RepairId")
Add-Log ("ToolVersion: $ToolVersion")
Add-Log ("ProblemId: $ProblemId")
Add-Log ("RecipeId: $RecipeId")
Add-Log 'ConfirmedByUser: true'
Add-Log ("Elevated: " + ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))

try {
    $run = Get-ItemProperty -LiteralPath 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run' -Name 'RazerAppEngine' -ErrorAction Stop
    $raw = [string]$run.RazerAppEngine
    $parsed = Parse-RunCommand $raw
    if ($null -eq $parsed) { throw 'RazerAppEngine Run contract could not be parsed.' }
    $launcher = $parsed.Executable
    $args = $parsed.Arguments
    $root = Normalize-Path (Split-Path -Parent $launcher)
    if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) { throw 'Validated RazerAppEngine launcher is missing.' }
    if ([IO.Path]::GetFileName($launcher) -ine 'RazerAppEngine.exe') { throw 'Unexpected launcher executable.' }
    foreach ($required in @('--url-params=apps=synapse,chroma-app','--launch-force-hidden=synapse,chroma-app','--autoStart=1')) {
        if ($args.IndexOf($required,[StringComparison]::OrdinalIgnoreCase) -lt 0) { throw "Run contract missing required argument: $required" }
    }
    $launcherSig = Assert-RazerSignature $launcher
    Add-Log ("Launcher: $launcher")
    Add-Log ("Arguments: $args")
    Add-Log ("Launcher signer: $($launcherSig.SignerSubject)")

    $before = @(Get-AppEngineProcesses $root $launcher)
    $unexpected = @($before | Where-Object { $_.Kind -eq 'OTHER' })
    if ($unexpected.Count -gt 0) { throw 'Unexpected AppEngine process path detected.' }
    $versioned = @($before | Where-Object { $_.Kind -eq 'VERSIONED_RUNTIME' })
    $runtimePaths = @($versioned | ForEach-Object ExecutablePath | Sort-Object -Unique)
    $mains = @($versioned | Where-Object { -not $_.IsHelper -and $_.CommandLine -match '(?i)--url-params=' })

    if ($before.Count -eq 0) {
        $actionMode = 'START_ONLY_RECOVERY'
    } elseif ($runtimePaths.Count -eq 1 -and $mains.Count -eq 1) {
        $actionMode = 'FULL_RUNTIME_RESTART'
    } else {
        throw 'AppEngine runtime state is ambiguous; no repair action allowed.'
    }
    Add-Log ("ActionMode: $actionMode")

    if ($actionMode -eq 'FULL_RUNTIME_RESTART') {
        $runtimeExe = [string]$runtimePaths[0]
        $mainPid = [int]$mains[0].ProcessId
        $runtimeSig = Assert-RazerSignature $runtimeExe
        $runtimeBefore = [ordered]@{Executable=$runtimeExe;MainPid=$mainPid;Arguments=[string]$mains[0].CommandLine;Signer=$runtimeSig.SignerSubject}
        Add-Log ("Runtime: $runtimeExe")
        Add-Log ("Main PID: $mainPid")

        try { $proc=[Diagnostics.Process]::GetProcessById($mainPid); [void]$proc.CloseMainWindow() } catch {}
        Start-Sleep -Seconds 3
        $now = @(Get-AppEngineProcesses $root $launcher)
        if (@($now | Where-Object { $_.ProcessId -eq $mainPid }).Count -gt 0) {
            Stop-Process -Id $mainPid -Force -ErrorAction Stop
            $actions += [pscustomobject][ordered]@{Name='Stop AppEngine runtime main';Attempted=$true;Success=$true;Message="PID=$mainPid";HResult=''}
        }
        Start-Sleep -Milliseconds 700
        $now = @(Get-AppEngineProcesses $root $launcher)
        foreach ($x in @($now | Where-Object { $_.ExecutablePath -eq $runtimeExe -or $_.ExecutablePath -eq $launcher })) {
            try {
                Stop-Process -Id ([int]$x.ProcessId) -Force -ErrorAction Stop
                $actions += [pscustomobject][ordered]@{Name='Stop AppEngine residual';Attempted=$true;Success=$true;Message="PID=$($x.ProcessId)";HResult=''}
            } catch {
                $actions += [pscustomobject][ordered]@{Name='Stop AppEngine residual';Attempted=$true;Success=$false;Message=$_.Exception.Message;HResult=('0x{0:X8}' -f $_.Exception.HResult)}
            }
        }
        $deadline=(Get-Date).AddSeconds(12)
        do { Start-Sleep -Milliseconds 350; $left=@(Get-AppEngineProcesses $root $launcher) } while ($left.Count -gt 0 -and (Get-Date) -lt $deadline)
        if ($left.Count -gt 0) { throw 'Old AppEngine runtime stack did not stop completely.' }
        Start-Sleep -Seconds 2
    }

    if (@(Get-AppEngineProcesses $root $launcher).Count -gt 0) { throw 'AppEngine process appeared before controlled relaunch; refusing duplicate start.' }

    $lp = Start-Process -FilePath $launcher -ArgumentList $args -WorkingDirectory $root -PassThru -ErrorAction Stop
    $actions += [pscustomobject][ordered]@{Name='Launch RazerAppEngine';Attempted=$true;Success=$true;Message="PID=$($lp.Id); Mode=$actionMode";HResult=''}
    Add-Log ("Launcher PID: $($lp.Id)")
    Start-Sleep -Seconds 60

    $after = @(Get-AppEngineProcesses $root $launcher)
    $vr = @($after | Where-Object { $_.Kind -eq 'VERSIONED_RUNTIME' })
    $vp = @($vr | ForEach-Object ExecutablePath | Sort-Object -Unique)
    $vm = @($vr | Where-Object { -not $_.IsHelper -and $_.CommandLine -match '(?i)--url-params=' })
    if ($vp.Count -ne 1 -or $vm.Count -ne 1) { throw 'Post-repair AppEngine runtime is not uniquely identifiable.' }
    $pages = @($vr | ForEach-Object PageName | Where-Object { $_ } | Sort-Object -Unique)
    $mainArgs = [string]$vm[0].CommandLine
    $okContract = [bool]($mainArgs -match '(?i)--url-params=apps=synapse,chroma-app')
    $okTray = [bool](@($pages | Where-Object { $_ -match '(?i)^win-systray' }).Count -gt 0)
    $okSyn = [bool](@($pages | Where-Object { $_ -in @('win-synapse','synapse') }).Count -gt 0)
    $okChr = [bool](@($pages | Where-Object { $_ -in @('win-chroma-app','chroma-app') }).Count -gt 0)
    $runtimeAfter = [ordered]@{Executable=$vp[0];MainPid=[int]$vm[0].ProcessId;Arguments=$mainArgs;Pages=$pages;ContractComplete=$okContract;SystrayPresent=$okTray;SynapsePresent=$okSyn;ChromaPresent=$okChr}
    if (-not ($okContract -and $okTray -and $okSyn -and $okChr)) { throw 'Post-repair AppEngine user-mode contract is incomplete.' }

    $status='SUCCESS'
    $message='Controlled AppEngine runtime recovery completed.'
    $exitCode=0
} catch {
    $status='FAILED'
    $message=$_.Exception.Message
    $exitCode=1
    Add-Log ('ERROR: ' + $_.Exception.Message)
}

$completed=Get-Date
$result=[ordered]@{
    SchemaVersion=2; RepairId=$RepairId; ToolVersion=$ToolVersion; RepairVersion=$RepairVersion;
    ProblemId=$ProblemId; RecipeId=$RecipeId; ConfirmedByUser=$true; TargetGate=$TargetGate;
    Started=$Started.ToString('o'); Completed=$completed.ToString('o');
    Elevated=([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator);
    Status=$status; Message=$message; Before=$before; Actions=$actions; After5Seconds=$after; Dependencies=@(); ExitCode=$exitCode;
    VerificationStatus='NOT_RUN'; VerificationDetail=''; VerificationModuleId=''; VerificationVersion=''; VerifiedAt='';
    ActionMode=$actionMode; RuntimeBefore=$runtimeBefore; RuntimeAfter=$runtimeAfter
}
Add-Log ("Status: $status")
Add-Log ("Message: $message")
$utf8=New-Object Text.UTF8Encoding($false)
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($ResultPath))|Out-Null
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($LogPath))|Out-Null
[IO.File]::WriteAllText($ResultPath,($result|ConvertTo-Json -Depth 12),$utf8)
[IO.File]::WriteAllText($LogPath,$sb.ToString(),$utf8)
exit $exitCode
