"""
Groq LLM integration - free tier with Llama models.

Two jobs:
1. Domain detection - given any message, figure out which of the three business domains 
   (if any) the user wants. This is called on EVERY turn, not just the first one.
2. In-domain conversation - once a domain is set, answer naturally in character.
   If the user switches topics, the LLM detects this and we switch domains seamlessly.
"""

import json
from groq import Groq
from config import Config


def _get_client() -> Groq | None:
    if not Config.GROQ_API_KEY:
        return None
    return Groq(api_key=Config.GROQ_API_KEY)


# ---------------------------------------------------------------------------
# Domain detection - NOW CALLED ON EVERY TURN
# ---------------------------------------------------------------------------

def classify_domain(user_message: str, domains: dict, current_domain: str | None = None) -> dict:
    """
    Asks the LLM to decide which business domain (if any) the caller's
    message belongs to. Called on EVERY turn, not just the first one.

    Returns a dict:
      {"domain_key": "<key>"|None, "reasoning": str, "switched": bool}
    domain_key is None if the request is out of scope or too vague.
    switched is True if the domain changed from current_domain.
    """
    client = _get_client()

    domain_descriptions = "\n".join(
        f'- "{key}": {d["label"]} ({d["company_name"]}) - services include: '
        f'{", ".join(d.get("services", [])[:6])}'
        for key, d in domains.items()
    )

    if not client:
        return _keyword_fallback_classify(user_message, domains, current_domain)

    current_context = f"""The caller is currently in a conversation. 
Their current domain is: {current_domain or "not yet determined"}.

IMPORTANT: If the user asks about something clearly belonging to a DIFFERENT domain 
than the current one, you MUST return that new domain_key. For example, if they were 
talking about IT services but now ask "what's the petrol price?", return "petrol_pump".

If they are continuing within the same domain, return the same domain_key.
If the message is just a greeting, acknowledgment, or follow-up question within the 
current domain, keep the current domain.

If there is no current domain and the message is vague (just "hello", "hi", "ok"), 
return null for domain_key and ask what they need help with."""

    system_prompt = f"""You are an intelligent routing classifier for a multi-business voice assistant.
The assistant can help with exactly these business domains:
{domain_descriptions}

{current_context}

Given what the caller just said, decide which ONE domain key it belongs to.
Use your own judgement - for example:
- "logo design", "website", "app", "cybersecurity" → it_services
- "food", "menu", "delivery", "reservation", "biryani" → restaurant  
- "petrol", "diesel", "fuel", "car wash", "oil change" → petrol_pump

Respond with ONLY a JSON object, no other text, in this exact format:
{{"domain_key": "<one of: {', '.join(domains.keys())}, or null>", "reasoning": "<one short sentence>", "switched": <true or false>}}

Use null for domain_key if the request doesn't fit any domain, or if it's just a 
generic greeting with no topic. Set switched to true ONLY if this is a different 
domain than the current one."""

    try:
        completion = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
            max_tokens=120,
        )
        raw = completion.choices[0].message.content.strip()
        raw = raw.strip("`").replace("json\n", "").strip()
        parsed = json.loads(raw)
        domain_key = parsed.get("domain_key")
        if domain_key not in domains:
            domain_key = None

        # Determine if switched
        is_switched = False
        if current_domain and domain_key and domain_key != current_domain:
            is_switched = True
        elif parsed.get("switched") is True:
            is_switched = True

        return {
            "domain_key": domain_key, 
            "reasoning": parsed.get("reasoning", ""),
            "switched": is_switched
        }
    except Exception as exc:
        print(f"[groq] classify_domain error: {exc}")
        return _keyword_fallback_classify(user_message, domains, current_domain)


def _keyword_fallback_classify(user_message: str, domains: dict, current_domain: str | None = None) -> dict:
    """Only used if Groq is unreachable/unconfigured."""
    lower = user_message.lower()

    # Check for strong domain indicators first
    domain_keywords = {
        "it_services": ["website", "web", "app", "mobile", "cyber", "security", "logo", "design", "graphic", "cloud", "aws", "azure", "seo", "marketing", "software", "development", "it support", "helpdesk"],
        "restaurant": ["food", "menu", "biryani", "karahi", "bbq", "delivery", "reservation", "table", "catering", "buffet", "lunch", "dinner", "eat", "dine"],
        "petrol_pump": ["petrol", "diesel", "fuel", "gas", "car wash", "oil change", "tire", "air pressure", "pump", "station"]
    }

    scores = {key: 0 for key in domains}
    for key, keywords in domain_keywords.items():
        for kw in keywords:
            if kw in lower:
                scores[key] += 1

    best_key = max(scores, key=scores.get) if scores else None
    if best_key and scores[best_key] > 0:
        is_switched = current_domain is not None and best_key != current_domain
        return {"domain_key": best_key, "reasoning": "keyword fallback", "switched": is_switched}

    # Keep current domain if no strong indicators
    if current_domain:
        return {"domain_key": current_domain, "reasoning": "keeping current domain", "switched": False}

    return {"domain_key": None, "reasoning": "no match", "switched": False}


def generate_clarifying_response(domains: dict) -> str:
    """LLM-generated prompt asking the caller what they need."""
    client = _get_client()
    labels = ", ".join(d["label"] for d in domains.values())

    if not client:
        return (
            f"I can help you with {labels}. What would you like to know?"
        )

    system_prompt = (
        "You are a warm, natural-sounding voice assistant that can help with "
        f"these services: {labels}. The caller hasn't specified what they want yet. "
        "Ask a short, friendly question (1-2 sentences, spoken style, no markdown) to find out."
    )
    try:
        completion = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.7,
            max_tokens=80,
        )
        return _clean_for_speech(completion.choices[0].message.content.strip())
    except Exception as exc:
        print(f"[groq] clarifying response error: {exc}")
        return f"I can help you with {labels}. What would you like to know?"


def generate_out_of_scope_response(user_message: str, domains: dict) -> str:
    """
    LLM-generated response for when the caller asks about something 
    none of the three domains cover.
    """
    client = _get_client()
    labels = ", ".join(d["label"] for d in domains.values())

    if not client:
        return (
            f"I'm sorry, we don't provide that kind of service. "
            f"I can help you with {labels} though. Would any of those interest you?"
        )

    system_prompt = (
        "You are a warm, natural-sounding voice assistant. You can only help with "
        f"these services: {labels}. The caller just asked about something outside "
        "all of these. Politely explain that you don't provide that particular service, "
        "then invite them to ask about one of the ones you do offer. "
        "Keep it to 1-2 short spoken sentences, no markdown, sound human."
    )
    try:
        completion = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=100,
        )
        return _clean_for_speech(completion.choices[0].message.content.strip())
    except Exception as exc:
        print(f"[groq] out-of-scope response error: {exc}")
        return (
            f"I'm sorry, we don't provide that kind of service. "
            f"I can help you with {labels} though. Would any of those interest you?"
        )


def generate_domain_switch_greeting(old_domain: dict, new_domain: dict) -> str:
    """Generate a smooth transition when switching domains mid-conversation."""
    client = _get_client()

    if not client:
        return f"Switching to {new_domain['company_name']}. How can I help you with that?"

    system_prompt = f"""You are a warm, professional voice assistant. 
The caller was just talking about {old_domain['company_name']} ({old_domain['label']}) 
but has now switched to asking about {new_domain['company_name']} ({new_domain['label']}).

Generate a brief, natural-sounding transition (1 sentence) that acknowledges the switch 
and welcomes them to the new topic. Keep it short, friendly, and spoken-style. No markdown."""

    try:
        completion = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.7,
            max_tokens=60,
        )
        return _clean_for_speech(completion.choices[0].message.content.strip())
    except Exception as exc:
        print(f"[groq] domain switch greeting error: {exc}")
        return f"Sure, I can help you with {new_domain['company_name']}. What would you like to know?"


# ---------------------------------------------------------------------------
# In-domain conversation - INTELLIGENT LLM-FIRST APPROACH
# ---------------------------------------------------------------------------

def generate_response(
    user_message: str,
    domain: dict,
    conversation_history: list[dict] | None = None,
) -> tuple[str, str]:
    """
    Generate a human-like spoken response using Groq LLM.
    This is the PRIMARY method - we always try LLM first for intelligence.
    Returns (response_text, source) where source is 'llm' or 'fallback'.
    """
    client = _get_client()
    if not client:
        return _fallback_response(domain), "fallback"

    services_text = "\n".join(f"- {s}" for s in domain.get("services", []))

    # Build conversation context
    history_text = ""
    if conversation_history:
        recent = conversation_history[-6:]  # Last 6 messages for context
        for msg in recent:
            role = "Agent" if msg["role"] == "agent" else "Caller"
            history_text += f"{role}: {msg['content']}\n"

    system_prompt = f"""You are a friendly, professional voice agent for {domain['company_name']} ({domain['label']}).
You are having a live phone conversation. Keep answers concise (2-4 sentences max), natural, and spoken aloud.
Never use bullet points, markdown, or special characters.

Services offered:
{services_text}

FAQ knowledge (use these as reference, but answer in your own words):
{_build_faq_summary(domain)}

Rules:
- Answer EVERY question helpfully using the services and FAQ above as grounding.
- If asked about prices, timings, or specifics, give the exact info from the FAQ.
- If asked about something NOT in your services, politely say you don't offer that and suggest what you DO offer.
- Sound human - use contractions, be warm but professional.
- Never say you are an AI unless directly asked.
- Keep responses SHORT - people are listening, not reading.
- If the caller wants to end, say goodbye warmly.
- Prices/timings should be realistic for Pakistan/Lahore context."""

    messages = [{"role": "system", "content": system_prompt}]

    if history_text:
        messages.append({"role": "user", "content": f"Recent conversation context:\n{history_text}\n\nCaller just said: {user_message}"})
    else:
        messages.append({"role": "user", "content": user_message})

    try:
        completion = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=250,
        )
        text = completion.choices[0].message.content.strip()
        text = _clean_for_speech(text)
        return text, "llm"
    except Exception as exc:
        print(f"[groq] API error: {exc}")
        return _fallback_response(domain), "fallback"


def _build_faq_summary(domain: dict) -> str:
    """Build a condensed FAQ reference for the LLM prompt."""
    faqs = domain.get("faqs", [])
    if not faqs:
        return "No specific FAQs available."

    lines = []
    for faq in faqs[:5]:  # Top 5 FAQs
        lines.append(f"Q: {faq['question']} -> A: {faq['answer'][:150]}...")
    return "\n".join(lines)


def _clean_for_speech(text: str) -> str:
    """Remove markdown and formatting unsuitable for TTS."""
    for char in ["*", "#", "`", "- ", "\n", "\""]:
        text = text.replace(char, " ")
    while "  " in text:
        text = text.replace("  ", " ")
    return text.strip()


def _fallback_response(domain: dict) -> str:
    services = domain.get("services", [])
    if services:
        sample = ", ".join(services[:3])
        return (
            f"Thank you for your question. At {domain['company_name']}, "
            f"we offer services including {sample}, and more. "
            f"Could you tell me more specifically what you need help with?"
        )
    return "Thank you for calling. How can I assist you today?"