param(
    [Parameter(Mandatory=$true)][string]$ResultPath,
    [Parameter(Mandatory=$true)][string]$ToolVersion,
    [Parameter(Mandatory=$true)][string]$MeasurementStamp
)

$ErrorActionPreference = 'Continue'
$ModuleId = 'RHC.DIAG.CHROMA.SERVICES'
$ModuleVersion = '1.0.0'
$Started = Get-Date
$Names = @(
    'Razer Chroma SDK Diagnostic Service',
    'Razer Chroma SDK Server',
    'Razer Chroma SDK Service',
    'Razer Chroma Stream Server'
)
$services = @()
$errors = @()

foreach ($name in $Names) {
    try {
        $q = $name.Replace("'", "''")
        $svc = Get-CimInstance Win32_Service -Filter "Name='$q' OR DisplayName='$q'" -Property Name,DisplayName,State,StartMode,ProcessId,ExitCode,PathName -ErrorAction Stop | Select-Object -First 1
        if ($null -eq $svc) {
            $services += [pscustomobject][ordered]@{
                Name=$name; ServiceName=''; DisplayName=''; State='NOT_FOUND'; StartMode=''; ProcessId=0; ExitCode=0; Path=''
            }
        } else {
            $services += [pscustomobject][ordered]@{
                Name=$name
                ServiceName=[string]$svc.Name
                DisplayName=[string]$svc.DisplayName
                State=[string]$svc.State
                StartMode=[string]$svc.StartMode
                ProcessId=[uint32]$svc.ProcessId
                ExitCode=[uint32]$svc.ExitCode
                Path=[string]$svc.PathName
            }
        }
    } catch {
        $errors += ("{0}: {1}" -f $name,[string]$_.Exception.Message)
        $services += [pscustomobject][ordered]@{
            Name=$name; ServiceName=''; DisplayName=''; State='UNKNOWN'; StartMode=''; ProcessId=0; ExitCode=0; Path=''
        }
    }
}

$Completed = Get-Date
$status = if ($errors.Count -eq 0) { 'SUCCESS' } else { 'PARTIAL' }
$result = [ordered]@{
    SchemaVersion=1
    ModuleId=$ModuleId
    ModuleVersion=$ModuleVersion
    ToolVersion=$ToolVersion
    MeasurementStamp=$MeasurementStamp
    Started=$Started.ToString('o')
    Completed=$Completed.ToString('o')
    Elevated=([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    ReadOnly=$true
    Status=$status
    Errors=$errors
    Services=$services
}

$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($ResultPath)) | Out-Null
[System.IO.File]::WriteAllText($ResultPath, ($result | ConvertTo-Json -Depth 8), $utf8)
exit 0
