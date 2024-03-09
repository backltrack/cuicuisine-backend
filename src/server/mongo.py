from fastapi.encoders import jsonable_encoder
from pymongo import MongoClient
from server.model import *

# LOAD COLLECTIONS

client = MongoClient('localhost', 27017)
db = client['cuicuisine']

users_collection = db['users']
books_collection = db['books']
recipes_collection = db['recipes']

def getUserById(id: str):
    user = users_collection.find_one({'_id': id})
    print(user)
    if user is not None:
        return User(**user)

def getUserByEmail(email: str) -> User:
    user = users_collection.find_one({'email': email})
    print(user)
    if user is not None:
        return User(**user)

def updateUser(id: str, data: dict):
    try:
        #data = User.model_validate(data)
        _data = jsonable_encoder(data)
        result = users_collection.update_one(filter={"_id": id}, update={'$set': _data})
        return result.modified_count > 0
    except Exception as e:
        print(e)
        return None
