from utils.facial_recognition_module import find_closest_match
from utils.cache import encodings_cache  

def authenticate_user(login_image_data):
    if not encodings_cache:
        print("ERROR: encodings_cache is EMPTY")
        return None

    matched_uid = find_closest_match(login_image_data, encodings_cache)
    return matched_uid