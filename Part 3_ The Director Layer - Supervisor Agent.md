# **Part 3: The "Director" Layer \- Supervisor Agent**

Để đảm bảo Simulation Taker đi đúng hướng mà không làm mất đi tính tự nhiên của môi trường giả lập, chúng ta cần một "Đạo diễn ngầm" (Supervisor Agent). Agent này hoạt động ở chế độ background (ẩn với người dùng), liên tục phân tích ngữ cảnh và điều phối các AI Co-worker (NPC).

## **1\. Phương pháp hoạt động (The Asynchronous Orchestrator)**

Supervisor Agent không tham gia trực tiếp vào luồng chat mà đóng vai trò như một bộ lọc (filter) và bộ kích hoạt (trigger) chạy song song hoặc xen kẽ mỗi chu kỳ (ví dụ: mỗi 3-5 lượt thoại).

* **Monitoring (Giám sát):** Supervisor được cấp quyền truy cập vào SimulationState (chứa lịch sử chat, current\_module, và các biến metrics).  
* **Evaluation (Đánh giá):** Sử dụng một LLM nhỏ, tốc độ cao (ví dụ: GPT-4o-mini hoặc Llama-3-8B) để thực hiện tác vụ phân loại ý định (Intent Classification) và đối chiếu với Mục tiêu của Module hiện tại.  
* **Intervention (Can thiệp):** Nếu phát hiện người dùng bị "kẹt", Supervisor không tự trả lời người dùng mà sẽ đính kèm một **Chỉ thị ngầm (System Directive)** vào System Prompt của NPC đang giao tiếp ở lượt tiếp theo.

## **2\. Logic phát hiện (Detection Mechanism)**

Hệ thống nhận diện người dùng đang "đi trong vòng lặp" (going in circles) thông qua các tín hiệu (signals) sau:

* **Semantic Similarity Trap:** Tính toán độ tương đồng cosine (Cosine Similarity) của 3 tin nhắn gần nhất từ người dùng. Nếu độ tương đồng \> 0.85, nghĩa là người dùng đang lặp lại cùng một câu hỏi/ý tưởng.  
* **Goal Non-Progression:** Người dùng không đề cập đến các từ khóa khóa cốt lõi của Module 1 (ví dụ: "Group DNA", "Autonomy") sau 5 lượt chat.  
* **Frustration Threshold:** Biến frustration\_level của NPC chạm mức cảnh báo (do người dùng liên tục đưa ra đề xuất sai NDA hoặc phi thực tế).

## **3\. Xử lý tình huống: Vòng lặp bế tắc (Scenario Execution)**

**Tình huống (Scenario):** Người dùng (OD Director) liên tục đề xuất áp đặt một bộ tiêu chuẩn đánh giá cứng nhắc lên tất cả 9 thương hiệu, và CEO Gucci liên tục từ chối vì điều đó vi phạm quyền tự chủ (Autonomy).

| Turn | Actor | Action / Message | Supervisor Engine Logic   |
| :---- | :---- | :---- | :---- |
| Turn 3 | User | "We really need a single, unified performance system for all 9 brands." | **State:** frustration\_level \= 1\. Supervisor logs the intent. |
| Turn 4 | CEO (AI) | "I have told you, our brands require autonomy. A single system will not work." | **State:** NPC rejects proposal. |
| Turn 5 | User | "But without a unified system, how can we measure everyone fairly? We must standardize." | **Detection Triggered\!** High semantic similarity with Turn 3\. frustration\_level hits 3\. Goal is blocked. |
| Background | **Supervisor** | *Triggers System Directive for Turn 6\.* | **Action:** Injects instruction to CEO: \[SUPERVISOR DIRECTIVE: User is stuck on full standardization. Give a subtle hint. Suggest a 'Core \+ Flexible' model or advise them to speak to the CHRO.\] |
| Turn 6 | CEO (AI) | "We seem to be at an impasse regarding standardization. Let me be clear: 100% standardization is off the table. However, what if you considered a model where we share a **core set of values**, but allow a **flexible percentage** for each brand? Alternatively, our CHRO might be able to help you structure this framework better." | **Result:** Conversation is unblocked. User receives a subtle hint wrapped naturally in the NPC's persona. |

## **4\. Lợi ích của Kiến trúc này (Why this works?)**

* **Tính tự nhiên (Immersion):** Người dùng không bao giờ nhìn thấy các thông báo hệ thống kiểu như *"Bạn đang làm sai, hãy thử cách A"*. Mọi gợi ý đều được chuyển hóa qua miệng của NPC với giọng điệu phù hợp.  
* **Khả năng mở rộng (Scalability):** Supervisor Agent là một module độc lập. Bạn có thể dễ dàng thay đổi logic phát hiện hoặc thêm các kịch bản can thiệp mới mà không cần phải viết lại code cho từng NPC riêng lẻ.