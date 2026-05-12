games = {}
rooms = {}
player_game_map = {}

def create_game(p1, p2):
    game_id = f"{p1}_{p2}"
    
    games[game_id] = {
        "players": [p1, p2],
        "board": [""] * 9,
        "turn": p1
    }

    rooms[game_id] = [p1, p2]
    player_game_map[p1] = game_id
    player_game_map[p2] = game_id
    
    # Also register the reverse ID so either player can look it up
    reverse_id = f"{p2}_{p1}"
    games[reverse_id] = games[game_id]
    rooms[reverse_id] = rooms[game_id]
    
    return game_id

def make_move(game_id, player, index):
    game = games.get(game_id)

    if not game:
        return {"error": "Game not found"}

    if game["turn"] != player:
        return {"error": "Not your turn"}

    if game["board"][index] != "":
        return {"error": "Cell occupied"}

    symbol = "X" if game["players"][0] == player else "O"
    game["board"][index] = symbol

    game["turn"] = (
        game["players"][1]
        if player == game["players"][0]
        else game["players"][0]
    )

    return game


def check_winner(board):
    wins = [
        [0,1,2],[3,4,5],[6,7,8],
        [0,3,6],[1,4,7],[2,5,8],
        [0,4,8],[2,4,6]
    ]

    for a,b,c in wins:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]

    if "" not in board:
        return "DRAW"

    return None

def compute_elo(r1, r2, result1, K=32):

    e1 = 1 / (1 + 10 ** ((r2 - r1) / 400))# expected scores
    e2 = 1 / (1 + 10 ** ((r1 - r2) / 400))

    r1_new = r1 + K * (result1 - e1)# new ratings
    r2_new = r2 + K * ((1 - result1) - e2)

    return int(r1_new), int(r2_new)