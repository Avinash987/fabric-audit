# FA-1 · Kickoff: get fabric-audit off the ground

**Sprint:** Offer Sprint · Day 1 · ⏱️ ~90 min
**Type:** Story · **Priority:** High

---

## 📖 The story

> 💬 **Your lead, Monday morning:**
> "We keep finding cables plugged into the wrong port, and we only catch them by walking the floor.
> I want a service that knows how the racks _should_ be cabled. Later it'll check that against reality.
> Today, just get the project started: running, tested, with CI on. Keep it small."

**As an** audit engineer
**I want** a service that knows the expected cabling
**So that** later it can catch wrong cables automatically

---

## ✅ Acceptance criteria

- [x] Project runs on **Python 3.12** with FastAPI, pytest and ruff
- [x] `GET /healthz` returns **200**
- [x] Models exist for **Device**, **Interface** and **Link** (device A port → device B port)
- [x] **3 tests** pass
- [x] **GitHub Actions** runs ruff and pytest on every push, and it's green

---

## 🧩 Tasks

- [x] 1. Set up the project (Python 3.12, dependencies, `.gitignore`)
- [x] 2. Add `/healthz` and the models
- [x] 3. Write the tests and the CI workflow
- [x] 4. Commit and push

---

## 🤔 Think about it

- A cable has two ends. Is **A → B** the same as **B → A**?
- What's a _bad_ link? (Hint: can a port connect to itself?)
- Why should `/healthz` stay dumb and not check anything else?

---

## 📝 My notes

### ⚡ TL;DR: 5 things to remember
1. **uv** does everything (Python, venv, deps, run). Commit `uv.lock`, ignore `.venv/`.
2. **FastAPI** is the app and **uvicorn** is the server. **ASGI** is the contract between them.
3. **A cable has no direction.** Keep both ends as given and compare with `key()`, which sorts them.
4. **Reject bad input; never quietly fix it.** An audit tool must not hide mistakes.
5. **`/healthz` = "am I alive?"**, nothing more. Dependency checks go in `/readyz`.

---

### 🛠️ uv: one tool replaces five

| Old way | uv way |
|---|---|
| `pyenv install 3.12` | `uv python install 3.12` |
| `python -m venv .venv` | automatic |
| `pip install fastapi` | `uv add fastapi` |
| `pip install pytest` (dev) | `uv add --dev pytest ruff httpx` → `dev` group |
| `requirements.txt` | `pyproject.toml` + `uv.lock` |
| `source .venv/bin/activate && pytest` | `uv run pytest` |
| rebuild env | `uv sync` |

- `uv.lock` holds the exact version and hash of every package. **Commit it**, so laptop = CI = Docker.
- `.venv/` is **ignored**. It's disposable, and `uv sync` rebuilds it.
- uv is written in Rust, so it's very fast.

---

### 🌐 How a request reaches my code

```
curl ──HTTP──▶ uvicorn (server, :8000) ──ASGI──▶ FastAPI app ──▶ my route
```

- **FastAPI** = framework: routes and validation. It **can't** open a port by itself.
- **uvicorn** = ASGI server: opens the port, receives HTTP, hands each request to the app.
- **ASGI** = the standard contract between them, so the server can be swapped.

```bash
uv run uvicorn fabric_audit.main:app --reload
#              └─package─┘ └file┘ └var┘  └ dev only: restart on save
```

- `fastapi dev` is just a wrapper around uvicorn and needs `fastapi[standard]`.
  I use **uvicorn directly** so it's the same command in Docker/k8s later (Day 7).

---

### 🧱 Data model decisions

| Decision | Why |
|---|---|
| `Link.key()` puts the smaller end first | LLDP reports each cable **twice**, once from each end. A→B and B→A must count as one cable. |
| Each end in the key is **(device, port)** | With only the device, a cable in the **wrong port** gets the same key as the right one, and the audit misses it. |
| Keep the ends **as given**; normalize only in `key()` | My first version reordered the ends in a before-validator. Keeping the raw data is simpler, and findings can show what was actually reported. |
| `Interface` fields are `device` and `port` | Was `device_name` and `name`, which was confusing. A field name should make sense **outside its class** (in JSON, logs, dicts): `"port": "eth1"`, not `"name": "eth1"`. |
| Same device on both ends → `ValidationError` | A port can't cable to its own device. **Reject, never quietly fix.** |
| Unknown role / empty name → `ValidationError` | Same rule: bad input should fail loudly. |
| Models are **frozen** | Hashable, so links fit in sets and dict keys. Later, "plan vs. observed" becomes a **set difference**. |

---

### 🔁 Rethink: why A→B = B→A (from basics)

**One cable, three rows.**

```
 spine1 [eth1] ════════ [eth3] leaf1
```

| Source | Rows | What it says |
|---|---|---|
| Plan (one human) | 1 | `spine1:eth1, leaf1:eth3` |
| spine1's LLDP | 1 | `spine1:eth1 → leaf1:eth3` |
| leaf1's LLDP | 1 | `leaf1:eth3 → spine1:eth1` |

Each switch puts **itself first**. So with a plain field-by-field compare, leaf1's row ≠ the plan row, and it's flagged **unexpected** even though the cable is perfect.
→ 2,000 good cables = **2,000 false alarms**. Nobody trusts the tool after day one.
Writing the plan the other way round doesn't help; the problem just moves to spine1's row.

**Idea 1: store both directions** (like an adjacency list). It's rejected:
- one unplugged cable → **2** missing alarms
- one switch unreachable → its cables show as **missing** even though they're fine
- `len(plan)` = 4,000 for 2,000 cables

**Idea 2: canonical form.** It's the one I picked. Write every cable one fixed way, **smaller end first**. Then:
- one key per cable, so `len(plan)` = 2,000
- one switch's report is enough to match
- one unplugged cable = 1 alarm

**Bug I hit:** my first key used **device names only**, so `leaf1:eth3` and `leaf1:eth4` got the same key, and a wrong-port cable passed. That's the exact bug this project exists to catch. The fix is to make each end `(device, port)`.

**Testing lessons**
- My tests were **green while the code was wrong**: the test that would catch it was skipped. Green ≠ correct.
- Test 2b (different cables ≠ same key) guards against a `key()` that's too loose.
- A good test changes **one thing**, here just the port.
- A test you've never seen fail might check nothing. Break the code on purpose once.

**Python bits**
- Tuples compare element by element: device first, then port if the devices are equal.
- Tuples are hashable and lists aren't, so keys can go in a set.
- The other canonical form: `frozenset({a, b})`, where `{a, b} == {b, a}`. It has to be **frozen** to be hashable.

---

### 🚦 Ops thinking

- **`/healthz` = liveness.** It checks nothing else. If it checked the DB, a DB outage would make Kubernetes **restart healthy pods**, and that wouldn't fix anything.
- **`/readyz` = readiness** (later). Dependency checks go here, so k8s stops sending traffic instead of restarting.
- **CI = the same commands I run locally**, so green locally means green in CI:
  ```bash
  uv run ruff check .            # lint
  uv run ruff format --check .   # formatting
  uv run pytest -v               # tests
  ```
- **Pinned Python (3.12) + lock file** → no "works on my machine."

---

### 🎤 Interview angle: answer these cold
- Why compare with a sorted `key()` instead of reordering the ends at validation time?
- What exactly breaks if `/healthz` checks the database?
- A teammate says "just use requirements.txt." What do you lose?
- Why do the models need to be frozen for the audit engine?
- What's the difference between FastAPI, uvicorn and ASGI?

## 🏁 Done when

CI is green on GitHub and `/healthz` returns 200 on my laptop. 🎉

**Next up → FA-2:** build a virtual data center with containerlab.
