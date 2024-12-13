from typing_extensions import Annotated
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, status, Body, Depends, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from typing import Annotated

from jose import JWTError, jwt
from passlib.context import CryptContext

from datetime import timedelta, datetime, timezone
from os import path, mkdir, remove, listdir

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
    expire = datetime.now(timezone.utc) + timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDES)
    to_encode.update({"exp": expire})
    print(to_encode)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY_ACCESS, algorithm=ALGORITHM)
    return encoded_jwt, expire

def create_refresh_token(data: dict | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
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

@app.post("/email_exists", response_model=bool)
async def email_exists(
    data: dict = Body(...)
):
    user = getUserByEmail(email=data['email'])
    return bool(user) 


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

@app.post("/change/add", status_code=status.HTTP_200_OK, response_model=bool)
async def add_change(
    current_user: Annotated[User, Depends(get_current_active_user)],
    json_data: dict = Body(...)
):
    if 'objectType' in json_data.keys() and 'objectId' in json_data.keys() and 'changeId' in json_data.keys() and 'operationType' in json_data.keys():
        return addChange(changeId=json_data['changeId'], objectType=json_data['objectType'], operationType=int(json_data['operationType']), objectId=json_data['objectId'])
    return False

@app.get("/change/get/{id}", response_model=dict)
async def get_changes(
    current_user: Annotated[User, Depends(get_current_active_user)],
    id: str
):
    changes = getChangesAfter(changeId=id, userId=current_user.id)
    if changes:
        return {'result': True, 'changes': changes}
    
    return {'result': False}
    

@app.get("/users/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user

@app.post('/users/me/update', response_description="Update user", status_code=status.HTTP_200_OK, response_model=dict)
async def update_user_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
    json_data: dict = Body(...)
):
    update = UpdateUserRequest(**json_data)
    data = update.dump()
    id = data.pop('id')
    
    result, lastUpdate = updateUser(str(current_user.id), data)

    if result:
        return {'result': True, 'dateTime': lastUpdate}
    
    return {'result': False}

@app.delete('/users/me/delete', response_description="Delete user", status_code=status.HTTP_200_OK, response_model=bool)
async def delete_user_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return deleteUser(current_user.id)

@app.get('/users/me/fetchall', response_model=dict)
async def fetch_all(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    books = getUserBooks(current_user.id)
    data = {'books': [], 'recipes': [], 'lastChange': getLastChange()}
    for book in books:
        data['books'].append(str(book.id))
        data['recipes'] += book.recipeIds.copy()

    return data

@app.get('/books/get/{id}', response_model=Book|None)
async def get_book(
    current_user: Annotated[User, Depends(get_current_active_user)],
    id: str
):
    book: Book = getBookById(id)
    if book:
        if str(current_user.id) in book.users:
            return book
        
@app.get('/books/get_users/{id}', response_model=dict|None)
async def get_book_usernames(
    current_user: Annotated[User, Depends(get_current_active_user)],
    id: str
):
    book: Book = getBookById(id)
    if book:
        if str(current_user.id) in book.users and book.access[str(current_user.id)] == 2:
            usernames = {}
            for userId in book.users:
                user = getUserById(userId)
                usernames[userId] = user.name
            return usernames
    

@app.post('/books/update', response_description="Update book", status_code=status.HTTP_200_OK, response_model=dict)
async def update_book(
    current_user: Annotated[User, Depends(get_current_active_user)],
    json_data: dict = Body(...)
):
    update = UpdateBookRequest(**json_data)
    data = update.dump()
    id = data.pop('id')

    book = getBookById(id)

    if book:
        if str(current_user.id) in book.users:
            if book.access[str(current_user.id)] > 1:
                result, lastUpdate = updateBookSet(id, data)
                if result:
                    return {'result': True, 'dateTime': lastUpdate}
    
    return {'result': False}

@app.put('/books/create', response_description="Create book", status_code=status.HTTP_201_CREATED, response_model=dict)
async def create_book(
    current_user: Annotated[User, Depends(get_current_active_user)],
    form_data: Annotated[AddBookRequestForm, Depends()]
):    
    ack, lastUpdate = addBook(
        id=form_data.id,
        name=form_data.name,
        recipeIds=[],
        users=[str(current_user.id)],
        access={str(current_user.id): 2}
    )
    
    return {'result': ack, 'lastUpdate': lastUpdate}

@app.delete('/books/delete', response_description="Delete book", status_code=status.HTTP_200_OK, response_model=bool)
async def delete_book(
    current_user: Annotated[User, Depends(get_current_active_user)],
    id: str = Body(...)
):
    if id != "":
        book = getBookById(id)
        if isinstance(book, Book):
            if str(current_user.id) in book.users and book.access[str(current_user.id)] == 2:
                return deleteBook(id)
    
    return False


@app.get('/recipes/get/{id}', response_model=Recipe|None)
async def get_recipe(
    current_user: Annotated[User, Depends(get_current_active_user)],
    id: str
):
    recipe: Recipe = getRecipeById(id)

    if recipe:
        access = getRecipeUserAccess(userId=current_user.id, recipeId=id)
        if access != None:
            return recipe

@app.post('/recipes/update', response_description="Update recipe", status_code=status.HTTP_200_OK, response_model=dict)
async def update_recipe(
    current_user: Annotated[User, Depends(get_current_active_user)],
    json_data: dict = Body(...)
):
    update = UpdateRecipeRequest(**json_data)
    data = update.dump()
    id = data.pop('id')

    access = getRecipeUserAccess(userId=current_user.id, recipeId=id)
    
    if access != None and access > 0:
        ack, lastUpdate = updateRecipe(id, data)
        if ack:
            return {'result': True, 'dateTime': lastUpdate}
    
    return {'result': False}

@app.put('/recipes/create', response_description="Create recipe", status_code=status.HTTP_201_CREATED, response_model=dict)
async def create_recipe(
    current_user: Annotated[User, Depends(get_current_active_user)],
    form_data: Annotated[AddRecipeRequestForm, Depends()]
):
    book = getBookById(form_data.bookId)

    if book and str(current_user.id) in book.users:
        if book.access[str(current_user.id)] > AccessLevel.READ:
            ack, lastUpdate = addRecipe(id=form_data.id, name=form_data.name)
            
            if ack:
                book.recipeIds.append(str(form_data.id))
                ack, _ = updateBookSet(book.id, {'recipeIds': book.recipeIds})
                return {'result': ack, 'lastUpdate': lastUpdate}
    
    return {'result': False}

@app.delete('/recipes/delete', response_description="Delete recipe", status_code=status.HTTP_200_OK, response_model=bool)
async def recipe(
    current_user: Annotated[User, Depends(get_current_active_user)],
    id: str = Body(...)
):
    if id != "":
        recipe = getRecipeById(id)
        if isinstance(recipe, Recipe):
            access = getRecipeUserAccess(userId=current_user.id, recipeId=id)
            if access != None and access > 1:
                return deleteRecipe(id)
    
    return False

## Images
@app.post("/image/upload", status_code=status.HTTP_200_OK, response_model=bool)
async def uploadFile(
    current_user: Annotated[User, Depends(get_current_active_user)],
    file: UploadFile,
    info: Annotated[ImageInfoForm, Depends()]
):
    if not path.exists("../storage/"):
        mkdir("../storage/")
    
    if not path.exists(f"../storage/{info.recipeId}"):
        mkdir(f"../storage/{info.recipeId}")

    try:
        with open(f"../storage/{info.recipeId}/{info.imageId}", "wb") as out_file:
            content = await file.read()
            out_file.write(content)
        
        return True
    except Exception as e:
        return  False

@app.get("/image/download/{recipeId}/{imageId}", status_code=status.HTTP_200_OK)
async def downloadFile(
    current_user: Annotated[User, Depends(get_current_active_user)],
    recipeId: str,
    imageId: str
):
    if imageId and recipeId:
        imagePath = f"../storage/{recipeId}/{imageId}"
        access = getRecipeUserAccess(userId=current_user.id, recipeId=recipeId)
        if access != None:
            if path.isfile(imagePath):
                return FileResponse(path=imagePath, media_type='application/octet-stream', filename=imageId)

@app.delete("/image/delete", status_code=status.HTTP_200_OK, response_model=bool)
async def deleteFile(
    current_user: Annotated[User, Depends(get_current_active_user)],
    data: dict = Body(...)
):
    if ('recipeId' in data.keys() and 'imageId' in data.keys()):
        recipeId = data['recipeId']
        imageId = data['imageId']

        imagePath = f"../storage/{recipeId}/{imageId}"
        folderPath = f"../storage/{recipeId}"
        access = getRecipeUserAccess(userId=current_user.id, recipeId=recipeId)
        if access != None and access > 0:
            if path.isfile(imagePath):
                remove(imagePath)
                if len(listdir(folderPath)) == 0:
                    remove(folderPath)
                return True
    return False