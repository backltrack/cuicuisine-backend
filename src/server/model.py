#!/usr/bin/python3

import json
from typing import Annotated, Union
from typing_extensions import Annotated
from fastapi.param_functions import Form, Doc

from pydantic import BaseModel, Field
from pydantic_mongo import AbstractRepository, ObjectIdField
from bson import ObjectId
from datetime import datetime

from enum import IntEnum

class UpdateStatusCode(IntEnum):
    SUCCESS = 0
    NOT_AUTHORIZED = 1
    OBJECT_NOT_FOUND = 2
    CONFLICT = 3
    SERVER_ERROR = 4

class OperationType(IntEnum):
    CREATE = 0
    DELETE = 1
    UPDATE = 2

class AccessLevel(IntEnum):
    READ = 0
    WRITE = 1
    OWN = 2

class RequestBase:
    def dump(self, exclude_empty=True):
        data = self.__dict__.copy()
        to_exclude = []
        if exclude_empty:
            for key in data.keys():
                if data[key] is None or data[key] == (None,):
                    to_exclude.append(key)
            for key in to_exclude:
                data.pop(key)
        return data

class Result(BaseModel, RequestBase):
    result: bool
    reason: str = ''

class Token(BaseModel):
    access_token: str
    #expires_in: int
    refresh_token: str
    #refresh_token_expires_in: int
    token_type: str

class TokenData(BaseModel):
    id: str | None = None


class User(BaseModel):
    id: ObjectIdField = None
    name: str
    email: str
    favoriteRecipes: list[str] | None = []
    lastUpdate: datetime

class DbUser(User):
    disabled: bool = False
    hashed_password: str

class Ingredient(BaseModel):
    bookIngredientId: str
    quantity: float
    unitOverride: str | None = None
    densityOverride: float | None = None

class BookIngredient(BaseModel):
    id: str
    name: str
    unit: str
    density: float | None = 0

class Tag(BaseModel):
    id: str
    name: str
    category: str | None = None

class Book(BaseModel):
    id: ObjectIdField = None
    name: str
    recipeIds: list[str] = []
    users: list[str]
    access: dict[str, int] ## to change
    bookIngredients: list[BookIngredient] = []
    tags: list[Tag] = []
    lastUpdate: datetime

class RecipeStep(BaseModel):
    name: str | None = None
    step: str
    time: int

class Comment(BaseModel):
    userId: str
    comment: str
    initials: str

class Recipe(BaseModel):
    id: ObjectIdField = None
    name: str
    pictures: list[str] = []
    preparationTime: int = 0
    cookingTime: int = 0
    waitingTime: int = 0
    tags: list[str] = []
    quantity: int = 2
    quantityType: str = "personnes"
    recipeIngredients: list[Ingredient] = []
    steps: list[RecipeStep] = []
    comments: list[Comment] = []
    creationDate: datetime
    lastUpdate: datetime

class Change(BaseModel):
    id: ObjectIdField = None
    changeId: str
    objectType: str
    operationType: int
    objectId: str
    creationDate: datetime

class Recovery(BaseModel):
    id: ObjectIdField = None
    email: str
    code: str
    expiration_date: datetime

class Migration(BaseModel):
    id: ObjectIdField = None
    version: int
    description: str
    applied_at: datetime

class UserRepository(AbstractRepository[DbUser]):
   class Meta:
      collection_name = 'users'

class BookRepository(AbstractRepository[Book]):
   class Meta:
      collection_name = 'books'

class RecipeRepository(AbstractRepository[Recipe]):
   class Meta:
      collection_name = 'recipes'

class ChangeRepository(AbstractRepository[Change]):
    class Meta:
        collection_name = 'changes'

class RecoveryRepository(AbstractRepository[Recovery]):
    class Meta:
        collection_name = 'recoveries'

class MigrationRepository(AbstractRepository[Migration]):
    class Meta:
        collection_name = 'migrations'

class UpdateUserRequest(BaseModel, RequestBase):
    id: str
    name: str|None = None
    email: str|None = None
    favoriteRecipes: list[str]|None = None
    requestDate: str|None = None

class NewUserPasswordRequest(BaseModel, RequestBase):
    old_pwd: str
    new_pwd: str

class RecoverPasswordRequest(BaseModel, RequestBase):
    email: str
    encrypted_password: str
    security_code: str

class AddBookRequestForm:
    def __init__(
        self,
        *,
        id: Annotated[str, Form()],
        name: Annotated[str, Form()],
        tags: Annotated[str, Form()] = "[]",
        bookIngredients: Annotated[str, Form()] = "[]"
    ):
        self.id = ObjectId(id)
        self.name = name
        self.tags = [Tag(**t) for t in json.loads(tags)]
        self.bookIngredients = [BookIngredient(**bi) for bi in json.loads(bookIngredients)]


class UpdateBookRequest(BaseModel, RequestBase):
        id: str
        name: str|None = None
        recipeIds: list[str]|None = None
        users: list[str]|None = None
        access: dict[str, int]|None = None
        tags: list[Tag]|None = None
        bookIngredients: list[BookIngredient]|None = None
        requestDate: str|None = None

        def dump(self, exclude_empty=True):
            data = super().dump(exclude_empty)
            if 'tags' in data:
                data['tags'] = [tag.model_dump() for tag in data['tags']]
            if 'bookIngredients' in data:
                data['bookIngredients'] = [ingredient.model_dump() for ingredient in data['bookIngredients']]
            return data

class AddRecipeRequestForm:
    def __init__(
        self,
        id: Annotated[
            str,
            Form()
        ],
        name: Annotated[
            str,
            Form()
        ],
        bookId: Annotated[
            str,
            Form()
        ]
    ):
        self.id = ObjectId(id)
        self.name = name
        self.bookId = bookId

class UpdateRecipeRequest(BaseModel, RequestBase):
        id: str
        name: str|None = None
        pictures: list[str]|None = None
        preparationTime: int|None = None,
        cookingTime: int|None = None,
        waitingTime: int|None = None,
        tags: list[str]|None = None,
        quantity: int|None = None,
        quantityType: str|None = None,
        recipeIngredients: list[Ingredient]|None = None,
        steps: list[RecipeStep]|None = None,
        comments: list[Comment]|None = None
        requestDate: str|None = None


class MyOAuth2RefreshRequestForm:
    def __init__(
        self,
        *,
        grant_type: Annotated[
            Union[str, None],
            Form(pattern="refresh_token"),
            Doc(
                """
                The OAuth2 spec says it is required and MUST be the fixed string
                "password". Nevertheless, this dependency class is permissive and
                allows not passing it. If you want to enforce it, use instead the
                `OAuth2PasswordRequestFormStrict` dependency.
                """
            ),
        ] = None,
        refresh_token: Annotated[
            str,
            Form(),
            Doc(
                """
                `username` string. The OAuth2 spec requires the exact field name
                `username`.
                """
            ),
        ],
        client_id: Annotated[
            Union[str, None],
            Form(),
            Doc(
                """
                If there's a `client_id`, it can be sent as part of the form fields.
                But the OAuth2 specification recommends sending the `client_id` and
                `client_secret` (if any) using HTTP Basic auth.
                """
            ),
        ] = None,
        client_secret: Annotated[
            Union[str, None],
            Form(),
            Doc(
                """
                If there's a `client_password` (and a `client_id`), they can be sent
                as part of the form fields. But the OAuth2 specification recommends
                sending the `client_id` and `client_secret` (if any) using HTTP Basic
                auth.
                """
            ),
        ] = None,
    ):
        self.grant_type = grant_type
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret

class ImageInfoForm:
    def __init__(
        self,
        *,
        recipeId: Annotated[
            str,
            Form()
        ],
        imageId: Annotated[
            str,
            Form()
        ]
    ):
        self.recipeId = recipeId
        self.imageId = imageId


    