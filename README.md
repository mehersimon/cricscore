# 🏏 CricScore — Cricket Simulation & Management System

A full-stack web app for live cricket scoring, simulation, and match management.

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
python app.py
```

### 3. Open in browser
```
http://localhost:5000
```

---

## 🔐 Login Credentials
| Field    | Value |
|----------|-------|
| Login ID | `123` |
| Password | `123` |

---

## 📂 Project Structure
```
cricscore/
├── app.py                  # Flask app + all routes
├── requirements.txt
├── database.db             # Auto-created on first run
├── templates/
│   ├── base.html           # Navbar + layout
│   ├── index.html          # Home page
│   ├── login.html          # Admin login
│   ├── dashboard.html      # Match setup
│   ├── scoreboard.html     # Live scoreboard + controls
│   └── leaderboard.html    # Stats & history
├── static/
│   ├── css/style.css       # Dark cricket theme
│   └── js/main.js          # Live updates + ball events
└── models/
    ├── team.py             # Team OOP class
    ├── player.py           # Player OOP class
    └── match.py            # Match OOP class
```

---

## ✨ Features

### Public (No Login)
- Live scoreboard with auto-refresh
- Team scores, overs, run rate, wickets
- Match history & leaderboard

### Admin (ID: 123 / Pass: 123)
- Create new match (Real: 11 players / Short: 9 players)
- Select batsman & bowler per ball
- Ball events: 0, 1, 2, 3, 4, 6, Wicket, Wide, No Ball
- Auto-calculations: RR, SR, Extras, Target, Winner
- Reset match

### Auto-Calculated Stats
- Strike Rate = (Runs / Balls) × 100
- Run Rate = Total Runs / Overs
- Required Run Rate (2nd innings)
- Extras (Wides + No Balls)
- Automatic winner declaration

---

## ⌨️ Keyboard Shortcuts (Admin)
| Key | Action  |
|-----|---------|
| `0` | Dot ball |
| `1` | 1 Run |
| `2` | 2 Runs |
| `3` | 3 Runs |
| `4` | Four |
| `6` | Six |
| `w` | Wicket |
| `e` | Wide |
| `n` | No Ball |
