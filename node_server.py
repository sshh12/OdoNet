"""
Run a node

$ python node_server.py
"""
import logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] (%(levelname)s) %(message)s')

from odonet import config, node_config
from odonet import odonet_node


# Ensure this file exists. (Use full path if running from service/rc.local)
# Example configs can be found in /.examples
CONFIG_FILE = 'local-node.config.json'
# CONFIG_FILE = '/home/pi/OdoNet/pi.config.json'


if __name__ == "__main__":

    conf = config.load_config(CONFIG_FILE)

    node_config.configure(conf)
    odonet_node.Node(conf).run()
