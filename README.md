## To Run The Project

First Clone the Project

```bash 
git clone git@github.com:CS6201/project-sandwhich.git
```

### 1. Setup Environment Variables

Create a `.env` file in the root directory and add:

```bash
MONGO_URI=your_mongodb_connection_string
```

### 2. Setup Databases

#### MySQL
- Ensure MySQL is running.
- Update credentials in `database/sql.py`:
  - host
  - user
  - password
  - database

#### MongoDB
- Use MongoDB Atlas and paste the connection string in `.env`.

### 3. Install Dependencies
```bash
uv sync
```

### 4. Populate Databases (Scraper)

Place `batch_data.csv` in the root directory.

Run:

```bash
uv run python -m utils.scraper
```

This will:

- Insert user metadata into MySQL
- Store profile images in MongoDB

### 5. Configure Frontend

Update the backend IP address in all JS files inside `js/`:

- `login.js` 
- `lobby.js` 
- `game.js` 
- `leaderboard.js` 

### 6. Start Backend Server

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

### 7. Start Frontend Server

```bash
python -m http.server 5500
```

### 8. Access Application

Open in browser:

```bash
http://<YOUR_IP>:5500/public/login.html
```

### Notes:

- Ensure both servers are running simultaneously.

- Scraper must be run before login (database must be populated).

- All users are authenticated using facial recognition only.

Enjoy!

## Project Overview

This project is a real-time multiplayer Tic-Tac-Toe system with:
- Facial recognition-based login
- MySQL for structured user data
- MongoDB for profile images
- WebSocket-based real-time lobby and gameplay
- Elo rating system for leaderboard