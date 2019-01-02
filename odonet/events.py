
from datetime import datetime
import subprocess
import tempfile
import logging
import pickle
import os


try:
    import cv2
    import numpy as np
except ImportError:
    logging.warning('OpenCV/Numpy not found.')


TIME_FORMAT = '%Y-%m-%d-%H-%M-%S'

THUMB_SIZE = (300, 170)

CUR_DIR = os.path.dirname(__file__)

EVENTS_PATH = os.path.join(CUR_DIR, '..', 'events')


class Event:

    def __init__(self):

        self.init_date = datetime.now()
        self.images = []
        self.node = '-'
        self.score = -1


    def add_image(self, image, objects=None, date=None, motion=0):

        if date is None:
            date = datetime.now()

        if objects is None:
            objects = []

        _, data = cv2.imencode('.jpg', image)
        image_data = data.tostring()

        self.images.append((date, image_data, motion, objects))


    @property
    def age(self):
        return (datetime.now() - self.init_date).seconds


    def __len__(self):
        return len(self.images)


    def __str__(self):
        return '<Event images={} node={} time=({})>'.format(len(self.images), self.node, self.init_date)


class EventObject:

    def __init__(self, name, bbox=None):
        self.name = name
        self.bbox = bbox

    def __str__(self):
        return '<EventObject name={}>'.format(self.name)


def score(event):

    img_scores = 0
    score = 0

    for _, _, motion, objects in event.images:
        img_scores += motion
        for object in objects:
            img_scores += 50
            if object.name == 'person':
                img_scores += 5000

    score += img_scores / len(event.images)

    event.score = score

    return score


def save_event(event, thumb=True, gif=True):

    dir = os.path.join(EVENTS_PATH, event.node)
    os.makedirs(dir, exist_ok=True)

    date_formatted = event.init_date.strftime(TIME_FORMAT)
    name = '{}_{}_{}_{}'.format(date_formatted, event.node, int(event.score), len(event))
    fn = os.path.join(dir, name)

    with open(fn + '.event.pkl', 'wb') as event_file:
        pickle.dump(event, event_file)

    if thumb and len(event.images) > 0:
        _create_thumb(event, fn + '.event.jpg')

    if gif and len(event.images) > 0:
        _create_gif(event, fn + '.event.gif')


def _create_thumb(event, output_name):
    img_data = max(event.images, key=lambda i: i[2])[1]
    img_data = np.fromstring(img_data, np.uint8)
    img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
    img = cv2.resize(img, THUMB_SIZE)
    cv2.imwrite(output_name, img)


def _create_gif(event, output_name, frame_delay=60):

    tmp_dir = tempfile.gettempdir()
    tmp_fns = []

    for i, (date, image_data, motion, objects) in enumerate(event.images):
        fn = os.path.join(tmp_dir, 'tmp_gif_{}.jpg'.format(i))
        tmp_fns.append(fn)
        with open(fn, 'wb') as f:
            f.write(image_data)

    cmd = ['magick', 'convert', '-delay', '10', '-loop', '0']
    for tmp_fn in tmp_fns:
        cmd.extend(['-delay', str(frame_delay), tmp_fn])
    cmd += [output_name]

    subprocess.Popen(cmd)


def load_event(event_name):

    day, node, score, length = event_name.split('_')

    base_fn = os.path.join(EVENTS_PATH, node, event_name)

    with open(base_fn + '.pkl', 'rb') as event_file:
        return base_fn, pickle.load(event_file)


def load_events(limit=1000):

    events = []
    events_size = 0

    for node in os.listdir(EVENTS_PATH):

        if len(node) != 1:
            continue

        dir = os.path.join(EVENTS_PATH, node)

        for fn in os.listdir(dir):

            if not fn.endswith('.pkl'):
                continue

            day, id, score, length = fn.split('_')
            event_name = fn.replace('.pkl', '')

            date = datetime.strptime(day, TIME_FORMAT)

            base_fn = os.path.join(EVENTS_PATH, node, event_name)

            events_size += os.path.getsize(base_fn + '.pkl')

            events.append((date, id, score, base_fn, event_name))

    events.sort(reverse=True)
    events = events[:limit]

    return events_size, events
