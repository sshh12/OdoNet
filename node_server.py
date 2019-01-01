
from odonet import config, piconfig
from odonet import odonet_node

import logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] (%(levelname)s) %(message)s')


CONFIG_FILE = 'local-node.config.json'


if __name__ == "__main__":

    conf = config.load_config(CONFIG_FILE)
    conf['FILE'] = CONFIG_FILE

    piconfig.configure(conf)
    odonet_node.Node(conf).run()
