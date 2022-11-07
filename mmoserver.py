from deps.bottle import route, run, template, static_file
from bson import ObjectId
import pprint
import json
import wordlist
import mmodb

@route('/resources/<filename:path>')
def send_static(filename):
    print(filename)
    return static_file(filename, root='resources')

@route('/hello/<name>')
def index(name):
    return template('<b>Hello {{name}}</b>!', name=name)

@route('/wordlist')
def wordlist_():
    return wordlist.wordlist()

@route('/entry/<id>')
def index(id):
    db = mmodb.get_mmo_db()
    entries = db.entries
    entry_id = ObjectId(id)
    entry = entries.find_one({"_id": entry_id})
    body = entry['definition']
    print(body)
    return template('<pre>{{body}}</pre>', body=body)


if __name__ == "__main__":
    run(host='localhost', port=8080, reloader=True)

