$baseUrl = "https://193.233.138.42:8443/pYjH5z6vA2oXm0Ytt9"
$cookieFile = "$PSScriptRoot\c_upd.txt"
$loginJson = "$PSScriptRoot\login_payload.json"

# 1. Login
$init = curl.exe -k -s -D - "$baseUrl/" --max-time 15
$raw = $init -join "`n"
$cookie = [regex]::Match($raw, '3x-ui=([^;]+)').Groups[1].Value
$csrf = [regex]::Match($raw, 'csrf-token" content="([^"]+)').Groups[1].Value

$loginRes = curl.exe -k -s -c $cookieFile -b "3x-ui=$cookie" -H "X-CSRF-Token: $csrf" -H "Content-Type: application/json" -X POST "$baseUrl/login" -d "@$loginJson" --max-time 15
Write-Host "Login: $loginRes"

# 2. Get inbound 2
$in2raw = curl.exe -k -s -b $cookieFile -H "X-CSRF-Token: $csrf" "$baseUrl/panel/api/inbounds/get/2" --max-time 15
$in2str = $in2raw -join ""

# Parse JSON
$in2json = $in2str | ConvertFrom-Json
$obj = $in2json.obj

# Update streamSettings realitySettings
$stream = $obj.streamSettings | ConvertFrom-Json
$stream.realitySettings.serverNames = @("193-233-138-42.sslip.io")
$obj.streamSettings = ($stream | ConvertTo-Json -Compress)

$updatedPayload = ($obj | ConvertTo-Json -Depth 10 -Compress)
Set-Content -Path "$PSScriptRoot\inbound2_payload.json" -Value $updatedPayload -Encoding utf8

# Send update
$updateRes = curl.exe -k -s -b $cookieFile -H "X-CSRF-Token: $csrf" -H "Content-Type: application/json" -X POST "$baseUrl/panel/api/inbounds/update/2" -d "@$PSScriptRoot\inbound2_payload.json" --max-time 15
Write-Host "Update Inbound 2: $updateRes"
