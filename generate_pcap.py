from scapy.all import *
import base64
import random
import string
import codecs

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

# Reverse shell handshake decoy
packets += [
    IP(src=victim_ip, dst=attacker_ip)/TCP(sport=3333, dport=4444, flags="S"),
    IP(src=attacker_ip, dst=victim_ip)/TCP(sport=4444, dport=3333, flags="SA"),
    IP(src=victim_ip, dst=attacker_ip)/TCP(sport=3333, dport=4444, flags="A")
]

# Base64-like command decoys
commands = [
    ("echo RkFLRV9GTEFHX0hFUkU=", "fm_{aprilfool}"),
    ("echo SElERU5fRkxBRw==", "fm_ct{nothing_here}")
]

for cmd, resp in commands:
    packets.append(IP(src=victim_ip, dst=attacker_ip)/TCP(sport=3333, dport=4444, flags="PA")/Raw(load=cmd))
    packets.append(IP(src=attacker_ip, dst=victim_ip)/TCP(sport=4444, dport=3333, flags="PA")/Raw(load=resp))

# Subtle DNS hint
packets.append(IP(src=victim_ip, dst=dns_server)/UDP(sport=RandShort(), dport=53)/DNS(rd=1, qd=DNSQR(qname="rot13.this.is.not.malware.net")))

# 100 fake flags
sarcastic_keywords = [
    "NICE_TRY", "TOTALLY_REAL", "YOU_WISH", "IM_NOT_THE_ONE", "FAKE_FLAG_ALERT", "LOL_NOPE",
    "SO_CLOSE", "404FLAGNOTFOUND", "DENIED", "WRONG_ONE", "NOT_IT", "TRY_AGAIN", "REALISH",
    "KEEP_LOOKING", "LOLFLAG", "NOPENOPENOPE", "ALMOST_HAD_IT", "FLAGLESS", "NEVER_FOUND_ME",
    "IM_A_TRAP", "FAKER_THAN_YOUR_EXCUSES", "LOLNICE", "UNTOUCHABLE", "IS_THIS_IT", "THIS_IS_NOT",
    "TRICKEDYA", "FALSE_POSITIVE", "FAKE_NEWS", "MISS_ME", "HA_GOTEM", "PROBABLY_NOT", "ERRFLAGX",
    "REALLY_THO", "CLOSE_BUT_NO", "DEC0Y_FLAG", "WRONG_PORTAL", "MAYBE?", "JOKES_ON_YOU",
    "PRETENDING", "DELIBERATELY_FAKE", "TOTALLY_A_FLAG", "YEAH_NO", "SECRETLY_FAKE", "MISLEADING",
    "BEEP_BOOP", "FLAG_OF_IMAGINATION", "HARD_PASS", "GHOST_FLAG", "RED_HERRING"
]

for _ in range(100):
    word = random.choice(sarcastic_keywords)
    fake_flag = f"flag{{{word}_{random.randint(100, 999)}}}"
    base64_cmd = base64.b64encode(f"echo {fake_flag}".encode()).decode()
    packets.append(IP(src=victim_ip, dst=attacker_ip)/TCP(sport=3333, dport=4444, flags="PA")/Raw(load=f"echo {base64_cmd}"))
    packets.append(IP(src=attacker_ip, dst=victim_ip)/TCP(sport=4444, dport=3333, flags="PA")/Raw(load=fake_flag))

# Simulated pip install
packets.append(IP(src=victim_ip, dst=attacker_ip)/TCP(sport=5555, dport=80, flags="PA")/Raw(load="pip install cyberrush"))
packets.append(IP(src=attacker_ip, dst=victim_ip)/TCP(sport=80, dport=5555, flags="PA")/Raw(load="HTTP/1.1 200 OK\r\nContent-Type: application/gzip\r\n\r\n<binary data: cyberushtar.gz>"))

# Real flag in obfuscated ROT13 setup script
real_flag = "FM_CTF{y)v_cRkd3D_tII3_C0d#}"
rot13_flag = codecs.encode(real_flag, 'rot_13')

setup_script = (
    "import os\n"
    "# hmm this feels... rotated? 🤔\n"
    "def obf(s):\n"
    "    return ''.join(chr(((ord(c)-97+13)%26)+97) if c.islower() else "
    "chr(((ord(c)-65+13)%26)+65) if c.isupper() else c for c in s)\n"
    f"cmd = obf('{rot13_flag}')\n"
    "os.system(cmd)\n"
)

packets.append(IP(src=attacker_ip, dst=victim_ip)/TCP(sport=80, dport=5555, flags="PA")/Raw(load=setup_script))

# Save PCAP
wrpcap("localfile_dump.pcap", packets)
