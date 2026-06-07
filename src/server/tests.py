from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated

from app import app
from model import *
from datetime import datetime

def test_add_user():
    with TestClient(app) as client:
        response = client.post("/add_user", json={'firebaseId': 'test','name': 'sucre', 'email': 'auieauei@bépobépo.fr', 'lastUpdate': str(datetime.now())})
        
        assert response.status_code == 201

        body = response.json()
        assert body.get("name") == "sucre"
        assert body.get("email") == "auieauei@bépobépo.fr"
        assert body.get("favoriteRecipes") == []
        assert "_id" in body

        print(body)

def test_delete_user(id):
    with TestClient(app) as client:
        response = client.delete("/delete_user/{}".format(id))
        
        assert response.status_code == 204

def test_add_recipe():
    with TestClient(app) as client:
        response = client.post("/add_recipe", json={
            'id': str(uuid.uuid4()),
            'name': 'test',
            'pictures': [],
            'preparationTime': 0,
            'cookingTime': 0,
            'waitingTime': 0,
            'tags': ['tag'],
            'persons': 2,
            'recipeIngredients': [],
            'steps': [],
            'comments': [],
            'creationDate': str(datetime.now()),
            'lastUpdate': str(datetime.now())
            })
        
def test_update_recipe():
    with TestClient(app) as client:
        """ _recipe = recipe.dict()
        _recipe['creationDate'] = str(_recipe['creationDate'])
        _recipe['lastUpdate'] = str(_recipe['lastUpdate'])
        print(_recipe) """
        response = client.post("/update_recipe", json={
            'id': "ba89c109-d727-458d-980c-28951179003f",
            'name': 'test-update',
            'pictures': [],
            'preparationTime': 10,
            'cookingTime': 10,
            'waitingTime': 10,
            'tags': ['tag'],
            'persons': 2,
            'recipeIngredients': [],
            'steps': [],
            'comments': [],
            'creationDate': str(datetime.now()),
            'lastUpdate': str(datetime.now())
            })
        
recipe = Recipe(name= 'test-update', pictures= [], preparationTime= 10, cookingTime= 10, waitingTime= 10, tags= ['tag'], persons= 2, recipeIngredients= [], steps= [], comments= [], creationDate= datetime.now(), lastUpdate= datetime.now())
recipe.id = "ba89c109-d727-458d-980c-28951179003f"

#test_add_user()
#test_delete_user('POGkW18pnMfTPa86RKuec577N1y2')
#test_add_recipe()
test_update_recipe()