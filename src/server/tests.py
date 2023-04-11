from fastapi import FastAPI
from fastapi.testclient import TestClient
from app import app
from model import *
from datetime import datetime

def test_add_user():
    with TestClient(app) as client:
        response = client.post("/add_user", json={'firebaseId': 'POGkW18pnMfTPa86RKuec577N1y2','name': 'test', 'email': 'auieauei@bépobépo.fr', 'lastUpdate': str(datetime.now())})
        
        assert response.status_code == 201

        body = response.json()
        assert body.get("name") == "test"
        assert body.get("email") == "auieauei@bépobépo.fr"
        assert body.get("favoriteRecipes") == []
        assert "_id" in body

        print(body)

def test_delete_user(id):
    with TestClient(app) as client:
        response = client.delete("/delete_user/{}".format(id))
        
        assert response.status_code == 204


#test_add_user()
test_delete_user('POGkW18pnMfTPa86RKuec577N1y2')