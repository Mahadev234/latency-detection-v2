import os
import time
import flask
import socket
import requests

from flask import render_template

app = flask.Flask(__name__)

# Configuration (Get from environment variables or set defaults)
EXTERNAL_IP_MEASUREMENT_URL = os.environ.get(
    "EXTERNAL_IP_MEASUREMENT_URL", "https://api.ipify.org?format=json"
)  # Replace with your actual URL


def measure_rtt(host, port=80, timeout=4):
    try:
        start_time = time.perf_counter()
        with socket.create_connection((host, port), timeout=timeout) as sock:
            end_time = time.perf_counter()
            rtt = (end_time - start_time) * 1000  # Convert to milliseconds
        return rtt
    except socket.timeout:
        print(f"Connection to {host}:{port} timed out")
    except socket.error as e:
        print(f"Socket error: {e}")
    except Exception as e:
        print(f"Error measuring RTT: {e}")
    return None


@app.route("/")
def index():
    # Measure server latency
    start_time = time.perf_counter()  # More accurate timing in Python
    time.sleep(0.01)  # Example: 10ms delay
    end_time = time.perf_counter()
    server_latency = (end_time - start_time) * 1000

    # Measure latency from external IP using an external service
    external_latency = None
    try:
        start_time = time.perf_counter()
        response = requests.get(EXTERNAL_IP_MEASUREMENT_URL, timeout=4)
        end_time = time.perf_counter()
        if response.status_code == 200:
            data = response.json()
            external_latency = (end_time - start_time) * 1000
        else:
            print(f"Received non-200 response: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error measuring external latency: {e}")

    # Measure RTT using socket to a known server (e.g., Google DNS)
    rtt = measure_rtt("8.8.8.8", 80, timeout=4)

    # Proxy detection logic (simplified example - enhance as needed)
    proxy_detected = flask.request.headers.get("X-Forwarded-For") is not None

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
