import json
from server.mongo import *
from server.model import *
from server.app import get_password_hash

from bson import ObjectId

from os import path, listdir, mkdir
from shutil import copy
        
user_map = {}
book_map = {}
recipe_map = {}

def getUserInitials(oldUserId):
    if oldUserId in user_map.keys():
        userId = user_map[oldUserId]
        user = getUserById(userId)
        if user:
            names = user.name.split(' ')
            if len(names) > 1:
                initials = names[0][0] + names[1][0]
                return initials.upper()
            elif len(names) > 0:
                return names[0][0].upper()
            else:
                return ""


def findRecipe(id, data):
    for recipe in data['recipes']:
        if recipe['id'] == id:
            return recipe

def findBook(id, data):
    for recipe in data['books']:
        if recipe['id'] == id:
            return recipe

with open('../tests/extract_recettes.json', 'r') as f:
    data = json.load(f)

for user in data['users']:
    if not getUserByEmail(user['email']):
        newuser = addUser(user['name'], user['email'], get_password_hash("ToChange01"))
        user_map[user['id']] = newuser.id

for recipe in data['recipes']:
    _recipe = recipe.copy()
    oldId = _recipe.pop('id')
    currentId = ObjectId()

    _variants = []
    for variant in _recipe['variants']:
        if variant['userUid'] in user_map.keys():
            newVariant = {
                'userId': str(user_map[variant['userUid']]),
                'variant': variant['variant'],
                'initials': getUserInitials(variant['userUid'])
            }
            _variants.append(newVariant)
    _recipe['variants'] = _variants
            

    addRecipe(id=currentId, name=_recipe['name'])
    updateRecipe(currentId, _recipe)
    recipe_map[oldId] = currentId

for book in data['books']:
    access = {}
    recipes = []
    users = []
    for userId in book['access'].keys():
        if userId in user_map.keys():
            access[str(user_map[userId])] = book['access'][userId]
    for oldId in book['recipeUids']:
        if oldId in recipe_map.keys():
            recipes.append(str(recipe_map[oldId]))
    for oldId in book['users']:
        if oldId in user_map.keys():
            users.append(str(user_map[oldId]))


    addBook(
        id=ObjectId(),
        name=book['name'],
        recipeIds=recipes,
        users=users,
        access=access
    )

for oldId in recipe_map.keys():
    p = f"../tests/images/{oldId}"
    if path.exists(p):
        local_images = listdir(p)
        recipe_pictures = findRecipe(oldId, data)['pictures']
        for recipe_pict in recipe_pictures:
            if path.exists(path.join(p, recipe_pict)):
                new_p = f"../storage/{recipe_map[oldId]}"
                    
                if not path.exists(new_p):
                    mkdir(new_p)
                copy(path.join(p, recipe_pict), path.join(new_p, recipe_pict))
            else:
                picts = recipe_pictures[:].remove(recipe_pict)
                if not picts:
                    picts = []
                updateRecipe(recipe_map[oldId], {'pictures': picts})


