# Script to update inbound port from 2053 to 2087 via 3X-UI API

$baseUrl = "https://193.233.138.42:8443/pYjH5z6vA2oXm0Ytt9"

# Step 1: Get session cookie and CSRF token
$resp = curl -k -s -D - "$baseUrl/" --max-time 15 2>$null
$cookie = [regex]::Match($resp, '3x-ui=([^;]+)').Groups[1].Value
$csrf = [regex]::Match($resp, 'csrf-token" content="([^"]+)').Groups[1].Value
Write-Output "CSRF: $csrf"

# Step 2: Login
$loginResult = curl -k -s -c C:\Users\MiPro\Desktop\VPN\cookies_update.txt -b "3x-ui=$cookie" -H "X-CSRF-Token: $csrf" -H "Content-Type: application/json" -X POST "$baseUrl/login" -d '{"username":"igorsvincov@yandex.ru","password":"IgoR@090362"}' --max-time 15 2>$null
Write-Output "Login: $loginResult"

# Step 3: Get current inbound 2
$inbound2Raw = curl -k -s -b C:\Users\MiPro\Desktop\VPN\cookies_update.txt -H "X-CSRF-Token: $csrf" "$baseUrl/panel/api/inbounds/get/2" --max-time 15 2>$null
$inbound2 = $inbound2Raw | ConvertFrom-Json

if (-not $inbound2.success) {
    Write-Output "Failed to get inbound 2: $inbound2Raw"
    exit 1
}

$obj = $inbound2.obj
Write-Output "Current port: $($obj.port)"
Write-Output "Current remark: $($obj.remark)"

# Step 4: Modify the port from 2053 to 2087
# The 3X-UI update API expects form data with specific fields

$settings = $obj.settings | ConvertTo-Json -Depth 10 -Compress
$streamSettings = $obj.streamSettings | ConvertTo-Json -Depth 10 -Compress
$sniffing = $obj.sniffing | ConvertTo-Json -Depth 10 -Compress

# Build form data for update
$updateBody = @{
    up = $obj.up
    down = $obj.down
    total = $obj.total
    remark = "VLESS-Reality-2087"
    enable = "true"
    expiryTime = $obj.expiryTime
    listen = ""
    port = 2087
    protocol = "vless"
    settings = $settings
    streamSettings = $streamSettings
    sniffing = $sniffing
    tag = "in-2087-tcp"
    subSortIndex = $obj.subSortIndex
} | ConvertTo-Json -Depth 10 -Compress

Write-Output "Sending update..."
$updateResult = curl -k -s -b C:\Users\MiPro\Desktop\VPN\cookies_update.txt -H "X-CSRF-Token: $csrf" -H "Content-Type: application/json" -X POST "$baseUrl/panel/api/inbounds/update/2" -d $updateBody --max-time 15 2>$null
Write-Output "Update result: $updateResult"

# Also update inbound 1 (port 443 -> port 8880)
$inbound1Raw = curl -k -s -b C:\Users\MiPro\Desktop\VPN\cookies_update.txt -H "X-CSRF-Token: $csrf" "$baseUrl/panel/api/inbounds/get/1" --max-time 15 2>$null
$inbound1 = $inbound1Raw | ConvertFrom-Json

if ($inbound1.success) {
    $obj1 = $inbound1.obj
    Write-Output "Inbound 1 current port: $($obj1.port)"
    
    $settings1 = $obj1.settings | ConvertTo-Json -Depth 10 -Compress
    $streamSettings1 = $obj1.streamSettings | ConvertTo-Json -Depth 10 -Compress
    $sniffing1 = $obj1.sniffing | ConvertTo-Json -Depth 10 -Compress
    
    $updateBody1 = @{
        up = $obj1.up
        down = $obj1.down
        total = $obj1.total
        remark = "VLESS-Reality-8880"
        enable = "true"
        expiryTime = $obj1.expiryTime
        listen = ""
        port = 8880
        protocol = "vless"
        settings = $settings1
        streamSettings = $streamSettings1
        sniffing = $sniffing1
        tag = "in-8880-tcp"
        subSortIndex = $obj1.subSortIndex
    } | ConvertTo-Json -Depth 10 -Compress
    
    $updateResult1 = curl -k -s -b C:\Users\MiPro\Desktop\VPN\cookies_update.txt -H "X-CSRF-Token: $csrf" -H "Content-Type: application/json" -X POST "$baseUrl/panel/api/inbounds/update/1" -d $updateBody1 --max-time 15 2>$null
    Write-Output "Inbound 1 update result: $updateResult1"
}
