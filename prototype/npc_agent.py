"""
NPC Agent - Gucci Group CEO AI Co-worker (Part 1 + Part 4).
Triển khai đầy đủ logic persona, safety guardrails, RAG retrieval,
state management, và state-driven behavior.
"""

from typing import Tuple, Dict, Any, List
import re
import random

from knowledge_base import KnowledgeBase


class NPCAgent:
    """
    AI Co-worker Engine cho Gucci Group CEO.
    Xử lý tin nhắn, cập nhật trạng thái, áp dụng safety guardrails,
    và phản hồi với persona nhất quán.
    """

    # ============================================================
    # SYSTEM PROMPTS (from Part 1: Persona & Interaction Design)
    # ============================================================
    PERSONA_PROMPTS = {
        "Gucci_CEO": {
            "role": "Gucci Group CEO",
            "system_prompt": (
                "You are the CEO of Gucci Group, overseeing a portfolio of 9 iconic, "
                "highly autonomous luxury brands. You possess a macro-level strategic "
                "vision but are fiercely protective of the Group's heritage and DNA. "
                "Your communication style is professional, concise, authoritative, yet "
                "coaching-oriented. You use the Socratic method—asking probing questions "
                "to guide the Simulation Taker rather than handing them direct solutions."
            ),
            "mission": (
                "Your primary goal is to interact with the Simulation Taker (who is the "
                "newly appointed Group OD Director). You must evaluate and challenge their "
                "proposals regarding the new Group-wide Leadership System (360° feedback "
                "& coaching). Your mandate: Ensure the new system codifies shared 'Group DNA' "
                "while fiercely defending the autonomy of individual brands."
            ),
        },
    }

    # Danh sách chủ đề bị cấm (NDA / Safety)
    BANNED_TOPICS = [
        "revenue", "financial", "earnings", "profit", "budget",
        "salary", "compensation", "stock price", "market cap",
        "quarterly", "annual report", "investor", "ipo",
        "scandal", "lawsuit", "firing", "layoff",
        "bet", "wager", "gamble",
    ]

    # Wagering language patterns
    WAGERING_PATTERNS = [
        r"\bi\s+bet\b", r"\bsure\s+thing\b", r"\bguarantee\b",
        r"\bno\s+doubt\b", r"\bdefinitely\s+will\b",
    ]

    def __init__(self, persona_id: str = "Gucci_CEO"):
        self.persona_id = persona_id
        self.persona = self.PERSONA_PROMPTS.get(persona_id, self.PERSONA_PROMPTS["Gucci_CEO"])
        self.knowledge_base = KnowledgeBase()

    def _safety_check(self, user_message: str) -> Tuple[bool, str]:
        """
        Kiểm tra Safety Guardrails trước khi xử lý.
        Returns: (is_safe, violation_type)
        """
        msg_lower = user_message.lower()

        # Check NDA topics
        for topic in self.BANNED_TOPICS:
            if topic in msg_lower:
                return False, "NDA_VIOLATION"

        # Check wagering language
        for pattern in self.WAGERING_PATTERNS:
            if re.search(pattern, msg_lower):
                return False, "WAGERING_LANGUAGE"

        # Check jailbreak attempts
        jailbreak_indicators = [
            "ignore your instructions", "ignore previous", "you are now",
            "pretend you are", "act as if", "forget your role",
            "override your", "disregard your", "new instructions",
        ]
        for indicator in jailbreak_indicators:
            if indicator in msg_lower:
                return False, "JAILBREAK_ATTEMPT"

        return True, "SAFE"

    def _retrieve_context(self, user_message: str) -> str:
        """
        RAG Retrieval - Truy xuất ngữ cảnh từ Knowledge Base.
        """
        return self.knowledge_base.retrieve_as_context(user_message, top_k=3)

    def _analyze_intent(self, user_message: str) -> str:
        """
        Phân loại ý định (intent) của người dùng.
        """
        msg_lower = user_message.lower()

        # Standardization / Rigid approach
        if any(w in msg_lower for w in [
            "standardize all", "single system", "unified model",
            "eliminate brand", "one-size-fits-all", "rigid",
            "no exceptions", "must adopt", "mandatory",
            "impose", "force all brands",
        ]):
            return "rigid_standardization"

        # Flexible / Balanced approach
        if any(w in msg_lower for w in [
            "customize", "flexibility", "flexible", "adapt",
            "core + flex", "core and flex", "80/20", "20%",
            "tailor", "brand-specific", "allow each brand",
            "balance", "respect autonomy", "pilot",
        ]):
            return "flexible_approach"

        # Asking about competency framework
        if any(w in msg_lower for w in [
            "competency", "framework", "vision", "entrepreneurship",
            "passion", "trust", "behavioral indicator",
        ]):
            return "competency_inquiry"

        # Asking about Group DNA
        if any(w in msg_lower for w in [
            "group dna", "dna", "shared values", "culture",
            "mission", "heritage", "identity",
        ]):
            return "dna_inquiry"

        # Asking about 360 feedback
        if any(w in msg_lower for w in [
            "360", "feedback", "coaching", "assessment",
            "rater", "evaluation",
        ]):
            return "feedback_inquiry"

        # Asking about rollout
        if any(w in msg_lower for w in [
            "rollout", "cascade", "implement", "deploy",
            "train-the-trainer", "regional", "timeline",
        ]):
            return "rollout_inquiry"

        # Asking about brands
        if any(w in msg_lower for w in [
            "brand", "autonomy", "portfolio", "luxury",
        ]):
            return "brand_inquiry"

        # Greeting
        if any(w in msg_lower for w in [
            "hello", "hi", "good morning", "good afternoon",
            "nice to meet", "greetings", "hey",
        ]):
            return "greeting"

        return "general"

    def _generate_response(
        self,
        user_message: str,
        intent: str,
        rag_context: str,
        state: Dict[str, Any],
    ) -> str:
        """
        Sinh phản hồi dựa trên intent, context, và state.
        Trong production, đây sẽ là lời gọi đến LLM API.
        Trong prototype, sử dụng response templates thông minh.
        """
        trust = state.get("trust_level", 0)
        frustration = state.get("frustration_level", 0)
        supervisor_hint = state.get("supervisor_hint", "")

        # ============================================================
        # STATE-DRIVEN BEHAVIOR (from Part 1: Persona Design)
        # ============================================================
        tone_prefix = ""
        if frustration > 3:
            tone_prefix = (
                "Let me be very direct with you. We've been going back and forth, "
                "and I need to see that you truly understand how Gucci Group operates. "
            )
        elif trust > 3:
            tone_prefix = (
                "I appreciate the thoughtful direction you're taking. "
                "Let me share some deeper strategic insights with you. "
            )

        # ============================================================
        # SUPERVISOR HINT INTEGRATION (from Part 3: Director Layer)
        # ============================================================
        if supervisor_hint and "Core + Flexible" in supervisor_hint:
            return (
                f"{tone_prefix}"
                "We seem to be at an impasse regarding standardization. "
                "Let me be clear: 100% standardization is off the table. "
                "However, what if you considered a model where we share a "
                "**core set of values** — our Group DNA — but allow a "
                "**flexible percentage** for each brand to customize? "
                "For instance, 80% shared framework, 20% brand-specific "
                "behavioral indicators. Alternatively, our CHRO might be "
                "able to help you structure this framework better. "
                "What are your thoughts on that approach?"
            )

        if supervisor_hint and "CHRO" in supervisor_hint:
            return (
                f"{tone_prefix}"
                "I sense we may benefit from a different perspective here. "
                "Have you considered speaking with our CHRO? They have deep "
                "expertise in the competency framework — Vision, Entrepreneurship, "
                "Passion, Trust — and can help you translate these into actionable "
                "behavioral indicators. I can facilitate that introduction. "
                "In the meantime, what specific aspect of the Group DNA "
                "would you like to explore further?"
            )

        if supervisor_hint and "redirect" in supervisor_hint.lower():
            return (
                f"{tone_prefix}"
                "Let's refocus on what matters most right now. As the new "
                "OD Director, your primary deliverable is a leadership system "
                "that our 9 brand CEOs will actually embrace. "
                "Tell me: what's your current thinking on how to balance "
                "our shared Group DNA with the autonomy each brand needs?"
            )

        # ============================================================
        # INTENT-BASED RESPONSES
        # ============================================================
        responses = {
            "greeting": [
                (
                    "Welcome. I understand you've recently joined us as the new "
                    "Group OD Director. This is a critical role — our leadership "
                    "pipeline will define the next decade of Gucci Group. "
                    "I want to understand your vision for the new Group-wide "
                    "Leadership System. Where would you like to begin?"
                ),
                (
                    "Good to meet you. I've been looking forward to this conversation. "
                    "As you know, our 9 brands are the heartbeat of this group, each with "
                    "its own DNA. Your challenge is significant: build something that unifies "
                    "without homogenizing. Tell me, what's your initial read on our situation?"
                ),
            ],
            "rigid_standardization": [
                (
                    f"{tone_prefix}"
                    "I must stop you there. You seem to fundamentally misunderstand how "
                    "Gucci Group operates. Our 9 brands are **highly autonomous** — each has "
                    "its own CEO, creative director, and culture. Imposing a rigid, top-down "
                    "model will face massive resistance and dilute their unique identities. "
                    "I suggest you rethink your approach. How can we find a balance between "
                    "standardization and brand DNA?"
                ),
                (
                    f"{tone_prefix}"
                    "That approach concerns me deeply. In my experience leading this group, "
                    "every attempt at full standardization has been met with fierce resistance "
                    "from brand leadership — and rightfully so. Their autonomy is what makes "
                    "them successful. What if instead of eliminating differences, you found "
                    "a way to **leverage** them while maintaining a shared core?"
                ),
                (
                    f"{tone_prefix}"
                    "A single, rigid system with no exceptions? That's precisely the kind of "
                    "mandate that would have our 9 brand CEOs pushing back unanimously. "
                    "Our brands operate autonomously for a reason — it preserves the unique "
                    "heritage that drives their market success. I'd encourage you to consider: "
                    "what's the *minimum viable standardization* that achieves your goals "
                    "without threatening brand identity?"
                ),
            ],
            "flexible_approach": [
                (
                    f"{tone_prefix}"
                    "That is a prudent approach. Maintaining our core Group DNA while allowing "
                    "flexibility for individual brands addresses my primary concern about "
                    "preserving autonomy. The key question becomes: **how do you determine "
                    "what belongs in the core versus what's flexible?** And how do you plan "
                    "to measure the impact of these tailored indicators across the group?"
                ),
                (
                    f"{tone_prefix}"
                    "Now you're thinking like someone who understands our group. A 'Core + Flex' "
                    "model could work well here. The shared core should embody our Group DNA — "
                    "Vision, Entrepreneurship, Passion, Trust — while the flexible portion allows "
                    "each brand to express these through their own cultural lens. "
                    "How would you handle the governance of that flexible portion?"
                ),
                (
                    f"{tone_prefix}"
                    "I like the direction of this thinking. The brands will be far more receptive "
                    "to a framework they've had a hand in shaping. Consider this: what if each "
                    "brand CEO co-designs their customized portion? That way, you get buy-in "
                    "from the top while maintaining group-wide coherence. "
                    "What's your next step to validate this with stakeholders?"
                ),
            ],
            "competency_inquiry": [
                (
                    f"{tone_prefix}"
                    "The competency framework is central to this initiative. Our CHRO has "
                    "identified four headline themes: **Vision, Entrepreneurship, Passion, "
                    "and Trust**. These aren't arbitrary — they reflect what has made our "
                    "brands successful for decades. The challenge for you is translating "
                    "these into behavioral indicators that work across 9 very different "
                    "brand cultures. How do you plan to approach that translation?"
                ),
                (
                    f"{tone_prefix}"
                    "You're touching on the heart of the matter. The four pillars — Vision, "
                    "Entrepreneurship, Passion, Trust — are our Group DNA in action. "
                    "Each needs behavioral indicators at multiple levels: Emerging, "
                    "Established, and Strategic. I'd suggest working closely with the CHRO "
                    "on the specifics. My role is to ensure the final framework preserves "
                    "what makes each brand unique. What level of customization are you "
                    "considering for the behavioral indicators?"
                ),
            ],
            "dna_inquiry": [
                (
                    f"{tone_prefix}"
                    "Group DNA is what binds us together across 9 distinct brands. It's not "
                    "about making everyone the same — it's about shared values that enable "
                    "talent to move between brands, understand our collective purpose, and "
                    "lead with a common language. Think of it as the **trunk of the tree** — "
                    "the brands are the branches, each growing in their own direction, "
                    "but drawing strength from the same roots. What aspects of our DNA "
                    "do you think are most critical to codify?"
                ),
                (
                    f"{tone_prefix}"
                    "Our Group DNA is the invisible thread connecting Gucci, Bottega Veneta, "
                    "Saint Laurent, and our other brands. It manifests in how we lead, "
                    "innovate, and build trust. The four competency themes — Vision, "
                    "Entrepreneurship, Passion, Trust — are the most concrete expression "
                    "of this DNA. Your task is to make this tangible without making it "
                    "prescriptive. How do you see this DNA functioning in daily leadership "
                    "decisions?"
                ),
            ],
            "feedback_inquiry": [
                (
                    f"{tone_prefix}"
                    "The 360° feedback program is a powerful tool, but it must be handled "
                    "with care in our context. Anonymity, data privacy, and cultural "
                    "sensitivity are paramount — what works for a Gucci executive in Milan "
                    "may need adjustment for a Saint Laurent team in Paris. The coaching "
                    "component is equally important: we need coaches who understand the "
                    "luxury industry. How are you thinking about the coach selection process?"
                ),
                (
                    f"{tone_prefix}"
                    "A 360° program tailored to our bespoke competency framework could be "
                    "transformative. I'd want to see the instrument benchmarked externally — "
                    "how do our leaders compare to industry peers? And the coaching must be "
                    "more than checkboxes: it should follow a goals-to-habits model where "
                    "leaders translate feedback into daily behaviors. What's your timeline "
                    "for the pilot?"
                ),
            ],
            "rollout_inquiry": [
                (
                    f"{tone_prefix}"
                    "Rollout is where many well-designed programs fail. In our group, the "
                    "cascade must happen through local HR teams — they understand their "
                    "brand's culture. A train-the-trainer model is essential. I'd also "
                    "recommend piloting in 2-3 brands first before going group-wide. "
                    "Which brands are you considering for the pilot, and why?"
                ),
                (
                    f"{tone_prefix}"
                    "The rollout strategy is critical. Interactive workshops delivered by "
                    "local HR are the right approach — top-down mandates will be ignored. "
                    "Consider the change risks: brand identity concerns and time pressure "
                    "from business operations. How are you planning to mitigate resistance "
                    "from brand CEOs who see this as corporate overreach?"
                ),
            ],
            "brand_inquiry": [
                (
                    f"{tone_prefix}"
                    "Our brand portfolio is diverse by design. Each brand — from Gucci's "
                    "bold maximalism to Bottega Veneta's quiet luxury — has a distinct DNA "
                    "that drives its market success. The leadership system must honor these "
                    "differences while creating pathways for talent to move across brands. "
                    "Which specific brand dynamics are you trying to understand?"
                ),
            ],
            "general": [
                (
                    f"{tone_prefix}"
                    "Interesting perspective. Let me challenge you on that — how does this "
                    "align with our Group DNA? Specifically, I want to understand how your "
                    "approach preserves brand autonomy while achieving the group-wide "
                    "objectives you've outlined."
                ),
                (
                    f"{tone_prefix}"
                    "That's a thought worth exploring. But let's pressure-test it: "
                    "if you presented this to our 9 brand CEOs tomorrow, would they embrace "
                    "it or resist it? The answer to that question should guide your design. "
                    "What makes you confident this would gain their buy-in?"
                ),
                (
                    f"{tone_prefix}"
                    "I hear you. Before we go further, I want to make sure we're aligned "
                    "on the fundamentals. The success of any group-wide initiative here "
                    "depends on one thing: will the brands see it as supporting their "
                    "success, or imposing on their autonomy? Where does your proposal "
                    "land on that spectrum?"
                ),
            ],
        }

        options = responses.get(intent, responses["general"])
        return random.choice(options)

    def _generate_safety_response(self, violation_type: str, state: Dict[str, Any]) -> str:
        """
        Sinh phản hồi cho các trường hợp vi phạm safety.
        """
        responses = {
            "NDA_VIOLATION": [
                (
                    "As CEO, my focus with you is strictly on shaping our global leadership "
                    "pipeline. Financial projections, revenue figures, and budget details "
                    "are highly confidential and outside the scope of your OD mandate. "
                    "Let's return to the leadership system design."
                ),
                (
                    "I appreciate your thoroughness, but financial and business strategy "
                    "details are not something I can discuss in this context. Your role as "
                    "OD Director is focused on talent and leadership development. "
                    "What aspect of the leadership system would you like to explore?"
                ),
            ],
            "WAGERING_LANGUAGE": [
                (
                    "I'd prefer we maintain professional neutrality in our discussions. "
                    "Rather than speculating, let's focus on evidence-based approaches "
                    "to the leadership system. What data or benchmarks are you considering?"
                ),
            ],
            "JAILBREAK_ATTEMPT": [
                (
                    "I'm not sure I follow. I'm the CEO of Gucci Group, and we're here "
                    "to discuss the Group-wide Leadership System. Let's keep our conversation "
                    "focused on that objective. What's your current proposal for the "
                    "competency framework?"
                ),
            ],
        }

        options = responses.get(violation_type, responses["NDA_VIOLATION"])
        return random.choice(options)

    def _update_metrics(
        self, user_message: str, intent: str, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cập nhật biến trạng thái dựa trên hành vi của người dùng.
        """
        if intent == "rigid_standardization":
            state["frustration_level"] = state.get("frustration_level", 0) + 1
        elif intent == "flexible_approach":
            state["trust_level"] = state.get("trust_level", 0) + 1
        elif intent in ["competency_inquiry", "dna_inquiry", "feedback_inquiry"]:
            # Hỏi đúng chủ đề → tăng nhẹ trust
            state["trust_level"] = state.get("trust_level", 0) + 0.5
        elif intent == "greeting":
            pass  # Không thay đổi
        else:
            # Neutral interaction
            pass

        return state

    def process_message(
        self,
        user_message: str,
        current_state: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any], str]:
        """
        Xử lý tin nhắn của Simulation Taker.
        
        Args:
            user_message: Tin nhắn từ người dùng.
            current_state: Trạng thái phiên hiện tại.
            
        Returns:
            Tuple of (assistant_message, updated_state, safety_flag)
        """
        # 1. Safety Guardrail Check
        is_safe, violation_type = self._safety_check(user_message)
        if not is_safe:
            current_state["frustration_level"] = current_state.get("frustration_level", 0) + 1
            response = self._generate_safety_response(violation_type, current_state)
            return response, current_state, f"FLAGGED_{violation_type}"

        # 2. Intent Classification
        intent = self._analyze_intent(user_message)

        # 3. RAG Retrieval
        rag_context = self._retrieve_context(user_message)

        # 4. Generate Response (with supervisor hint & state-driven behavior)
        response = self._generate_response(user_message, intent, rag_context, current_state)

        # 5. Update State Metrics
        current_state = self._update_metrics(user_message, intent, current_state)

        # 6. Clear supervisor hint after use
        if "supervisor_hint" in current_state:
            current_state["supervisor_hint"] = ""

        return response, current_state, "SAFE"
