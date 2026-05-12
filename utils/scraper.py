import csv
import requests
from concurrent.futures import ThreadPoolExecutor
from database.sql import get_connection, create_table, insert_user
from database.mongo import store_image

# get_connection()
create_table()

def read_csv(file_path):
    students = []

    with open(file_path, newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:
            students.append(row)

    return students

def build_url(website):
    if not website.startswith("http"):
        website = "https://" + website
    return website.rstrip("/") + "/images/pfp.jpg"

data = read_csv("batch_data.csv")

def fetch_image(image_url, student):
    try:
        response = requests.get(image_url, timeout=5)

        if response.status_code == 200:
            print(f"[SUCCESS] {student['uid']} ✅")
            return response.content 
        else:
            print(f"[FAIL] {student['uid']} → {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] {student['uid']} → {e}")

    return None

def process_student(student):
    website = student["website_url"]
    image_url = build_url(website)

    # if student["uid"] >= '2025101107':
    image_data = fetch_image(image_url, student)

    with ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(insert_user, student["uid"], student["name"])

            if image_data:
                executor.submit(store_image, student["uid"], image_data)

for student in data:
    process_student(student)
