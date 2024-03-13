from typing_extensions import Annotated, Doc
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, status, Body, Request, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from typing import Annotated, Dict

from jose import JWTError, jwt
from passlib.context import CryptContext

from datetime import timedelta, datetime

# try:
from server.model import *
from server.mongo import *
# except:
#     # for test purpose
#     from model import *
#     from mongo import *



# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY_ACCESS = "b8b24km3big8wx83fz49hswuwrsdzvw7db4c56upjwxvb89hukx342fnh5crnitv"
SECRET_KEY_REFRESH = "ma4sh6puq5cyq7xgw798472pqdyshs2cxo4uj9xjsk62smq4epuyctzw929te735"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDES = 3600
REFRESH_TOKEN_EXPIRE_DAYS = 365



# Instantiate the FastAPI
app = FastAPI()

# Handle exceptions
class InvalidEmailException(Exception):
    pass

class InvalidPasswordException(Exception):
    pass


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    print(exc.detail)
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return JSONResponse(({"error": "unauthorized_client", "error_description": exc.detail}), status_code=exc.status_code)
    else:
        return exc

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(email: str, password: str):
    print(email)
    user = getUserByEmail(email=email)
    if not user:
        raise InvalidEmailException
    if not verify_password(password, user.hashed_password) or user.disabled:
        raise InvalidPasswordException
    return user

def validate_access_token(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY_ACCESS, algorithms=[ALGORITHM])
        id: str = payload.get("sub")
        return id
    except JWTError:
        raise credentials_exception

def validate_refresh_token(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY_REFRESH, algorithms=[ALGORITHM])
        exp: datetime = datetime.fromtimestamp(payload.get("exp"))
        id: str = payload.get("sub")
        return id, exp
    except JWTError:
        raise credentials_exception

# Token gesture
def create_access_token(data: dict | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDES)
    to_encode.update({"exp": expire})
    print(to_encode)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY_ACCESS, algorithm=ALGORITHM)
    return encoded_jwt, expire

def create_refresh_token(data: dict | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    print(to_encode)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY_REFRESH, algorithm=ALGORITHM)
    print(encoded_jwt)
    return encoded_jwt, expire

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        id = validate_access_token(token)
    except JWTError:
        raise credentials_exception
    user = getUserById(id=id)
    print("id=" + str(id))
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# routes
@app.get("/test_connexion", response_model=bool)
async def test_connection():
    return True

@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    try:
        user = authenticate_user(form_data.username, form_data.password)
        
        access_token, access_token_expiration_time = create_access_token(data={"sub": str(user.id)})
        refresh_token, refresh_token_expiration_time = create_refresh_token(data={"sub": str(user.id)})
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"} #, "expires_in": int(access_token_expiration_time.timestamp()), "refresh_token_expires_in": int(refresh_token_expiration_time.timestamp())

    except InvalidEmailException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidPasswordException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.post("/register", response_model=Token)
async def register_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    # if password too weak:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Incorrect password",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
    user = getUserByEmail(email=form_data.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email already exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user = addUser(name="test", email=form_data.username, password=get_password_hash(form_data.password))

        access_token, access_token_expiration_time = create_access_token(data={"sub": str(user.id)})
        refresh_token, refresh_token_expiration_time = create_refresh_token(data={"sub": str(user.id)})
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"} #, "expires_in": int(access_token_expiration_time.timestamp()), "refresh_token_expires_in": int(refresh_token_expiration_time.timestamp())

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.post("/refresh_token", response_model=Token)
async def refresh_access_token(form_data: Annotated[MyOAuth2RefreshRequestForm, Depends()]):
    id, exp = validate_refresh_token(form_data.refresh_token)
    access_token, access_token_expiration_time = create_access_token(data={"sub": id})
    return {"access_token": access_token, "refresh_token": form_data.refresh_token, "token_type": "bearer"} #, "expires_in": int(access_token_expiration_time.timestamp()), "refresh_token_expires_in": int(exp.timestamp())}

@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user

@app.post('/users/me/update', response_description="Update user", status_code=status.HTTP_201_CREATED, response_model=bool)
async def update_user_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_data: dict = Body(...)
):
    updated_user = updateUser(current_user.id, user_data)
    return updated_user is not None

@app.get('/users/me/lastupdate', response_model=datetime|None)
async def read_user_me_last_update(
    current_user: Annotated[User, Depends(get_current_active_user)],
) :
    return current_user.lastUpdate




###################

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="bbd867e7-bb3a-40bf-af02-6d8ed9a1d168")

# # root
# @app.get("/", tags=["Root"])
# async def readRoot():
#     return {"message": "Welcome to this fantastic app!"}


# # Define DB Functions
# ## Users
# @app.post('/add_user', response_description="Create a new user", status_code=status.HTTP_201_CREATED, response_model=User)
# def addUser(user: User = Body(...)):
#     try:
#         _user = jsonable_encoder(user)
#         _newUser = users_collection.insert_one(_user)
#         print(type(_newUser.inserted_id))
#         print(_newUser.inserted_id)
#         _createdUser = users_collection.find_one({"_id": _newUser.inserted_id})
#         return _createdUser
#     except Exception as e:
#         print(e)
#         return None

# @app.post('/update_user', response_description="Update user", status_code=status.HTTP_201_CREATED, response_model=bool)
# def updateUser(user: dict = Body(...)):
#     try:
#         id = user['id']
#         user = User.validate(user)
#         _user = jsonable_encoder(user)
#         _user.pop('_id', None)
#         result = users_collection.update_one(filter={"_id": id}, update={'$set': _user})
#         return result.modified_count > 0
#     except Exception as e:
#         print(e)
#         return None

# @app.get('/get_user/{id}', response_model=User|None)
# def getUser(id: str):
#     user = users_collection.find_one({'firebaseId': id})
#     print(user)
#     if user is not None:
#         return user
    
# @app.get('/get_user_last_update/{id}', response_model=datetime|None)
# def getUserLastUpdate(id: str):
#     user = users_collection.find_one({'firebaseId': id})
#     print(user)
#     if user is not None:
#         print(user['lastUpdate'])
#         return user['lastUpdate']

# @app.get('/user_exists/{id}', response_model=bool)
# def userExists(id: str):
#     user = users_collection.find_one({'firebaseId': id})
#     if user is not None:
#         return True
#     return False

# @app.get('/get_user_books/{id}', response_model=list[Book])
# def getUserBooks(id: str):
#     books = books_collection.find({'users': id})
#     if books is not None:
#         return books
#     return False

# @app.get('/get_user_books_id/{id}', response_model=list[str])
# def getUserBooksId(id: str):
#     books = books_collection.find({'users': id})
#     if books is not None:
#         return [book.id for book in books]
#     return False

# @app.delete('/delete_user/{id}', response_description="Delete user", status_code=status.HTTP_204_NO_CONTENT)
# def deleteUser(id: str):
#     print(id)
#     users_collection.delete_one({'uid': id})

# ## Books
# @app.post('/add_book', response_description="Create a new book", status_code=status.HTTP_201_CREATED, response_model=Book)
# def addBook(book: Book = Body(...)):
#     try:
#         _book = jsonable_encoder(book)
#         _newBook = books_collection.insert_one(_book)
#         _createdBook = books_collection.find_one({"_id": _newBook.inserted_id})
#         return _createdBook
#     except Exception as e:
#         print(e)
#         return None
    
# @app.post('/update_book', response_description="Update book", status_code=status.HTTP_201_CREATED, response_model=bool)
# def updateBook(book: dict = Body(...)):
#     try:
#         id = book['id']
#         book = Book.validate(book)
#         _book = jsonable_encoder(book)
#         _book.pop('_id', None)
#         result = books_collection.update_one(filter={"_id": id}, update={'$set': _book})
#         return result.modified_count > 0
#     except Exception as e:
#         print(e)
#         return None

# @app.get('/get_book/{id}', response_model=Book|None)
# def getBook(id: str):
#     book = books_collection.find_one({'_id': id})
#     print(book)
#     if book is not None:
#         return book
    
# @app.get('/get_book_last_update/{id}', response_model=datetime|None)
# def getBookLastUpdate(id: str):
#     book = books_collection.find_one({'_id': id})
#     print(book)
#     if book is not None:
#         return book['lastUpdate']

# @app.get('/book_exists/{id}', response_model=bool)
# def bookExists(id: str):
#     book = books_collection.find_one({'_id': id})
#     if book is not None:
#         return True
#     return False

# @app.get('/get_book_recipes/{id}', response_model=list[Recipe]|None)
# def getBookRecipes(id: str):
#     book = books_collection.find_one({'_id': id})
#     if book is not None:
#         recipe_uids = book['recipeUids']
#         recipes = []
#         for uid in recipe_uids:
#             recipe = recipes_collection.find_one({'_id': uid})
#             recipes.append(recipe)
#         return recipes

# @app.get('/get_book_recipes_id/{id}', response_model=list[str]|None)
# def getBookRecipesId(id: str):
#     book = books_collection.find_one({'_id': id})
#     if book is not None:
#         recipe_uids = book['recipeUids']
#         return recipe_uids

# @app.delete('/delete_book/{id}', response_description="Delete book", status_code=status.HTTP_204_NO_CONTENT)
# def deleteUser(id: str):
#     print(id)
#     books_collection.delete_one({'_book': id})


# ## Recipes
# @app.post('/add_recipe', response_description="Create a new recipe", status_code=status.HTTP_201_CREATED, response_model=Recipe)
# def addRecipe(recipe: Recipe = Body(...)):
#     try:
#         _recipe = jsonable_encoder(recipe)
#         _newRecipe = recipes_collection.insert_one(_recipe)
#         _createdRecipe = recipes_collection.find_one({"_id": _newRecipe.inserted_id})
#         return _createdRecipe
#     except Exception as e:
#         print(e)
#         return None

# @app.post('/update_recipe', response_description="Update recipe", status_code=status.HTTP_201_CREATED, response_model=bool)
# def updateRecipe(recipe: dict = Body(...)):
#     try:
#         id = recipe['id']
#         recipe = Recipe.validate(recipe)
#         _recipe = jsonable_encoder(recipe)
#         _recipe.pop('_id', None)
#         print(_recipe)
#         print(id)
#         result = recipes_collection.update_one(filter={"_id": id}, update={'$set': _recipe})
#         return result.modified_count > 0
#     except Exception as e:
#         print(e)
#         return None

# @app.get('/get_recipe/{id}', response_model=Recipe|None)
# def getRecipe(id: str):
#     recipe = recipes_collection.find_one({'_id': id})
#     print(recipe)
#     if recipe is not None:
#         return recipe
    
# @app.get('/get_recipe_last_update/{id}', response_model=datetime|None)
# def getRecipeLastUpdate(id: str):
#     recipe = recipes_collection.find_one({'_id': id})
#     print(recipe)
#     if recipe is not None:
#         return recipe['lastUpdate']

# @app.get('/recipe_exists/{id}', response_model=bool)
# def recipeExists(id: str):
#     recipe = recipes_collection.find_one({'_id': id})
#     if recipe is not None:
#         return True
#     return False

# @app.delete('/delete_recipe/{id}', response_description="Delete recipe", status_code=status.HTTP_204_NO_CONTENT)
# def deleteUser(id: str):
#     print(id)
#     recipes_collection.delete_one({'_id': id})