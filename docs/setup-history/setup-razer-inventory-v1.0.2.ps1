[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$OutputPath,
    [string]$ToolVersion = '2.2.2'
)

# Setup Scanner 1.0.2 for Razer Health Monitor v2.2.2.
# Read-only: queries PnP/CIM/registry/driver metadata only.
# It writes:
#   - the requested inventory JSON on success
#   - SetupScannerDebug-v1.0.2.json next to the inventory on every run
#   - SetupScannerDebug-v1.0.2.txt next to the inventory on every run

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$ScanVersion = '1.0.2'
$VendorId = '1532'

# Empirically verified on 2026-09-10 with four controlled device states:
# 1) dongle only / switch Wireless, 2) cable only / switch Wire,
# 3) dongle+cable / switch Wire, 4) dongle+cable / switch Wireless.
# The mapping is device/PID knowledge owned by the Setup profile layer; the
# Health Engine remains free of product-specific PID constants.
$VerifiedConnectionTypes = @{
    '02C9' = 'wireless-dongle'
    '02CC' = 'wired-usb'
}
$VerifiedConnectionTypeEvidence = 'verified-four-state-pnp-matrix-2026-09-10'
$started = Get-Date
$parent = Split-Path -Parent $OutputPath
if (-not $parent) { $parent = (Get-Location).Path }
if (-not (Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
}

$DebugJsonPath = Join-Path $parent 'SetupScannerDebug-v1.0.2.json'
$DebugTextPath = Join-Path $parent 'SetupScannerDebug-v1.0.2.txt'

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

# Last-resort diagnostic path: even an unexpected terminating error before the
# normal export stage should leave a machine-readable and human-readable trace.
trap {
    $fatal = $_
    try {
        $fallback = [ordered]@{
            schemaVersion = 1
            scannerVersion = $ScanVersion
            toolVersion = $ToolVersion
            fatal = $true
            occurredAt = (Get-Date).ToUniversalTime().ToString('o')
            outputPath = $OutputPath
            error = [ordered]@{
                type = if ($fatal.Exception) { $fatal.Exception.GetType().FullName } else { '' }
                hresult = if ($fatal.Exception) { ('0x{0:X8}' -f $fatal.Exception.HResult) } else { '' }
                message = if ($fatal.Exception) { $fatal.Exception.Message } else { [string]$fatal }
                scriptStackTrace = [string]$fatal.ScriptStackTrace
                positionMessage = if ($fatal.InvocationInfo) { [string]$fatal.InvocationInfo.PositionMessage } else { '' }
            }
        }

        [System.IO.File]::WriteAllText(
            $DebugJsonPath,
            ($fallback | ConvertTo-Json -Depth 8),
            $utf8NoBom
        )

        $fallbackText = @(
            "=== RAZER SETUP SCANNER FATAL $ScanVersion ==="
            "Zeit: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff'))"
            "Typ: $($fallback.error.type)"
            "HResult: $($fallback.error.hresult)"
            "Meldung: $($fallback.error.message)"
            ""
            "Position:"
            $fallback.error.positionMessage
            ""
            "Stack:"
            $fallback.error.scriptStackTrace
        ) -join [Environment]::NewLine

        [System.IO.File]::WriteAllText(
            $DebugTextPath,
            $fallbackText,
            $utf8NoBom
        )
    }
    catch {
        # No secondary failure should mask the original scanner error.
    }

    Write-Error $fatal
    exit 99
}

$errors = New-Object System.Collections.Generic.List[object]

function Add-ScanError {
    param([string]$Stage, [System.Exception]$Exception)
    $errors.Add([ordered]@{
        stage = $Stage
        type = if ($Exception) { $Exception.GetType().FullName } else { '' }
        hresult = if ($Exception) { ('0x{0:X8}' -f $Exception.HResult) } else { '' }
        message = if ($Exception) { $Exception.Message } else { '' }
    }) | Out-Null
}

function Get-OptionalPropertyString {
    param(
        [object]$InputObject,
        [string]$PropertyName
    )

    if ($null -eq $InputObject -or -not $PropertyName) {
        return ''
    }

    try {
        $prop = $InputObject.PSObject.Properties[$PropertyName]
        if ($null -ne $prop -and $null -ne $prop.Value) {
            return [string]$prop.Value
        }
    }
    catch {
        # Missing optional properties are normal in Enum\USB / Enum\HID.
    }

    return ''
}

function Get-PidFromId {
    param([string]$Id)
    if ($Id -and $Id -match '(?i)VID_1532&PID_([0-9A-F]{4})') {
        return $Matches[1].ToUpperInvariant()
    }
    return ''
}

function Clean-Name {
    param([string]$Value)
    if (-not $Value) { return '' }
    $s = [string]$Value
    $s = $s -replace '^@[^;]+;',''
    $s = $s -replace '^Razer Inc\.\s*','Razer '
    return $s.Trim()
}

function Best-Model {
    param([object[]]$Names, [string]$DevicePid)

    $clean = @(
        $Names |
        ForEach-Object { Clean-Name ([string]$_) } |
        Where-Object {
            $_ -and
            $_ -notmatch '(?i)^(USB Input Device|HID-compliant device|HID-compliant mouse|HID-compliant consumer control device|HID Keyboard Device|Razer Control Device)$'
        } |
        Select-Object -Unique
    )

    $razer = @(
        $clean |
        Where-Object {
            $_ -match '(?i)\bRazer\b' -and
            $_ -notmatch '(?i)Control Device|Virtual'
        }
    )

    if ($razer.Count -gt 0) { return [string]$razer[0] }
    if ($clean.Count -gt 0) { return [string]$clean[0] }
    return "Razer Gerät PID $DevicePid"
}

function Product-Key {
    param([string]$Name, [string]$DevicePid)

    $s = if ($Name) { $Name.ToLowerInvariant() } else { '' }
    $s = $s -replace '\brazer\b',''
    $s = $s -replace '(?i)wireless usb dongle|usb dongle|hyperspeed dongle|dongle|receiver',''
    $s = $s -replace '[^a-z0-9]+',' '
    $s = ($s -replace '\s+',' ').Trim()

    if (-not $s -or $s -match '^gerät pid') {
        return "pid-$($DevicePid.ToLowerInvariant())"
    }
    return $s
}

function Connection-Type {
    param([string]$Name, [bool]$Present, [string]$DevicePid)

    $key = ([string]$DevicePid).ToUpperInvariant()
    if ($VerifiedConnectionTypes.ContainsKey($key)) {
        return [string]$VerifiedConnectionTypes[$key]
    }
    # Never infer a connection path from a marketing/model token such as
    # "HyperSpeed": the four-state test proved that the same product name is
    # used for both its wireless-dongle and wired USB PIDs.
    if ($Name -match '(?i)dongle|receiver') { return 'wireless-dongle' }
    if ($Present) { return 'usb-device' }
    return 'alternate-usb'
}

function Connection-Type-Source {
    param([string]$Name, [string]$DevicePid)
    $key = ([string]$DevicePid).ToUpperInvariant()
    if ($VerifiedConnectionTypes.ContainsKey($key)) { return $VerifiedConnectionTypeEvidence }
    if ($Name -match '(?i)dongle|receiver') { return 'device-name-evidence' }
    return 'generic-topology'
}

# ---------------------------------------------------------------------------
# 1) Present PnP devices via PnpDevice cmdlet (primary present-device source)
# ---------------------------------------------------------------------------
$pnpCmdRows = @()
try {
    if (Get-Command Get-PnpDevice -ErrorAction SilentlyContinue) {
        $pnpCmdRows = @(
            Get-PnpDevice -PresentOnly -ErrorAction Stop |
            Where-Object {
                [string]$_.InstanceId -match '(?i)VID_1532&PID_[0-9A-F]{4}'
            } |
            ForEach-Object {
                [ordered]@{
                    instanceId = [string]$_.InstanceId
                    name       = [string]$_.FriendlyName
                    class      = [string]$_.Class
                    status     = [string]$_.Status
                    source     = 'Get-PnpDevice'
                }
            }
        )
    }
}
catch {
    Add-ScanError 'Get-PnpDevice' $_.Exception
}

# ---------------------------------------------------------------------------
# 2) Win32_PnPEntity via CIM (problem code + service)
#    Use a provider-side filter first; fall back to full enumeration.
# ---------------------------------------------------------------------------
$cimPnp = @()
try {
    $cimPnp = @(
        Get-CimInstance Win32_PnPEntity `
            -Filter "PNPDeviceID LIKE '%VID_1532&PID_%'" `
            -Property PNPDeviceID,ConfigManagerErrorCode,Name,Service `
            -ErrorAction Stop
    )
}
catch {
    Add-ScanError 'Win32_PnPEntity filtered' $_.Exception
    try {
        $cimPnp = @(
            Get-CimInstance Win32_PnPEntity -ErrorAction Stop |
            Where-Object {
                [string]$_.PNPDeviceID -match '(?i)VID_1532&PID_[0-9A-F]{4}'
            }
        )
    }
    catch {
        Add-ScanError 'Win32_PnPEntity fallback-full' $_.Exception
    }
}

# ---------------------------------------------------------------------------
# 3) Signed driver associations
# ---------------------------------------------------------------------------
$signed = @()
try {
    $signed = @(
        Get-CimInstance Win32_PnPSignedDriver `
            -Filter "DeviceID LIKE '%VID_1532&PID_%'" `
            -Property DeviceID,DriverProviderName,InfName,DeviceName,DriverVersion `
            -ErrorAction Stop
    )
}
catch {
    Add-ScanError 'Win32_PnPSignedDriver filtered' $_.Exception
    try {
        $signed = @(
            Get-CimInstance Win32_PnPSignedDriver -ErrorAction Stop |
            Where-Object {
                [string]$_.DeviceID -match '(?i)VID_1532&PID_[0-9A-F]{4}'
            }
        )
    }
    catch {
        Add-ScanError 'Win32_PnPSignedDriver fallback-full' $_.Exception
    }
}

# ---------------------------------------------------------------------------
# 4) Historical/alternate USB + HID enum paths
# ---------------------------------------------------------------------------
$registryRows = New-Object System.Collections.Generic.List[object]
foreach ($rootName in @('USB','HID')) {
    $root = "HKLM:\SYSTEM\CurrentControlSet\Enum\$rootName"
    try {
        if (-not (Test-Path -LiteralPath $root)) { continue }

        Get-ChildItem -LiteralPath $root -ErrorAction Stop |
        Where-Object {
            $_.PSChildName -match '(?i)^VID_1532&PID_[0-9A-F]{4}'
        } |
        ForEach-Object {
            $deviceKey = $_

            Get-ChildItem -LiteralPath $deviceKey.PSPath -ErrorAction SilentlyContinue |
            ForEach-Object {
                $v = Get-ItemProperty -LiteralPath $_.PSPath -ErrorAction SilentlyContinue

                $friendlyName = Get-OptionalPropertyString $v 'FriendlyName'
                $deviceDesc = Get-OptionalPropertyString $v 'DeviceDesc'
                $service = Get-OptionalPropertyString $v 'Service'
                $mfg = Get-OptionalPropertyString $v 'Mfg'

                $registryRows.Add([ordered]@{
                    instanceId   = "$rootName\$($deviceKey.PSChildName)\$($_.PSChildName)"
                    friendlyName = $friendlyName
                    deviceDesc   = $deviceDesc
                    service      = $service
                    manufacturer = $mfg
                    source       = "Registry-$rootName"
                }) | Out-Null
            }
        }
    }
    catch {
        Add-ScanError "Registry-$rootName" $_.Exception
    }
}

# ---------------------------------------------------------------------------
# 5) DriverStore mapping (read-only pnputil /enum-drivers)
# ---------------------------------------------------------------------------
$pnputilText = ''
try {
    $pnputilText = (& "$env:SystemRoot\System32\pnputil.exe" /enum-drivers 2>&1 | Out-String -Width 4096)
}
catch {
    Add-ScanError 'pnputil /enum-drivers' $_.Exception
}

$oemToOriginal = @{}
$allRazerInf = New-Object System.Collections.Generic.List[string]

foreach ($block in @(
    [regex]::Split([string]$pnputilText,'(?:\r?\n){2,}') |
    Where-Object { $_.Trim() }
)) {
    $oem = [regex]::Match($block,'(?i)\boem\d+\.inf\b')
    $origMatches = [regex]::Matches(
        $block,
        '(?i)\b(?:rzdevu_[0-9a-f]{4}_[a-z0-9]+|rzcommonu)\.inf\b'
    )

    if ($origMatches.Count -gt 0) {
        $name = $origMatches[0].Value.ToLowerInvariant()

        if (-not $allRazerInf.Contains($name)) {
            $allRazerInf.Add($name) | Out-Null
        }

        if ($oem.Success) {
            $oemToOriginal[$oem.Value.ToLowerInvariant()] = $name
        }
    }
}

# ---------------------------------------------------------------------------
# Merge all discovered PIDs
# ---------------------------------------------------------------------------
$pids = New-Object System.Collections.Generic.List[string]

foreach ($row in $pnpCmdRows) {
    $DevicePid = Get-PidFromId ([string]$row.instanceId)
    if ($DevicePid -and -not $pids.Contains($DevicePid)) { $pids.Add($DevicePid) | Out-Null }
}
foreach ($row in $cimPnp) {
    $DevicePid = Get-PidFromId ([string]$row.PNPDeviceID)
    if ($DevicePid -and -not $pids.Contains($DevicePid)) { $pids.Add($DevicePid) | Out-Null }
}
foreach ($row in $signed) {
    $DevicePid = Get-PidFromId ([string]$row.DeviceID)
    if ($DevicePid -and -not $pids.Contains($DevicePid)) { $pids.Add($DevicePid) | Out-Null }
}
foreach ($row in $registryRows) {
    $DevicePid = Get-PidFromId ([string]$row.instanceId)
    if ($DevicePid -and -not $pids.Contains($DevicePid)) { $pids.Add($DevicePid) | Out-Null }
}
foreach ($inf in $allRazerInf) {
    if ($inf -match '(?i)^rzdevu_([0-9a-f]{4})_') {
        $DevicePid = $Matches[1].ToUpperInvariant()
        if (-not $pids.Contains($DevicePid)) { $pids.Add($DevicePid) | Out-Null }
    }
}

# ---------------------------------------------------------------------------
# Build connections
# ---------------------------------------------------------------------------
$connections = New-Object System.Collections.Generic.List[object]

foreach ($DevicePid in @($pids | Sort-Object)) {
    $pattern = "VID_${VendorId}&PID_$DevicePid"

    $cmdNodes = @(
        $pnpCmdRows |
        Where-Object { [string]$_.instanceId -like "*$pattern*" }
    )

    $cimNodes = @(
        $cimPnp |
        Where-Object { [string]$_.PNPDeviceID -like "*$pattern*" }
    )

    $signedRows = @(
        $signed |
        Where-Object { [string]$_.DeviceID -like "*$pattern*" }
    )

    $regRows = @(
        $registryRows |
        Where-Object { [string]$_.instanceId -like "*$pattern*" }
    )

    # presentAtScan is deliberately a PHYSICAL USB/HID path state. RZVIRTUAL
    # and RZCONTROL are binding evidence, not proof that the physical
    # connection itself is active.
    $physicalCmdNodes = @(
        $cmdNodes | Where-Object { [string]$_.instanceId -match '^(?i)(USB|HID)\\' }
    )
    $physicalCimNodes = @(
        $cimNodes | Where-Object { [string]$_.PNPDeviceID -match '^(?i)(USB|HID)\\' }
    )
    $present = ($physicalCmdNodes.Count -gt 0 -or $physicalCimNodes.Count -gt 0)

    $names = @()
    $names += @($cmdNodes | ForEach-Object { $_.name })
    $names += @($cimNodes | ForEach-Object { $_.Name })
    $names += @($signedRows | ForEach-Object { $_.DeviceName })
    $names += @($regRows | ForEach-Object { $_.friendlyName })
    $names += @($regRows | ForEach-Object { $_.deviceDesc })

    $model = Best-Model $names $DevicePid

    $infs = New-Object System.Collections.Generic.List[string]
    foreach ($row in $signedRows) {
        $name = ([string]$row.InfName).ToLowerInvariant()
        if ($oemToOriginal.ContainsKey($name)) {
            $name = [string]$oemToOriginal[$name]
        }
        if ($name -and -not $infs.Contains($name)) {
            $infs.Add($name) | Out-Null
        }
    }
    foreach ($name in $allRazerInf) {
        if (
            $name -match "(?i)^rzdevu_$($DevicePid.ToLowerInvariant())_" -and
            -not $infs.Contains($name)
        ) {
            $infs.Add($name) | Out-Null
        }
    }

    $services = New-Object System.Collections.Generic.List[string]
    foreach ($name in @($cimNodes | ForEach-Object { $_.Service })) {
        if (
            $name -and
            [string]$name -match '(?i)^Rz(?:Dev_[0-9a-f]{4}|Common)$' -and
            -not $services.Contains([string]$name)
        ) {
            $services.Add([string]$name) | Out-Null
        }
    }
    foreach ($name in @($regRows | ForEach-Object { $_.service })) {
        if (
            $name -and
            [string]$name -match '(?i)^Rz(?:Dev_[0-9a-f]{4}|Common)$' -and
            -not $services.Contains([string]$name)
        ) {
            $services.Add([string]$name) | Out-Null
        }
    }

    $expected = "RzDev_$($DevicePid.ToLowerInvariant())"
    $hasVcon = @(
        $infs |
        Where-Object { $_ -match '(?i)_vcon\.inf$' }
    ).Count -gt 0

    if ($hasVcon -and -not $services.Contains($expected)) {
        $services.Add($expected) | Out-Null
    }

    # Prefer CIM nodes because they include problem code + service.
    $nodeOut = @(
        $cimNodes |
        ForEach-Object {
            [ordered]@{
                instanceId = [string]$_.PNPDeviceID
                name = [string]$_.Name
                service = [string]$_.Service
                problemCode = [int]$_.ConfigManagerErrorCode
                present = $true
            }
        }
    )

    # If CIM did not expose the device, retain Get-PnpDevice evidence.
    if ($nodeOut.Count -eq 0) {
        $nodeOut = @(
            $cmdNodes |
            ForEach-Object {
                [ordered]@{
                    instanceId = [string]$_.instanceId
                    name = [string]$_.name
                    service = ''
                    problemCode = 0
                    present = $true
                }
            }
        )
    }

    $razerInfs = @(
        $infs | Where-Object { $_ -match '(?i)^(?:rzdevu_[0-9a-f]{4}_[a-z0-9]+|rzcommonu)\.inf$' }
    )
    $inboxInfs = @(
        $infs | Where-Object { $_ -notmatch '(?i)^(?:rzdevu_[0-9a-f]{4}_[a-z0-9]+|rzcommonu)\.inf$' }
    )
    $hasRzDevInf = @($razerInfs | Where-Object { $_ -match "(?i)^rzdevu_$($DevicePid.ToLowerInvariant())_" }).Count -gt 0
    $hasRzDevService = @($services | Where-Object { $_ -ieq "RzDev_$($DevicePid.ToLowerInvariant())" }).Count -gt 0
    $usesRazerFilterStack = ($hasRzDevInf -or $hasRzDevService)
    $hasVcon = @($razerInfs | Where-Object { $_ -match '(?i)_vcon\.inf$' }).Count -gt 0
    $hasDeviceFilterInf = @(
        $razerInfs | Where-Object { $_ -match '(?i)_(?:dkm|mpos|kbd|kbd2|mou|mou2)\.inf$' }
    ).Count -gt 0

    $connections.Add([ordered]@{
        pid = $DevicePid
        modelName = $model
        productKey = (Product-Key $model $DevicePid)
        connectionType = (Connection-Type $model $present $DevicePid)
        connectionTypeSource = (Connection-Type-Source $model $DevicePid)
        presentAtScan = $present
        driverStack = $(if($usesRazerFilterStack){'razer-filter'}else{'windows-inbox'})
        driverInfNames = @($infs)
        razerDriverInfNames = @($razerInfs)
        inboxDriverInfNames = @($inboxInfs)
        serviceNames = @($services)
        capabilities = [ordered]@{
            requiresRzVirtual = $hasVcon
            requiresRzControl = $hasVcon
            requiresRazerBoundNodes = $usesRazerFilterStack
            requiresDeviceFilters = $hasDeviceFilterInf
        }
        nodes = @($nodeOut)
    }) | Out-Null
}

# ---------------------------------------------------------------------------
# Required products = products/connections actually present during setup.
# ---------------------------------------------------------------------------
$products = New-Object System.Collections.Generic.List[object]

# Connections are OrderedDictionary objects. In Windows PowerShell 5.1,
# "Group-Object productKey" does not reliably resolve dictionary keys and can
# collapse all devices into one empty group. Group explicitly through the
# dictionary indexer instead.
$groups = @(
    $connections |
    Group-Object -Property { [string]$_['productKey'] }
)

foreach ($group in $groups) {
    $presentConnections = @(
        $group.Group |
        Where-Object { [bool]$_['presentAtScan'] }
    )

    if ($presentConnections.Count -eq 0) { continue }

    $firstPresent = $presentConnections | Select-Object -First 1
    $name = [string]$firstPresent['modelName']

    $pidsFor = @(
        $group.Group |
        ForEach-Object { [string]$_['pid'] } |
        Where-Object { $_ } |
        Sort-Object -Unique
    )

    $key = [string]$group.Name
    if (-not $key) {
        # Never emit an invalid required product with an empty identity.
        $fallbackPid = [string]$firstPresent['pid']
        $key = Product-Key $name $fallbackPid
    }

    $products.Add([ordered]@{
        key = $key
        name = $name
        required = $true
        connectionPids = $pidsFor
    }) | Out-Null
}

# ---------------------------------------------------------------------------
# Logical product IDs from local AppEngine evidence (read-only).
# ---------------------------------------------------------------------------
$logical = New-Object System.Collections.Generic.List[string]
$logicalLatest = @{}
$mainLog = Join-Path $env:LOCALAPPDATA 'Razer\RazerAppEngine\User Data\Logs\main.log'

if (Test-Path -LiteralPath $mainLog) {
    try {
        foreach ($line in @(
            Get-Content -LiteralPath $mainLog -Tail 12000 -ErrorAction Stop
        )) {
            $idMatch = [regex]::Match(
                [string]$line,
                '(?i)product(?:Id|_id)["\\]*\s*[:=]\s*([0-9]+)'
            )
            $powerMatch = [regex]::Match(
                [string]$line,
                '(?i)isPowerOn["\\]*\s*[:=]\s*(true|false)'
            )

            if ($idMatch.Success -and $powerMatch.Success) {
                $logicalLatest[[string]$idMatch.Groups[1].Value] =
                    ([string]$powerMatch.Groups[1].Value -ieq 'true')
            }
        }
    }
    catch {
        Add-ScanError 'AppEngine main.log' $_.Exception
    }
}

foreach ($id in @($logicalLatest.Keys | Sort-Object)) {
    if ($logicalLatest[$id]) {
        $logical.Add([string]$id) | Out-Null
    }
}

# Windows PowerShell 5.1 can throw "Argument types do not match" when
# generic List[T] instances containing ordered dictionaries are embedded
# directly in another [ordered] hashtable. Materialize every generic list
# as a plain PowerShell array first.
$productArray = @()
if ($products.Count -gt 0) {
    $productArray = [object[]]$products.ToArray()
}

$connectionArray = @()
if ($connections.Count -gt 0) {
    $connectionArray = [object[]]$connections.ToArray()
}

$logicalArray = @()
if ($logical.Count -gt 0) {
    $logicalArray = [string[]]$logical.ToArray()
}

$pidArray = @()
if ($pids.Count -gt 0) {
    $pidArray = [string[]]$pids.ToArray()
}

$registryArray = @()
if ($registryRows.Count -gt 0) {
    $registryArray = [object[]]$registryRows.ToArray()
}

$driverStoreInfArray = @()
if ($allRazerInf.Count -gt 0) {
    $driverStoreInfArray = [string[]]$allRazerInf.ToArray()
}

$errorArray = @()
if ($errors.Count -gt 0) {
    $errorArray = [object[]]$errors.ToArray()
}

$inventory = [ordered]@{
    schemaVersion = 2
    toolVersion = $ToolVersion
    scanVersion = $ScanVersion
    createdAt = (Get-Date).ToUniversalTime().ToString('o')
    vendorId = $VendorId
    computer = $env:COMPUTERNAME
    products = $productArray
    productGroups = @(
        $groups |
        ForEach-Object {
            [ordered]@{
                key = [string]$_.Name
                count = @($_.Group).Count
                pids = @(
                    $_.Group |
                    ForEach-Object { [string]$_['pid'] } |
                    Where-Object { $_ } |
                    Sort-Object -Unique
                )
            }
        }
    )
    connections = $connectionArray
    logicalProductIds = $logicalArray
    sourceSummary = @(
        "Get-PnpDevice=$($pnpCmdRows.Count)",
        "CIM-PnP=$($cimPnp.Count)",
        "SignedDriver=$($signed.Count)",
        "Registry=$($registryArray.Count)",
        "DriverStoreINF=$($driverStoreInfArray.Count)"
    )
}

$debug = [ordered]@{
    schemaVersion = 1
    scannerVersion = $ScanVersion
    toolVersion = $ToolVersion
    startedAt = $started.ToUniversalTime().ToString('o')
    finishedAt = (Get-Date).ToUniversalTime().ToString('o')
    outputPath = $OutputPath
    counts = [ordered]@{
        getPnpDevicePresent = $pnpCmdRows.Count
        cimPnp = $cimPnp.Count
        signedDrivers = $signed.Count
        registryRows = $registryArray.Count
        driverStoreRazerInf = $driverStoreInfArray.Count
        discoveredPids = $pidArray.Count
        connections = $connectionArray.Count
        requiredProducts = $productArray.Count
        logicalProductIds = $logicalArray.Count
    }
    discoveredPids = @($pidArray | Sort-Object)
    presentPnpDevices = @($pnpCmdRows | Select-Object -First 200)
    cimPnpDevices = @(
        $cimPnp |
        Select-Object -First 200 |
        ForEach-Object {
            [ordered]@{
                pnpDeviceId = [string]$_.PNPDeviceID
                name = [string]$_.Name
                service = [string]$_.Service
                problemCode = [int]$_.ConfigManagerErrorCode
            }
        }
    )
    signedDriverSample = @(
        $signed |
        Select-Object -First 200 |
        ForEach-Object {
            [ordered]@{
                deviceId = [string]$_.DeviceID
                deviceName = [string]$_.DeviceName
                provider = [string]$_.DriverProviderName
                infName = [string]$_.InfName
                driverVersion = [string]$_.DriverVersion
            }
        }
    )
    registrySample = @($registryArray | Select-Object -First 200)
    driverStoreInf = $driverStoreInfArray
    products = $productArray
    connections = $connectionArray
    logicalProductIds = $logicalArray
    errors = $errorArray
}

$debugJson = $debug | ConvertTo-Json -Depth 14
[System.IO.File]::WriteAllText($DebugJsonPath, $debugJson, $utf8NoBom)

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("=== RAZER SETUP SCANNER DEBUG $ScanVersion ===") | Out-Null
$lines.Add("Zeit: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff'))") | Out-Null
$lines.Add("OutputPath: $OutputPath") | Out-Null
$lines.Add("") | Out-Null
$lines.Add("Get-PnpDevice present: $($pnpCmdRows.Count)") | Out-Null
$lines.Add("CIM PnP:               $($cimPnp.Count)") | Out-Null
$lines.Add("SignedDriver:          $($signed.Count)") | Out-Null
$lines.Add("Registry rows:         $($registryRows.Count)") | Out-Null
$lines.Add("DriverStore Razer INF: $($allRazerInf.Count)") | Out-Null
$lines.Add("PIDs:                  $(@($pids | Sort-Object) -join ', ')") | Out-Null
$lines.Add("Connections:           $($connections.Count)") | Out-Null
$lines.Add("Required products:     $($products.Count)") | Out-Null
$lines.Add("") | Out-Null

foreach ($p in $products) {
    $lines.Add("PRODUCT: key=$($p.key) | $($p.name) | PIDs=$($p.connectionPids -join ',')") | Out-Null
}
foreach ($c in $connections) {
    $lines.Add(
        "CONNECTION: PID=$($c.pid) present=$($c.presentAtScan) type=$($c.connectionType) stack=$($c.driverStack) rzv=$($c.capabilities.requiresRzVirtual) rzc=$($c.capabilities.requiresRzControl) filters=$($c.capabilities.requiresDeviceFilters) model=$($c.modelName)"
    ) | Out-Null
}
if ($errors.Count -gt 0) {
    $lines.Add("") | Out-Null
    $lines.Add("ERRORS:") | Out-Null
    foreach ($e in $errors) {
        $lines.Add("$($e.stage): $($e.type) | $($e.message)") | Out-Null
    }
}

[System.IO.File]::WriteAllText(
    $DebugTextPath,
    ($lines -join [Environment]::NewLine),
    $utf8NoBom
)

if ($productArray.Count -eq 0 -or $connectionArray.Count -eq 0) {
    Write-Error "Keine aktuell verbundenen Razer-Produkte erkannt. Debug: $DebugJsonPath"
    exit 2
}

$inventoryJson = $inventory | ConvertTo-Json -Depth 14
[System.IO.File]::WriteAllText($OutputPath, $inventoryJson, $utf8NoBom)

Write-Output "SETUP_OK products=$($productArray.Count) connections=$($connectionArray.Count) debug=$DebugJsonPath"
exit 0
