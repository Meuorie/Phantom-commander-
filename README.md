# Phantom Commander

Zero‑trace network auditor.
Built with Python, Scapy, and Rich UI.
**For educational purposes only.**

## Requirements
- Linux (Arch recommended)
- Python 3
- Root privileges
- Wireless card with monitor mode (for WiFi Void)
- Scapy & Rich (`pip install scapy rich`)

## Quick Start
```bash
git clone https://github.com/Meuorie/PhantomCommander.git
cd PhantomCommander
sudo python3 phantom_commander.py

## What It Does

· Ghost Scan – silently discovers all live hosts on the local subnet.
· Silent MITM – ARP spoofs the target and gateway to capture HTTP traffic.
· WiFi Void – floods deauthentication packets to disconnect a device from Wi‑Fi.
· Surgical Exit – restores the target's ARP cache, leaving no trace.

## Disclaimer

This tool is for authorized testing only.
Do not use it on networks or devices you do not own.
The author assumes no responsibility for misuse.

```
