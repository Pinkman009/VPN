"""
vpn_app.py - Redesigned GUI Desktop Client for Teletok Connect.
Modern, functional, spacious UX/UI with chip/card lists, quick-add presets,
thread-safe state handling, and built-in QR generator.
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
    fetch_subscription_status, create_payment_order, activate_trial_period
)
import vpn_speedtest

# Modern theme settings
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
AUTOSTART_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "TeletokConnect"

def clean_domain_input(raw):
    """Sanitizes user domain input (strips http://, www., paths, etc.)."""
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
    """Creates an icon for the Windows notification tray."""
    img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    color = (46, 204, 113, 255) if connected else (127, 140, 141, 255)
    d.ellipse((8, 8, 56, 56), fill=color)
    d.ellipse((20, 20, 44, 44), fill=(22, 22, 26, 255))
    d.ellipse((26, 26, 38, 38), fill=color)
    return img


# ---------------------------------------------------------------------------
# Share QR Modal Dialog
# ---------------------------------------------------------------------------
class ShareQrDialog(ctk.CTkToplevel):
    def __init__(self, parent, engine):
        super().__init__(parent)
        self.title("Подключение смартфона — QR код")
        self.geometry("480x620")
        self.resizable(False, False)
        self.engine = engine
        self.transient(parent)
        self.grab_set()

        self.platform_var = ctk.StringVar(value="Android")

        # Header
        title = ctk.CTkLabel(
            self,
            text="📱 Подключение смартфона",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#00a8ff"
        )
        title.pack(pady=(20, 2))

        sub = ctk.CTkLabel(
            self,
            text="Отсканируйте QR в приложении Happ или Hiddify",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#8c8c9e"
        )
        sub.pack(pady=(0, 12))

        # Platform selector
        self.seg_btn = ctk.CTkSegmentedButton(
            self,
            values=["Android (Happ / Hiddify)", "Apple iOS (Happ / Streisand)"],
            variable=self.platform_var,
            command=self.update_qr,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            height=36
        )
        self.seg_btn.pack(padx=30, pady=(0, 14), fill="x")

        # QR Card with white background
        self.qr_card = ctk.CTkFrame(self, fg_color="white", corner_radius=12, width=240, height=240)
        self.qr_card.pack(pady=4)
        self.qr_card.pack_propagate(False)

        self.qr_label = ctk.CTkLabel(self.qr_card, text="")
        self.qr_label.pack(expand=True)

        # Instructions
        self.info_label = ctk.CTkLabel(
            self,
            text="1. Откройте Happ или Hiddify на смартфоне\n2. Нажмите «+» ➔ «Сканировать QR-код»\n3. Все настройки и раздельные правила применятся сами!",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#a0a0b0",
            justify="center"
        )
        self.info_label.pack(pady=(14, 10))

        # Copy link button
        self.copy_btn = ctk.CTkButton(
            self,
            text="📋 Скопировать ключ VLESS",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            height=36,
            fg_color="#272730",
            hover_color="#363642",
            command=self.copy_link
        )
        self.copy_btn.pack(padx=40, fill="x", pady=(0, 8))

        close_btn = ctk.CTkButton(
            self,
            text="Закрыть",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=36,
            fg_color="#00a8ff",
            hover_color="#008ecc",
            command=self.destroy
        )
        close_btn.pack(padx=40, fill="x", pady=(0, 16))

        self.current_link = ""
        self.update_qr()

    def get_link(self):
        platform = self.platform_var.get()
        fp = "randomized" if "Android" in platform else "chrome"
        alias = "Teletok-Android" if "Android" in platform else "Teletok-iOS"
        return f"vless://04756662-2f98-44ad-a53a-369d29118670@node.teletok.space:443?security=reality&encryption=none&pbk=t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE&headerType=none&fp={fp}&spx=%2F&type=tcp&flow=xtls-rprx-vision&sni=speed.cloudflare.com&sid=dae45f#{alias}"

    def update_qr(self, val=None):
        self.current_link = self.get_link()
        qr = qrcode.QRCode(box_size=5, border=1)
        qr.add_data(self.current_link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").get_image()
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(216, 216))
        self.qr_label.configure(image=ctk_img)
        self.qr_label.image = ctk_img
        self.copy_btn.configure(text="📋 Скопировать ключ VLESS")

    def copy_link(self):
        self.clipboard_clear()
        self.clipboard_append(self.current_link)
        self.copy_btn.configure(text="✔ Ключ скопирован в буфер!")


# ---------------------------------------------------------------------------
# Subscription & Pricing Modal Dialog
# ---------------------------------------------------------------------------
class SubscriptionDialog(ctk.CTkToplevel):
    def __init__(self, parent, engine):
        super().__init__(parent)
        self.title("Тарифы и подписка — Teletok VPN")
        self.geometry("540x740")
        self.resizable(False, False)
        self.parent = parent
        self.engine = engine
        self.transient(parent)
        self.grab_set()

        self.client_id = self.engine.settings.get("client_uuid", "79500490409")
        self.selected_plan_id = ctk.StringVar(value="1_year")
        self.current_sub = None
        self.current_plans = None
        self.polling_active = False

        self._build_dialog_ui()
        self._load_status_async()

    def _build_dialog_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 8))

        title = ctk.CTkLabel(
            header,
            text="⭐ Тарифы и подписка Teletok VPN",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#00a8ff"
        )
        title.pack(anchor="w")

        sub = ctk.CTkLabel(
            header,
            text="Высокая скорость • До 3 устройств на 1 ключ • Защита от спама и блокировок",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#8c8c9e"
        )
        sub.pack(anchor="w", pady=(2, 0))

        # Status Card
        self.status_card = ctk.CTkFrame(self, fg_color="#1a1e2b", corner_radius=12, border_width=1, border_color="#2b3b55")
        self.status_card.pack(fill="x", padx=24, pady=(0, 14), ipady=6)

        self.status_header = ctk.CTkLabel(
            self.status_card,
            text="Загрузка информации о подписке...",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#f0f0f5"
        )
        self.status_header.pack(anchor="w", padx=16, pady=(8, 2))

        self.status_details = ctk.CTkLabel(
            self.status_card,
            text="Связь с сервером 193.233.138.42...",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#a0a0b2"
        )
        self.status_details.pack(anchor="w", padx=16, pady=(0, 2))

        self.security_notice = ctk.CTkLabel(
            self.status_card,
            text="🛡️ Лимит: до 3 устройств • Заблокированы торренты, майнинг и почтовый спам",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#2ecc71"
        )
        self.security_notice.pack(anchor="w", padx=16, pady=(0, 8))

        # Plan selection header
        plans_lbl = ctk.CTkLabel(
            self,
            text="Выберите период подписки:",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#f0f0f5"
        )
        plans_lbl.pack(anchor="w", padx=26, pady=(0, 8))

        # Plans container
        self.plans_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.plans_frame.pack(fill="x", padx=24, pady=0)

        self.plan_radios = {}
        plan_definitions = [
            ("1_month", "1 месяц", "149 ₽", "149 ₽/мес • Базовый доступ на 30 дней", None),
            ("3_months", "3 месяца", "390 ₽", "130 ₽/мес • Экономия 13%", "-13%"),
            ("6_months", "6 месяцев", "690 ₽", "115 ₽/мес • Экономия 23%", "-23%"),
            ("1_year", "1 год", "1 190 ₽", "99 ₽/мес • Экономия 33% • Хит 🔥", "ХИТ! -33%"),
        ]

        for pid, name, price, desc, badge in plan_definitions:
            card = ctk.CTkFrame(self.plans_frame, fg_color="#21212a", corner_radius=10, border_width=1, border_color="#2f2f3d")
            card.pack(fill="x", pady=4, ipady=4)

            def _make_selector(plan_id_val):
                return lambda e: self.on_plan_selected(plan_id_val)

            top_line = ctk.CTkFrame(card, fg_color="transparent")
            top_line.pack(fill="x", padx=12, pady=(4, 2))

            rb = ctk.CTkRadioButton(
                top_line,
                text=f"{name} — {price}",
                value=pid,
                variable=self.selected_plan_id,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                command=self.update_pay_button,
                fg_color="#00a8ff"
            )
            rb.pack(side="left")
            self.plan_radios[pid] = rb

            if badge:
                badge_lbl = ctk.CTkLabel(
                    top_line,
                    text=badge,
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                    fg_color="#e67e22" if "ХИТ" in badge else "#27ae60",
                    text_color="white",
                    corner_radius=6,
                    padx=6,
                    pady=1
                )
                badge_lbl.pack(side="right")

            sub_desc = ctk.CTkLabel(
                card,
                text=f"    {desc}",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#8c8c9e"
            )
            sub_desc.pack(anchor="w", padx=14, pady=(0, 4))

            card.bind("<Button-1>", _make_selector(pid))
            top_line.bind("<Button-1>", _make_selector(pid))
            sub_desc.bind("<Button-1>", _make_selector(pid))

        # Trial Button Frame (shown if eligible / expired)
        self.trial_btn = ctk.CTkButton(
            self,
            text="🎁 Активировать 3 дня бесплатно (Тестовый период)",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=38,
            fg_color="#27ae60",
            hover_color="#219955",
            corner_radius=8,
            command=self.activate_trial
        )
        self.trial_btn.pack(fill="x", padx=24, pady=(10, 6))

        # Pay button
        self.pay_btn = ctk.CTkButton(
            self,
            text="💳 Оплатить 1 190 ₽ через ЮMoney (Банковская карта)",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=44,
            fg_color="#00a8ff",
            hover_color="#008ecc",
            corner_radius=10,
            command=self.start_payment
        )
        self.pay_btn.pack(fill="x", padx=24, pady=(6, 6))

        # Status and polling info
        self.poll_label = ctk.CTkLabel(
            self,
            text="Оплата проходит мгновенно через официальную форму ЮMoney (P2P без комиссий)",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#8c8c9e",
            wraplength=480
        )
        self.poll_label.pack(padx=24, pady=(2, 6))

        close_btn = ctk.CTkButton(
            self,
            text="Закрыть",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=32,
            fg_color="#282832",
            hover_color="#363644",
            command=self.on_close
        )
        close_btn.pack(padx=24, fill="x", pady=(4, 16))

        self.update_pay_button()

    def on_plan_selected(self, plan_id):
        self.selected_plan_id.set(plan_id)
        self.update_pay_button()

    def update_pay_button(self):
        prices = {"1_month": "149 ₽", "3_months": "390 ₽", "6_months": "690 ₽", "1_year": "1 190 ₽"}
        pid = self.selected_plan_id.get()
        p = prices.get(pid, "149 ₽")
        self.pay_btn.configure(text=f"💳 Оплатить {p} через ЮMoney (Банковская карта)")

    def _load_status_async(self):
        def _worker():
            sub, plans = fetch_subscription_status(self.client_id)
            self.after(0, self._render_status, sub, plans)
        threading.Thread(target=_worker, daemon=True).start()

    def _render_status(self, sub, plans):
        self.current_sub = sub
        self.current_plans = plans
        if not sub:
            self.status_header.configure(text="● Ошибка соединения с сервером биллинга", text_color="#e74c3c")
            self.status_details.configure(text="Проверьте подключение к Интернету.")
            return

        is_active = sub.get("is_active", False)
        days_left = sub.get("days_left", 0)
        exp_date = sub.get("expiry_date", "--")
        limit_ip = sub.get("limit_ip", 3)

        if is_active:
            self.status_header.configure(
                text=f"● Подписка активна (осталось: {days_left} дн.)",
                text_color="#2ecc71"
            )
            self.status_details.configure(
                text=f"Действует до: {exp_date} • Устройств: до {limit_ip} на ключ"
            )
            if days_left > 3:
                self.trial_btn.configure(state="disabled", text="✔ Тестовый период уже использован / Подписка активна")
        else:
            self.status_header.configure(
                text="● Подписка истекла или не активна",
                text_color="#e74c3c"
            )
            self.status_details.configure(
                text="Выберите тариф для продления или активируйте бесплатный тест."
            )
            self.trial_btn.configure(state="normal", text="🎁 Активировать 3 дня бесплатно (Тестовый период)")

    def activate_trial(self):
        self.trial_btn.configure(text="⏳ Активация 3 дней...", state="disabled")
        def _worker():
            ok, msg = activate_trial_period(self.client_id)
            def _cb():
                if ok:
                    self.poll_label.configure(text="🎉 Тестовый период на 3 дня успешно активирован!", text_color="#2ecc71")
                    self._load_status_async()
                    if hasattr(self.parent, "update_subscription_display"):
                        self.parent.update_subscription_display()
                else:
                    self.poll_label.configure(text=f"Внимание: {msg}", text_color="#e74c3c")
                    self.trial_btn.configure(state="normal", text="🎁 Попробовать снова")
            self.after(0, _cb)
        threading.Thread(target=_worker, daemon=True).start()

    def start_payment(self):
        plan_id = self.selected_plan_id.get()
        self.pay_btn.configure(state="disabled", text="⏳ Создание платежной формы...")
        self.poll_label.configure(text="Связываемся с ЮMoney API...", text_color="#00a8ff")

        def _worker():
            ok, pay_url, order_id, plan_info = create_payment_order(plan_id, self.client_id)
            self.after(0, self._on_payment_created, ok, pay_url, order_id, plan_info)
        threading.Thread(target=_worker, daemon=True).start()

    def _on_payment_created(self, ok, pay_url, order_id, plan_info):
        if not ok or not pay_url:
            self.pay_btn.configure(state="normal")
            self.update_pay_button()
            self.poll_label.configure(text=f"Ошибка создания счета: {pay_url}", text_color="#e74c3c")
            return

        webbrowser.open(pay_url)

        self.polling_active = True
        self.pay_btn.configure(state="disabled", text="Ожидание оплаты в браузере...")
        self.poll_label.configure(
            text="🌐 Форма оплаты открыта в браузере. После оплаты статус обновится автоматически в течение нескольких секунд...",
            text_color="#f39c12"
        )

        initial_expiry = self.current_sub.get("expiry_time", 0) if self.current_sub else 0
        self._poll_status_loop(initial_expiry, attempts=60)

    def _poll_status_loop(self, initial_expiry, attempts):
        if not self.polling_active or attempts <= 0:
            if attempts <= 0 and self.polling_active:
                self.pay_btn.configure(state="normal")
                self.update_pay_button()
                self.poll_label.configure(text="Время ожидания истекло. Если вы оплатили, нажмите 'Проверить статус'.", text_color="#a0a0b2")
            return

        def _check():
            sub, _ = fetch_subscription_status(self.client_id)
            def _cb():
                if not self.polling_active:
                    return
                if sub:
                    curr_exp = sub.get("expiry_time", 0)
                    if curr_exp > initial_expiry:
                        self.polling_active = False
                        self.pay_btn.configure(state="normal")
                        self.update_pay_button()
                        exp_date = sub.get("expiry_date", "--")
                        self.poll_label.configure(
                            text=f"🎉 Оплата успешно получена! Подписка продлена до {exp_date}!",
                            text_color="#2ecc71"
                        )
                        self._render_status(sub, self.current_plans)
                        if hasattr(self.parent, "update_subscription_display"):
                            self.parent.update_subscription_display()
                        return

                self.after(3000, lambda: self._poll_status_loop(initial_expiry, attempts - 1))
            self.after(0, _cb)

        threading.Thread(target=_check, daemon=True).start()

    def on_close(self):
        self.polling_active = False
        self.destroy()


# ---------------------------------------------------------------------------
# Main Application Window
# ---------------------------------------------------------------------------
class TeletokApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Teletok Connect")
        self.geometry("600x840")
        self.minsize(560, 780)

        # Engine instance
        self.engine = VpnEngine()
        self.tray_icon = None
        self.is_checking_speed = False
        self.is_updating_geo = False
        self.is_busy = False

        self.protocol("WM_DELETE_WINDOW", self.on_minimize_to_tray)

        self._build_ui()
        self._update_status_ui()
        self._start_tray()

    def _build_ui(self):
        # 1. Header Banner
        self.header_frame = ctk.CTkFrame(self, fg_color="#18181f", corner_radius=0)
        self.header_frame.pack(fill="x", padx=0, pady=0)

        top_row = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        top_row.pack(fill="x", padx=25, pady=(16, 4))

        self.title_label = ctk.CTkLabel(
            top_row,
            text="TELETOK CONNECT",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#00a8ff"
        )
        self.title_label.pack(side="left")

        self.version_badge = ctk.CTkLabel(
            top_row,
            text="v2.0 • Ultra",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#6e6e82",
            fg_color="#23232c",
            corner_radius=6,
            padx=8,
            pady=2
        )
        self.version_badge.pack(side="right")

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Сетевой акселератор • Прямой доступ к сервисам без ограничений",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#8c8c9e"
        )
        self.subtitle_label.pack(anchor="w", padx=25, pady=(0, 14))

        # Main Scrollable Content Body
        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=22, pady=12)

        # 1.5 Subscription & Billing Status Card
        self.sub_card = ctk.CTkFrame(self.body, fg_color="#181e2b", corner_radius=14, border_width=1, border_color="#2b3b55")
        self.sub_card.pack(fill="x", pady=(0, 14), ipady=4)

        sub_inner = ctk.CTkFrame(self.sub_card, fg_color="transparent")
        sub_inner.pack(fill="x", padx=16, pady=8)

        sub_info_col = ctk.CTkFrame(sub_inner, fg_color="transparent")
        sub_info_col.pack(side="left", fill="both", expand=True)

        self.sub_status_label = ctk.CTkLabel(
            sub_info_col,
            text="⭐ Подписка: проверка статуса...",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#00a8ff"
        )
        self.sub_status_label.pack(anchor="w")

        self.sub_desc_label = ctk.CTkLabel(
            sub_info_col,
            text="До 3 устройств на ключ • Без торрентов и спама",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#8c8c9e"
        )
        self.sub_desc_label.pack(anchor="w")

        self.sub_action_btn = ctk.CTkButton(
            sub_inner,
            text="💎 Тарифы",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            width=110,
            height=34,
            fg_color="#00a8ff",
            hover_color="#008ecc",
            corner_radius=8,
            command=self.open_subscription_dialog
        )
        self.sub_action_btn.pack(side="right", padx=(8, 0))

        # 2. Main Connection Card
        self.conn_card = ctk.CTkFrame(self.body, fg_color="#212129", corner_radius=14)
        self.conn_card.pack(fill="x", pady=(0, 14), ipady=8)

        self.status_badge = ctk.CTkLabel(
            self.conn_card,
            text="● ОТКЛЮЧЕНО",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#95a5a6"
        )
        self.status_badge.pack(pady=(12, 10))

        self.connect_btn = ctk.CTkButton(
            self.conn_card,
            text="ПОДКЛЮЧИТЬ",
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            height=52,
            fg_color="#00a8ff",
            hover_color="#008ecc",
            corner_radius=26,
            command=self.toggle_connection
        )
        self.connect_btn.pack(padx=30, fill="x", pady=(0, 10))

        self.share_btn = ctk.CTkButton(
            self.conn_card,
            text="📱 Подключить смартфон через QR-код",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            height=38,
            fg_color="#2b2b36",
            hover_color="#383846",
            corner_radius=19,
            command=self.open_share_dialog
        )
        self.share_btn.pack(padx=30, fill="x", pady=(0, 14))

        # Node selector
        self.node_frame = ctk.CTkFrame(self.conn_card, fg_color="#1a1a20", corner_radius=10)
        self.node_frame.pack(fill="x", padx=20, pady=(0, 8), ipady=6)

        node_head = ctk.CTkLabel(
            self.node_frame,
            text="Сервер подключения:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#8c8c9e"
        )
        node_head.pack(anchor="w", padx=14, pady=(4, 2))

        node_options = [f"{k}: {v['name']}" for k, v in NODES.items()]
        current_node_key = self.engine.settings.get("selected_node", "443-frag")
        current_node_val = f"{current_node_key}: {NODES.get(current_node_key, {}).get('name', '')}"

        self.node_menu = ctk.CTkOptionMenu(
            self.node_frame,
            values=node_options,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=34,
            fg_color="#282834",
            button_color="#363646",
            command=self.on_node_changed
        )
        self.node_menu.set(current_node_val)
        self.node_menu.pack(fill="x", padx=14, pady=(0, 6))

        # 3. Diagnostics & Speed Card
        self.diag_card = ctk.CTkFrame(self.body, fg_color="#212129", corner_radius=14)
        self.diag_card.pack(fill="x", pady=(0, 14), ipady=6)

        diag_top = ctk.CTkFrame(self.diag_card, fg_color="transparent")
        diag_top.pack(fill="x", padx=20, pady=(10, 4))

        self.diag_title = ctk.CTkLabel(
            diag_top,
            text="Диагностика и проверка сети",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#f0f0f5"
        )
        self.diag_title.pack(side="left")

        self.diag_info_frame = ctk.CTkFrame(self.diag_card, fg_color="#1a1a20", corner_radius=10)
        self.diag_info_frame.pack(fill="x", padx=20, pady=(4, 10), ipady=8)

        self.ip_label = ctk.CTkLabel(
            self.diag_info_frame,
            text="Исходящий IP:  Определение...",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#a0a0b2"
        )
        self.ip_label.pack(anchor="w", padx=14, pady=2)

        self.ping_label = ctk.CTkLabel(
            self.diag_info_frame,
            text="Задержка (Пинг):  -- мс",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#a0a0b2"
        )
        self.ping_label.pack(anchor="w", padx=14, pady=2)

        self.speed_label = ctk.CTkLabel(
            self.diag_info_frame,
            text="Скорость и доступ:  Нажмите кнопку для проверки",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#a0a0b2"
        )
        self.speed_label.pack(anchor="w", padx=14, pady=2)

        # Buttons row
        diag_btns = ctk.CTkFrame(self.diag_card, fg_color="transparent")
        diag_btns.pack(fill="x", padx=20, pady=(0, 10))

        self.check_speed_btn = ctk.CTkButton(
            diag_btns,
            text="⚡ Проверить скорость и сервисы",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            height=36,
            fg_color="#2b2b36",
            hover_color="#383846",
            corner_radius=18,
            command=self.run_speed_check
        )
        self.check_speed_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.update_geo_btn = ctk.CTkButton(
            diag_btns,
            text="🔄 Обновить базы (GitHub)",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            height=36,
            fg_color="#2b2b36",
            hover_color="#383846",
            corner_radius=18,
            command=self.run_geodata_update
        )
        self.update_geo_btn.pack(side="right", fill="x", expand=True, padx=(6, 0))

        privacy_row = ctk.CTkFrame(self.diag_card, fg_color="transparent")
        privacy_row.pack(fill="x", padx=20, pady=(0, 6))

        self.webrtc_btn = ctk.CTkButton(
            privacy_row,
            text="🛡️ Защитить от утечек WebRTC и IPv6 (Chrome / Edge)",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=32,
            fg_color="#1a2736",
            hover_color="#24384d",
            border_width=1,
            border_color="#00a8ff",
            corner_radius=16,
            command=self.run_webrtc_protection
        )
        self.webrtc_btn.pack(fill="x")

        heal_row = ctk.CTkFrame(self.diag_card, fg_color="transparent")
        heal_row.pack(fill="x", padx=20, pady=(0, 6))

        self.heal_btn = ctk.CTkButton(
            heal_row,
            text="🧹 Очистить кэш, освободить порты и починить сеть",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=32,
            fg_color="#1e3d2f",
            hover_color="#275641",
            border_width=1,
            border_color="#2ecc71",
            text_color="#2ecc71",
            corner_radius=16,
            command=self.run_self_heal
        )
        self.heal_btn.pack(fill="x")

        # 4. Spacious Split-Tunneling Section
        self.rules_card = ctk.CTkFrame(self.body, fg_color="#212129", corner_radius=14)
        self.rules_card.pack(fill="x", pady=(0, 10), ipady=8)

        rules_header = ctk.CTkLabel(
            self.rules_card,
            text="Исключения и маршрутизация (Split-Tunneling)",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#f0f0f5"
        )
        rules_header.pack(anchor="w", padx=20, pady=(12, 2))

        rules_desc = ctk.CTkLabel(
            self.rules_card,
            text="Выберите режим и управляйте сайтами в 1 клик:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#8c8c9e"
        )
        rules_desc.pack(anchor="w", padx=20, pady=(0, 8))

        # Mode Segmented Switch
        self.rule_mode_var = ctk.StringVar(value="direct")
        self.mode_selector = ctk.CTkSegmentedButton(
            self.rules_card,
            values=["Напрямую (мимо туннеля)", "Через туннель"],
            variable=self.rule_mode_var,
            command=self.on_rule_mode_changed,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            height=36
        )
        self.mode_selector.pack(fill="x", padx=20, pady=(0, 10))

        # Quick Add Presets Row
        self.preset_frame = ctk.CTkFrame(self.rules_card, fg_color="transparent")
        self.preset_frame.pack(fill="x", padx=20, pady=(0, 8))

        self.preset_label = ctk.CTkLabel(
            self.preset_frame,
            text="Быстрое добавление:",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#8c8c9e"
        )
        self.preset_label.pack(anchor="w", pady=(0, 4))

        self.preset_buttons_frame = ctk.CTkFrame(self.preset_frame, fg_color="transparent")
        self.preset_buttons_frame.pack(fill="x")

        # Custom Domain Input Row
        self.input_frame = ctk.CTkFrame(self.rules_card, fg_color="transparent")
        self.input_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.domain_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Введите домен (например, lenta.ru или chatgpt.com)",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            height=38
        )
        self.domain_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.domain_entry.bind("<Return>", lambda e: self.add_custom_domain())

        self.add_btn = ctk.CTkButton(
            self.input_frame,
            text="+ Добавить",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            width=105,
            height=38,
            fg_color="#00a8ff",
            hover_color="#008ecc",
            command=self.add_custom_domain
        )
        self.add_btn.pack(side="right")

        # Spacious Scrollable Domain List (Height 230px!)
        self.domain_list_frame = ctk.CTkScrollableFrame(
            self.rules_card,
            fg_color="#18181f",
            corner_radius=10,
            height=230
        )
        self.domain_list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # 5. Footer Frame (Autostart & Tray)
        self.footer = ctk.CTkFrame(self, fg_color="#18181f", height=48, corner_radius=0)
        self.footer.pack(fill="x", side="bottom")

        self.autostart_var = ctk.BooleanVar(value=self.engine.settings.get("autostart", False))
        self.autostart_cb = ctk.CTkCheckBox(
            self.footer,
            text="Автозапуск",
            variable=self.autostart_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.on_autostart_toggled
        )
        self.autostart_cb.pack(side="left", padx=(16, 6), pady=12)

        self.autoconnect_var = ctk.BooleanVar(value=self.engine.settings.get("autoconnect", True))
        self.autoconnect_cb = ctk.CTkCheckBox(
            self.footer,
            text="⚡ Автоподключение",
            variable=self.autoconnect_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.on_autoconnect_toggled
        )
        self.autoconnect_cb.pack(side="left", padx=6, pady=12)

        self.adblock_var = ctk.BooleanVar(value=self.engine.settings.get("adblock_enabled", True))
        self.adblock_cb = ctk.CTkCheckBox(
            self.footer,
            text="🛡️ AdBlock",
            variable=self.adblock_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#00a8ff",
            command=self.on_adblock_toggled
        )
        self.adblock_cb.pack(side="left", padx=6, pady=12)

        self.tray_btn = ctk.CTkButton(
            self.footer,
            text="В трей ▾",
            width=90,
            height=28,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#2b2b36",
            hover_color="#383846",
            command=self.on_minimize_to_tray
        )
        self.tray_btn.pack(side="right", padx=(6, 16), pady=12)

        # Initial render of presets & domains
        self._refresh_presets()
        self._refresh_domain_list()

        # Check for autostart / minimized flag
        is_startup = "--autostart" in sys.argv or "--minimized" in sys.argv
        if is_startup:
            self.after(50, self.withdraw)

        # Initial background ping scheduled safely after mainloop starts
        self.after(300, lambda: threading.Thread(target=self._initial_ping, daemon=True).start())

        # Check subscription status from server
        self.after(500, self.update_subscription_display)

        # Auto-connect if enabled
        if self.engine.settings.get("autoconnect", True):
            self.after(800, self._startup_autoconnect)

    def open_subscription_dialog(self):
        SubscriptionDialog(self, self.engine)

    def update_subscription_display(self):
        threading.Thread(target=self._check_subscription_bg, daemon=True).start()

    def _check_subscription_bg(self):
        client_id = self.engine.settings.get("client_uuid", "79500490409")
        sub, _ = fetch_subscription_status(client_id)
        self.after(0, self._render_subscription, sub)

    def _render_subscription(self, sub):
        if not sub:
            self.sub_status_label.configure(
                text="⚠️ Статус подписки: Не удалось получить",
                text_color="#e74c3c"
            )
            self.sub_desc_label.configure(
                text="Проверьте соединение или обновите статус",
                text_color="#8c8c9e"
            )
            return

        is_active = sub.get("is_active", False)
        days_left = sub.get("days_left", 0)
        exp_date = sub.get("expiry_date", "--")
        limit_ip = sub.get("limit_ip", 3)

        if is_active:
            self.sub_status_label.configure(
                text=f"⭐ Подписка активна (осталось {days_left} дн., до {exp_date})",
                text_color="#2ecc71"
            )
            self.sub_desc_label.configure(
                text=f"До {limit_ip} устройств • Защита от торрентов и спама активна",
                text_color="#a0a0b2"
            )
            self.sub_action_btn.configure(
                text="💎 Продлить",
                fg_color="#282834",
                hover_color="#363646"
            )
        else:
            self.sub_status_label.configure(
                text="⚠️ Подписка истекла или не активна",
                text_color="#e74c3c"
            )
            self.sub_desc_label.configure(
                text="Доступен тест на 3 дня или тарифы от 99 ₽/мес",
                text_color="#e67e22"
            )
            self.sub_action_btn.configure(
                text="🎁 Выбрать тариф",
                fg_color="#e67e22",
                hover_color="#d35400"
            )

    def _startup_autoconnect(self):
        if not self.engine.is_connected:
            self.toggle_connection()

    # -----------------------------------------------------------------------
    # Rules & Preset Handlers
    # -----------------------------------------------------------------------
    def on_rule_mode_changed(self, choice):
        self._refresh_presets()
        self._refresh_domain_list()

    def _refresh_presets(self):
        # Clear old preset buttons
        for w in self.preset_buttons_frame.winfo_children():
            w.destroy()

        mode = "direct" if "Напрямую" in self.rule_mode_var.get() else "proxy"
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
                ("Canva", "canva.com"),
                ("Claude", "claude.ai")
            ]

        for title, domain in presets:
            btn = ctk.CTkButton(
                self.preset_buttons_frame,
                text=f"+ {title}",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                height=26,
                fg_color="#272732",
                hover_color="#353544",
                corner_radius=13,
                command=lambda d=domain: self._add_preset_domain(d)
            )
            btn.pack(side="left", padx=2, pady=2)

    def _add_preset_domain(self, domain):
        mode = "direct" if "Напрямую" in self.rule_mode_var.get() else "proxy"
        if mode == "direct":
            self.engine.add_direct_domain(domain)
        else:
            self.engine.add_proxy_domain(domain)
        self._refresh_domain_list()

    def add_custom_domain(self):
        val = clean_domain_input(self.domain_entry.get())
        if val:
            mode = "direct" if "Напрямую" in self.rule_mode_var.get() else "proxy"
            if mode == "direct":
                self.engine.add_direct_domain(val)
            else:
                self.engine.add_proxy_domain(val)
            self.domain_entry.delete(0, "end")
            self._refresh_domain_list()

    def remove_domain(self, domain, mode):
        if mode == "direct":
            self.engine.remove_direct_domain(domain)
        else:
            self.engine.remove_proxy_domain(domain)
        self._refresh_domain_list()

    def _refresh_domain_list(self):
        for w in self.domain_list_frame.winfo_children():
            w.destroy()

        mode = "direct" if "Напрямую" in self.rule_mode_var.get() else "proxy"
        domains = self.engine.settings.get("custom_direct_domains", []) if mode == "direct" else self.engine.settings.get("custom_proxy_domains", [])

        if not domains:
            empty_lbl = ctk.CTkLabel(
                self.domain_list_frame,
                text="Список пока пуст. Добавьте сайт выше или нажмите на готовый пресет.",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color="#6e6e80"
            )
            empty_lbl.pack(pady=20)
            return

        for domain in domains:
            row = ctk.CTkFrame(self.domain_list_frame, fg_color="#212129", corner_radius=8, height=36)
            row.pack(fill="x", pady=2, padx=4)
            row.pack_propagate(False)

            icon_lbl = ctk.CTkLabel(row, text="🌐", font=ctk.CTkFont(size=13))
            icon_lbl.pack(side="left", padx=(10, 6))

            name_lbl = ctk.CTkLabel(
                row,
                text=domain,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color="#e0e0ea"
            )
            name_lbl.pack(side="left", padx=4)

            tag_color = "#2ecc71" if mode == "direct" else "#00a8ff"
            tag_text = "НАПРЯМУЮ" if mode == "direct" else "ЧЕРЕЗ ТУННЕЛЬ"
            tag_lbl = ctk.CTkLabel(
                row,
                text=tag_text,
                font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                text_color=tag_color,
                fg_color="#18181f",
                corner_radius=4,
                padx=6,
                pady=1
            )
            tag_lbl.pack(side="left", padx=10)

            del_btn = ctk.CTkButton(
                row,
                text="✕",
                width=28,
                height=26,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                fg_color="#2b2b36",
                hover_color="#e74c3c",
                command=lambda d=domain, m=mode: self.remove_domain(d, m)
            )
            del_btn.pack(side="right", padx=6)

    # -----------------------------------------------------------------------
    # Connection Handlers (Thread-Safe with self.after)
    # -----------------------------------------------------------------------
    def on_node_changed(self, choice):
        node_key = choice.split(":")[0].strip()
        self.engine.settings["selected_node"] = node_key
        save_settings(self.engine.settings)
        if self.engine.is_connected:
            self.toggle_connection()
            time.sleep(0.3)
            self.toggle_connection()

    def toggle_connection(self):
        if self.is_busy:
            return
        self.is_busy = True

        if self.engine.is_connected:
            self.connect_btn.configure(text="Отключение...", state="disabled", fg_color="#7f8c8d")
            self.status_badge.configure(text="● ОТКЛЮЧЕНИЕ...", text_color="#f39c12")
            threading.Thread(target=self._worker_disconnect, daemon=True).start()
        else:
            self.connect_btn.configure(text="Подключение...", state="disabled", fg_color="#f39c12")
            self.status_badge.configure(text="● ПОДКЛЮЧЕНИЕ К СЕРВЕРУ...", text_color="#f39c12")
            threading.Thread(target=self._worker_connect, daemon=True).start()

    def _worker_connect(self):
        try:
            self.engine.connect()
            self.after(0, self._on_connect_success)
        except Exception as e:
            self.after(0, lambda err=str(e): self._on_connect_error(err))

    def _on_connect_success(self):
        self.is_busy = False
        self._update_status_ui()
        self._update_tray_state()
        self.run_speed_check()

    def _on_connect_error(self, err_msg):
        self.is_busy = False
        self.status_badge.configure(
            text=f"Ошибка подключения: {err_msg[:40]}",
            text_color="#e74c3c"
        )
        self.connect_btn.configure(
            text="ПОДКЛЮЧИТЬ",
            fg_color="#00a8ff",
            hover_color="#008ecc",
            state="normal"
        )

    def _worker_disconnect(self):
        try:
            self.engine.disconnect()
            self.after(0, self._on_disconnect_success)
        except Exception as e:
            self.after(0, lambda: self._on_disconnect_success())

    def _on_disconnect_success(self):
        self.is_busy = False
        self._update_status_ui()
        self._update_tray_state()
        self._initial_ping()

    def _update_status_ui(self):
        if self.engine.is_connected:
            self.status_badge.configure(text="● ПОДКЛЮЧЕНО (Хельсинки • Защищено)", text_color="#2ecc71")
            self.connect_btn.configure(
                text="ОТКЛЮЧИТЬ",
                fg_color="#e74c3c",
                hover_color="#c0392b",
                state="normal"
            )
        else:
            self.status_badge.configure(text="● ОТКЛЮЧЕНО", text_color="#95a5a6")
            self.connect_btn.configure(
                text="ПОДКЛЮЧИТЬ",
                fg_color="#00a8ff",
                hover_color="#008ecc",
                state="normal"
            )

    # -----------------------------------------------------------------------
    # Diagnostics & Speed Checks
    # -----------------------------------------------------------------------
    def _initial_ping(self):
        p = vpn_speedtest.measure_ping()
        info = vpn_speedtest.get_ip_info(proxy=None)
        self.after(0, lambda: self._apply_initial_diagnostics(p, info))

    def _apply_initial_diagnostics(self, p, info):
        self.ping_label.configure(text=f"Задержка (Пинг):  {p} мс" if p > 0 else "Задержка (Пинг):  Недоступен")
        self.ip_label.configure(text=f"Текущий IP:  {info['ip']} ({info['country']})")

    def run_speed_check(self):
        if self.is_checking_speed:
            return
        self.is_checking_speed = True
        self.check_speed_btn.configure(text="⏳ Измерение скорости и доступности...", state="disabled")
        threading.Thread(target=self._worker_speed_check, daemon=True).start()

    def _worker_speed_check(self):
        proxy = "http://127.0.0.1:10897" if self.engine.is_connected else None
        p = vpn_speedtest.measure_ping()
        info = vpn_speedtest.get_ip_info(proxy=proxy)
        services = vpn_speedtest.check_service_status(proxy=proxy)
        speed = vpn_speedtest.measure_download_speed(proxy=proxy, max_seconds=4.0)

        self.after(0, lambda: self._apply_speed_results(p, info, services, speed))

    def _apply_speed_results(self, p, info, services, speed):
        yt = "✔" if services.get('YouTube') else "✖"
        gpt = "✔" if services.get('ChatGPT') else "✖"
        cld = "✔" if services.get('Claude') else "✖"

        self.ping_label.configure(text=f"Задержка (Пинг):  {p} мс")
        self.ip_label.configure(text=f"Исходящий IP:  {info['ip']} ({info['country']} {info['city']})")
        self.speed_label.configure(text=f"Скорость: {speed} Мбит/с | YouTube: {yt} | ChatGPT: {gpt} | Claude: {cld}")

        self.check_speed_btn.configure(text="⚡ Проверить скорость и сервисы", state="normal")
        self.is_checking_speed = False

    def run_geodata_update(self):
        if self.is_updating_geo:
            return
        self.is_updating_geo = True
        self.update_geo_btn.configure(text="⏳ Загрузка Geo-баз...", state="disabled")
        threading.Thread(target=self._worker_update_geodata, daemon=True).start()

    def _worker_update_geodata(self):
        # Update both local app directory and _internal if running frozen
        dirs = [APP_DIR]
        internal_dir = os.path.join(APP_DIR, "_internal")
        if os.path.isdir(internal_dir):
            dirs.append(internal_dir)
        ok, msg = vpn_speedtest.update_geodata_files(dirs)
        self.after(0, lambda: self._apply_geodata_update_result(ok, msg))

    def _apply_geodata_update_result(self, ok, msg):
        self.update_geo_btn.configure(text="🔄 Обновить базы (GitHub)", state="normal")
        self.is_updating_geo = False
        if ok:
            self.speed_label.configure(text=f"✔ {msg}")
        else:
            self.speed_label.configure(text=f"✖ {msg}")

    # -----------------------------------------------------------------------
    # System Integration
    # -----------------------------------------------------------------------
    def open_share_dialog(self):
        ShareQrDialog(self, self.engine)

    def on_autostart_toggled(self):
        enabled = self.autostart_var.get()
        self.engine.settings["autostart"] = enabled
        save_settings(self.engine.settings)
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_SET_VALUE)
            if enabled:
                launcher = os.path.join(APP_DIR, "Запустить_Teletok_VPN.bat")
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{launcher}" --autostart')
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print("Autostart error:", e)

    def on_autoconnect_toggled(self):
        val = self.autoconnect_var.get()
        self.engine.settings["autoconnect"] = val
        save_settings(self.engine.settings)

    def _startup_autoconnect(self):
        if not self.engine.is_connected:
            self.toggle_connection()

    def run_webrtc_protection(self):
        from vpn_core import apply_webrtc_protection
        res = apply_webrtc_protection()
        protected = [k for k, v in res.items() if v is True]
        if protected:
            self.webrtc_btn.configure(
                text=f"✔ WebRTC & IPv6 защищены ({', '.join(protected)})!",
                fg_color="#183628",
                border_color="#2ecc71"
            )
        else:
            self.webrtc_btn.configure(
                text="✔ Защита активна (браузеры настроены)",
                fg_color="#183628",
                border_color="#2ecc71"
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
            border_color="#2ecc71"
        )
        self.after(3500, lambda: self.heal_btn.configure(
            text="🧹 Очистить кэш, освободить порты и починить сеть",
            fg_color="#1e3d2f",
            border_color="#2ecc71"
        ))

    def on_adblock_toggled(self):
        enabled = self.adblock_var.get()
        self.engine.settings["adblock_enabled"] = enabled
        save_settings(self.engine.settings)
        from vpn_core import toggle_server_adblock
        threading.Thread(target=toggle_server_adblock, args=(enabled,), daemon=True).start()
        if self.engine.is_connected:
            self.engine.connect(self.engine.settings.get("selected_node"))

    def _start_tray(self):
        menu = (
            item('Показать окно', self.on_restore_from_tray, default=True),
            item('Подключить / Отключить', self._tray_toggle),
            pystray.Menu.SEPARATOR,
            item('Выход', self.on_exit_app)
        )
        self.tray_icon = pystray.Icon("TeletokConnect", create_tray_icon(False), "Teletok Connect", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _update_tray_state(self):
        if self.tray_icon:
            self.tray_icon.icon = create_tray_icon(self.engine.is_connected)
            status_text = "Teletok Connect: Активно" if self.engine.is_connected else "Teletok Connect: Отключено"
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
