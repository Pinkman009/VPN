$baseUrl = "https://193.233.138.42:8443/pYjH5z6vA2oXm0Ytt9"
$cookieFile = "$PSScriptRoot\c_test.txt"
$loginJsonFile = "$PSScriptRoot\login_payload.json"

Set-Content -Path $loginJsonFile -Value '{"username":"igorsvincov@yandex.ru","password":"IgoR@090362"}'

# 1. Get initial cookie and csrf
$init = curl.exe -k -s -D - "$baseUrl/" --max-time 15
$raw = $init -join "`n"
$cookieMatch = [regex]::Match($raw, '3x-ui=([^;]+)')
$csrfMatch = [regex]::Match($raw, 'csrf-token" content="([^"]+)')

$cookie = $cookieMatch.Groups[1].Value
$csrf = $csrfMatch.Groups[1].Value
Write-Host "Got cookie: $cookie"
Write-Host "Got CSRF: $csrf"

# 2. Login
$loginRes = curl.exe -k -s -c $cookieFile -b "3x-ui=$cookie" -H "X-CSRF-Token: $csrf" -H "Content-Type: application/json" -X POST "$baseUrl/login" -d "@$loginJsonFile" --max-time 15
Write-Host "Login response: $loginRes"

# 3. Get inbounds
$inboundsRes = curl.exe -k -s -b $cookieFile -H "X-CSRF-Token: $csrf" "$baseUrl/panel/api/inbounds/list" --max-time 15
$inboundsRes | Out-File -FilePath "$PSScriptRoot\inbounds.json" -Encoding utf8
Write-Host "Inbounds saved to inbounds.json"
