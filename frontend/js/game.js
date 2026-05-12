const params = new URLSearchParams(window.location.search);
const uid = params.get("uid");
const gameId = params.get("game_id");
// players array passed from lobby redirect; fallback to null
let gamePlayers = null;
try {
    const raw = params.get("players");
    if (raw) gamePlayers = JSON.parse(decodeURIComponent(raw));
} catch (e) { /* will be set from first server message */ }

console.log("UID:", uid, "GAME:", gameId);

if (!uid || !gameId) {
    alert("Missing game parameters. Redirecting to lobby...");
    window.location.href = `lobby.html?uid=${uid || ''}`;
}

const ws = new WebSocket(`ws://<YOUR_IP>:8000/ws/${uid}`);

let currentBoard = ["", "", "", "", "", "", "", "", ""];
let currentTurn = null;

function sendMove(index) {
    if (currentBoard[index] !== "") {
        alert("Cell already occupied!");
        return;
    }
    if (currentTurn !== uid) {
        alert("Not your turn!");
        return;
    }
    ws.send(JSON.stringify({
        type: "move",
        game_id: gameId,
        index: index
    }));
}

function renderBoard(board) {
    const boardDiv = document.getElementById("board");
    boardDiv.innerHTML = "";
    currentBoard = board;

    board.forEach((cell, index) => {
        const btn = document.createElement("button");

        btn.innerText = cell || "";

        btn.className = "cell";

        if (cell === "X") {
            btn.classList.add("x");
        } else if (cell === "O") {
            btn.classList.add("o");
        }

        if (cell === "") {
            btn.onclick = () => sendMove(index);
        } else {
            btn.disabled = true;
        }

        boardDiv.appendChild(btn);
    });
}

function updateStatus(turn, winner, players) {
    const status = document.getElementById("status");

    if (winner) {
        if (winner === "DRAW") {
            status.innerText = "Game Over: DRAW!";
            status.style.color = "#FFA500";
        } else {
            // players[0] is X, players[1] is O
            const iAmX = players && players[0] === uid;
            const xWon = winner === "X";
            const iWon = (iAmX && xWon) || (!iAmX && !xWon);

            status.innerText = iWon ? "🎉 You Won!" : "😢 You Lost!";
            status.style.color = iWon ? "#4CAF50" : "#F44336";
        }

        setTimeout(() => {
            window.location.href = `lobby.html?uid=${uid}`;
        }, 3000);
    } else {
        if (turn === uid) {
            status.innerText = "Your turn!";
            status.style.color = "#2196F3";
        } else {
            status.innerText = "Waiting for opponent...";
            status.style.color = "#9E9E9E";
        }
    }
}

ws.onopen = () => {
    console.log("Game WebSocket connected");
    // Small delay to let server register the connection
    setTimeout(() => {
        ws.send(JSON.stringify({
            type: "get_game_state",
            game_id: gameId
        }));
    }, 800);
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("GAME MESSAGE:", data);

    if (data.type === "game_update" || data.type === "game_state") {
        if (data.players) gamePlayers = data.players;
        renderBoard(data.board);
        currentTurn = data.turn;
        updateStatus(data.turn, data.winner, gamePlayers);
    }

    if (data.type === "game_over") {
        alert("Opponent disconnected. You win!");
        setTimeout(() => {
            window.location.href = `lobby.html?uid=${uid}`;
        }, 1000);
    }

    if (data.error) {
        console.error("Game error:", data.error);
        // Don't alert on every error — just log it
    }
};

ws.onerror = (error) => {
    console.error("WebSocket error:", error);
    document.getElementById("status").innerText = "Connection error — check backend is running.";
};

ws.onclose = () => {
    console.log("WebSocket closed");
};