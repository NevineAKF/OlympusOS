# OlympusOS â Cognitive Urban Operating System

> *A multi-agent AI orchestration platform for intelligent crowd management and crisis coordination at mega-scale urban events.*

---

## Executive Summary

OlympusOS is a **cognitive operating system for cities** â a proof-of-concept AI orchestration platform designed to address one of the most underestimated risks in modern urban infrastructure: the systemic failure of human coordination during high-density events.

Traditional monitoring systems are passive. They display data. They do not reason across it. They do not issue coordinated decisions. They do not adapt in real time to cascading crises. When 80,000 people exit a stadium simultaneously and the metro system fails, the gap between dashboards and intelligence becomes a matter of public safety.

OlympusOS was conceptually designed for **Milano Cortina 2026** â the Winter Olympics â as a next-generation AI command layer capable of detecting, predicting, coordinating, and resolving crowd-scale emergencies through a network of specialized autonomous agents. The prototype demonstrates the architecture of a system that, at full scale, would represent a new category of urban infrastructure: **Cognitive Urban Intelligence**.

---

## The Problem

Large-scale events expose fundamental fragility in urban systems:

- **Overcrowding** develops faster than human operators can respond
- **Fragmented monitoring** means no single operator sees the full picture
- **Reactive coordination** arrives minutes after critical thresholds are breached
- **Communication bottlenecks** between transport, security, medical, and communications agencies cause cascading delays
- **Dashboard paralysis** â operators see data but lack synthesis, prediction, or decision support

The 2022 Itaewon crowd crush, the 2010 Love Parade disaster, and dozens of stadium incidents share a common thread: the information was available, but the intelligence was not.

OlympusOS addresses this by replacing passive dashboards with **active cognitive coordination** â a system that perceives, forecasts, deliberates, and executes.

---

## Architecture Overview

```
âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
â                    OlympusOS Cognitive Layer                         â
â                                                                      â
â  ââââââââââââ  ââââââââââââ  ââââââââââââ  ââââââââââââ           â
â  âPerceptionâ  â Forecast â  â Mobility â  â  Transit â           â
â  â  Agent   â  â  Agent   â  â  Agent   â  â  Agent   â           â
â  ââââââ¬ââââââ  ââââââ¬ââââââ  ââââââ¬ââââââ  ââââââ¬ââââââ           â
â       â              â              â              â                  â
â  ââââââ´ââââââ  ââââââ´ââââââ       â              â                  â
â  â  Safety  â  â  Comms   â       â              â                  â
â  â  Agent   â  â  Agent   â       â              â                  â
â  ââââââ¬ââââââ  ââââââ¬ââââââ       â              â                  â
â       ââââââââââââââââ´ââââââââââââââ´âââââââââââââââ                 â
â                              â                                       â
â                   ââââââââââââ¼âââââââââââ                           â
â                   â   Orchestrator       â                           â
â                   â   (Command Core)     â                           â
â                   ââââââââââââ¬âââââââââââ                           â
ââââââââââââââââââââââââââââââââ¼âââââââââââââââââââââââââââââââââââââââ
                                â
          âââââââââââââââââââââââ¼ââââââââââââââââââââââ
          â                     â                       â
   ââââââââ¼âââââââ    âââââââââââ¼âââââââââ    âââââââââ¼ââââââââ
   â  CesiumJS   â    â  FastAPI Backend  â    â Speechmatics  â
   â  3D Digital â    â  WebSocket / REST â    â  Live Audio   â
   â  Twin Layer â    â  CrewAI Pipeline  â    â  Transcript   â
   âââââââââââââââ    ââââââââââââââââââââ    âââââââââââââââââ
```

---

## Features

### Implemented
- Real-time 7-agent CrewAI multi-agent orchestration pipeline
- FastAPI backend with WebSocket streaming at 10Hz
- CesiumJS + Google Photorealistic 3D Tiles (San Siro, Milan â real textured 3D buildings)
- 90-second JSON-driven cinematic crisis scenario engine
- Agent communication panel (WhatsApp-style live feed)
- Autonomous crowd dot simulation (80+ entities with density-based color transitions)
- Bus deployment animation (30 buses routing depot â north gate)
- Ambulance dispatch with live position updates and flash alerts
- Metro M5 failure event with flashing red polyline
- Green evacuation corridor rendering with dual-layer glow
- Live Speechmatics transcript streaming panel
- Metrics HUD (Crowd Risk / Evacuation / Response / Buses)
- Camera flythrough system (7 cinematic camera positions auto-sequenced)
- Vultr cloud deployment with nginx reverse proxy + systemd service

### Simulated (Architecture Exists, Data Mocked)
- SUMO traffic simulation integration (baseline + intervention JSON generated)
- Speechmatics real-time audio analysis (audio file plays, transcript streamed)
- Agent-to-agent causal reasoning (scripted to appear live and autonomous)
- Real crowd density from camera feeds (replaced with mathematical simulation)

### Conceptually Designed (Not Implemented in Prototype)
- Live CCTV camera ingestion with YOLO object detection
- Real IoT sensor grid integration
- Drone coordination layer
- Reinforcement learning policy optimization
- Vector database agent memory with RAG retrieval
- Multi-city deployment infrastructure

---

## Technology Stack

### Frontend
- **CesiumJS 1.114** â 3D geospatial rendering
- **Google Maps Platform** â Photorealistic 3D Tiles (Map Tiles API)
- **HTML5 / CSS3 / JavaScript** â single-file SPA architecture
- **Web Audio API** â soft bell notification sounds
- **WebSocket** â real-time backend communication

### Backend
- **Python 3.11** â runtime
- **FastAPI** â async REST + WebSocket server
- **CrewAI** â multi-agent orchestration framework
- **Speechmatics SDK** â audio transcription pipeline
- **SUMO 1.18** â traffic simulation engine
- **uvicorn** â ASGI server

### AI Models (via Featherless.ai)
- DeepSeek-V3.1 â Orchestrator, Forecast
- Mistral-Nemo-Instruct-2407 â Safety, Communications
- Qwen2.5-7B-Instruct â Mobility, Transit

### Infrastructure
- **Vultr** â Ubuntu 24.04 VPS (46GB disk, 2 vCPU)
- **nginx** â reverse proxy, static file serving
- **systemd** â process supervision
- **GitHub** â version control, CI pipeline

---

## Installation & Deployment

### Prerequisites
```
Python 3.11+
Node.js 18+
SUMO 1.18 (sudo apt install sumo)
nginx
git
```

### Clone and Configure
```bash
git clone https://github.com/NevineAKF/OlympusOS
cd OlympusOS
cp .env.example .env
```

### Required Environment Variables
```env
GOOGLE_MAPS_API_KEY=your_google_maps_platform_key
CESIUM_ION_TOKEN=your_cesium_ion_token
SPEECHMATICS_API_KEY=your_speechmatics_key
FEATHERLESS_API_KEY=your_featherless_key
GEMINI_API_KEY=your_gemini_key
```

### Install Backend
```bash
pip install -r requirements.txt
```

### Run Backend
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Configure nginx
```nginx
server {
    listen 80;
    location / { root /var/www/olympusos/dashboard; index index.html; }
    location /ws { proxy_pass http://localhost:8000; proxy_http_version 1.1;
                   proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "Upgrade"; }
    location /run_demo { proxy_pass http://localhost:8000; }
}
```

### Live Demo
Access at: `http://your-server-ip/`
Click **â¶ RUN DEMO** to launch the 90-second cinematic scenario.

---

## Demo Mode (For Judges)

The live website is deployed at: **http://66.245.207.177/**

No credentials required. Click **â¶ RUN DEMO** and watch the full 90-second scenario unfold automatically.

The demo is self-contained and JSON-driven â no backend interaction required for the visual simulation. The FastAPI backend and CrewAI agents run independently in the background and can be verified via WebSocket connection logs in the system.

---

## Future Roadmap

### Phase 1 â Live Sensor Integration (6 months)
- CCTV ingestion with real-time YOLO crowd density detection
- IoT pressure sensor grid at stadium gates
- Real SUMO traffic simulation with live road state

### Phase 2 â AI Capability Expansion (12 months)
- Reinforcement learning policy optimization for crowd routing
- Vector database agent memory (persistent reasoning across events)
- Multilingual command interface (Italian, English, French)
- Drone coordination API for aerial crowd monitoring

### Phase 3 â Municipal Deployment (18â24 months)
- Integration with Italian police dispatch systems
- Real-time ambulance and fire coordination API
- Smart traffic signal control interface
- Satellite crowd density feeds

### Phase 4 â National Scale (3â5 years)
- Multi-city deployment framework
- Autonomous emergency coordination without human approval
- Digital twin integration for full urban modeling
- Government API for Olympic and World Cup deployments

---

## Limitations of Current Prototype

This system is a proof-of-concept constrained by:

- **Solo development** â single developer over 3 days
- **Compute limits** â no GPU inference, LLM calls via external API
- **API quotas** â Speechmatics, Google Maps, Featherless rate limits
- **No live sensors** â crowd simulation is mathematical, not camera-derived
- **No institutional integration** â police, medical, and transport APIs unavailable
- **Infrastructure budget** â $200 Vultr credit, $890 Google Maps credit

The architecture demonstrates systems-level thinking for a platform that, at full scale, would require dedicated engineering teams, institutional partnerships, and government-grade infrastructure.

---

## Acknowledgements

- **Milano Cortina 2026** â inspiration for the crisis scenario
- **Cesium** â open-source 3D geospatial engine
- **Google Maps Platform** â Photorealistic 3D Tiles
- **CrewAI** â multi-agent orchestration framework
- **Speechmatics** â real-time audio transcription
- **SUMO** â open-source traffic simulation

---

## Enterprise Vision

OlympusOS is not a hackathon project. It is the first implementation of a concept that cities will need within the next decade: **a cognitive coordination layer that sits above existing infrastructure and reasons across it in real time**.

Traditional smart city platforms aggregate data. OlympusOS synthesizes it into decisions. The difference is the difference between a sensor grid and an intelligence. Between a dashboard and a command center. Between reaction and anticipation.

The prototype proves the architecture. The vision requires the infrastructure.

---

*Built for Milano Cortina 2026 â Winter Olympics AI Hackathon*
*Repository: https://github.com/NevineAKF/OlympusOS*
