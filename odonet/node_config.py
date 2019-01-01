"""
Configure the node itself.

Write system config files, etc...
"""
import subprocess
import logging
import time
import os


WPA_FILE = "/etc/wpa_supplicant/wpa_supplicant.conf"
WPA_CONFIG = """
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US

network={{
        ssid="{}"
        psk="{}"
}}
"""

DNSMASQ_FILE = "/etc/dhcpcd.conf"
DNSMASQ_CONFIG = """
# Auto Generated Config

# Allow users of this group to interact with dhcpcd via the control socket.
#controlgroup wheel

# Inform the DHCP server of our hostname for DDNS.
hostname

# Use the hardware address of the interface for the Client ID.
clientid
# or
# Use the same DUID + IAID as set in DHCPv6 for DHCPv4 ClientID as per RFC4361.
# Some non-RFC compliant DHCP servers do not reply with this set.
# In this case, comment out duid and enable clientid above.
#duid

# Persist interface configuration when dhcpcd exits.
persistent

# Rapid commit support.
# Safe to enable by default because it requires the equivalent option set
# on the server to actually work.
option rapid_commit

# A list of options to request from the DHCP server.
option domain_name_servers, domain_name, domain_search, host_name
option classless_static_routes
# Most distributions have NTP support.
option ntp_servers
# Respect the network MTU. This is applied to DHCP routes.
option interface_mtu

# A ServerID is required by RFC2131.
require dhcp_server_identifier

# Generate Stable Private IPv6 Addresses instead of hardware based ones
slaac private

# Example static IP configuration:
#interface eth0
#static ip_address=192.168.0.10/24
#static ip6_address=fd51:42f8:caae:d92e::ff/64
#static routers=192.168.0.1
#static domain_name_servers=192.168.0.1 8.8.8.8 fd51:42f8:caae:d92e::1

# It is possible to fall back to a static IP if DHCP fails:
# define static profile
#profile static_eth0
#static ip_address=192.168.1.23/24
#static routers=192.168.1.1
#static domain_name_servers=192.168.1.1

# fallback to static profile on eth0
#interface eth0
#fallback static_eth0

interface {}
static ip_address={}/24
nohook wpa_supplicant
"""

DNSMASQ_IP_FILE = "/etc/dnsmasq.conf"
DNSMASQ_IP_CONFIG = """
interface={}
  dhcp-range={},{},255.255.255.0,24h
"""

HOSTAPD_FILE = "/etc/hostapd/hostapd.conf"
HOSTAPD_CONFIG = """
interface={}
hw_mode=g
channel={}
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
ssid={}
wpa_passphrase={}
"""


def configure(conf):
    """Configure the device to work with the given config"""

    # Only have code for editing raspberry pi
    if conf['about']['type'] == 'pi':

        logging.info('Configuring Pi...')

        if _configure_rasbian_wifi(conf) or _configure_rasbian_ap(conf):
            logging.warning('Reboot required...')
            time.sleep(1)
            reboot()

    else:
        logging.warning('No configuration will be installed since this is not a Pi.')

    # wait a little before starting OdoNet server
    time.sleep(8)


def _read(fn):
    """Get contents of file"""
    with open(fn, 'r') as f:
        return f.read()


def _write(fn, text):
    """Write text to file"""
    with open(fn, 'w') as f:
        f.write(text)


def reboot():
    """Reboot system"""
    subprocess.Popen(['reboot'], shell=True)


def _configure_rasbian_wifi(conf):
    """Write WiFi config"""
    ssid = conf['networking']['parent']['ssid']
    passw = conf['networking']['parent']['wpa_pass']

    new_config = WPA_CONFIG.format(ssid, passw)
    old_config = _read(WPA_FILE)

    if new_config != old_config:
        logging.info('New WIFI config detected.')
        _write(WPA_FILE, new_config)
        return True

    return False


def _configure_rasbian_ap(conf):
    """Write WiFi access-point config"""
    ap_device = conf['networking']['this']['ap_device']
    my_ip = conf['networking']['this']['ipv4']
    my_ssid = conf['networking']['this']['ssid']
    my_passw = conf['networking']['this']['wpa_pass']
    channel = conf['networking']['this']['channel']

    # Make DHCP assign ips between .11-.30
    ip_prefix = '.'.join(my_ip.split('.')[:-1])
    ip_start = ip_prefix + '.11'
    ip_end = ip_prefix + '.30'

    new_dns_config = DNSMASQ_CONFIG.format(ap_device, my_ip)
    new_dns_ip_config = DNSMASQ_IP_CONFIG.format(ap_device, ip_start, ip_end)
    new_hostapd_config = HOSTAPD_CONFIG.format(ap_device, channel, my_ssid, my_passw)

    old_dns_config = _read(DNSMASQ_FILE)
    old_dns_ip_config = _read(DNSMASQ_IP_FILE)
    old_hostapd_config = _read(HOSTAPD_FILE)

    # Check if any configs differ
    diff = False
    diff |= new_dns_config != old_dns_config
    diff |= new_dns_ip_config != old_dns_ip_config
    diff |= new_hostapd_config != old_hostapd_config

    if diff:
        logging.info('New AP config detected.')
        _write(DNSMASQ_FILE, new_dns_config)
        _write(DNSMASQ_IP_FILE, new_dns_ip_config)
        _write(HOSTAPD_FILE, new_hostapd_config)
        return True

    return False
