# Эталонная рабочая конфигурация и инструкция по откату (SNAPSHOT_AND_ROLLBACK.md)

Данный документ фиксирует **все технические нюансы, параметры и решения**, обеспечивающие стабильную работу VPN на всех типах устройств (Android, iOS, Windows) в условиях фильтрации ТСПУ (DPI) в РФ.

Рядом сохранена папка `backup/`, содержащая эталонную базу 3X-UI (`x-ui.db`), конфигурацию Xray (`config.json`), правила фаервола UFW и параметры ядра Linux.

---

## 1. Сводные параметры инфраструктуры

| Параметр | Значение | Описание / Зачем так настроено |
| :--- | :--- | :--- |
| **Локация VPS** | Хельсинки, Финляндия | AEZA Group LLC, чистый IP `193.233.138.42` |
| **SSH доступ** | `root@193.233.138.42:22` | Пароль: `xXM3yS7biwUj` |
| **Панель управления** | `https://193.233.138.42:8443/pYjH5z6vA2oXm0Ytt9/` | 3X-UI v3.8.5. Логин: `igorsvincov@yandex.ru`, Пароль: `IgoR@090362` |
| **Ядро Xray** | `Xray 26.9.9` (Go 1.27.1) | Установлено в `/usr/local/x-ui/bin/xray-linux-amd64` |
| **База настроек** | `/etc/x-ui/x-ui.db` (SQLite3) | Хранит клиентов, инбаунды, маршруты, настройки подписок |
| **Основной VLESS порт** | `443` (TCP) | VLESS + XTLS-Reality, flow: `xtls-rprx-vision` |
| **Резервный VLESS порт** | `2053` (TCP) | VLESS + XTLS-Reality, flow: `xtls-rprx-vision` |
| **Cloudflare WARP** | SOCKS5 `127.0.0.1:40000` | Чистые резидентные IP для обхода Cloudflare Captcha и банов OpenAI/Claude |

---

## 2. Ключевые нюансы маскировки и обхода блокировок (DPI / ТСПУ)

### Нюанс 1: Выбор SNI (маскировочного домена)
- ❌ **Почему нельзя использовать `apple.com` или `samsung.com`**: ТСПУ Роскомнадзора в 2024–2026 гг. активно отслеживает и отправляет `TCP RST` (сброс соединения) на попытки установить TLS ClientHello с поддельными SNI популярных вендоров к датацентровым IP-адресам за пределами РФ.
- ✅ **Рабочие проверенные SNI**:
  - Порт 443: **`speed.cloudflare.com`** (целевой сервер `speed.cloudflare.com:443`). Не блокируется, имеет огромный легитимный глобальный CDN-трафик, handshake проходит мгновенно.
  - Порт 2053: **`azure.microsoft.com`** (целевой сервер `azure.microsoft.com:443`). Корпоративный трафик Microsoft Azure.

### Нюанс 2: Разница клиентов Android vs iOS (Главная причина сбоя на Android)
- **iOS (приложение Happ / Streisand)**:
  - Использует родные TLS-библиотеки Apple или эмуляцию Chrome (`fp=chrome`). Подключения проходят штатно.
- **Android (приложение Happ, Hiddify, V2RayTun, ядро sing-box)**:
  - ⚠️ **Проблема**: Встроенный в Android-клиенты sing-box uTLS-движок при параметре `fp=chrome` формировал ClientHello с набором расширений и шифров, который Xray на сервере отбрасывал с ошибкой `REALITY: processed invalid connection: failed to read client hello` (сервер получил 33 000+ сброшенных попыток).
  - ✅ **Решение**: Для Android в ключе VLESS **обязательно** указывается параметр **`fp=randomized`**. При этом sing-box генерирует динамический валидный TLS-отпечаток, который сервер Xray принимает без ошибок.

### Нюанс 3: XTLS-Reality ключи и ShortId
- **Public Key (pbk)**: `t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE`
- **Private Key (на сервере)**: `yPkaUKcc-bi4DCT5QgxjLzDTtcaDPEPu2_f_qE35E2s`
- **Client UUID**: `04756662-2f98-44ad-a53a-369d29118670`
- **ShortId (sid)**: `dae45f`
- **Flow**: `xtls-rprx-vision` (прямой шифрованный туннель без двойного TLS-оверхеда).

### Нюанс 4: Особенности клиентов под Windows (Happ / v2rayN)
- **Права администратора для TUN**: Сетевой адаптер Wintun и модификация таблицы системных маршрутов Windows (`0.0.0.0/0`) требуют прав Администратора. При запуске без прав администратора Wintun остаётся в статусе `Disconnected`, и интернет идет напрямую через физический Wi-Fi/LAN (VPN не перехватывает трафик).
- **DNS в режиме System Proxy**: Дефолтный Cloudflare DNS (`1.1.1.1`) деградирует/блокируется ТСПУ. Необходимо использовать `8.8.8.8` или `77.88.8.8`.

---

## 3. Эталонные ключи подключения

### Для Android (Happ, Hiddify, V2RayTun, NekoBox)
```text
vless://04756662-2f98-44ad-a53a-369d29118670@193.233.138.42:443?security=reality&encryption=none&pbk=t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE&headerType=none&fp=randomized&spx=%2F&type=tcp&flow=xtls-rprx-vision&sni=speed.cloudflare.com&sid=dae45f#VLESS-443-Finland-Android
```
*Резервный (порт 2053):*
```text
vless://04756662-2f98-44ad-a53a-369d29118670@193.233.138.42:2053?security=reality&encryption=none&pbk=t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE&headerType=none&fp=randomized&spx=%2F&type=tcp&flow=xtls-rprx-vision&sni=azure.microsoft.com&sid=dae45f#VLESS-2053-Finland-Android
```

### Для iOS (Happ, Streisand)
```text
vless://04756662-2f98-44ad-a53a-369d29118670@193.233.138.42:443?security=reality&encryption=none&pbk=t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE&headerType=none&fp=chrome&spx=%2F&type=tcp&flow=xtls-rprx-vision&sni=speed.cloudflare.com&sid=dae45f#VLESS-443-Aeza-Finland
```

---

## 4. Оптимизация ядра Linux (sysctl)

Файл конфигурации на сервере: `/etc/sysctl.d/99-vpn-optimize.conf`
Копия в репозитории: `backup/99-vpn-optimize.conf`

```ini
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
net.ipv4.tcp_fastopen = 3
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.core.rmem_default = 1048576
net.core.wmem_default = 1048576
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_mtu_probing = 1
```
- **BBR + FQ**: минимизирует задержки при потерях пакетов на мобильных сетях (LTE/5G).
- **TCP Fast Open = 3**: отправка данных в первом SYN-пакете (ускоряет открытие страниц).
- **MTU Probing = 1**: устраняет зависания при нестандартном MTU мобильных операторов (МТС, Т2).
- **Буферы 16 МБ**: гарантируют максимальную скорость стриминга 4K на YouTube.

---

## 5. Маршрутизация через Cloudflare WARP

В `/usr/local/x-ui/bin/config.json` настроен outbound:
```json
{
  "tag": "warp",
  "protocol": "socks",
  "settings": {
    "servers": [{ "address": "127.0.0.1", "port": 40000 }]
  }
}
```
Все запросы к доменам OpenAI (`chatgpt.com`, `api.openai.com`), Anthropic (`claude.ai`), Netflix, Spotify автоматически маршрутизируются через `warp`.

---

## 6. Как выполнить откат (Rollback)

### Вариант А: Автоматический откат в 1 команду
В корне репозитория запустить скрипт:
```powershell
python restore_backup.py
```
Скрипт автоматически:
1. Подключится по SSH к VPS.
2. Остановит службу `x-ui`.
3. Загрузит проверенные файлы из папки `backup/`:
   - `backup/x-ui.db` -> `/etc/x-ui/x-ui.db`
   - `backup/config.json` -> `/usr/local/x-ui/bin/config.json`
   - `backup/99-vpn-optimize.conf` -> `/etc/sysctl.d/99-vpn-optimize.conf`
   - `backup/ufw_user.rules` -> `/etc/ufw/user.rules`
4. Применит настройки ядра `sysctl --system`.
5. Перезапустит `warp-svc` и запустит `x-ui`.
6. Выведет подтверждение активного статуса служб.

### Вариант Б: Ручной откат через SSH-консоль
```bash
# 1. Остановка службы
systemctl stop x-ui

# 2. Восстановление базы из резервной копии (если делали локально на VPS)
cp /etc/x-ui/x-ui.db.bak /etc/x-ui/x-ui.db

# 3. Перезапуск
systemctl start x-ui
systemctl restart warp-svc

# 4. Проверка статуса
systemctl status x-ui
ss -tlnp | grep -E ':443|:2053|:8443'
```
