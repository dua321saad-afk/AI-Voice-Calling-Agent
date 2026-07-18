"""
Intelligent AI Agent: LLM-driven on EVERY turn.

Key improvements:
1. Domain re-classification on EVERY turn - seamless mid-conversation switching
2. LLM-first answering - FAQ is reference only, not a keyword trap
3. Smart state management - prevents loops, handles interruptions gracefully
4. Context-aware - full conversation history fed to LLM for coherent responses
"""

from data.knowledge_base import get_domain, DOMAINS
from services import groq_service


GOODBYE_PHRASES = [
    "goodbye", "bye", "bye bye", "thank you bye", "thanks bye",
    "that's all", "that is all", "nothing else", "no more questions",
    "hang up", "end call", "talk later", "see you", "take care",
]


def is_goodbye(text: str) -> bool:
    """Check if user wants to end the conversation."""
    lower = text.lower().strip()
    # Must be a clear goodbye, not just containing the word
    return any(phrase == lower or lower.startswith(phrase + " ") or lower.endswith(" " + phrase) for phrase in GOODBYE_PHRASES)


def _answer_in_domain(speech_text: str, domain_key: str, conversation_history: list[dict], is_switch: bool = False) -> dict:
    """
    Handles a turn once the domain is known. 
    If is_switch is True, adds a transition greeting before the actual answer.
    """
    domain = get_domain(domain_key)

    if is_goodbye(speech_text):
        return {
            "text": (
                f"Thank you for calling {domain['company_name']}! "
                f"We appreciate your time. Have a wonderful day. Goodbye!"
            ),
            "source": "goodbye",
            "confidence": 100,
            "is_goodbye": True,
            "domain_key": domain_key,
            "switched": False,
        }

    # ALWAYS use LLM for intelligent responses
    # FAQ data is embedded in the LLM prompt as reference
    llm_text, llm_source = groq_service.generate_response(
        speech_text, domain, conversation_history
    )

    # If this is a domain switch, prepend a smooth transition
    if is_switch and conversation_history:
        old_domain_key = None
        for msg in reversed(conversation_history):
            if msg.get("domain_key") and msg["domain_key"] != domain_key:
                old_domain_key = msg["domain_key"]
                break

        if old_domain_key:
            old_domain = get_domain(old_domain_key)
            switch_greeting = groq_service.generate_domain_switch_greeting(old_domain, domain)
            llm_text = switch_greeting + " " + llm_text

    confidence = 90.0 if llm_source == "llm" else 60.0

    return {
        "text": llm_text,
        "source": llm_source,
        "confidence": confidence,
        "is_goodbye": False,
        "domain_key": domain_key,
        "switched": is_switch,
    }


def process_turn(
    speech_text: str,
    current_domain_key: str | None,
    conversation_history: list[dict] | None = None,
) -> dict:
    """
    Main entry point for the voice agent, one turn at a time.

    INTELLIGENT BEHAVIOR:
    1. Re-classifies domain on EVERY turn using LLM
    2. Seamlessly switches domains mid-conversation if user changes topic
    3. Uses LLM for ALL responses - FAQ is grounding, not replacement
    4. Maintains full conversation context for coherent responses

    Returns dict with: text, source, confidence, is_goodbye, domain_key, switched
    """
    conversation_history = conversation_history or []

    if not speech_text or not speech_text.strip():
        return {
            "text": "I'm sorry, I didn't catch that. Could you please repeat your question?",
            "source": "retry",
            "confidence": 0,
            "is_goodbye": False,
            "domain_key": current_domain_key,
            "switched": False,
        }

    speech_text = speech_text.strip()

    # Check for goodbye first (works regardless of domain)
    if is_goodbye(speech_text):
        if current_domain_key:
            domain = get_domain(current_domain_key)
            return {
                "text": f"Thank you for calling {domain['company_name']}! Have a wonderful day. Goodbye!",
                "source": "goodbye",
                "confidence": 100,
                "is_goodbye": True,
                "domain_key": current_domain_key,
                "switched": False,
            }
        return {
            "text": "No problem, have a great day! Goodbye.",
            "source": "goodbye",
            "confidence": 100,
            "is_goodbye": True,
            "domain_key": None,
            "switched": False,
        }

    # === INTELLIGENT DOMAIN CLASSIFICATION ON EVERY TURN ===
    classification = groq_service.classify_domain(speech_text, DOMAINS, current_domain_key)
    detected_domain = classification["domain_key"]
    is_switched = classification.get("switched", False)

    # If no domain detected and we have a current domain, stay in current domain
    # (handles follow-ups like "ok", "and then?", "what about pricing?")
    if detected_domain is None and current_domain_key:
        # Check if it's a generic follow-up
        word_count = len(speech_text.split())
        is_generic = word_count <= 3 and speech_text.lower() in [
            "ok", "okay", "yes", "no", "sure", "great", "thanks", "thank you",
            "and", "then", "what else", "go on", "continue",
        ]

        if is_generic or word_count <= 3:
            # Stay in current domain, let LLM handle it with context
            return _answer_in_domain(speech_text, current_domain_key, conversation_history, is_switch=False)
        else:
            # User asked something specific but out of scope
            text = groq_service.generate_out_of_scope_response(speech_text, DOMAINS)
            return {
                "text": text,
                "source": "clarify",
                "confidence": 50,
                "is_goodbye": False,
                "domain_key": current_domain_key,
                "switched": False,
            }

    # No domain and no current domain - need clarification
    if detected_domain is None:
        word_count = len(speech_text.split())
        if word_count <= 3:
            text = groq_service.generate_clarifying_response(DOMAINS)
        else:
            text = groq_service.generate_out_of_scope_response(speech_text, DOMAINS)
        return {
            "text": text,
            "source": "clarify",
            "confidence": 50,
            "is_goodbye": False,
            "domain_key": None,
            "switched": False,
        }

    # === DOMAIN DETECTED - ANSWER INTELLIGENTLY ===
    # If switched domains, handle transition smoothly
    return _answer_in_domain(speech_text, detected_domain, conversation_history, is_switch=is_switched)