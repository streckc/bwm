#!/usr/bin/env python3

from bottle import get, post, request, response, run, static_file, error
from datetime import date, timedelta
import os
import re
import json
import bwdb


@get('/')
def main_page():
    global html_path, parameters
    header = ''
    footer = ''


    page = read_html_include('header')
    page += read_html_include('main_page')
    page += read_html_include('footer')
    return page


@get('/hosts/<host_id:int>')
@get('/hosts/<name:re:[0-9a-z_\-\.]+>')
@get('/hosts/<addr:re:[0-9]{1,3}\.[0-9\.]{5,11}>')
@get('/hosts')
def get_hosts(host_id=-1, addr='', name='', count=50):
    global db
    if host_id >= 0:
        hosts = db.get_host_objs(host_id=host_id, count=count)
    elif addr != '':
        hosts = db.get_host_objs(addr=addr, count=count)
    elif name != '':
        hosts = db.get_host_objs(name=name, count=count)
    else:
        hosts = db.get_host_objs(count=count)
    response.content_type = 'application/json'
    return json.dumps(hosts)


@post('/bw')
def get_bandwidth():
    global db
    #print(request.forms.get('xx'))
    host_id_param = request.forms.get('host_id')
    host_id = -1
    if host_id_param:
        host_id = host_id_param
    bandwidth = db.get_bandwidth_objs(host_id=host_id)
    response.content_type = 'application/json'
    return json.dumps(bandwidth)


@get('/img/<filename>')
def display_image(filename=''):
    global html_path
    image_path = os.path.join(html_path,'img')
    return static_file(filename, root=image_path)


@get('/js/<path:path>')
def display_image(path=''):
    global html_path
    js_path = os.path.join(html_path,'js')
    return static_file(path, root=js_path)


@error(404)
def error405(error):
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


def init_globals():
    global script_path, html_path, database_path, db, variables
    script_path = os.path.dirname(os.path.realpath(__file__))
    html_path = os.path.realpath(os.path.join(script_path, '..', 'html'))
    database_path = os.path.realpath(os.path.join(script_path, 'net_mon.db'))
    db = bwdb.DB(db=database_path)
    variables = {'__JQ_JS_PATH__': get_html_path('jq.*.min.js'),
                 '__VIS_JS_PATH__': get_html_path('vis.*.min.js'),
                 '__VIS_CSS_PATH__': get_html_path('vis.*.min.css')}
    update_variables()

def update_variables():
    global variables
    variables['__YESTERDAY__'] = (date.today() - timedelta(1)).strftime('%Y-%m-%d')
    variables['__TODAY__'] = date.today().strftime('%Y-%m-%d')
    variables['__TOMORROW__'] = (date.today() + timedelta(1)).strftime('%Y-%m-%d')
  

if __name__ == "__main__":
    init_globals()
    run(host='', port=8123, debug=True)

