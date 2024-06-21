import os
import time
import flask
import asyncio
import websockets
import requests

from flask import render_template

app = flask.Flask(__name__)

# Configuration (Get from environment variables or set defaults)
EXTERNAL_IP_MEASUREMENT_URL = os.environ.get(
    "EXTERNAL_IP_MEASUREMENT_URL", "https://api.ipify.org?format=json"
)  # Replace with your actual URL


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
    # Measure latency from external IP using an external service
    external_latency = None
    try:
        start_time = time.perf_counter()
        response = requests.get(
            EXTERNAL_IP_MEASUREMENT_URL, timeout=4, params={"rand": time.time()}
        )
        end_time = time.perf_counter()
        if response.status_code == 200:
            external_latency = (end_time - start_time) * 1000
        else:
            print(f"Received non-200 response: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error measuring external latency: {e}")

    # Measure RTT using WebSocket to a known server (e.g., echo.websocket.org)
    uri = "wss://echo.websocket.events/"  # Example WebSocket server for testing
    rtt = asyncio.run(measure_websocket_rtt(uri, timeout=4))

    # Proxy detection logic (simplified example - enhance as needed)
    proxy_detected = flask.request.headers.get("X-Forwarded-For") is not None

    # Render the page and measure server latency
    start_time = time.perf_counter()
    rendered_page = render_template(
        "index.html",
        table_html={
            "Server Latency (ms)": "Calculating...",
            "External IP Latency (ms)": (
                round(external_latency, 2)
                if external_latency is not None
                else "Unavailable"
            ),
            "Round-Trip Time (ms)": round(rtt, 2) if rtt is not None else "Unavailable",
            "Proxy Detected": "Yes" if proxy_detected else "No",
        },
    )
    end_time = time.perf_counter()
    server_latency = (end_time - start_time) * 1000

    table_data = {
        "Server Latency (ms)": round(server_latency, 2),
        "External IP Latency (ms)": (
            round(external_latency, 2)
            if external_latency is not None
            else "Unavailable"
        ),
        "Round-Trip Time (ms)": round(rtt, 2) if rtt is not None else "Unavailable",
        "Proxy Detected": "Yes" if proxy_detected else "No",
    }

    return render_template("index.html", table_html=table_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
