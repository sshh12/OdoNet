"""
Utilities for OdoNet configs
"""
import hashlib
import json


def load_config(fn):
    """Load config from file"""
    with open(fn, 'r') as json_file:
        conf = json.load(json_file)
        conf['_file'] = fn
    return conf


def set_config(conf):
    """Overwrite the config file with a new config"""
    if '_file' not in conf:
        print('Cant find config file.')
    else:
        with open(conf['_file'], 'w') as json_file:
            json.dump(conf, json_file, indent=4)


def is_same_config(a, b):
    """Are a and b the same config"""
    return repr(a) == repr(b)


def copy(config):
    """Clone the config"""
    return eval(repr(config))


def create_node_config(original_config, node_id, secret):
    """Generate a config for a node with id `node_id`"""
    new_config = copy(original_config)
    new_config['about']['id'] = node_id

    # The name is just for display purposes
    new_config['about']['name'] = "Node " + node_id

    # Make the internal address 10.0.XX.10:82XX where XX is ascii value of node id
    # Children of this node will be given ipv4s 10.0.XX.11-10.0.XX.30
    # This should enure no two nodes accidently set the same ip.
    new_config['networking']['this']['ipv4'] = '10.0.{}.10'.format(ord(node_id))
    new_config['networking']['this']['port'] = 8200 + ord(node_id)

    new_config['networking']['this']['channel'] = 1 + (ord(node_id) % 14)
    new_config['networking']['this']['ssid'] = 'ODONET_' + node_id
    new_config['networking']['this']['wpa_pass'] = _generate_hash(secret, node_id)[:20]

    return new_config


def link_configs(config, parent_config, backup_parents=None):
    """Edit `config` to connect to parent with optional backup parents"""
    if backup_parents is None:
        backup_parents = []

    new_config = copy(config)
    node_parent_net = new_config['networking']['parent']
    parent_net = parent_config['networking']['this']

    # Bind this.parent network config to match parent config
    node_parent_net['ipv4'] = parent_net['ipv4']
    node_parent_net['port'] = parent_net['port']
    node_parent_net['ssid'] = parent_net['ssid']
    node_parent_net['wpa_pass'] = parent_net['wpa_pass']

    # Add backup configs
    new_config['networking']['backup'] = []
    for i, backup_parent_config in enumerate(backup_parents):
        network_params = backup_parent_config['networking']['this']
        new_config['networking']['backup'].append({
            'priority': i,
            'ipv4': network_params['ipv4'],
            'port': network_params['port'],
            'ssid': network_params['ssid'],
            'wpa_pass': network_params['wpa_pass']
        })

    return new_config


def _generate_hash(secret, text):
    """Generate simple hash of secret and text"""
    hash = hashlib.sha256()
    hash.update(bytes(secret, 'ascii'))
    hash.update(bytes(text, 'ascii'))

    return hash.hexdigest()
