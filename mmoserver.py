from deps.bottle import route, run, template, static_file
from pymongo import MongoClient
from bson import ObjectId
import threading
import io
import pprint
import json

@route('/resources/<filename:path>')
def send_static(filename):
    print(filename)
    return static_file(filename, root='resources')

@route('/hello/<name>')
def index(name):
    return template('<b>Hello {{name}}</b>!', name=name)

@route('/wordlist')
def wordlist():
    db = get_mmo_db()
    entries = db.entries.find()

    out = io.StringIO()
    
    for e in entries[:10]:
        print(e)
        print(f'<li><a href="/entry/{str(e["_id"])}">{e["definition"]}</a></li>', file=out)
        
    return out.getvalue()

@route('/entry/<id>')
def index(id):
    db = get_mmo_db()
    entries = db.entries
    entry_id = ObjectId(id)
    entry = entries.find_one({"_id": entry_id})
    body = entry['definition']
    print(body)
    return template('<pre>{{body}}</pre>', body=body)

def get_mmo_db():
    return get_mongo_client().mmo

# The pymongo docs say:
# "Create the MongoClient" once for each process, and reuse it for all
# operations. It is a common mistake to create a new client for each
# request, which is very inefficient."
# 
# Source: https://pymongo.readthedocs.io/en/stable/faq.html#how-does-connection-pooling-work-in-pymongo
#
# This implements our shared mongo client, but in such a way that the
# client in only created on first use (to allow for tests that don't use
# mongo etc)
mongo_client = None
mongo_client_lock = threading.Lock()
def get_mongo_client():
    global mongo_client
    with mongo_client_lock:
        if not mongo_client:
            mongo_client = MongoClient('localhost', 27000)
    return mongo_client

if __name__ == "__main__":
    run(host='localhost', port=8080)

