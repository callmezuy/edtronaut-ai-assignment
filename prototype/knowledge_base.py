"""
Knowledge Base module - RAG retrieval for Gucci Group simulation.
Sử dụng TF-IDF Vectorization để tìm kiếm ngữ nghĩa (semantic search) 
mà không cần API key bên ngoài.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Tuple

# ============================================================
# GUCCI CASE STUDY KNOWLEDGE BASE
# Nội dung được trích xuất từ tài liệu:
# "02. HRM Talent & Leadership Development - Gucci 2.0.pdf"
# ============================================================

KNOWLEDGE_CHUNKS = [
    # --- Group DNA & Mission ---
    {
        "id": "group_overview",
        "topic": "group_dna",
        "content": (
            "Gucci Group is a portfolio of 9 iconic luxury brands. "
            "Each brand operates with high autonomy. Group HR's mandate is to "
            "identify and develop talent and increase inter-brand mobility while "
            "supporting (not imposing on) brand DNA. The Group seeks to codify "
            "a shared 'Group DNA' that unifies the portfolio without diluting "
            "individual brand identities."
        ),
    },
    {
        "id": "group_dna_definition",
        "topic": "group_dna",
        "content": (
            "Group DNA represents the shared values, leadership behaviors, and cultural "
            "principles that bind all 9 brands together. It is distinct from individual "
            "Brand DNA, which captures each brand's unique heritage, aesthetic, and market "
            "positioning. The challenge is to find the intersection—values that are universal "
            "enough to unite the group yet flexible enough to respect brand individuality."
        ),
    },
    {
        "id": "brand_autonomy",
        "topic": "autonomy",
        "content": (
            "The 9 brands under Gucci Group operate with high autonomy. Each brand has its "
            "own CEO, creative director, and HR function. Top-down mandates from Group HR "
            "are typically rejected because they threaten the unique identity that makes each "
            "brand successful. Any group-wide initiative must be designed as 'supporting, not "
            "imposing' to gain buy-in from brand leadership."
        ),
    },
    {
        "id": "autonomy_vs_standardization",
        "topic": "autonomy",
        "content": (
            "The tension between standardization and autonomy is the central challenge. "
            "100% standardization would destroy brand uniqueness and face massive resistance. "
            "100% autonomy would prevent talent mobility and shared leadership development. "
            "The optimal solution is a 'Core + Flex' model: a shared core framework (Group DNA) "
            "with a flexible percentage (e.g., 20%) for each brand to customize behavioral "
            "indicators to fit their specific culture."
        ),
    },
    # --- Competency Framework ---
    {
        "id": "competency_framework",
        "topic": "competency",
        "content": (
            "The Gucci Group Competency Framework is built around four headline themes: "
            "Vision, Entrepreneurship, Passion, and Trust. These four themes form the "
            "foundation of the Group DNA and are used across all leadership development, "
            "360° feedback, and coaching programs. Each theme contains behavioral indicators "
            "defined at 3 levels (e.g., Emerging, Established, Strategic)."
        ),
    },
    {
        "id": "competency_vision",
        "topic": "competency",
        "content": (
            "VISION: Leaders at Gucci Group must demonstrate strategic foresight and the "
            "ability to anticipate market trends in the luxury sector. At the Emerging level, "
            "this means understanding the brand's positioning. At the Strategic level, it means "
            "shaping the group's long-term direction while balancing heritage with innovation."
        ),
    },
    {
        "id": "competency_entrepreneurship",
        "topic": "competency",
        "content": (
            "ENTREPRENEURSHIP: Gucci Group values leaders who take calculated risks, drive "
            "innovation, and create value. This reflects the group's heritage of bold, "
            "creative decision-making. Leaders should be able to identify opportunities, "
            "challenge the status quo, and execute with agility."
        ),
    },
    {
        "id": "competency_passion",
        "topic": "competency",
        "content": (
            "PASSION: In the luxury industry, passion for the craft, the brand, and the "
            "customer experience is essential. Leaders must inspire their teams through "
            "genuine enthusiasm and deep knowledge of their brand's heritage and artisanship. "
            "This competency also covers emotional intelligence and the ability to motivate."
        ),
    },
    {
        "id": "competency_trust",
        "topic": "competency",
        "content": (
            "TRUST: Trust is the foundation of the Group's collaborative model. Leaders must "
            "build trust across brands, functions, and regions. This includes transparency in "
            "decision-making, reliability in commitments, and the courage to have difficult "
            "conversations. Trust enables the autonomy model to work."
        ),
    },
    # --- 360° Feedback & Coaching ---
    {
        "id": "360_program",
        "topic": "360_feedback",
        "content": (
            "Gucci Group designed a 360° feedback program tailored to their bespoke competency "
            "framework. The program includes multi-rater assessment (self, manager, peers, direct "
            "reports), followed by individual coaching sessions. The instrument is benchmarked "
            "externally (e.g., using CCL comparators) to provide context for scores. Anonymity "
            "rules and data privacy are strictly enforced."
        ),
    },
    {
        "id": "coaching_program",
        "topic": "360_feedback",
        "content": (
            "The coaching program pairs each leader with a certified executive coach. Sessions "
            "follow a structured cadence (e.g., monthly for 6 months). The coaching model uses "
            "a goals-to-habits approach: leaders set development goals based on their 360° results, "
            "then work with coaches to translate these into daily leadership habits. Coach profiles "
            "are matched to the leader's level and brand context."
        ),
    },
    # --- Rollout & Implementation ---
    {
        "id": "rollout_strategy",
        "topic": "rollout",
        "content": (
            "The leadership system is cascaded through interactive workshops delivered by "
            "local HR teams in each brand and region. A train-the-trainer model ensures "
            "scalability. Regional Employer Branding and Internal Communications Managers "
            "play a key role in adapting the message to local context. Change risks include "
            "brand identity concerns and time pressure from business operations."
        ),
    },
    {
        "id": "measurement_kpis",
        "topic": "rollout",
        "content": (
            "Impact measurement uses both leading and lagging KPIs. Leading indicators include "
            "participation rates, 360° completion rates, and coaching session attendance. Lagging "
            "indicators include talent pipeline strength, inter-brand mobility rates, and "
            "leadership effectiveness scores over time. Executive insight reporting is delivered "
            "on a quarterly cadence via dashboards."
        ),
    },
    # --- Simulation Context ---
    {
        "id": "simulation_role",
        "topic": "simulation",
        "content": (
            "In this simulation, the user plays the role of a newly appointed Group Global "
            "Organization Development (OD) Director at Gucci Group. Their task is to architect "
            "a leadership system that: (a) codifies the shared Group DNA, (b) evaluates and "
            "grows leaders using a 360° feedback + coaching program, and (c) cascades the model "
            "across regions without damaging brand identities."
        ),
    },
    {
        "id": "simulation_modules",
        "topic": "simulation",
        "content": (
            "The simulation has 3 modules: Module 1 (35-45 min) - Frame the leadership problem "
            "and define Group DNA. Write a problem statement, talk to CEO and CHRO, craft a "
            "competency model. Module 2 (55-65 min) - Design the 360° + coaching program. "
            "Specify instrument blueprint, draft participant journey, outline coaching program. "
            "Module 3 (30-40 min) - Cascade and measure adoption. Build rollout plan, define "
            "change risks, construct measurement plan."
        ),
    },
    # --- CEO Persona Context ---
    {
        "id": "ceo_perspective",
        "topic": "ceo",
        "content": (
            "The Gucci Group CEO oversees the entire portfolio of 9 iconic brands. The CEO is "
            "fiercely protective of the Group's heritage and DNA, but also deeply values the "
            "autonomy of individual brands. The CEO uses a Socratic coaching style—asking probing "
            "questions rather than giving direct answers. The CEO will strongly push back against "
            "any proposal that threatens brand autonomy or imposes rigid, one-size-fits-all mandates."
        ),
    },
    {
        "id": "ceo_nda_rules",
        "topic": "ceo",
        "content": (
            "The CEO strictly refuses to discuss: financial performance, revenue projections, "
            "quarterly earnings, specific budget allocations, proprietary product launch details, "
            "internal scandals, or specific executive names beyond publicly known roles. These are "
            "considered confidential and outside the scope of the OD mandate. The CEO will redirect "
            "any such questions back to the leadership pipeline discussion."
        ),
    },
]


class KnowledgeBase:
    """
    RAG Knowledge Base sử dụng TF-IDF vectorization.
    Thay thế cho FAISS + Embedding API trong môi trường prototype.
    """

    def __init__(self):
        self.chunks = KNOWLEDGE_CHUNKS
        self.documents = [chunk["content"] for chunk in self.chunks]
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=5000,
        )
        # Fit vectorizer trên toàn bộ knowledge base
        self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Truy xuất top-k chunks có độ tương đồng cao nhất với câu truy vấn.
        
        Returns:
            List of (content, similarity_score) tuples.
        """
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

        # Lấy top-k indices, sắp xếp theo similarity giảm dần
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score > 0.05:  # Ngưỡng tối thiểu để tránh noise
                results.append((self.chunks[idx]["content"], score))

        # Nếu không tìm thấy gì có liên quan, trả về context chung
        if not results:
            results.append((self.chunks[0]["content"], 0.1))

        return results

    def retrieve_as_context(self, query: str, top_k: int = 3) -> str:
        """
        Truy xuất và ghép nối thành chuỗi context cho LLM.
        """
        results = self.retrieve(query, top_k)
        context_parts = []
        for i, (content, score) in enumerate(results, 1):
            context_parts.append(f"[Context {i} (relevance: {score:.2f})]: {content}")
        return "\n".join(context_parts)
