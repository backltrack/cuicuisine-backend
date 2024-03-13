from fastapi.encoders import jsonable_encoder
from pymongo import MongoClient
from server.model import *
from datetime import datetime
from bson import ObjectId

# LOAD COLLECTIONS

client = MongoClient('localhost', 27017)
db = client['cuicuisine']

users_collection = UserRepository(db)
books_collection = BookRepository(db)
recipes_collection = RecipeRepository(db)

def getUserById(id: str) -> DbUser:
    user = users_collection.find_one_by_id(ObjectId(id))

    if isinstance(user, DbUser):
        return user

def getUserByEmail(email: str) -> DbUser:
    user = users_collection.find_one_by({'email': email})
    
    if isinstance(user, DbUser):
        return user

def updateUser(id: str, data: dict):
    try:
        #data = User.model_validate(data)
        _data = jsonable_encoder(data)
        result = users_collection.get_collection.update_one(filter={"_id": id}, update={'$set': _data})
        return result.modified_count > 0
    except Exception as e:
        print(e)
        return None

def addUser(name: str, email: str, password: str) -> User:
    try:
        result = users_collection.save(DbUser(
            name=name,
            email=email,
            hashed_password=password,
            lastUpdate=datetime.now()
        ))
        print(result.inserted_id)
        checked_user = getUserById(result.inserted_id)
        print(checked_user)
        return checked_user
    except Exception as e:
        print(e)
