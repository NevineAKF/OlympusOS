import os
import queue
import threading
import time

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OlympusOS — Urban Operations",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CESIUM_TOKEN = os.getenv("CESIUM_ION_TOKEN", "")

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ── Base ── */
  html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #050a14 !important;
    color: #ffffff !important;
    font-family: 'Inter', 'Segoe UI', sans-serif;
  }
  [data-testid="stSidebar"] { display: none; }
  [data-testid="stHeader"]  { background: #050a14 !important; border-bottom: 1px solid #00d4ff !important; }
  .block-container { padding: 0.75rem 1rem 1rem 1rem !important; max-width: 100% !important; }

  /* ── Top bar ── */
  .topbar {
    display: flex; align-items: center; justify-content: space-between;
    background: #050a14; border-bottom: 1px solid #00d4ff;
    padding: 0.6rem 1.2rem; margin-bottom: 0.75rem; border-radius: 6px;
  }
  .topbar-left  { display: flex; flex-direction: column; gap: 2px; }
  .topbar-title { font-size: 1.4rem; font-weight: 700; color: #00d4ff;
                  letter-spacing: 0.08em; font-family: monospace; }
  .topbar-sub   { font-size: 0.72rem; color: #8899bb; letter-spacing: 0.05em; }
  .status-dot   { display: inline-block; width: 10px; height: 10px;
                  border-radius: 50%; margin-right: 6px; }
  .dot-green { background: #39ff14; box-shadow: 0 0 10px #39ff14; }
  .dot-red   { background: #ff6b35; box-shadow: 0 0 10px #ff6b35; animation: blink 1s infinite; }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
  .status-text { font-size: 0.8rem; color: #aabbcc; }

  /* ── Section headers ── */
  .section-label {
    font-size: 0.65rem; font-weight: 600; letter-spacing: 0.15em;
    color: #00d4ff; text-transform: uppercase;
    border-bottom: 1px solid #00d4ff55; padding-bottom: 4px; margin-bottom: 8px;
  }

  /* ── Agent cards ── */
  .agent-card {
    background: #0a1020;
    border-left: 3px solid #00d4ff;
    border-top: 1px solid #00d4ff; border-right: 1px solid #00d4ff; border-bottom: 1px solid #00d4ff;
    box-shadow: 0 0 8px rgba(0,212,255,0.3);
    border-radius: 6px; padding: 8px 10px; margin-bottom: 6px;
    transition: box-shadow .3s;
  }
  .agent-card.active { box-shadow: 0 0 16px rgba(0,212,255,0.6); border-left-color: #00d4ff; }
  .agent-card.done   { border-left-color: #39ff14; box-shadow: 0 0 8px rgba(57,255,20,0.25); }
  .agent-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
  .agent-icon   { font-size: 1rem; }
  .agent-name   { font-size: 0.78rem; font-weight: 600; color: #00d4ff; flex: 1; }
  .agent-status { font-size: 0.65rem; font-weight: 700; letter-spacing: .1em;
                  padding: 2px 8px; border-radius: 3px; }
  .status-standby  { background: #1a2540; color: #8899bb; border: 1px solid #2a3550; }
  .status-thinking { background: rgba(255,107,53,0.2); color: #ff6b35;
                     border: 1px solid #ff6b35;
                     animation: pulse-border .8s ease-in-out infinite; }
  .status-complete { background: rgba(57,255,20,0.15); color: #39ff14;
                     border: 1px solid #39ff14; }
  @keyframes pulse-border { 0%,100%{opacity:1} 50%{opacity:.4} }
  .agent-output {
    font-family: monospace; font-size: 0.68rem; color: #8899bb;
    line-height: 1.4; max-height: 60px; overflow: hidden;
    white-space: pre-wrap; word-break: break-all;
  }
  .agent-ts { font-size: 0.6rem; color: #445566; margin-top: 3px; }

  /* ── Metric cards ── */
  .metric-card {
    background: #0d1526;
    border: 1px solid #00d4ff;
    box-shadow: 0 0 8px rgba(0,212,255,0.3);
    border-radius: 6px; padding: 10px 12px; margin-bottom: 8px; text-align: center;
  }
  .metric-label { font-size: 0.62rem; color: #7788aa; letter-spacing: .1em;
                  text-transform: uppercase; margin-bottom: 4px; }
  .metric-value { font-size: 2.2rem; font-weight: 700; font-family: monospace;
                  color: #00d4ff; line-height: 1; }
  .metric-value.alert  { color: #ff6b35; }
  .metric-value.safe   { color: #39ff14; }
  .metric-delta { font-size: 0.65rem; margin-top: 3px; }
  .delta-down { color: #39ff14; } .delta-up { color: #ff6b35; }

  /* ── Status log ── */
  .log-box {
    background: #020508; border: 1px solid #1a2540;
    border-radius: 6px; padding: 8px; font-family: monospace;
    font-size: 0.65rem; color: #445566; height: 130px;
    overflow-y: auto; line-height: 1.6;
  }
  .log-line { color: #667788; }
  .log-line.info    { color: #00d4ff; }
  .log-line.warn    { color: #ff6b35; }
  .log-line.success { color: #39ff14; }

  /* ── Camera feeds ── */
  .cam-feed {
    background: #020508; border: 1px solid #1e2d4a;
    border-radius: 6px; height: 100px; display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 4px;
  }
  .cam-icon  { font-size: 1.4rem; color: #334455; }
  .cam-label { font-size: 0.62rem; color: #556677; letter-spacing: .08em; }
  .cam-badge { font-size: 0.58rem; color: #ff6b35cc;
               border: 1px solid #ff6b3566; border-radius: 3px; padding: 1px 5px; }

  /* ── Counter cards ── */
  .counter-row { display: flex; gap: 6px; margin-bottom: 8px; }
  .counter-card {
    flex: 1; background: #0d1526;
    border: 1px solid #00d4ff; box-shadow: 0 0 8px rgba(0,212,255,0.3);
    border-radius: 6px; padding: 6px 8px; text-align: center;
  }
  .counter-val   { font-size: 1.1rem; font-weight: 700; font-family: monospace; color: #00d4ff; }
  .counter-label { font-size: 0.58rem; color: #556688; text-transform: uppercase; letter-spacing: .08em; }

  /* ── Run button ── */
  div[data-testid="stButton"] > button {
    background: #00d4ff !important; color: #050a14 !important;
    font-weight: 700 !important; font-size: 0.9rem !important;
    border: none !important; border-radius: 5px !important;
    padding: 10px 24px !important; letter-spacing: .05em !important;
    transition: background .2s, box-shadow .2s !important;
  }
  div[data-testid="stButton"] > button:hover {
    background: #33ddff !important; box-shadow: 0 0 20px #00d4ffaa !important;
  }
</style>
""", unsafe_allow_html=True)


# ── Session state ──────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "demo_running":    False,
        "demo_complete":   False,
        "agent_states":    {a: {"status": "standby", "output": "", "ts": ""} for a in AGENT_DEFS},
        "metrics":         dict(risk=0.83, evac=28, response="3:12", buses=0),
        "active_agents":   0,
        "sims_run":        0,
        "log_lines":       ["[SYSTEM] OlympusOS initialised", "[SYSTEM] Awaiting scenario trigger"],
        "map_overlays":    [],
        "result_queue":    queue.Queue(),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

AGENT_DEFS = {
    "perception":     {"icon": "🔵", "label": "Perception"},
    "forecast":       {"icon": "🔮", "label": "Forecast"},
    "mobility":       {"icon": "🚦", "label": "Mobility"},
    "transit":        {"icon": "🚌", "label": "Transit"},
    "safety":         {"icon": "🛡️",  "label": "Safety"},
    "communications": {"icon": "📢", "label": "Communications"},
    "orchestrator":   {"icon": "🧠", "label": "Orchestrator"},
}

_init_state()


# ── CesiumJS HTML ──────────────────────────────────────────────────────────────
def _cesium_html(overlays: list[str]) -> str:
    gate4_circle  = '"gate4"'  in str(overlays)
    corridor      = '"corridor"' in str(overlays)
    bus_route     = '"bus"'    in str(overlays)

    gate4_js = f"""
        viewer.entities.add({{
            id: 'gate4_pulse',
            position: Cesium.Cartesian3.fromDegrees(9.1235, 45.4775),
            ellipse: {{
                semiMajorAxis: 80, semiMinorAxis: 80,
                material: new Cesium.ColorMaterialProperty(
                    Cesium.Color.fromCssColorString('#ff6b35').withAlpha(0.45)),
                outline: true, outlineColor: Cesium.Color.fromCssColorString('#ff6b35'),
            }},
        }});
        viewer.entities.add({{
            id: 'gate4_label',
            position: Cesium.Cartesian3.fromDegrees(9.1235, 45.479),
            label: {{ text: '⚠ CROWD ANOMALY — GATE 4', font: '13px monospace',
                      fillColor: Cesium.Color.fromCssColorString('#ff6b35'),
                      showBackground: true,
                      backgroundColor: Cesium.Color.fromCssColorString('#0a0e1acc') }},
        }});
    """ if gate4_circle else ""

    corridor_js = """
        viewer.entities.add({
            id: 'corridor',
            corridor: {
                positions: Cesium.Cartesian3.fromDegreesArray([
                    9.1235, 45.4775,  9.1220, 45.4790,
                    9.1200, 45.4805,  9.1185, 45.4820,
                ]),
                width: 18,
                material: Cesium.Color.fromCssColorString('#00ff88').withAlpha(0.55),
            },
        });
        viewer.entities.add({
            id: 'corr_label',
            position: Cesium.Cartesian3.fromDegrees(9.1210, 45.4800),
            label: { text: '✓ EVACUATION CORRIDOR', font: '12px monospace',
                     fillColor: Cesium.Color.fromCssColorString('#00ff88'),
                     showBackground: true,
                     backgroundColor: Cesium.Color.fromCssColorString('#0a0e1acc') },
        });
    """ if corridor else ""

    bus_js = """
        viewer.entities.add({
            id: 'bus_route',
            polyline: {
                positions: Cesium.Cartesian3.fromDegreesArray([
                    9.1240, 45.4781,  9.1100, 45.4800,
                    9.0980, 45.4820,  9.0900, 45.4830,
                ]),
                width: 4,
                material: new Cesium.PolylineGlowMaterialProperty({
                    glowPower: 0.3,
                    color: Cesium.Color.fromCssColorString('#00d4ff'),
                }),
            },
        });
        viewer.entities.add({
            id: 'bus_label',
            position: Cesium.Cartesian3.fromDegrees(9.1050, 45.4810),
            label: { text: '🚌 EMERGENCY BUS ROUTE', font: '12px monospace',
                     fillColor: Cesium.Color.fromCssColorString('#00d4ff'),
                     showBackground: true,
                     backgroundColor: Cesium.Color.fromCssColorString('#0a0e1acc') },
        });
    """ if bus_route else ""

    return f"""
<!DOCTYPE html><html><head>
<meta charset="utf-8">
<script src="https://cesium.com/downloads/cesiumjs/releases/1.115/Build/Cesium/Cesium.js"></script>
<link  href="https://cesium.com/downloads/cesiumjs/releases/1.115/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
<style>
  html, body {{
    margin: 0; padding: 0; width: 100%; height: 100%;
    background: #050a14; overflow: hidden;
  }}
  #cesiumContainer {{
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  }}
  /* Hide Cesium credits bar */
  .cesium-viewer-bottom {{ display: none !important; }}
</style>
</head><body>
<div id="cesiumContainer"></div>
<script>
  Cesium.Ion.defaultAccessToken = '{CESIUM_TOKEN}';

  var viewer = new Cesium.Viewer('cesiumContainer', {{
    terrainProvider: Cesium.createWorldTerrain(),
    baseLayerPicker:       false,
    geocoder:              false,
    homeButton:            false,
    sceneModePicker:       false,
    navigationHelpButton:  false,
    animation:             false,
    timeline:              false,
    fullscreenButton:      false,
    infoBox:               false,
    selectionIndicator:    false,
    imageryProvider: new Cesium.IonImageryProvider({{ assetId: 4 }}),
  }});

  viewer.scene.globe.enableLighting = false;

  // 3-D buildings
  viewer.scene.primitives.add(Cesium.createOsmBuildings());

  // San Siro marker
  viewer.entities.add({{
    id: 'sansiro',
    position: Cesium.Cartesian3.fromDegrees(9.1240, 45.4781, 0),
    point: {{ pixelSize: 12, color: Cesium.Color.fromCssColorString('#00d4ff'),
              outlineColor: Cesium.Color.WHITE, outlineWidth: 2 }},
    label: {{ text: '🏟 San Siro — 80,000 fans', font: '13px monospace',
              fillColor: Cesium.Color.fromCssColorString('#00d4ff'),
              pixelOffset: new Cesium.Cartesian2(0, -26),
              showBackground: true,
              backgroundColor: Cesium.Color.fromCssColorString('#050a14ee') }},
  }});

  {gate4_js}
  {corridor_js}
  {bus_js}

  // Position camera directly over San Siro, angled down
  viewer.camera.setView({{
    destination: Cesium.Cartesian3.fromDegrees(9.1240, 45.4781, 600),
    orientation: {{
      heading: Cesium.Math.toRadians(0),
      pitch:   Cesium.Math.toRadians(-45),
      roll:    0,
    }},
  }});
</script>
</body></html>
"""


# ── Background crew runner ─────────────────────────────────────────────────────
def _run_crew_thread(result_q: queue.Queue):
    try:
        result_q.put(("log", "info", "CrewAI scenario started"))
        from agents.crew import run_demo_scenario
        result = run_demo_scenario()
        result_q.put(("done", result))
    except Exception as exc:
        result_q.put(("error", str(exc)))


# ── Demo state machine ─────────────────────────────────────────────────────────
DEMO_STEPS = [
    (1.0,  "log",     "warn",    "⚠ Metro M5 failure detected — 80,000 fans at San Siro"),
    (1.5,  "overlay", "gate4",   None),
    (2.0,  "agent",   "perception",     "thinking"),
    (4.5,  "agent",   "perception",     "complete:Crowd anomaly confirmed at Gate 4. Density 0.91. Severity 0.83. Type: crowd_anomaly."),
    (5.0,  "metric",  "risk",    0.83),
    (5.5,  "agent",   "forecast", "thinking"),
    (8.0,  "agent",   "forecast", "complete:Crowd crush predicted in 8 min. Confidence 0.87. Action: open corridor now."),
    (8.5,  "agent",   "mobility", "thinking"),
    (11.0, "agent",   "mobility", "complete:Rerouting Via Piccolomini → Via Harar. Est. improvement 62%."),
    (11.5, "agent",   "transit",  "thinking"),
    (14.0, "agent",   "transit",  "complete:Deploy 50 buses on shuttle route San Siro → Lotto. Wait: 4 min."),
    (14.5, "overlay", "bus",     None),
    (14.5, "metric",  "buses",   50),
    (15.0, "agent",   "safety",  "thinking"),
    (18.0, "agent",   "safety",  "complete:Risk CRITICAL. Opening corridor via Via dei Giganti. 12 units dispatched."),
    (18.5, "overlay", "corridor", None),
    (19.0, "metric",  "evac",    18),
    (19.0, "metric",  "response", "0:47"),
    (19.5, "agent",   "communications", "thinking"),
    (22.0, "agent",   "communications", "complete:Broadcast sent. EN: 'Please use Gate 7 exit.' IT: 'Usare Uscita 7.'"),
    (22.5, "agent",   "orchestrator",   "thinking"),
    (26.0, "agent",   "orchestrator",   "complete:Priority HIGH. All 6 agents coordinated. Est. resolution 18 min."),
    (26.5, "metric",  "risk",    0.34),
    (27.0, "log",     "success", "✓ OlympusOS scenario complete — crisis resolved"),
]

def _tick_demo():
    if not st.session_state.demo_running:
        return
    if "demo_start_time" not in st.session_state:
        st.session_state.demo_start_time = time.time()

    elapsed = time.time() - st.session_state.demo_start_time
    processed = st.session_state.get("steps_processed", set())

    for i, step in enumerate(DEMO_STEPS):
        if i in processed:
            continue
        t, kind, arg1, arg2 = step
        if elapsed < t:
            continue
        processed.add(i)

        if kind == "log":
            st.session_state.log_lines.append(f"[{arg1.upper()}] {arg2}")

        elif kind == "overlay":
            if arg1 not in st.session_state.map_overlays:
                st.session_state.map_overlays.append(f'"{arg1}"')

        elif kind == "agent":
            agent_key = arg1
            if arg2 == "thinking":
                st.session_state.agent_states[agent_key]["status"] = "thinking"
                st.session_state.agent_states[agent_key]["ts"] = time.strftime("%H:%M:%S")
                st.session_state.active_agents = sum(
                    1 for a in st.session_state.agent_states.values() if a["status"] == "thinking"
                )
            elif arg2.startswith("complete:"):
                st.session_state.agent_states[agent_key]["status"] = "complete"
                st.session_state.agent_states[agent_key]["output"] = arg2[len("complete:"):]
                st.session_state.agent_states[agent_key]["ts"] = time.strftime("%H:%M:%S")
                st.session_state.active_agents = sum(
                    1 for a in st.session_state.agent_states.values() if a["status"] == "thinking"
                )

        elif kind == "metric":
            st.session_state.metrics[arg1] = arg2

    st.session_state.steps_processed = processed

    all_done = len(processed) == len(DEMO_STEPS)
    if all_done and not st.session_state.demo_complete:
        st.session_state.demo_complete = True
        st.session_state.demo_running  = False
        st.session_state.sims_run += 1


# ── TOP BAR ────────────────────────────────────────────────────────────────────
is_active = st.session_state.demo_running
dot_class  = "dot-red" if is_active else "dot-green"
dot_label  = "ACTIVE" if is_active else "STANDBY"

top_left, top_right = st.columns([5, 1])
with top_left:
    st.markdown(f"""
    <div class="topbar">
      <div class="topbar-left">
        <div class="topbar-title">⚡ OLYMPOS</div>
        <div class="topbar-sub">Agentic Urban Operations System — San Siro, Milan</div>
      </div>
      <div style="display:flex;align-items:center;gap:6px">
        <span class="status-dot {dot_class}"></span>
        <span class="status-text">{dot_label}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

with top_right:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("▶ RUN DEMO", disabled=is_active):
        # Reset state
        st.session_state.demo_running  = True
        st.session_state.demo_complete = False
        st.session_state.demo_start_time = time.time()
        st.session_state.steps_processed  = set()
        st.session_state.map_overlays     = []
        st.session_state.metrics          = dict(risk=0.83, evac=28, response="3:12", buses=0)
        st.session_state.active_agents    = 0
        st.session_state.agent_states     = {a: {"status": "standby", "output": "", "ts": ""} for a in AGENT_DEFS}
        st.session_state.log_lines        = [
            "[SYSTEM] OlympusOS initialised",
            "[WARN]   Metro M5 failure detected",
            "[SYSTEM] Launching CrewAI scenario…",
        ]
        # Launch real crew in background
        rq = queue.Queue()
        st.session_state.result_queue = rq
        threading.Thread(target=_run_crew_thread, args=(rq,), daemon=True).start()
        st.rerun()


# ── TICK demo steps ────────────────────────────────────────────────────────────
_tick_demo()


# ── THREE-COLUMN LAYOUT ────────────────────────────────────────────────────────
col_map, col_feed, col_metrics = st.columns([4, 3.5, 2.5])


# ══ LEFT: MAP ══════════════════════════════════════════════════════════════════
with col_map:
    st.markdown('<div class="section-label">🗺 Live Map — Milan</div>', unsafe_allow_html=True)
    components.html(
        _cesium_html(st.session_state.map_overlays),
        height=480,
        scrolling=False,
    )

    # Camera feeds
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">📷 Camera Feeds</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    for col, label in [(c1, "CAM 1 — Gate 4"), (c2, "CAM 2 — Metro Lotto")]:
        with col:
            st.markdown(f"""
            <div class="cam-feed">
              <div class="cam-icon">📹</div>
              <div class="cam-label">{label}</div>
              <div class="cam-badge">YOLO Detection Active</div>
            </div>
            """, unsafe_allow_html=True)


# ══ MIDDLE: AGENT FEED ════════════════════════════════════════════════════════
with col_feed:
    st.markdown('<div class="section-label">🤖 Agent Feed</div>', unsafe_allow_html=True)

    for agent_key, meta in AGENT_DEFS.items():
        state  = st.session_state.agent_states[agent_key]
        status = state["status"]
        css    = {"standby": "status-standby", "thinking": "status-thinking", "complete": "status-complete"}[status]
        label  = {"standby": "STANDBY", "thinking": "THINKING...", "complete": "COMPLETE"}[status]
        card_c = {"standby": "", "thinking": "active", "complete": "done"}[status]

        output_html = ""
        if state["output"]:
            preview = state["output"][:180] + ("…" if len(state["output"]) > 180 else "")
            output_html = f'<div class="agent-output">{preview}</div>'

        ts_html = f'<div class="agent-ts">{state["ts"]}</div>' if state["ts"] else ""

        st.markdown(f"""
        <div class="agent-card {card_c}">
          <div class="agent-header">
            <span class="agent-icon">{meta['icon']}</span>
            <span class="agent-name">{meta['label']}</span>
            <span class="agent-status {css}">{label}</span>
          </div>
          {output_html}
          {ts_html}
        </div>
        """, unsafe_allow_html=True)


# ══ RIGHT: METRICS ════════════════════════════════════════════════════════════
with col_metrics:
    st.markdown('<div class="section-label">📊 Metrics</div>', unsafe_allow_html=True)

    m = st.session_state.metrics

    risk_class = "alert" if m["risk"] > 0.6 else "safe"
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">Crowd Risk Score</div>
      <div class="metric-value {risk_class}">{m['risk']:.2f}</div>
      <div class="metric-delta {'delta-down' if m['risk'] < 0.83 else 'delta-up'}">
        {'↓ Decreasing' if m['risk'] < 0.83 else '↑ Critical'}
      </div>
    </div>
    """, unsafe_allow_html=True)

    evac_class = "safe" if m["evac"] < 25 else "alert"
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">Evacuation Time</div>
      <div class="metric-value {evac_class}">{m['evac']} min</div>
      <div class="metric-delta {'delta-down' if m['evac'] < 28 else ''}">
        {'↓ Optimised' if m['evac'] < 28 else '—'}
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">Emergency Response</div>
      <div class="metric-value {'safe' if m['response'] == '0:47' else 'alert'}">{m['response']}</div>
      <div class="metric-delta {'delta-down' if m['response'] == '0:47' else ''}">
        {'↓ Units dispatched' if m['response'] == '0:47' else '—'}
      </div>
    </div>
    """, unsafe_allow_html=True)

    buses_class = "safe" if m["buses"] > 0 else ""
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">Buses Deployed</div>
      <div class="metric-value {buses_class}">{m['buses']}</div>
      <div class="metric-delta {'delta-up' if m['buses'] > 0 else ''}">
        {'↑ Fleet active' if m['buses'] > 0 else '—'}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Counters
    st.markdown('<div class="section-label" style="margin-top:8px">System</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="counter-row">
      <div class="counter-card">
        <div class="counter-val">{st.session_state.active_agents}/7</div>
        <div class="counter-label">Active Agents</div>
      </div>
      <div class="counter-card">
        <div class="counter-val">{st.session_state.sims_run}</div>
        <div class="counter-label">Sims Run</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Log
    st.markdown('<div class="section-label">System Log</div>', unsafe_allow_html=True)
    log_lines = st.session_state.log_lines[-20:]
    lines_html = ""
    for line in reversed(log_lines):
        cls = "info" if "[INFO]" in line or "[SYSTEM]" in line else \
              "warn" if "[WARN]" in line else \
              "success" if "[SUCCESS]" in line else "log-line"
        lines_html += f'<div class="log-line {cls}">{line}</div>'
    st.markdown(f'<div class="log-box">{lines_html}</div>', unsafe_allow_html=True)


# ── Auto-rerun while demo is live ─────────────────────────────────────────────
if st.session_state.demo_running:
    time.sleep(0.6)
    st.rerun()
