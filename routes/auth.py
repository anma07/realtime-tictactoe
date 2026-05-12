from fastapi import APIRouter
from pydantic import BaseModel
from utils.face_auth import authenticate_user
from database.sql import user_exists, set_user_online, get_connection

router = APIRouter()


class LoginRequest(BaseModel):
    image_data: str


def get_user_name(uid: str) -> str:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM users WHERE uid = %s", (uid,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else uid
    except Exception:
        return uid


@router.post("/login")
async def login(request: LoginRequest):
    try:
        print("LOGIN REQUEST RECEIVED")

        uid = authenticate_user(request.image_data)
        print("MATCHED UID:", uid)

        if uid is None:
            return {"status": "fail", "reason": "face_not_recognized"}

        if not user_exists(uid):
            return {"status": "fail", "reason": "user_not_found"}

        set_user_online(uid)
        name = get_user_name(uid)

        return {"status": "success", "uid": uid, "name": name}

    except Exception as e:
        print("LOGIN ERROR:", e)
        return {"status": "error", "reason": str(e)}