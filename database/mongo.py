from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

def _get_collection():
    uri = os.getenv("MONGO_URI")

    if not uri:
        raise ValueError("MONGO_URI not found in .env file")

    client = MongoClient(uri)
    db = client["project_db"]
    return db["profile_images"]

collection = _get_collection()

def store_image(uid, image_data):
    try:
        collection.update_one(
            {"uid": uid},
            {"$set": {"image": image_data}},
            upsert=True
        )
        print(f"[MONGO] Stored {uid}")
    except Exception as e:
        print(f"[MONGO ERROR] {uid} → {e}")


def get_all_images():
    data = {}

    try:
        for doc in collection.find({}, {"_id": 0}):
            uid = doc["uid"]
            image = doc["image"]
            data[uid] = image

    except Exception as e:
        print(f"[MONGO ERROR] Fetching images → {e}")

    return data