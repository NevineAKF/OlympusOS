#!/usr/bin/env bash
# OlympusOS full deployment script
# Run as root on the Vultr server: bash /var/www/olympusos/deploy.sh
set -e

PROJECT=/var/www/olympusos
echo "=== OlympusOS Deploy ==="

# ── 1. Pull latest code ──────────────────────────────────────────────────────
cd "$PROJECT"
git pull origin main || true

# ── 2. Install Python dependencies ──────────────────────────────────────────
echo "→ Installing Python packages…"
pip3 install --break-system-packages --quiet \
  fastapi "uvicorn[standard]" websockets python-dotenv openai \
  "crewai>=0.28" speechmatics-python gtts 2>/dev/null || true

# ── 3. Generate simulation data ──────────────────────────────────────────────
echo "→ Generating simulation data…"
mkdir -p "$PROJECT/sumo/output"
python3 "$PROJECT/sumo/generate_sim_data.py"

# ── 4. Generate emergency call audio ────────────────────────────────────────
echo "→ Generating audio file…"
mkdir -p "$PROJECT/audio"
python3 "$PROJECT/audio/generate_audio.py"

# ── 5. nginx configuration ───────────────────────────────────────────────────
echo "→ Configuring nginx…"
cat > /etc/nginx/sites-available/olympusos <<'NGINX'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    root /var/www/olympusos/dashboard;
    index index.html;

    # Serve static dashboard
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy WebSocket to FastAPI
    location /ws {
        proxy_pass         http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host $host;
        proxy_read_timeout 3600s;
    }

    # Proxy REST endpoints to FastAPI
    location /run_demo {
        proxy_pass         http://127.0.0.1:8000/run_demo;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
    }

    # Serve audio file
    location /audio/ {
        alias /var/www/olympusos/audio/;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/olympusos /etc/nginx/sites-enabled/olympusos
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
echo "   nginx ✓"

# ── 6. systemd service for FastAPI backend ───────────────────────────────────
echo "→ Creating systemd service…"
cat > /etc/systemd/system/olympusos-backend.service <<SERVICE
[Unit]
Description=OlympusOS FastAPI Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/olympusos
EnvironmentFile=/var/www/olympusos/.env
ExecStart=/usr/bin/python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable olympusos-backend
systemctl restart olympusos-backend
echo "   backend service ✓"

# ── 7. Smoke tests ───────────────────────────────────────────────────────────
echo "→ Waiting for backend to start…"
sleep 4

echo "→ Testing http://localhost/ (dashboard)…"
curl -sf http://localhost/ | grep -q "OlympusOS" && echo "   dashboard ✓" || echo "   dashboard ✗ — check nginx"

echo "→ Testing http://localhost/run_demo…"
STATUS=$(curl -sf -X POST http://localhost/run_demo -o /dev/null -w "%{http_code}" 2>/dev/null)
[ "$STATUS" = "200" ] && echo "   run_demo ✓" || echo "   run_demo HTTP $STATUS"

echo ""
echo "=== Deploy complete ==="
echo "    Dashboard:  http://66.245.207.177/"
echo "    Backend:    http://66.245.207.177:8000/"
echo "    Logs:       journalctl -u olympusos-backend -f"
