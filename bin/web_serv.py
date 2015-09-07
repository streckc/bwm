#!/usr/bin/env python3

from flask import Flask, request, Response, send_from_directory
from datetime import date, timedelta, datetime
import os
import re
import bwdb
import json

app = Flask(__name__)


@app.route('/', methods=['GET'])
def main_page():
    global html_path, parameters
    header = ''
    footer = ''


    page = read_html_include('header')
    page += read_html_include('main_page')
    page += read_html_include('footer')
    return page


@app.route('/hosts/<identifier>', methods=['GET'])
@app.route('/hosts', methods=['GET'])
def get_hosts(identifier='', count=50):
    global database_path
    db = bwdb.DB(db=database_path)
    if re.match('^[0-9]+$', identifier):
        hosts = db.get_host_objs(host_id=int(identifier), count=count)
    elif re.match('^[0-9]{1,3}\.[0-9\.]{5,11}$', identifier):
        hosts = db.get_host_objs(addr=identifier, count=count)
    elif re.match('^[0-9a-z_\-\.]+$', identifier):
        hosts = db.get_host_objs(name=identifier, count=count)
    else:
        hosts = db.get_host_objs(count=count)
    return Response(json.dumps(hosts),  mimetype='application/json')


@app.route('/bw', methods=['POST', 'GET'])
def get_bandwidth():
    global database_path
    db = bwdb.DB(db=database_path)

    if request.method == 'GET':
        params = request.args
    else:
        params = request.form

    start = params.get('start_date', '')
    end = params.get('end_date', '')
    host_id = params.get('host_id', -1)
    scope = params.get('scope', 'auto')
    if scope == 'auto':
        scope = get_scope(start, end)

    bandwidth = db.get_bandwidth_objs(host_id=host_id, start=start, end=end, scope=scope)
    data = {'scope': scope, 'host_id': host_id, 'start': start, 'end': end, 'data': bandwidth}
    return Response(json.dumps(data),  mimetype='application/json')


@app.route('/report/top/<int:count>', methods=['POST'])
def get_top_host_report(count=10):
    global database_path
    db = bwdb.DB(db=database_path)
    start = ''
    end = ''

    if request.form.get('start_date'):
        start = request.form.get('start_date')
    if request.form.get('end_date'):
        end = request.form.get('end_date')

    scope = get_scope(start, end)
    hosts = db.get_host_objs_by_bw(start=start, end=end, count=count, scope=scope)

    return Response(json.dumps(hosts),  mimetype='application/json')


@app.route('/report/summary', methods=['POST'])
def get_summary_report():
    global database_path
    db = bwdb.DB(db=database_path)
    start = ''
    end = ''

    if request.form.get('start_date'):
        start = request.form.get('start_date')
    if request.form.get('end_date'):
        end = request.form.get('end_date')

    scope = get_scope(start, end)
    hosts = db.get_data_summary(start=start, end=end, scope=scope)

    return Response(json.dumps(hosts),  mimetype='application/json')


@app.route('/img/<filename>', methods=['GET'])
def display_image(filename=''):
    global html_path
    image_path = os.path.join(html_path,'img')
    return send_from_directory(image_path, filename)


@app.route('/css/<filename>', methods=['GET'])
def display_css(filename=''):
    global html_path
    css_path = os.path.join(html_path,'css')
    return send_from_directory(css_path, filename)


@app.route('/js/<path:path>', methods=['GET'])
def display_js(path=''):
    global html_path
    js_path = os.path.join(html_path,'js')
    return send_from_directory(js_path, path)


@app.errorhandler(404)
def error404(error):
    return 'xxx '+str(error)


def read_html_include(name):
    global html_path, variables
    content = ''
    update_variables()
    with open(os.path.join(html_path, name+'.inc.html'), 'r') as infile:
        content = infile.read()
    for key in variables:
        content = content.replace(key, variables[key])
    return content


def get_html_path(glob):
    global html_path
    file_path = get_file_path(html_path, glob)
    return file_path.replace(html_path, '').replace('\\', '/')


def get_file_path(path, glob):
    for (root, dirs, files) in os.walk(path):
        for filename in sorted(files, reverse=True):
            if re.match(glob, filename):
                return os.path.join(root, filename)
    return ''


def get_scope(start, end):
    global hour_min_day, minute_min_day
    scope = ''

    start_date = datetime.strptime(minute_min_day, '%Y-%m-%d')
    end_date = datetime.now() + timedelta(days=1)

    if start:
        start_date = datetime.strptime(start, '%Y-%m-%d')
    if end:
        end_date = datetime.strptime(end, '%Y-%m-%d')

    diff = end_date - start_date
    if diff.days > 4*7 or start < hour_min_day:
        scope = 'day'
    elif diff.days > 1*7 or start < minute_min_day:
        scope = 'hour'
    else:
        scope = 'minute'

    return scope


def init_globals():
    global script_path, html_path, database_path, variables, day_min_day, hour_min_day, minute_min_day
    script_path = os.path.dirname(os.path.realpath(__file__))
    html_path = os.path.realpath(os.path.join(script_path, '..', 'html'))
    database_path = os.path.realpath(os.path.join(script_path, 'net_mon.db'))
    variables = {'__JQ_JS_PATH__': get_html_path('jq.*.min.js'),
                 '__JQUI_JS_PATH__': get_html_path('jquery-ui.min.js'),
                 '__JQUI_CSS_PATH__': get_html_path('jquery-ui.min.css'),
                 '__VIS_JS_PATH__': get_html_path('vis.*.min.js'),
                 '__VIS_CSS_PATH__': get_html_path('vis.*.min.css')}
    update_variables()

    db = bwdb.DB(db=database_path)
    day_min_day = db.get_min_full_day(table='day')
    hour_min_day = db.get_min_full_day(table='hour')
    minute_min_day = db.get_min_full_day(table='minute')


def update_variables():
    global variables
    variables['__YESTERDAY__'] = (date.today() - timedelta(1)).strftime('%Y-%m-%d')
    variables['__TODAY__'] = date.today().strftime('%Y-%m-%d')
    variables['__TOMORROW__'] = (date.today() + timedelta(1)).strftime('%Y-%m-%d')
  

if __name__ == "__main__":
    init_globals()
    app.run(host='', port=8123, debug=True)

