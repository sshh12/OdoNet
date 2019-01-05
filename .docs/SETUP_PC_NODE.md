
# Setup: PC Node

> These instructions where written using a laptop with: Python 3.5 (Anaconda), Windows 10, Intel i7, 2.4 GHz WiFi

1. Install [Python 3](https://www.python.org/downloads/) and [pip](https://stackoverflow.com/questions/4750806/how-do-i-install-pip-on-windows)
2. Install dependencies
	* `pip install opencv-python`
		* Download ML model [MobileNetSSD](https://github.com/chuanqi305/MobileNet-SSD) and place weights and prototxt in `/dnn`
	* `pip install numpy`
	* `pip install scikit-image`
	* `pip install scipy`
	* `pip install pyftpdlib`
3. Find your local ipv4
	* `ipconfig`
	```bash
	Wireless LAN adapter Wi-Fi:

   Connection-specific DNS Suffix  . :
   Link-local IPv6 Address . . . . . : ...
   IPv4 Address. . . . . . . . . . . : 10.0.0.20 <- This one
                                        192.168... <- It could also look like this
   Subnet Mask . . . . . . . . . . . : 255.255.255.0
   Default Gateway . . . . . . . . . : 10.0.0.1
   ```
4. Create a config file (examples in `/.examples`)
	* Copy and edit the text below into `local-node.config.json` and confirm that `CONFIG_FILE = 'local-node.config.json'` in `node_server.py`
	```javascript
	{
	    "devices": [],
	    "version": 1,
	    "networking": {
	        "parent": {
	            "port": 8200,
	            "wpa_pass": "WIFI PASSWORD",
	            "ssid": "WIFI NAME/SSID",
	            "ipv4": "ROOT SERVER IP"
	        },
	        "this": {
	            "ap_device": "-",
	            "port": 8005,
	            "wpa_pass": "WIFI PASSWORD",
	            "ipv4": "LOCAL IP",
	            "wifi_device": "-",
	            "channel": -1,
	            "ssid": "WIFI NAME/SSID"
	        }
	    },
	    "about": {
	        "type": "computer",
	        "id": "0",
	        "name": "PC Node"
	    }
	}
5. First Run
	* `python node_server.py`
	* Open the dashboard at `http://localhost:5000` on the Root computer
	* When `PC Node (0)` appears click `Configure` and give the node it's ID
		* The ID must be a single letter (`a-zA-Z`)
	* Turn off the node (`Ctrl-C`)
6. Add optional devices
	* Edit `local-node.config.json` as described in [devices](https://github.com/sshh12/OdoNet/blob/master/.docs/DEVICES.md)
7. Run
	* `python node_server.py`