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
changes_collection = ChangeRepository(db)

# CHANGES
def addChange(changeId: str, objectType: str, objectId: str) -> None:
    changes_collection.save(
        Change(
            changeId=changeId,
            objectType=objectType,
            objectId=objectId,
            creationDate=datetime.now()
        )
    )

def getChangesAfter(changeId: str, userId: str):
    lastChange: Change = changes_collection.find_one_by({'changeId': changeId})
    newChanges = changes_collection.find_by({'creationDate': {'$gt': lastChange.creationDate}})

    newUserChanges = []

    userBookIds = getUserBooksId(userId)
    
    for change in newChanges:
        print(change.model_dump())
        if change.objectType == 'user':
            if change.objectId == userId:
                newUserChanges.append(change.model_dump())
        elif change.objectType == 'book':
            if change.objectId in userBookIds:
                newUserChanges.append(change.model_dump())
        elif change.objectType == 'recipe':
            print(str(getRecipeBook(change.objectId).id))
            print(userBookIds)
            if str(getRecipeBook(change.objectId).id) in userBookIds:
                print('is in book')
                newUserChanges.append(change.model_dump())
    
    return newUserChanges

def getLastChange():
    sortedChanges = changes_collection.get_collection().find().sort('creationDate', -1)
    for change in sortedChanges:
        return change['changeId']
        

# USER
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
        return result.modified_count > 0, data['lastUpdate']
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

def getUserBooks(id:str):
    books = books_collection.find_by({"users": str(id)})
    return books

def getUserBooksId(id:str):
    books = getUserBooks(id)
    return [str(book.id) for book in books]

# BOOKS
def getBookById(id: str) -> Book:
    book = books_collection.find_one_by_id(ObjectId(id))
    if isinstance(book, Book):
        return book
    
def addBook(name: str, recipeIds: list[str], users: list[str], access: dict[str, int]):
    try:
        result = books_collection.save(Book(
            name = name,
            recipeIds=recipeIds,
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
        return result.modified_count > 0, data['lastUpdate']
    except Exception as e:
        print(e)
        return None

def deleteBook(id: str):
    try:
        books_collection.delete_by_id(ObjectId(id))
        return True

    except Exception as e:
        print(e)
        return False


# RECIPES
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
        return result.modified_count > 0, data['lastUpdate']
    except Exception as e:
        print(e)
        return None


def getRecipeBook(recipeId: str):
    try:
        book = books_collection.find_one_by({'recipeIds': recipeId})
        return book
    except Exception as e:
        print(e)

def getRecipeUserAccess(userId: str, recipeId: str) -> int|None:
    try:
        book = getRecipeBook(recipeId)
        if book:
            if str(userId) in book.users:
                return book.access[str(userId)]

    except Exception as e:
        print(e)

def deleteRecipe(id: str):
    try:
        result = recipes_collection.delete_by_id(ObjectId(id))
        print(result)
        return True

    except Exception as e:
        print(e)
        return False