# UAV Strategic Deconfliction System (4D + ML Enhanced)

This project implements a high‑performance UAV (drone) mission **strategic deconfliction system** capable of validating flight plans against simulated air traffic using **4D geometric checks** and a **Machine Learning pre‑screening filter**.  
It follows a safety‑critical, two‑tiered verification pipeline:

**ML Filter → Geometric Core**

---

## 🚀 Key Features

### **4D Conflict Detection**

- Performs high‑fidelity geometric checks across **X, Y, Z + Time**
- Uses **linear interpolation** between waypoints
- Detects conflicts, closest approach, conflict time, and distance

### **ML Pre‑Screening Filter**

- Trained **Random Forest classifier**
- Filters out **≈75% of non‑conflicting mission pairs**
- Reduces heavy geometric computations → boosts performance & scalability

### **Two-Tiered Architecture**

1. **ML Filter** — probabilistic screening
2. **Geometric Engine** — deterministic safety verification

### **Full‑Stack Deployment**

- **Backend:** Flask API
- **Frontend:** React + Vite + Tailwind + SVG visualizations
- Animated 4D trajectory viewer

### **Detailed Reporting**

Outputs include:

- `status`: CLEAR / CONFLICT
- `conflict_time`
- `conflict_location`
- `minimum_distance`
- ML statistics (filtered count, prediction decision path)

---

## 🏗️ Architecture Overview

```
uav/
├── backend/
│   └── app.py               # Flask REST API
├── Deconfliction_System/
│   ├── src/                 # Core: models, trajectory logic, algorithms
│   └── ml_models/
│       └── conflict_model.pkl   # Required ML model
└── frontend/
    └── src/
        └── App.jsx
```

### **Core Modules**

| Component                        | Description                              |
| -------------------------------- | ---------------------------------------- |
| `models.py`                      | Mathematical & geometric models          |
| `trajectory.py`                  | 4D trajectory interpolation logic        |
| `temporal_checker.py`            | Core conflict detection engine           |
| `MLEnhancedDeconflictionService` | ML → Geometry orchestrator               |
| `app.py`                         | Flask REST API server                    |
| React Frontend                   | UI, dashboards, SVG flight visualization |

---

## ⚙️ Installation & Setup

This project uses **Python for backend logic** and **Node.js for the frontend**.

### **Prerequisites**

- Python **3.8+**
- Node.js **18+**
- npm
- Git

---

## 🐍 Backend Setup (Python)

From the project root (`uav/`):

```bash
python -m venv venv_backend
# Windows:
venv_backend\Scripts\activate
# macOS/Linux:
source venv_backend/bin/activate
```

Install dependencies:

```bash
pip install Flask Flask-CORS numpy scikit-learn
```

---

## 🤖 ML Model Setup

1. Ensure folder exists:

```
Deconfliction_System/ml_models
```

2. Place the required ML file:

```
conflict_model.pkl
```

---

## 🌐 Frontend Setup (React)

```bash
cd frontend
npm install
```

Tailwind CSS is already configured.

---

## ▶️ Running the System

### **1. Start the Backend API**

From project root:

```bash
python backend/app.py
```

Expected:  
`Server running at http://localhost:5000`

---

### **2. Start the Frontend**

```bash
cd frontend
npm run dev
```

Expected:  
`Local: http://localhost:5173`

---

## 💻 Usage Guide

1. Open the frontend URL (e.g., `http://localhost:5173`)
2. Load a scenario:
   - **Conflict Scenario** (guaranteed collision)
   - **Clear Scenario**
3. Toggle **ML ON / ML OFF**
4. Click **Run Deconfliction**
5. View:
   - ML filtered count
   - Final decision (CLEAR/CONFLICT)
   - Minimum separation distance
   - Conflict time
6. Play/Pause trajectory animation
7. Observe closest approach approaching **0.00m** at ~90s in the conflict scenario

---

## 📊 Notes on Performance

- ML model filters **≈75%** of pairs → geometric engine runs only on high‑risk trajectories
- Ensures scalability for real‑time UTM‑like systems
- Supports multiple mission pair checks

---

## 📁 Future Extensions

- RNN/LSTM‑based trajectory prediction
- Integration with real ADS‑B traffic
- Drone category rules (MTOW‑based separation)
- WebSocket real‑time monitoring

---

## 🏁 Conclusion

This system demonstrates a **scalable, intelligent, and safety‑focused approach** to UAV mission deconfliction by combining **machine learning** with **deterministic 4D geometry** in a modern full‑stack environment.

---

### 👤 Author

_Your Name_
