"""
collect_metrics.py
==================
EMQX Cloud – Real-Time Broker Metrics Collector

Description
-----------
Polls the EMQX Cloud REST API (v5) at a fixed interval and records broker
performance metrics to a CSV file with timestamps. The collected data
replicates the time-series visible in the EMQX Cloud dashboard:

  - Sessions          : number of active connected clients
  - Subscriptions     : total active topic subscriptions
  - Messages inbound  : messages received by the broker  (recv_msg)
  - Messages outbound : messages sent by the broker       (send_msg)
  - Received packets  : inbound traffic in kilobytes      (recv_oct / 1024)
  - Sent packets      : outbound traffic in kilobytes     (send_oct / 1024)
  - Total packets     : combined traffic in kilobytes

The script appends one row per polling cycle to the output CSV, preserving
all previously collected data across multiple runs.

Usage
-----
  # Default settings (30-second interval, runs indefinitely)
  python collect_metrics.py

  # Custom interval and total duration
  python collect_metrics.py --interval 60 --duration 7200

  # Custom output file
  python collect_metrics.py --output ../data/raw/session_metrics.csv

Arguments
---------
  --interval   INT   Polling interval in seconds          (default: 30)
  --duration   INT   Total duration in seconds; 0=forever (default: 0)
  --output     STR   Output CSV path

Output CSV columns
------------------
  timestamp          : YYYY-MM-DD HH:MM:SS
  sessions           : active connected sessions
  subscriptions      : total active subscriptions
  messages_inbound   : cumulative messages received
  messages_outbound  : cumulative messages sent
  received_kb        : cumulative received bytes / 1024
  sent_kb            : cumulative sent bytes / 1024
  total_kb           : (received + sent) bytes / 1024

Dependencies
------------
  requests >= 2.28

Author
------
  Juliam Diaz – Master's Thesis, 2025
"""

import os
import csv
import time
import argparse
import logging
import requests
from datetime import datetime
from typing import List, Dict

# =============================================================================
# BROKER CREDENTIALS – EMQX Cloud (Serverless)
# =============================================================================

API_BASE_URL = "https://bf19ac0a.ala.eu-central-1.emqxsl.com:8443/api/v5"
API_USER     = "k6656166"
API_PASSWORD = "QscqAridKH.0veRT"

# =============================================================================
# DEFAULT CONFIGURATION
# =============================================================================

SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT   = os.path.join(SCRIPT_DIR, "..", "data", "raw", "collected_metrics.csv")
DEFAULT_INTERVAL = 30   # seconds between polls
DEFAULT_DURATION = 0    # 0 = run indefinitely

CSV_FIELDNAMES = [
    "timestamp",
    "sessions",
    "subscriptions",
    "messages_inbound",
    "messages_outbound",
    "received_kb",
    "sent_kb",
    "total_kb",
]

# =============================================================================
# LOGGING SETUP
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# =============================================================================
# API FUNCTIONS
# =============================================================================

def fetch_clients(session: requests.Session) -> List[Dict]:
    """
    Retrieve the full list of connected clients from the EMQX REST API.

    Handles pagination automatically until all pages have been fetched.

    Parameters
    ----------
    session : requests.Session
        Authenticated HTTP session (Basic Auth pre-configured).

    Returns
    -------
    List[Dict]
        List of client objects returned by GET /api/v5/clients.
        Returns an empty list on request failure.
    """
    clients = []
    page    = 1

    while True:
        try:
            response = session.get(
                "{}/clients".format(API_BASE_URL),
                params={"page": page, "limit": 100},
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()

            batch = payload.get("data", [])
            clients.extend(batch)

            meta        = payload.get("meta", {})
            total       = meta.get("count", len(clients))
            page_size   = meta.get("limit", 100)
            total_pages = -(-total // page_size)  # ceiling division

            if page >= total_pages or not batch:
                break

            page += 1

        except requests.exceptions.RequestException as exc:
            log.error("Failed to fetch /clients (page %d): %s", page, exc)
            break

    return clients


def aggregate_metrics(clients: List[Dict]) -> Dict:
    """
    Aggregate per-client statistics into broker-level totals.

    Parameters
    ----------
    clients : List[Dict]
        Raw client list from fetch_clients().

    Returns
    -------
    Dict
        Aggregated metrics with keys matching CSV_FIELDNAMES (except timestamp).
    """
    sessions      = len(clients)
    subscriptions = sum(c.get("subscriptions_cnt", 0) for c in clients)
    recv_msg      = sum(c.get("recv_msg", 0) for c in clients)
    send_msg      = sum(c.get("send_msg", 0) for c in clients)
    recv_oct      = sum(c.get("recv_oct", 0) for c in clients)
    send_oct      = sum(c.get("send_oct", 0) for c in clients)

    return {
        "sessions":          sessions,
        "subscriptions":     subscriptions,
        "messages_inbound":  recv_msg,
        "messages_outbound": send_msg,
        "received_kb":       round(recv_oct / 1024, 4),
        "sent_kb":           round(send_oct / 1024, 4),
        "total_kb":          round((recv_oct + send_oct) / 1024, 4),
    }


# =============================================================================
# CSV HELPERS
# =============================================================================

def ensure_csv(filepath: str) -> None:
    """Create the CSV file with headers if it does not already exist."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

    if not os.path.isfile(filepath):
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
        log.info("Created new CSV file: %s", os.path.abspath(filepath))
    else:
        log.info("Appending to existing CSV: %s", os.path.abspath(filepath))


def append_row(filepath: str, row: Dict) -> None:
    """Append a single metrics row to the CSV file."""
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writerow(row)


# =============================================================================
# MAIN COLLECTION LOOP
# =============================================================================

def collect(interval: int, duration: int, output: str) -> None:
    """
    Execute the polling loop, writing one CSV row per cycle.

    Parameters
    ----------
    interval : int   Seconds between polls.
    duration : int   Total runtime in seconds (0 = indefinite).
    output   : str   Path to the output CSV file.
    """
    ensure_csv(output)

    auth_session = requests.Session()
    auth_session.auth = (API_USER, API_PASSWORD)
    auth_session.headers.update({"Accept": "application/json"})

    start_time  = time.time()
    cycle_count = 0

    log.info("Starting collection  |  interval=%ds  |  duration=%s",
             interval, "{}s".format(duration) if duration else "indefinite")
    log.info("Output -> %s", os.path.abspath(output))
    log.info("Press Ctrl+C to stop.\n")

    try:
        while True:
            cycle_start = time.time()

            clients = fetch_clients(auth_session)
            metrics = aggregate_metrics(clients)
            ts      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            row = {"timestamp": ts}
            row.update(metrics)
            append_row(output, row)
            cycle_count += 1

            log.info(
                "[%4d] %s | sessions=%d | subs=%d | "
                "in=%d msg | out=%d msg | rx=%.2f KB | tx=%.2f KB",
                cycle_count, ts,
                metrics["sessions"],
                metrics["subscriptions"],
                metrics["messages_inbound"],
                metrics["messages_outbound"],
                metrics["received_kb"],
                metrics["sent_kb"],
            )

            if duration and (time.time() - start_time) >= duration:
                log.info("Duration limit reached (%ds). Stopping.", duration)
                break

            elapsed    = time.time() - cycle_start
            sleep_time = max(0.0, interval - elapsed)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        log.info("\nCollection stopped by user after %d cycle(s).", cycle_count)

    log.info("Total samples collected: %d", cycle_count)
    log.info("Data saved to: %s", os.path.abspath(output))


# =============================================================================
# ENTRY POINT
# =============================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="EMQX Cloud – Broker Metrics Collector"
    )
    parser.add_argument(
        "--interval", type=int, default=DEFAULT_INTERVAL,
        help="Polling interval in seconds (default: {})".format(DEFAULT_INTERVAL)
    )
    parser.add_argument(
        "--duration", type=int, default=DEFAULT_DURATION,
        help="Total duration in seconds; 0 = run forever (default: 0)"
    )
    parser.add_argument(
        "--output", type=str, default=DEFAULT_OUTPUT,
        help="Output CSV path"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    collect(
        interval=args.interval,
        duration=args.duration,
        output=args.output,
    )
