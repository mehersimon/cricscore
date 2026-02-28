// CricScore Main JS

const CS = {
  ballLog: [],
  matchState: null,
  isAdmin: false,

  init() {
    this.isAdmin = document.body.dataset.admin === 'true';
    this.bindEvents();
    if (document.getElementById('score-display')) {
      this.startPolling();
    }
  },

  // ─── TOAST ────────────────────────────────────────────────────────────────
  showToast(msg, type = 'success', duration = 3000) {
    let toast = document.getElementById('global-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'global-toast';
      toast.className = 'toast';
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.className = `toast ${type}`;
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => toast.classList.remove('show'), duration);
  },

  // ─── BALL LOG ─────────────────────────────────────────────────────────────
  addBallToTrack(event) {
    const track = document.getElementById('ball-track');
    if (!track) return;
    const dot = document.createElement('div');
    let cls = 'b-' + event;
    let label = event;
    if (event === 'wicket') { cls = 'b-W'; label = 'W'; }
    if (event === 'wide') { cls = 'b-Wd'; label = 'Wd'; }
    if (event === 'no_ball') { cls = 'b-Nb'; label = 'Nb'; }
    dot.className = `ball-dot ${cls}`;
    dot.textContent = label;
    track.appendChild(dot);
    this.ballLog.push(event);

    // Over separator every 6 valid balls
    const validBalls = this.ballLog.filter(b => b !== 'wide' && b !== 'no_ball').length;
    if (validBalls > 0 && validBalls % 6 === 0) {
      const sep = document.createElement('div');
      sep.style.cssText = 'width:2px;height:32px;background:rgba(0,230,118,0.3);border-radius:2px;margin:0 2px;flex-shrink:0;';
      track.appendChild(sep);
    }
    track.scrollLeft = track.scrollWidth;
  },

  // ─── SCORE UPDATE ──────────────────────────────────────────────────────────
  updateScoreDisplay(data) {
    const el = id => document.getElementById(id);
    if (el('score-display')) {
      el('score-display').textContent = `${data.score}/${data.wickets}`;
      el('score-display').classList.add('updated');
      setTimeout(() => el('score-display')?.classList.remove('updated'), 600);
    }
    if (el('overs-val')) el('overs-val').textContent = data.overs;
    if (el('rr-val')) el('rr-val').textContent = data.run_rate;
    if (el('extras-val')) el('extras-val').textContent = data.extras;
    if (el('innings-label')) el('innings-label').textContent = `Innings ${data.innings}`;
    if (data.innings === 2 && data.target && el('target-val')) {
      el('target-val').textContent = `Target: ${data.target} | Need: ${data.target - data.score} off ${(data.max_overs * 6) - (data.balls_bowled || 0)} balls`;
    }

    if (data.bat_stats) {
      if (el('bat-name')) el('bat-name').textContent = data.bat_stats.name;
      if (el('bat-runs')) el('bat-runs').textContent = data.bat_stats.runs;
      if (el('bat-balls')) el('bat-balls').textContent = data.bat_stats.balls;
      if (el('bat-sr')) el('bat-sr').textContent = data.bat_stats.sr;
      if (el('bat-fours')) el('bat-fours').textContent = data.bat_stats.fours;
      if (el('bat-sixes')) el('bat-sixes').textContent = data.bat_stats.sixes;
    }
  },

  // ─── SEND EVENT ──────────────────────────────────────────────────────────
  async sendEvent(eventType) {
    const batsman = document.getElementById('batsman-select')?.value;
    const bowler = document.getElementById('bowler-select')?.value;

    if (!batsman || !bowler) {
      this.showToast('⚠ Select batsman and bowler first!', 'error');
      return;
    }

    const btns = document.querySelectorAll('.event-btn');
    btns.forEach(b => b.disabled = true);

    try {
      const res = await fetch('/add_event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_type: eventType, batsman_id: batsman, bowler_id: bowler })
      });

      const data = await res.json();

      if (data.error) {
        this.showToast('❌ ' + data.error, 'error');
        return;
      }

      this.addBallToTrack(eventType);
      this.updateScoreDisplay(data);

      // Feedback messages
      if (eventType === '4') this.showToast('🔵 FOUR! Great shot!', 'info');
      else if (eventType === '6') this.showToast('🟡 SIX! Magnificent!', 'info');
      else if (eventType === 'wicket') this.showToast('🔴 WICKET!', 'error');
      else if (eventType === 'wide') this.showToast('🟠 Wide ball — extra run', 'info');
      else if (eventType === 'no_ball') this.showToast('🟠 No ball — extra run', 'info');

      if (data.status === 'innings_end') {
        this.showToast(`🏁 ${data.message}`, 'info', 5000);
        setTimeout(() => location.reload(), 2000);
      }

      if (data.status === 'match_end') {
        this.showMatchResult(data.result);
      }

    } catch (e) {
      this.showToast('Connection error', 'error');
    } finally {
      btns.forEach(b => b.disabled = false);
    }
  },

  // ─── MATCH RESULT ────────────────────────────────────────────────────────
  showMatchResult(result) {
    const container = document.getElementById('result-container');
    if (container) {
      container.innerHTML = `
        <div class="result-banner">
          <div style="font-size:2rem;margin-bottom:8px;">🏆</div>
          <div class="result-text">${result}</div>
          <div style="color:var(--muted);margin-top:8px;font-family:Rajdhani;letter-spacing:1px;">MATCH COMPLETE</div>
        </div>`;
    }
    this.showToast('🏆 ' + result, 'success', 8000);

    // Confetti-like animation
    for (let i = 0; i < 30; i++) {
      setTimeout(() => this.spawnConfetti(), i * 80);
    }
  },

  spawnConfetti() {
    const c = document.createElement('div');
    const colors = ['#00e676', '#ffd700', '#ff5252', '#42a5f5'];
    c.style.cssText = `position:fixed;top:-10px;left:${Math.random()*100}%;width:8px;height:8px;background:${colors[Math.floor(Math.random()*colors.length)]};border-radius:50%;animation:confettiFall 1.5s ease forwards;z-index:9999;`;
    document.body.appendChild(c);
    setTimeout(() => c.remove(), 2000);
  },

  // ─── RESET MATCH ─────────────────────────────────────────────────────────
  async resetMatch() {
    if (!confirm('Reset current match? This cannot be undone.')) return;
    const res = await fetch('/reset_match', { method: 'POST' });
    const data = await res.json();
    if (data.status === 'ok') {
      this.showToast('Match reset', 'success');
      setTimeout(() => window.location.href = '/dashboard', 1000);
    }
  },

  // ─── POLLING ──────────────────────────────────────────────────────────────
  startPolling() {
    if (this.isAdmin) return; // Admins update live, no need to poll
    setInterval(async () => {
      try {
        const res = await fetch('/api/match_state');
        const data = await res.json();
        if (!data.error) {
          const el = id => document.getElementById(id);
          if (el('score-display')) el('score-display').textContent = `${data.score}/${data.wickets}`;
          if (el('overs-val')) el('overs-val').textContent = data.overs;
          if (el('rr-val')) el('rr-val').textContent = data.run_rate;
          if (el('extras-val')) el('extras-val').textContent = data.extras;
        }
      } catch (_) {}
    }, 5000);
  },

  // ─── LEADERBOARD ──────────────────────────────────────────────────────────
  async loadLeaderboard() {
    const container = document.getElementById('leaderboard-data');
    if (!container) return;
    try {
      const res = await fetch('/api/leaderboard');
      const data = await res.json();

      let html = `
        <div class="two-col" style="gap:1.5rem">
          <div class="card">
            <div class="card-header"><span class="card-title">⚡ Top Batsmen</span></div>
            ${data.batsmen.length === 0 ? '<p style="color:var(--muted);text-align:center;padding:1rem">No data yet</p>' : ''}
            ${data.batsmen.map((b, i) => `
              <div class="leaderboard-item">
                <div class="lb-rank rank-${i+1}">${i+1}</div>
                <div class="lb-info">
                  <div class="lb-name">${b.player_name}</div>
                  <div class="lb-team">${b.team_name} • ${b.fours || 0} fours, ${b.sixes || 0} sixes</div>
                </div>
                <div class="lb-score">${b.runs}</div>
              </div>`).join('')}
          </div>
          <div class="card">
            <div class="card-header"><span class="card-title">🎯 Top Bowlers</span></div>
            ${data.bowlers.length === 0 ? '<p style="color:var(--muted);text-align:center;padding:1rem">No data yet</p>' : ''}
            ${data.bowlers.map((b, i) => `
              <div class="leaderboard-item">
                <div class="lb-rank rank-${i+1}">${i+1}</div>
                <div class="lb-info">
                  <div class="lb-name">${b.player_name}</div>
                  <div class="lb-team">${b.team_name}</div>
                </div>
                <div class="lb-score" style="color:var(--red)">${b.wickets}W</div>
              </div>`).join('')}
          </div>
        </div>
        <div class="card" style="margin-top:1.5rem">
          <div class="card-header"><span class="card-title">📋 Match History</span></div>
          ${data.history.length === 0 ? '<p style="color:var(--muted);text-align:center;padding:1rem">No completed matches yet</p>' : ''}
          ${data.history.map(m => `
            <div class="match-history-item">
              <div class="match-history-teams">${m.team1} <span style="color:var(--muted)">vs</span> ${m.team2}</div>
              <div class="match-history-result">${m.result}</div>
              <div class="match-history-date">${m.created_at || ''}</div>
            </div>`).join('')}
        </div>`;

      container.innerHTML = html;
    } catch (e) {
      container.innerHTML = '<p style="color:var(--red)">Failed to load leaderboard</p>';
    }
  },

  // ─── EVENTS ───────────────────────────────────────────────────────────────
  bindEvents() {
    // Format toggle
    document.querySelectorAll('.format-option input').forEach(radio => {
      radio.addEventListener('change', () => {
        const overs = document.getElementById('overs-input');
        if (overs) overs.value = radio.value === 'real' ? 20 : 10;
      });
    });

    // Keyboard shortcut hints
    document.addEventListener('keydown', e => {
      if (!this.isAdmin) return;
      const keyMap = { '0':'0','1':'1','2':'2','3':'3','4':'4','6':'6','w':'wicket','e':'wide','n':'no_ball' };
      const btn = document.querySelector(`.event-btn[data-key="${e.key}"]`);
      if (btn) btn.click();
    });
  }
};

// Confetti animation CSS
const confettiStyle = document.createElement('style');
confettiStyle.textContent = `
  @keyframes confettiFall {
    0% { transform: translateY(0) rotate(0deg); opacity: 1; }
    100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
  }
`;
document.head.appendChild(confettiStyle);

document.addEventListener('DOMContentLoaded', () => CS.init());
