[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$OutputPath,
    [string]$ToolVersion = '2.3.1',
    [string]$KnownPids = '',
    [string]$TargetProductKey = ''
)

# Fast live connection probe 1.0.1 for Razer Health Monitor v2.3.1.
# Read-only and present-only: no registry history, DriverStore or INF traversal.
# It enumerates current Razer PnP nodes once and performs at most one root
# Get-PnpDeviceProperty call for each currently present Razer PID.

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$ProbeVersion = '1.0.1'
$VendorId = '1532'
$started = Get-Date
$errors = New-Object System.Collections.Generic.List[object]
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function Add-ProbeError {
    param([string]$Stage, [System.Exception]$Exception)
    $errors.Add([ordered]@{
        stage = $Stage
        type = if ($Exception) { $Exception.GetType().FullName } else { '' }
        message = if ($Exception) { $Exception.Message } else { '' }
    }) | Out-Null
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

function Normalize-ProductIdentity {
    param([string]$Value)
    $s = Clean-Name $Value
    if (-not $s) { return '' }
    if ($s -match '(?i)^(USB Composite Device|USB Input Device|HID-compliant .+|HID Keyboard Device|Razer Control Device|\(Standard .+\)|Microsoft)$') {
        return ''
    }
    $s = $s.ToLowerInvariant()
    $s = $s -replace '\brazer\b',''
    $s = $s -replace '(?i)\b(?:wireless usb dongle|usb dongle|dongle|receiver|wired usb|wired|usb cable|cable)\b',''
    $s = $s -replace '[^a-z0-9]+',' '
    return (($s -replace '\s+',' ').Trim())
}

function Get-ExplicitRole {
    param([object[]]$Names)
    $joined = (@($Names | ForEach-Object { Clean-Name ([string]$_) } | Where-Object { $_ }) -join ' | ')
    if ($joined -match '(?i)\b(?:wireless usb dongle|usb dongle|dongle|receiver|wireless connection)\b') {
        return 'wireless-dongle'
    }
    if ($joined -match '(?i)\b(?:wired usb|usb cable|cable connection|wired connection)\b') {
        return 'wired-usb'
    }
    return ''
}

function Get-DeviceClass {
    param([object[]]$Rows, [string]$ModelName)
    $primary = @(
        $Rows |
        Where-Object {
            [string]$_.InstanceId -match '(?i)^HID\\VID_1532&PID_[0-9A-F]{4}&MI_00\\' -and
            [string]$_.Class -match '(?i)^(Mouse|Keyboard)$'
        } |
        ForEach-Object { ([string]$_.Class).ToLowerInvariant() } |
        Sort-Object -Unique
    )
    if ($primary.Count -eq 1) { return [string]$primary[0] }

    $modelClass = @(
        $Rows |
        Where-Object {
            (Clean-Name ([string]$_.FriendlyName)) -eq (Clean-Name $ModelName) -and
            [string]$_.Class -match '(?i)^(Mouse|Keyboard)$'
        } |
        ForEach-Object { ([string]$_.Class).ToLowerInvariant() } |
        Sort-Object -Unique
    )
    if ($modelClass.Count -eq 1) { return [string]$modelClass[0] }

    $classes = @(
        $Rows |
        Where-Object { [string]$_.Class -match '(?i)^(Mouse|Keyboard)$' } |
        ForEach-Object { ([string]$_.Class).ToLowerInvariant() } |
        Sort-Object -Unique
    )
    if ($classes.Count -eq 1) { return [string]$classes[0] }
    return 'device'
}

$known = @{}
foreach ($raw in @($KnownPids -split ',')) {
    $devicePid = ([string]$raw).Trim().ToUpperInvariant()
    if ($devicePid -match '^[0-9A-F]{4}$') { $known[$devicePid] = $true }
}

$pnpRows = @()
try {
    if (-not (Get-Command Get-PnpDevice -ErrorAction SilentlyContinue)) {
        throw 'Get-PnpDevice is unavailable.'
    }
    $pnpRows = @(
        Get-PnpDevice -PresentOnly -ErrorAction Stop |
        Where-Object { [string]$_.InstanceId -match '(?i)VID_1532&PID_[0-9A-F]{4}' } |
        ForEach-Object {
            [pscustomobject]@{
                InstanceId = [string]$_.InstanceId
                FriendlyName = [string]$_.FriendlyName
                Class = [string]$_.Class
                Status = [string]$_.Status
            }
        }
    )
}
catch {
    Add-ProbeError 'Get-PnpDevice present-only' $_.Exception
}

$presentPids = @(
    $pnpRows |
    ForEach-Object { Get-PidFromId ([string]$_.InstanceId) } |
    Where-Object { $_ } |
    Sort-Object -Unique
)

$probePids = @()
if ($TargetProductKey) {
    # Guided learning may need to discover a previously unknown connection PID.
    $probePids = @($presentPids)
}
else {
    # Normal live presence refresh is deliberately limited to already-known PIDs.
    $probePids = @(
        $presentPids | Where-Object { $known.ContainsKey([string]$_) }
    )
}

$presentByPid = @{}
foreach ($devicePid in $probePids) {
    $rows = @($pnpRows | Where-Object { (Get-PidFromId ([string]$_.InstanceId)) -eq $devicePid })
    $root = @(
        $rows |
        Where-Object { [string]$_.InstanceId -match "(?i)^USB\\VID_${VendorId}&PID_$devicePid\\" } |
        Sort-Object InstanceId -Unique |
        Select-Object -First 1
    )
    $rootId = ''
    $productName = ''
    $productKey = ''
    $identitySource = 'none'
    $identityConfidence = 'none'
    if ($root.Count -gt 0) {
        $rootId = [string]$root[0].InstanceId
        try {
            $props = @(
                Get-PnpDeviceProperty -InstanceId $rootId -ErrorAction Stop |
                Where-Object { [string]$_.KeyName -in @('DEVPKEY_Device_BusReportedDeviceDesc','DEVPKEY_Device_FriendlyName','DEVPKEY_Device_DeviceDesc') }
            )
            $bus = @($props | Where-Object { [string]$_.KeyName -eq 'DEVPKEY_Device_BusReportedDeviceDesc' } | Select-Object -First 1)
            if ($bus.Count -gt 0 -and [string]$bus[0].Data) {
                $productName = Clean-Name ([string]$bus[0].Data)
                $productKey = Normalize-ProductIdentity $productName
                if ($productKey) {
                    $identitySource = 'bus-reported-device-description'
                    $identityConfidence = 'high'
                }
            }
            if (-not $productKey) {
                foreach ($key in @('DEVPKEY_Device_FriendlyName','DEVPKEY_Device_DeviceDesc')) {
                    $v = @($props | Where-Object { [string]$_.KeyName -eq $key } | Select-Object -First 1)
                    if ($v.Count -gt 0 -and [string]$v[0].Data) {
                        $candidateName = Clean-Name ([string]$v[0].Data)
                        $candidateKey = Normalize-ProductIdentity $candidateName
                        if ($candidateKey) {
                            $productName = $candidateName
                            $productKey = $candidateKey
                            $identitySource = 'root-device-description'
                            $identityConfidence = 'medium'
                            break
                        }
                    }
                }
            }
        }
        catch {
            Add-ProbeError "Get-PnpDeviceProperty $rootId" $_.Exception
        }
    }
    if (-not $productName) {
        $named = @($rows | ForEach-Object { Clean-Name ([string]$_.FriendlyName) } | Where-Object { $_ -match '(?i)\bRazer\b' } | Select-Object -First 1)
        if ($named.Count -gt 0) { $productName = [string]$named[0] }
    }
    $deviceClass = Get-DeviceClass $rows $productName
    $roleNames = @($productName) + @($rows | ForEach-Object { [string]$_.FriendlyName })
    $explicitRole = Get-ExplicitRole $roleNames
    $presentByPid[$devicePid] = [ordered]@{
        pid = $devicePid
        present = $true
        productKey = $productKey
        productName = $productName
        deviceClass = $deviceClass
        identitySource = $identitySource
        identityConfidence = $identityConfidence
        identityVerified = ($identityConfidence -eq 'high' -and [bool]$productKey)
        explicitRole = $explicitRole
        rootInstanceId = $rootId
    }
}

$outConnections = New-Object System.Collections.Generic.List[object]
if ($TargetProductKey) {
    foreach ($devicePid in @($presentPids)) {
        $entry = $presentByPid[$devicePid]
        if ([string]$entry.productKey -eq $TargetProductKey) {
            $outConnections.Add($entry) | Out-Null
        }
    }
}
else {
    foreach ($devicePid in @($known.Keys | Sort-Object)) {
        if ($presentByPid.ContainsKey($devicePid)) {
            $outConnections.Add($presentByPid[$devicePid]) | Out-Null
        }
        else {
            $outConnections.Add([ordered]@{
                pid = $devicePid
                present = $false
                productKey = ''
                productName = ''
                deviceClass = 'device'
                identitySource = 'not-present'
                identityConfidence = 'none'
                identityVerified = $false
                explicitRole = ''
                rootInstanceId = ''
            }) | Out-Null
        }
    }
}

$errorArray = @()
if ($errors.Count -gt 0) { $errorArray = [object[]]$errors.ToArray() }
$result = [ordered]@{
    schemaVersion = 1
    toolVersion = $ToolVersion
    probeVersion = $ProbeVersion
    createdAt = (Get-Date).ToUniversalTime().ToString('o')
    elapsedMs = [int](((Get-Date) - $started).TotalMilliseconds)
    vendorId = $VendorId
    mode = $(if($TargetProductKey){'target-product'}else{'known-connections'})
    targetProductKey = $TargetProductKey
    connections = @($outConnections.ToArray())
    errors = $errorArray
}

$parent = Split-Path -Parent $OutputPath
if ($parent -and -not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
[System.IO.File]::WriteAllText($OutputPath, ($result | ConvertTo-Json -Depth 8), $utf8NoBom)
