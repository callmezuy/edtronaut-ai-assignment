"""
Supervisor Agent - The "Director" Layer (Part 3).
Agent giám sát ngầm, phát hiện khi người dùng bị kẹt và đưa ra 
chỉ thị ẩn (hidden directive) cho NPC.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, Any, Optional, List
import re


class SupervisorAgent:
    """
    Supervisor Agent hoạt động ở chế độ background.
    Phân tích ngữ cảnh và điều phối NPC bằng cách inject supervisor_hint.
    """

    # Từ khóa cốt lõi của từng Module
    MODULE_KEYWORDS = {
        "Module_1": [
            "group dna", "brand autonomy", "competency", "framework",
            "vision", "entrepreneurship", "passion", "trust",
            "problem statement", "leadership", "culture", "mission",
        ],
        "Module_2": [
            "360", "feedback", "coaching", "rater", "instrument",
            "anonymity", "benchmark", "development", "assessment",
        ],
        "Module_3": [
            "rollout", "cascade", "train-the-trainer", "kpi",
            "measurement", "change management", "regional", "adoption",
        ],
    }

    # Thư viện các chỉ thị ngầm (hints) cho từng tình huống
    HINT_LIBRARY = {
        "semantic_loop": (
            "[SUPERVISOR DIRECTIVE: The user is repeating the same idea. "
            "Acknowledge their persistence, then pivot the conversation. "
            "Suggest a concrete alternative approach, such as a 'Core + Flexible' model, "
            "or advise them to speak with the CHRO for a different perspective.]"
        ),
        "off_topic": (
            "[SUPERVISOR DIRECTIVE: The user has drifted from the core objectives. "
            "Gently redirect them back to the current module's goals. "
            "Reference the competency framework (Vision, Entrepreneurship, Passion, Trust) "
            "to anchor the discussion.]"
        ),
        "high_frustration": (
            "[SUPERVISOR DIRECTIVE: The user has triggered multiple frustration points. "
            "De-escalate by acknowledging the complexity of the challenge. "
            "Offer a structured suggestion: recommend starting with a pilot program "
            "at 2-3 brands before group-wide rollout. Be warmer in tone.]"
        ),
        "stalled_progress": (
            "[SUPERVISOR DIRECTIVE: The user hasn't made progress on key deliverables. "
            "Proactively ask what specific deliverable they're working on. "
            "Offer to discuss the problem statement, competency model, or CEO presentation. "
            "Give them a concrete next step.]"
        ),
        "standardization_stuck": (
            "[SUPERVISOR DIRECTIVE: User is stuck on full standardization vs. autonomy debate. "
            "Give a subtle hint. Suggest a 'Core + Flexible' model where 80% is shared Group DNA "
            "and 20% is customizable per brand. Alternatively, advise them to consult with the CHRO "
            "who can provide the competency framework structure.]"
        ),
    }

    def __init__(self, check_interval: int = 3):
        """
        Args:
            check_interval: Số lượt chat giữa mỗi lần Supervisor đánh giá.
        """
        self.check_interval = check_interval
        self.turn_count = 0
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))

    def analyze(
        self,
        message_history: List[str],
        current_state: Dict[str, Any],
    ) -> Optional[str]:
        """
        Phân tích lịch sử hội thoại và trạng thái hiện tại.
        Trả về supervisor_hint nếu cần can thiệp, None nếu không.
        """
        self.turn_count += 1

        # Chỉ đánh giá sau mỗi check_interval lượt
        if self.turn_count < self.check_interval:
            return None

        # Reset counter
        self.turn_count = 0

        # --- Detection 1: Frustration Threshold ---
        frustration = current_state.get("frustration_level", 0)
        if frustration >= 3:
            return self.HINT_LIBRARY["high_frustration"]

        # --- Detection 2: Semantic Similarity Trap ---
        if len(message_history) >= 3:
            recent = message_history[-3:]
            hint = self._detect_semantic_loop(recent)
            if hint:
                # Kiểm tra thêm nếu loop liên quan đến standardization
                combined = " ".join(recent).lower()
                if any(w in combined for w in ["standardize", "unified", "single system", "rigid"]):
                    return self.HINT_LIBRARY["standardization_stuck"]
                return hint

        # --- Detection 3: Goal Non-Progression ---
        target_module = current_state.get("target_module", "Module_1")
        if len(message_history) >= 5:
            hint = self._detect_goal_stall(message_history[-5:], target_module)
            if hint:
                return hint

        return None

    def _detect_semantic_loop(self, recent_messages: List[str]) -> Optional[str]:
        """
        Phát hiện Semantic Similarity Trap.
        Nếu 3 tin nhắn gần nhất có cosine similarity > 0.85 → loop detected.
        """
        if len(recent_messages) < 3:
            return None

        try:
            tfidf_matrix = self.vectorizer.fit_transform(recent_messages)
            sim_matrix = cosine_similarity(tfidf_matrix)

            # Lấy similarity giữa các cặp tin nhắn (không tính đường chéo)
            avg_similarity = (
                sim_matrix[0][1] + sim_matrix[0][2] + sim_matrix[1][2]
            ) / 3

            if avg_similarity > 0.65:  # Ngưỡng cho TF-IDF (thấp hơn embedding)
                return self.HINT_LIBRARY["semantic_loop"]
        except ValueError:
            # Xử lý trường hợp vectorizer lỗi (tin nhắn quá ngắn)
            pass

        return None

    def _detect_goal_stall(
        self, recent_messages: List[str], target_module: str
    ) -> Optional[str]:
        """
        Phát hiện Goal Non-Progression.
        Nếu người dùng không đề cập từ khóa cốt lõi sau 5 lượt → stalled.
        """
        keywords = self.MODULE_KEYWORDS.get(target_module, self.MODULE_KEYWORDS["Module_1"])
        combined_text = " ".join(recent_messages).lower()

        keyword_hits = sum(1 for kw in keywords if kw in combined_text)

        # Nếu ít hơn 2 từ khóa xuất hiện trong 5 tin nhắn → stalled
        if keyword_hits < 2:
            return self.HINT_LIBRARY["stalled_progress"]

        return None

    def get_analysis_summary(
        self, message_history: List[str], current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Trả về bản phân tích chi tiết (cho debugging/logging).
        """
        summary = {
            "turn_count": self.turn_count,
            "frustration_level": current_state.get("frustration_level", 0),
            "trust_level": current_state.get("trust_level", 0),
            "total_messages": len(message_history),
        }

        if len(message_history) >= 3:
            try:
                recent = message_history[-3:]
                tfidf = self.vectorizer.fit_transform(recent)
                sim = cosine_similarity(tfidf)
                summary["avg_similarity_last_3"] = round(
                    float((sim[0][1] + sim[0][2] + sim[1][2]) / 3), 3
                )
            except ValueError:
                summary["avg_similarity_last_3"] = 0.0

        return summary
