
from datetime import datetime
import subprocess
import threading
import requests
import tempfile
import logging
import queue
import time
import cv2
import os
import io

from odonet import events


CUR_DIR = os.path.dirname(__file__)

DNN_MODEL = (
    os.path.join(CUR_DIR, '..', 'dnn', 'MobileNetSSD.prototxt.txt'),
    os.path.join(CUR_DIR, '..', 'dnn', 'MobileNetSSD.caffemodel')
)

SMALL_DIM = (300, 300)


try:
    import cv2
    import numpy as np
    mobile_net = cv2.dnn.readNetFromCaffe(*DNN_MODEL)
except ImportError:
    logging.warning('OpenCV/Numpy not found.')

try:
    from skimage.measure import compare_ssim
    from skimage.measure import compare_nrmse
except ImportError:
    logging.warning('Skimage not found.')

try:
    from picamera import PiCamera
    from picamera.array import PiRGBArray
except ImportError:
    logging.warning('PiCamera lib not found.')

try:
    from pyftpdlib.authorizers import DummyAuthorizer
    from pyftpdlib.handlers import FTPHandler
    from pyftpdlib.servers import FTPServer
except ImportError:
    logging.warning('FTP lib not found.')


class BaseCamera:

    def __init__(self, cam_conf):

        self.width = cam_conf.get('width', 1920)
        self.height = cam_conf.get('height', 1080)
        self.mode = cam_conf.get('mode', 'monitor')
        self.monitor_rate = cam_conf.get('rate', 15 * 60)
        self.use_ai = cam_conf.get('use_ai', True)
        self.motion_threshold = cam_conf.get('motion_threshold', 100)

        self.cur_event = None
        self.cur_event_images = []
        self.time_last_sent = 0
        self.last_img = None
        self.last_img_small = None
        self.reset_prev_frame = False
        self.avg_motion = 0


    def capture(self):
        return None


    def capture_array(self):
        img_data = self.capture()
        if img_data:
            ary = np.fromstring(img_data, np.uint8)
            return cv2.imdecode(ary, cv2.IMREAD_COLOR)
        return None


    def ready(self):
        return True


    def move(self, dir):
        logging.error('This camera does not support movement.')


    def tick(self):

        if not self.ready():
            return None, None

        if self.mode == 'stream':
            return self.stream_tick()

        elif self.mode == 'monitor':
            return self.monitor_tick()


    def stream_tick(self):

        time_now = time.time()

        self.time_last_sent = time_now
        image_data = self.capture()

        return image_data, None


    def monitor_tick(self):

        time_now = time.time()
        date_now = datetime.now()

        send_image, send_event = None, None

        if self.last_img is None or self.reset_prev_frame:

            self.last_img = self.capture_array()
            self.last_img_small = cv2.resize(self.last_img, SMALL_DIM)
            self.reset_prev_frame = False

        else:

            cur_img = self.capture_array()
            if cur_img is None:
                return None, None
            cur_img_small = cv2.resize(cur_img, SMALL_DIM)

            motion = compute_motion_score(self.last_img_small, cur_img_small)
            self.avg_motion = self.avg_motion * 0.95 + motion * 0.05
            print(self.avg_motion)

            if motion > self.motion_threshold:
                if self.cur_event is None:
                    self.cur_event = events.Event()
                    self.cur_event_images.append((date_now, self.last_img, self.last_img_small, motion))
                self.cur_event_images.append((date_now, cur_img, cur_img_small, motion))

            self.last_img = cur_img
            self.last_img_small = cur_img_small

        if self.cur_event is not None and (self.cur_event.age >= 120 or len(self.cur_event) >= 16):
            for date, image_array, small_array, motion in self.cur_event_images:
                if self.use_ai:
                    detected = detect_objs(small_array, output_shape=image_array.shape)
                else:
                    detected = []
                self.cur_event.add_image(image_array, date=date, objects=detected, motion=motion)
            events.score(self.cur_event)
            logging.info('Sending Event {}'.format(self.cur_event))
            if len(self.cur_event) > 0:
                send_event = self.cur_event
            self.cur_event = None
            self.cur_event_images = []

        if time_now - self.time_last_sent >= self.monitor_rate:

            self.time_last_sent = time_now
            send_image = self.capture()

        return send_image, send_event


class RaspberryPiCamera(BaseCamera):

    def __init__(self, cam_conf):
        super().__init__(cam_conf)
        self.camera = PiCamera()
        self.camera.resolution = (self.width, self.height)
        self.camera.start_preview()
        self.capture()
        logging.info('Found PiCamera')
        time.sleep(1)


    def capture_array(self):
        pixels = PiRGBArray(self.camera)
        self.camera.capture(pixels, format="bgr")
        return pixels.array

    def capture(self):
        buffer = io.BytesIO()
        self.camera.capture(buffer, format="jpeg")
        return buffer.getvalue()


class USBWebcam(BaseCamera):

    def __init__(self, cam_conf):
        super().__init__(cam_conf)
        self.temp_dir = tempfile.gettempdir()
        self.temp_img = os.path.join(self.temp_dir, 'usbcap.jpg')
        self.cmd = ['fswebcam -r {}x{} --no-banner {}'.format(self.width, self.height, self.temp_img)]
        self.capture()
        logging.info('Found USB Camera')
        time.sleep(1)


    def _take_pic(self):
        subprocess.call(self.cmd, shell=True)


    def capture_array(self):
        self._take_pic()
        return cv2.imread(self.temp_img)


    def capture(self):
        self._take_pic()
        with open(self.temp_img, 'rb') as image_file:
            return image_file.read()


class Insteon_75790(BaseCamera):

    MOVES = {
        'up': 0,
        'down': 2,
        'left': 6,
        'right': 4
    }

    def __init__(self, cam_conf):
        super().__init__(cam_conf)
        self.cam_ip = cam_conf['ip']
        self.cam_port = cam_conf.get('port', 80)
        self.cam_user = cam_conf.get('username', 'admin')
        self.cam_pass = cam_conf.get('password', '')
        self.move_dist = cam_conf.get('movement', 1)
        self.capture()
        logging.info('Found Insteon 75790 Camera')


    def _send_request(self, url_data):
        return requests.get('http://{}:{}/{}user={}&pwd={}'.format(self.cam_ip, self.cam_port, url_data, self.cam_user, self.cam_pass))


    def move(self, dir):
        move_id = InsteonIPCam.MOVES[dir]
        self._send_request('decoder_control.cgi?command={}&'.format(move_id))
        time.sleep(self.move_dist)
        self._send_request('decoder_control.cgi?command={}&'.format(1))
        self.reset_prev_frame = True


    def capture(self):
        req = self._send_request('snapshot.cgi?')
        return req.content


class RTSPCamera(BaseCamera):

    def __init__(self, cam_conf):
        super().__init__(cam_conf)
        self.cam_ip = cam_conf['ip']
        self.cam_port = cam_conf.get('port', 554)
        self.cam_user = cam_conf.get('username', 'admin')
        self.cam_pass = cam_conf.get('password', 'password')
        self.cam_url = cam_conf.get('password', 'videoMain')
        self.url = 'rtsp://{}:{}@{}:{}/{}'.format(self.cam_user,
                                                         self.cam_pass,
                                                         self.cam_ip,
                                                         self.cam_port,
                                                         self.cam_url)
        self.cap = cv2.VideoCapture(self.url)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 5);
        self.capture()
        logging.info('Found RTSP Camera')


    def ready(self):
        return self.cap.isOpened()


    def capture_array(self):
        ret, frame = self.cap.read()
        if ret:
            return frame
        return None


    def capture(self):
        _, img_data = cv2.imencode('.jpg', self.capture_array())
        return img_data.tostring()


class FTPCamera(BaseCamera):

    def __init__(self, cam_conf):
        super().__init__(cam_conf)
        self.my_ip = cam_conf['my_ip']
        self.ftp_ip = cam_conf.get('ip', self.my_ip)
        self.ftp_port = cam_conf.get('port', 21)
        self.ftp_user = cam_conf.get('username', 'user')
        self.ftp_pass = cam_conf.get('password', '12345')
        self.buffer_size = cam_conf.get('buffer_size', 3)

        self.auth = DummyAuthorizer()
        self.auth.add_user(self.ftp_user, self.ftp_pass, os.getcwd(), perm='elradfmwMT')

        self.img_buffer = queue.Queue(self.buffer_size)

        this = self
        class CamHandler(FTPHandler):

            def on_file_received(ftp_self, fn):

                if not fn.endswith('.jpg'):
                    return

                with open(fn, 'rb') as img_file:
                    this.img_buffer.put(img_file.read())

                os.remove(fn)

            def on_incomplete_file_received(self, fn):

                os.remove(fn)

        self.handler = CamHandler
        self.handler.authorizer = self.auth

        self.server = FTPServer((self.ftp_ip, self.ftp_port), self.handler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

        logging.info('Found FTP Camera')


    def ready(self):
        return not self.img_buffer.empty()


    def capture(self):
        if not self.img_buffer.empty():
            return self.img_buffer.get()
        return None


CAMERAS = {
    'picamera': RaspberryPiCamera,
    'usbwebcam': USBWebcam,
    'insteon-75790': Insteon_75790,
    'rtspcamera': RTSPCamera,
    'ftpcamera': FTPCamera
}


def compute_motion_score(prev_img, now_img):

    rmse = compare_nrmse(prev_img, now_img)
    ssim = compare_ssim(prev_img, now_img, multichannel=True)

    score = (rmse + (1 - ssim) * 1.5) / .45 * 100

    print('MOTION {} {} {}'.format(rmse, ssim, score))

    return score


def detect_objs(image, min_confid=0.6, objects=None, output_shape=None):

    all_classes = [
        "background", "aeroplane", "bicycle", "bird", "boat",
        "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
        "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
        "sofa", "train", "tvmonitor"
    ]

    if objects is None:
        objects = ['bus', 'motorbike', 'car', 'cat', 'cow', 'person', 'horse', 'bird', 'sheep']

    if output_shape is None:
        output_shape = image.shape

    (h, w) = output_shape[:2]

    blob = cv2.dnn.blobFromImage(image, 0.007843, SMALL_DIM, 127.5)

    mobile_net.setInput(blob)
    detections = mobile_net.forward()

    detected = []

    for i in np.arange(0, detections.shape[2]):

        confid = detections[0, 0, i, 2]
        class_idx = int(detections[0, 0, i, 1])

        if 0 > class_idx or class_idx >= len(all_classes):
            continue

        obj_name = all_classes[class_idx]

        if confid > min_confid and obj_name in objects:

            bbox = (detections[0, 0, i, 3:7] * np.array([w, h, w, h])).astype("int")

            detected.append(events.EventObject(obj_name, bbox=bbox))

    return detected
