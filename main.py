"""
NetScan Pro - Android Network Scanner App
Built with Kivy | Cybersecurity Tool
"""

import os
import threading
import socket
import subprocess
import platform
import json
from datetime import datetime

os.environ['KIVY_NO_ENV_CONFIG'] = '1'

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.animation import Animation
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, NumericProperty, BooleanProperty

# ─── THEME ─────────────────────────────────────────────────────────────────────
COLORS = {
    'bg_dark':    (0.04, 0.05, 0.08, 1),
    'bg_card':    (0.07, 0.09, 0.13, 1),
    'bg_input':   (0.05, 0.07, 0.11, 1),
    'accent':     (0.0,  0.85, 0.6,  1),    # #00D99A neon teal
    'accent2':    (0.0,  0.55, 1.0,  1),    # #008CFF electric blue
    'danger':     (1.0,  0.25, 0.35, 1),    # #FF3F59 red alert
    'warn':       (1.0,  0.65, 0.0,  1),    # #FFA500 orange
    'text_main':  (0.88, 0.92, 0.96, 1),
    'text_dim':   (0.42, 0.50, 0.60, 1),
    'border':     (0.12, 0.18, 0.26, 1),
}

def hex_color(r, g, b, a=1):
    return (r, g, b, a)

Window.clearcolor = COLORS['bg_dark']

# ─── UTILITIES ─────────────────────────────────────────────────────────────────

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "192.168.1.1"

def get_network_prefix(ip):
    parts = ip.split('.')
    return '.'.join(parts[:3])

def ping_host(ip, timeout=1):
    """Ping a host and return True if alive."""
    try:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        result = subprocess.run(
            ['ping', param, '1', '-W', str(timeout), ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout + 1
        )
        return result.returncode == 0
    except Exception:
        return False

def scan_ports(ip, ports, timeout=0.5):
    """Scan common ports on an IP."""
    open_ports = []
    for port in ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            result = s.connect_ex((ip, port))
            if result == 0:
                open_ports.append(port)
            s.close()
        except Exception:
            pass
    return open_ports

def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return "Unknown"

COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
    443: "HTTPS", 445: "SMB", 3306: "MySQL",
    3389: "RDP", 5900: "VNC", 8080: "HTTP-Alt", 8443: "HTTPS-Alt"
}

PORT_RISK = {
    23: "HIGH",   # Telnet - unencrypted
    21: "MED",    # FTP
    3389: "HIGH", # RDP exposed
    5900: "HIGH", # VNC
    445: "HIGH",  # SMB
    3306: "MED",  # DB exposed
}

# ─── CUSTOM WIDGETS ────────────────────────────────────────────────────────────

class GlowButton(Button):
    def __init__(self, accent=None, **kwargs):
        super().__init__(**kwargs)
        self.accent = accent or COLORS['accent']
        self.background_color = (0, 0, 0, 0)
        self.color = COLORS['bg_dark']
        self.bold = True
        self.font_size = dp(14)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.accent)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])

class OutlineButton(Button):
    def __init__(self, accent=None, **kwargs):
        super().__init__(**kwargs)
        self.accent = accent or COLORS['accent']
        self.background_color = (0, 0, 0, 0)
        self.color = self.accent
        self.bold = True
        self.font_size = dp(13)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COLORS['bg_card'])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
            Color(*self.accent)
            Line(rounded_rectangle=[self.x, self.y, self.width, self.height, dp(8)], width=1.2)

class DeviceCard(BoxLayout):
    def __init__(self, device_data, on_tap=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(14)
        self.spacing = dp(6)
        self.size_hint_y = None
        self.height = dp(110)
        self.device_data = device_data
        self.on_tap_cb = on_tap

        # Risk color
        risk = device_data.get('risk', 'LOW')
        risk_color = COLORS['danger'] if risk == 'HIGH' else (COLORS['warn'] if risk == 'MED' else COLORS['accent'])

        with self.canvas.before:
            Color(*COLORS['bg_card'])
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            Color(*risk_color[:3], 0.6)
            self._border = Line(rounded_rectangle=[self.x, self.y, self.width, self.height, dp(10)], width=1.0)

        self.bind(pos=self._update_bg, size=self._update_bg)

        # Top row: IP + risk badge
        top = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))
        ip_lbl = Label(
            text=device_data['ip'],
            color=COLORS['text_main'],
            font_size=dp(15),
            bold=True,
            size_hint_x=0.6,
            halign='left',
            text_size=(None, None)
        )
        risk_lbl = Label(
            text=f"  {risk} RISK  ",
            color=risk_color,
            font_size=dp(11),
            bold=True,
            size_hint_x=0.4,
            halign='right'
        )
        top.add_widget(ip_lbl)
        top.add_widget(risk_lbl)
        self.add_widget(top)

        # Hostname
        host_lbl = Label(
            text=device_data.get('hostname', 'Unknown'),
            color=COLORS['text_dim'],
            font_size=dp(12),
            size_hint_y=None,
            height=dp(18),
            halign='left',
            text_size=(Window.width - dp(60), None)
        )
        self.add_widget(host_lbl)

        # Ports
        ports = device_data.get('open_ports', [])
        if ports:
            port_strs = [f"{p}({COMMON_PORTS.get(p,'')})" for p in ports[:5]]
            port_text = "  ".join(port_strs)
        else:
            port_text = "No open ports detected"

        port_lbl = Label(
            text=port_text,
            color=COLORS['accent2'],
            font_size=dp(11),
            size_hint_y=None,
            height=dp(16),
            halign='left',
            text_size=(Window.width - dp(60), None)
        )
        self.add_widget(port_lbl)

        # Detail button
        if on_tap:
            btn = OutlineButton(
                text="VIEW DETAILS →",
                size_hint_y=None,
                height=dp(28),
                accent=COLORS['accent']
            )
            btn.bind(on_press=lambda x: on_tap(device_data))
            self.add_widget(btn)

    def _update_bg(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size
        risk = self.device_data.get('risk', 'LOW')
        self._border.rounded_rectangle = [self.x, self.y, self.width, self.height, dp(10)]

# ─── SCREENS ───────────────────────────────────────────────────────────────────

class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scan_results = []
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        # ── Header ──
        header = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
        title_col = BoxLayout(orientation='vertical')
        title_lbl = Label(
            text="[b]NETSCAN PRO[/b]",
            markup=True,
            color=COLORS['accent'],
            font_size=dp(20),
            halign='left',
            size_hint_y=None,
            height=dp(32)
        )
        subtitle = Label(
            text="Wi-Fi Network Analyzer",
            color=COLORS['text_dim'],
            font_size=dp(11),
            halign='left',
            size_hint_y=None,
            height=dp(18)
        )
        title_col.add_widget(title_lbl)
        title_col.add_widget(subtitle)
        header.add_widget(title_col)
        header.add_widget(Widget())

        history_btn = OutlineButton(
            text="HISTORY",
            size_hint=(None, None),
            size=(dp(90), dp(36)),
            accent=COLORS['accent2']
        )
        history_btn.bind(on_press=self.go_history)
        header.add_widget(history_btn)
        root.add_widget(header)

        # ── Info Card ──
        self.local_ip = get_local_ip()
        info_box = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(90),
            padding=dp(14),
            spacing=dp(4)
        )
        with info_box.canvas.before:
            Color(*COLORS['bg_card'])
            RoundedRectangle(pos=info_box.pos, size=info_box.size, radius=[dp(10)])
        info_box.bind(pos=lambda w, v: setattr(w.canvas.before.children[1], 'pos', v),
                      size=lambda w, v: setattr(w.canvas.before.children[1], 'size', v))

        ip_row = BoxLayout(size_hint_y=None, height=dp(24))
        ip_row.add_widget(Label(text="YOUR IP", color=COLORS['text_dim'], font_size=dp(11), halign='left', size_hint_x=0.35))
        self.ip_label = Label(text=self.local_ip, color=COLORS['accent'], font_size=dp(14), bold=True, halign='left', size_hint_x=0.65)
        ip_row.add_widget(self.ip_label)

        net_row = BoxLayout(size_hint_y=None, height=dp(24))
        prefix = get_network_prefix(self.local_ip)
        net_row.add_widget(Label(text="NETWORK", color=COLORS['text_dim'], font_size=dp(11), halign='left', size_hint_x=0.35))
        net_row.add_widget(Label(text=f"{prefix}.0/24", color=COLORS['text_main'], font_size=dp(13), halign='left', size_hint_x=0.65))

        stat_row = BoxLayout(size_hint_y=None, height=dp(24))
        stat_row.add_widget(Label(text="DEVICES", color=COLORS['text_dim'], font_size=dp(11), halign='left', size_hint_x=0.35))
        self.devices_count = Label(text="—", color=COLORS['accent2'], font_size=dp(13), bold=True, halign='left', size_hint_x=0.65)
        stat_row.add_widget(self.devices_count)

        info_box.add_widget(ip_row)
        info_box.add_widget(net_row)
        info_box.add_widget(stat_row)
        root.add_widget(info_box)

        # ── Range Row ──
        range_row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(10))
        range_row.add_widget(Label(text="Range:", color=COLORS['text_dim'], font_size=dp(13), size_hint_x=None, width=dp(55)))
        self.range_input = TextInput(
            text=f"{get_network_prefix(self.local_ip)}.1",
            multiline=False,
            font_size=dp(13),
            background_color=COLORS['bg_input'],
            foreground_color=COLORS['text_main'],
            cursor_color=COLORS['accent'],
            size_hint_x=0.5,
            hint_text="e.g. 192.168.1.1"
        )
        self.end_input = TextInput(
            text="254",
            multiline=False,
            font_size=dp(13),
            background_color=COLORS['bg_input'],
            foreground_color=COLORS['text_main'],
            cursor_color=COLORS['accent'],
            size_hint_x=0.2,
            hint_text="end"
        )
        range_row.add_widget(self.range_input)
        range_row.add_widget(Label(text="to", color=COLORS['text_dim'], font_size=dp(12), size_hint_x=None, width=dp(20)))
        range_row.add_widget(self.end_input)
        root.add_widget(range_row)

        # ── Scan Button ──
        self.scan_btn = GlowButton(text="▶  START SCAN", size_hint_y=None, height=dp(48))
        self.scan_btn.bind(on_press=self.start_scan)
        root.add_widget(self.scan_btn)

        # ── Progress ──
        self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(6))
        self.status_label = Label(
            text="Ready to scan",
            color=COLORS['text_dim'],
            font_size=dp(12),
            size_hint_y=None,
            height=dp(20)
        )
        root.add_widget(self.progress_bar)
        root.add_widget(self.status_label)

        # ── Results ──
        results_header = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(10))
        results_header.add_widget(Label(text="DISCOVERED DEVICES", color=COLORS['text_dim'], font_size=dp(11), halign='left'))
        self.sort_btn = OutlineButton(text="SORT BY RISK", size_hint=(None, None), size=(dp(110), dp(26)), accent=COLORS['accent2'])
        self.sort_btn.bind(on_press=self.sort_by_risk)
        results_header.add_widget(self.sort_btn)
        root.add_widget(results_header)

        self.scroll = ScrollView()
        self.results_layout = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        self.results_layout.bind(minimum_height=self.results_layout.setter('height'))
        self.scroll.add_widget(self.results_layout)
        root.add_widget(self.scroll)

        self.add_widget(root)

    def go_history(self, *args):
        self.manager.current = 'history'

    def start_scan(self, *args):
        self.scan_btn.disabled = True
        self.scan_btn.text = "⏳  SCANNING..."
        self.scan_results = []
        self.results_layout.clear_widgets()
        self.progress_bar.value = 0
        self.status_label.text = "Initializing scan..."

        base_ip = self.range_input.text.strip()
        try:
            end = int(self.end_input.text.strip())
        except ValueError:
            end = 254

        # parse base
        parts = base_ip.split('.')
        prefix = '.'.join(parts[:3])
        try:
            start_host = int(parts[3])
        except (IndexError, ValueError):
            start_host = 1

        thread = threading.Thread(
            target=self._scan_network,
            args=(prefix, start_host, end),
            daemon=True
        )
        thread.start()

    def _scan_network(self, prefix, start, end):
        total = end - start + 1
        found = []

        def update_ui(dt):
            pass

        for i, host in enumerate(range(start, end + 1)):
            ip = f"{prefix}.{host}"
            progress = int(((i + 1) / total) * 100)

            Clock.schedule_once(lambda dt, p=progress, ip_=ip: self._update_progress(p, ip_))

            if ping_host(ip, timeout=1):
                ports = scan_ports(ip, list(COMMON_PORTS.keys()), timeout=0.4)
                hostname = get_hostname(ip)

                # Calculate risk
                risk = 'LOW'
                for p in ports:
                    r = PORT_RISK.get(p, 'LOW')
                    if r == 'HIGH':
                        risk = 'HIGH'
                        break
                    elif r == 'MED' and risk == 'LOW':
                        risk = 'MED'

                device = {
                    'ip': ip,
                    'hostname': hostname,
                    'open_ports': ports,
                    'risk': risk,
                    'scanned_at': datetime.now().strftime("%H:%M:%S")
                }
                found.append(device)
                Clock.schedule_once(lambda dt, d=device: self._add_device_card(d))

        Clock.schedule_once(lambda dt: self._scan_complete(found))

    def _update_progress(self, progress, current_ip):
        self.progress_bar.value = progress
        self.status_label.text = f"Scanning {current_ip}... ({progress}%)"

    def _add_device_card(self, device):
        self.scan_results.append(device)
        card = DeviceCard(device, on_tap=self.show_device_detail)
        self.results_layout.add_widget(card)
        self.devices_count.text = str(len(self.scan_results))

    def _scan_complete(self, found):
        self.scan_btn.disabled = False
        self.scan_btn.text = "▶  START SCAN"
        self.progress_bar.value = 100
        count = len(found)
        self.status_label.text = f"✓ Scan complete — {count} device{'s' if count != 1 else ''} found"

        # Save to history
        app = App.get_running_app()
        app.add_to_history(found)

        if count == 0:
            empty_lbl = Label(
                text="No devices found.\nCheck your network connection.",
                color=COLORS['text_dim'],
                font_size=dp(14),
                halign='center',
                size_hint_y=None,
                height=dp(80)
            )
            self.results_layout.add_widget(empty_lbl)

    def sort_by_risk(self, *args):
        if not self.scan_results:
            return
        order = {'HIGH': 0, 'MED': 1, 'LOW': 2}
        self.scan_results.sort(key=lambda d: order.get(d.get('risk', 'LOW'), 2))
        self.results_layout.clear_widgets()
        for device in self.scan_results:
            card = DeviceCard(device, on_tap=self.show_device_detail)
            self.results_layout.add_widget(card)

    def show_device_detail(self, device_data):
        app = App.get_running_app()
        app.root.get_screen('detail').load_device(device_data)
        app.root.current = 'detail'


class DeviceDetailScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.device = {}

    def load_device(self, device_data):
        self.device = device_data
        self.clear_widgets()
        self._build_ui()

    def _build_ui(self):
        d = self.device
        risk = d.get('risk', 'LOW')
        risk_color = COLORS['danger'] if risk == 'HIGH' else (COLORS['warn'] if risk == 'MED' else COLORS['accent'])

        root = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(14))

        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
        back_btn = OutlineButton(text="← BACK", size_hint=(None, None), size=(dp(80), dp(36)), accent=COLORS['accent2'])
        back_btn.bind(on_press=lambda x: setattr(App.get_running_app().root, 'current', 'dashboard'))
        hdr.add_widget(back_btn)
        hdr.add_widget(Label(text="[b]DEVICE REPORT[/b]", markup=True, color=COLORS['accent'], font_size=dp(17)))
        root.add_widget(hdr)

        # IP + Risk banner
        banner = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80), padding=dp(14), spacing=dp(4))
        with banner.canvas.before:
            Color(*COLORS['bg_card'])
            self._banner_rect = RoundedRectangle(pos=banner.pos, size=banner.size, radius=[dp(10)])
            Color(*risk_color[:3], 0.25)
            self._banner_hl = RoundedRectangle(pos=banner.pos, size=banner.size, radius=[dp(10)])
        banner.bind(pos=self._update_banner, size=self._update_banner)

        banner.add_widget(Label(text=d['ip'], color=risk_color, font_size=dp(22), bold=True, halign='left', size_hint_y=None, height=dp(32)))
        banner.add_widget(Label(text=f"Risk Level: {risk}  •  Scanned at {d.get('scanned_at','')}", color=COLORS['text_dim'], font_size=dp(12), halign='left', size_hint_y=None, height=dp(20)))
        root.add_widget(banner)

        # Details grid
        info_section = self._make_section("DEVICE INFO")
        info_section.add_widget(self._row("Hostname", d.get('hostname', 'Unknown')))
        info_section.add_widget(self._row("IP Address", d['ip']))
        info_section.add_widget(self._row("Status", "ONLINE", COLORS['accent']))
        root.add_widget(info_section)

        # Ports section
        ports_section = self._make_section("OPEN PORTS")
        ports = d.get('open_ports', [])
        if ports:
            for port in ports:
                service = COMMON_PORTS.get(port, 'Unknown')
                port_risk = PORT_RISK.get(port, 'LOW')
                pr_color = COLORS['danger'] if port_risk == 'HIGH' else (COLORS['warn'] if port_risk == 'MED' else COLORS['accent'])
                row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(8))
                row.add_widget(Label(text=str(port), color=COLORS['accent2'], font_size=dp(14), bold=True, size_hint_x=0.2, halign='left'))
                row.add_widget(Label(text=service, color=COLORS['text_main'], font_size=dp(13), size_hint_x=0.5, halign='left'))
                row.add_widget(Label(text=port_risk, color=pr_color, font_size=dp(12), bold=True, size_hint_x=0.3, halign='right'))
                ports_section.add_widget(row)
        else:
            ports_section.add_widget(Label(text="No open ports detected", color=COLORS['text_dim'], font_size=dp(13), size_hint_y=None, height=dp(30)))
        root.add_widget(ports_section)

        # Security recommendations
        rec_section = self._make_section("SECURITY RECOMMENDATIONS")
        recs = self._get_recommendations(d)
        for rec in recs:
            rec_box = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
            bullet = Label(text="⚠" if rec['level'] == 'warn' else "✓", color=COLORS['warn'] if rec['level'] == 'warn' else COLORS['accent'], font_size=dp(16), size_hint_x=None, width=dp(24))
            rec_lbl = Label(text=rec['text'], color=COLORS['text_main'], font_size=dp(12), halign='left', text_size=(Window.width - dp(80), None), size_hint_y=None, height=dp(36))
            rec_box.add_widget(bullet)
            rec_box.add_widget(rec_lbl)
            rec_section.add_widget(rec_box)
        root.add_widget(rec_section)

        self.add_widget(root)

    def _make_section(self, title):
        box = BoxLayout(orientation='vertical', size_hint_y=None, padding=[dp(14), dp(10)], spacing=dp(6))
        box.bind(minimum_height=box.setter('height'))
        with box.canvas.before:
            Color(*COLORS['bg_card'])
            rect = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(10)])
        box.bind(pos=lambda w, v: setattr(rect, 'pos', v), size=lambda w, v: setattr(rect, 'size', v))

        title_lbl = Label(text=title, color=COLORS['text_dim'], font_size=dp(11), bold=True, size_hint_y=None, height=dp(22), halign='left')
        box.add_widget(title_lbl)
        return box

    def _row(self, label, value, value_color=None):
        row = BoxLayout(size_hint_y=None, height=dp(30))
        row.add_widget(Label(text=label, color=COLORS['text_dim'], font_size=dp(12), size_hint_x=0.4, halign='left'))
        row.add_widget(Label(text=value, color=value_color or COLORS['text_main'], font_size=dp(13), bold=bool(value_color), size_hint_x=0.6, halign='left'))
        return row

    def _get_recommendations(self, device):
        recs = []
        ports = device.get('open_ports', [])
        if 23 in ports:
            recs.append({'text': 'Telnet (23) is open — disable immediately, use SSH instead', 'level': 'warn'})
        if 21 in ports:
            recs.append({'text': 'FTP (21) transmits data unencrypted — switch to SFTP', 'level': 'warn'})
        if 3389 in ports:
            recs.append({'text': 'RDP (3389) exposed — restrict access with firewall rules', 'level': 'warn'})
        if 5900 in ports:
            recs.append({'text': 'VNC (5900) open — ensure strong password is set', 'level': 'warn'})
        if 445 in ports:
            recs.append({'text': 'SMB (445) exposed — update Windows, check for EternalBlue', 'level': 'warn'})
        if not ports:
            recs.append({'text': 'No exposed ports — device appears well hardened', 'level': 'ok'})
        if device.get('risk') == 'LOW' and ports:
            recs.append({'text': 'Only low-risk services detected — maintain regular patching', 'level': 'ok'})
        return recs if recs else [{'text': 'Run full scan for detailed recommendations', 'level': 'ok'}]

    def _update_banner(self, widget, *args):
        self._banner_rect.pos = widget.pos
        self._banner_rect.size = widget.size
        self._banner_hl.pos = widget.pos
        self._banner_hl.size = widget.size


class HistoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        hdr = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
        back_btn = OutlineButton(text="← BACK", size_hint=(None, None), size=(dp(80), dp(36)), accent=COLORS['accent2'])
        back_btn.bind(on_press=lambda x: setattr(App.get_running_app().root, 'current', 'dashboard'))
        hdr.add_widget(back_btn)
        hdr.add_widget(Label(text="[b]SCAN HISTORY[/b]", markup=True, color=COLORS['accent'], font_size=dp(17)))
        root.add_widget(hdr)

        self.scroll = ScrollView()
        self.history_layout = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, padding=[0, dp(4)])
        self.history_layout.bind(minimum_height=self.history_layout.setter('height'))
        self.scroll.add_widget(self.history_layout)
        root.add_widget(self.scroll)

        clear_btn = OutlineButton(text="CLEAR HISTORY", size_hint_y=None, height=dp(44), accent=COLORS['danger'])
        clear_btn.bind(on_press=self.clear_history)
        root.add_widget(clear_btn)

        self.add_widget(root)

    def on_enter(self):
        self.refresh()

    def refresh(self):
        self.history_layout.clear_widgets()
        app = App.get_running_app()
        if not app.scan_history:
            self.history_layout.add_widget(Label(
                text="No scans recorded yet.\nRun a scan from the dashboard.",
                color=COLORS['text_dim'],
                font_size=dp(14),
                halign='center',
                size_hint_y=None,
                height=dp(80)
            ))
            return

        for entry in reversed(app.scan_history):
            card = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80), padding=dp(12), spacing=dp(4))
            with card.canvas.before:
                Color(*COLORS['bg_card'])
                rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(10)])
            card.bind(pos=lambda w, v: setattr(rect, 'pos', v), size=lambda w, v: setattr(rect, 'size', v))

            card.add_widget(Label(text=f"Scan — {entry['time']}", color=COLORS['text_main'], font_size=dp(14), bold=True, size_hint_y=None, height=dp(24), halign='left'))
            card.add_widget(Label(text=f"{entry['count']} device(s) found", color=COLORS['text_dim'], font_size=dp(12), size_hint_y=None, height=dp(20), halign='left'))
            highs = sum(1 for d in entry['devices'] if d.get('risk') == 'HIGH')
            risk_txt = f"{highs} HIGH risk" if highs else "No high-risk devices"
            risk_color = COLORS['danger'] if highs else COLORS['accent']
            card.add_widget(Label(text=risk_txt, color=risk_color, font_size=dp(12), size_hint_y=None, height=dp(18), halign='left'))
            self.history_layout.add_widget(card)

    def clear_history(self, *args):
        App.get_running_app().scan_history = []
        self.refresh()


# ─── APP ───────────────────────────────────────────────────────────────────────

class NetScanApp(App):
    scan_history = []

    def build(self):
        self.title = "NetScan Pro"
        sm = ScreenManager(transition=FadeTransition(duration=0.2))
        sm.add_widget(DashboardScreen(name='dashboard'))
        sm.add_widget(DeviceDetailScreen(name='detail'))
        sm.add_widget(HistoryScreen(name='history'))
        return sm

    def add_to_history(self, devices):
        entry = {
            'time': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'count': len(devices),
            'devices': devices
        }
        self.scan_history.append(entry)


if __name__ == '__main__':
    NetScanApp().run()
