"""
Run the root server

$ python root_server.py
"""
import logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] (%(levelname)s) %(message)s')

from odonet import config
from odonet import odonet_root


# Ensure this file exists.
# Example configs can be found in /.examples
CONFIG_FILE = 'root.config.json'


if __name__ == "__main__":

    conf = config.load_config(CONFIG_FILE)
    odonet_root.Node(conf).run()
