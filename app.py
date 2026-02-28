from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import os
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'cricscore_secret_2024'

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

# ─── DB INIT ──────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name TEXT NOT NULL,
                player_count INTEGER DEFAULT 11
            );
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER,
                player_name TEXT NOT NULL,
                runs INTEGER DEFAULT 0,
                balls INTEGER DEFAULT 0,
                wickets INTEGER DEFAULT 0,
                fours INTEGER DEFAULT 0,
                sixes INTEGER DEFAULT 0,
                is_out INTEGER DEFAULT 0,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            );
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team1 TEXT NOT NULL,
                team2 TEXT NOT NULL,
                overs INTEGER NOT NULL,
                format TEXT DEFAULT 'real',
                total_runs INTEGER DEFAULT 0,
                total_wickets INTEGER DEFAULT 0,
                extras INTEGER DEFAULT 0,
                wides INTEGER DEFAULT 0,
                no_balls INTEGER DEFAULT 0,
                balls_bowled INTEGER DEFAULT 0,
                result TEXT DEFAULT 'In Progress',
                created_at TEXT,
                current_batting_team TEXT DEFAULT '',
                current_bowling_team TEXT DEFAULT '',
                innings INTEGER DEFAULT 1,
                target INTEGER DEFAULT 0,
                team1_score INTEGER DEFAULT 0,
                team1_wickets INTEGER DEFAULT 0,
                team1_balls INTEGER DEFAULT 0,
                team2_score INTEGER DEFAULT 0,
                team2_wickets INTEGER DEFAULT 0,
                team2_balls INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS ball_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER,
                over_number INTEGER,
                ball_number INTEGER,
                batsman_id INTEGER,
                bowler_id INTEGER,
                event_type TEXT,
                runs INTEGER DEFAULT 0,
                created_at TEXT,
                FOREIGN KEY (match_id) REFERENCES matches(id)
            );
            INSERT OR IGNORE INTO users (id, username, password) VALUES (1, '123', '123');
        ''')
    print("✅ Database initialized")

# ─── AUTH ─────────────────────────────────────────────────────────────────────

def is_admin():
    return session.get('logged_in') is True

def validate_input(text, field_name):
    if not text or len(text.strip()) == 0:
        raise ValueError(f"{field_name} cannot be empty")
    if not re.match(r'^[A-Za-z0-9 _\-\.]+$', text.strip()):
        raise ValueError(f"{field_name} contains invalid characters")
    return text.strip()

# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    db = get_db()
    matches = db.execute(
        "SELECT * FROM matches ORDER BY id DESC LIMIT 5"
    ).fetchall()
    active_match = db.execute(
        "SELECT * FROM matches WHERE result='In Progress' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    db.close()
    return render_template('index.html', matches=matches, active_match=active_match, is_admin=is_admin())

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?", (username, password)
        ).fetchone()
        db.close()
        if user:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not is_admin():
        return redirect(url_for('login'))
    db = get_db()
    active_match = db.execute(
        "SELECT * FROM matches WHERE result='In Progress' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    db.close()
    return render_template('dashboard.html', active_match=active_match)

@app.route('/setup_match', methods=['POST'])
def setup_match():
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        fmt = request.form.get('format', 'real')
        team1 = validate_input(request.form.get('team1', ''), 'Team 1')
        team2 = validate_input(request.form.get('team2', ''), 'Team 2')
        overs = int(request.form.get('overs', 20))
        player_count = 11 if fmt == 'real' else 9

        if overs < 1 or overs > 50:
            raise ValueError("Overs must be between 1 and 50")

        db = get_db()
        # Close any existing active match
        db.execute("UPDATE matches SET result='Abandoned' WHERE result='In Progress'")

        # Create teams
        db.execute("DELETE FROM teams WHERE team_name=? OR team_name=?", (team1, team2))
        c1 = db.execute("INSERT INTO teams (team_name, player_count) VALUES (?,?)", (team1, player_count))
        team1_id = c1.lastrowid
        c2 = db.execute("INSERT INTO teams (team_name, player_count) VALUES (?,?)", (team2, player_count))
        team2_id = c2.lastrowid

        # Create default players
        for i in range(1, player_count + 1):
            db.execute("INSERT INTO players (team_id, player_name) VALUES (?,?)", (team1_id, f"{team1} Player {i}"))
        for i in range(1, player_count + 1):
            db.execute("INSERT INTO players (team_id, player_name) VALUES (?,?)", (team2_id, f"{team2} Player {i}"))

        # Create match
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        m = db.execute(
            """INSERT INTO matches (team1, team2, overs, format, result, created_at,
               current_batting_team, current_bowling_team, innings)
               VALUES (?,?,?,?,'In Progress',?,?,?,1)""",
            (team1, team2, overs, fmt, now, team1, team2)
        )
        match_id = m.lastrowid
        db.commit()
        db.close()
        session['match_id'] = match_id
        session['team1_id'] = team1_id
        session['team2_id'] = team2_id
        return redirect(url_for('scoreboard'))
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/scoreboard')
def scoreboard():
    db = get_db()
    match_id = session.get('match_id')
    match = None
    players_bat = []
    players_bowl = []
    team1_players = []
    team2_players = []
    current_batsman = None
    current_bowler = None

    if match_id:
        match = db.execute("SELECT * FROM matches WHERE id=?", (match_id,)).fetchone()

    if not match:
        match = db.execute("SELECT * FROM matches WHERE result='In Progress' ORDER BY id DESC LIMIT 1").fetchone()
        if match:
            session['match_id'] = match['id']

    if match:
        team1_id = db.execute("SELECT id FROM teams WHERE team_name=?", (match['team1'],)).fetchone()
        team2_id = db.execute("SELECT id FROM teams WHERE team_name=?", (match['team2'],)).fetchone()

        if team1_id:
            team1_players = db.execute("SELECT * FROM players WHERE team_id=?", (team1_id['id'],)).fetchall()
            session['team1_id'] = team1_id['id']
        if team2_id:
            team2_players = db.execute("SELECT * FROM players WHERE team_id=?", (team2_id['id'],)).fetchall()
            session['team2_id'] = team2_id['id']

        if match['innings'] == 1:
            players_bat = team1_players
            players_bowl = team2_players
        else:
            players_bat = team2_players
            players_bowl = team1_players

        bid = session.get('current_batsman_id')
        bwid = session.get('current_bowler_id')
        if bid:
            current_batsman = db.execute("SELECT * FROM players WHERE id=?", (bid,)).fetchone()
        if bwid:
            current_bowler = db.execute("SELECT * FROM players WHERE id=?", (bwid,)).fetchone()

    db.close()
    return render_template('scoreboard.html',
        match=match,
        team1_players=team1_players,
        team2_players=team2_players,
        players_bat=players_bat,
        players_bowl=players_bowl,
        current_batsman=current_batsman,
        current_bowler=current_bowler,
        is_admin=is_admin()
    )

@app.route('/add_event', methods=['POST'])
def add_event():
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        data = request.json
        match_id = session.get('match_id')
        if not match_id:
            return jsonify({'error': 'No active match'}), 400

        event_type = data.get('event_type')
        batsman_id = data.get('batsman_id')
        bowler_id = data.get('bowler_id')

        if batsman_id:
            session['current_batsman_id'] = batsman_id
        if bowler_id:
            session['current_bowler_id'] = bowler_id

        db = get_db()
        match = db.execute("SELECT * FROM matches WHERE id=?", (match_id,)).fetchone()
        if not match or match['result'] != 'In Progress':
            db.close()
            return jsonify({'error': 'Match not active'}), 400

        innings = match['innings']
        score_key = f'team{innings}_score'
        wkt_key = f'team{innings}_wickets'
        balls_key = f'team{innings}_balls'

        total_runs = match[score_key]
        total_wickets = match[wkt_key]
        balls_bowled = match[balls_key]
        extras = match['extras']
        wides = match['wides']
        no_balls = match['no_balls']
        max_balls = match['overs'] * 6
        player_count = 11 if match['format'] == 'real' else 9

        runs_added = 0
        is_extra = False
        ball_counts = True

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        over_num = balls_bowled // 6
        ball_num = balls_bowled % 6

        if event_type == 'wicket':
            total_wickets += 1
            balls_bowled += 1
            ball_num += 1
            if batsman_id:
                db.execute("UPDATE players SET is_out=1 WHERE id=?", (batsman_id,))
                db.execute("UPDATE players SET balls=balls+1 WHERE id=?", (batsman_id,))
            if bowler_id:
                db.execute("UPDATE players SET wickets=wickets+1 WHERE id=?", (bowler_id,))
        elif event_type == 'wide':
            runs_added = 1
            total_runs += 1
            extras += 1
            wides += 1
            ball_counts = False
        elif event_type == 'no_ball':
            runs_added = 1
            total_runs += 1
            extras += 1
            no_balls += 1
            ball_counts = False
        else:
            runs_added = int(event_type) if event_type.isdigit() else 0
            total_runs += runs_added
            balls_bowled += 1
            if batsman_id:
                db.execute("UPDATE players SET runs=runs+?, balls=balls+1 WHERE id=?", (runs_added, batsman_id))
                if runs_added == 4:
                    db.execute("UPDATE players SET fours=fours+1 WHERE id=?", (batsman_id,))
                if runs_added == 6:
                    db.execute("UPDATE players SET sixes=sixes+1 WHERE id=?", (batsman_id,))

        db.execute(
            "INSERT INTO ball_events (match_id, over_number, ball_number, batsman_id, bowler_id, event_type, runs, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (match_id, over_num, ball_num, batsman_id, bowler_id, event_type, runs_added, now)
        )

        # Check innings end
        innings_ended = False
        result = 'In Progress'
        if balls_bowled >= max_balls or total_wickets >= player_count - 1:
            innings_ended = True

        if innings_ended and innings == 1:
            # End first innings, start second
            db.execute(f"""UPDATE matches SET
                team1_score=?, team1_wickets=?, team1_balls=?,
                extras=?, wides=?, no_balls=?,
                innings=2, target=?, current_batting_team=team2, current_bowling_team=team1,
                team2_balls=0, team2_score=0, team2_wickets=0
                WHERE id=?""",
                (total_runs, total_wickets, balls_bowled, extras, wides, no_balls, total_runs + 1, match_id))
            db.commit()
            db.close()
            return jsonify({
                'status': 'innings_end',
                'innings': 1,
                'score': total_runs,
                'wickets': total_wickets,
                'message': f'Innings Over! Target: {total_runs + 1} runs'
            })

        if innings_ended and innings == 2:
            team1_score = match['team1_score']
            if total_runs > team1_score:
                winner = match['current_batting_team']
                wickets_left = (player_count - 1) - total_wickets
                result = f"{winner} won by {wickets_left} wickets"
            elif total_runs == team1_score:
                result = "Match Tied"
            else:
                winner = match['current_bowling_team']
                diff = team1_score - total_runs
                result = f"{winner} won by {diff} runs"

            db.execute(f"""UPDATE matches SET
                team2_score=?, team2_wickets=?, team2_balls=?,
                extras=?, wides=?, no_balls=?,
                total_runs=?, total_wickets=?, result=?
                WHERE id=?""",
                (total_runs, total_wickets, balls_bowled, extras, wides, no_balls, total_runs, total_wickets, result, match_id))
            db.commit()
            db.close()
            return jsonify({
                'status': 'match_end',
                'result': result,
                'score': total_runs,
                'wickets': total_wickets
            })

        # Normal update
        db.execute(f"""UPDATE matches SET
            {score_key}=?, {wkt_key}=?, {balls_key}=?,
            extras=?, wides=?, no_balls=?
            WHERE id=?""",
            (total_runs, total_wickets, balls_bowled, extras, wides, no_balls, match_id))

        # Check if chasing team has passed target (during innings 2)
        if innings == 2:
            if total_runs > match['team1_score']:
                winner = match['current_batting_team']
                wl = (player_count - 1) - total_wickets
                result = f"{winner} won by {wl} wickets"
                db.execute("UPDATE matches SET result=? WHERE id=?", (result, match_id))
                db.commit()
                db.close()
                return jsonify({'status': 'match_end', 'result': result, 'score': total_runs, 'wickets': total_wickets})

        db.commit()

        # Build response
        overs_display = f"{balls_bowled // 6}.{balls_bowled % 6}"
        run_rate = round(total_runs / (balls_bowled / 6), 2) if balls_bowled > 0 else 0.0

        bat_stats = None
        if batsman_id and event_type not in ['wide', 'no_ball']:
            p = db.execute("SELECT * FROM players WHERE id=?", (batsman_id,)).fetchone()
            if p:
                sr = round((p['runs'] / p['balls']) * 100, 1) if p['balls'] > 0 else 0
                bat_stats = {'name': p['player_name'], 'runs': p['runs'], 'balls': p['balls'], 'sr': sr, 'fours': p['fours'], 'sixes': p['sixes']}

        bowl_stats = None
        if bowler_id:
            bp = db.execute("SELECT * FROM players WHERE id=?", (bowler_id,)).fetchone()
            if bp:
                bowl_stats = {'name': bp['player_name'], 'wickets': bp['wickets']}

        db.close()
        return jsonify({
            'status': 'ok',
            'score': total_runs,
            'wickets': total_wickets,
            'overs': overs_display,
            'balls_bowled': balls_bowled,
            'extras': extras,
            'run_rate': run_rate,
            'bat_stats': bat_stats,
            'bowl_stats': bowl_stats,
            'innings': innings,
            'event_type': event_type
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/match_state')
def match_state():
    db = get_db()
    match_id = session.get('match_id')
    if not match_id:
        match = db.execute("SELECT * FROM matches WHERE result='In Progress' ORDER BY id DESC LIMIT 1").fetchone()
        if match:
            match_id = match['id']

    if not match_id:
        db.close()
        return jsonify({'error': 'No active match'})

    match = db.execute("SELECT * FROM matches WHERE id=?", (match_id,)).fetchone()
    if not match:
        db.close()
        return jsonify({'error': 'Match not found'})

    innings = match['innings']
    sk = f'team{innings}_score'
    wk = f'team{innings}_wickets'
    bk = f'team{innings}_balls'

    balls = match[bk]
    score = match[sk]
    wickets = match[wk]
    overs_str = f"{balls // 6}.{balls % 6}"
    rr = round(score / (balls / 6), 2) if balls > 0 else 0.0

    db.close()
    return jsonify({
        'team1': match['team1'],
        'team2': match['team2'],
        'score': score,
        'wickets': wickets,
        'overs': overs_str,
        'run_rate': rr,
        'extras': match['extras'],
        'result': match['result'],
        'innings': innings,
        'target': match['target'],
        'team1_score': match['team1_score'],
        'team1_wickets': match['team1_wickets'],
        'current_batting': match['current_batting_team'],
        'current_bowling': match['current_bowling_team'],
        'max_overs': match['overs']
    })

@app.route('/api/leaderboard')
def leaderboard():
    db = get_db()
    batsmen = db.execute(
        "SELECT p.player_name, t.team_name, p.runs, p.balls, p.fours, p.sixes FROM players p JOIN teams t ON p.team_id=t.id WHERE p.balls>0 ORDER BY p.runs DESC LIMIT 10"
    ).fetchall()
    bowlers = db.execute(
        "SELECT p.player_name, t.team_name, p.wickets FROM players p JOIN teams t ON p.team_id=t.id WHERE p.wickets>0 ORDER BY p.wickets DESC LIMIT 10"
    ).fetchall()
    history = db.execute(
        "SELECT * FROM matches WHERE result != 'In Progress' ORDER BY id DESC LIMIT 10"
    ).fetchall()
    db.close()
    return jsonify({
        'batsmen': [dict(b) for b in batsmen],
        'bowlers': [dict(b) for b in bowlers],
        'history': [dict(m) for m in history]
    })

@app.route('/reset_match', methods=['POST'])
def reset_match():
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    db = get_db()
    db.execute("UPDATE matches SET result='Abandoned' WHERE result='In Progress'")
    db.commit()
    db.close()
    session.pop('match_id', None)
    session.pop('current_batsman_id', None)
    session.pop('current_bowler_id', None)
    return jsonify({'status': 'ok'})

@app.route('/leaderboard')
def leaderboard_page():
    db = get_db()
    matches = db.execute("SELECT * FROM matches ORDER BY id DESC LIMIT 20").fetchall()
    db.close()
    return render_template('leaderboard.html', matches=matches)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
