#!/usr/bin/env python3
"""
receiver.py — Week 5: a small HTTP endpoint that receives JSON security events
pushed from log_shipper.py on WEB01 and SRV01. Stands in for the Wazuh manager
until it's installed in Week 6, so the forwarding path exists and is proven
before the real SIEM is in place.
"""
from flask import Flask, request, jsonify
from pathlib import Path
from datetime import datetime, timezone
import json

app = Flask(__name__)

OUTDIR = Path("/var/log/nyagaka")
RECEIVED_LOG = OUTDIR / "received_events.jsonl"

@app.route("/events", methods=["POST"])
def receive_event():
    event = request.get_json(force=True, silent=True)
    if event is None:
        return jsonify({"error": "invalid or missing JSON body"}), 400

    event["received_at"] = datetime.now(timezone.utc).isoformat()

    OUTDIR.mkdir(parents=True, exist_ok=True)
    with open(RECEIVED_LOG, "a") as f:
        f.write(json.dumps(event) + "\n")

    print(f"Received: {event}")
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
