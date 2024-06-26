import os
import time
import flask
import asyncio
import websockets
import subprocess
import json
from flask import render_template, request
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

app = flask.Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Enable ProxyFix middleware
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

# Configuration (Get from environment variables or set defaults)
IPHUB_API_KEY = os.environ.get(
    "IPHUB_API_KEY", "MjQ0NTc6emRmVGF5dzltN0pqRFp6a0NqcHF5alVwOFVVMDcxY1U="
)  # Replace with your actual API key
IPHUB_URL = "http://v2.api.iphub.info/ip"  # IPHub API URL


async def measure_websocket_rtt(uri, timeout=4):
    try:
        start_time = time.perf_counter()
        async with websockets.connect(uri, close_timeout=timeout) as websocket:
            await websocket.send("ping")
            await websocket.recv()
            end_time = time.perf_counter()
            rtt = (end_time - start_time) * 1000  # Convert to milliseconds
        return rtt
    except asyncio.TimeoutError:
        print(f"Connection to {uri} timed out")
    except websockets.exceptions.InvalidURI as e:
        print(f"Invalid URI: {e}")
    except Exception as e:
        print(f"Error measuring RTT: {e}")
    return None


@app.route("/")
def index():
    server_start_time = time.perf_counter()
    # Measure latency and detect proxy status using IPHub
    external_latency = None
    proxy_detected = False
    country = "Unavailable"
    hostName = "Unavailable"
    ip_address = request.environ.get("HTTP_X_REAL_IP", request.remote_addr)

    try:
        start_time = time.perf_counter()
        result = subprocess.run(
            [
                "curl",
                f"{IPHUB_URL}/{ip_address}",
                "-H",
                f"X-Key: {IPHUB_API_KEY}",
            ],
            capture_output=True,
            text=True,
            timeout=4,
        )
        end_time = time.perf_counter()

        if result.returncode == 0:
            external_latency = (end_time - start_time) * 1000
            data = json.loads(result.stdout)
            proxy_detected = data.get("block") == 1
            country = data.get("countryName", "Unavailable")
            hostName = data.get("hostname", "Unavailable")
            print("data", data)
        else:
            print(f"Curl command failed with return code {result.returncode}")
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print("Curl command timed out")
    except json.JSONDecodeError:
        print("Failed to parse JSON response from curl")
    except Exception as e:
        print(f"Error measuring external latency: {e}")

    # Measure RTT using WebSocket to a known server (e.g., echo.websocket.org)
    uri = "wss://echo.websocket.events/"  # Example WebSocket server for testing
    rtt = asyncio.run(measure_websocket_rtt(uri, timeout=4))

    # Measure server latency accurately
    server_end_time = time.perf_counter()
    server_latency = (server_end_time - server_start_time) * 1000
    table_data = {
        "Server Latency (ms)": round(server_latency, 2),
        "External IP Latency (ms)": (
            round(external_latency, 2)
            if external_latency is not None
            else "Unavailable"
        ),
        "Round-Trip Time (ms)": round(rtt, 2) if rtt is not None else "Unavailable",
        "Proxy Detected": "Yes" if proxy_detected else "No",
        "Country": country,
        "Host Name": hostName,
    }

    return render_template("index.html", table_html=table_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
