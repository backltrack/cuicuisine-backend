import json
import os
from server.mongo import *
from server.model import *

from bson import ObjectId

from passlib.context import CryptContext

from os import path, listdir, mkdir
from shutil import copy

load_dotenv()

# Input
input_dir = os.getenv('INPUT_DIR')
input_file = path.join(input_dir, 'extract_recettes.json')
input_images_dir = path.join(input_dir, 'images')

if not path.exists(input_file):
    print(f"Input file {input_file} does not exist.")
    exit(1)

# Output
output_images_dir = os.getenv('OUTPUT_DIR')

if not path.exists(output_images_dir):
    mkdir(output_images_dir)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

user_map = {}
recipe_map = {}

with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

recipe_index = {r['id']: r for r in data['recipes']}

# Users
for user in data['users']:
    if not getUserByEmail(user['email']):
        newuser = addUser(user['name'], user['email'], get_password_hash("ToChange01"))
        user_map[user['id']] = newuser.id

# Recipes
for recipe in data['recipes']:
    _recipe = recipe.copy()
    oldId = _recipe.pop('id')
    currentId = ObjectId()

    _recipe['recipeIngredients'] = [
        {
            'bookIngredientId': ri['bookIngredientId'],
            'quantity': ri['quantity'],
            'unitOverride': ri.get('unit'),
            'densityOverride': ri.get('density'),
        }
        for ri in _recipe['recipeIngredients']
    ]

    _recipe['variants'] = [
        {
            'userId': str(user_map[v['userId']]),
            'variant': v['variant'],
            'initials': v['initials'],
        }
        for v in _recipe['variants']
        if v['userId'] in user_map
    ]

    addRecipe(id=currentId, name=_recipe['name'])
    updateRecipe(currentId, _recipe)
    recipe_map[oldId] = currentId

# Books
for book in data['books']:
    access = {str(user_map[uid]): level for uid, level in book['access'].items() if uid in user_map}
    recipes = [str(recipe_map[oid]) for oid in book['recipeIds'] if oid in recipe_map]
    users = [str(user_map[uid]) for uid in book['users'] if uid in user_map]

    addBook(
        id=ObjectId(),
        name=book['name'],
        recipeIds=recipes,
        users=users,
        access=access,
        tags=book.get('tags', []),
        bookIngredients=book.get('bookIngredients', []),
    )

# Update favoriteRecipes for each user
for user in data['users']:
    if user['id'] in user_map:
        mapped_favorites = [str(recipe_map[rid]) for rid in user.get('favoriteRecipes', []) if rid in recipe_map]
        if mapped_favorites:
            updateUser(str(user_map[user['id']]), {'favoriteRecipes': mapped_favorites})

# Copy images
for oldId, newId in recipe_map.items():
    src_dir = path.join(input_images_dir, str(oldId))
    if not path.exists(src_dir):
        continue

    recipe_pictures = recipe_index[oldId]['pictures']
    valid_pictures = []

    for picture in recipe_pictures:
        src_file = path.join(src_dir, picture)
        if path.exists(src_file):
            dst_dir = path.join(output_images_dir, str(newId))
            if not path.exists(dst_dir):
                mkdir(dst_dir)
            copy(src_file, path.join(dst_dir, picture))
            valid_pictures.append(picture)

    if len(valid_pictures) != len(recipe_pictures):
        updateRecipe(newId, {'pictures': valid_pictures})
