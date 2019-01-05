
# Setup: Main Server (Root)

> These instructions where written using a laptop with: Python 3.5 (Anaconda), Windows 10, Intel i7, 2.4 GHz WiFi

1. Install [Python 3](https://www.python.org/downloads/) and [pip](https://stackoverflow.com/questions/4750806/how-do-i-install-pip-on-windows)
2. Install dependencies
	* `pip install opencv-python`
	* `pip install numpy`
	* `pip install flask`
	* [ImageMagick](https://imagemagick.org/script/download.php)
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
	* Copy and edit the text below into `root.config.json`
	```javascript
	{
	  "version": 1.0,
	  "security": {
	    "secret": "PUT RANDOM TEXT HERE"
	  },
	  "networking": {
	    "parent": {},
	    "this": {
	      "ipv4": "LOCAL IP",
	      "ssid": "HOME WIFI NETWORK SSID",
	      "wpa_pass": "HOME WIFI PASSWORD",
	      "port": 8200
	    }
	  },
	  "about": {
	    "name": "Root Server",
	    "id": "@"
	  }
	}
5. Run
	* `python root_server.py`
	* Open `http://localhost:5000` in your browser