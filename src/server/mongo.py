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
        data['lastUpdate'] = datetime.now()
        
        result = users_collection.get_collection().update_one(filter={"_id": ObjectId(id)}, update={'$set': data})
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



def getBookById(id: str) -> Book:
    book = books_collection.find_one_by_id(ObjectId(id))
    if isinstance(book, Book):
        return book
    
def addBook(name: str, recipeUids: list[str], users: list[str], access: dict[str, int]):
    try:
        result = books_collection.save(Book(
            name = name,
            recipeUids=recipeUids,
            users=users,
            access=access,
            lastUpdate=datetime.now()
        ))
        print(result.inserted_id)
        checked_book = getBookById(result.inserted_id)
        print(checked_book)
        return checked_book
    except Exception as e:
        print(e)


def updateBook(id: str, data: dict):
    try:
        data['lastUpdate'] = datetime.now()
        
        result = books_collection.get_collection().update_one(filter={"_id": ObjectId(id)}, update={'$set': data})
        print(result.modified_count)
        return result.modified_count > 0
    except Exception as e:
        print(e)
        return None



def getRecipeById(id: str) -> Recipe:
    recipe = recipes_collection.find_one_by_id(ObjectId(id))
    if isinstance(recipe, Recipe):
        return recipe
    
def addRecipe(name: str):
    try:
        result = recipes_collection.save(Recipe(
            name = name,
            creationDate=datetime.now(),
            lastUpdate=datetime.now()
        ))
        print(result.inserted_id)
        checked_recipe = getRecipeById(result.inserted_id)
        print(checked_recipe)
        return checked_recipe
    except Exception as e:
        print(e)


def updateRecipe(id: str, data: dict):
    try:
        data['lastUpdate'] = datetime.now()
        _data = jsonable_encoder(data)

        result = recipes_collection.get_collection().update_one(filter={"_id": ObjectId(id)}, update={'$set': _data})
        return result.modified_count > 0
    except Exception as e:
        print(e)
        return None


def getRecipeBooks(recipeId: str):
    try:
        books = books_collection.find_by({'recipeUids': {'$elemMatch': {'$eq': str(recipeId)}}})
        return books
    except Exception as e:
        print(e)

def getRecipeUserAccess(userId: str, recipeId: str) -> int|None:
    try:
        books = getRecipeBooks(recipeId)
        for book in books:
            if str(userId) in book.users:
                return book.access[str(userId)]

    except Exception as e:
        print(e)