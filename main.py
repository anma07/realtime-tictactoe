from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from routes.auth import router as auth_router
from database.mongo import get_all_images
from websocket.lobby import connect_user, disconnect_user, broadcast_users, connected_users
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio

from websocket.game import (
    create_game,
    make_move,
    check_winner,
    compute_elo,
    rooms,
    games,
    player_game_map
)

from database.sql import (
    get_user_rating,
    update_user_rating,
    set_user_online,
    set_user_offline,
    get_connection
)

from utils.cache import encodings_cache
from utils.facial_recognition_module import build_encodings_cache


app = FastAPI()

# ------------------ CORS ------------------ #
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ STARTUP ------------------ #
@app.on_event("startup")
def load_cache():
    print("LOADING FACE CACHE...")
    db_images = get_all_images()
    print("Images fetched from Mongo:", len(db_images))
    encodings_cache.clear()
    encodings = build_encodings_cache(db_images)
    encodings_cache.update(encodings)
    print(f"Encodings loaded: {len(encodings_cache)}")

# ------------------ ROUTES ------------------ #
app.include_router(auth_router)


@app.get("/")
def home():
    return {"message": "Backend running"}


@app.get("/leaderboard")
def leaderboard():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT uid, name, elo_rating
        FROM users
        ORDER BY elo_rating DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [{"uid": r[0], "name": r[1], "elo": r[2]} for r in rows]


# ------------------ Helper: get name from DB ------------------ #
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


# ------------------ WEBSOCKET ------------------ #
@app.websocket("/ws/{uid}")
async def websocket_endpoint(websocket: WebSocket, uid: str):

    name = get_user_name(uid)
    await connect_user(uid, websocket, name)
    set_user_online(uid)
    await broadcast_users()

    print(f"{uid} ({name}) connected")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            # ---------- REQUEST LOBBY (re-broadcast to all) ---------- #
            if msg_type == "request_lobby":
                await broadcast_users()

            # ---------- GET GAME STATE ---------- #
            elif msg_type == "get_game_state":
                 game_id = message.get("game_id")
               # Try reverse if not found
                 if game_id not in games:
                    parts = game_id.split("_")
                    if len(parts) == 2:
                       game_id = f"{parts[1]}_{parts[0]}"
    
                 if game_id in games:
                    if game_id not in rooms:
                     rooms[game_id] = []
                    if uid not in rooms[game_id]:
                     rooms[game_id].append(uid)
                    player_game_map[uid] = game_id
                    game = games[game_id]
                    await websocket.send_text(json.dumps({
                      "type": "game_state",
                      "board": game["board"],
                      "turn": game["turn"],
                      "players": game["players"],
                      "winner": check_winner(game["board"])
                     }))
                 else:
                    await websocket.send_text(json.dumps({"error": "Game not found"}))

            # ---------- CHALLENGE ---------- #
            elif msg_type == "challenge":
                target_uid = message.get("to")
                if target_uid in connected_users:
                    await connected_users[target_uid].send_text(json.dumps({
                        "type": "challenge_received",
                        "from": uid,
                        "from_name": name
                    }))

            # ---------- CHALLENGE RESPONSE ---------- #
            elif msg_type == "challenge_response":
                from_uid = message.get("from")
                accepted = message.get("accepted")

                if accepted:
                    game_id = create_game(from_uid, uid)
                    for player in [from_uid, uid]:
                        if player in connected_users:
                            await connected_users[player].send_text(json.dumps({
                                "type": "game_start",
                                "game_id": game_id,
                                "players": [from_uid, uid]
                            }))
                else:
                    # Notify challenger of decline
                    if from_uid in connected_users:
                        await connected_users[from_uid].send_text(json.dumps({
                            "type": "challenge_declined",
                            "by": uid,
                            "by_name": name
                        }))

            # ---------- MOVE ---------- #
            elif msg_type == "move":
                game_id = message.get("game_id")
                index = message.get("index")

                result = make_move(game_id, uid, index)

                if "error" in result:
                    await websocket.send_text(json.dumps(result))
                    continue

                board = result["board"]
                players = result["players"]
                winner = check_winner(board)

                # ---------- GAME RESULT ---------- #
                if winner:
                    p1, p2 = players[0], players[1]
                    r1 = get_user_rating(p1)
                    r2 = get_user_rating(p2)

                    if winner == "X":
                        new_r1, new_r2 = compute_elo(r1, r2, 1)
                    elif winner == "O":
                        new_r1, new_r2 = compute_elo(r1, r2, 0)
                    elif winner == "DRAW":
                        new_r1, new_r2 = compute_elo(r1, r2, 0.5)

                    update_user_rating(p1, new_r1)
                    update_user_rating(p2, new_r2)

                # ---------- BROADCAST ---------- #
                for player in rooms.get(game_id, []):
                    if player in connected_users:
                        await connected_users[player].send_text(json.dumps({
                            "type": "game_update",
                            "board": board,
                            "turn": result["turn"],
                            "players": players,
                            "winner": winner
                        }))

                # ---------- CLEANUP ---------- #
                if winner:
                    for p in players:
                        player_game_map.pop(p, None)
                    rooms.pop(game_id, None)
                    games.pop(game_id, None)

    except WebSocketDisconnect:
        print(f"{uid} disconnected")
        set_user_offline(uid)
        disconnect_user(uid)
        await broadcast_users()

        game_id = player_game_map.get(uid)
        if game_id:
            # Wait 5 seconds in case player is just navigating to game page
            await asyncio.sleep(5)

            # If player reconnected, skip forfeit
            if uid in connected_users:
                print(f"{uid} reconnected, skipping forfeit")
                return

            # Player truly disconnected - forfeit
            players = rooms.get(game_id, [])
            opponent = next((p for p in players if p != uid), None)

            if opponent and opponent in connected_users:
                await connected_users[opponent].send_text(json.dumps({
                    "type": "game_over",
                    "reason": "opponent_disconnected",
                    "winner": opponent
                }))

            if len(players) == 2:
                p1, p2 = players[0], players[1]
                r1 = get_user_rating(p1)
                r2 = get_user_rating(p2)
                if opponent == p1:
                    new_r1, new_r2 = compute_elo(r1, r2, 1)
                else:
                    new_r1, new_r2 = compute_elo(r1, r2, 0)
                update_user_rating(p1, new_r1)
                update_user_rating(p2, new_r2)

            for p in players:
                player_game_map.pop(p, None)
            rooms.pop(game_id, None)
            games.pop(game_id, None)