from flask import Flask, render_template, send_file, request, jsonify
from datetime import datetime
import logging
import os
import io


from odonet import events


app = Flask('OdoNet',
            static_url_path='',
            static_folder=os.path.join('odonet_webapp', 'static'),
            template_folder=os.path.join('odonet_webapp', 'templates'))

logging.getLogger('werkzeug').setLevel(logging.ERROR)


app.odonet = {}
app.odonet['devices'] = {}
app.odonet['files'] = {}
app.odonet['update'] = {}


def _load_file(fn, res, files, data_type):

    if res not in files and os.path.exists(fn):
        with open(fn, 'rb') as data_file:
            app.odonet['files'][res] = (data_file.read(), data_type)


@app.route('/')
def index():
    return render_template('index.html', **app.odonet)


@app.route('/events')
def get_events():

    all_events = events.load_events()

    devices = set()

    for day, id, score, base_fn, event_name in all_events:

        devices.add(id)

        _load_file(base_fn + '.jpg', event_name + '.jpg', app.odonet['files'], 'image/jpeg')

    devices = sorted(devices)

    return render_template('events.html', events=all_events, date_now=datetime.now(), device_list=devices, **app.odonet)


@app.route('/event/<event_name>')
def view_event(event_name=''):

    base_fn, event = events.load_event(event_name)

    _load_file(base_fn + '.gif', event_name + '.gif', app.odonet['files'], 'image/gif')

    for i, (date, image_data, motion, objects) in enumerate(event.images):
        img_name = '{}_img_{}'.format(event_name, i)
        if img_name not in app.odonet['files']:
            app.odonet['files'][img_name] = (image_data, 'image/jpeg')

    return render_template('event.html', event_name=event_name, event=event, enumerate=enumerate, **app.odonet)



@app.route('/data/<name>', methods=['GET', 'POST'])
def put_data(name=''):
    result = app.handle_web_msg(name, request.get_json())
    if result is None:
        return jsonify({})
    return jsonify(result)


@app.route('/update')
def update_ready():
    updates = app.odonet['update']
    app.odonet['update'] = {}
    return jsonify(updates)


@app.route('/files/<filename>')
def get_file(filename=''):
    if filename in app.odonet['files']:
        data, file_type = app.odonet['files'][filename]
        buffer = io.BytesIO(data)
        return send_file(buffer,
                         attachment_filename=filename,
                         mimetype=file_type,
                         cache_timeout=None)
    else:
        return 'File not found'
