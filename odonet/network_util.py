"""
Networking Utilities
"""
from contextlib import contextmanager
import socketserver
import threading
import logging
import socket
import struct

from enum import Enum
import pickle
import time
import json
import io


class DataType(Enum):
    """Packet Types"""
    TEXT = 1
    IMAGE = 2
    JSON = 3
    PICKLE = 4


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """A special TCP server that supports threading"""
    pass


@contextmanager
def create_server(hostname, port, handler):
    """
    Create a TCP server on a seperate thread

    > with create_server('127.0.0.1', 80, handler) as server:
    >     do_stuff()
    """
    try:

        server = ThreadedTCPServer((hostname, port), handler)

        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        logging.info('TCP started on {}:{}'.format(hostname, port))

        yield server

        server.shutdown()
        server.server_close()

    except OSError as e:

        # This will occur if the this`-`ipv4` is set to an ip that connot be
        # binded to, which will occur if your using the default generated config
        # on a device that does not have 2 wifi adapters (one for connecting
        # to the node parent and the other for children to connect to)

        logging.error('Failed to init TCP server on {}:{}'.format(hostname, port))
        logging.warning('No nodes will be able to connect to this node.')

        yield None


def construct_packet(address, data_type, msg):
    """Build a packet"""
    if type(msg) == bytes:
        data = msg
    else:
        data = bytes(msg, 'ascii')

    packet = bytearray()

    packet.extend(bytes(address + '=', 'ascii'))
    packet.extend(struct.pack('IH', len(data), data_type.value))

    packet.extend(data)

    return packet


def read_encoded_socket(sock, reader_id='', decode_iif_mine=False):
    """Read a packet from `sock`"""
    data = bytearray(sock.recv(20))

    if len(data) == 0:
        return '', b'', None

    # [Address ? bytes]=[Size 4 bytes][DataType 2 bytes][Data ? bytes]
    content_index = data.index(b'=')
    packet_size, data_type = struct.unpack('IH', data[content_index + 1:content_index + 7])
    header_size = content_index + 6 + 1
    bytes_left = packet_size + header_size - len(data)

    # Keep reading until the entire packet is read
    while bytes_left > 0:
        buff = sock.recv(bytes_left)
        data.extend(buff)
        bytes_left -= len(buff)

    if packet_size + header_size == len(data):
        logging.info('{} bytes recieved'.format(len(data)))
    else:
        logging.error('Incomplete packet recieved {}/{}'.format(packet_size + header_size, len(data)))

    address = str(data[:content_index], 'ascii')

    data_type = DataType(data_type)

    ## Decode Data ##

    if decode_iif_mine and (len(address) > 1 or reader_id != address): # Dont read if not my packet
        decoded = None
    elif data_type == DataType.TEXT:
        decoded = str(data[header_size:], 'ascii')
    elif data_type == DataType.IMAGE:
        id = struct.unpack('H', data[header_size:header_size+2])[0]
        image_data = bytes(data[header_size+2:])
        decoded = {'current_image': image_data, 'cam': id}
    elif data_type == DataType.JSON:
        decoded = json.loads(data[header_size:])
    elif data_type == DataType.PICKLE:
        decoded = pickle.loads(data[header_size:])
    else:
        decoded = data

    return address, data, decoded


def send_packet(from_node, hostname, port, data, decode_iif_mine=False, timeout=60):
    """Send a packet to a server"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)

    try:
        sock.connect((hostname, port))

        sock.sendall(bytes(from_node, 'ascii') + data)
        socket_results = read_encoded_socket(sock, decode_iif_mine)

    except Exception as e:
        logging.error('Send packet failed: {}'.format(e))
        socket_results = None, None, None

    finally:
        sock.close()

    return socket_results
