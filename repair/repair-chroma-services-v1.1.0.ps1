param(
    [Parameter(Mandatory=$true)][string]$ResultPath,
    [Parameter(Mandatory=$true)][string]$LogPath,
    [Parameter(Mandatory=$true)][string]$RepairId,
    [Parameter(Mandatory=$true)][string]$ToolVersion,
    [Parameter(Mandatory=$true)][string]$ProblemId,
    [Parameter(Mandatory=$true)][string]$RecipeId
)

$ErrorActionPreference = 'Continue'
$RepairVersion = '1.1.0'
$Names = @('Razer Chroma SDK Service','Razer Chroma SDK Server')
$Started = Get-Date
$sb = [System.Text.StringBuilder]::new()
$actions = @()
$before = @()
$after = @()
$dependencies = @()

function Add-Log([string]$Text='') { [void]$sb.AppendLine($Text) }
function Snapshot-Service([string]$Name) {
    $svc = Get-CimInstance Win32_Service -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq $Name -or $_.DisplayName -eq $Name } | Select-Object -First 1
    if ($null -eq $svc) {
        return [ordered]@{ Name=$Name; ServiceName=''; State='NOT_FOUND'; StartMode=''; ProcessId=0; ExitCode=0; Path='' }
    }
    return [ordered]@{
        Name=$Name
        ServiceName=[string]$svc.Name
        State=[string]$svc.State
        StartMode=[string]$svc.StartMode
        ProcessId=[uint32]$svc.ProcessId
        ExitCode=[uint32]$svc.ExitCode
        Path=[string]$svc.PathName
    }
}

Add-Log '=== CHROMA SDK SERVICE REPAIR ==='
Add-Log ($Started.ToString('yyyy-MM-dd HH:mm:ss.fff'))
Add-Log ("RepairId: $RepairId")
Add-Log ("ToolVersion: $ToolVersion")
Add-Log ("ProblemId: $ProblemId")
Add-Log ("RecipeId: $RecipeId")
Add-Log 'ConfirmedByUser: true'
Add-Log ("Elevated: " + ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))
Add-Log
Add-Log '=== VORHER ==='
foreach ($name in $Names) {
    $snap = Snapshot-Service $name
    $before += [pscustomobject]$snap
    Add-Log ("{0}: State={1}, StartMode={2}, ProcessId={3}, ExitCode={4}, Path={5}" -f $snap.Name,$snap.State,$snap.StartMode,$snap.ProcessId,$snap.ExitCode,$snap.Path)
}

Add-Log
Add-Log '=== STARTVERSUCH ==='
foreach ($name in $Names) {
    $snap = Snapshot-Service $name
    $attempted = $false
    $success = $false
    $message = ''
    $hresult = ''
    if ($snap.State -eq 'NOT_FOUND') {
        $message = 'Dienst nicht gefunden; keine Aktion ausgeführt.'
    } elseif ($snap.StartMode -ne 'Auto') {
        $message = "StartMode=$($snap.StartMode); aus Sicherheitsgründen keine Aktion ausgeführt."
    } elseif ($snap.State -eq 'Running') {
        $success = $true
        $message = 'Bereits Running; keine Aktion erforderlich.'
    } else {
        $attempted = $true
        try {
            Start-Service -Name $snap.ServiceName -ErrorAction Stop
            $success = $true
            $message = 'Start-Service erfolgreich.'
        } catch {
            $success = $false
            $hresult = ('0x{0:X8}' -f $_.Exception.HResult)
            $message = $_.Exception.Message
        }
    }
    $actions += [pscustomobject][ordered]@{Name=$name;Attempted=$attempted;Success=$success;Message=$message;HResult=$hresult}
    Add-Log ("{0}: Attempted={1}, Success={2}, HResult={3}, Message={4}" -f $name,$attempted,$success,$hresult,$message)
}

Start-Sleep -Seconds 5
Add-Log
Add-Log '=== NACH 5 SEKUNDEN ==='
foreach ($name in $Names) {
    $snap = Snapshot-Service $name
    $after += [pscustomobject]$snap
    Add-Log ("{0}: State={1}, StartMode={2}, ProcessId={3}, ExitCode={4}, Path={5}" -f $snap.Name,$snap.State,$snap.StartMode,$snap.ProcessId,$snap.ExitCode,$snap.Path)
}

Add-Log
Add-Log '=== ABHAENGIGKEITEN ==='
foreach ($name in $Names) {
    try {
        $svc = Get-Service -Name $name -ErrorAction Stop
        $depends = @($svc.ServicesDependedOn | ForEach-Object Name)
        $dependents = @($svc.DependentServices | ForEach-Object Name)
        $dependencies += [pscustomobject][ordered]@{Name=$name;DependsOn=$depends;Dependents=$dependents}
        Add-Log $name
        Add-Log ('  DependsOn : ' + ($depends -join ', '))
        Add-Log ('  Dependents: ' + ($dependents -join ', '))
    } catch {
        $dependencies += [pscustomobject][ordered]@{Name=$name;DependsOn=@();Dependents=@()}
        Add-Log ("${name}: Abhängigkeiten nicht lesbar")
    }
}

$allStable = $true
foreach ($snap in $after) {
    if ($snap.State -ne 'Running' -or $snap.StartMode -ne 'Auto') { $allStable = $false }
}
$status = if ($allStable) { 'SUCCESS' } else { 'FAILED' }
$message = if ($allStable) { 'Beide Chroma-SDK-Dienste laufen nach 5 Sekunden stabil im StartMode Auto.' } else { 'Mindestens ein Chroma-SDK-Dienst ist nach 5 Sekunden nicht Running / Auto.' }
$exitCode = if ($allStable) { 0 } else { 1 }
$completed = Get-Date

$result = [ordered]@{
    SchemaVersion=1
    RepairId=$RepairId
    ToolVersion=$ToolVersion
    RepairVersion=$RepairVersion
    ProblemId=$ProblemId
    RecipeId=$RecipeId
    ConfirmedByUser=$true
    TargetGate=8
    Started=$Started.ToString('o')
    Completed=$completed.ToString('o')
    Elevated=([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    Status=$status
    Message=$message
    Before=$before
    Actions=$actions
    After5Seconds=$after
    Dependencies=$dependencies
    ExitCode=$exitCode
}

Add-Log
Add-Log '=== ERGEBNIS ==='
Add-Log ("Status: $status")
Add-Log ("Message: $message")

$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($ResultPath)) | Out-Null
[System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($LogPath)) | Out-Null
[System.IO.File]::WriteAllText($ResultPath, ($result | ConvertTo-Json -Depth 8), $utf8)
[System.IO.File]::WriteAllText($LogPath, $sb.ToString(), $utf8)
exit $exitCode
