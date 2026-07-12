import logging
from fastapi.staticfiles import StaticFiles
from typing_extensions import Annotated
from fastapi import FastAPI, status, Body, Depends, UploadFile, Request
from contextlib import asynccontextmanager
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from typing import Annotated

from jose import JWTError, jwt
from passlib.context import CryptContext

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64
import random, string

from server.email_sender import GmailSender

from datetime import timedelta, datetime, timezone
from os import path, mkdir, remove, listdir, rmdir, getenv

from server.model import *
from server.mongo import *
from server.migration_functions import apply_migrations

from server.debugLog import log

load_dotenv()

log.info("Starting Cuicuisine server")
log.info(f"Log level set to: {logging.getLevelName(log.logger.level)}")

# Set via the SECRET_KEY_ACCESS / SECRET_KEY_REFRESH env vars.
# To generate a value: openssl rand -hex 32
SECRET_KEY_ACCESS = getenv("SECRET_KEY_ACCESS")
SECRET_KEY_REFRESH = getenv("SECRET_KEY_REFRESH")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDES = 3600
REFRESH_TOKEN_EXPIRE_DAYS = 365

# Bump MINIMUM_APP_VERSION when shipping breaking API or model changes.
# Bump API_VERSION on any breaking API change.
MINIMUM_APP_VERSION = "1.0.0"
API_VERSION = 1

# Lifespan: run migrations at startup using the recommended async context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        if 'db' in globals():
            log.info("Checking pending database migrations")
            apply_migrations(db)
        else:
            log.info("No database instance found for migrations")
    except Exception as e:
        log.info(f"Migration check failed: {e}")
    yield

# Instantiate the FastAPI with lifespan manager
app = FastAPI(lifespan=lifespan)

app.mount("/ui", StaticFiles(directory="static",html=True))
app.mount("/downloads", StaticFiles(directory="downloads",html=False))

# CORS
origins = [
    "https://localhost:8000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Handle exceptions
class InvalidEmailException(Exception):
    pass

class InvalidPasswordException(Exception):
    pass


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return JSONResponse({"success": False, "error": "unauthorized_client", "detail": exc.detail}, status_code=exc.status_code)
    return JSONResponse({"success": False, "error": exc.detail}, status_code=exc.status_code)

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

# RSA decryption for passwords
def decrypt_data(data):
    decoded_data = base64.b64decode(data)

    pem_path = "src/private_key.pem" if getenv("ENV") == "production" else "private_key.pem"
    with open(pem_path, "r") as k:
        key = RSA.importKey(k.read())

    decipher = PKCS1_OAEP.new(key)
    return decipher.decrypt(decoded_data).decode()

# Security emails

def randomword(length):
   letters = string.ascii_lowercase
   return ''.join(random.choice(letters) for i in range(length))

def sendVerificationEmail():
    pass

def sendResetEmail(email) -> str:
    '''function that send a password reset email to the user's email, and returns the security code.'''
    securityCode = randomword(8).upper()
    GmailSender().send(
        dest=email,
        topic="Cuicuisine forgotten password",
        msg=f"Open Cuicuisine and use the following code to reset your password : {securityCode}"
    )
    return securityCode
    

# Token gesture
def create_access_token(data: dict | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDES)
    to_encode.update({"exp": expire})
    log.debug(to_encode)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY_ACCESS, algorithm=ALGORITHM)
    return encoded_jwt, expire

def create_refresh_token(data: dict | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    log.debug(to_encode)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY_REFRESH, algorithm=ALGORITHM)
    log.debug(encoded_jwt)
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
@app.get("/")
async def redirect_to_static(request: Request):
    return RedirectResponse(request.base_url.path + "ui/", status_code=302)

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
        pwd = decrypt_data(form_data.password)
        email = decrypt_data(form_data.username)

        user = authenticate_user(email, pwd)
        
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
        log.debug(e)
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

    email = decrypt_data(form_data.username)
    user = getUserByEmail(email=email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email already exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        pwd = decrypt_data(form_data.password)
        default_name = email.split('@')[0] if '@' in email else email
        user = addUser(name=default_name, email=email, password=get_password_hash(pwd))

        access_token, access_token_expiration_time = create_access_token(data={"sub": str(user.id)})
        refresh_token, refresh_token_expiration_time = create_refresh_token(data={"sub": str(user.id)})
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"} #, "expires_in": int(access_token_expiration_time.timestamp()), "refresh_token_expires_in": int(refresh_token_expiration_time.timestamp())

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.post("/refresh_token", response_model=Token|None)
async def refresh_access_token(form_data: Annotated[MyOAuth2RefreshRequestForm, Depends()]):
    id, exp = validate_refresh_token(form_data.refresh_token)
    if getUserById(id):
        access_token, access_token_expiration_time = create_access_token(data={"sub": id})
        return {"access_token": access_token, "refresh_token": form_data.refresh_token, "token_type": "bearer"} #, "expires_in": int(access_token_expiration_time.timestamp()), "refresh_token_expires_in": int(exp.timestamp())}
    return None

@app.post("/change/add", status_code=status.HTTP_200_OK, response_model=bool)
async def add_change(
    current_user: Annotated[User, Depends(get_current_active_user)],
    json_data: dict = Body(...)
):
    log.debug(json_data)
    log.debug(f"operation type: {json_data['operationType']}")
    if 'objectType' in json_data.keys() and 'objectId' in json_data.keys() and 'changeId' in json_data.keys() and 'operationType' in json_data.keys():
        return addChange(changeId=json_data['changeId'], objectType=json_data['objectType'], operationType=int(json_data['operationType']), objectId=json_data['objectId'])
    return False

@app.get("/change/newer_count/{id}", response_model=int|None)
async def get_newer_changes_count(
    current_user: Annotated[User, Depends(get_current_active_user)],
    id: str
):
    result, changes = getChangesAfter(changeId=id, userId=str(current_user.id))
    if result:
        return len(changes)
    return None

@app.get("/change/get/{id}", response_model=dict)
async def get_changes(
    current_user: Annotated[User, Depends(get_current_active_user)],
    id: str
):
    result, changes = getChangesAfter(changeId=id, userId=str(current_user.id))
    log.debug(f"Changes fetched:  result={result}, changes={changes}")
    return {'success': result, 'changes': changes}
    

@app.get("/users/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user

@app.post("/users/me/change_password/", status_code=status.HTTP_200_OK, response_model=bool)
async def change_password(
    current_user: Annotated[User, Depends(get_current_active_user)],
    json_data: dict = Body(...)
):
    data = NewUserPasswordRequest(**json_data)
    old_pwd = decrypt_data(data.old_pwd)
    new_pwd = decrypt_data(data.new_pwd)

    user = getUserById(current_user.id)

    if verify_password(old_pwd, user.hashed_password):
        return updateUserPassword(current_user.id, get_password_hash(new_pwd))
    return False
    
@app.post("/users/request_password_recovery/", status_code=status.HTTP_200_OK, response_model=Result)
async def request_password_recovery(
    email: str = Body(...)
):
    """Send forgotten password email"""
    
    if email:
        user = getUserByEmail(email=email)
        
        if user:
            code = sendResetEmail(email)
            if code:
                addResult = addRecoveryRequest(email, code)
                if addResult:
                    return Result(result=True)
                return Result(result=False, reason="Failed to add code to db")
            return Result(result=False, reason="Failed to send code by email")

    return  Result(result=False, reason="Invalid email")

@app.post("/users/password_recovery/", status_code=status.HTTP_200_OK, response_model=Result)
async def password_recovery(
    json_data: dict = Body(...)
):
    data = RecoverPasswordRequest(**json_data)
    email = decrypt_data(data.email)
    pwd = decrypt_data(data.encrypted_password)
    code = decrypt_data(data.security_code)

    checkResult = checkRecoveryCode(email, code)

    if checkResult.result:
        removeAllRecoveriesForEmail(email)
        user = getUserByEmail(email=email)
        if updateUserPassword(user.id, get_password_hash(pwd)):
            return Result(result=True)
        return Result(result=False, reason="User update failed")
        
    return checkResult



@app.post('/users/me/update', response_description="Update user", status_code=status.HTTP_200_OK, response_model=dict)
async def update_user_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
    json_data: dict = Body(...)
):
    update = UpdateUserRequest(**json_data)
    data = update.dump()
    id = data.pop('id')
    requestDate = datetime.fromisoformat(data.pop('requestDate', None)) if 'requestDate' in data else None

    user = getUserById(id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if requestDate and user.lastUpdate.astimezone(timezone.utc) > requestDate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflict")

    ack, lastUpdate = updateUser(str(current_user.id), data)
    if not ack:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error")
    return {'success': True, 'dateTime': lastUpdate}

@app.delete('/users/me/delete', response_description="Delete user", status_code=status.HTTP_200_OK, response_model=dict)
async def delete_user_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    ack = deleteUser(current_user.id)
    if not ack:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error")
    return {'success': True}

@app.get('/users/me/fetchall', response_model=dict)
async def fetch_all(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    books = getUserBooks(current_user.id)
    data = {'books': [], 'recipes': [], 'lastChange': getLastUserChangeId(current_user.id)}
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
        if str(current_user.id) in book.users and book.access[str(current_user.id)] >= AccessLevel.READ:
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
    requestDate = datetime.fromisoformat(data.pop('requestDate', None)) if 'requestDate' in data else None

    book = getBookById(id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    if str(current_user.id) not in book.users or book.access[str(current_user.id)] < AccessLevel.WRITE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if requestDate and book.lastUpdate.astimezone(timezone.utc) > requestDate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflict")

    ack, lastUpdate = updateBookSet(id, data)
    if not ack:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error")
    return {'success': True, 'dateTime': lastUpdate}

@app.get('/books/revokeme/{id}', response_description="Remove user from book", status_code=status.HTTP_200_OK, response_model=dict)
async def revoke_me_from_book(
    current_user: Annotated[User, Depends(get_current_active_user)],
    id: str
):
    book: Book = getBookById(id)
    if not book or str(current_user.id) not in book.users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    if book.access[str(current_user.id)] == AccessLevel.OWN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner cannot leave their own book")

    book.users.remove(str(current_user.id))
    book.access.pop(str(current_user.id), None)
    result, lastUpdate = updateBookSet(id, {'users': book.users, 'access': book.access})
    if not result:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error")
    return {'success': True, 'dateTime': lastUpdate}

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
        access={str(current_user.id): 2},
        tags=form_data.tags,
        bookIngredients=form_data.bookIngredients
    )
    if not ack:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error")
    return {'success': True, 'lastUpdate': lastUpdate}

@app.delete('/books/delete', response_description="Delete book", status_code=status.HTTP_200_OK, response_model=dict)
async def delete_book(
    current_user: Annotated[User, Depends(get_current_active_user)],
    id: str = Body(...)
):
    book = getBookById(id) if id else None
    if not isinstance(book, Book):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    if str(current_user.id) not in book.users or book.access[str(current_user.id)] != AccessLevel.OWN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if not deleteBook(id):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error")
    return {'success': True}

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
    log.debug(data)
    requestDate = datetime.fromisoformat(data.pop('requestDate', None))

    access = getRecipeUserAccess(userId=current_user.id, recipeId=id)
    if access is None or access < AccessLevel.WRITE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    recipe = getRecipeById(id)
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    log.debug("requestDate: " + str(requestDate))
    log.debug("recipe.lastUpdate: " + str(recipe.lastUpdate))
    if requestDate and recipe.lastUpdate.astimezone(timezone.utc) > requestDate:
        log.debug("Conflict detected")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflict")

    ack, lastUpdate = updateRecipe(id, data)
    if not ack:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error")
    return {'success': True, 'dateTime': lastUpdate}

@app.put('/recipes/create', response_description="Create recipe", status_code=status.HTTP_201_CREATED, response_model=dict)
async def create_recipe(
    current_user: Annotated[User, Depends(get_current_active_user)],
    form_data: Annotated[AddRecipeRequestForm, Depends()]
):
    book = getBookById(form_data.bookId)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    if str(current_user.id) not in book.users or book.access[str(current_user.id)] < AccessLevel.WRITE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    ack_recipe, lastUpdate = addRecipe(id=form_data.id, name=form_data.name)
    if not ack_recipe:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error")

    book.recipeIds.append(str(form_data.id))
    updateBookSet(book.id, {'recipeIds': book.recipeIds})
    return {'success': True, 'lastUpdate': lastUpdate}

@app.get('/books/join/{id}', response_model=bool)
async def join_book(
    current_user: Annotated[User, Depends(get_current_active_user)],
    id: str
):
    book: Book = getBookById(id)
    if book:
        if str(current_user.id) not in book.users:
            joinBook(id, str(current_user.id))
            addChange(
                changeId=str(ObjectId()),
                objectType='book',
                operationType=OperationType.UPDATE,
                objectId=id
            )
            return True
    return False

@app.delete('/recipes/delete', response_description="Delete recipe", status_code=status.HTTP_200_OK, response_model=dict)
async def delete_recipe_endpoint(
    current_user: Annotated[User, Depends(get_current_active_user)],
    id: str = Body(...)
):
    recipe = getRecipeById(id) if id else None
    if not isinstance(recipe, Recipe):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    access = getRecipeUserAccess(userId=current_user.id, recipeId=id)
    if access is None or access != AccessLevel.OWN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if not deleteRecipe(id):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error")
    return {'success': True}
## Images
@app.post("/image/upload", status_code=status.HTTP_200_OK, response_model=dict)
async def uploadFile(
    current_user: Annotated[User, Depends(get_current_active_user)],
    file: UploadFile,
    info: Annotated[ImageInfoForm, Depends()]
):
    log.debug(f"Uploading file: recipeId={info.recipeId}, imageId={info.imageId}, filename={file.filename}, content_type={file.content_type}")
    if not path.exists("storage/"):
        mkdir("storage/")
    
    if not path.exists(f"storage/{info.recipeId}"):
        mkdir(f"storage/{info.recipeId}")

    try:
        with open(f"storage/{info.recipeId}/{info.imageId}", "wb") as out_file:
            content = await file.read()
            out_file.write(content)
        log.debug("File uploaded successfully")
        return {'success': True}
    except Exception as e:
        log.debug("Error uploading file:", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error")

@app.get("/image/download/{recipeId}/{imageId}", status_code=status.HTTP_200_OK)
async def downloadFile(
    current_user: Annotated[User, Depends(get_current_active_user)],
    recipeId: str,
    imageId: str
):
    if imageId and recipeId:
        imagePath = f"storage/{recipeId}/{imageId}"
        access = getRecipeUserAccess(userId=current_user.id, recipeId=recipeId)
        if access != None:
            if path.isfile(imagePath):
                return FileResponse(path=imagePath, media_type='application/octet-stream', filename=imageId)

@app.delete("/image/delete", status_code=status.HTTP_200_OK, response_model=dict)
async def deleteFile(
    current_user: Annotated[User, Depends(get_current_active_user)],
    data: dict = Body(...)
):
    if 'recipeId' not in data or 'imageId' not in data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missing recipeId or imageId")

    recipeId = data['recipeId']
    imageId = data['imageId']
    imagePath = f"storage/{recipeId}/{imageId}"
    folderPath = f"storage/{recipeId}"

    access = getRecipeUserAccess(userId=current_user.id, recipeId=recipeId)
    if access is None or access < AccessLevel.WRITE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if not path.isfile(imagePath):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    remove(imagePath)
    if len(listdir(folderPath)) == 0:
        rmdir(folderPath)
    return {'success': True}

@app.get("/version", status_code=status.HTTP_200_OK)
async def get_version():
    """Return the minimum compatible app version and current API version. No auth required."""
    return {"minimum_app_version": MINIMUM_APP_VERSION, "api_version": API_VERSION}

@app.get("/apk/get_latest", status_code=status.HTTP_200_OK, response_model=str|None)
async def get_latest():
    """Get the latest APK version"""
    for file in reversed(listdir("downloads/")):
        if file.endswith(".apk"):
            return "/downloads/" + file
    return None

@app.get("/apk/download", status_code=status.HTTP_200_OK)
async def download_latest_apk():
    """Download the latest APK with correct headers so browsers trigger a file download"""
    for file in reversed(listdir("downloads/")):
        if file.endswith(".apk"):
            return FileResponse(
                path=f"downloads/{file}",
                media_type="application/vnd.android.package-archive",
                filename=file,
            )
    raise HTTPException(status_code=404, detail="APK not found")