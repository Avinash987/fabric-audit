# fabric-audit

[![CI](https://github.com/Avinash987/fabric-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/Avinash987/fabric-audit/actions/workflows/ci.yml)

**Catch miscabled data center links automatically.**

In a data center, thousands of cables are plugged in by hand from a cabling plan. Mistakes happen: a cable lands in the wrong port, two cables get swapped, or one is never connected. These are usually found by people walking the floor.

fabric-audit compares **what should be cabled** (the plan) with **what is actually cabled** (what switches report over LLDP), and reports the differences.

> 🚧 **Early stage.** It currently has the data model, a health endpoint, tests and CI. See the [roadmap](#roadmap).

---

## Quickstart

You need [uv](https://docs.astral.sh/uv/). It installs Python 3.12 and every dependency for you.

```bash
git clone https://github.com/Avinash987/fabric-audit.git
cd fabric-audit
uv sync                                    # Python 3.12 + exact versions from uv.lock
uv run uvicorn fabric_audit.main:app --reload
```

In another terminal:

```bash
curl -i localhost:8000/healthz
# HTTP/1.1 200 OK
# {"status":"healthy"}
```

Interactive API docs: <http://localhost:8000/docs>

## Run the checks

These are the same commands CI runs on every push:

```bash
uv run ruff check .            # lint
uv run ruff format --check .   # formatting
uv run pytest -v               # tests
```

---

## The data model

A small spine-leaf fabric, like the one this project targets:

```
     spine1        spine2
       |   \      /   |
       |    \    /    |
       |     \  /     |
       |      \/      |
       |      /\      |
       |     /  \     |
     leaf1         leaf2
       |             |
     host1         host2
```

| Model | What it is | Example |
|---|---|---|
| `Device` | A switch or server, with a role of `spine`, `leaf` or `host` | `leaf1` (leaf) |
| `Interface` | A port on a device | `leaf1` / `eth1` |
| `Link` | One expected cable between two interfaces | `leaf1:eth1 ↔ spine1:eth1` |

```python
from fabric_audit.models import Link

link = Link(
    interface_a={"device": "leaf1", "port": "eth1"},
    interface_b={"device": "spine1", "port": "eth1"},
)
link.key()  # (('leaf1', 'eth1'), ('spine1', 'eth1'))
```

### Design decisions

- **A cable has no direction.** LLDP reports each cable twice, once from each end. `Link.key()` sorts the two ends, so `leaf1→spine1` and `spine1→leaf1` give the same key and count as one cable.
- **Bad input is rejected, never silently fixed.** An unknown role, an empty name, or a link with the same device on both ends raises a `ValidationError`. An audit tool must not hide mistakes in its own input.
- **Models are frozen**, so links can be stored in sets and used as dict keys when the plan is compared with what's observed.
- **`/healthz` checks nothing else.** It's a liveness check. Dependency checks will go in a separate `/readyz`, so a database outage doesn't make Kubernetes restart healthy pods.
- **Python is pinned to 3.12, and dependencies are locked** (`uv.lock`), so a laptop, CI and the container image all run the same versions.

---

## Project layout

```
src/fabric_audit/
  main.py        FastAPI app and /healthz
  models.py      Device, Interface, Link
tests/
  test_app.py    health check, link direction, validation
.github/workflows/
  ci.yml         ruff + pytest on every push
stories/         day-by-day build notes
```

## Tech stack

Python 3.12 · FastAPI · Pydantic v2 · uvicorn · pytest · ruff · uv · GitHub Actions

---

## Roadmap

- [x] Project setup, data model, health check, tests, CI
- [ ] Virtual fabric in containerlab (2 spines, 2 leaves, 2 hosts) with LLDP
- [ ] Collector: read LLDP neighbors and turn them into observed `Link`s
- [ ] Audit engine: missing, unexpected, wrong-port and swapped-pair findings
- [ ] Fault injection: break the lab on purpose and catch it
- [ ] Findings API and a CLI report
- [ ] Docker, Kubernetes (kind) and Terraform
- [ ] Prometheus metrics, a Grafana dashboard, an SLO and alerts
- [ ] AI-assisted triage of findings, with evals

---

*All data in this repo comes from a lab topology. No real network data is used.*
