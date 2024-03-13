#!/usr/bin/python3

from typing import Annotated, Union
from typing_extensions import Annotated
from fastapi.param_functions import Form, Doc

from pydantic import BaseModel, Field
from pydantic_mongo import AbstractRepository, ObjectIdField
from datetime import datetime
import uuid

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

class Book(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    name: str
    recipeUids: list[str]
    users: list[str]
    access: dict[str, int] ## to change
    lastUpdate: datetime

class Ingredient(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    name: str
    quantity: float
    unit: str
    density: float | None = 0

class Tag(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    name: str
    index: int

class RecipeStep(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    step: str
    time: int

class Variant(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    userId: str
    variant: str

class Access(BaseModel):
    pass

class Recipe(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    name: str
    pictures: list[str]
    preparationTime: int
    cookingTime: int
    waitingTime: int
    tags: list[str]
    quantity: int
    quantityType: str
    recipeIngredients: list[Ingredient]
    steps: list[RecipeStep]
    variants: list[Variant]
    creationDate: datetime
    lastUpdate: datetime


class UserRepository(AbstractRepository[DbUser]):
   class Meta:
      collection_name = 'users'

class BookRepository(AbstractRepository[Book]):
   class Meta:
      collection_name = 'books'

class RecipeRepository(AbstractRepository[Recipe]):
   class Meta:
      collection_name = 'recipes'


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