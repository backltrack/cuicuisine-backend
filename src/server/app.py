from pymongo import MongoClient
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, status, Body, Request

try:
    from server.model import *
except:
    from model import *

# LOAD COLLECTIONS

client = MongoClient('localhost', 27017)
db = client['family-recipes']

users_collection = db['users']
books_collection = db['books']
recipes_collection = db['recipes']

# Instantiate the FastAPI
app = FastAPI()


# root
@app.get("/", tags=["Root"])
async def readRoot():
    return {"message": "Welcome to this fantastic app!"}


# Define DB Functions
## Users
@app.post('/add_user', response_description="Create a new user", status_code=status.HTTP_201_CREATED, response_model=User)
def addUser(user: User = Body(...)):
    try:
        _user = jsonable_encoder(user)
        _newUser = users_collection.insert_one(_user)
        print(type(_newUser.inserted_id))
        print(_newUser.inserted_id)
        _createdUser = users_collection.find_one({"_id": _newUser.inserted_id})
        return _createdUser
    except Exception as e:
        print(e)
        return None

@app.post('/update_user', response_description="Update user", status_code=status.HTTP_201_CREATED, response_model=bool)
def updateUser(user: dict = Body(...)):
    try:
        id = user['id']
        user = User.validate(user)
        _user = jsonable_encoder(user)
        _user.pop('_id', None)
        result = users_collection.update_one(filter={"_id": id}, update={'$set': _user})
        return result.modified_count > 0
    except Exception as e:
        print(e)
        return None

@app.get('/get_user/{id}', response_model=User|None)
def getUser(id: str):
    user = users_collection.find_one({'firebaseId': id})
    print(user)
    if user is not None:
        return user
    
@app.get('/get_user_last_update/{id}', response_model=datetime|None)
def getUserLastUpdate(id: str):
    user = users_collection.find_one({'firebaseId': id})
    print(user)
    if user is not None:
        return user['lastUpdate']

@app.get('/user_exists/{id}', response_model=bool)
def userExists(id: str):
    user = users_collection.find_one({'firebaseId': id})
    if user is not None:
        return True
    return False

@app.get('/get_user_books/{id}', response_model=list[Book])
def getUserBooks(id: str):
    books = books_collection.find({'users': id})
    if books is not None:
        return books
    return False

@app.get('/get_user_books_id/{id}', response_model=list[str])
def getUserBooksId(id: str):
    books = books_collection.find({'users': id})
    if books is not None:
        return [book.id for book in books]
    return False

@app.delete('/delete_user/{id}', response_description="Delete user", status_code=status.HTTP_204_NO_CONTENT)
def deleteUser(id: str):
    print(id)
    users_collection.delete_one({'firebaseId': id})

## Books
@app.post('/add_book', response_description="Create a new book", status_code=status.HTTP_201_CREATED, response_model=Book)
def addBook(book: Book = Body(...)):
    try:
        _book = jsonable_encoder(book)
        _newBook = books_collection.insert_one(_book)
        _createdBook = books_collection.find_one({"_id": _newBook.inserted_id})
        return _createdBook
    except Exception as e:
        print(e)
        return None
    
@app.post('/update_book', response_description="Update book", status_code=status.HTTP_201_CREATED, response_model=bool)
def updateBook(book: dict = Body(...)):
    try:
        id = book['id']
        book = Book.validate(book)
        _book = jsonable_encoder(book)
        _book.pop('_id', None)
        result = books_collection.update_one(filter={"_id": id}, update={'$set': _book})
        return result.modified_count > 0
    except Exception as e:
        print(e)
        return None

@app.get('/get_book/{id}', response_model=Book|None)
def getBook(id: str):
    book = books_collection.find_one({'_id': id})
    print(book)
    if book is not None:
        return book
    
@app.get('/get_book_last_update/{id}', response_model=datetime|None)
def getBookLastUpdate(id: str):
    book = books_collection.find_one({'_id': id})
    print(book)
    if book is not None:
        return book['lastUpdate']

@app.get('/book_exists/{id}', response_model=bool)
def bookExists(id: str):
    book = books_collection.find_one({'_id': id})
    if book is not None:
        return True
    return False

@app.get('/get_book_recipes/{id}', response_model=list[Recipe]|None)
def getBookRecipes(id: str):
    book = books_collection.find_one({'_id': id})
    if book is not None:
        recipe_uids = book['recipeUids']
        recipes = []
        for uid in recipe_uids:
            recipe = recipes_collection.find_one({'_id': uid})
            recipes.append(recipe)
        return recipes

@app.get('/get_book_recipes_id/{id}', response_model=list[str]|None)
def getBookRecipesId(id: str):
    book = books_collection.find_one({'_id': id})
    if book is not None:
        recipe_uids = book['recipeUids']
        return recipe_uids

@app.delete('/delete_book/{id}', response_description="Delete book", status_code=status.HTTP_204_NO_CONTENT)
def deleteUser(id: str):
    print(id)
    books_collection.delete_one({'_book': id})


## Recipes
@app.post('/add_recipe', response_description="Create a new recipe", status_code=status.HTTP_201_CREATED, response_model=Recipe)
def addRecipe(recipe: Recipe = Body(...)):
    try:
        _recipe = jsonable_encoder(recipe)
        _newRecipe = recipes_collection.insert_one(_recipe)
        _createdRecipe = recipes_collection.find_one({"_id": _newRecipe.inserted_id})
        return _createdRecipe
    except Exception as e:
        print(e)
        return None

@app.post('/update_recipe', response_description="Update recipe", status_code=status.HTTP_201_CREATED, response_model=bool)
def updateRecipe(recipe: dict = Body(...)):
    try:
        id = recipe['id']
        recipe = Recipe.validate(recipe)
        _recipe = jsonable_encoder(recipe)
        _recipe.pop('_id', None)
        print(_recipe)
        print(id)
        result = recipes_collection.update_one(filter={"_id": id}, update={'$set': _recipe})
        return result.modified_count > 0
    except Exception as e:
        print(e)
        return None

@app.get('/get_recipe/{id}', response_model=Recipe|None)
def getRecipe(id: str):
    recipe = recipes_collection.find_one({'_id': id})
    print(recipe)
    if recipe is not None:
        return recipe
    
@app.get('/get_recipe_last_update/{id}', response_model=datetime|None)
def getRecipeLastUpdate(id: str):
    recipe = recipes_collection.find_one({'_id': id})
    print(recipe)
    if recipe is not None:
        return recipe['lastUpdate']

@app.get('/recipe_exists/{id}', response_model=bool)
def recipeExists(id: str):
    recipe = recipes_collection.find_one({'_id': id})
    if recipe is not None:
        return True
    return False

@app.delete('/delete_recipe/{id}', response_description="Delete recipe", status_code=status.HTTP_204_NO_CONTENT)
def deleteUser(id: str):
    print(id)
    recipes_collection.delete_one({'_id': id})