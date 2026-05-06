import json
import os
import glob
from collections import Counter
from datetime import datetime

from flask import Flask, jsonify, render_template
from prometheus_client import Counter as PromCounter, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

COWRIE_LOG_DIR = os.environ.get("COWRIE_LOG_DIR", "./logs/cowrie")

# Prometheus metrics
attack_attempts_total = PromCounter(
    "attack_attempts_total",
    "Total SSH attack attempts logged by Cowrie",
    ["username"],
)
unique_attackers = Gauge("unique_attackers", "Number of unique attacker IPs seen")


def _parse_cowrie_logs():
    """Read all cowrie JSON log files and return list of attack events."""
    events = []
    pattern = os.path.join(COWRIE_LOG_DIR, "cowrie.json*")
    for log_file in sorted(glob.glob(pattern)):
        try:
            with open(log_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("eventid") in (
                            "cowrie.login.failed",
                            "cowrie.login.success",
                        ):
                            events.append(
                                {
                                    "src_ip": entry.get("src_ip", "unknown"),
                                    "username": entry.get("username", ""),
                                    "password": entry.get("password", ""),
                                    "timestamp": entry.get("timestamp", ""),
                                    "session_id": entry.get("session", ""),
                                    "event": entry.get("eventid", ""),
                                }
                            )
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue
    return events


def _refresh_metrics(events):
    ips = {e["src_ip"] for e in events}
    unique_attackers.set(len(ips))


@app.route("/")
def index():
    events = _parse_cowrie_logs()
    _refresh_metrics(events)
    recent = events[-100:][::-1]
    usernames = [e["username"] for e in events if e["username"]]
    passwords = [e["password"] for e in events if e["password"]]
    top_user = Counter(usernames).most_common(1)[0][0] if usernames else "N/A"
    top_pass = Counter(passwords).most_common(1)[0][0] if passwords else "N/A"
    stats = {
        "total_attacks": len(events),
        "unique_ips": len({e["src_ip"] for e in events}),
        "top_username": top_user,
        "top_password": top_pass,
    }
    return render_template("index.html", attacks=recent, stats=stats)


@app.route("/api/attacks")
def api_attacks():
    events = _parse_cowrie_logs()
    return jsonify(events[-100:][::-1])


@app.route("/api/stats")
def api_stats():
    events = _parse_cowrie_logs()
    _refresh_metrics(events)
    usernames = [e["username"] for e in events if e["username"]]
    passwords = [e["password"] for e in events if e["password"]]
    top_creds = [
        {"username": u, "count": c}
        for u, c in Counter(usernames).most_common(10)
    ]
    active_services = {
        "cowrie": os.path.isdir(COWRIE_LOG_DIR),
        "dionaea": os.path.isdir("./logs/dionaea"),
        "dashboard": True,
    }
    return jsonify(
        {
            "total_attacks": len(events),
            "unique_ips": len({e["src_ip"] for e in events}),
            "top_credentials": top_creds,
            "active_services": active_services,
        }
    )


@app.route("/metrics")
def metrics():
    events = _parse_cowrie_logs()
    _refresh_metrics(events)
    usernames = [e["username"] for e in events if e["username"]]
    for username, count in Counter(usernames).items():
        try:
            attack_attempts_total.labels(username=username)._value.set(count)
        except Exception:
            pass
    from flask import Response
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    os.makedirs(COWRIE_LOG_DIR, exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=False)
