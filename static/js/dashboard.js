/**
 * ══════════════════════════════════════════════════════════════════
 * Momentum Shift Detector – Dashboard JavaScript
 * ══════════════════════════════════════════════════════════════════
 * Handles:
 *   - Match loading (sample / upload)
 *   - Ball-by-ball playback (auto-play + manual navigation)
 *   - Plotly chart updates (Momentum & Win Probability)
 *   - Ball feed panel rendering
 *   - Turning points timeline
 *   - Statistical cards updates
 *   - Momentum shift alerts
 */

// ── Global State ──────────────────────────────────────────────────
const state = {
    matchLoaded: false,
    currentInnings: 1,
    currentBallIndex: -1,
    totalBalls: { 1: 0, 2: 0 },
    isPlaying: false,
    playInterval: null,
    speed: 1000,          // ms between balls
    teams: { team1: '', team2: '' },
    target: 0,
    innings1Summary: null,
    matchSummary: null,
    lastShiftIndex: -1,   // track last shown shift
};

// ── Plotly Chart Config ───────────────────────────────────────────
const PLOTLY_LAYOUT_BASE = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { family: 'Inter, sans-serif', color: '#94a3b8', size: 11 },
    margin: { l: 45, r: 20, t: 10, b: 35 },
    xaxis: {
        gridcolor: 'rgba(255,255,255,0.04)',
        zeroline: false,
        title: { text: 'Over', font: { size: 10, color: '#64748b' } },
    },
    yaxis: {
        gridcolor: 'rgba(255,255,255,0.04)',
        zeroline: true,
        zerolinecolor: 'rgba(255,255,255,0.1)',
    },
    showlegend: true,
    legend: {
        orientation: 'h',
        x: 0.5,
        xanchor: 'center',
        y: 1.12,
        font: { size: 10, color: '#94a3b8' },
        bgcolor: 'rgba(0,0,0,0)',
    },
    hovermode: 'x unified',
};

const PLOTLY_CONFIG = {
    responsive: true,
    displayModeBar: false,
};

// ══════════════════════════════════════════════════════════════════
// INITIALIZATION
// ══════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    // Hide loading screen after a short delay
    setTimeout(() => {
        document.getElementById('loading-screen').classList.add('hidden');
    }, 800);

    // Setup innings tab listeners
    document.querySelectorAll('.innings-tab').forEach(tab => {
        tab.addEventListener('click', () => switchInnings(parseInt(tab.dataset.innings)));
    });

    // Initialize empty charts
    initCharts();
});


function initCharts() {
    // Momentum chart placeholder
    Plotly.newPlot('momentum-chart', [{
        x: [],
        y: [],
        type: 'scatter',
        mode: 'lines',
        line: { color: '#06d6a0', width: 2.5 },
        fill: 'tozeroy',
        fillcolor: 'rgba(6, 214, 160, 0.05)',
        name: 'Momentum Index',
    }], {
        ...PLOTLY_LAYOUT_BASE,
        yaxis: {
            ...PLOTLY_LAYOUT_BASE.yaxis,
            range: [-100, 100],
            title: { text: 'Momentum', font: { size: 10, color: '#64748b' } },
        },
        shapes: [{
            type: 'line',
            x0: 0, x1: 20,
            y0: 0, y1: 0,
            line: { color: 'rgba(255,255,255,0.15)', width: 1, dash: 'dash' },
        }],
    }, PLOTLY_CONFIG);

    // Win probability chart placeholder
    Plotly.newPlot('winprob-chart', [
        {
            x: [],
            y: [],
            type: 'scatter',
            mode: 'lines',
            line: { color: '#06d6a0', width: 2 },
            fill: 'tozeroy',
            fillcolor: 'rgba(6, 214, 160, 0.08)',
            name: 'Batting Team',
        },
        {
            x: [],
            y: [],
            type: 'scatter',
            mode: 'lines',
            line: { color: '#ef476f', width: 2 },
            fill: 'tozeroy',
            fillcolor: 'rgba(239, 71, 111, 0.08)',
            name: 'Bowling Team',
        },
    ], {
        ...PLOTLY_LAYOUT_BASE,
        yaxis: {
            ...PLOTLY_LAYOUT_BASE.yaxis,
            range: [0, 100],
            title: { text: 'Win %', font: { size: 10, color: '#64748b' } },
        },
    }, PLOTLY_CONFIG);
}


// ══════════════════════════════════════════════════════════════════
// MATCH LOADING
// ══════════════════════════════════════════════════════════════════

async function loadSampleMatch() {
    showLoadingState('Loading sample match...');
    try {
        const res = await fetch('/api/load-default', { method: 'POST' });
        const json = await res.json();
        if (json.error) throw new Error(json.error);
        onMatchLoaded(json);
    } catch (err) {
        alert('Failed to load sample match: ' + err.message);
        hideLoadingState();
    }
}


async function uploadFile(input) {
    if (!input.files || !input.files[0]) return;

    const file = input.files[0];
    const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
    showLoadingState(`Processing ${file.name} (${sizeMB} MB)...`);

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData });

        // Handle non-JSON responses (e.g., 413 from server)
        let json;
        const contentType = res.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
            json = await res.json();
        } else {
            // Server returned HTML error page (e.g., 413)
            if (res.status === 413) {
                throw new Error('File too large. Maximum upload size is 100 MB. Try a smaller dataset.');
            }
            throw new Error(`Server error (HTTP ${res.status}). Please check your CSV format.`);
        }

        if (json.error) {
            throw new Error(json.error);
        }

        onMatchLoaded(json);
    } catch (err) {
        hideLoadingState();
        // Show a user-friendly error
        const msg = err.message || 'Unknown error occurred';
        alert('Upload failed:\n\n' + msg);
    }
    input.value = '';
}


function onMatchLoaded(data) {
    state.matchLoaded = true;
    state.teams = data.teams;
    state.target = data.target;
    state.matchSummary = data.match_summary;

    // Determine total balls per innings
    state.totalBalls[1] = 0;
    state.totalBalls[2] = 0;

    // Fetch total balls for each innings
    Promise.all([
        fetch('/api/innings/1/balls?start=0&end=1').then(r => r.json()),
        fetch('/api/innings/2/balls?start=0&end=1').then(r => r.json()),
    ]).then(([inn1, inn2]) => {
        state.totalBalls[1] = inn1.total_balls || 0;
        state.totalBalls[2] = inn2.total_balls || 0;

        // Show dashboard
        document.getElementById('upload-section').style.display = 'none';
        document.getElementById('dashboard-section').style.display = 'block';
        document.getElementById('innings-tabs').style.display = 'flex';
        document.getElementById('btn-new-match').style.display = 'inline-flex';

        // Set team names
        document.getElementById('team-a-name').textContent = state.teams.team1;
        document.getElementById('team-b-name').textContent = state.teams.team2;

        // Initialize to innings 1
        switchInnings(1);
        hideLoadingState();
    });
}


function showUpload() {
    stopPlay();
    state.matchLoaded = false;
    state.currentBallIndex = -1;
    document.getElementById('upload-section').style.display = 'flex';
    document.getElementById('dashboard-section').style.display = 'none';
    document.getElementById('innings-tabs').style.display = 'none';
    document.getElementById('btn-new-match').style.display = 'none';
}


function showLoadingState(msg) {
    const screen = document.getElementById('loading-screen');
    screen.querySelector('.loading-text').textContent = msg || 'Loading...';
    screen.classList.remove('hidden');
}


function hideLoadingState() {
    document.getElementById('loading-screen').classList.add('hidden');
}


// ══════════════════════════════════════════════════════════════════
// INNINGS SWITCHING
// ══════════════════════════════════════════════════════════════════

function switchInnings(innings) {
    stopPlay();
    state.currentInnings = innings;
    state.currentBallIndex = -1;
    state.lastShiftIndex = -1;

    // Update tabs
    document.querySelectorAll('.innings-tab').forEach(tab => {
        tab.classList.toggle('active', parseInt(tab.dataset.innings) === innings);
    });

    // Update target display
    if (innings === 2) {
        document.getElementById('target-score').textContent = state.target;
        document.getElementById('current-rrr').parentElement.style.display = '';
    } else {
        document.getElementById('target-score').textContent = '—';
        document.getElementById('current-rrr').parentElement.style.display = innings === 1 ? 'none' : '';
    }

    // Reset displays
    resetDisplays();
    updateProgressBar();

    // Update innings 1 summary display if viewing innings 2
    if (innings === 2 && state.matchSummary) {
        document.getElementById('team-a-runs').textContent = state.matchSummary.innings1_total;
        document.getElementById('team-a-wickets').textContent = '/' + state.matchSummary.innings1_wickets;
        document.getElementById('team-a-overs').textContent = '(' + state.matchSummary.innings1_overs + ' ov)';
    }
}


function resetDisplays() {
    // Reset charts
    Plotly.restyle('momentum-chart', { x: [[]], y: [[]] }, [0]);
    Plotly.restyle('winprob-chart', { x: [[]], y: [[]] }, [0, 1]);

    // Reset feed and turning points
    document.getElementById('ball-feed').innerHTML =
        '<div class="empty-state"><div class="empty-icon">🏏</div><p>Press Play to start the match simulation</p></div>';
    document.getElementById('turning-points').innerHTML =
        '<div class="empty-state"><div class="empty-icon">🔍</div><p>Momentum shifts will appear here as the match progresses</p></div>';

    // Reset stats
    updateStatCards({});
    updateMomentumBar(0);

    // Reset header scores for current innings
    const innings = state.currentInnings;
    if (innings === 1) {
        document.getElementById('team-a-runs').textContent = '0';
        document.getElementById('team-a-wickets').textContent = '/0';
        document.getElementById('team-a-overs').textContent = '(0.0 ov)';
        document.getElementById('team-b-runs').textContent = '0';
        document.getElementById('team-b-wickets').textContent = '/0';
        document.getElementById('team-b-overs').textContent = '(0.0 ov)';
    } else {
        document.getElementById('team-b-runs').textContent = '0';
        document.getElementById('team-b-wickets').textContent = '/0';
        document.getElementById('team-b-overs').textContent = '(0.0 ov)';
    }

    document.getElementById('current-crr').textContent = '0.00';
    document.getElementById('current-rrr').textContent = '0.00';
}


// ══════════════════════════════════════════════════════════════════
// PLAYBACK CONTROLS
// ══════════════════════════════════════════════════════════════════

function togglePlay() {
    if (state.isPlaying) {
        stopPlay();
    } else {
        startPlay();
    }
}


function startPlay() {
    if (!state.matchLoaded) return;
    const total = state.totalBalls[state.currentInnings];
    if (state.currentBallIndex >= total - 1) return;

    state.isPlaying = true;
    document.getElementById('btn-play').textContent = '⏸';
    document.getElementById('btn-play').title = 'Pause';

    state.playInterval = setInterval(() => {
        if (state.currentBallIndex >= total - 1) {
            stopPlay();
            return;
        }
        nextBall();
    }, state.speed);
}


function stopPlay() {
    state.isPlaying = false;
    document.getElementById('btn-play').textContent = '▶';
    document.getElementById('btn-play').title = 'Play';
    if (state.playInterval) {
        clearInterval(state.playInterval);
        state.playInterval = null;
    }
}


function nextBall() {
    const total = state.totalBalls[state.currentInnings];
    if (state.currentBallIndex < total - 1) {
        state.currentBallIndex++;
        fetchAndRenderState();
    }
}


function prevBall() {
    if (state.currentBallIndex > 0) {
        state.currentBallIndex--;
        fetchAndRenderState();
    }
}


function resetPlayback() {
    stopPlay();
    state.currentBallIndex = -1;
    state.lastShiftIndex = -1;
    resetDisplays();
    updateProgressBar();
}


function seekBall(event) {
    const bar = document.getElementById('progress-bar');
    const rect = bar.getBoundingClientRect();
    const pct = (event.clientX - rect.left) / rect.width;
    const total = state.totalBalls[state.currentInnings];
    const idx = Math.round(pct * (total - 1));
    state.currentBallIndex = Math.max(0, Math.min(idx, total - 1));
    state.lastShiftIndex = -1;  // Reset shift tracking on seek
    fetchAndRenderState();
}


function updateSpeed(value) {
    state.speed = parseInt(value);
    const displaySpeed = (3000 / state.speed).toFixed(1);
    document.getElementById('speed-value').textContent = displaySpeed + 'x';

    // Restart interval if playing
    if (state.isPlaying) {
        clearInterval(state.playInterval);
        state.playInterval = setInterval(() => {
            const total = state.totalBalls[state.currentInnings];
            if (state.currentBallIndex >= total - 1) {
                stopPlay();
                return;
            }
            nextBall();
        }, state.speed);
    }
}


function updateProgressBar() {
    const total = state.totalBalls[state.currentInnings];
    const idx = state.currentBallIndex;
    const pct = total > 0 ? ((idx + 1) / total) * 100 : 0;
    document.getElementById('progress-fill').style.width = pct + '%';
    document.getElementById('progress-text').textContent =
        `Ball ${idx + 1} / ${total}`;
}


// ══════════════════════════════════════════════════════════════════
// DATA FETCHING & RENDERING
// ══════════════════════════════════════════════════════════════════

async function fetchAndRenderState() {
    const innings = state.currentInnings;
    const ballIdx = state.currentBallIndex;

    try {
        const res = await fetch(`/api/innings/${innings}/state/${ballIdx}`);
        const data = await res.json();
        if (data.error) {
            console.error(data.error);
            return;
        }
        renderDashboard(data);
    } catch (err) {
        console.error('Failed to fetch match state:', err);
    }
}


function renderDashboard(data) {
    updateMatchHeader(data);
    updateMomentumChart(data.momentum_data);
    updateWinProbChart(data.win_prob_data, data);
    updateBallFeed(data.feed, data.current_ball);
    updateTurningPoints(data.turning_points);
    updateStatCards(data.stats);
    updateMomentumBar(data.current_ball.momentum_index);
    updateProgressBar();

    // Check for shift alert
    checkShiftAlert(data.current_ball, data.ball_index);
}


// ── Match Header ──────────────────────────────────────────────────

function updateMatchHeader(data) {
    const ball = data.current_ball;
    const innings = data.innings;

    if (innings === 1) {
        document.getElementById('team-a-runs').textContent = ball.cumulative_runs;
        document.getElementById('team-a-wickets').textContent = '/' + ball.cumulative_wickets;
        document.getElementById('team-a-overs').textContent = '(' + ball.over + '.' + ball.ball + ' ov)';
    } else {
        // Innings 1 summary stays fixed
        if (data.innings1_summary) {
            document.getElementById('team-a-runs').textContent = data.innings1_summary.total_runs;
            document.getElementById('team-a-wickets').textContent = '/' + data.innings1_summary.total_wickets;
            document.getElementById('team-a-overs').textContent = '(' + data.innings1_summary.total_overs + ' ov)';
        }
        document.getElementById('team-b-runs').textContent = ball.cumulative_runs;
        document.getElementById('team-b-wickets').textContent = '/' + ball.cumulative_wickets;
        document.getElementById('team-b-overs').textContent = '(' + ball.over + '.' + ball.ball + ' ov)';
    }

    // Rates
    document.getElementById('current-crr').textContent =
        (ball.current_run_rate || 0).toFixed(2);

    const rrrEl = document.getElementById('current-rrr');
    const rrr = ball.required_run_rate || 0;
    rrrEl.textContent = rrr.toFixed(2);
    rrrEl.classList.toggle('danger', rrr > 10);

    if (innings === 2) {
        document.getElementById('target-score').textContent = data.target;
    }
}


// ── Momentum Chart ────────────────────────────────────────────────

function updateMomentumChart(momentumData) {
    if (!momentumData) return;

    const overs = momentumData.overs;
    const momentum = momentumData.momentum;

    // Color based on momentum value
    const colors = momentum.map(v => {
        if (v === null) return 'rgba(100,100,100,0.5)';
        return v >= 0 ? 'rgba(6, 214, 160, 0.8)' : 'rgba(239, 71, 111, 0.8)';
    });

    Plotly.react('momentum-chart', [{
        x: overs,
        y: momentum,
        type: 'scatter',
        mode: 'lines+markers',
        line: {
            color: '#06d6a0',
            width: 2.5,
            shape: 'spline',
        },
        marker: {
            size: 3,
            color: colors,
        },
        fill: 'tozeroy',
        fillcolor: 'rgba(6, 214, 160, 0.04)',
        name: 'Momentum Index',
        hovertemplate: 'Over %{x}<br>Momentum: %{y}<extra></extra>',
    }], {
        ...PLOTLY_LAYOUT_BASE,
        yaxis: {
            ...PLOTLY_LAYOUT_BASE.yaxis,
            range: [-105, 105],
            title: { text: 'Momentum', font: { size: 10, color: '#64748b' } },
            dtick: 25,
        },
        xaxis: {
            ...PLOTLY_LAYOUT_BASE.xaxis,
            range: [0, Math.max(20, (overs[overs.length - 1] || 0) + 1)],
        },
        shapes: [{
            type: 'line',
            x0: 0, x1: 20,
            y0: 0, y1: 0,
            line: { color: 'rgba(255,255,255,0.12)', width: 1, dash: 'dash' },
        }, {
            type: 'rect',
            x0: 0, x1: 20,
            y0: 0, y1: 100,
            fillcolor: 'rgba(6, 214, 160, 0.02)',
            line: { width: 0 },
        }, {
            type: 'rect',
            x0: 0, x1: 20,
            y0: -100, y1: 0,
            fillcolor: 'rgba(239, 71, 111, 0.02)',
            line: { width: 0 },
        }],
        annotations: [
            {
                x: 0.02, y: 95, xref: 'paper', yref: 'y',
                text: 'BATTING ↑', showarrow: false,
                font: { size: 9, color: 'rgba(6,214,160,0.5)' },
            },
            {
                x: 0.02, y: -95, xref: 'paper', yref: 'y',
                text: 'BOWLING ↓', showarrow: false,
                font: { size: 9, color: 'rgba(239,71,111,0.5)' },
            },
        ],
    }, PLOTLY_CONFIG);
}


// ── Win Probability Chart ─────────────────────────────────────────

function updateWinProbChart(winData, matchData) {
    if (!winData) return;

    const overs = winData.overs;
    const innings = matchData.innings;
    const battingName = matchData.current_ball.batting_team || 'Batting';
    const bowlingName = matchData.current_ball.bowling_team || 'Bowling';

    Plotly.react('winprob-chart', [{
        x: overs,
        y: winData.batting_prob,
        type: 'scatter',
        mode: 'lines',
        line: { color: '#06d6a0', width: 2, shape: 'spline' },
        fill: 'tozeroy',
        fillcolor: 'rgba(6, 214, 160, 0.1)',
        name: battingName,
        hovertemplate: '%{y:.1f}%<extra></extra>',
    }, {
        x: overs,
        y: winData.bowling_prob,
        type: 'scatter',
        mode: 'lines',
        line: { color: '#ef476f', width: 2, shape: 'spline' },
        fill: 'tozeroy',
        fillcolor: 'rgba(239, 71, 111, 0.1)',
        name: bowlingName,
        hovertemplate: '%{y:.1f}%<extra></extra>',
    }], {
        ...PLOTLY_LAYOUT_BASE,
        yaxis: {
            ...PLOTLY_LAYOUT_BASE.yaxis,
            range: [0, 100],
            title: { text: 'Win %', font: { size: 10, color: '#64748b' } },
            dtick: 25,
        },
        xaxis: {
            ...PLOTLY_LAYOUT_BASE.xaxis,
            range: [0, Math.max(20, (overs[overs.length - 1] || 0) + 1)],
        },
        shapes: [{
            type: 'line',
            x0: 0, x1: 20,
            y0: 50, y1: 50,
            line: { color: 'rgba(255,255,255,0.1)', width: 1, dash: 'dash' },
        }],
    }, PLOTLY_CONFIG);
}


// ── Ball Feed ─────────────────────────────────────────────────────

function updateBallFeed(feed, currentBall) {
    const container = document.getElementById('ball-feed');
    if (!feed || feed.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-icon">🏏</div><p>No balls delivered yet</p></div>';
        return;
    }

    let html = '';
    for (let i = 0; i < feed.length; i++) {
        const ball = feed[i];
        const isCurrent = (i === feed.length - 1);
        const isWicket = ball.is_wicket;
        const isBoundary = ball.is_boundary;
        const runs = ball.total_runs;

        // Determine feed item class
        let itemClass = 'feed-item';
        if (isCurrent) itemClass += ' current';
        else if (isWicket) itemClass += ' wicket';
        else if (isBoundary) itemClass += ' boundary';
        else if (runs >= 4) itemClass += ' highlight';

        // Determine runs bubble class
        let runsClass = 'feed-runs';
        if (isWicket) runsClass += ' wicket-ball';
        else if (ball.runs_off_bat === 6) runsClass += ' six';
        else if (ball.runs_off_bat === 4) runsClass += ' four';
        else if (runs >= 2) runsClass += ' two-three';
        else if (runs === 1) runsClass += ' single';
        else runsClass += ' dot';

        const displayRuns = isWicket ? 'W' : runs;
        const overLabel = `${ball.over}.${ball.ball}`;

        let detail = `<span class="batsman-name">${ball.batsman}</span>`;
        detail += ` <span class="bowler-name">vs ${ball.bowler}</span>`;

        if (isWicket) {
            detail += ` — <span class="dismissal-text">${ball.player_dismissed} ${ball.dismissal_kind}</span>`;
        } else if (ball.runs_off_bat === 6) {
            detail += ' — SIX! 💥';
        } else if (ball.runs_off_bat === 4) {
            detail += ' — FOUR! 🔥';
        } else if (ball.extras > 0) {
            detail += ` (${ball.extras} extras)`;
        }

        html += `
            <div class="${itemClass}">
                <span class="feed-over">${overLabel}</span>
                <span class="${runsClass}">${displayRuns}</span>
                <span class="feed-detail">${detail}</span>
            </div>
        `;
    }

    container.innerHTML = html;
    // Auto-scroll to bottom
    container.scrollTop = container.scrollHeight;
}


// ── Turning Points ────────────────────────────────────────────────

function updateTurningPoints(points) {
    const container = document.getElementById('turning-points');
    if (!points || points.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-icon">🔍</div><p>No momentum shifts detected yet</p></div>';
        return;
    }

    let html = '';
    for (const tp of points) {
        const isPositive = tp.change > 0;
        const icon = tp.severity === 'critical' ? '🔴' : (tp.severity === 'major' ? '🟠' : '🔵');

        html += `
            <div class="tp-item">
                <div class="tp-marker ${tp.severity}">${icon}</div>
                <div class="tp-content">
                    <div class="tp-header">
                        <span class="tp-over">Ov ${tp.over}</span>
                        <span class="tp-score">${tp.score}</span>
                        <span class="tp-severity ${tp.severity}">${tp.severity}</span>
                    </div>
                    <div class="tp-description">${tp.description}</div>
                </div>
                <div class="tp-change ${isPositive ? 'positive' : 'negative'}">
                    ${isPositive ? '▲' : '▼'}
                    ${Math.abs(tp.change).toFixed(0)}
                </div>
            </div>
        `;
    }

    container.innerHTML = html;
}


// ── Stat Cards ────────────────────────────────────────────────────

function updateStatCards(stats) {
    const runs5 = stats.runs_last_5_overs ?? 0;
    const dotPct = stats.dot_ball_pct ?? 0;
    const pressure = stats.pressure_index ?? 0;
    const momentum = stats.momentum_score ?? 0;
    const boundary = stats.boundary_freq ?? 0;
    const accel = stats.run_rate_acceleration ?? 0;

    document.getElementById('stat-runs5').textContent = Math.round(runs5);
    document.getElementById('stat-dotpct').textContent = dotPct.toFixed(1) + '%';

    const pressureEl = document.getElementById('stat-pressure');
    pressureEl.textContent = pressure.toFixed(1);
    pressureEl.className = 'stat-value ' + (pressure > 50 ? 'negative' : pressure > 25 ? 'neutral' : 'positive');

    const momentumEl = document.getElementById('stat-momentum');
    momentumEl.textContent = (momentum >= 0 ? '+' : '') + momentum.toFixed(1);
    momentumEl.className = 'stat-value ' + (momentum >= 0 ? 'positive' : 'negative');

    document.getElementById('stat-boundary').textContent = boundary.toFixed(1) + '%';

    const accelEl = document.getElementById('stat-accel');
    accelEl.textContent = (accel >= 0 ? '+' : '') + accel.toFixed(2);
    accelEl.className = 'stat-value ' + (accel >= 0 ? 'positive' : 'negative');
}


// ── Momentum Bar ──────────────────────────────────────────────────

function updateMomentumBar(value) {
    const v = value || 0;
    const pct = ((v + 100) / 200) * 100;  // Map [-100,100] to [0%,100%]
    document.getElementById('momentum-indicator').style.left = pct + '%';

    const valueEl = document.getElementById('momentum-value');
    valueEl.textContent = (v >= 0 ? '+' : '') + v.toFixed(0);
    valueEl.style.color = v >= 0 ? '#06d6a0' : '#ef476f';
}


// ── Shift Alerts ──────────────────────────────────────────────────

function checkShiftAlert(ball, ballIndex) {
    if (!ball.is_shift) return;
    if (ballIndex <= state.lastShiftIndex) return;

    state.lastShiftIndex = ballIndex;
    showShiftAlert(ball.shift_severity, ball.shift_description);
}


function showShiftAlert(severity, description) {
    const alert = document.getElementById('shift-alert');
    const icon = severity === 'critical' ? '🚨' : (severity === 'major' ? '⚠️' : '📊');

    alert.className = 'shift-alert show ' + severity;
    document.getElementById('shift-alert-icon').textContent = icon;
    document.getElementById('shift-alert-title').textContent =
        `${severity.charAt(0).toUpperCase() + severity.slice(1)} Momentum Shift`;
    document.getElementById('shift-alert-body').textContent = description;

    // Auto-hide after 4 seconds
    setTimeout(() => hideShiftAlert(), 4000);
}


function hideShiftAlert() {
    document.getElementById('shift-alert').classList.remove('show');
}
