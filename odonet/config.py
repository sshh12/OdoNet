import hashlib
import json


def load_config(fn):

    with open(fn, 'r') as json_file:
        return json.load(json_file)


def set_config(conf):

    if 'FILE' not in conf:
        print('Cant find config file.')
    else:
        with open(conf['FILE'], 'w') as json_file:
            json.dump(conf, json_file, indent=4)


def is_same_config(a, b):
    return repr(a) == repr(b)


def copy(config):
    return eval(repr(config))


def create_node_config(original_config, node_id, secret):

    new_config = copy(original_config)

    new_config['about']['name'] = "Node " + node_id
    new_config['about']['id'] = node_id
    new_config['networking']['this']['ipv4'] = '10.0.{}.10'.format(ord(node_id))
    new_config['networking']['this']['port'] = 8200 + ord(node_id)
    new_config['networking']['this']['ssid'] = 'ODONET_' + node_id
    new_config['networking']['this']['wpa_pass'] = _generate_hash(secret, node_id)[:16]

    return new_config


def link_configs(config, parent_config):

    new_config = copy(config)
    node_parent_net = new_config['networking']['parent']
    parent_net = parent_config['networking']['this']

    node_parent_net['ipv4'] = parent_net['ipv4']
    node_parent_net['port'] = parent_net['port']
    node_parent_net['ssid'] = parent_net['ssid']
    node_parent_net['wpa_pass'] = parent_net['wpa_pass']

    return new_config


def _generate_hash(secret, text):

    hash = hashlib.sha256()
    hash.update(bytes(secret, 'ascii'))
    hash.update(bytes(text, 'ascii'))

    return hash.hexdigest()
