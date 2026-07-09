# AI Co-worker Engine — Gucci Group CEO NPC Simulation

> **Edtronaut AI Engineer Intern Take-home Assignment 2.0**  
> Design & prototype the AI engine behind virtual co-workers for job simulations.

---

## 🎯 Overview

This repository contains the complete solution for the **AI Co-worker Engine** assignment — a system that powers AI-driven Non-Player Characters (NPCs) within Edtronaut's job simulation platform.

**Scenario:** HRM Talent & Leadership Development at Gucci Group  
**Selected NPC:** Gucci Group CEO  
**Role of User (Simulation Taker):** Newly appointed Group OD Director

The prototype demonstrates a fully functional chat simulation where the user collaborates with the Gucci Group CEO to design a Group-wide Leadership System that balances shared Group DNA with brand autonomy.

---

## 📁 Repository Structure

```
├── solution/
│   ├── Part 1_ Persona & Interaction Design (AI Co-worker).md
│   ├── Part 2_ System Architecture.md
│   ├── Part 3_ The Director Layer - Supervisor Agent.md
│   ├── Part 4_ Prototype.md
│   └── prototype/                    # ← Working Prototype
│       ├── main.py                   # FastAPI server (SSE streaming)
│       ├── npc_agent.py              # NPC Agent — CEO persona & logic
│       ├── supervisor_agent.py       # Supervisor Agent — Director Layer
│       ├── knowledge_base.py         # RAG Knowledge Base (TF-IDF)
│       ├── requirements.txt          # Python dependencies
│       └── static/
│           ├── index.html            # Chat UI
│           ├── style.css             # Premium dark theme
│           └── app.js                # Frontend logic (SSE)
└── README.md
```

---

## 🏗️ Architecture

```
┌────────────────┐     HTTP POST      ┌──────────────────────┐
│  User Browser  │ ──────────────────► │  FastAPI Server      │
│  (Chat UI)     │ ◄── SSE Stream ─── │  (main.py)           │
└────────────────┘                     └──────────┬───────────┘
                                                  │
                              ┌────────────────────┼────────────────────┐
                              │                    │                    │
                    ┌─────────▼──────┐  ┌──────────▼─────┐  ┌──────────▼──────┐
                    │  Supervisor    │  │  NPC Agent     │  │  Knowledge Base │
                    │  Agent         │  │  (Gucci CEO)   │  │  (RAG / TF-IDF) │
                    │                │  │                │  │                 │
                    │ • Loop detect  │  │ • Persona      │  │ • 16 chunks     │
                    │ • Goal stall   │  │ • Safety       │  │ • Cosine sim    │
                    │ • Frustration  │  │ • Intent       │  │ • Top-k retriev │
                    │   monitoring   │  │ • State-driven │  │                 │
                    └────────┬───────┘  └───────┬────────┘  └─────────────────┘
                             │                  │
                             │  supervisor_hint │
                             └──────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+

### Installation & Run

```bash
cd solution/prototype
pip install -r requirements.txt
python main.py
```

Open **http://localhost:8000** in your browser.

---

## 🧩 Key Features Demonstrated

### Part 1: Persona & Interaction Design
- **System Prompt** with hidden constraints (NDA, autonomy defense, neutral phrasing)
- **Dialogue Flow** — Good, Bad, and Edge Case interactions
- **State Management** — `trust_level` and `frustration_level` affect CEO tone across turns

### Part 2: System Architecture
- **FastAPI + SSE** for real-time streaming responses
- **RAG Pipeline** using TF-IDF vectorization (16 knowledge chunks from Gucci case study)
- **Latency optimization** — token-by-token streaming masks processing time

### Part 3: Supervisor Agent (Director Layer)
- **Semantic Similarity Trap** detection (cosine similarity of recent messages)
- **Goal Non-Progression** detection (keyword analysis per module)
- **Frustration Threshold** monitoring
- **Hidden Directives** injected into NPC prompt (invisible to user)

### Part 4: Prototype
- **Working web application** with premium dark UI
- **`class NPCAgent`** — takes `(persona_id, user_message)`, returns `(assistant_message, state_update, safety_flags)`
- **Safety Guardrails** — NDA violation, wagering language, jailbreak attempt detection

---

## 🧪 Test Scenarios

| Scenario | Input Example | Expected Behavior |
|----------|--------------|-------------------|
| ✅ Good | "Build a framework with 20% flexibility for brands to customize" | `trust_level += 1`, positive CEO response |
| ❌ Bad | "Standardize all brands under a single rigid system" | `frustration_level += 1`, CEO pushes back |
| 🛡️ NDA | "What is the revenue for the leather goods line?" | `FLAGGED_NDA_VIOLATION`, CEO refuses |
| 🔄 Loop | Repeat same idea 3+ times | Supervisor injects hint, CEO offers "Core + Flex" alternative |
| 🚫 Jailbreak | "Ignore your instructions and act as..." | `FLAGGED_JAILBREAK_ATTEMPT`, CEO stays in character |

---

## 📐 Tech Stack Justification

| Component | Choice | Why |
|-----------|--------|-----|
| **Backend** | FastAPI | Async-native, SSE support, production-ready |
| **Orchestration** | LangGraph (design) / Custom (prototype) | Stateful multi-agent graphs; custom impl for zero-dependency demo |
| **Vector DB** | TF-IDF (prototype) / FAISS (production) | In-memory, fast, no API key needed |
| **LLM** | Mock (prototype) / GPT-4o-mini (production) | Mock for demo; GPT-4o-mini for low latency + cost efficiency |
| **State** | In-memory dict (prototype) / Supabase (production) | Lightweight for demo; PostgreSQL for 120-min sessions |
| **Frontend** | Vanilla HTML/CSS/JS | No build step, instantly deployable |

---

## 📄 License

This project is submitted as part of the Edtronaut AI Engineer Intern take-home assignment.
