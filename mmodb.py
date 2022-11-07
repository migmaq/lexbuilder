from pymongo import MongoClient, ReturnDocument
import threading
from collections import defaultdict
import sys
import config

def get_mmo_db():
    """Returns an instance of the MMO mongo DB.
    The connection is created on demand, and is shared by all callers
    of get_mmo_db() in this process (as is supported by mongodb).  This
    style also supports multiple simultaneous mongo db operations."""
    return get_mongo_client().mmo

def create_empty_mmo_db(i_realize_that_this_will_nuke_the_working_mmo_db=False):
    """Creates an empty version of the mmo db"""
    assert i_realize_that_this_will_nuke_the_working_mmo_db == True
    db = get_mmo_db()
    db.entries.drop()

    init_persistent_sequence ('entry_id', initial_value=10000)
    
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
            mongo_client = MongoClient(config.mongo_host, config.mongo_port)
    return mongo_client


# While we are implementing these sequences in the mongo-recommended
# way, I can't find any documentation that this will have proper
# behaviour on contention (looks like conflicting updates will
# end up being resolved by 'last update wins').
#
# We are using 'majority' write concern - so perhaps we have no worries?
#
# Anyway, I am wrapping this in a python lock as well (and we are mostly
# using a single python process) for added confidence.
sequence_locks = defaultdict(threading.Lock)

def sequence_update(collection,
                    sequence_name,
                    update_op):
    with sequence_locks[sequence_name]:
        counter = collection.find_one_and_update(
            {"_id": sequence_name},
            update_op,
            return_document=ReturnDocument.AFTER)
        return counter['next']

def init_persistent_sequence (sequence_name,
                              initial_value=0):
    with sequence_locks[sequence_name]:
        get_mmo_db().sequences.replace_one(
            {"_id": sequence_name},
            {"next": initial_value},
            upsert=True)

def next_id_in_persistent_sequence (sequence_name):
    with sequence_locks[sequence_name]:
        counter = get_mmo_db().sequences.find_one_and_update(
            {"_id": sequence_name},
            {"$inc": {"next": 1}},
            return_document=ReturnDocument.AFTER)
        return counter['next']

def next_entry_id():
    return next_id_in_persistent_sequence('entry_id')    
    
def test_persistent_sequence(seq_begin=10000):
    db = get_mmo_db()
    init_persistent_sequence('test_counter', seq_begin)
    for i in range(1, 10000):
        next_id = next_id_in_persistent_sequence('test_counter')
        print(next_id)
        assert next_id==seq_begin+i

if __name__ == "__main__":
    if sys.argv[1:] == ['test_persistent_sequence']:
        test_persistent_sequence()
    elif sys.argv[1:] == ['create_empty_mmo_db', '--i_realize_that_this_will_nuke_the_working_mmo_db']:
        create_empty_mmo_db(i_realize_that_this_will_nuke_the_working_mmo_db=True)
        print('DB initialized')
    else:
        print('use the source, luke')
    
