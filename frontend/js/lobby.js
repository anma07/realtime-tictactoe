const params = new URLSearchParams(window.location.search);
const uid = params.get("uid");

console.log("UID:", uid);

if (!uid) {
    alert("UID missing. Go back and login again.");
    window.location.href = "login.html";
    throw new Error("No UID provided");
}

// Set leaderboard link with uid
const lbBtn = document.getElementById("leaderboardBtn");
if (lbBtn) lbBtn.onclick = () => window.location.href = `leaderboard.html?uid=${uid}`;

const ws = new WebSocket(`ws://<YOUR_IP>:8000/ws/${uid}`);

ws.onopen = () => {
    console.log("WS CONNECTED");
    // Ask server to re-broadcast current lobby state immediately
    ws.send(JSON.stringify({ type: "request_lobby" }));
    // Also poll every 5 seconds so new joiners appear without full reconnect
    setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "request_lobby" }));
        }
    }, 5000);
};

ws.onerror = (error) => {
    console.error("WebSocket error:", error);
    alert("Connection error. Please try again.");
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("MESSAGE:", data);

    // ── Lobby update ──────────────────────────────────────────────
    if (data.type === "lobby_update") {
        const usersDiv = document.getElementById("users");
        usersDiv.innerHTML = "";

        // data.users is now [{uid, name}, ...]
        const others = data.users.filter(u => u.uid !== uid);

        if (others.length === 0) {
            usersDiv.innerHTML = "<p>No other players online. Waiting for opponents...</p>";
            return;
        }

        others.forEach(user => {
            const btn = document.createElement("button");
            btn.innerText = `Challenge ${user.name}`;
            btn.className = "challenge-btn";
            btn.dataset.targetUid = user.uid;

            btn.onclick = () => {
                console.log("Challenging:", user.uid);
                ws.send(JSON.stringify({ type: "challenge", to: user.uid }));
                btn.disabled = true;
                btn.innerText = `Challenge sent to ${user.name}...`;
            };

            usersDiv.appendChild(btn);
        });
    }

    // ── Challenge received ─────────────────────────────────────────
    if (data.type === "challenge_received") {
        const accept = confirm(`Challenge from ${data.from_name || data.from}. Accept?`);
        ws.send(JSON.stringify({
            type: "challenge_response",
            from: data.from,
            accepted: accept
        }));
    }

    // ── Challenge declined ─────────────────────────────────────────
    if (data.type === "challenge_declined") {
        alert(`${data.by_name || data.by} declined your challenge.`);
        // Re-enable the button for that user
        document.querySelectorAll(".challenge-btn").forEach(btn => {
            if (btn.dataset.targetUid === data.by) {
                btn.disabled = false;
                btn.innerText = `Challenge ${btn.dataset.targetName || data.by}`;
            }
        });
    }

    // ── Game start ─────────────────────────────────────────────────
    if (data.type === "game_start") {
        console.log("Game starting:", data.game_id);
        window.location.href = `game.html?uid=${uid}&game_id=${encodeURIComponent(data.game_id)}&players=${encodeURIComponent(JSON.stringify(data.players))}`;
    }
};

ws.onclose = () => {
    console.log("WebSocket closed");
    const usersDiv = document.getElementById("users");
    if (usersDiv) usersDiv.innerHTML = "<p style='color:#c00'>Connection lost. Please <a href='login.html'>log in again</a>.</p>";
};