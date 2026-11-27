# PolyGen — Generative Text-to-3D Asset Pipeline

> **Assignment Ref:** Infotact Solutions (`ITS/GAI/1279`)  
> **Architecture:** React / Three.js Frontend (Member 1) $\leftrightarrow$ FastAPI Orchestrator (Member 3) $\leftrightarrow$ Text-to-3D Diffusion Pipeline (Member 2)

---

## 1. Repository Structure

```text
PolyGen/
├── API_CONTRACT.md          # Locked v1.0 single source of truth for endpoints & schemas
├── README.md                # Clean-run instructions & module ownership guide
├── .env.example             # Environment variable template (never commit real secrets)
├── frontend/                # [Member 1] React + Three.js / React-Three-Fiber 3D viewer
├── generator/               # [Member 2] TripoSR / ControlNet / Trimesh .glb pipeline
├── backend/                 # [Member 3] FastAPI job queue, SQLite store & asset delivery
└── storage/                 # Runtime .glb assets & SQLite job state (gitignored)
> **Owner:** Member 3 (Backend, Integration & Delivery)[cite: 1, 5]  
> **Contract Reference:** See root [`API_CONTRACT.md`](../API_CONTRACT.md)[cite: 1, 3]

## 1. Local Clean-Environment Setup (Python 3.9+)

From the repository root:

```bash
# 1. Copy environment template (never commit .env)
cp .env.example .env

# 2. Create and activate virtual environment
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r requirements.txt

# 4. Run automated verification suite
pytest -v

# 5. Start the backend server
uvicorn app.main:app --reload --port 8000