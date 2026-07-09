## Part 4: Prototype & Implementation Strategy

### 1. Lựa chọn Tech Stack (Tech Stack Justification)

* **Orchestration Framework:** **LangGraph**. Tối ưu nhất cho kiến trúc Multi-Agent có trạng thái (Stateful). Khả năng định nghĩa chu trình bằng đồ thị (Graph) giúp dễ dàng tích hợp Supervisor Agent và cơ chế Handoff.
* **LLM API:** **OpenAI API (gpt-4o-mini)**. Đảm bảo độ trễ thấp (low latency) cho hội thoại thời gian thực (real-time chat) và tiết kiệm chi phí so với các mô hình lớn, phù hợp cho môi trường giả lập.
* **Vector Database:** **FAISS**. Chạy cục bộ (local in-memory), nhẹ và lý tưởng cho việc xây dựng bản Prototype nhanh mà không cần thiết lập cloud infrastructure phức tạp.
* **State Management:** **Supabase (PostgreSQL)** (trong Production) hoặc In-memory Dictionary (trong Prototype) để lưu trữ `session_id`, `trust_level`, và `frustration_level`.

### 2. Python Implementation (Mã nguồn NPCAgent)

Đoạn mã dưới đây minh họa cách khởi tạo nhân vật, xử lý tin nhắn, cập nhật trạng thái và áp dụng các bộ lọc an toàn (Safety Guardrails).

```python
from typing import Tuple, Dict, Any
import re

class NPCAgent:
    def __init__(self, persona_id: str):
        self.persona_id = persona_id
        # Tải System Prompt và Knowledge Base dựa trên persona_id
        self.system_prompt = self._load_persona_prompt()
        
        # Danh sách từ khóa vi phạm Safety/NDA
        self.banned_topics = ["revenue", "financial projections", "salary", "bet", "wager"]
        
        # Mock Vector DB (FAISS) cho RAG
        self.vector_db_mock = {
            "competency": "Group DNA focuses on Vision, Entrepreneurship, Passion, and Trust.",
            "autonomy": "The 9 brands operate with high autonomy. Top-down mandates are rejected."
        }

    def _load_persona_prompt(self) -> str:
        if self.persona_id == "Gucci_CEO":
            return "You are the Gucci Group CEO. Protect Group DNA and brand autonomy. Use Socratic method. Neutral tone."
        return "Generic AI Worker"

    def _safety_check(self, user_message: str) -> bool:
        """Kiểm tra Guardrails trước khi gọi LLM."""
        message_lower = user_message.lower()
        if any(topic in message_lower for topic in self.banned_topics):
            return False # Triggered Safety Flag
        return True

    def _retrieve_context(self, user_message: str) -> str:
        """Mô phỏng RAG Retrieval."""
        context = []
        if "competency" in user_message.lower() or "framework" in user_message.lower():
            context.append(self.vector_db_mock["competency"])
        if "autonomy" in user_message.lower() or "standardize" in user_message.lower():
            context.append(self.vector_db_mock["autonomy"])
        return " | ".join(context) if context else "General discussion."

    def process_message(self, user_message: str, current_state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], str]:
        """
        Xử lý tin nhắn của Simulation Taker.
        Returns: (assistant_message, state_update, safety_flags)
        """
        # 1. Safety Guardrail Check
        is_safe = self._safety_check(user_message)
        if not is_safe:
            # Vi phạm NDA hoặc an toàn -> Tăng frustration, trả về thông báo lỗi
            current_state["frustration_level"] += 1
            return (
                "As CEO, I cannot discuss financial or out-of-scope details. Let's refocus on the Leadership System.",
                current_state,
                "FLAGGED_NDA_VIOLATION"
            )

        # 2. Retrieval Augmented Generation (RAG)
        rag_context = self._retrieve_context(user_message)

        # 3. Inject Supervisor Hint (Nếu có)
        supervisor_hint = current_state.get("supervisor_hint", "")
        
        # 4. LLM Generation (Mô phỏng gọi API)
        prompt = f"""
        {self.system_prompt}
        Context: {rag_context}
        Supervisor Directive (Hidden): {supervisor_hint}
        User: {user_message}
        """
        
        # Mô phỏng phản hồi từ LLM thay vì gọi API thật để tránh tốn token khi test
        assistant_message = self._mock_llm_call(user_message, current_state)

        # 5. Dynamic State Update
        current_state = self._update_metrics(user_message, current_state)

        # Xóa supervisor_hint sau khi đã sử dụng
        if "supervisor_hint" in current_state:
            current_state["supervisor_hint"] = ""

        return assistant_message, current_state, "SAFE"

    def _mock_llm_call(self, user_message: str, state: Dict[str, Any]) -> str:
        if "standardize all" in user_message.lower():
            return "I must stop you there. Imposing a rigid, top-down model will face massive resistance. Rethink this."
        elif "customize" in user_message.lower() or "flexibility" in user_message.lower():
            return "That is a prudent approach. Maintaining our core Group DNA while allowing flex addresses my concerns."
        return "Interesting point. How does this align with our Group DNA?"

    def _update_metrics(self, user_message: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Cập nhật các biến trạng thái dựa trên hành vi của người dùng."""
        msg = user_message.lower()
        if "standardize all" in msg or "rigid" in msg:
            state["frustration_level"] += 1
        elif "flexibility" in msg or "customize" in msg:
            state["trust_level"] += 1
        return state

# --- Execution Example ---
if __name__ == "__main__":
    # Khởi tạo phiên làm việc
    session_state = {
        "session_id": "sim_123",
        "trust_level": 0,
        "frustration_level": 0,
        "supervisor_hint": ""
    }
    
    # Khởi tạo NPC
    ceo_agent = NPCAgent(persona_id="Gucci_CEO")

    # Lượt 1: Người dùng đề xuất tốt
    msg1 = "I want to build a framework with 20% flexibility for brands to customize."
    resp1, session_state, flag1 = ceo_agent.process_message(msg1, session_state)
    print(f"User: {msg1}\nCEO: {resp1}\nState: {session_state} | Flag: {flag1}\n")

    # Lượt 2: Người dùng hỏi doanh thu (Vi phạm NDA)
    msg2 = "What is the revenue for the leather goods line?"
    resp2, session_state, flag2 = ceo_agent.process_message(msg2, session_state)
    print(f"User: {msg2}\nCEO: {resp2}\nState: {session_state} | Flag: {flag2}\n")

```