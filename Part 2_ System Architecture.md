## Part 2: System Architecture (The Engine)

### 1. High-Level Diagram (Cấu trúc Boxes & Arrows)

Kiến trúc được thiết kế dựa trên mô hình luồng tác vụ hướng sự kiện (Event-driven) và quản lý trạng thái tập trung.

**Luồng dữ liệu (Data Flow):**

1. **[User Front-End]** $\rightarrow$ Gửi HTTP POST request (chứa `user_message`, `session_id`, `npc_id`).
2. **[API Gateway - FastAPI]** $\rightarrow$ Tiếp nhận, xác thực request và đẩy vào hệ thống điều phối.
3. **[Orchestration Layer - LangGraph]** $\rightarrow$ Đóng vai trò bộ não trung tâm. LangGraph duy trì một "State Graph" để luân chuyển dữ liệu qua các Nodes:
* $\rightarrow$ **[State Management - Supabase]**: Tải và cập nhật bộ nhớ ngắn hạn (Short-term Memory) và các biến trạng thái (`trust_level`, `frustration_level`).
* $\rightarrow$ **[Retrieval Node - FAISS/Pinecone]**: Hệ thống RAG truy xuất ngữ cảnh tĩnh (Knowledge Base: Gucci DNA, Competency Framework).
* $\rightarrow$ **[Agent Node - LLM API]**: Bơm System Prompt (Persona), RAG Context và State vào LLM để sinh phản hồi.


4. 
**[Output Parser & Safety Guardrail]** $\rightarrow$ Kiểm duyệt văn bản (đảm bảo giọng điệu trung lập, không ngôn ngữ cá cược)  trước khi trả về.


5. **[User Front-End]** $\leftarrow$ Nhận phản hồi dưới dạng Streaming (SSE - Server-Sent Events).

### 2. Cơ chế sử dụng công cụ (Tool Use)

NPC cần tương tác với các công cụ trong môi trường giả lập (in-sim) như *KPI calculator*, *simple A/B simulator*, hoặc *portfolio pack export*.

* **Phương pháp triển khai:** Áp dụng **Function Calling (Tool Calling)** bản địa của các LLM hiện đại.
* **Quy trình thực thi:**
1. Trong System Prompt, LLM được cung cấp schema của các công cụ (ví dụ: `calculate_kpi(budget, target)`).
2. Khi người dùng yêu cầu tính toán, LLM tạm dừng sinh văn bản tự nhiên và xuất ra một JSON chứa tên hàm và tham số.
3. **Orchestration Layer** nhận diện JSON này, kích hoạt một Python function nội bộ thực thi logic tính toán thực tế.
4. Kết quả (Raw Data) được gửi ngược lại cho LLM để AI "đọc hiểu" và trình bày lại bằng ngôn ngữ tự nhiên (Ví dụ: "Dựa trên máy tính KPI, nếu bạn chọn phương án này, tỷ lệ duy trì sẽ tăng 15%.").



### 3. Cân bằng giữa Latency và Quality (Tối ưu Hiệu năng)

Bài toán: Hệ thống RAG phức tạp sẽ gây nghẽn cổ chai, làm mất tính thời gian thực của hội thoại.

| Phương pháp Tối ưu | Cơ chế Hoạt động | Tác động |
| --- | --- | --- |
| **Streaming Responses** | Phân phối các token đầu ra qua Server-Sent Events (SSE) ngay khi LLM bắt đầu sinh text. | Giảm First-Token-Latency (Thời gian chờ từ ngữ đầu tiên) xuống dưới 1 giây. Che giấu hoàn toàn độ trễ xử lý phía sau. |
| **Semantic Caching** | Sử dụng Redis hoặc bộ nhớ đệm Vector để lưu các cặp câu hỏi - câu trả lời có độ tương đồng ngữ nghĩa cao. | Bỏ qua hoàn toàn bước gọi RAG và LLM nếu người dùng hỏi những câu phổ biến (ví dụ: "Nhiệm vụ của Gucci là gì?"). |
| **Asynchronous RAG (Phân luồng)** | LangGraph tách luồng: Gọi LLM tạo phản hồi tức thì (Ví dụ: "Tôi đang xem xét số liệu bạn đưa...") trong khi RAG fetch dữ liệu nặng dưới nền. | Giữ nhịp độ hội thoại tự nhiên, không làm gián đoạn trải nghiệm người dùng. |
| **Model Routing (Định tuyến LLM)** | Dùng LLM nhỏ (Llama-3 8B) cho các tác vụ phân loại ý định (Intent Classification). Chỉ gọi LLM lớn (GPT-4o/Claude 3.5) cho các phản hồi đòi hỏi suy luận phức tạp. | Giảm chi phí API và tăng tốc độ phản hồi trung bình. |


---

Để thể hiện sự am hiểu kỹ thuật sâu sắc trong báo cáo, chúng ta sẽ bóc tách kiến trúc từ mức High-Level (Boxes & Arrows) xuống mức **Low-Level (Technical & Data Flow)**. Ở cấp độ này, chúng ta định nghĩa rõ cấu trúc dữ liệu, schema, các API endpoint và cách LangGraph luân chuyển trạng thái.

Dưới đây là bản thiết kế Low-Level Architecture (sẵn sàng để bạn đưa vào slide dưới dạng code snippet hoặc mô hình dữ liệu).

### 1. Cấu trúc Trạng thái Hệ thống (LangGraph `StateGraph`)

Trong LangGraph, mọi dữ liệu giao tiếp giữa các Agent đều đi qua một object gọi là `State`. Đây là cốt lõi của hệ thống:

```python
from typing import TypedDict, Annotated, List, Dict
from langchain_core.messages import BaseMessage
import operator

class SimulationState(TypedDict):
    session_id: str
    messages: Annotated[List[BaseMessage], operator.add] # Lịch sử chat (append-only)
    current_agent: str # Tác tử đang hold hội thoại (vd: "Gucci_CEO")
    target_module: str # Vị trí trong kịch bản (vd: "Module_1_Problem_Statement")
    user_metrics: Dict[str, int] # vd: {"trust_level": 50, "frustration_level": 0}
    supervisor_hint: str # Tin nhắn chỉ đạo ngầm từ Supervisor cho NPC
    safety_flag: bool # Cờ kiểm duyệt

```

### 2. Thiết kế Cơ sở dữ liệu (Supabase / PostgreSQL)

Hệ thống cần lưu trữ liên tục để giữ context cho mô phỏng dài 120-150 phút.

* **Table `chat_sessions**`:
* `session_id` (UUID - PK)
* `user_id` (UUID)
* `current_module` (Varchar) - Lưu tiến độ (Module 1, 2, 3).
* `metrics` (JSONB) - Lưu `{trust_level, frustration_level}`.


* **Table `chat_messages**`:
* `id` (UUID - PK)
* `session_id` (UUID - FK)
* `role` (Enum: 'user', 'assistant', 'system', 'tool')
* `agent_name` (Varchar) - Để biết câu này là của CEO hay CHRO.
* `content` (Text)



### 3. API Gateway (FastAPI Endpoints)

FastAPI sẽ cung cấp đầu cuối giao tiếp thông qua giao thức **Server-Sent Events (SSE)** để stream từng token về Front-End, giảm thiểu độ trễ cảm nhận (perceived latency).

```python
@app.post("/api/v1/simulation/{session_id}/chat")
async def chat_with_npc(session_id: str, request: ChatRequest):
    # request schema: {"user_message": "...", "requested_agent": "Gucci_CEO"}
    
    # Khởi chạy LangGraph workflow dưới dạng async stream
    async def event_generator():
        async for chunk in app_graph.astream_events(
            {"messages": [HumanMessage(content=request.user_message)]}, 
            version="v1"
        ):
            if chunk["event"] == "on_chat_model_stream":
                yield f"data: {chunk['data']['chunk'].content}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

```

### 4. Chi tiết luồng thực thi bên trong LangGraph (Node & Edge Topology)

Đây là cách các hàm (Nodes) kết nối với nhau dưới tầng code:

1. **Node 1: `load_state_node**`: Fetch lịch sử chat và `user_metrics` từ Supabase dựa trên `session_id`.
2. **Node 2: `supervisor_node**`:
* Đầu vào: Lịch sử tin nhắn + Metrics.
* Logic: Gọi một LLM nhỏ (vd: `gpt-4o-mini`) đánh giá xem người dùng có đang đi lạc đề không. Nếu có, cập nhật `frustration_level += 1` vào Supabase và set biến `supervisor_hint = "Hãy nhắc người dùng quay lại việc xác định Group DNA"`.


3. **Node 3: `rag_retrieval_node**`:
* Sử dụng Embedding Model (vd: `text-embedding-3-small`).
* Truy vấn FAISS/Pinecone với metadata filter: `{"agent_owner": current_agent}` (CEO chỉ lấy tài liệu của CEO).
* Đầu ra: Chuỗi văn bản context.


4. **Node 4: `npc_generation_node**`:
* Khởi tạo Prompt: `System_Prompt_CEO` + `RAG_Context` + `supervisor_hint` (nếu có).
* Gọi LLM (vd: Claude 3.5 Sonnet hoặc GPT-4o) được bind với các Tools (`llm.bind_tools([calculate_kpi])`).


5. **Node 5: `tool_execution_node**`:
* Nếu LLM ở Node 4 trả về `tool_calls`, chuyển hướng sang chạy code Python thực tế tính KPI, sau đó loop ngược kết quả lại Node 4.


6. **Node 6: `safety_parser_node**`:
* Quét regex hoặc dùng Guardrails AI chặn các từ khóa rủi ro (wager language, offensive text) trước khi trả về User. Cập nhật `safety_flag`.



### 5. RAG Pipeline (Low-Level)

Để trả lời cho câu hỏi *"Can I use any vector DB or reranker?"* từ phần FAQ của đề bài:

* **Chunking Strategy:** Tách các tài liệu PDF/CSV của Gucci ra thành các chunk nhỏ (khoảng 500 tokens, overlap 50 tokens) bằng `RecursiveCharacterTextSplitter`.
* **Vector DB:** Dùng **FAISS** (tốc độ nhanh, chạy in-memory tốt cho prototype local) hoặc **Pinecone** (nếu scale production).
* **Reranker (Crucial step):** Sau khi FAISS trả về Top-10 chunks (dựa trên Cosine Similarity), dùng một Cross-Encoder model (vd: `bge-reranker-large`) để chấm điểm lại (re-score) các chunks này dựa trên câu hỏi thực tế của người dùng. Lấy Top-3 chunks đưa vào LLM.
* *Lý giải (đưa vào slide):* Việc thêm Reranker tuy tăng độ trễ khoảng 100-200ms nhưng cải thiện đáng kể chỉ số `hits@k`, giảm hiện tượng Hallucination khi AI tìm kiếm các thông tin chuyên ngành nhân sự phức tạp của Gucci.