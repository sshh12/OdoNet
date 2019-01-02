"""
The OdoNet Node
"""
from collections import defaultdict
import socketserver
import subprocess
import logging
import struct
import queue
import pickle
import time
import os

from odonet import network_util, wifi_util
from odonet import node_config, config
from odonet import events
from odonet import cameras


CUR_DIR = os.path.dirname(__file__)

UPDATE_FN = os.path.join(CUR_DIR, '..', 'odonet-update.zip')


class Node:

    def __init__(self, conf):
        """Create root node from config"""
        self.conf = conf

        # Read network params
        self.my_ip = conf['networking']['this']['ipv4']
        self.my_port = conf['networking']['this']['port']
        self.ping_freq = conf['networking']['this'].get('ping_freq', 6)
        self.timeout = conf['networking']['this'].get('timeout', 10)
        self.my_id = conf['about']['id']
        self.tick_length = conf['about'].get('tick_length', 0.8)
        self.parent_ip = conf['networking']['parent']['ipv4']
        self.parent_port = conf['networking']['parent']['port']

        # Event Backup
        max_events = conf['about'].get('events_backup_size', 500)
        self.saved_events_left = max(0, max_events - len(events.load_events()[1]))

        self.packet_queue = defaultdict(queue.Queue)

        # Create TCP server
        this = self
        class TCPTransceiver(socketserver.BaseRequestHandler):
            def handle(self):
                this._handle_tcp(self)
        self.TCPTransceiver = TCPTransceiver

        # Create devices
        self._init_devices()


    def _init_devices(self):
        """Start up all the devices."""
        self.devices = []

        for device_conf in self.conf['devices']:

            device_type = device_conf['type']
            device_conf['_my_ip'] = self.my_ip

            try:

                if device_type in cameras.CAMERAS:
                    self.devices.append(cameras.CAMERAS[device_type](device_conf))

            except Exception as e:
                logging.error('Failed to init device ({}): {}'.format(device_conf, e))


    def run(self):
        """Start the server"""
        with network_util.create_server(self.my_ip, self.my_port, self.TCPTransceiver) as server:

            logging.info('Starting server...')

            # Tell the server the device has started
            self._send_msg(self.my_id + '-boot')
            self._send_obj(self.conf)

            # Keep track of loops
            ticks = 0

            while True:

                start = time.time()

                # Send out ping
                if ticks % self.ping_freq == 0:
                    self._send_msg(self.my_id + '-tick', timeout=2)

                # Run though all the devices
                for idx, device in enumerate(self.devices):

                    tick_result = device.tick()

                    if tick_result.image is not None:

                        self._send_image(idx, tick_result.image)

                    if tick_result.event is not None:

                        event = tick_result.event
                        event.node = self.my_id
                        event_sent = self._send_obj(event)

                        # Backup event
                        if not event_sent and self.saved_events_left > 0:
                            self.saved_events_left -= 1
                            events.save_event(event, thumb=False, gif=False)

                # Make sure the device isnt ticking too fast
                # to prevent too much traffic and high power consumption
                time_left = max(0, self.tick_length - time.time() + start)
                time.sleep(time_left)

                ticks += 1


    def _handle_tcp(self, tcp):
        """Handle a packet from a child"""
        address, data, decoded = network_util.read_encoded_socket(tcp.request, decode_iif_mine=True)

        logging.info('Routing {} -> @'.format(address))

        # Nodes dont handle data, so send it up the tree until it hits the root
        self._forward_packet(data)

        # See if the child node has data ready for it
        last_node_id = address[0]

        if last_node_id in self.packet_queue and not self.packet_queue[last_node_id].empty():

            tcp.request.sendall(self.packet_queue[last_node_id].get())


    def _handle_root_cmd(self, decoded):
        """Handle a cmd from root"""

        ## ROOT MSG TYPES ##

        if decoded == 'config':
            self._send_obj(self.conf)

        elif decoded == 'reboot':
            node_config.reboot()

        elif decoded == 'reload':
            self._init_devices()

        elif decoded == 'wifisignal':
            quality, strength = self._get_wifi_signal()
            self._send_obj({'wifiquality': '{}/{}'.format(quality, strength)})

        elif type(decoded) == dict and 'networking' in decoded:
            config.set_config(decoded)
            self.conf = decoded

        elif type(decoded) == dict and 'movecam' in decoded:
            camera = self.cameras[decoded['movecam']]
            camera.move(decoded['dir'])

        elif type(decoded) == dict and 'update_zip' in decoded:
            zip_data = decoded['update_zip']
            print(UPDATE_FN)
            with open(UPDATE_FN, 'wb') as update_zip:
                update_zip.write(zip_data)
            subprocess.run(['unzip', '-d', os.path.dirname(UPDATE_FN), '-o', UPDATE_FN])
            os.remove(UPDATE_FN)
            logging.info('Updated!')

        elif type(decoded) == dict and 'shellcmd' in decoded:
            logging.info('> ' + decoded['shellcmd'])
            cmd = decoded['shellcmd'].split(' ')
            try:
                result = subprocess.run(cmd, stdout=subprocess.PIPE)
                self._send_obj({'shelloutput': result.stdout.decode('utf-8')})
            except:
                logging.error('Shell cmd failed')
                self._send_obj({'shelloutput': 'error.'})


    def _forward_packet(self, data, timeout=None, **kwargs):

        if timeout is None:
            timeout = self.timeout

        address, data, decoded = network_util.send_packet(self.my_id,
                                                          self.parent_ip,
                                                          self.parent_port,
                                                          data,
                                                          decode_iif_mine=True,
                                                          timeout=timeout)

        if data is None:
            logging.error('Packet forwarding failed')
            return False

        elif len(data) > 0:
            if len(address) == 1: # This packet is for me
                logging.info('Received ({})'.format(type(decoded)))
                self._handle_root_cmd(decoded)
            else: # Send this packet to the next node in the address
                logging.info('Routing {} -> {}'.format(self.my_id, address[1]))
                self.packet_queue[address[1]].put(data[1:])

        return True


    def _send_msg(self, data, **kwargs):
        """Send text to root"""
        packet = network_util.construct_packet('', network_util.DataType.TEXT, data)
        return self._forward_packet(packet, **kwargs)


    def _send_image(self, cam_id, image_data):
        """Send image to root"""
        id_data = struct.pack('H', cam_id)
        packet = network_util.construct_packet('', network_util.DataType.IMAGE, id_data + image_data)
        return self._forward_packet(packet)


    def _send_obj(self, obj):
        """Send object to root"""
        obj_data = pickle.dumps(obj)
        packet = network_util.construct_packet('', network_util.DataType.PICKLE, obj_data)
        return self._forward_packet(packet)


    def _get_wifi_signal(self):
        """Determine current WiFi signal quality/strength"""
        ssid = self.conf['networking']['parent']['ssid']
        wifi_device = self.conf['networking']['this']['wifi_device']

        scan_results = wifi_util.scan_networks(wifi_device)

        for found_mac in scan_results:
            wifi_network = scan_results[found_mac]
            if wifi_network.get('essid', '') == ssid:
                return (wifi_network['quality'], wifi_network['signal_level'])

        return (-1, -1)
