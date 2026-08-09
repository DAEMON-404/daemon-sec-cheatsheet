---
title: "Shodan"
description: "Shodan search filters, dorks, CLI and API workflows for internet-wide asset and service discovery."
category: enumeration
tags: [enumeration, osint, recon]
tools: [Shodan]
difficulty: intermediate
updated: "2026-08-09"
source: "repo:Enumeration/Shodan_Cheatsheet.md"
---

# Shodan

**Shodan** is the world's first search engine for Internet-connected devices. Unlike traditional search engines that index web content, Shodan indexes device information.

| Function | Description |
|:---------|:------------|
| Banner Grabbing | Captures service banners and metadata |
| Port Scanning | Indexes open ports and services |
| Vulnerability Detection | Identifies known CVEs |
| SSL/TLS Analysis | Certificate and encryption info |
| Geographic Mapping | Device location tracking |
| Historical Data | Track changes over time |

## Getting Started

### Account Setup

1. Create an account at [shodan.io](https://www.shodan.io).
2. Get your API key: Account → API Key.
3. Choose a plan (free tier available with limitations).

### Plan Comparison

| Feature | Free | Membership | Small Business | Corporate |
|:--------|:----:|:----------:|:--------------:|:---------:|
| Search Results | 10 | Unlimited | Unlimited | Unlimited |
| Query Credits | 0 | 100/month | 10,000/month | Unlimited |
| Scan Credits | 0 | 100/month | 5,000/month | Unlimited |
| Network Monitoring | No | Yes | Yes | Yes |
| API Access | Limited | Full | Full | Full |

### CLI Installation

```bash
# Install via pip
pip install shodan

# Initialize with API key
shodan init YOUR_API_KEY

# Verify installation
shodan info
```

## Query Syntax Reference

### Core Filters

| Filter | Example |
|:------|:-------|
| `title:` | `title:"Admin Panel"` |
| `product:` | `product:"Apache"` |
| `port:` | `port:22` |
| `country:` | `country:"US"` |
| `city:` | `city:"New York"` |
| `region:` | `region:"California"` |
| `org:` | `org:"Google"` |
| `asn:` | `asn:AS15169` |
| `net:` | `net:8.8.8.0/24` |
| `geo:` | `geo:"40.7128,-74.0060"` |
| `vuln:` | `vuln:CVE-2021-44228` |
| `has_screenshot:` | `has_screenshot:true` |
| `html:` | `html:"server version"` |
| `header:` | `header:"Server: Nginx"` |
| `ssl:` | `ssl:"Google"` |
| `ssl.cert.subject.cn:` | `ssl.cert.subject.cn:"*.google.com"` |
| `ssl.cert.issuer.cn:` | `ssl.cert.issuer.cn:"Let's Encrypt"` |
| `os:` | `os:"Windows Server 2019"` |
| `before:` | `before:01/01/2024` |
| `after:` | `after:01/01/2024` |
| `hostname:` | `hostname:"example.com"` |
| `isp:` | `isp:"Comcast"` |
| `version:` | `version:"7.4"` |
| `http.title:` | `http.title:"Dashboard"` |
| `http.status:` | `http.status:200` |
| `http.component:` | `http.component:"WordPress"` |
| `http.favicon.hash:` | `http.favicon.hash:116323821` |

### Boolean Operators

- **AND** → implicit (space between filters)
- **OR** → explicit `OR` keyword
- **NOT** → minus sign (`-`) or `NOT` keyword

```text
# AND (implicit)
apache port:80 country:US

# OR
title:"Camera" OR title:"Webcam"

# NOT
apache -country:CN
apache NOT country:CN
```

## Finding Cameras

> **Note — Common IP camera ports.** HTTP: 80, 8080 · HTTPS: 443 · RTSP: 554 · custom ports vary by manufacturer (e.g. 81, 8888).

### Camera Brands and Queries

| Brand | Common Ports | Search Query |
|:------|:-------------|:-------------|
| Axis | 80, 443 | `title:"AXIS"` / `product:"Axis"` |
| D-Link | 80, 8080 | `title:"DCS-930L"` / `product:"D-Link"` |
| Foscam | 80, 88, 443 | `title:"Foscam"` / `product:"Foscam"` |
| Hikvision | 80, 443, 554, 8000, 8080 | `title:"Hikvision"` / `product:"Hikvision"` |
| Dahua | 80, 443, 554, 8000, 8080, 8081, 8888 | `title:"Dahua"` / `html:"Dahua"` |
| Ubiquiti UniFi | 80, 443, 8080, 8443, 7080, 7443 | `title:"UniFi"` / `"UniFi Video"` |
| Reolink | 80, 443, 8080 | `title:"Reolink"` / `product:"Reolink"` |
| Linksys | 80, 1024 | `title:"Linksys WVC80N"` |
| Panasonic | 80, 443 | `title:"Panasonic Network Camera"` |
| Sony | 80, 443 | `title:"Sony Network Camera"` |
| Trendnet | 80, 443 | `title:"TV-IP"` |
| TP-Link | 80, 8080 | `title:"TP-Link"` |
| Vivotek | 80, 443 | `title:"Vivotek"` |
| AvTech | 80, 8888 | `title:"AVTech"` |
| Wansview | 80, 8080 | `title:"Wansview"` |
| Wyze | 80, 443, 8080 | `title:"Wyze"` |
| Uniview | 80, 443, 554, 8080 | `title:"Uniview"` |
| Amcrest | 80, 8080, 8000 | `title:"Amcrest"` |
| Lorex | 80, 443 | `title:"Lorex"` |
| Mobotix | 80, 443, 8080 | `title:"Mobotix"` |
| Avigilon | 80, 443, 554, 8080 | `title:"Avigilon"` |
| FLIR | 80, 443, 554 | `title:"FLIR"` |

### Example Camera Queries

```text
title:"AXIS" country:"US"                                # Axis cameras in the US
title:"Foscam" has_screenshot:true                       # Foscam with screenshots
title:"Hikvision" city:"New York"                        # Hikvision in New York
title:"TP-Link" port:8080                                # TP-Link on port 8080
title:"DCS-930L" port:8080                               # D-Link on custom port
title:"Reolink" country:"DE" OR country:"GB" OR country:"FR"  # Reolink in Europe
"UniFi Video" has_screenshot:true                        # UniFi with screenshots
html:"Dahua" port:80                                     # Dahua HTML interface
```

## Tips and Tricks for Advanced Searching

**Boolean operators:**
```text
title:"Axis" OR title:"Hikvision" OR title:"Dahua"     # multiple brands
title:"Camera" AND port:8080 AND country:"US"          # combine filters
title:"Camera" NOT "authentication required"           # exclude results
```

**Advanced query techniques:**
```text
header:"Server: Boa"                                    # by HTTP header
http.status:200 "admin"                                 # by HTTP status code
"200 OK" http.title:"Index of"                          # open web interfaces
title:"Camera" (port:80 OR port:8080 OR port:8888)      # across multiple ports
product:"Apache" "2.2.15"                               # product + vulnerable version
http.favicon.hash:116323821                             # by favicon hash
ssl.cert.subject.cn:"*.target.com"                      # by SSL certificate
```

**Filtering by response content:**
```text
"username" "password" filetype:html
"It works!" "Apache"                                    # default pages
title:"Admin" OR title:"Administration" OR title:"Dashboard"
http.title:"Login" OR http.title:"Sign In"
```

**Organizational & network searches:**
```text
org:"Company Name"
asn:AS12345
net:192.168.1.0/24
isp:"Amazon Technologies"
```

**Performance tips:** use specific queries; combine `port:` with `product`/`title`; use `has_screenshot` sparingly (slows queries); narrow geographic scope; prefer title/product filters (indexed, faster than HTML content).

## Finding Vulnerable Servers

> **Important —** These queries help identify common vulnerabilities. Always use findings responsibly and with proper authorization.

### Known Vulnerability Queries

```text
vuln:CVE-2014-0160      # Heartbleed
vuln:CVE-2014-0224      # OpenSSL CCS Injection
vuln:CVE-2014-6271      # Shellshock
vuln:ms17-010           # EternalBlue
vuln:CVE-2021-44228     # Log4Shell
vuln:CVE-2021-26855     # ProxyLogon
vuln:CVE-2019-0708      # BlueKeep
vuln:CVE-2017-5638      # Apache Struts
vuln:CVE-2020-1472      # Zerologon
vuln:CVE-2021-34527     # PrintNightmare
```

### Default Credentials

```text
"220" "Anonymous FTP login allowed"
"220" "telnet" "default password"
"default password" http.title:"admin"
"cisco" "level 15 access"
```

### Outdated Software

```text
"Apache/2.2.15"
"Microsoft-IIS/6.0"
"OpenSSH_5"
"nginx/1.4"
"PHP/5.2"
```

### Example Queries by Service

```text
"MongoDB Server Information" port:27017          # open MongoDB
"200 OK" "elastic indices" port:9200             # ElasticSearch without auth
port:445 "smb" "NT_STATUS_ACCESS_DENIED"         # open SMB
port:3389 "Remote Desktop Protocol"              # exposed RDP
"X-Jenkins" "200 OK"                             # Jenkins without auth
"kube-apiserver" port:6443                        # exposed Kubernetes API
"couchdb" port:5984 "200 OK"                      # CouchDB no auth
```

### Geographic Vulnerability Filtering

```text
vuln:ms17-010 country:"US"                                    # EternalBlue in US
"MongoDB Server Information" port:27017 country:"DE"          # open MongoDB in Germany
vuln:CVE-2014-6271 region:"California"                        # Shellshock in California
vuln:CVE-2014-0160 city:"London"                             # Heartbleed in London
"Apache/2.2.15" country:"FR" has_screenshot:true             # outdated Apache in France
"220" "Anonymous FTP login allowed" country:"JP"             # anon FTP in Japan
```

## Searching by Geographic Filters

> **Note — Common geographic filters.** `country:"<code>"` · `city:"<name>"` · `region:"<name>"` · `geo:"<lat>,<lon>"`.

```text
http country:"US"                                # web servers in the US
ftp country:"DE"                                 # FTP in Germany
telnet city:"London"                             # Telnet in London
rdp region:"California"                           # RDP in California
mysql city:"Paris"                               # MySQL in Paris
"elastic indices" port:9200 city:"Berlin"        # Elasticsearch in Berlin
http geo:"40.7128,-74.0060"                       # near New York City
```

SSH by country: `ssh country:"US"` · `ssh country:"JP"` · `ssh country:"GB"` · `ssh country:"DE"` · `ssh country:"AU"`.

## Finding Plex Media Servers

Common port: HTTP 32400.

```text
"X-Plex-Protocol" port:32400                                       # worldwide
"X-Plex-Protocol" port:32400 country:"US"                          # in the US
"X-Plex-Protocol" port:32400 country:"DE" has_screenshot:true      # with screenshots
"X-Plex-Version" port:32400                                        # by version
```

## Finding Raspberry Pi Devices

Common ports: SSH 22, HTTP 80.

```text
"Raspbian" port:22                               # via SSH
"Raspberry Pi" port:80                            # via HTTP
"Raspbian" port:22 country:"US"                   # in the US
title:"Pi-hole" http.component:"Pi-hole"          # Pi-hole instances
"RFB" "Raspbian" port:5900                         # with VNC
```

## Finding Proxmox Servers

Common port: HTTPS 8006.

```text
"Proxmox" port:8006
"Proxmox" port:8006 country:"US"
"Proxmox" port:8006 has_screenshot:true
title:"Proxmox Virtual Environment"
```

## Finding Web Cameras & Video Streaming

> **Note — Common streaming ports.** MJPEG: 8081, 8082, 8888 · RTSP: 554, 322 · HTTP: 80, 8080.

```text
"MJPEG Server" port:8081                          # MJPEG streams
"Motion JPEG" port:8888                            # motion JPEG
port:554 "rtsp"                                    # RTSP streams
"200 OK" "webcam" NOT "password"                   # webcams with no auth
"IP Webcam Server" http.component:"IP Webcam"      # IP Webcam Android app
title:"Blue Iris" http.favicon.hash:-1616143106    # Blue Iris DVR
```

## Finding IoT Devices

> **Note — Common IoT protocols/ports.** MQTT: 1883, 8883 (TLS) · CoAP: 5683 · ZigBee: 6100 · smart-home hubs: 8080-8090.

```text
port:1883                                          # IoT via MQTT
title:"Home" OR title:"Smart" port:8080             # smart-home hubs
"MQTT" port:1883                                    # open MQTT brokers
product:"Arduino" OR product:"Raspberry Pi" OR product:"ESP"
title:"Home Assistant" port:8123                    # Home Assistant
"SmartThings" port:39500                            # SmartThings hubs
"Philips hue" port:80                               # Philips Hue bridges
"Nest" port:443                                     # Nest devices
"Ring" product:"Ring"                               # Ring doorbells
```

## Finding Industrial Control Systems

> **Important — Common ICS/SCADA protocols.** Modbus: 502 · Siemens S7: 102 · Profinet: 34962-34964 · OPC UA: 4840 · DNP3: 20000 · BACnet: 47808 · EtherNet/IP: 44818.

```text
port:502 "Modbus"
port:102 "Siemens"
"Siemens" OR "Modbus" OR "PLC"
port:44818 "Allen-Bradley"
port:47808 "BACnet"
port:20000 "DNP3"
port:4840 "OPC"
"Schneider Electric" port:502
"GE" "PLC" OR "PACSystems"
```

## Finding Network Attached Storage (NAS)

> **Note — Common NAS ports.** QNAP: 8080, 8443 · Synology: 5000, 5001 · WD MyCloud: 80 · Netgear ReadyNAS: 80, 443.

```text
title:"QNAP" port:8080
"Synology" port:5000
"WD MyCloud" port:80
"NAS" "sharing" has_screenshot:true
title:"FreeNAS" OR title:"TrueNAS"
title:"ReadyNAS"
title:"Buffalo" "NAS"
title:"Drobo"
```

## Finding Database Servers

> **Note — Common DB ports.** MySQL 3306 · PostgreSQL 5432 · MongoDB 27017 · Redis 6379 · Cassandra 9042 · Elasticsearch 9200 · CouchDB 5984 · InfluxDB 8086 · Neo4j 7474.

```text
"MongoDB Server Information" port:27017 -"authentication"   # unprotected MongoDB
"redis_version" port:6379
port:5432 "PostgreSQL"
"elasticsearch" port:9200
"MySQL" port:3306 -"Access denied"
"couchdb" port:5984 "Welcome"
port:9042 "cassandra"
port:8086 "InfluxDB"
port:7474 "neo4j"
port:3306 "MariaDB"
port:1521 "Oracle"
port:1433 "SQL Server"
```

## Finding VPN & Remote Access Services

> **Note — Common remote access ports.** OpenVPN 1194 · WireGuard 51820 · IPSec 500/4500 · RDP 3389 · VNC 5900-5999 · SSH 22 · TeamViewer 5938.

```text
"OpenVPN" port:1194
port:3389 has_screenshot:true
port:5900 "RFB"                                    # VNC
"Citrix" port:1494
"Fortinet" ssl:"Fortinet"
"GlobalProtect" ssl:"Palo Alto"
"Pulse Secure" port:443
"SonicWall" port:443
port:7070 "AnyDesk"
port:5938 "TeamViewer"
port:51820                                          # WireGuard
```

## Finding Printers & Multifunction Devices

> **Note — Common printer ports.** HP/Canon/Xerox: 80, 443, 9100 (JetDirect) · Ricoh: 80, 443, 8080 · IPP: 631.

```text
"HP" port:9100
title:"Canon" port:80
"Xerox" OR "WorkCentre"
"printer" port:80 has_screenshot:true
title:"Brother" "printer"
title:"EPSON" port:80
title:"Ricoh" port:80
title:"Kyocera"
port:631 "IPP"
```

## Finding Game Servers

> **Note — Common game server ports.** Minecraft 25565 · Counter-Strike/ARK 27015 · Rust 28015 · TeamSpeak 9987.

```text
"Minecraft Server" port:25565
product:"Counter-Strike" port:27015
"ARK" port:27015
product:"Rust" port:28015
product:"TeamSpeak" port:9987
"Valheim" port:2456
product:"Garry's Mod"
"7 Days to Die" port:26900
```

## Finding Cloud Services & APIs

> **Note — Common cloud/API ports.** HTTP/HTTPS 80/443 · API gateways 8080/8443 · Docker 2375/2376.

```text
port:2375 product:"Docker"                          # exposed Docker APIs
title:"Kubernetes Dashboard"
"X-Jenkins" http.title:"Dashboard"
http.title:"GitLab"
title:"Grafana"
title:"Kibana"
title:"Prometheus" port:9090
title:"Portainer"
title:"Swagger UI"
"169.254.169.254"                                   # AWS metadata leaks
http.title:"Index of /.git"                         # exposed .git directories
http.title:"Index of" ".env"                        # exposed .env files
```

## Finding Network Infrastructure

> **Note — Common network device ports.** SNMP 161 · SSH 22 · Telnet 23 · BGP 179.

```text
"cisco" product:"Cisco IOS"
"Juniper" product:"Juniper"
product:"MikroTik"
"EdgeOS" OR "Ubiquiti"
title:"pfSense"
title:"OPNsense"
"FortiGate" ssl:"Fortinet"
"SonicWall" port:443
"BIG-IP" product:"BIG-IP"
"NETGEAR" product:"NETGEAR"
"TP-LINK" product:"TP-LINK"
port:161 "public"                                   # SNMP enabled
```

## Advanced Filtering Techniques

```text
ssl:"OpenSSL/1.0" "weak"                            # weak SSL/TLS configs
"Basic realm" port:80                               # exposed info
vuln:CVE-2021-21315
"X-Powered-By: PHP" port:80                          # by response header
header:"X-Custom-Header"                             # custom applications
geo:"40.7128,-74.0060"                              # geographic proximity
ssl.cert.issuer.cn:ssl.cert.subject.cn              # self-signed certs
ssl.cert.expired:true                                # expired certs
http.component:"WordPress" http.component_category:"cms"
```

## Using Shodan CLI for Advanced Queries

```bash
# Install and initialize
pip install shodan
shodan init YOUR_API_KEY

# Basic search
shodan search "apache"

# Export results with specific fields
shodan search "title:Camera" --fields ip_str,port,org,country,html

# Download bulk data
shodan download camera-results "title:Camera"

# Host information lookup
shodan host 8.8.8.8
shodan host --history 8.8.8.8

# Stream real-time Shodan data
shodan stream

# Count results for a query
shodan count "apache"

# Parse downloaded data
shodan parse camera-results.json.gz --fields ip_str,port

# Domain / DNS
shodan domain example.com
shodan dns resolve example.com
shodan dns reverse 8.8.8.8

# Stats with facets
shodan stats --facets country apache

# Convert data format
shodan convert results.json.gz csv
```

## Shodan API Usage (Python)

**Basic search:**
```python
import shodan

api = shodan.Shodan('YOUR_API_KEY')
results = api.search('apache')

for result in results['matches']:
    print(f"IP: {result['ip_str']}")
    print(f"Port: {result['port']}")
    print(f"Org: {result.get('org', 'N/A')}")
    print("---")
```

**Host lookup:**
```python
import shodan

api = shodan.Shodan('YOUR_API_KEY')
host = api.host('8.8.8.8')

print(f"IP: {host['ip_str']}")
print(f"Organization: {host.get('org', 'N/A')}")
print(f"OS: {host.get('os', 'N/A')}")

for item in host['data']:
    print(f"Port: {item['port']}")
    print(f"Banner: {item['data'][:100]}...")
```

**Streaming API:**
```python
import shodan

api = shodan.Shodan('YOUR_API_KEY')
for banner in api.stream.banners():
    print(banner)
```

**Network alerts:**
```python
import shodan

api = shodan.Shodan('YOUR_API_KEY')
alert = api.create_alert('My Network', '192.168.1.0/24')
print(f"Alert ID: {alert['id']}")
```

## Practical Search Strategies

```text
product:"Cisco" "privilege" "escalation"                   # 1. vulnerability chain
"default username is" OR "default password is"             # 2. default installs
"200 OK" after:2024-01-01                                  # 3. recently indexed
"Apache/2.4.49" OR "Apache/2.4.50"                         # 4. known CVEs
"SCADA" OR "HMI" OR "historian"                            # 5. critical infrastructure
org:"Your Company Name"                                    # 6. your org's exposure
ssl.cert.subject.cn:"yourcompany.com" -org:"Your Company"  # 7. shadow IT
title:"Index of /backup"                                   # 8. misconfigured storage
http.title:"phpMyAdmin" OR http.title:"Adminer"            # 9. exposed dev envs
http.title:"admin" http.status:200 -http.title:"login"     # 10. exposed admin panels
```

## Ethical Considerations

> **Important —**
> - **Permission:** always have explicit authorization before attempting any access or testing.
> - **Responsibility:** use findings to improve security and report vulnerabilities responsibly.
> - **Legal compliance:** comply with all relevant regulations (CFAA, GDPR, etc.).
> - **No malicious intent:** never use Shodan for unauthorized access or data theft.

**Pre-search checklist:** authorization confirmed · legitimate security purpose · legal implications reviewed · prepared to disclose responsibly · Shodan ToS understood · findings reported to the right parties.

**Common mistakes to avoid:** over-broad searches (false positives), assuming every result is vulnerable, unauthorized testing, premature public disclosure, assuming ownership of exposed services, ignoring honeypots.

## Responsible Vulnerability Disclosure

1. **Identify** — confirm the vulnerability, document with evidence, note affected systems/versions.
2. **Find contact** — check `/.well-known/security.txt`, the org's site, published VDPs, or whois/reverse DNS.
3. **Report** — send a detailed technical report, allow a reasonable timeline (typically 90 days), do not disclose before a patch, offer to verify the fix.
4. **Document** — keep records of all communications, dates, responses, and patch releases.

| Timeline | Action |
|:--------:|:-------|
| Day 1 | Discover and confirm vulnerability |
| Day 1 | Contact vendor with details |
| Day 30 | Follow up if no response |
| Day 60 | Consider escalation |
| Day 90 | Coordinate public disclosure after patch |

## Resources and References

- [Shodan Official Website](https://www.shodan.io)
- [Shodan CLI Documentation](https://cli.shodan.io)
- [Shodan API Documentation](https://developer.shodan.io)
- [Shodan Query Cheat Sheet](https://cheatsheet.shodan.io)

**Related tools:** Censys, ZoomEye, GreyNoise, BinaryEdge, Shodan Maps.
