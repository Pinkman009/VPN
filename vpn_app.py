"""
vpn_app.py - Unblocknet Desktop Client.
Zero-lag instant navigation, smooth vector-antialiased round power button (Happ style),
clean dark theme, and separate tabs for Connection, Plans and Settings.
"""

import os
import sys
import time
import re
import threading
import winreg
import webbrowser
from urllib.parse import urlparse
from PIL import Image, ImageDraw
import customtkinter as ctk
import pystray
from pystray import MenuItem as item
import qrcode

from vpn_core import (
    VpnEngine, NODES, save_settings,
    fetch_subscription_status, create_payment_order, activate_trial_period,
    request_owner_email_code, activate_code, send_diagnostic_report
)
import vpn_speedtest
from vpn_updater import (
    CURRENT_VERSION, check_for_updates, download_update, install_update_and_restart
)

# Modern Cyber-Violet Palette (Happ Inspired)
COLOR_BG = "#0f1019"
COLOR_SURFACE = "#171827"
COLOR_BORDER = "#27293d"
COLOR_PRIMARY = "#7c4dff"
COLOR_PRIMARY_HOVER = "#651fff"
COLOR_CONNECTED = "#00e676"
COLOR_CONNECTED_HOVER = "#00c853"
COLOR_TEXT_WHITE = "#ffffff"
COLOR_TEXT_MUTED = "#8c8fa6"
COLOR_ACCENT_ORANGE = "#ff9100"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
AUTOSTART_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "Unblocknet"


def clean_domain_input(raw):
    """Sanitizes user domain input."""
    s = raw.strip().lower()
    if not s:
        return ""
    if "://" in s:
        try:
            parsed = urlparse(s)
            s = parsed.netloc or parsed.path
        except Exception:
            pass
    s = s.split("/")[0].split(":")[0]
    if s.startswith("www."):
        s = s[4:]
    return re.sub(r"[^\w\.\-]", "", s)


def create_tray_icon(connected=False):
    """Creates a sleek round icon for the Windows notification tray."""
    img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    color = (0, 230, 118, 255) if connected else (124, 77, 255, 255)
    d.ellipse((6, 6, 58, 58), fill=color)
    d.ellipse((18, 18, 46, 46), fill=(15, 16, 25, 255))
    d.ellipse((25, 25, 39, 39), fill=color)
    return img


def create_power_button_image(state="off", size=150):
    """Generates razor-sharp antialiased Happ-style concentric power button."""
    S = size * 3  # 3x supersampling
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = S // 2, S // 2

    if state == "on":
        # Glowing green concentric rings
        d.ellipse((6, 6, S - 6, S - 6), fill=(0, 230, 118, 25))
        d.ellipse((26, 26, S - 26, S - 26), fill=(0, 230, 118, 50))
        d.ellipse((50, 50, S - 50, S - 50), fill=(16, 32, 25, 255), outline=(0, 230, 118, 240), width=6)
        icon_color = (0, 230, 118, 255)
    else:
        # Sleek dark cyber ring (exact Happ match)
        d.ellipse((6, 6, S - 6, S - 6), fill=(26, 28, 42, 35))
        d.ellipse((26, 26, S - 26, S - 26), fill=(30, 33, 50, 75))
        d.ellipse((50, 50, S - 50, S - 50), fill=(22, 24, 36, 255), outline=(58, 62, 92, 220), width=5)
        icon_color = (138, 145, 178, 255)

    # Power icon: arc + vertical stroke
    r = int(S * 0.19)
    arc_box = (cx - r, cy - r, cx + r, cy + r)
    d.arc(arc_box, start=305, end=235, fill=icon_color, width=9)
    d.line((cx, cy - int(r * 1.25), cx, cy - int(r * 0.15)), fill=icon_color, width=9)

    return img.resize((size, size), Image.Resampling.LANCZOS)


# ---------------------------------------------------------------------------
# Share QR Modal Dialog
# ---------------------------------------------------------------------------
class ShareQrDialog(ctk.CTkToplevel):
    def __init__(self, parent, engine):
        super().__init__(parent)
        self.title("Подключение смартфона — QR код")
        self.geometry("480x640")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)
        self.engine = engine
        self.transient(parent)
        self.grab_set()

        self.mode_var = ctk.StringVar(value="⚡ Подписка (2 канала)")

        title = ctk.CTkLabel(
            self,
            text="📱 Подключение смартфона",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=COLOR_PRIMARY
        )
        title.pack(pady=(20, 2))

        sub = ctk.CTkLabel(
            self,
            text="Для приложений Happ, Hiddify, Streisand, v2rayNG",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLOR_TEXT_MUTED
        )
        sub.pack(pady=(0, 12))

        self.seg_btn = ctk.CTkSegmentedButton(
            self,
            values=["⚡ Подписка (2 канала)", "🌐 Порт 443", "🛡️ Резерв 2053"],
            variable=self.mode_var,
            command=self.update_qr,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            selected_color=COLOR_PRIMARY,
            selected_hover_color=COLOR_PRIMARY_HOVER,
            height=36
        )
        self.seg_btn.pack(padx=24, pady=(0, 12), fill="x")

        self.qr_card = ctk.CTkFrame(self, fg_color="white", corner_radius=12, width=220, height=220)
        self.qr_card.pack(pady=4)
        self.qr_card.pack_propagate(False)

        self.qr_label = ctk.CTkLabel(self.qr_card, text="")
        self.qr_label.pack(expand=True)

        self.info_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_MUTED,
            justify="center"
        )
        self.info_label.pack(pady=(12, 10), padx=20)

        self.copy_btn = ctk.CTkButton(
            self,
            text="📋 Скопировать ссылку подписки",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            height=36,
            fg_color=COLOR_SURFACE,
            hover_color="#24263b",
            border_width=1,
            border_color=COLOR_BORDER,
            command=self.copy_link
        )
        self.copy_btn.pack(padx=36, fill="x", pady=(0, 8))

        close_btn = ctk.CTkButton(
            self,
            text="Закрыть",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=36,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            command=self.destroy
        )
        close_btn.pack(padx=36, fill="x", pady=(0, 16))

        self.current_link = ""
        self.update_qr()

    def get_link_and_info(self):
        mode = self.mode_var.get()
        uuid_val = self.engine.settings.get("client_uuid") or "04756662-2f98-44ad-a53a-369d29118670"
        sub_url = self.engine.settings.get("sub_url") or "http://193.233.138.42:80/dlngedpbfjlw072y/83sm0dymf1qn5w9m"

        if "Подписка" in mode:
            link = sub_url
            info = (
                "⚡ Рекомендуется для Happ / Hiddify / Streisand:\n"
                "Загружает сразу 2 независимых канала (443 и 2053) с авто-переключением.\n"
                "В Happ нажмите «+» ➔ «Сканировать QR-код» (или добавьте ссылку из буфера)."
            )
            btn_txt = "📋 Скопировать ссылку подписки"
        elif "443" in mode:
            link = f"vless://{uuid_val}@193.233.138.42:443?security=reality&encryption=none&pbk=t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE&headerType=none&fp=safari&spx=%2F&type=tcp&flow=xtls-rprx-vision&sni=azure.microsoft.com&sid=dae45f#Unblocknet-Azure-443"
            info = (
                "🌐 Основной прямой VLESS ключ (Порт 443 — Microsoft Azure).\n"
                "Отпечаток: Safari (100% защита от ТСПУ и DPI блокировок).\n"
                "Подходит для любого VPN-клиента (Happ, V2Box, Hiddify, v2rayNG)."
            )
            btn_txt = "📋 Скопировать VLESS ключ (Порт 443)"
        else:
            link = f"vless://{uuid_val}@193.233.138.42:2053?security=reality&encryption=none&pbk=t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE&headerType=none&fp=safari&spx=%2F&type=tcp&flow=xtls-rprx-vision&sni=azure.microsoft.com&sid=dae45f#Unblocknet-Azure-2053"
            info = (
                "🛡️ Резервный прямой VLESS ключ (Порт 2053 — Microsoft Azure).\n"
                "Нестандартный защищенный порт. Обходит фильтрацию порта 443.\n"
                "Используйте, если мобильный оператор временно глушит порт 443."
            )
            btn_txt = "📋 Скопировать VLESS ключ (Порт 2053)"

        return link, info, btn_txt

    def update_qr(self, val=None):
        link, info, btn_txt = self.get_link_and_info()
        self.current_link = link
        self.info_label.configure(text=info)
        self.copy_btn.configure(text=btn_txt)

        qr = qrcode.QRCode(box_size=5, border=1)
        qr.add_data(self.current_link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").get_image()
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(200, 200))
        self.qr_label.configure(image=ctk_img)
        self.qr_label.image = ctk_img

    def copy_link(self):
        self.clipboard_clear()
        self.clipboard_append(self.current_link)
        self.copy_btn.configure(text="✔ Скопировано в буфер обмена!")


# ---------------------------------------------------------------------------
# Update Progress & Installation Modal Dialog
# ---------------------------------------------------------------------------
class UpdateProgressDialog(ctk.CTkToplevel):
    def __init__(self, parent, update_info):
        super().__init__(parent)
        self.title("Обновление Unblocknet")
        self.geometry("440x360")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)
        self.parent_app = parent
        self.update_info = update_info
        self.cancel_event = threading.Event()
        self.transient(parent)
        self.grab_set()

        ver = update_info.get("latest_version", "")
        size_mb = update_info.get("asset_size", 0) / (1024 * 1024)

        title = ctk.CTkLabel(
            self,
            text=f"🚀 Вышло обновление v{ver}",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLOR_CONNECTED
        )
        title.pack(pady=(22, 6))

        size_txt = f"Размер обновления: {size_mb:.1f} МБ" if size_mb > 0 else ""
        sub = ctk.CTkLabel(
            self,
            text=f"Загрузка компонентов обновления...\n{size_txt}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_MUTED
        )
        sub.pack(pady=(0, 16))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self, width=360, height=14, corner_radius=7, fg_color="#1d1e30", progress_color=COLOR_PRIMARY)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10)

        # Status text
        self.progress_lbl = ctk.CTkLabel(
            self,
            text="Подготовка к скачиванию...",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_TEXT_WHITE
        )
        self.progress_lbl.pack(pady=6)

        # Action Buttons frame
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=40, pady=(16, 12))

        self.cancel_btn = ctk.CTkButton(
            self.btn_frame,
            text="Отмена",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=34,
            fg_color="#202236",
            hover_color="#2c2e4a",
            command=self.on_cancel
        )
        self.cancel_btn.pack(side="right", padx=(10, 0))

        # Start download thread
        threading.Thread(target=self._start_download, daemon=True).start()

    def _start_download(self):
        url = self.update_info.get("download_url")
        def _cb(downloaded, total, pct):
            dl_mb = downloaded / (1024 * 1024)
            tot_mb = total / (1024 * 1024) if total > 0 else 0
            def _update_ui():
                if not self.winfo_exists():
                    return
                self.progress_bar.set(pct / 100.0)
                self.progress_lbl.configure(text=f"Скачивание: {dl_mb:.1f} МБ / {tot_mb:.1f} МБ ({pct}%)")
            self.after(0, _update_ui)

        ok, path_or_err = download_update(url, progress_callback=_cb, cancel_event=self.cancel_event)
        def _on_done():
            if not self.winfo_exists():
                return
            if ok:
                self.progress_bar.set(1.0)
                self.progress_lbl.configure(text="✔ Обновление скачано! Перезапуск...", text_color=COLOR_CONNECTED)
                self.cancel_btn.configure(state="disabled")
                self.after(1200, lambda: self._apply_and_restart(path_or_err))
            else:
                self.progress_lbl.configure(text=f"Ошибка скачивания: {path_or_err}", text_color="#ff5252")
                self.cancel_btn.configure(text="Закрыть")
        self.after(0, _on_done)

    def _apply_and_restart(self, new_exe):
        try:
            install_update_and_restart(new_exe)
        finally:
            self.parent_app.on_exit_app()

    def on_cancel(self):
        self.cancel_event.set()
        self.destroy()


# ---------------------------------------------------------------------------
# Main Application Window: Unblocknet
# ---------------------------------------------------------------------------
class TeletokApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Unblocknet")
        self.geometry("490x740")
        self.minsize(460, 680)
        self.configure(fg_color=COLOR_BG)

        # Pre-render razor sharp button images
        self.img_btn_off = ctk.CTkImage(light_image=create_power_button_image("off", 146), dark_image=create_power_button_image("off", 146), size=(146, 146))
        self.img_btn_on = ctk.CTkImage(light_image=create_power_button_image("on", 146), dark_image=create_power_button_image("on", 146), size=(146, 146))

        # Engine instance & state
        self.engine = VpnEngine()
        self.tray_icon = None
        self.is_checking_speed = False
        self.is_busy = False
        self.is_owner = False

        # Plan selection state
        self.selected_plan_id = ctk.StringVar(value="1y")
        self.selected_devices = 3
        self.plan_desc_labels = {}
        self.billing_polling = False
        self.current_sub = None
        self.latest_update_info = None

        self.protocol("WM_DELETE_WINDOW", self.on_minimize_to_tray)

        self._build_ui()
        self._update_status_ui()
        self._start_tray()

    def _build_ui(self):
        # 1. Clean Top Header
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=22, pady=(16, 8))

        title_lbl = ctk.CTkLabel(
            self.header,
            text="UNBLOCKNET",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=COLOR_TEXT_WHITE
        )
        title_lbl.pack(side="left")

        tray_icon_btn = ctk.CTkButton(
            self.header,
            text="В трей ▾",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            width=80,
            height=28,
            fg_color=COLOR_SURFACE,
            hover_color="#24263b",
            border_width=1,
            border_color=COLOR_BORDER,
            corner_radius=8,
            command=self.on_minimize_to_tray
        )
        tray_icon_btn.pack(side="right")

        # 2. Ultra-Fast Zero-Lag Nav Bar
        self.nav_frame = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=10, height=42, border_width=1, border_color=COLOR_BORDER)
        self.nav_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.nav_buttons = {}
        tabs = [
            ("connect", "🚀 Подключение"),
            ("billing", "💎 Тарифы"),
            ("settings", "⚙️ Настройки")
        ]

        for idx, (tid, label) in enumerate(tabs):
            btn = ctk.CTkButton(
                self.nav_frame,
                text=label,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                height=34,
                corner_radius=8,
                fg_color=COLOR_PRIMARY if tid == "connect" else "transparent",
                hover_color=COLOR_PRIMARY_HOVER if tid == "connect" else "#202236",
                text_color=COLOR_TEXT_WHITE if tid == "connect" else COLOR_TEXT_MUTED,
                command=lambda target=tid: self.switch_tab(target)
            )
            btn.pack(side="left", fill="both", expand=True, padx=3, pady=3)
            self.nav_buttons[tid] = btn

        # 3. Content Pages Stack Container (Zero-lag switching)
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self._build_tab_connect()
        self._build_tab_billing()
        self._build_tab_settings()

        # Show initial tab
        self.switch_tab("connect")

        # Startup triggers
        is_startup = "--autostart" in sys.argv or "--minimized" in sys.argv
        if is_startup:
            self.after(50, self.withdraw)

        self.after(300, lambda: threading.Thread(target=self._initial_ping, daemon=True).start())
        self.after(500, self.update_subscription_display)

        if self.engine.settings.get("autoconnect", True):
            self.after(800, self._startup_autoconnect)

        self.after(2000, self.check_updates_background)

    def switch_tab(self, tab_name):
        """Instant zero-freeze page switcher."""
        self.page_connect.pack_forget()
        self.page_billing.pack_forget()
        self.page_settings.pack_forget()

        for tid, btn in self.nav_buttons.items():
            if tid == tab_name:
                btn.configure(fg_color=COLOR_PRIMARY, text_color=COLOR_TEXT_WHITE)
            else:
                btn.configure(fg_color="transparent", text_color=COLOR_TEXT_MUTED)

        if tab_name == "connect":
            self.page_connect.pack(fill="both", expand=True)
        elif tab_name == "billing":
            self.page_billing.pack(fill="both", expand=True)
        elif tab_name == "settings":
            self.page_settings.pack(fill="both", expand=True)

    # -----------------------------------------------------------------------
    # TAB 1: CONNECT (Clean Happ Center Layout)
    # -----------------------------------------------------------------------
    def _build_tab_connect(self):
        self.page_connect = ctk.CTkFrame(self.content_container, fg_color="transparent")

        # Update Notification Banner (shows when new version is available on GitHub)
        self.update_banner = ctk.CTkButton(
            self.page_connect,
            text="✨ Доступно обновление! Нажмите для установки",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=36,
            fg_color="#311b92",
            hover_color="#4527a0",
            border_width=1,
            border_color=COLOR_PRIMARY,
            corner_radius=8,
            command=self.start_app_update
        )
        self.update_banner.pack_forget()

        # Centered Big Round Power Button (Pure image without ugly frame artifacts)
        btn_area = ctk.CTkFrame(self.page_connect, fg_color="transparent")
        btn_area.pack(pady=(16, 6))

        self.power_btn = ctk.CTkButton(
            btn_area,
            image=self.img_btn_off,
            text="",
            width=150,
            height=150,
            fg_color="transparent",
            hover_color=COLOR_BG,
            corner_radius=75,
            command=self.toggle_connection
        )
        self.power_btn.pack()

        # Status text below button (Exact Happ style)
        self.status_badge = ctk.CTkLabel(
            self.page_connect,
            text="● ОТКЛЮЧЕНО",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLOR_TEXT_MUTED
        )
        self.status_badge.pack(pady=(4, 8))

        # Quick Trial Banner on Main Screen (Visible for new / expired users)
        self.trial_banner = ctk.CTkButton(
            self.page_connect,
            text="🎁 Активировать 3 дня бесплатно в 1 клик",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=34,
            fg_color="#183628",
            hover_color="#1e4634",
            border_width=1,
            border_color=COLOR_CONNECTED,
            corner_radius=8,
            command=self.activate_trial_action
        )
        # Hidden by default until subscription check completes
        self.trial_banner.pack_forget()

        # Server Node Selector Card
        self.node_card = ctk.CTkFrame(self.page_connect, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        self.node_card.pack(fill="x", pady=(0, 10), ipady=6)
        node_card = self.node_card

        node_header = ctk.CTkFrame(node_card, fg_color="transparent")
        node_header.pack(fill="x", padx=14, pady=(6, 4))

        node_title = ctk.CTkLabel(
            node_header,
            text="Сервер подключения:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_MUTED
        )
        node_title.pack(side="left")

        self.server_ping_badge = ctk.CTkLabel(
            node_header,
            text="🇫🇮 Финляндия",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_TEXT_WHITE
        )
        self.server_ping_badge.pack(side="right")

        node_options = [f"{k}: {v['name']}" for k, v in NODES.items()]
        current_node_key = self.engine.settings.get("selected_node", "443-frag")
        current_node_val = f"{current_node_key}: {NODES.get(current_node_key, {}).get('name', '')}"

        self.node_menu = ctk.CTkOptionMenu(
            node_card,
            values=node_options,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=34,
            fg_color="#1d1e30",
            button_color="#2b2d45",
            button_hover_color=COLOR_PRIMARY,
            command=self.on_node_changed
        )
        self.node_menu.set(current_node_val)
        self.node_menu.pack(fill="x", padx=14, pady=(0, 4))

        # Diagnostics & Speed Card
        self.diag_card = ctk.CTkFrame(self.page_connect, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        self.diag_card.pack(fill="x", pady=(0, 10), ipady=6)

        self.ip_label = ctk.CTkLabel(
            self.diag_card,
            text="Исходящий IP:  Определение...",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_MUTED
        )
        self.ip_label.pack(anchor="w", padx=14, pady=(6, 2))

        self.ping_label = ctk.CTkLabel(
            self.diag_card,
            text="Задержка (Пинг):  -- мс",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_MUTED
        )
        self.ping_label.pack(anchor="w", padx=14, pady=2)

        self.speed_label = ctk.CTkLabel(
            self.diag_card,
            text="Скорость и доступ:  Нажмите кнопку для проверки",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_MUTED
        )
        self.speed_label.pack(anchor="w", padx=14, pady=2)

        self.check_speed_btn = ctk.CTkButton(
            self.diag_card,
            text="⚡ Проверить сервисы (YouTube, ChatGPT, IP)",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=32,
            fg_color="#202236",
            hover_color="#2c2e4a",
            border_width=1,
            border_color=COLOR_BORDER,
            command=self.run_speed_and_diag
        )
        self.check_speed_btn.pack(fill="x", padx=14, pady=(6, 6))

        # Mobile QR Button
        self.share_btn = ctk.CTkButton(
            self.page_connect,
            text="📱 Подключить смартфон через QR-код",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=40,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            corner_radius=10,
            command=self.open_share_dialog
        )
        self.share_btn.pack(fill="x", pady=(0, 4))

    # -----------------------------------------------------------------------
    # TAB 2: BILLING (Dedicated clean tab)
    # -----------------------------------------------------------------------
    def _build_tab_billing(self):
        self.page_billing = ctk.CTkScrollableFrame(self.content_container, fg_color="transparent")

        # Current Subscription Card
        self.sub_card = ctk.CTkFrame(self.page_billing, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        self.sub_card.pack(fill="x", pady=(4, 12), ipady=6)

        self.sub_header = ctk.CTkLabel(
            self.sub_card,
            text="⭐ Подписка: Загрузка статуса...",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLOR_PRIMARY
        )
        self.sub_header.pack(anchor="w", padx=16, pady=(8, 2))

        self.sub_details = ctk.CTkLabel(
            self.sub_card,
            text="Связь с сервером...",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_MUTED
        )
        self.sub_details.pack(anchor="w", padx=16, pady=(0, 8))

        # Device Selector Card
        self.device_card = ctk.CTkFrame(self.page_billing, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        self.device_card.pack(fill="x", pady=(0, 10), ipady=6)

        dev_top = ctk.CTkFrame(self.device_card, fg_color="transparent")
        dev_top.pack(fill="x", padx=16, pady=(8, 2))

        dev_title = ctk.CTkLabel(
            dev_top,
            text="📱 Количество устройств:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLOR_TEXT_WHITE
        )
        dev_title.pack(side="left")

        dev_counter_box = ctk.CTkFrame(dev_top, fg_color="#10111a", corner_radius=8, border_width=1, border_color=COLOR_BORDER)
        dev_counter_box.pack(side="right")

        self.btn_dev_minus = ctk.CTkButton(
            dev_counter_box,
            text="—",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            width=32,
            height=30,
            fg_color="transparent",
            hover_color="#222538",
            command=lambda: self._change_devices(-1)
        )
        self.btn_dev_minus.pack(side="left")

        self.device_count_lbl = ctk.CTkLabel(
            dev_counter_box,
            text="3 устройства",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_PRIMARY,
            width=96
        )
        self.device_count_lbl.pack(side="left", padx=4)

        self.btn_dev_plus = ctk.CTkButton(
            dev_counter_box,
            text="+",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            width=32,
            height=30,
            fg_color="transparent",
            hover_color="#222538",
            command=lambda: self._change_devices(+1)
        )
        self.btn_dev_plus.pack(side="left")

        dev_hint = ctk.CTkLabel(
            self.device_card,
            text="Базовый тариф включает 3 устройства. Дополнительные подключаются со скидкой (от 20 до 35 ₽/мес за устр., до 10 устройств).",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_MUTED,
            wraplength=440,
            justify="left"
        )
        dev_hint.pack(anchor="w", padx=16, pady=(0, 6))

        # Plans Header
        plans_head = ctk.CTkLabel(
            self.page_billing,
            text="Выберите период подписки:",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLOR_TEXT_WHITE
        )
        plans_head.pack(anchor="w", padx=4, pady=(2, 6))

        self.plan_definitions = [
            ("1m", "1 месяц", None),
            ("3m", "3 месяца", "-13%"),
            ("6m", "6 месяцев", "-23%"),
            ("1y", "1 год (Максимум выгоды)", "ХИТ! -33%"),
        ]

        self.plan_radios = {}
        self.plan_desc_labels = {}
        for pid, name, badge in self.plan_definitions:
            card = ctk.CTkFrame(self.page_billing, fg_color=COLOR_SURFACE, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
            card.pack(fill="x", pady=4, ipady=4)

            top_line = ctk.CTkFrame(card, fg_color="transparent")
            top_line.pack(fill="x", padx=12, pady=(4, 2))

            rb = ctk.CTkRadioButton(
                top_line,
                text=f"{name}",
                value=pid,
                variable=self.selected_plan_id,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                fg_color=COLOR_PRIMARY,
                hover_color=COLOR_PRIMARY_HOVER,
                command=self.update_billing_button
            )
            rb.pack(side="left")
            self.plan_radios[pid] = rb

            if badge:
                badge_lbl = ctk.CTkLabel(
                    top_line,
                    text=badge,
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                    fg_color=COLOR_ACCENT_ORANGE,
                    text_color="white",
                    corner_radius=6,
                    padx=7,
                    pady=1
                )
                badge_lbl.pack(side="right")

            desc_lbl = ctk.CTkLabel(
                card,
                text="    Загрузка расчетов...",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=COLOR_TEXT_MUTED
            )
            desc_lbl.pack(anchor="w", padx=14, pady=(0, 4))
            self.plan_desc_labels[pid] = desc_lbl

            def _make_selector(val):
                return lambda e: self._on_plan_card_clicked(val)
            card.bind("<Button-1>", _make_selector(pid))
            top_line.bind("<Button-1>", _make_selector(pid))
            desc_lbl.bind("<Button-1>", _make_selector(pid))

        self.update_plan_card_labels()

        # Trial Period Button
        self.trial_btn = ctk.CTkButton(
            self.page_billing,
            text="🎁 Активировать 3 дня бесплатно (Тестовый период)",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=38,
            fg_color="#183628",
            hover_color="#1e4634",
            border_width=1,
            border_color=COLOR_CONNECTED,
            corner_radius=8,
            command=self.activate_trial_action
        )
        self.trial_btn.pack(fill="x", pady=(10, 6))

        # Clean Pay Button (no mention of payment gateway)
        self.pay_btn = ctk.CTkButton(
            self.page_billing,
            text="Оплатить 1 190 ₽",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=46,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            corner_radius=10,
            command=self.start_yoomoney_payment
        )
        self.pay_btn.pack(fill="x", pady=(6, 6))

        # Status & Notice
        self.billing_status_lbl = ctk.CTkLabel(
            self.page_billing,
            text="Оплата проходит через защищенную платежную форму (банковская карта / СБП)",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_MUTED,
            wraplength=440
        )
        self.billing_status_lbl.pack(pady=(2, 8))

        # Referral & Promocode Card
        self.referral_card = ctk.CTkFrame(self.page_billing, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        self.referral_card.pack(fill="x", pady=(4, 12), ipady=6)

        ref_head = ctk.CTkLabel(
            self.referral_card,
            text="🎁 Реферальная программа — Бонус +14 дней",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLOR_TEXT_WHITE
        )
        ref_head.pack(anchor="w", padx=16, pady=(10, 2))

        ref_desc = ctk.CTkLabel(
            self.referral_card,
            text="Поделитесь Unblocknet с другом: друг получит +7 дней бонуса (10 дней с триалом), а вам начислится +14 дней после его первой оплаты!",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_MUTED,
            wraplength=440,
            justify="left"
        )
        ref_desc.pack(anchor="w", padx=16, pady=(0, 8))

        # Personal Code Sub-section
        my_code_lbl = ctk.CTkLabel(
            self.referral_card,
            text="Ваш персональный промокод для друзей:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_PRIMARY
        )
        my_code_lbl.pack(anchor="w", padx=16, pady=(4, 2))

        my_code_row = ctk.CTkFrame(self.referral_card, fg_color="transparent")
        my_code_row.pack(fill="x", padx=16, pady=(2, 8))

        self.my_ref_code_var = ctk.StringVar(value="Загрузка кода...")
        self.my_ref_code_entry = ctk.CTkEntry(
            my_code_row,
            textvariable=self.my_ref_code_var,
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            height=36,
            fg_color="#10111a",
            border_color=COLOR_BORDER,
            justify="center",
            state="readonly"
        )
        self.my_ref_code_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.copy_ref_btn = ctk.CTkButton(
            my_code_row,
            text="📋 Скопировать",
            width=115,
            height=36,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#27293d",
            hover_color="#363952",
            command=self.copy_referral_code
        )
        self.copy_ref_btn.pack(side="left", padx=(0, 4))

        self.share_ref_btn = ctk.CTkButton(
            my_code_row,
            text="📤 Поделиться",
            width=105,
            height=36,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            command=self.share_referral_code
        )
        self.share_ref_btn.pack(side="left")

        # Divider
        div = ctk.CTkFrame(self.referral_card, fg_color=COLOR_BORDER, height=1)
        div.pack(fill="x", padx=16, pady=(4, 8))

        # Enter Promo Code Sub-section
        enter_code_lbl = ctk.CTkLabel(
            self.referral_card,
            text="Есть промокод от друга или код активации?",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_TEXT_WHITE
        )
        enter_code_lbl.pack(anchor="w", padx=16, pady=(2, 2))

        code_row = ctk.CTkFrame(self.referral_card, fg_color="transparent")
        code_row.pack(fill="x", padx=16, pady=(2, 4))

        self.code_entry = ctk.CTkEntry(
            code_row,
            placeholder_text="Введите промокод (например: UB-XXXX-YYYY-ZZZZ)",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=34,
            fg_color="#1d1e30",
            border_color=COLOR_BORDER
        )
        self.code_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.activate_code_btn = ctk.CTkButton(
            code_row,
            text="Применить",
            width=110,
            height=34,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#183628",
            hover_color="#1e4634",
            border_width=1,
            border_color=COLOR_CONNECTED,
            command=self.activate_code_action
        )
        self.activate_code_btn.pack(side="right")

        self.promo_status_lbl = ctk.CTkLabel(
            self.referral_card,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_MUTED
        )
        self.promo_status_lbl.pack(anchor="w", padx=16, pady=(0, 6))

        # Statistics & History Sub-section
        stats_frame = ctk.CTkFrame(self.referral_card, fg_color="#121320", corner_radius=8)
        stats_frame.pack(fill="x", padx=16, pady=(4, 6), ipady=4)

        stats_head = ctk.CTkLabel(
            stats_frame,
            text="📊 Ваша статистика приглашений:",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=COLOR_TEXT_WHITE
        )
        stats_head.pack(anchor="w", padx=10, pady=(4, 2))

        badges_row = ctk.CTkFrame(stats_frame, fg_color="transparent")
        badges_row.pack(fill="x", padx=10, pady=(2, 4))

        self.ref_stat_invited = ctk.CTkLabel(
            badges_row,
            text="👥 Приглашено: 0",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="#1e2035",
            corner_radius=6,
            padx=8,
            pady=3
        )
        self.ref_stat_invited.pack(side="left", padx=(0, 6))

        self.ref_stat_paid = ctk.CTkLabel(
            badges_row,
            text="💳 Оплатили: 0",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="#1e2035",
            corner_radius=6,
            padx=8,
            pady=3
        )
        self.ref_stat_paid.pack(side="left", padx=(0, 6))

        self.ref_stat_bonus = ctk.CTkLabel(
            badges_row,
            text="⚡ Начислено: +0 дн.",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#183628",
            text_color=COLOR_CONNECTED,
            corner_radius=6,
            padx=8,
            pady=3
        )
        self.ref_stat_bonus.pack(side="left")

        # History list container
        self.ref_history_frame = ctk.CTkFrame(self.referral_card, fg_color="transparent")
        self.ref_history_frame.pack(fill="x", padx=16, pady=(2, 6))

        self.update_billing_button()

    @staticmethod
    def _format_device_count(n):
        if n % 10 == 1 and n % 100 != 11:
            return f"{n} устройство"
        elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
            return f"{n} устройства"
        return f"{n} устройств"

    def _calculate_plan_price(self, plan_id, devices=None):
        if devices is None:
            devices = self.selected_devices
        devices = max(3, min(10, devices))
        base_prices = {"1m": 149, "3m": 390, "6m": 690, "1y": 1190}
        extra_rates = {"1m": 35, "3m": 90, "6m": 150, "1y": 240}
        base = base_prices.get(plan_id, 1190)
        extra = max(0, devices - 3) * extra_rates.get(plan_id, 35)
        return base + extra

    def _change_devices(self, delta):
        new_val = max(3, min(10, self.selected_devices + delta))
        if new_val == self.selected_devices:
            return
        self.selected_devices = new_val
        self.device_count_lbl.configure(text=self._format_device_count(self.selected_devices))
        if hasattr(self, "btn_dev_minus"):
            self.btn_dev_minus.configure(state="disabled" if self.selected_devices <= 3 else "normal")
        if hasattr(self, "btn_dev_plus"):
            self.btn_dev_plus.configure(state="disabled" if self.selected_devices >= 10 else "normal")
        self.update_plan_card_labels()
        self.update_billing_button()

    def update_plan_card_labels(self):
        dev_str = self._format_device_count(self.selected_devices)
        plan_names = {
            "1m": "1 месяц",
            "3m": "3 месяца",
            "6m": "6 месяцев",
            "1y": "1 год (Максимум выгоды)",
        }
        for pid, rb in self.plan_radios.items():
            price = self._calculate_plan_price(pid, self.selected_devices)
            price_fmt = f"{price:,} ₽".replace(",", " ")
            name = plan_names.get(pid, pid)
            rb.configure(text=f"{name} — {price_fmt}")

            desc_lbl = self.plan_desc_labels.get(pid)
            if desc_lbl:
                if pid == "1m":
                    per_dev = round(price / self.selected_devices)
                    desc_lbl.configure(text=f"    {price_fmt} • {dev_str} (~{per_dev} ₽/устр)")
                elif pid == "3m":
                    per_mo = round(price / 3)
                    per_dev = round(per_mo / self.selected_devices)
                    desc_lbl.configure(text=f"    {per_mo} ₽/мес • Скидка 13% • {dev_str} (~{per_dev} ₽/устр/мес)")
                elif pid == "6m":
                    per_mo = round(price / 6)
                    per_dev = round(per_mo / self.selected_devices)
                    desc_lbl.configure(text=f"    {per_mo} ₽/мес • Скидка 23% • {dev_str} (~{per_dev} ₽/устр/мес)")
                elif pid == "1y":
                    per_mo = round(price / 12)
                    per_dev = round(per_mo / self.selected_devices)
                    desc_lbl.configure(text=f"    {per_mo} ₽/мес • Скидка 33% • Хит продаж 🔥 • {dev_str} (~{per_dev} ₽/устр/мес)")

    def _on_plan_card_clicked(self, plan_id):
        self.selected_plan_id.set(plan_id)
        self.update_billing_button()

    def update_billing_button(self):
        pid = self.selected_plan_id.get()
        if pid not in ["1m", "3m", "6m", "1y"]:
            pid = "1y"
            self.selected_plan_id.set("1y")
        price = self._calculate_plan_price(pid, self.selected_devices)
        price_fmt = f"{price:,} ₽".replace(",", " ")
        dev_str = self._format_device_count(self.selected_devices)
        self.pay_btn.configure(text=f"Оплатить {price_fmt} ({dev_str})")

    # -----------------------------------------------------------------------
    # TAB 3: SETTINGS
    # -----------------------------------------------------------------------
    def _build_tab_settings(self):
        self.page_settings = ctk.CTkScrollableFrame(self.content_container, fg_color="transparent")

        # Split-Tunneling Card
        rules_card = ctk.CTkFrame(self.page_settings, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        rules_card.pack(fill="x", pady=(4, 10), ipady=6)

        rules_head = ctk.CTkLabel(
            rules_card,
            text="Раздельная маршрутизация (Split-Tunneling):",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLOR_TEXT_WHITE
        )
        rules_head.pack(anchor="w", padx=14, pady=(8, 4))

        self.rule_mode_var = ctk.StringVar(value="РФ напрямую (DIRECT)")
        self.rule_mode_menu = ctk.CTkSegmentedButton(
            rules_card,
            values=["РФ напрямую (DIRECT)", "Через VPN (PROXY)"],
            variable=self.rule_mode_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            selected_color=COLOR_PRIMARY,
            selected_hover_color=COLOR_PRIMARY_HOVER,
            command=self.on_rule_mode_changed,
            height=32
        )
        self.rule_mode_menu.pack(fill="x", padx=14, pady=(0, 8))

        preset_lbl = ctk.CTkLabel(
            rules_card,
            text="Быстрые пресеты сервисов:",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_MUTED
        )
        preset_lbl.pack(anchor="w", padx=14, pady=(2, 2))

        self.preset_buttons_frame = ctk.CTkFrame(rules_card, fg_color="transparent")
        self.preset_buttons_frame.pack(fill="x", padx=12, pady=(0, 6))

        # Add custom domain
        add_row = ctk.CTkFrame(rules_card, fg_color="transparent")
        add_row.pack(fill="x", padx=14, pady=(4, 6))

        self.domain_entry = ctk.CTkEntry(
            add_row,
            placeholder_text="Например: habr.com или kinopoisk.ru",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=34,
            fg_color="#1d1e30",
            border_color=COLOR_BORDER
        )
        self.domain_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.domain_entry.bind("<Return>", lambda e: self.add_custom_domain())

        self.add_btn = ctk.CTkButton(
            add_row,
            text="+ Добавить",
            width=90,
            height=34,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            command=self.add_custom_domain
        )
        self.add_btn.pack(side="right")

        self.domains_list_frame = ctk.CTkScrollableFrame(rules_card, height=110, fg_color="#11121e", corner_radius=8)
        self.domains_list_frame.pack(fill="x", padx=14, pady=(2, 6))

        # System Options
        sys_card = ctk.CTkFrame(self.page_settings, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        sys_card.pack(fill="x", pady=(0, 10), ipady=6)

        sys_head = ctk.CTkLabel(
            sys_card,
            text="Системные опции:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLOR_TEXT_WHITE
        )
        sys_head.pack(anchor="w", padx=14, pady=(8, 6))

        self.autoconnect_var = ctk.BooleanVar(value=self.engine.settings.get("autoconnect", True))
        self.autoconnect_cb = ctk.CTkCheckBox(
            sys_card,
            text="🚀 Автоподключение при запуске Windows",
            variable=self.autoconnect_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=COLOR_PRIMARY,
            command=self.on_autoconnect_toggled
        )
        self.autoconnect_cb.pack(anchor="w", padx=16, pady=4)

        self.adblock_var = ctk.BooleanVar(value=self.engine.settings.get("adblock_enabled", True))
        self.adblock_cb = ctk.CTkCheckBox(
            sys_card,
            text="🛡️ Блокировка рекламы (AdBlock)",
            variable=self.adblock_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=COLOR_PRIMARY,
            command=self.on_adblock_toggled
        )
        self.adblock_cb.pack(anchor="w", padx=16, pady=(4, 1))

        self.adblock_hint = ctk.CTkLabel(
            sys_card,
            text="Блокирует баннеры, трекеры и рекламу на сайтах. Для вырезания видео-прероллов в плеере YouTube используйте расширение uBlock Origin.",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLOR_TEXT_MUTED,
            wraplength=440,
            justify="left"
        )
        self.adblock_hint.pack(anchor="w", padx=36, pady=(0, 4))

        self.webrtc_btn = ctk.CTkButton(
            sys_card,
            text="🛡️ Защитить WebRTC и IPv6 от утечек (Chrome / Edge)",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=34,
            fg_color="#1e1f32",
            hover_color="#2b2d46",
            border_width=1,
            border_color=COLOR_BORDER,
            command=self.run_webrtc_protection
        )
        self.webrtc_btn.pack(fill="x", padx=16, pady=(8, 4))

        self.heal_btn = ctk.CTkButton(
            sys_card,
            text="🧹 Очистить кэш, освободить порты и починить сеть",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=36,
            fg_color="#183628",
            hover_color="#1e4634",
            border_width=1,
            border_color=COLOR_CONNECTED,
            command=self.run_self_heal
        )
        self.heal_btn.pack(fill="x", padx=16, pady=(4, 6))

        self.report_issue_btn = ctk.CTkButton(
            sys_card,
            text="📋 Отправить отчет об ошибке разработчику",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=34,
            fg_color="#202236",
            hover_color="#2c2e4a",
            border_width=1,
            border_color=COLOR_BORDER,
            command=self.send_error_report_action
        )
        self.report_issue_btn.pack(fill="x", padx=16, pady=(0, 10))

        # App Update Card (Releases)
        self.update_card = ctk.CTkFrame(self.page_settings, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        self.update_card.pack(fill="x", pady=(0, 10), ipady=6)

        update_head = ctk.CTkLabel(
            self.update_card,
            text="🔄 Обновление приложения:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLOR_TEXT_WHITE
        )
        update_head.pack(anchor="w", padx=14, pady=(8, 2))

        self.app_version_lbl = ctk.CTkLabel(
            self.update_card,
            text=f"Текущая версия: v{CURRENT_VERSION}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_MUTED
        )
        self.app_version_lbl.pack(anchor="w", padx=14, pady=(0, 2))

        self.update_status_lbl = ctk.CTkLabel(
            self.update_card,
            text="Готово к проверке обновлений",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_MUTED
        )
        self.update_status_lbl.pack(anchor="w", padx=14, pady=(0, 6))

        update_btns_row = ctk.CTkFrame(self.update_card, fg_color="transparent")
        update_btns_row.pack(fill="x", padx=14, pady=(2, 6))

        self.check_update_btn = ctk.CTkButton(
            update_btns_row,
            text="🔄 Проверить обновления",
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#202236",
            hover_color="#2c2e4a",
            border_width=1,
            border_color=COLOR_BORDER,
            command=lambda: self.check_updates_background(manual=True)
        )
        self.check_update_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.apply_update_btn = ctk.CTkButton(
            update_btns_row,
            text="⚡ Установить обновление",
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#183628",
            hover_color="#1e4634",
            border_width=1,
            border_color=COLOR_CONNECTED,
            command=self.start_app_update
        )
        self.apply_update_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))
        self.apply_update_btn.pack_forget()

        self._refresh_presets()
        self._refresh_domain_list()

    # -----------------------------------------------------------------------
    # Connection Management & State Handlers
    # -----------------------------------------------------------------------
    def toggle_connection(self):
        if self.is_busy:
            return
        self.is_busy = True
        self.power_btn.configure(state="disabled")

        if not self.engine.is_connected:
            # If user has no active subscription, auto-activate 3 days free trial!
            if self.current_sub and not self.current_sub.get("is_active"):
                self.status_badge.configure(text="● АКТИВАЦИЯ ТЕСТА 3 ДНЯ...", text_color=COLOR_PRIMARY)
                threading.Thread(target=self._auto_trial_and_connect, daemon=True).start()
                return

            self.status_badge.configure(text="● ПОДКЛЮЧЕНИЕ...", text_color=COLOR_PRIMARY)
            threading.Thread(target=self._worker_connect, daemon=True).start()
        else:
            self.status_badge.configure(text="● ОТКЛЮЧЕНИЕ...", text_color=COLOR_TEXT_MUTED)
            threading.Thread(target=self._worker_disconnect, daemon=True).start()

    def _auto_trial_and_connect(self):
        try:
            activate_trial_period()
            self.update_subscription_display()
        except Exception:
            pass
        try:
            node = self.engine.settings.get("selected_node", "443-frag")
            ok = self.engine.connect(node)
            self.after(0, self._on_connect_finished, ok)
        except Exception as e:
            self.after(0, self._on_connect_error, str(e))

    def _worker_connect(self):
        try:
            node = self.engine.settings.get("selected_node", "443-frag")
            ok = self.engine.connect(node)
            self.after(0, self._on_connect_finished, ok)
        except Exception as e:
            self.after(0, self._on_connect_error, str(e))

    def _on_connect_error(self, err_msg):
        self.is_busy = False
        self.power_btn.configure(state="normal")
        self._update_status_ui()
        self.status_badge.configure(text="● СБОЙ ПОДКЛЮЧЕНИЯ", text_color="#ff5252")
        print(f"[Unblocknet Connection Error] {err_msg}")
        # Automatically send anonymous crash/error telemetry to GitHub Issues
        threading.Thread(
            target=send_diagnostic_report,
            args=("Автоматический отчет: сбой запуска туннеля", str(err_msg)),
            daemon=True
        ).start()

    def send_error_report_action(self):
        self.report_issue_btn.configure(text="⏳ Отправка отчета...", state="disabled")
        def _worker():
            ok, res_or_url = send_diagnostic_report(
                title="Ручной отчет пользователя о неполадках",
                detail="Пользователь нажал кнопку отправки отчета в приложении Unblocknet."
            )
            def _cb():
                self.report_issue_btn.configure(state="normal")
                if ok:
                    self.report_issue_btn.configure(text="✔ Отчет успешно отправлен разработчику!")
                    self.after(4000, lambda: self.report_issue_btn.configure(text="📋 Отправить отчет об ошибке разработчику"))
                else:
                    self.report_issue_btn.configure(text="✖ Ошибка отправки отчета")
                    self.after(3000, lambda: self.report_issue_btn.configure(text="📋 Отправить отчет об ошибке разработчику"))
            self.after(0, _cb)
        threading.Thread(target=_worker, daemon=True).start()

    # -----------------------------------------------------------------------
    # In-App Auto-Update Methods (Releases)
    # -----------------------------------------------------------------------
    def check_updates_background(self, manual=False):
        if manual:
            self.check_update_btn.configure(text="⏳ Проверка...", state="disabled")
            self.update_status_lbl.configure(text="Проверка обновлений...", text_color=COLOR_PRIMARY)

        def _worker():
            res = check_for_updates()
            self.after(0, self._on_update_check_finished, res, manual)
        threading.Thread(target=_worker, daemon=True).start()

    def _on_update_check_finished(self, res, manual=False):
        self.check_update_btn.configure(text="🔄 Проверить обновления", state="normal")
        self.latest_update_info = res
        if res.get("has_update"):
            new_v = res.get("latest_version")
            self.update_status_lbl.configure(
                text=f"✨ Доступна новая версия v{new_v}! Нажмите «Установить обновление».",
                text_color=COLOR_CONNECTED
            )
            self.apply_update_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))
            # Show banner on main page
            self.update_banner.configure(text=f"✨ Вышло обновление v{new_v} • Установить в 1 клик")
            self.update_banner.pack(before=self.power_btn.master, fill="x", pady=(0, 8))
        else:
            self.apply_update_btn.pack_forget()
            self.update_banner.pack_forget()
            if res.get("error"):
                self.update_status_lbl.configure(text=f"Статус проверки: {res['error']}", text_color=COLOR_TEXT_MUTED)
            else:
                self.update_status_lbl.configure(text="✔ У вас установлена самая свежая версия программы.", text_color=COLOR_CONNECTED)

    def start_app_update(self):
        if self.latest_update_info and self.latest_update_info.get("has_update"):
            UpdateProgressDialog(self, self.latest_update_info)
        else:
            self.check_updates_background(manual=True)

    def _on_connect_finished(self, ok):
        self.is_busy = False
        self.power_btn.configure(state="normal")
        self._update_status_ui()
        if ok:
            threading.Thread(target=self.run_speed_and_diag, daemon=True).start()

    def _worker_disconnect(self):
        self.engine.disconnect()
        self.after(0, self._on_disconnect_finished)

    def _on_disconnect_finished(self):
        self.is_busy = False
        self.power_btn.configure(state="normal")
        self._update_status_ui()

    def _update_status_ui(self):
        conn = self.engine.is_connected
        if conn:
            self.status_badge.configure(text="● ЗАЩИЩЕНО • ТРАФИК ЗАШИФРОВАН", text_color=COLOR_CONNECTED)
            self.power_btn.configure(image=self.img_btn_on)
        else:
            self.status_badge.configure(text="● ОТКЛЮЧЕНО", text_color=COLOR_TEXT_MUTED)
            self.power_btn.configure(image=self.img_btn_off)
        self._update_tray_state()

    def on_node_changed(self, choice):
        node_key = choice.split(":")[0].strip()
        self.engine.settings["selected_node"] = node_key
        save_settings(self.engine.settings)
        if self.engine.is_connected:
            self.toggle_connection()
            self.after(1000, self.toggle_connection)

    # -----------------------------------------------------------------------
    # Subscription & Billing Methods
    # -----------------------------------------------------------------------
    def update_subscription_display(self):
        threading.Thread(target=self._check_subscription_bg, daemon=True).start()

    def _check_subscription_bg(self):
        sub, _, ref = fetch_subscription_status()
        self.after(0, self._render_subscription, sub, ref)

    def _render_subscription(self, sub, ref=None):
        self.current_sub = sub
        if ref:
            self._render_referral(ref)
        if not sub:
            self.sub_header.configure(text="⚠️ Статус подписки: Ошибка соединения", text_color="#e74c3c")
            self.sub_details.configure(text="Проверьте подключение к Интернету или обновите статус.")
            return

        is_owner = sub.get("is_owner", False)
        self.is_owner = is_owner

        if is_owner:
            self.trial_banner.pack_forget()
            self.sub_header.configure(
                text="👑 Владелец • Пожизненный безлимитный доступ",
                text_color=COLOR_CONNECTED
            )
            self.sub_details.configure(
                text="Действует бессрочно • Безлимитно устройств • Максимальный приоритет",
                text_color=COLOR_TEXT_WHITE
            )
            self.trial_btn.configure(state="disabled", text="✔ Пожизненный доступ активен")
            self.pay_btn.configure(state="disabled", text="Оплата не требуется (Владелец)")
            self.billing_status_lbl.configure(text="Ваш аккаунт подтвержден как владелец сервиса.", text_color=COLOR_CONNECTED)
            return

        is_active = sub.get("is_active", False)
        days_left = sub.get("days_left", 0)
        exp_date = sub.get("expiry_date", "--")
        limit_ip = sub.get("limit_ip", 3)

        if is_active:
            self.trial_banner.pack_forget()
            fam_badge = " (Семейный доступ)" if limit_ip >= 6 else ""
            self.sub_header.configure(
                text=f"⭐ Подписка активна (осталось {days_left} дн.)",
                text_color=COLOR_CONNECTED
            )
            self.sub_details.configure(
                text=f"Действует до: {exp_date} • Лимит: до {limit_ip} устройств одновременно{fam_badge}",
                text_color=COLOR_TEXT_WHITE
            )
            if days_left > 3:
                self.trial_btn.configure(state="disabled", text="✔ Подписка активна / Тест использован")
            self.pay_btn.configure(state="normal")
            self.update_billing_button()
        else:
            try:
                self.trial_banner.pack(before=self.node_card, fill="x", pady=(0, 10))
            except Exception:
                pass
            self.sub_header.configure(text="⚠️ Подписка истекла или не активна", text_color="#e74c3c")
            self.sub_details.configure(text="Доступен бесплатный тест на 3 дня или тарифы со скидкой.")
            self.trial_btn.configure(state="normal", text="🎁 Активировать 3 дня бесплатно (Тестовый период)")
            self.pay_btn.configure(state="normal")
            self.update_billing_button()

    def copy_referral_code(self):
        code = self.my_ref_code_var.get().strip()
        if code and not code.startswith("Загрузка"):
            self.clipboard_clear()
            self.clipboard_append(code)
            self.promo_status_lbl.configure(text=f"📋 Промокод {code} скопирован в буфер обмена!", text_color=COLOR_CONNECTED)

    def share_referral_code(self):
        code = self.my_ref_code_var.get().strip()
        if code and not code.startswith("Загрузка"):
            msg = f"Попробуй быстрый VPN без блокировок Unblocknet! Скачай тут: https://github.com/Pinkman009/VPN/releases и введи мой промокод {code} во вкладке «Тарифы» — получишь +7 дней бесплатного доступа!"
            self.clipboard_clear()
            self.clipboard_append(msg)
            self.promo_status_lbl.configure(text="📤 Текст с ссылкой и промокодом скопирован! Отправьте его другу.", text_color=COLOR_CONNECTED)

    def _render_referral(self, ref):
        if not ref:
            return
        code = ref.get("code") or ""
        if code:
            self.my_ref_code_var.set(code)
        self.ref_stat_invited.configure(text=f"👥 Приглашено: {ref.get('friends_invited', 0)}")
        self.ref_stat_paid.configure(text=f"💳 Оплатили: {ref.get('friends_paid', 0)}")
        bonus = ref.get("bonus_days_earned", 0)
        self.ref_stat_bonus.configure(text=f"⚡ Начислено: +{bonus} дн.")

        for child in self.ref_history_frame.winfo_children():
            child.destroy()

        history = ref.get("history") or []
        if history:
            h_lbl = ctk.CTkLabel(
                self.ref_history_frame,
                text="📜 Последние начисления:",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=COLOR_TEXT_MUTED
            )
            h_lbl.pack(anchor="w", pady=(2, 2))
            for item in history[:3]:
                row = ctk.CTkFrame(self.ref_history_frame, fg_color="transparent")
                row.pack(fill="x", pady=1)
                ctk.CTkLabel(row, text=f"• {item.get('date', '')} — {item.get('event', '')}", font=ctk.CTkFont(family="Segoe UI", size=10), text_color=COLOR_TEXT_MUTED).pack(side="left")
                ctk.CTkLabel(row, text=item.get("days", ""), font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=COLOR_CONNECTED).pack(side="right")

    def activate_trial_action(self):
        self.trial_btn.configure(text="⏳ Активация 3 дней...", state="disabled")
        def _worker():
            ok, msg = activate_trial_period()
            def _cb():
                if ok:
                    self.billing_status_lbl.configure(text="🎉 Тестовый период на 3 дня успешно активирован!", text_color=COLOR_CONNECTED)
                    self._check_subscription_bg()
                else:
                    self.billing_status_lbl.configure(text=f"Внимание: {msg}", text_color="#e74c3c")
                    self.trial_btn.configure(state="normal", text="🎁 Попробовать снова")
            self.after(0, _cb)
        threading.Thread(target=_worker, daemon=True).start()

    def activate_code_action(self):
        code = self.code_entry.get().strip()
        if not code:
            self.promo_status_lbl.configure(text="Введите промокод или код активации", text_color="#e74c3c")
            return
        self.activate_code_btn.configure(state="disabled", text="⏳ Проверка...")

        def _worker():
            ok, msg, res = activate_code(code)
            def _cb():
                self.activate_code_btn.configure(state="normal", text="Применить")
                if ok:
                    self.code_entry.delete(0, "end")
                    self.promo_status_lbl.configure(text=f"🎉 {msg}", text_color=COLOR_CONNECTED)
                    self.engine.settings = load_settings()
                    self._check_subscription_bg()
                    if self.engine.is_connected:
                        threading.Thread(target=self._seamless_reconnect, daemon=True).start()
                else:
                    self.promo_status_lbl.configure(text=f"Внимание: {msg}", text_color="#e74c3c")
            self.after(0, _cb)
        threading.Thread(target=_worker, daemon=True).start()

    def _seamless_reconnect(self):
        try:
            self.engine.disconnect()
            time.sleep(0.5)
            self._worker_connect()
        except Exception:
            pass

    def start_yoomoney_payment(self):
        plan_id = self.selected_plan_id.get()
        self.pay_btn.configure(state="disabled", text="⏳ Создание счета...")
        self.billing_status_lbl.configure(text="Формируем защищенную ссылку на оплату...", text_color=COLOR_PRIMARY)

        def _worker():
            ok, pay_url, order_id, plan_info = create_payment_order(plan_id, devices=self.selected_devices)
            self.after(0, self._on_payment_url_ready, ok, pay_url, order_id, plan_info)
        threading.Thread(target=_worker, daemon=True).start()

    def _on_payment_url_ready(self, ok, pay_url, order_id, plan_info):
        if not ok or not pay_url:
            self.pay_btn.configure(state="normal")
            self.update_billing_button()
            self.billing_status_lbl.configure(text=f"Ошибка создания счета: {pay_url}", text_color="#e74c3c")
            return

        webbrowser.open(pay_url)
        self.billing_polling = True
        self.pay_btn.configure(state="disabled", text="Ожидание оплаты...")
        self.billing_status_lbl.configure(
            text="🌐 Форма оплаты открыта в браузере. После подтверждения подписка продлится автоматически...",
            text_color=COLOR_ACCENT_ORANGE
        )

        initial_expiry = self.current_sub.get("expiry_time", 0) if self.current_sub else 0
        self._poll_payment_status(initial_expiry, attempts=60)

    def _poll_payment_status(self, initial_expiry, attempts):
        if not self.billing_polling or attempts <= 0:
            if attempts <= 0 and self.billing_polling:
                self.pay_btn.configure(state="normal")
                self.update_billing_button()
                self.billing_status_lbl.configure(text="Время ожидания истекло. Нажмите 'Оплатить' для повтора.", text_color=COLOR_TEXT_MUTED)
            return

        def _check():
            sub, _ = fetch_subscription_status()
            def _cb():
                if not self.billing_polling:
                    return
                if sub:
                    curr_exp = sub.get("expiry_time", 0)
                    if curr_exp > initial_expiry:
                        self.billing_polling = False
                        self.pay_btn.configure(state="normal")
                        self.update_billing_button()
                        exp_date = sub.get("expiry_date", "--")
                        lim = sub.get("limit_ip", 3)
                        self.billing_status_lbl.configure(
                            text=f"🎉 Оплата получена! Подписка продлена до {exp_date} (лимит: {lim} устр.)!",
                            text_color=COLOR_CONNECTED
                        )
                        self._render_subscription(sub)
                        return
                self.after(3000, lambda: self._poll_payment_status(initial_expiry, attempts - 1))
            self.after(0, _cb)
        threading.Thread(target=_check, daemon=True).start()

    # -----------------------------------------------------------------------
    # Speedtest & Diagnostics
    # -----------------------------------------------------------------------
    def _initial_ping(self):
        try:
            node_key = self.engine.settings.get("selected_node", "443-frag")
            node = NODES.get(node_key, {})
            host = node.get("vps_host", "193.233.138.42")
            port = node.get("vps_port", 443)
            p = vpn_speedtest.measure_tcp_ping(host, port)
            self.after(0, lambda: self.ping_label.configure(text=f"Задержка (Пинг):  {p:.1f} мс" if p else "Задержка (Пинг):  N/A"))
        except Exception:
            pass

    def run_speed_and_diag(self):
        if self.is_checking_speed:
            return
        self.is_checking_speed = True
        self.check_speed_btn.configure(text="⏳ Проверка доступности...", state="disabled")
        threading.Thread(target=self._speed_worker, daemon=True).start()

    def _speed_worker(self):
        ip = vpn_speedtest.get_external_ip()
        node_key = self.engine.settings.get("selected_node", "443-frag")
        node = NODES.get(node_key, {})
        host = node.get("vps_host", "193.233.138.42")
        port = node.get("vps_port", 443)
        ping_val = vpn_speedtest.measure_tcp_ping(host, port)
        acc = vpn_speedtest.check_service_accessibility()
        self.after(0, self._on_speed_finished, ip, ping_val, acc)

    def _on_speed_finished(self, ip, ping_val, acc):
        self.is_checking_speed = False
        self.check_speed_btn.configure(text="⚡ Проверить сервисы (YouTube, ChatGPT, IP)", state="normal")
        self.ip_label.configure(text=f"Исходящий IP:  {ip}")
        self.ping_label.configure(text=f"Задержка (Пинг):  {ping_val:.1f} мс" if ping_val else "Задержка (Пинг):  N/A")

        yt = "✔" if acc.get("YouTube", {}).get("ok") else "✖"
        gpt = "✔" if acc.get("ChatGPT", {}).get("ok") else "✖"
        cld = "✔" if acc.get("Claude", {}).get("ok") else "✖"
        self.speed_label.configure(text=f"YouTube: {yt}  |  ChatGPT: {gpt}  |  Claude: {cld}")

    # -----------------------------------------------------------------------
    # Rules & Preset Handlers
    # -----------------------------------------------------------------------
    def on_rule_mode_changed(self, choice):
        self._refresh_presets()
        self._refresh_domain_list()

    def _refresh_presets(self):
        for w in self.preset_buttons_frame.winfo_children():
            w.destroy()

        mode = "direct" if "DIRECT" in self.rule_mode_var.get() else "proxy"
        if mode == "direct":
            presets = [
                ("Сбер", "sberbank.ru"),
                ("Т-Банк", "t-bank.ru"),
                ("Госуслуги", "gosuslugi.ru"),
                ("VK", "vk.com"),
                ("Кинопоиск", "kinopoisk.ru"),
                ("Ozon", "ozon.ru"),
                ("Wildberries", "wildberries.ru"),
                ("Авито", "avito.ru")
            ]
        else:
            presets = [
                ("YouTube", "youtube.com"),
                ("ChatGPT", "chatgpt.com"),
                ("Instagram", "instagram.com"),
                ("Discord", "discord.com"),
                ("Notion", "notion.so"),
                ("Spotify", "spotify.com"),
            ]

        row = 0
        col = 0
        for label, domain in presets:
            btn = ctk.CTkButton(
                self.preset_buttons_frame,
                text=label,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                height=26,
                fg_color="#1d1e30",
                hover_color="#282a44",
                border_width=1,
                border_color=COLOR_BORDER,
                command=lambda d=domain: self._add_preset_domain(d)
            )
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
            col += 1
            if col > 3:
                col = 0
                row += 1

        for c in range(4):
            self.preset_buttons_frame.grid_columnconfigure(c, weight=1)

    def _add_preset_domain(self, domain):
        mode = "direct" if "DIRECT" in self.rule_mode_var.get() else "proxy"
        if mode == "direct":
            self.engine.add_direct_domain(domain)
        else:
            self.engine.add_proxy_domain(domain)
        self._refresh_domain_list()

    def add_custom_domain(self):
        raw = self.domain_entry.get()
        domain = clean_domain_input(raw)
        if not domain:
            return
        self.domain_entry.delete(0, "end")
        mode = "direct" if "DIRECT" in self.rule_mode_var.get() else "proxy"
        if mode == "direct":
            self.engine.add_direct_domain(domain)
        else:
            self.engine.add_proxy_domain(domain)
        self._refresh_domain_list()

    def remove_custom_domain(self, domain):
        mode = "direct" if "DIRECT" in self.rule_mode_var.get() else "proxy"
        if mode == "direct":
            self.engine.remove_direct_domain(domain)
        else:
            self.engine.remove_proxy_domain(domain)
        self._refresh_domain_list()

    def _refresh_domain_list(self):
        for w in self.domains_list_frame.winfo_children():
            w.destroy()

        mode = "direct" if "DIRECT" in self.rule_mode_var.get() else "proxy"
        key = "custom_direct_domains" if mode == "direct" else "custom_proxy_domains"
        domains = self.engine.settings.get(key, [])

        if not domains:
            empty = ctk.CTkLabel(
                self.domains_list_frame,
                text="Список пуст. Добавьте домены из пресетов выше.",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=COLOR_TEXT_MUTED
            )
            empty.pack(pady=8)
            return

        for d in sorted(domains):
            row = ctk.CTkFrame(self.domains_list_frame, fg_color="#18192b", corner_radius=6)
            row.pack(fill="x", padx=4, pady=2)

            lbl = ctk.CTkLabel(
                row,
                text=d,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=COLOR_TEXT_WHITE
            )
            lbl.pack(side="left", padx=8, pady=3)

            del_btn = ctk.CTkButton(
                row,
                text="✕",
                width=24,
                height=22,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                fg_color="transparent",
                hover_color="#361a24",
                text_color="#ff5252",
                command=lambda target=d: self.remove_custom_domain(target)
            )
            del_btn.pack(side="right", padx=4, pady=2)

    # -----------------------------------------------------------------------
    # System Options, Healing & Tray
    # -----------------------------------------------------------------------
    def on_autoconnect_toggled(self):
        val = self.autoconnect_var.get()
        self.engine.settings["autoconnect"] = val
        save_settings(self.engine.settings)

    def on_adblock_toggled(self):
        enabled = self.adblock_var.get()
        self.engine.settings["adblock_enabled"] = enabled
        save_settings(self.engine.settings)
        from vpn_core import toggle_server_adblock
        threading.Thread(target=toggle_server_adblock, args=(enabled,), daemon=True).start()
        if self.engine.is_connected:
            self.engine.connect(self.engine.settings.get("selected_node"))

    def run_webrtc_protection(self):
        from vpn_core import apply_webrtc_protection
        res = apply_webrtc_protection()
        protected = [k for k, v in res.items() if v is True]
        if protected:
            self.webrtc_btn.configure(
                text=f"✔ WebRTC & IPv6 защищены ({', '.join(protected)})!",
                fg_color="#183628",
                border_color=COLOR_CONNECTED
            )
        else:
            self.webrtc_btn.configure(
                text="✔ Защита активна (браузеры настроены)",
                fg_color="#183628",
                border_color=COLOR_CONNECTED
            )

    def run_self_heal(self):
        self.heal_btn.configure(text="⏳ Очистка портов и сброс DNS-кэша...", state="disabled")
        def _worker():
            import vpn_core
            vpn_core.self_heal_network()
            if self.engine.is_connected:
                try:
                    self.engine.connect()
                except Exception:
                    pass
            self.after(0, self._on_heal_finished)
        threading.Thread(target=_worker, daemon=True).start()

    def _on_heal_finished(self):
        self.heal_btn.configure(
            text="✔ Сеть и кэш очищены, порты свободны!",
            state="normal",
            fg_color="#183628",
            border_color=COLOR_CONNECTED
        )
        self.after(3500, lambda: self.heal_btn.configure(
            text="🧹 Очистить кэш, освободить порты и починить сеть",
            fg_color="#183628",
            border_color=COLOR_CONNECTED
        ))

    def open_share_dialog(self):
        ShareQrDialog(self, self.engine)

    def _startup_autoconnect(self):
        if not self.engine.is_connected:
            self.toggle_connection()

    def _start_tray(self):
        menu = (
            item('Показать окно', self.on_restore_from_tray, default=True),
            item('Подключить / Отключить', self._tray_toggle),
            pystray.Menu.SEPARATOR,
            item('Выход', self.on_exit_app)
        )
        self.tray_icon = pystray.Icon("Unblocknet", create_tray_icon(False), "Unblocknet", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _update_tray_state(self):
        if self.tray_icon:
            self.tray_icon.icon = create_tray_icon(self.engine.is_connected)
            status_text = "Unblocknet: Активно" if self.engine.is_connected else "Unblocknet: Отключено"
            self.tray_icon.title = status_text

    def _tray_toggle(self, icon=None, item=None):
        self.after(0, self.toggle_connection)

    def on_minimize_to_tray(self):
        self.withdraw()

    def on_restore_from_tray(self, icon=None, item=None):
        self.after(0, self.deiconify)

    def on_exit_app(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        self.engine.disconnect()
        self.after(0, self.destroy)
        sys.exit(0)


if __name__ == '__main__':
    app = TeletokApp()
    app.mainloop()
