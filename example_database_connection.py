# pylint: disable=broad-except,unused-argument,missing-module-docstring,fixme,missing-docstring
# pylint: disable=missing-function-docstring,missing-class-docstring
import os
import sys

from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()

# Before running, create a .env file in the root folder and set the DATABASE_PASSWORD there
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")

URI = f"mongodb+srv://juhanikataja:{DATABASE_PASSWORD} \
        @cluster0.stid8ni.mongodb.net/?appName=Cluster0"

# Create a new client and connect to the server
with MongoClient(URI, server_api=ServerApi('1')) as client:
    db = client["battleship-game-db"]
    collection = db["test-collection"]

    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
        sys.exit()

    # test user creation, these can create duplicates
    user = {"name": "VP", "matches_won": 12, "matches_lost": 8}
    collection.insert_one(user)

    users = [
        {"name": "Juhani", "matches_won": 2, "matches_lost": 10},
        {"name": "Mongo", "matches_won": 0, "matches_lost": 0}
    ]
    collection.insert_many(users)

    # Get one
    print(collection.find_one({"name": "Juhani"}))

    # Get all
    for user in collection.find():
        print(user)

    # Get users who have won at least one match
    for user in collection.find({"matches_won": {"$gt": 0}}):
        print(user)

    # Increment VP's matches won by 1
    collection.update_one(
        {"name": "VP"},
        {"$inc": {"matches_won": 1}}
    )

    # Count all documents
    count = collection.count_documents({})
    print(count)
