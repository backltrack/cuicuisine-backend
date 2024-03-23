#!/usr/bin/python3

from typing import Annotated, Union
from typing_extensions import Annotated
from fastapi.param_functions import Form, Doc

from pydantic import BaseModel, Field
from pydantic_mongo import AbstractRepository, ObjectIdField
from datetime import datetime

class RequestFormBase:
    def dump(self, exclude_empty=True):
        data = self.__dict__.copy()
        to_exclude = []
        if exclude_empty:
            for key in data.keys():
                if not data[key]:
                    to_exclude.append(key)
            for key in to_exclude:
                data.pop(key)
        return data


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
    id: ObjectIdField = None
    name: str
    recipeUids: list[str] = []
    users: list[str]
    access: dict[str, int] ## to change
    lastUpdate: datetime

class Ingredient(BaseModel):
    id: ObjectIdField = None
    name: str
    quantity: float
    unit: str
    density: float | None = 0

class Tag(BaseModel):
    id: ObjectIdField = None
    name: str
    index: int

class RecipeStep(BaseModel):
    id: ObjectIdField = None
    step: str
    time: int

class Variant(BaseModel):
    id: ObjectIdField = None
    userId: str
    variant: str

class Access(BaseModel):
    pass

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
    variants: list[Variant] = []
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

class UpdateUserRequestForm(RequestFormBase):
    def __init__(
        self,
        *,
        name: Annotated[
            Union[str, None],
            Form()
        ] = None,
        email: Annotated[
            Union[str, None],
            Form()
        ] = None,
        favoriteRecipes: Annotated[
            Union[list[str], None],
            Form()
        ] = None
    ):
        self.name = name
        self.email = email
        self.favoriteRecipes = favoriteRecipes

class AddBookRequestForm:
    def __init__(
        self,
        *,
        name: Annotated[
            str,
            Form()
        ]
    ):
        self.name = name

class UpdateBookRequestForm(RequestFormBase):
    def __init__(
        self,
        *,
        id: Annotated[
            str,
            Form()
        ],
        name: Annotated[
            Union[str, None],
            Form()
        ] = None,
        recipeUids: Annotated[
            Union[list[str], None],
            Doc("")
        ] = None,
        users: Annotated[
            Union[list[str], None],
            Form()
        ] = None,
        access: Annotated[
            Union[dict[str, int], None],
            Form(),
        ] = None
    ):
        self.id = id
        self.name = name
        self.recipeUids = recipeUids
        self.users = users
        self.access = access

class AddRecipeRequestForm:
    def __init__(
        self,
        *,
        name: Annotated[
            str,
            Form()
        ]
    ):
        self.name = name

class UpdateRecipeRequestForm(RequestFormBase):
    def __init__(
        self,
        *,
        id: Annotated[
            str,
            Form()
        ],
        name: Annotated[
            Union[str, None],
            Form()
        ] = None,
        pictures: Annotated[
            Union[list[str], None],
            Form()
        ] = None,
        preparationTime: Annotated[
            Union[int, None],
            Form()
        ] = None,
        cookingTime: Annotated[
            Union[int, None],
            Form()
        ] = None,
        waitingTime: Annotated[
            Union[int, None],
            Form()
        ] = None,
        tags: Annotated[
            Union[list[str], None],
            Form()
        ] = None,
        quantity: Annotated[
            Union[int, None],
            Form()
        ] = None,
        quantityType: Annotated[
            Union[str, None],
            Form()
        ] = None,
        recipeIngredients: Annotated[
            Union[list[Ingredient], None], 
            Form()
        ] = None,
        steps: Annotated[
            Union[list[RecipeStep], None],
            Form()
        ] = None,
        variants: Annotated[
            Union[list[Variant], None],
            Form()
        ] = None
    ):
        self.id = id
        self.name = name
        self.pictures = pictures
        self.preparationTime = preparationTime
        self.cookingTime = cookingTime
        self.waitingTime = waitingTime
        self.tags = tags
        self.quantity = quantity
        self.quantityType = quantityType
        self.recipeIngredients = recipeIngredients
        self.steps = steps
        self.variants = variants

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