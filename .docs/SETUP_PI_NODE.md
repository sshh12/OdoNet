# Setup: Raspberry Pi Node
> These instructions were written using the RPi 3 B+ and Raspbian Stretch Lite (4.14
November 2018)
### Setting up only one RPi

#### Setup RPi
**Needed only for WiFi Mesh/Chaining
1. Download [raspbian](https://www.raspberrypi.org/downloads/raspbian/) and [install](https://www.raspberrypi.org/documentation/installation/installing-images/README.md) it
2. Connect the RPi to [WiFi](https://www.raspberrypi.org/documentation/configuration/wireless/wireless-cli.md) and [enable SSH](https://www.raspberrypi.org/documentation/remote-access/ssh/)
3. **Connect a [USB WiFi adapter](https://www.amazon.com/gp/product/B00YI0AIRS/ref=oh_aui_detailpage_o05_s00?ie=UTF8&psc=1) (this should be `wlan1`)
4. **Install WiFi tools
	* `sudo apt-get install dnsmasq hostapd`
	* [More info](https://www.raspberrypi.org/documentation/configuration/wireless/access-point.md). Dont worry about the config files, these will be replaced by OdoNet.
5. I might have missed some dependencies...install as errors arise.

#### Setup OdoNet on RPi

0. Clone OdoNet
	* `cd ~` and `git clone https://github.com/sshh12/OdoNet.git`
1. Install [Python 3](https://www.python.org/downloads/) and [pip](https://stackoverflow.com/questions/4750806/how-do-i-install-pip-on-windows)
2. Install dependencies
	* `pip install opencv-python`
		* Download ML model [MobileNetSSD](https://github.com/chuanqi305/MobileNet-SSD) and place weights and prototxt in `dnn`
	* `pip install numpy`
	* `pip install scikit-image`
	* `pip install scipy`
	* `pip install pyftpdlib`
	* `pip install picamera`
	* `sudo apt-get install fswebcam`
3. Create a config file (examples in `/.examples`)
	* Copy and edit the text below into `pi.config.json` and confirm that `CONFIG_FILE = '/home/pi/OdoNet/pi.config.json'` in `node_server.py`
	* Ensure that you are only editing `"parent": {` and not `"this": {`
	```javascript
	{
	  "version": 1.0,
	  "networking": {
	    "parent": {
	      "ipv4": "ROOT IP",
	      "port": 8200,
	      "ssid": "WIFI NAME/SSID",
	      "wpa_pass": "WIFI PASSWORD"
	    },
	    "this": {
	      "ipv4": "10.0.48.10",
	      "port": 8248,
	      "ssid": "ODONET_0",
	      "wpa_pass": "abcdefghi",
	      "wifi_device": "wlan0",
	      "ap_device": "wlan1",
	      "channel": 5
	    }
	  },
	  "devices": [],
	  "about": {
	    "name": "Unconfigured Node",
	    "id": "0",
	    "type": "pi"
	  }
	}
4. Add Auto start
	* Edit `/etc/rc.local` and add `sudo python3 /home/pi/OdoNet/node_server.py &`
5. First Run
	* `python node_server.py` (This will most likely cause the RPi to automatically restart and reconnect)
	* Open the dashboard at `http://localhost:5000` on the Root computer
	* When `Unconfigured Node (0)` appears click `Configure` and give the node it's ID
		* The ID must be a single letter (`a-zA-Z`)
	* The RPi should automatically reboot
6. Add optional devices
	* Edit `pi.config.json` as described in [devices](https://github.com/sshh12/OdoNet/blob/master/.docs/DEVICES.md)
		* OR click `Config` on the root dashboard when the RPi is connected, edit the config, the click `Reboot`
7. Run
	* The server will automatically start when the RPi boots.

### Setting up more than one RPi

1. Follow steps (RPi Setup **1-5**) and (OdoNet Setup **1-4**) on the first RPi
2. Use a tool like [win32diskimager](https://sourceforge.net/projects/win32diskimager/) to create a `.img` of the unconfigured RPi's SD card
3. Use the same tool to flash this `.img` onto the other RPi's SD cards
4. Power each RPi on ONE AT A TIME and follow  (OdoNet Setup **5-7**)
