from fastapi import WebSocket

connected_users = {}   # uid -> websocket
connected_names = {}   # uid -> display name


async def connect_user(uid: str, websocket: WebSocket, name: str = ""):
    await websocket.accept()
    connected_users[uid] = websocket
    connected_names[uid] = name or uid


def disconnect_user(uid: str):
    connected_users.pop(uid, None)
    connected_names.pop(uid, None)


async def broadcast_users():
    import json

    users = [
        {"uid": uid, "name": connected_names.get(uid, uid)}
        for uid in connected_users
    ]

    message = json.dumps({
        "type": "lobby_update",
        "users": users
    })

    disconnected = []
    for uid, ws in list(connected_users.items()):
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(uid)

    for uid in disconnected:
        disconnect_user(uid)