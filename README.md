# uns-performance-evaluation

## Performance Evaluation of Architectural Design Approaches for Unified Namespace in Industrial Data Systems

> Dataset and analysis scripts supporting the research paper of the same title.

---

## Overview

This repository provides the datasets, preprocessing pipeline, and visualization scripts supporting the performance evaluation presented in the associated paper. The study benchmarks two architectural design approaches for implementing a **Unified Namespace (UNS)** over an EMQX MQTT broker in an industrial data system, comparing their behavior under equivalent load conditions across multiple tag-count scenarios (220 and 1100 tags).

Twenty-four broker performance metrics — spanning session management, message throughput, packet rates, and byte transfer — were collected via the EMQX Cloud REST API, processed into aligned time series, and visualized for side-by-side comparative analysis.

---

## Repository Structure

```
uns-performance-evaluation/
│
├── data/
│   ├── raw/                          # Original time series exported from Grafana (CSV)
│   │   ├── authentication_success.csv
│   │   ├── authorization_allow.csv
│   │   ├── client_authorized.csv
│   │   ├── client_connections.csv
│   │   ├── connected_sessions.csv
│   │   ├── packets_connect.csv
│   │   ├── packets_received.csv
│   │   ├── packets_sent.csv
│   │   ├── packets_subscribe_received.csv
│   │   ├── pingreq_packets.csv
│   │   ├── publish_messages.csv
│   │   ├── received_bytes_rate_per_min.csv
│   │   ├── received_bytes_rate_per_sec.csv
│   │   ├── received_message_rate_per_min.csv
│   │   ├── received_message_rate_per_sec.csv
│   │   ├── received_packets_rate_per_sec.csv
│   │   ├── sent_bytes_rate_per_min.csv
│   │   ├── sent_bytes_rate_per_sec.csv
│   │   ├── sent_message_rate_per_min.csv
│   │   ├── sent_message_rate_per_sec.csv
│   │   ├── sent_packets_rate_per_sec.csv
│   │   ├── subscriptions.csv
│   │   └── topics.csv
│   │
│   └── processed/                    # Aligned and cleaned workbook (output of pipeline)
│       └── mqtt_metrics_processed.xlsx
│
├── scripts/
│   ├── process_data.py               # Python preprocessing pipeline
│   └── plot_mqtt_metrics.m           # MATLAB visualization script
│
└── README.md
```

---

## Dataset Description

### Raw Data (`data/raw/`)

Each CSV file corresponds to one MQTT broker metric. Files were exported using Grafana's **Join by field** transform, which merges the two experimental sessions into a single time-indexed table.

**CSV column schema:**

| Column | Type | Description |
|---|---|---|
| `Time` | `datetime` (`YYYY-MM-DD HH:MM:SS`) | Sample timestamp |
| `Schultz Method` | `float` | Metric value during Session 1 (2025-11-05) |
| `Parris Method` | `float` | Metric value during Session 2 (2025-11-05) |

**Metrics and units:**

| File | Metric | Unit |
|---|---|---|
| `authentication_success.csv` | Authentication Success events | count |
| `authorization_allow.csv` | Authorization Allow events | count |
| `client_authorized.csv` | Authorized clients | count |
| `client_connections.csv` | Client connection attempts | count |
| `connected_sessions.csv` | Active connected sessions | count |
| `packets_connect.csv` | CONNECT packets | count |
| `packets_received.csv` | Total packets received | count |
| `packets_sent.csv` | Total packets sent | count |
| `packets_subscribe_received.csv` | SUBSCRIBE packets received | count |
| `pingreq_packets.csv` | PINGREQ packets | messages/sec |
| `publish_messages.csv` | PUBLISH messages | messages/sec |
| `received_bytes_rate_per_min.csv` | Inbound byte rate | Bytes/min |
| `received_bytes_rate_per_sec.csv` | Inbound byte rate | Bytes/sec |
| `received_message_rate_per_min.csv` | Inbound message rate | messages/min |
| `received_message_rate_per_sec.csv` | Inbound message rate | messages/sec |
| `received_packets_rate_per_sec.csv` | Inbound packet rate | packets/sec |
| `sent_bytes_rate_per_min.csv` | Outbound byte rate | Bytes/min |
| `sent_bytes_rate_per_sec.csv` | Outbound byte rate | Bytes/sec |
| `sent_message_rate_per_min.csv` | Outbound message rate | messages/min |
| `sent_message_rate_per_sec.csv` | Outbound message rate | messages/sec |
| `sent_packets_rate_per_sec.csv` | Outbound packet rate | packets/sec |
| `subscriptions.csv` | Active topic subscriptions | count |
| `topics.csv` | Active topics | count |

### Processed Data (`data/processed/`)

`mqtt_metrics_processed.xlsx` is the output of `process_data.py`. It contains one Excel sheet per metric, each with exactly 60 aligned time-stamped samples per session, ready for direct import into MATLAB.

---

## Scripts

### `process_data.py` – Preprocessing Pipeline

**Language:** Python 3.8+  
**Dependencies:** `pandas >= 1.3`, `xlsxwriter >= 3.0`

Reads all raw CSVs, extracts a fixed-length 60-sample block from each experimental session, aligns both blocks temporally, and writes the unified result to the processed Excel workbook.

```bash
cd scripts/
python process_data.py
```

The script automatically resolves paths relative to its own location and can be run from any working directory.

### `plot_mqtt_metrics.m` – Visualization

**Language:** MATLAB R2019b+  
**Dependencies:** none (standard MATLAB toolboxes)

Reads `mqtt_metrics_processed.xlsx` and renders one figure per metric, overlaying the Schultz and Parris time series with zero-padded boundaries, soft grid styling, and a shared horizontal legend.

```matlab
cd scripts/
run('plot_mqtt_metrics.m')
```

---

## Experimental Setup

| Parameter | Value |
|---|---|
| Broker | EMQX |
| Monitoring | Grafana + Prometheus |
| Sampling interval | 2 minutes (raw), aligned to 60 samples |
| Session 1 (Schultz) window | 2025-11-05 13:54 – 15:52 |
| Session 2 (Parris) window | 2025-11-05 13:58 – 15:56 |
| Metrics collected | 24 |

---

## Citation

If you use this dataset or scripts in your research, please cite the associated paper:

```
@article{diaz2025uns,
  title   = {Performance Evaluation of Architectural Design Approaches
             for Unified Namespace in Industrial Data Systems},
  author  = {D{\'i}az, Juliam A. and Delgado, Joaqu{\'i}n and Rey, Juan M. and Duarte, Natalia and Hern{\'a}ndez, Iv{\'a}n},
  year    = {2025}
}
```

---

## License

This repository is provided for academic reproducibility purposes in support of the paper listed above.

---

## Author

**Juliam Diaz**  
Master's Thesis, 2025
