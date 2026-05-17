# 🏛️ OlympusOS — Cognitive Urban Operating System

> **A multi-agent AI orchestration platform for real-time crowd intelligence, crisis prediction, and autonomous coordination at mega-scale urban events.**

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![CesiumJS](https://img.shields.io/badge/CesiumJS-1.114-48B5C4?style=for-the-badge&logo=cesium&logoColor=white)
![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-FF6B35?style=for-the-badge)
![Vultr](https://img.shields.io/badge/Deployed_on-Vultr-007BFC?style=for-the-badge&logo=vultr&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-39FF14?style=for-the-badge)

**🔴 LIVE DEMO → [http://66.245.207.177/](http://66.245.207.177/)**

*Built for Milano Cortina 2026 — Winter Olympics AI Hackathon*

</div>

---

## 🧠 What Is OlympusOS?

OlympusOS is a **cognitive operating system for cities** — an AI orchestration platform built to solve one of the most underestimated risks in modern urban infrastructure: the systemic failure of human coordination during high-density events.

Traditional monitoring systems are passive. They display data. They do not reason across it, issue coordinated decisions, or adapt in real time to cascading crises. When 80,000 people exit a stadium simultaneously and the metro system fails, the gap between a dashboard and intelligence becomes a matter of public safety.

OlympusOS replaces that gap with **seven specialized AI agents** that perceive anomalies, forecast trajectories, deliberate on interventions, and execute coordinated responses — autonomously, in under 60 seconds.

Designed for **Milano Cortina 2026**, it represents a new category of urban infrastructure: **Cognitive Urban Intelligence**.

---

## 🎬 Live Demo

**→ [http://66.245.207.177/](http://66.245.207.177/)**

No login required. Click **▶ RUN DEMO** to launch the full 90-second cinematic crisis scenario over a photorealistic 3D rendering of San Siro Stadium, Milan. Watch seven AI agents detect a crowd crush in real time, deliberate, and resolve the incident — no injuries, response time 47 seconds.

---

## ⚡ The Problem

Large-scale events expose fundamental fragility in urban systems:

- 📡 **Fragmented monitoring** — no single operator sees the full picture
- ⏱️ **Reactive coordination** — response arrives minutes after critical thresholds breach
- 🔗 **Communication bottlenecks** — transport, security, medical, and comms agencies operate in silos
- 📊 **Dashboard paralysis** — operators see data but receive no synthesis, prediction, or decision support
- 🌊 **Cascade failure** — one blocked gate triggers metro overcrowding triggers ambulance gridlock

The 2022 Itaewon crowd crush (158 deaths), the 2010 Love Parade disaster (21 deaths), and dozens of stadium incidents share a common thread: **the information existed. The intelligence did not.**

---

## 🤖 The Seven Agents

OlympusOS deploys a coordinated team of seven specialized AI agents, each with a defined cognitive role:

| Emoji | Agent | Role | Model |
|-------|-------|------|-------|
| 👁️ | **Perception** | Real-time crowd density monitoring, camera anomaly detection | DeepSeek-V3.1 |
| 🔮 | **Forecast** | Predictive crush trajectory modeling, risk scoring | DeepSeek-V3.1 |
| 🚦 | **Mobility** | Evacuation corridor planning, route optimization | Qwen2.5-7B-Instruct |
| 🚌 | **Transit** | Bus and transport fleet coordination | Qwen2.5-7B-Instruct |
| 🛡️ | **Safety** | Medical team dispatch, ambulance routing | Mistral-Nemo-Instruct-2407 |
| 📢 | **Communications** | Bilingual public alerts (EN/IT), stadium broadcast | Mistral-Nemo-Instruct-2407 |
| 🧠 | **Orchestrator** | Command authority — synthesizes agent inputs, issues binding decisions | DeepSeek-V3.1 |

Agents communicate through a **CrewAI pipeline** with causal pacing: detection → forecast → deliberation → authorization → execution. The Orchestrator holds veto and override authority over all agents.

---

## ✅ Feature Matrix

| Feature | Status | Description |
|---------|--------|-------------|
| 7-Agent CrewAI Pipeline | ✅ Implemented | Real-time multi-agent orchestration at 10Hz |
| FastAPI WebSocket Backend | ✅ Implemented | Async streaming server, persistent connections |
| Google Photorealistic 3D Tiles | ✅ Implemented | Real San Siro Stadium — textured 3D buildings |
| 90s Cinematic Scenario Engine | ✅ Implemented | JSON-driven, 51 events across 4 dramatic acts |
| Live Agent Chat Feed | ✅ Implemented | WhatsApp-style panel with colored agent identities |
| Crowd Dot Simulation | ✅ Implemented | 80 entities, density-based orange→red color transitions |
| Bus Fleet Animation | ✅ Implemented | 30 buses routed depot → north gate over 25 seconds |
| Ambulance Dispatch | ✅ Implemented | Flashing position animation with live routing |
| Metro M5 Failure Event | ✅ Implemented | Flashing red polyline on service suspension |
| Evacuation Corridor | ✅ Implemented | Dual-layer green glow polyline along Corridor B |
| Speechmatics Transcript | ✅ Implemented | Live word-by-word emergency broadcast stream |
| Metrics HUD | ✅ Implemented | Crowd Risk / Evacuation / Response / Buses |
| Camera Flythrough System | ✅ Implemented | 8 cinematic camera positions, cubic easing |
| Vultr Cloud Deployment | ✅ Implemented | nginx reverse proxy + systemd process supervision |
| SUMO Traffic Simulation | 🔶 Mocked | Architecture exists, data generated from simulation |
| Real CCTV Ingestion | 🔲 Designed | YOLO object detection pipeline — not yet wired |
| IoT Sensor Grid | 🔲 Designed | Pressure sensor API integration conceptualized |
| RL Policy Optimization | 🔲 Designed | Reinforcement learning layer for route decisions |

---

## 🏗️ Architecture

```
                        OlympusOS — Cognitive Layer
                        ===========================

  [Perception]   [Forecast]   [Mobility]   [Transit]
       |               |            |            |
  [Safety]       [Communications]  |            |
       |               |            |            |
       +---------------+------------+------------+
                                |
                         [Orchestrator]
                         Command Core
                                |
       +------------------------+------------------------+
       |                        |                        |
  [CesiumJS]            [FastAPI Backend]         [Speechmatics]
  3D Digital Twin       WebSocket / REST          Live Transcript
  Google 3D Tiles       CrewAI Pipeline           Audio Analysis
       |                        |                        |
       +------------------------+------------------------+
                                |
                     [Vultr Ubuntu 24.04]
                     nginx --> systemd
                     http://66.245.207.177/
```

### 🔄 Crisis Response Flow

```
  DETECT (0-12s)
  Perception detects density spike at Gate 4
       --> Camera 7 confirms visual bottleneck
       --> Forecast models 6.4 ppl/m2 in 3:40

  DELIBERATE (12-30s)
  Mobility identifies Corridor B as clear
       --> Safety stages medical teams
       --> Transit holds 30 buses at Lampugnano
       --> Orchestrator: AUTHORIZE

  EXECUTE (30-66s)
  Corridor B opens  -->  Gate 4 outflow redirects
  30 buses deploy   -->  M5 fails, buses become critical
  Ambulances roll   -->  Comms pushes bilingual alert

  RESOLVE (66-90s)
  Density: 6.4 --> 2.6 ppl/m2
  Risk: 0.83 --> 0.28
  Response window: 47 seconds. No injuries.
```

---

## 🛠️ Technology Stack

### 🖥️ Frontend
| Technology | Version | Purpose |
|-----------|---------|---------|
| CesiumJS | 1.114 | 3D geospatial rendering engine |
| Google Maps Platform | — | Photorealistic 3D Tiles (Map Tiles API) |
| HTML5 / CSS3 / JavaScript | ES2022 | Single-file SPA, zero build step |
| Web Audio API | — | Soft bell notifications per agent event |
| WebSocket API | — | Real-time backend event streaming |

### ⚙️ Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11 | Runtime |
| FastAPI | 0.104 | Async REST + WebSocket server |
| CrewAI | Latest | Multi-agent orchestration framework |
| uvicorn | Latest | ASGI server |
| Speechmatics SDK | Latest | Real-time audio transcription |
| SUMO | 1.18 | Traffic simulation engine |

### 🤖 AI Models (via Featherless.ai)
| Model | Agents |
|-------|--------|
| DeepSeek-V3.1 | 🧠 Orchestrator, 🔮 Forecast, 👁️ Perception |
| Mistral-Nemo-Instruct-2407 | 🛡️ Safety, 📢 Communications |
| Qwen2.5-7B-Instruct | 🚦 Mobility, 🚌 Transit |

### ☁️ Infrastructure
| Component | Detail |
|-----------|--------|
| Cloud Provider | Vultr — Ubuntu 24.04 VPS |
| Reverse Proxy | nginx |
| Process Manager | systemd |
| Version Control | GitHub |

---

## 🚀 Installation & Deployment

### Prerequisites

```bash
Python 3.11+
SUMO 1.18        # sudo apt install sumo
nginx
git
```

### 1. Clone

```bash
git clone https://github.com/NevineAKF/OlympusOS
cd OlympusOS
```

### 2. Configure Environment

```bash
cp .env.example .env
```

```env
GOOGLE_MAPS_API_KEY=your_google_maps_platform_key
CESIUM_ION_TOKEN=your_cesium_ion_token
SPEECHMATICS_API_KEY=your_speechmatics_key
FEATHERLESS_API_KEY=your_featherless_key
GEMINI_API_KEY=your_gemini_key
```

### 3. Install Backend

```bash
pip install -r requirements.txt
```

### 4. Run Backend

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 5. Configure nginx

```nginx
server {
    listen 80;

    location / {
        root /var/www/olympusos/dashboard;
        index index.html;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }

    location /run_demo {
        proxy_pass http://localhost:8000;
    }
}
```

### 6. Inject API Keys into Frontend

```bash
KEY=$(grep -oP 'GOOGLE_MAPS_API_KEY\s*=\s*\K\S+' .env)
ION=$(grep -oP 'CESIUM_ION_TOKEN\s*=\s*\K\S+' .env)
sed -i "s|__GOOGLE_MAPS_API_KEY__|${KEY}|g; s|__CESIUM_ION_TOKEN__|${ION}|g" dashboard/index.html
```

### 7. Access

Navigate to `http://your-server-ip/` and click **▶ RUN DEMO**.

---

## 🗺️ Roadmap

### 📍 Phase 1 — Live Sensor Integration *(0–6 months)*
- 🎥 CCTV ingestion with real-time YOLO crowd density detection
- 📡 IoT pressure sensor grid at stadium gates
- 🚗 Live SUMO traffic simulation with real road state feeds
- 🗺️ Dynamic map overlays from real sensor data

### 📍 Phase 2 — AI Capability Expansion *(6–12 months)*
- 🧬 Reinforcement learning policy optimization for crowd routing
- 🗂️ Vector database agent memory — persistent reasoning across events
- 🌍 Multilingual command interface (Italian, English, French, German)
- 🚁 Drone coordination API for aerial crowd monitoring
- 📈 Predictive modeling with 10-minute lookahead horizons

### 📍 Phase 3 — Municipal Deployment *(12–24 months)*
- 🚔 Integration with Italian police dispatch systems
- 🚑 Real-time ambulance and fire brigade coordination API
- 🚦 Smart traffic signal control interface
- 🛰️ Satellite crowd density feeds for stadium perimeter
- 🏛️ Government compliance and audit logging layer

### 📍 Phase 4 — National Scale *(2–5 years)*
- 🌐 Multi-city deployment framework
- 🤖 Autonomous emergency coordination — zero human approval latency
- 🏙️ Digital twin integration for full urban system modeling
- 🏅 Government API for Olympics, World Cup, and G7-scale events
- 📊 Federated learning across event venues globally

---

## ⚠️ Prototype Limitations

This is a proof-of-concept built by a solo developer over 3 days:

| Constraint | Detail |
|-----------|--------|
| 👤 Solo development | Single developer, 72-hour build window |
| 💻 No GPU inference | All LLM calls routed through external API |
| 📡 No live sensors | Crowd simulation is mathematical, not camera-derived |
| 🔒 No institutional APIs | Police, medical, and transport systems unavailable |
| 💰 Infrastructure budget | $200 Vultr credit, $890 Google Maps credit |
| ⚡ API rate limits | Speechmatics, Google Maps, Featherless quotas |

The architecture demonstrates systems-level thinking for a platform that, at full scale, would require dedicated engineering teams, institutional partnerships, and government-grade infrastructure.

---

## 🙏 Acknowledgements

| Project | Role |
|---------|------|
| [Milano Cortina 2026](https://www.milanocortina2026.olimpiadi.it/) | Inspiration and hackathon context |
| [Cesium](https://cesium.com/) | Open-source 3D geospatial rendering engine |
| [Google Maps Platform](https://mapsplatform.google.com/) | Photorealistic 3D Tiles |
| [CrewAI](https://crewai.com/) | Multi-agent orchestration framework |
| [Speechmatics](https://www.speechmatics.com/) | Real-time audio transcription |
| [SUMO](https://sumo.dlr.de/) | Open-source traffic simulation |
| [Featherless.ai](https://featherless.ai/) | LLM inference API |

---

## 🌐 Vision

Cities are the most complex adaptive systems humanity has ever built. And yet, when they fail — when 80,000 people try to leave a stadium at once, when a metro line drops, when a bottleneck turns into a crush — the systems designed to protect people are still running on radio calls, spreadsheets, and fragmented dashboards.

**OlympusOS is the answer to that gap.**

Not a smarter dashboard. Not a better alert system. A **cognitive layer** — a system that sees, reasons, decides, and acts. One that treats a city's real-time sensor data as a language and speaks back in coordinated action. One that compresses a 20-minute human coordination cycle into 47 seconds of autonomous intervention.

The prototype proves the architecture. The crisis at San Siro — 6.4 people per square metre, children near the railings, a metro line down, 47,000 app notifications pushed in the same second — all of it resolved, no injuries, under a minute.

This is what it looks like when cities stop reacting and start thinking.

**OlympusOS. Cities that think.**

---

<div align="center">

*Built for Milano Cortina 2026 — Winter Olympics AI Hackathon*

**🔴 [http://66.245.207.177/](http://66.245.207.177/) — Live Demo**

[![GitHub](https://img.shields.io/badge/GitHub-NevineAKF%2FOlympusOS-181717?style=for-the-badge&logo=github)](https://github.com/NevineAKF/OlympusOS)

</div>
