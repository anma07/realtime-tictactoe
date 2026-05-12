async function loadLeaderboard() {
    try {
        const res = await fetch("http://<YOUR_IP>:8000/leaderboard");
        const data = await res.json();

        const table = document.getElementById("table");
        table.innerHTML = "";

        if (data.length === 0) {
            table.innerHTML = "<tr><td colspan='3' style='text-align:center;padding:30px;'>No players yet</td></tr>";
            return;
        }

        data.forEach((user, index) => {
            const row = document.createElement("tr");

            let rankDisplay = index + 1;
            if (index === 0) rankDisplay = "🥇 " + rankDisplay;
            else if (index === 1) rankDisplay = "🥈 " + rankDisplay;
            else if (index === 2) rankDisplay = "🥉 " + rankDisplay;

            row.innerHTML = `
                <td class="rank">${rankDisplay}</td>
                <td>${user.name}</td>
                <td><strong>${user.elo}</strong></td>
            `;

            table.appendChild(row);
        });
    } catch (error) {
        console.error("Error loading leaderboard:", error);
        const table = document.getElementById("table");
        table.innerHTML = "<tr><td colspan='3' style='text-align:center;padding:30px;color:red;'>Error loading leaderboard</td></tr>";
    }
}

loadLeaderboard();