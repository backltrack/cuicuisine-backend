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

@app.post('/users/me/update', response_description="Update user", status_code=status.HTTP_200_OK, response_model=bool)
async def update_user_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
    json_data: dict = Body(...)
):
    update = UpdateUserRequest(**json_data)
    data = update.dump()
    id = data.pop('id')
    print(data)
    
    updated_user = updateUser(str(current_user.id), data)
    return updated_user is not None


@app.get('/books/get/{id}', response_model=Book|None)
async def get_book(
    current_user: Annotated[User, Depends(get_current_active_user)],
    id: str
):
    print(id)
    print(current_user)
    book: Book = getBookById(id)
    print(f"{book}")
    if book:
        if str(current_user.id) in book.users:
            return book

@app.post('/books/update', response_description="Update book", status_code=status.HTTP_200_OK, response_model=bool)
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
                result = updateBook(id, data)
                return result
    
    return False

@app.put('/books/create', response_description="Create book", status_code=status.HTTP_201_CREATED, response_model=Book|None)
async def create_book(
    current_user: Annotated[User, Depends(get_current_active_user)],
    form_data: Annotated[AddBookRequestForm, Depends()]
):
    
    book = addBook(
        name=form_data.name,
        recipeUids=[],
        users=[str(current_user.id)],
        access={str(current_user.id): 2}
    )
    
    return book


@app.get('/recipes/get/{id}', response_model=Recipe|None)
async def get_recipe(
    current_user: Annotated[User, Depends(get_current_active_user)],
    id: str
):
    recipe: Recipe = getRecipeById(id)

    if recipe:
        access = getRecipeUserAccess(userId=current_user.id, recipeId=id)
        if access and access > 0:
            print(access)
            return recipe

@app.post('/test', status_code=status.HTTP_200_OK, response_model=bool)
async def test(
    current_user: Annotated[User, Depends(get_current_active_user)],
    json_data: dict = Body(...)
):
    print(json_data)
    t = Test(**json_data)
    print(t)
    data = t.dump()
    print(data)
    return True

@app.post('/recipes/update', response_description="Update recipe", status_code=status.HTTP_200_OK, response_model=bool)
async def update_recipe(
    current_user: Annotated[User, Depends(get_current_active_user)],
    json_data: dict = Body(...)
):
    print(json_data)
    update = UpdateRecipeRequest(**json_data)
    data = update.dump()
    id = data.pop('id')

    access = getRecipeUserAccess(userId=current_user.id, recipeId=id)
    print(access)
    if access and access > 1:
        result = updateRecipe(id, data)
        return result
    
    return False

#testing
# @app.post('/recipes/update', response_description="Update recipe", status_code=status.HTTP_200_OK, response_model=bool)
# async def update_recipe(
#     current_user: Annotated[User, Depends(get_current_active_user)],
#     data: UpdateRecipeRequest
# ):
#     data = data.dump()
#     id = data.pop('id')
#     print(id)
#     print(data)

#     print(current_user)

#     access = getRecipeUserAccess(userId=current_user.id, recipeId=id)
#     print(access)
#     if access and access > 1:
#         result = updateRecipe(id, data)
#         return result
    
#     return False

@app.put('/recipes/create', response_description="Create recipe", status_code=status.HTTP_201_CREATED, response_model=Recipe|None)
async def create_recipe(
    current_user: Annotated[User, Depends(get_current_active_user)],
    form_data: Annotated[AddRecipeRequestForm, Depends()]
):
    book = getBookById(form_data.bookId)
    print(book)
    print(current_user)

    if book and str(current_user.id) in book.users:
        if book.access[str(current_user.id)] > 0:
            recipe = addRecipe(name=form_data.name)

            book.recipeUids.append(str(recipe.id))
            updateBook(book.id, {'recipeUids': book.recipeUids})

            return recipe
    
    return None
