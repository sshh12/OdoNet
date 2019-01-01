"""
The OdoNet Root
"""
from collections import defaultdict
from datetime import datetime
import socketserver
import pickle
import logging
import queue
import time
import json
import re

from odonet import network_util
from odonet import webapp
from odonet import config
from odonet import events


class Node:

    def __init__(self, conf):
        """Create node from config"""
        self.conf = conf

        # Read network params
        self.my_ip = conf['networking']['this']['ipv4']
        self.my_port = conf['networking']['this']['port']
        self.web_ip = conf['networking']['this'].get('web_ipv4', '0.0.0.0')
        self.web_port = conf['networking']['this'].get('web_port', 5000)
        self.secret = conf['security']['secret']

        self.packet_queue = defaultdict(queue.Queue)
        self.routes = {}

        # Create TCP server
        this = self
        class TCPTransceiver(socketserver.BaseRequestHandler):
            def handle(self):
                this._handle_tcp(self)
        self.TCPTransceiver = TCPTransceiver

        # Bind handlers
        self.app = webapp.app
        self.app.handle_web_msg = self._handle_web_server
        self.node_data = self.app.odonet


    def run(self):
        """Start the server"""
        with network_util.create_server(self.my_ip, self.my_port, self.TCPTransceiver) as server:

            # Once the TCP server is running, start the webserver
            self._web_update('page')
            self.app.run(host=self.web_ip, port=self.web_port, debug=False)


    def _handle_web_server(self, name, data):
        """Handle a cmd from the user's browser"""

        ## Client CMD ##

        if name == 'reset':
            self.node_data['devices'] = {}
            self.node_data['files'] = {}
            self.routes = {}
            self._web_update('page')
            return {}

        elif name == 'config':

            node, new_config = data['id'], data['conf']
            old_config = self.node_data['devices'][node]['config']

            if not config.is_same_config(old_config, new_config):
                self._send_obj(node, new_config)

        elif name == 'reboot':

            node = data['id']
            self._send_msg(node, 'reboot')
            self._delete_node(node)
            self._web_update('page')

        elif name == 'reload':

            node = data['id']
            self._send_msg(node, 'reload')
            self._delete_node(node)
            self._web_update('page')

        elif name == 'shell':

            node, cmd = data['id'], data['script']
            if len(cmd) > 0:
                self._send_obj(node, {'shellcmd': cmd})

        elif name == 'route':

            node = data['id']
            route = re.sub(r'[@\-<>\s]', '', data['route'])

            if len(route) == 0 or route[-1] != node or route == self.routes[node]:
                return {'alert': 'Invalid Route'}
            for n in route:
                if n not in self.node_data['devices']:
                    return {'alert': 'Node in route does not exist'}
                elif not self.node_data['devices'][node]['config']:
                    return {'alert': 'Node in route is not ready'}
                elif route.count(n) > 1:
                    return {'alert': 'Duplicate nodes in route'}

            old_config = self.node_data['devices'][node]['config']
            if len(route) == 1:
                parent_config = self.conf
            else:
                parent_config = self.node_data['devices'][route[-2]]['config']

            new_config = config.link_configs(old_config, parent_config)

            if not config.is_same_config(old_config, new_config):
                self._send_obj(node, new_config)

        elif name == 'configure':

            cur_id, new_id = data['id'], data['new_id']
            if new_id is None or cur_id == new_id or len(new_id) != 1 or new_id in self.routes:
                return {'alert': 'Invalid Id'}

            old_config = self.node_data['devices'][cur_id]['config']
            new_config = config.create_node_config(old_config, new_id, self.secret)

            self._send_obj(cur_id, new_config)
            self._send_msg(cur_id, 'reboot')
            self._delete_node(cur_id)
            self._web_update('page')

        elif name == 'move-cam':
            cur_id, cam, dir = data['id'], data['cam'], data['dir']
            self._send_obj(cur_id, {'movecam': cam, 'dir': dir})


    def _handle_tcp(self, tcp):
        """Handle a packet from a child"""
        address, data, decoded = network_util.read_encoded_socket(tcp.request)

        # Ignore malformed packet
        if len(address) == 0:
            logging.error('Packet w/o address')
            return

        origin_node_id = address[-1] # The node the packet started from
        last_node_id = address[0] # The node the packet just came from

        logging.info('Packet from {} ({})'.format(address, type(decoded)))

        # See if child node has data for it
        if last_node_id in self.packet_queue and not self.packet_queue[last_node_id].empty():

            tcp.request.sendall(self.packet_queue[last_node_id].get())

        # Save the route the packet came through
        self.routes[origin_node_id] = address

        # Handle data sent
        self._handle_node_data(address, origin_node_id, decoded)


    def _handle_node_data(self, address, node, decoded):
        """Handle data coming from a node"""

        # Check if this is the first time node in seen
        if node not in self.node_data['devices']:

            self.node_data['devices'][node] = {
                'name': 'New Device',
                'id': node,
                'wifi_quality': None,
                'config': None
            }

            # Ask for its config and signal
            self._send_msg(node, 'config')
            self._send_msg(node, 'wifisignal')

        # Update saved node data
        device = self.node_data['devices'][node]
        device['last_updated'] = datetime.now()
        device['address'] = address
        device['address_str'] = " <-> ".join(['@'] + list(address))

        self._web_update('last_updated', str(device['last_updated']), node)

        ## NODE MSG TYPES ##

        if decoded == 'deleteme':
            self._delete_node(node)

        elif type(decoded) == dict and 'networking' in decoded:
            device['name'] = decoded['about']['name']
            device['config'] = decoded
            device['config_str'] = json.dumps(decoded, indent=3)
            self._web_update('page')

        elif type(decoded) == dict and 'wifiquality' in decoded:
            device['wifi_quality'] = decoded['wifiquality']

        elif type(decoded) == dict and 'shelloutput' in decoded:
            logging.info(decoded['shelloutput'])

        elif type(decoded) == events.Event:
            decoded.node = node
            logging.info('Received Event {}'.format(decoded))
            events.save_event(decoded, node)
            self._web_update('new_event')

        elif type(decoded) == dict and 'current_image' in decoded:

            cam_id, image_data = decoded['cam'], decoded['current_image']

            files_path = 'current_image_{}'.format(cam_id)

            if files_path in device:
                del self.node_data['files'][device[files_path]]
            else:
                self._web_update('page')

            fn = '{}_current_image_{}_{}.jpg'.format(node, cam_id, time.time())
            self.node_data['files'][fn] = (image_data, 'image/jpeg')
            device[files_path] = fn
            self._web_update(files_path, fn, node)


    def _web_update(self, key, value=True, node=None):
        """Tell the webapp something updated"""
        if node is None:
            self.node_data['update'][key] = value
        else:
            node_key = 'node_' + node
            if node_key not in self.node_data['update']:
                self.node_data['update'][node_key] = {}
            self.node_data['update'][node_key][key] = value


    def _delete_node(self, node):
        """
        Delete node from local records.

        Note: If the node is alive it will automatically reconnect.
        """
        del self.node_data['devices'][node]
        del self.routes[node]


    def _send_msg(self, node, data):
        """Send text to node"""
        route = self.routes[node]
        packet = network_util.construct_packet(route, network_util.DataType.TEXT, data)
        self.packet_queue[route[0]].put(packet)


    def _send_obj(self, node, obj):
        """Send object to node"""
        route = self.routes[node]
        obj_data = pickle.dumps(obj)
        packet = network_util.construct_packet(route, network_util.DataType.PICKLE, obj_data)
        self.packet_queue[route[0]].put(packet)
