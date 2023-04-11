#!/usr/bin/python3

from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
import uuid

class User(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    firebaseId: str
    name: str
    email: str
    favoriteRecipes: list[str] | None = []
    lastUpdate: datetime

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
    persons: int
    recipeIngrdients: list[Ingredient]
    steps: list[RecipeStep]
    variants: list[Variant]
    creationDate: datetime
    lastUpdate: datetime

