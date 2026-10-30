param(
    [switch]$Stop,
    [switch]$CheckOnly,
    [switch]$Watchdog,
    [switch]$AllowDirect,
    [int]$ParentPid = 0
)

$ErrorActionPreference = 'Stop'

$proxyKey         = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
$endpoint         = '127.0.0.1:10897'
$statePath        = Join-Path $PSScriptRoot 'vpn-proxy-state.clixml'
$xrayPath         = Join-Path $PSScriptRoot 'v2rayN\v2rayN-windows-64\bin\Xray\xray.exe'
$blockConfig      = Join-Path $PSScriptRoot 'vpn-client-block.json'
$fragScript       = Join-Path $PSScriptRoot 'vpn-fragment.py'
$eventName        = 'Local\VPN-Finland-Stop'
$cleanupMutexName = 'Local\VPN-Finland-Cleanup'
$runMutexName     = 'Local\VPN-Finland-Run'
$proxyNames       = @('ProxyEnable', 'ProxyServer', 'ProxyOverride', 'AutoConfigURL')
$envNames         = @('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY')
$candidates       = @(
    @{ Name = '443-frag';  Config = (Join-Path $PSScriptRoot 'vpn-client-443-frag.json') },
    @{ Name = '2053-frag'; Config = (Join-Path $PSScriptRoot 'vpn-client-2053-frag.json') },
    @{ Name = '2053';      Config = (Join-Path $PSScriptRoot 'vpn-client-2053.json') },
    @{ Name = '443';       Config = (Join-Path $PSScriptRoot 'vpn-client-443.json') }
)

Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class VpnInternetSettings {
    [DllImport("wininet.dll", SetLastError = true)]
    public static extern bool InternetSetOption(IntPtr handle, int option, IntPtr buffer, int length);
}
public static class VpnEnv {
    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, IntPtr wParam, string lParam, uint fuFlags, uint uTimeout, out IntPtr lpdwResult);
    public static void Broadcast() {
        IntPtr res;
        SendMessageTimeout(new IntPtr(0xffff), 0x1A, IntPtr.Zero, "Environment", 2, 5000, out res);
    }
}
'@

function Notify-ProxyChange {
    [void][VpnInternetSettings]::InternetSetOption([IntPtr]::Zero, 39, [IntPtr]::Zero, 0)
    [void][VpnInternetSettings]::InternetSetOption([IntPtr]::Zero, 37, [IntPtr]::Zero, 0)
}

function Get-ProxySnapshot {
    $s = Get-ItemProperty -LiteralPath $proxyKey
    $present = @()
    $values = @{}
    foreach ($name in $proxyNames) {
        if ($s.PSObject.Properties.Name -contains $name) {
            $present += $name
            $values[$name] = $s.$name
        }
    }
    return @{ Present = $present; Values = $values }
}

function Apply-ProxySet($snapshot) {
    foreach ($name in $proxyNames) {
        if ($snapshot.Present -contains $name) {
            $type = 'String'
            if ($name -eq 'ProxyEnable') { $type = 'DWord' }
            New-ItemProperty -LiteralPath $proxyKey -Name $name -Value $snapshot.Values[$name] -PropertyType $type -Force | Out-Null
        } else {
            Remove-ItemProperty -LiteralPath $proxyKey -Name $name -ErrorAction SilentlyContinue
        }
    }
    Notify-ProxyChange
}

function Apply-ProxyOn {
    New-ItemProperty -LiteralPath $proxyKey -Name ProxyServer -Value $endpoint -PropertyType String -Force | Out-Null
    New-ItemProperty -LiteralPath $proxyKey -Name ProxyOverride -Value '<local>;localhost;127.*;192.168.*;10.*' -PropertyType String -Force | Out-Null
    Remove-ItemProperty -LiteralPath $proxyKey -Name AutoConfigURL -ErrorAction SilentlyContinue
    New-ItemProperty -LiteralPath $proxyKey -Name ProxyEnable -Value 1 -PropertyType DWord -Force | Out-Null
    Notify-ProxyChange
}

function Get-EnvSnapshot {
    $present = @()
    $values = @{}
    foreach ($name in $envNames) {
        $v = [Environment]::GetEnvironmentVariable($name, 'User')
        if ($null -ne $v) { $present += $name; $values[$name] = $v }
    }
    return @{ Present = $present; Values = $values }
}

function Apply-EnvOn {
    [Environment]::SetEnvironmentVariable('HTTP_PROXY', 'http://127.0.0.1:10897', 'User')
    [Environment]::SetEnvironmentVariable('HTTPS_PROXY', 'http://127.0.0.1:10897', 'User')
    [Environment]::SetEnvironmentVariable('ALL_PROXY', 'http://127.0.0.1:10897', 'User')
    [Environment]::SetEnvironmentVariable('NO_PROXY', 'localhost,127.0.0.1,::1,.ru,.su,.xn--p1ai,192.168.0.0/16,10.0.0.0/8', 'User')
    [VpnEnv]::Broadcast()
}

function Apply-EnvSet($snapshot) {
    foreach ($name in $envNames) {
        if ($snapshot.Present -contains $name) {
            [Environment]::SetEnvironmentVariable($name, $snapshot.Values[$name], 'User')
        } else {
            [Environment]::SetEnvironmentVariable($name, $null, 'User')
        }
    }
    [VpnEnv]::Broadcast()
}

function Stop-OwnedCore($state) {
    if (-not $state.CoreId) { return }
    $p = Get-Process -Id $state.CoreId -ErrorAction SilentlyContinue
    if ($p) {
        $started = $p.StartTime.ToUniversalTime().Ticks
        if (-not $state.CoreStarted -or $started -eq $state.CoreStarted) {
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        }
    }
}

function Restore-SessionState {
    $m = New-Object Threading.Mutex($false, $cleanupMutexName)
    $acquired = $false
    try {
        try { $acquired = $m.WaitOne(10000) } catch [Threading.AbandonedMutexException] { $acquired = $true }
        if (-not (Test-Path -LiteralPath $statePath)) { return $false }
        $state = Import-Clixml -LiteralPath $statePath
        $current = Get-ItemProperty -LiteralPath $proxyKey
        if ($current.ProxyServer -eq $endpoint) { Apply-ProxySet $state }
        if ($state.EnvPresent -or $state.EnvValues) {
            Apply-EnvSet $state
        }
        Remove-Item -LiteralPath $statePath -ErrorAction SilentlyContinue
        Stop-OwnedCore $state
        Stop-OwnedRelay $state
        return $true
    } finally {
        if ($acquired) { try { $m.ReleaseMutex() } catch { } }
        $m.Dispose()
    }
}

function Test-Tunnel {
    param([string]$Url = 'https://www.gstatic.com/generate_204', [int]$Timeout = 6)
    $code = & curl.exe --noproxy localhost --proxy "http://$endpoint" --silent --max-time $Timeout --output NUL --write-out '%{http_code}' $Url
    if ($LASTEXITCODE -ne 0) { return $false }
    return ($code -eq '204' -or $code -eq '200')
}

function Test-ExitIp {
    $ip = & curl.exe --noproxy localhost --proxy "http://$endpoint" --silent --max-time 8 'https://api.ipify.org'
    if ($LASTEXITCODE -ne 0) { return $false }
    return ($ip.Trim() -eq '193.233.138.42')
}

function Test-BrowserPath {
    try {
        $proxy = [System.Net.WebRequest]::GetSystemWebProxy()
        $resolved = $proxy.GetProxy([uri]'https://www.gstatic.com/generate_204').AbsoluteUri
        if ($resolved -notlike '*10897*') { return $false }
        $r = Invoke-WebRequest -Uri 'https://www.gstatic.com/generate_204' -UseBasicParsing -TimeoutSec 12
        return ($r.StatusCode -eq 204 -or $r.StatusCode -eq 200)
    } catch {
        return $false
    }
}

function Wait-ProxyPort {
    param([int]$TimeoutMs = 8000)
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while ($sw.ElapsedMilliseconds -lt $TimeoutMs) {
        $c = New-Object Net.Sockets.TcpClient
        try { $c.Connect('127.0.0.1', 10897); return $true }
        catch { Start-Sleep -Milliseconds 150 }
        finally { $c.Dispose() }
    }
    return $false
}

function Stop-Core($proc) {
    if ($proc) {
        $proc.Refresh()
        if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
    }
}

function Stop-Relay($proc) { Stop-Core $proc }

function Stop-OwnedRelay($state) {
    if (-not $state.RelayId) { return }
    $p = Get-Process -Id $state.RelayId -ErrorAction SilentlyContinue
    if ($p) {
        $started = $p.StartTime.ToUniversalTime().Ticks
        if (-not $state.RelayStarted -or $started -eq $state.RelayStarted) {
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        }
    }
}

function Start-Fragment {
    $py = (Get-Command python -ErrorAction SilentlyContinue).Source
    $argList = @($fragScript)
    if (-not $py) {
        $py = (Get-Command py -ErrorAction SilentlyContinue).Source
        if ($py) { $argList = @('-3', $fragScript) }
    }
    if (-not $py) { return $null }
    if (-not (Test-Path -LiteralPath $fragScript)) { return $null }
    $p = Start-Process -FilePath $py -ArgumentList $argList -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while ($sw.ElapsedMilliseconds -lt 8000) {
        if (Get-NetTCPConnection -LocalPort 10899 -State Listen -ErrorAction SilentlyContinue) { return $p }
        $p.Refresh()
        if ($p.HasExited) { return $null }
        Start-Sleep -Milliseconds 150
    }
    Stop-Relay $p
    return $null
}

function Start-Core {
    param([string]$ConfigPath)
    & $xrayPath run -test -c $ConfigPath | Out-Null
    if ($LASTEXITCODE -ne 0) { return $null }
    $p = Start-Process -FilePath $xrayPath -ArgumentList @('run', '-c', ('"{0}"' -f $ConfigPath)) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru
    if (-not (Wait-ProxyPort)) { Stop-Core $p; return $null }
    return $p
}

function Select-Candidate {
    param([int]$StartIndex = 0)
    for ($offset = 0; $offset -lt $candidates.Count; $offset++) {
        $idx = ($StartIndex + $offset) % $candidates.Count
        $cfg = $candidates[$idx].Config
        if (-not (Test-Path -LiteralPath $cfg)) { continue }
        $core = Start-Core $cfg
        if (-not $core) { continue }
        if ((Test-Tunnel) -and (Test-ExitIp)) {
            return @{ Index = $idx; Core = $core }
        }
        Stop-Core $core
    }
    return $null
}

function Save-State($s) { $s | Export-Clixml -LiteralPath $statePath }

if ($Watchdog) {
    if ($ParentPid -gt 0) {
        while (Get-Process -Id $ParentPid -ErrorAction SilentlyContinue) { Start-Sleep -Seconds 1 }
    }
    try { [void](Restore-SessionState) } catch { }
    exit 0
}

if ($Stop) {
    try {
        $s = [Threading.EventWaitHandle]::OpenExisting($eventName)
        [void]$s.Set()
        $s.Dispose()
    } catch { }
    Start-Sleep -Milliseconds 900
    try {
        if (Restore-SessionState) { Write-Host 'Previous proxy and environment settings restored.' }
        else { Write-Host 'No active VPN session found.' }
    } catch {
        Write-Host ("Restore failed: " + $_.Exception.Message) -ForegroundColor Red
    }
    exit 0
}

$runMutex = New-Object Threading.Mutex($false, $runMutexName)
$locked = $false
$core = $null
$relay = $null
$signal = $null
$sessionActive = $false
$state = $null
$snapshot = $null
$envSnapshot = $null
$exitCode = 0

try {
    try { $locked = $runMutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $locked = $true }
    if (-not $locked) { throw 'VPN launcher is already running.' }
    if (Test-Path -LiteralPath $statePath) { throw 'An interrupted session was found. Run VPN-Stop.bat first.' }
    if (-not (Test-Path -LiteralPath $xrayPath)) { throw 'Xray executable is missing.' }
    if (Get-NetAdapter | Where-Object { $_.Name -like 'happ*' -and $_.Status -eq 'Up' }) {
        throw 'Disconnect Happ TUN before starting this launcher.'
    }
    $settings = Get-ItemProperty -LiteralPath $proxyKey
    if ($settings.ProxyEnable -eq 1) { throw 'Disable Happ or another active system proxy first.' }
    if (Get-NetTCPConnection -LocalPort 10897 -State Listen -ErrorAction SilentlyContinue) {
        throw 'Local port 10897 is already in use.'
    }

    Write-Host 'Starting TLS fragmentation relay (anti-TSPU)...'
    $relay = Start-Fragment
    if ($relay) { Write-Host 'Fragmentation relay on 127.0.0.1:10899/10900.' }
    else { Write-Host 'WARNING: fragmentation relay unavailable; plain endpoints only.' -ForegroundColor Yellow }

    Write-Host 'Selecting a working endpoint (fragmented 443/2053, then plain)...'
    $selected = Select-Candidate 0
    if (-not $selected) { throw 'Neither Reality endpoint responded. Check the network and try again.' }
    $core = $selected.Core
    $candidateIndex = $selected.Index
    Write-Host ("Connected via port {0}. YouTube: HTTP 200. Exit IP: 193.233.138.42" -f $candidates[$candidateIndex].Name)

    if ($CheckOnly) {
        Write-Host 'CheckOnly passed. Windows proxy settings were not changed.'
        Stop-Core $core
        $core = $null
        Stop-Relay $relay
        $relay = $null
        exit 0
    }

    $snapshot = Get-ProxySnapshot
    $envSnapshot = Get-EnvSnapshot
    $state = @{
        Present        = $snapshot.Present
        Values         = $snapshot.Values
        EnvPresent     = $envSnapshot.Present
        EnvValues      = $envSnapshot.Values
        CoreId         = $core.Id
        CoreStarted    = $core.StartTime.ToUniversalTime().Ticks
        RelayId        = if ($relay) { $relay.Id } else { $null }
        RelayStarted   = if ($relay) { $relay.StartTime.ToUniversalTime().Ticks } else { $null }
        CandidateIndex = $candidateIndex
    }
    Save-State $state

    Start-Process -FilePath 'powershell.exe' -WindowStyle Hidden -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath, '-Watchdog', '-ParentPid', $PID
    ) | Out-Null

    Apply-ProxyOn
    Apply-EnvOn
    $sessionActive = $true

    if (-not (Test-BrowserPath)) {
        throw 'Windows proxy did not pass the browser check. Rolling back to keep internet working.'
    }

    Write-Host 'VPN is ON. Russian sites go direct; blocked sites (Claude, Codex, Antigravity, YouTube) go via Finland.'
    Write-Host 'Proxy env vars set for new CLI processes (reopen your terminal once).'
    Write-Host 'Press Enter or Q to stop. Closing this window with X is also safe.'

    $signal = New-Object Threading.EventWaitHandle($false, [Threading.EventResetMode]::ManualReset, $eventName)
    $fail = 0
    $lastCheck = [DateTime]::UtcNow
    $nextRetry = [DateTime]::MinValue
    $mode = 'proxy'

    while ($true) {
        if ($signal.WaitOne(1000)) { break }
        if (-not [Console]::IsInputRedirected -and [Console]::KeyAvailable) {
            $key = [Console]::ReadKey($true).Key
            if ($key -eq 'Enter' -or $key -eq 'Q') { break }
        }

        if ($mode -eq 'proxy') {
            if ((([DateTime]::UtcNow) - $lastCheck).TotalSeconds -ge 5) {
                $lastCheck = [DateTime]::UtcNow
                $core.Refresh()
                if ($core.HasExited -or -not (Test-Tunnel)) { $fail++ } else { $fail = 0 }
                if ($fail -ge 3) {
                    Write-Host 'Tunnel unstable, switching endpoint...' -ForegroundColor Yellow
                    Stop-Core $core
                    $core = $null
                    Start-Sleep -Milliseconds 400
                    $alt = Select-Candidate ($candidateIndex + 1)
                    if ($alt) {
                        $core = $alt.Core
                        $candidateIndex = $alt.Index
                        $state.CoreId = $core.Id
                        $state.CoreStarted = $core.StartTime.ToUniversalTime().Ticks
                        $state.CandidateIndex = $candidateIndex
                        Save-State $state
                        $fail = 0
                        Write-Host ("Reconnected via port {0}." -f $candidates[$candidateIndex].Name)
                    } else {
                        $fail = 0
                        if ($AllowDirect) {
                            Apply-ProxySet $snapshot
                            $sessionActive = $false
                            Write-Host 'No endpoint available. VPN paused (traffic goes DIRECT). Enter or Q to stop.' -ForegroundColor Yellow
                        } else {
                            $b = Start-Core $blockConfig
                            if ($b) {
                                $core = $b
                                $state.CoreId = $core.Id
                                $state.CoreStarted = $core.StartTime.ToUniversalTime().Ticks
                                Save-State $state
                                $mode = 'block'
                                Write-Host 'No endpoint available. Fail-closed: foreign traffic BLOCKED (no IP leak), RU sites still work.' -ForegroundColor Yellow
                            } else {
                                Apply-ProxySet $snapshot
                                $sessionActive = $false
                                Write-Host 'Fallback failed. VPN paused. Enter or Q to stop.' -ForegroundColor Red
                            }
                        }
                        $nextRetry = [DateTime]::UtcNow.AddSeconds(20)
                    }
                }
            }
        }
        else {
            if (-not $core -or $core.HasExited) {
                $b = Start-Core $blockConfig
                if ($b) { $core = $b }
            }
            if ([DateTime]::UtcNow -ge $nextRetry) {
                $nextRetry = [DateTime]::UtcNow.AddSeconds(20)
                Stop-Core $core
                $core = $null
                Start-Sleep -Milliseconds 300
                $sel = Select-Candidate 0
                if ($sel) {
                    $core = $sel.Core
                    $candidateIndex = $sel.Index
                    $state.CoreId = $core.Id
                    $state.CoreStarted = $core.StartTime.ToUniversalTime().Ticks
                    $state.CandidateIndex = $candidateIndex
                    Save-State $state
                    if (-not $sessionActive) { Apply-ProxyOn; $sessionActive = $true }
                    $mode = 'proxy'
                    $fail = 0
                    Write-Host ("VPN reconnected via port {0}." -f $candidates[$candidateIndex].Name) -ForegroundColor Green
                } else {
                    $b = Start-Core $blockConfig
                    if ($b) { $core = $b }
                }
            }
        }
    }
} catch {
    Write-Host ("ERROR: " + $_.Exception.Message) -ForegroundColor Red
    $exitCode = 1
} finally {
    try {
        if ($sessionActive -or (Test-Path -LiteralPath $statePath)) {
            [void](Restore-SessionState)
            Write-Host 'Previous Windows proxy and environment settings restored.'
        }
    } catch {
        Write-Host ("Cleanup failed: " + $_.Exception.Message + ' Run VPN-Stop.bat.') -ForegroundColor Red
        $exitCode = 1
    }
    if ($core) { Stop-Core $core }
    if ($relay) { Stop-Relay $relay }
    if ($signal) { $signal.Dispose() }
    if ($locked) { $runMutex.ReleaseMutex() }
    $runMutex.Dispose()
}
exit $exitCode
