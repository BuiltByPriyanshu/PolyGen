# PolyGen: Generative Text-to-3D Asset Pipeline

> **Status:** Work in progress (Week 1). This README is a temporary placeholder.

PolyGen turns a text prompt into a game-ready, textured 3D asset. Type something like
*"A rusted, medieval broadsword with a glowing blue sapphire in the hilt"* and get an
optimized `.glb` you can inspect in the browser and export to Unreal Engine or Unity.

## Pipeline

```
Text prompt
   │
   ▼
1. Mesh generation      Shap-E / TripoSR  →  raw .obj
   │
   ▼
2. Texture synthesis    Stable Diffusion + ControlNet  →  UV-mapped textures
   │
   ▼
3. Mesh optimization    trimesh / open3d  →  QEM decimation (~500k → ~10k polys)
   │
   ▼
4. Export               .glb / .gltf (PBR materials)
   │
   ▼
5. Web viewer           React + react-three-fiber (rotate, inspect, export)
```

## Tech Stack

| Layer | Tools |
|---|---|
| Generative AI | Shap-E, TripoSR, Stable Diffusion, ControlNet |
| Mesh processing | Python, trimesh, open3d |
| Backend | Python, FastAPI, PyTorch (CUDA) |
| Frontend | React, Three.js, react-three-fiber, drei |

## Project Structure

```
PolyGen/
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app
│   │   ├── config.py
│   │   └── pipeline/
│   │       ├── mesh_gen.py     # text -> raw .obj
│   │       ├── texture_gen.py  # texture synthesis
│   │       ├── optimize.py     # decimation / cleanup
│   │       └── export.py       # .glb / .gltf export
│   ├── outputs/                # generated assets (gitignored)
│   └── requirements.txt
├── frontend/                   # Vite + React + react-three-fiber
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- NVIDIA GPU with CUDA (recommended for generation)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Roadmap

- [ ] **Week 1:** Text-to-3D mesh generation (`.obj`) and React canvas rendering it
- [ ] **Week 2:** Texture generation (SD + ControlNet) and UV unwrapping
- [ ] **Mid-project review:** Recognizable geometry, texture mapped onto mesh in viewer
- [ ] **Week 3:** QEM decimation and PBR material support (roughness, metalness, normal maps)
- [ ] **Week 4:** `.glb` / `.gltf` export, HDRI lighting, UI polish
- [ ] **Final review**

## Notes

- Model weights and generated outputs are gitignored; download weights on first run.
- Keep `generate_mesh(prompt) -> path` as a stable interface so the underlying model
  (Shap-E or SD + TripoSR) can be swapped without touching the API or frontend.

## License

TBD
