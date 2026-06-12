# NetScan Pro 🔍
### Android Network Scanner — Built with Python & Kivy

A cybersecurity Android app that scans your local Wi-Fi network for connected devices, checks open ports, assesses risk levels, and provides security recommendations.

---

## Features

- **Network Discovery** — Ping-sweep your subnet to find all live devices
- **Port Scanning** — Checks 15 common ports (SSH, HTTP, RDP, SMB, VNC, etc.)
- **Risk Assessment** — Flags HIGH / MED / LOW risk based on exposed services
- **Hostname Resolution** — Resolves device names via reverse DNS
- **Device Detail View** — Full report per device with security advice
- **Scan History** — Review past scan sessions
- **Cyberpunk UI** — Dark neon theme optimized for mobile

---

## Project Structure

```
network_scanner/
├── main.py           # Full app (UI + scanning logic)
├── buildozer.spec    # Android build config
├── requirements.txt  # Python deps
└── assets/           # Icons/splash (add your own)
```

---

## Run on Desktop (for testing)

```bash
# 1. Install Kivy
pip install kivy

# 2. Run
python main.py
```

---

## Build for Android

### Prerequisites
- Linux or macOS (WSL2 on Windows works)
- Python 3.8+
- Java JDK 17
- Android SDK/NDK (auto-installed by buildozer)

### Steps

```bash
# 1. Install buildozer
pip install buildozer

# 2. Install system deps (Ubuntu/Debian)
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip \
    autoconf libtool pkg-config zlib1g-dev libncurses5-dev \
    libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# 3. Build APK (first build takes ~15–20 min)
cd network_scanner
buildozer android debug

# 4. Install on connected Android device
buildozer android deploy run
```

The APK will be in `bin/netscanpro-1.0-debug.apk`

---

## Android Permissions Used

| Permission | Why |
|---|---|
| `INTERNET` | Network scanning |
| `ACCESS_WIFI_STATE` | Read Wi-Fi info |
| `ACCESS_NETWORK_STATE` | Check connectivity |
| `CHANGE_WIFI_STATE` | Wi-Fi control |

---

## Scanned Ports & Risk Levels

| Port | Service | Risk |
|---|---|---|
| 22 | SSH | LOW |
| 80 | HTTP | LOW |
| 443 | HTTPS | LOW |
| 21 | FTP | MED |
| 3306 | MySQL | MED |
| 23 | Telnet | HIGH |
| 3389 | RDP | HIGH |
| 5900 | VNC | HIGH |
| 445 | SMB | HIGH |

---

## Ethical Notice

This tool is for **authorized network testing only**. Only scan networks you own or have explicit permission to test. Unauthorized scanning may violate computer crime laws.
