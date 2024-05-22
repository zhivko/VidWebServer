'''
Created on 12 May 2024

@author: kleme
'''
from _io import StringIO

from redis.client import Redis

import pandas as pd

import pickle

from MyFlask import MyFlask



redis_client = Redis(host='localhost', port=6379, db=0)


def read(whichkey: str):
    #mydictionary_serialized = redis_client.hgetall(whichkey)     # Get the hash back from Redis
    #mydictionary = {key.decode('utf-8'): pd.read_json(StringIO(value.decode('utf-8'))) for key, value in mydictionary_serialized.items()}
    
    obj = redis_client.get(whichkey)
    if obj==None:
        return None
    
    mydictionary = pickle.loads(obj)
    
    return mydictionary

def write(myKey: str, mydictionary):
    #myDictionary_serialized = {key: value.to_json() for key, value in mydictionary.items()}
    #redis_client.hmset(myKey, myDictionary_serialized)
    redis_client.set(myKey, pickle.dumps(mydictionary))

def delete(whichkey: str):
    if not redis_client.exists(whichkey):
        print(f"Key {whichkey} does not exist")
        return

    # Delete the dictionary
    redis_client.delete(whichkey)    