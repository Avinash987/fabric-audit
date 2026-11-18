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

- We use uv python tool to manage project - written in rust very fast, replaces pyenv, venv, pip, req.txt, run commands like source .venv/bin/activate.
- uv python install 3.12
- venv done for you automatically
- pip install fastapi - uv add fastapi
- requirements.txt - pyproject.toml and uv.lock
- source .venv/bin/activate, then the command - uv run pytest
- uv add fastapi uvicorn - adds to project dependencies
- uv add --dev pytest ruff httpx - creates a dependency group called dev.
- FastAPI = framework (routes, validation). Can't listen on a port by itself.
- uvicorn = ASGI server. Opens port 8000, receives HTTP, hands requests to the app.
- ASGI = the standard contract between server and app → servers are swappable.
- uv run uvicorn fabric_audit.main:app --reload
  - fabric_audit.main:app → package.file:variable
  - --reload → restart on file changes (dev only, never in prod)
- `fastapi dev` = wrapper that starts uvicorn; needs fastapi[standard] (extra deps).
- Use uvicorn directly → same command in Docker/k8s later (Day 7).
- uv.lock → exact versions of every package (+ hashes), committed so laptop = CI = Docker.
- .venv/ → ignored; rebuilt anytime with `uv sync`.

## 🏁 Done when

CI is green on GitHub and `/healthz` returns 200 on my laptop. 🎉

**Next up → FA-2:** build a virtual data center with containerlab.
