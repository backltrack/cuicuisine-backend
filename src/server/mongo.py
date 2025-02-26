from fastapi.encoders import jsonable_encoder
from pymongo import MongoClient
from server.model import *
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from dotenv import load_dotenv
from os import getenv

load_dotenv()

# LOAD COLLECTIONS

client = MongoClient(getenv("MONGO_ALIAS"), int(getenv("MONGO_PORT")))
db = client['cuicuisine']

users_collection = UserRepository(db)
books_collection = BookRepository(db)
recipes_collection = RecipeRepository(db)
changes_collection = ChangeRepository(db)
recoveries_collection = RecoveryRepository(db)

# CHANGES
def addChange(changeId: str, objectType: str, operationType: int, objectId: str) -> bool:
    if operationType == OperationType.DELETE:
        previous_changes = changes_collection.find_by({"objectId": objectId})
        for change in previous_changes:
            result = changes_collection.delete_by_id(change.id)
            if not True:
                return False

    result = changes_collection.save(
        Change(
            changeId=changeId,
            objectType=objectType,
            operationType=operationType,
            objectId=objectId,
            creationDate=datetime.now(timezone.utc)
        )
    )
    return True

def getChangesAfter(changeId: str, userId: str):
    lastChange: Change = changes_collection.find_one_by({'changeId': changeId})
    newChanges = changes_collection.find_by({'creationDate': {'$gt': lastChange.creationDate}})

    newUserChanges = []

    userBookIds = getUserBooksId(userId)
    
    for change in newChanges:
        if change.objectType == 'user':
            if change.objectId == userId:
                newUserChanges.append(change.model_dump())
        elif change.objectType == 'book':
            if change.objectId in userBookIds:
                newUserChanges.append(change.model_dump())
        elif change.objectType == 'recipe':
            if str(getRecipeBook(change.objectId).id) in userBookIds:
                newUserChanges.append(change.model_dump())
    
    return newUserChanges

def getLastUserChangeId(userId: str) -> str|None:
    userBookIds = getUserBooksId(userId)
    sortedChanges = changes_collection.get_collection().find().sort('creationDate', -1)

    for _change in sortedChanges:
        change = Change.model_validate(_change)
        if change.objectType == 'user':
            if change.objectId == userId:
                return change.changeId
        elif change.objectType == 'book':
            if change.objectId in userBookIds:
                return change.changeId
        elif change.objectType == 'recipe':
            if str(getRecipeBook(change.objectId).id) in userBookIds:
                return change.changeId
        
# RECOVERIES
def addRecoveryRequest(email: str, code: str):
    result = recoveries_collection.save(Recovery(
        email=email,
        code=code,
        expiration_date=datetime.today() + timedelta(minutes=15)
    ))
    return True

def checkRecoveryCode(email: str, code: str) -> Result:
    recovery = recoveries_collection.find_one_by(query={'email': email, 'code': code})

    if not recovery:
        return Result(result=False, reason="Wrong code")
    if datetime.today() > recovery.expiration_date:
        return Result(result=False, reason="Code expired")
    return Result(result=True)

def removeAllRecoveriesForEmail(email: str):
    result = recoveries_collection.get_collection().delete_many(filter={"email": email})
    return True

# USER
def getUserById(id: str) -> DbUser|None:
    user = users_collection.find_one_by_id(ObjectId(id))

    if isinstance(user, DbUser):
        return user

def getUserByEmail(email: str) -> DbUser:
    user = users_collection.find_one_by({'email': email})
    
    if isinstance(user, DbUser):
        return user

def updateUser(id: str, data: dict):
    try:
        data['lastUpdate'] = datetime.now(timezone.utc)
        
        result = users_collection.get_collection().update_one(filter={"_id": ObjectId(id)}, update={'$set': data})
        return result.modified_count > 0, data['lastUpdate']
    except Exception as e:
        print(e)
        return None

def updateUserPassword(id: str, password: str) -> bool:
    result = updateUser(id, {"hashed_password": password})
    return result and result[0]


def addUser(name: str, email: str, password: str) -> User:
    try:
        result = users_collection.save(DbUser(
            name=name,
            email=email,
            hashed_password=password,
            lastUpdate=datetime.now(timezone.utc)
        ))
        checked_user = getUserById(result.inserted_id)
        return checked_user
    except Exception as e:
        print(e)

def deleteUser(id: str) -> bool:
    try:
        # get books
        books = getUserBooks(id)
        # search for books that only belong to this user
        for book in books:
            if len(book.users) == 1:
                deleteBook(book.id)
        # delete user
        result = users_collection.delete_by_id(ObjectId(id))
        return True
    except Exception as e:
        print(e)
        return False

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
    
def addBook(id: ObjectId, name: str, recipeIds: list[str], users: list[str], access: dict[str, int]):
    currentTime = datetime.now(timezone.utc)
    try:
        result = books_collection.save(Book(
            id = id,
            name = name,
            recipeIds=recipeIds,
            users=users,
            access=access,
            lastUpdate=currentTime
        ))
        return True, currentTime
    except Exception as e:
        print(e)
        return False, currentTime


def updateBook(id: str, data: dict):
    try:
        result = books_collection.get_collection().update_one(filter={"_id": ObjectId(id)}, update=data)
        books_collection.get_collection().update_one(filter={"_id": ObjectId(id)}, update={'$set': {'lastUpdate': datetime.now(timezone.utc)}})
        return True, data['lastUpdate']
    except Exception as e:
        print(e)
        return False, ''
    
def updateBookSet(id: str, data: dict):
    return updateBook(id, {'$set': data})

def updateBookPull(id: str, data: dict):
    return updateBook(id, {'$pull': data})

def deleteBook(id: str):
    try:
        book = getBookById(id)
        for recipeId in book.recipeIds:
            recipe = getRecipeById(recipeId)
            if (isinstance(recipe, Recipe)):
                recipes_collection.delete_by_id(ObjectId(recipeId))
        result = books_collection.delete_by_id(ObjectId(id))
        return True

    except Exception as e:
        print(e)
        return False


# RECIPES
def getRecipeById(id: str) -> Recipe|None:
    try:
        recipe = recipes_collection.find_one_by_id(ObjectId(id))
    except Exception as e:
        print(e)

    if isinstance(recipe, Recipe):
        return recipe
    
def addRecipe(id: ObjectId, name: str):
    currentTime = datetime.now(timezone.utc)
    try:
        result = recipes_collection.save(Recipe(
            id = id,
            name = name,
            creationDate=currentTime,
            lastUpdate=currentTime
        ))
        return True, currentTime
    except Exception as e:
        print(e)
        return False, currentTime


def updateRecipe(id: str, data: dict):
    try:
        dateNow = datetime.now(timezone.utc)
        result = recipes_collection.get_collection().update_one(filter={"_id": ObjectId(id)}, update={'$set': jsonable_encoder(data)})
        recipes_collection.get_collection().update_one(filter={"_id": ObjectId(id)}, update={'$set': {'lastUpdate': dateNow}})
        return True, dateNow
    except Exception as e:
        print(e)
        return False, ''


def getRecipeBook(recipeId: str):
    try:
        book = books_collection.find_one_by({'recipeIds': recipeId})
        return book
    except Exception as e:
        print(e)

def getRecipeUserAccess(userId: str, recipeId: str) -> int|None:
    book = getRecipeBook(recipeId)
    if book:
        if str(userId) in book.users:
            return book.access[str(userId)]

def deleteRecipe(id: str):
    try:
        book = getRecipeBook(id)
        if book:
            updateBookPull(book.id, {'recipeIds': id})
        result = recipes_collection.delete_by_id(ObjectId(id))
        return True

    except Exception as e:
        print(e)
        return False