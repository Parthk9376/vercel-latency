from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "q-vercel-latency.json")

with open(DATA_FILE, "r") as f:
    data = json.load(f)


def percentile(values, p):
    values = sorted(values)
    if len(values) == 1:
        return values[0]

    position = (len(values) - 1) * p
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    fraction = position - lower

    return values[lower] + (values[upper] - values[lower]) * fraction


@app.post("/api/latency")
async def latency(request: Request):
    body = await request.json()

    regions = body["regions"]
    threshold = body["threshold_ms"]

    result = {}

    for region in regions:
        rows = [r for r in data if r["region"] == region]

        latencies = [r["latency_ms"] for r in rows]
        uptimes = [r["uptime_pct"] for r in rows]

        result[region] = {
            "avg_latency": sum(latencies) / len(latencies),
            "p95_latency": percentile(latencies, 0.95),
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(1 for x in latencies if x > threshold)
        }

    return result
