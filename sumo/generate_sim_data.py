"""
Generate synthetic SUMO-style simulation frames for the OlympusOS demo.
Outputs baseline.json and intervention.json to sumo/output/.
Each file is a list of 600 frames at 10 Hz (60 seconds of simulation).
"""
import json
import math
import os
import random

random.seed(42)
OUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Gate positions ──────────────────────────────────────────────────────────
GATES = {
    "gate1": (9.1205, 45.4770),
    "gate2": (9.1258, 45.4775),
    "gate3": (9.1268, 45.4788),
    "gate4": (9.1238, 45.4783),   # anomaly gate
    "gate5": (9.1218, 45.4796),
    "gate6": (9.1202, 45.4792),
}

DEPOT_POS    = (9.1330, 45.4940)   # Lampugnano depot
CENTRAL_POS  = (9.2047, 45.4854)   # Milano Centrale

N_FRAMES     = 600   # 60 s × 10 Hz
N_PEDS       = 60    # pedestrian dots
N_BUSES      = 5

# ── Initial pedestrian positions scattered around gates ─────────────────────
def _init_peds():
    peds = []
    gate_keys = list(GATES.keys())
    for i in range(N_PEDS):
        g = gate_keys[i % len(gate_keys)]
        cx, cy = GATES[g]
        peds.append({
            "id": f"p{i}",
            "lng": cx + random.uniform(-0.003, 0.003),
            "lat": cy + random.uniform(-0.002, 0.002),
            "gate": g,
        })
    return peds


def _lerp(a, b, t):
    return a + (b - a) * t


def _gate4_density(t_sec: float, baseline: bool) -> float:
    """Return gate-4 crowd density for a given sim second."""
    if baseline:
        # Metro fails at t=10, density climbs to 0.95 by t=40, stays high
        if t_sec < 10:
            return 0.40
        rise = min(1.0, (t_sec - 10) / 30.0)
        return _lerp(0.40, 0.95, rise)
    else:
        # Intervention kicks in at t=25 — density peaks at 0.83 then falls
        if t_sec < 10:
            return 0.40
        if t_sec < 25:
            rise = min(1.0, (t_sec - 10) / 15.0)
            return _lerp(0.40, 0.83, rise)
        fall = min(1.0, (t_sec - 25) / 30.0)
        return _lerp(0.83, 0.22, fall)


def _bus_positions(t_sec: float, active: bool):
    if not active:
        return []
    buses = []
    for i in range(N_BUSES):
        # Each bus starts staggered from depot, moves toward Central
        offset = i * 8                             # 8-second stagger
        t_bus = max(0.0, t_sec - 22 - offset)      # buses deploy from t=22
        frac = min(1.0, t_bus / 35.0)
        lng = _lerp(DEPOT_POS[0], CENTRAL_POS[0], frac)
        lat = _lerp(DEPOT_POS[1], CENTRAL_POS[1], frac)
        buses.append({"id": f"bus{i}", "lng": lng, "lat": lat})
    return buses


def _ped_positions(peds, t_sec, gate4_density, baseline):
    """Drift pedestrians: gate-4 peds crowd together at high density."""
    result = []
    for p in peds:
        lng, lat = p["lng"], p["lat"]
        if p["gate"] == "gate4":
            if baseline and gate4_density > 0.6:
                # Drift toward gate4 centre (crowd crush)
                cx, cy = GATES["gate4"]
                lng += (cx - lng) * 0.02
                lat += (cy - lat) * 0.02
            elif not baseline and t_sec > 25:
                # Disperse after intervention
                lng += random.uniform(-0.0001, 0.0001)
                lat += random.uniform(-0.0001, 0.0001)
        else:
            # Random walk
            lng += random.uniform(-0.00005, 0.00005)
            lat += random.uniform(-0.00005, 0.00005)
        p["lng"], p["lat"] = lng, lat
        result.append({"id": p["id"], "lng": lng, "lat": lat, "gate": p["gate"]})
    return result


def _signal_states(t_sec, baseline):
    if baseline or t_sec < 20:
        return {"via_verdi": "red", "via_harar": "green"}
    return {"via_verdi": "green", "via_harar": "green"}


def generate(baseline: bool) -> list:
    peds = _init_peds()
    frames = []
    for frame_idx in range(N_FRAMES):
        t_sec = frame_idx / 10.0
        g4 = _gate4_density(t_sec, baseline)
        metro = "ok" if t_sec < 10 else "failed"
        bus_active = (not baseline) and t_sec >= 22

        gates_density = {
            "gate1": 0.20 + 0.05 * math.sin(t_sec * 0.3),
            "gate2": 0.25 + 0.04 * math.sin(t_sec * 0.2 + 1),
            "gate3": 0.30 + 0.05 * math.sin(t_sec * 0.25),
            "gate4": round(g4, 3),
            "gate5": 0.22 + 0.03 * math.sin(t_sec * 0.35),
            "gate6": 0.18 + 0.04 * math.sin(t_sec * 0.28 + 2),
        }

        ped_positions = _ped_positions(peds, t_sec, g4, baseline)
        buses = _bus_positions(t_sec, bus_active)
        corridor = (not baseline) and t_sec >= 25

        frames.append({
            "t": round(t_sec, 1),
            "metro_m5": metro,
            "gates": gates_density,
            "pedestrians": ped_positions,
            "buses": buses,
            "corridor": corridor,
            "signals": _signal_states(t_sec, baseline),
        })
    return frames


if __name__ == "__main__":
    print("Generating baseline.json …")
    baseline_frames = generate(baseline=True)
    with open(os.path.join(OUT_DIR, "baseline.json"), "w") as f:
        json.dump(baseline_frames, f, separators=(",", ":"))
    print(f"  {len(baseline_frames)} frames → sumo/output/baseline.json")

    print("Generating intervention.json …")
    intervention_frames = generate(baseline=False)
    with open(os.path.join(OUT_DIR, "intervention.json"), "w") as f:
        json.dump(intervention_frames, f, separators=(",", ":"))
    print(f"  {len(intervention_frames)} frames → sumo/output/intervention.json")
    print("Done.")
