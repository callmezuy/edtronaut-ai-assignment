"""
FastAPI Server - Main entry point cho Gucci CEO NPC Simulation.
Cung cấp API endpoint với SSE streaming và giao diện web.
"""

import json
import uuid
import asyncio
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from npc_agent import NPCAgent
from supervisor_agent import SupervisorAgent

# ============================================================
# APP INITIALIZATION
# ============================================================
app = FastAPI(
    title="Gucci CEO NPC Simulation",
    description="AI Co-worker Engine Prototype - Edtronaut Take-home Assignment",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# ============================================================
# IN-MEMORY SESSION STORE
# (Production: Supabase/PostgreSQL)
# ============================================================
sessions: Dict[str, Dict[str, Any]] = {}

# Agent instances
npc_agent = NPCAgent(persona_id="Gucci_CEO")
supervisor_agent = SupervisorAgent(check_interval=3)


def get_or_create_session(session_id: str) -> Dict[str, Any]:
    """Lấy hoặc tạo mới session state."""
    if session_id not in sessions:
        sessions[session_id] = {
            "session_id": session_id,
            "trust_level": 0,
            "frustration_level": 0,
            "supervisor_hint": "",
            "target_module": "Module_1",
            "message_history": [],      # Lịch sử tin nhắn user (cho Supervisor)
            "full_history": [],          # Lịch sử đầy đủ (user + assistant)
            "turn_count": 0,
        }
    return sessions[session_id]


# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the chat interface."""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/api/session/new")
async def create_session():
    """Tạo session mới."""
    session_id = str(uuid.uuid4())[:8]
    session = get_or_create_session(session_id)
    return JSONResponse({
        "session_id": session_id,
        "state": {
            "trust_level": session["trust_level"],
            "frustration_level": session["frustration_level"],
            "turn_count": session["turn_count"],
        },
    })


@app.post("/api/chat/{session_id}")
async def chat_with_npc(session_id: str, request: Request):
    """
    Xử lý tin nhắn và trả về phản hồi qua SSE streaming.
    Luồng: User Message → Supervisor → NPC Agent → Safety → Stream Response
    """
    body = await request.json()
    user_message = body.get("user_message", "").strip()

    if not user_message:
        return JSONResponse({"error": "Empty message"}, status_code=400)

    session = get_or_create_session(session_id)
    session["turn_count"] += 1

    # Lưu tin nhắn user vào history
    session["message_history"].append(user_message)
    session["full_history"].append({"role": "user", "content": user_message})

    # --- Step 1: Supervisor Agent Analysis ---
    supervisor_hint = supervisor_agent.analyze(
        message_history=session["message_history"],
        current_state=session,
    )
    if supervisor_hint:
        session["supervisor_hint"] = supervisor_hint

    # --- Step 2: NPC Agent Processing ---
    assistant_message, updated_state, safety_flag = npc_agent.process_message(
        user_message=user_message,
        current_state=session,
    )

    # Cập nhật session state
    sessions[session_id] = updated_state
    updated_state["full_history"].append({"role": "assistant", "content": assistant_message})

    # --- Step 3: SSE Streaming Response ---
    async def event_generator():
        """Mô phỏng streaming từng token (như gọi LLM thật)."""
        # Gửi metadata trước
        meta = {
            "type": "meta",
            "safety_flag": safety_flag,
            "state": {
                "trust_level": updated_state.get("trust_level", 0),
                "frustration_level": updated_state.get("frustration_level", 0),
                "turn_count": updated_state.get("turn_count", 0),
                "supervisor_active": supervisor_hint is not None,
            },
        }
        yield f"data: {json.dumps(meta)}\n\n"

        # Stream từng từ (mô phỏng token streaming)
        words = assistant_message.split(" ")
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            chunk = {"type": "token", "content": token}
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.03)  # 30ms delay giữa các token

        # Gửi tín hiệu kết thúc
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/session/{session_id}/state")
async def get_session_state(session_id: str):
    """Lấy trạng thái hiện tại của session."""
    session = get_or_create_session(session_id)
    return JSONResponse({
        "session_id": session_id,
        "trust_level": session.get("trust_level", 0),
        "frustration_level": session.get("frustration_level", 0),
        "turn_count": session.get("turn_count", 0),
        "target_module": session.get("target_module", "Module_1"),
        "total_messages": len(session.get("message_history", [])),
    })


@app.get("/api/session/{session_id}/history")
async def get_chat_history(session_id: str):
    """Lấy lịch sử chat."""
    session = get_or_create_session(session_id)
    return JSONResponse({
        "session_id": session_id,
        "history": session.get("full_history", []),
    })


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("  Gucci CEO NPC Simulation - Prototype")
    print("  Open http://localhost:8000 in your browser")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
