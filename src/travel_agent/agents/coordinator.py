"""Coordinator Agent — entry point of the travel planning workflow.

Parses user's natural language input into a structured TravelIntent.

Two parsing paths:
  1. LLM (primary)  — uses ChatOpenAI + with_structured_output()
  2. Fallback (no-API) — regex/keyword parser when LLM unavailable

Both paths produce the same TravelIntent schema type.
"""

import re
from datetime import date, timedelta

from langchain_core.prompts import ChatPromptTemplate

from travel_agent.graph.state import GraphState
from travel_agent.schemas.common import Budget, POICategory
from travel_agent.schemas.travel import TravelConstraints, TravelIntent, TravelPreferences
from travel_agent.services.llm_client import get_llm


SYSTEM_PROMPT = """You are a travel intent parser for a travel planning system.

Extract structured travel information from the user's request.
Fill in all fields you can determine from their message.

The user's message may include a "=== 你的旅行记忆 ===" section
containing historical preferences (liked cuisines, interest categories,
budget habits, past destinations). USE this information to enrich
the travel intent — especially for fields the user didn't explicitly
mention in their current request.

Examples of how to use memory:
- If memory shows "🍽️ 美食偏好: 川菜", add restaurant to interests and "川菜" to cuisine_preferences.
- If memory shows "🏛️ 兴趣偏好: 景点、美食", add those interests if not already present.
- If memory shows "💰 预算习惯: 舒适型", set an appropriate budget level.
- If memory shows "👥 出行人数: 双人出行", default companions to 2.

Rules:
1. destination: The city or region they want to visit.
2. duration_days: How many days (infer from phrases like "3天" or "三日").
3. start_date: If they mention a specific date, extract it as YYYY-MM-DD.
4. companions: Number of travelers (default 1, but prefer memory value).
5. preferences.interests: Extract from mentioned interests AND memory.
6. preferences.cuisine_preferences: Extract cuisine mentions AND memory.
7. preferences.pace: "relaxed", "moderate", or "intensive".
8. constraints.must_visit: Any specific places they mention.
9. budget: Parse any budget mentions AND use memory budget level as default.

Output ONLY as a valid TravelIntent. Do not include explanations.
For any field you cannot determine, leave its default value.

IMPORTANT: Memory is not the user's current request — merge it, don't override it."""

# ── Keyword → POICategory mapping ──
_KEYWORD_INTERESTS: dict[str, POICategory] = {
    "景点": POICategory.ATTRACTION,
    "景区": POICategory.ATTRACTION,
    "风景": POICategory.ATTRACTION,
    "名胜": POICategory.ATTRACTION,
    "美食": POICategory.RESTAURANT,
    "餐厅": POICategory.RESTAURANT,
    "小吃": POICategory.RESTAURANT,
    "餐饮": POICategory.RESTAURANT,
    "吃饭": POICategory.RESTAURANT,
    "购物": POICategory.SHOPPING,
    "逛街": POICategory.SHOPPING,
    "买": POICategory.SHOPPING,
    "文化": POICategory.MUSEUM,
    "博物馆": POICategory.MUSEUM,
    "历史": POICategory.MUSEUM,
    "户外": POICategory.PARK,
    "自然": POICategory.PARK,
    "公园": POICategory.PARK,
    "爬山": POICategory.PARK,
    "夜生活": POICategory.NIGHTLIFE,
    "酒吧": POICategory.NIGHTLIFE,
    "娱乐": POICategory.ENTERTAINMENT,
    "游乐": POICategory.ENTERTAINMENT,
    "乐园": POICategory.ENTERTAINMENT,
    "酒店": POICategory.HOTEL,
    "住宿": POICategory.HOTEL,
}


def coordinator_node(state: GraphState) -> dict:
    """Parse user input into a structured TravelIntent.

    Attempts LLM parsing first. Falls back to regex-based parsing
    when the API key is missing or the LLM call fails.

    Args:
        state: Current GraphState with user_input field.

    Returns:
        Updated state with travel_intent and missing_info.
    """
    user_input = state.get("user_input", "")

    # ── Path 1: LLM parsing ──
    try:
        llm = get_llm()
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{input}"),
        ])
        chain = prompt | llm.with_structured_output(TravelIntent)
        intent: TravelIntent = chain.invoke({"input": user_input})
        intent.raw_input = user_input
        missing = _check_missing(intent)
        return {
            "travel_intent": intent,
            "missing_info": missing,
            "current_phase": "research" if not missing else "clarify",
        }
    except Exception:
        # Fall through to fallback parser
        pass

    # ── Path 2: Fallback parser (no API key) ──
    intent = _fallback_parse(user_input)

    missing = _check_missing(intent)
    return {
        "travel_intent": intent,
        "missing_info": missing,
        "current_phase": "research" if not missing else "clarify",
    }


# ── Fallback parser ──


def _fallback_parse(user_input: str) -> TravelIntent:
    """Rule-based fallback parser for when LLM is unavailable.

    Extracts travel information from Chinese natural language using
    regex patterns and keyword matching. Also merges preferences
    from any embedded memory context (=== 你的旅行记忆 ===).
    """
    dest = _extract_destination(user_input)
    days = _extract_duration(user_input)
    start = _extract_start_date(user_input)
    companions = _extract_companions(user_input)
    bmin, bmax = _extract_budget(user_input)
    interests = _extract_interests(user_input)
    pace = _extract_pace(user_input)
    must_visit = _extract_must_visit(user_input)
    companion_info = _extract_companion_info(user_input)

    # ── Merge memory-based preferences ──
    memory_prefs = _parse_memory_preferences(user_input)

    # Merge interests from memory (don't duplicate)
    existing_cats = set(interests)
    for cat in memory_prefs.get("interests", []):
        if cat not in existing_cats:
            interests.append(cat)
            existing_cats.add(cat)

    # Merge cuisine preferences from memory
    cuisine_prefs = memory_prefs.get("cuisines", [])

    # Use memory-based companions as default only if regex found no explicit match
    mem_companions = memory_prefs.get("companions", 0)
    if companions == 1 and mem_companions > 1:
        companions = mem_companions

    # Use memory pace as default only if regex didn't detect a pace
    mem_pace = memory_prefs.get("pace", "")
    if pace == "moderate" and mem_pace:
        pace = mem_pace

    intent = TravelIntent(
        destination=dest,
        duration_days=days if days > 0 else None,
        start_date=start,
        companions=companions,
        budget=Budget(min_amount=bmin, max_amount=bmax, currency="CNY") if bmin > 0 or bmax > 0 else None,
        preferences=TravelPreferences(
            interests=interests,
            cuisine_preferences=cuisine_prefs,
            pace=pace,
            accommodation_type="hotel",
        ),
        constraints=TravelConstraints(
            must_visit=must_visit,
        ),
        companion_info=companion_info,
        purpose="leisure",
        raw_input=user_input,
    )
    return intent


def _extract_destination(text: str) -> str:
    """Extract destination city name."""
    patterns = [
        r"(?:去|到|在|游玩|游览|访问|出发去|前往)(\w{2,4}(?:市|区|岛)?)(?:\s|，|的|旅|玩|游|$)",
        r"目的地[：:]\s*(\w+)",
        r"(\w+)旅游",
        r"(\w+)旅行",
        r"(\w+)游",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            city = m.group(1)
            # Filter out common false matches
            if city not in ("喜欢", "预算", "旅游", "旅行", "出发", "一共", "总共"):
                return city
    return ""


def _extract_duration(text: str) -> int:
    """Extract number of days."""
    patterns = [
        r"(\d+)\s*天(?:[^前]|$)",
        r"(\d+)\s*日(?:[^期]|$)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return int(m.group(1))
    return 0


def _extract_start_date(text: str) -> date | None:
    """Extract start date (ISO format or Chinese date)."""
    # ISO format: 2026-07-20
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass

    # Chinese date: 2026年7月20日
    m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass

    # Relative: 下周一, 下个月 → not supported in MVP
    return None


def _extract_companions(text: str) -> int:
    """Extract number of travelers."""
    patterns = [
        r"(\d+)\s*(?:个|位)?\s*人",
        r"一共\s*(\d+)\s*(?:个|位)?\s*人",
        r"(\d+)\s*(?:个|位)?\s*同行",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return max(1, int(m.group(1)))
    return 1


def _extract_budget(text: str) -> tuple[float, float]:
    """Extract budget range."""
    # Range: 2000-3000元 or 2000~3000元
    m = re.search(r"预算[：:\s]*(\d+)\s*[~\-到至]\s*(\d+)\s*(?:元|块)?", text)
    if m:
        return float(m.group(1)), float(m.group(2))

    # Single: 预算3000元
    m = re.search(r"预算[：:\s]*(\d+)\s*(?:元|块)?", text)
    if m:
        return 0, float(m.group(1))

    # 花N元
    m = re.search(r"花\s*(\d+)\s*(?:元|块)?", text)
    if m:
        return 0, float(m.group(1))

    return 0, 0


def _extract_interests(text: str) -> list[POICategory]:
    """Extract interest categories from keywords."""
    found: set[POICategory] = set()
    for keyword, category in _KEYWORD_INTERESTS.items():
        if keyword in text:
            found.add(category)

    # Check "喜欢" section
    like_match = re.search(r"喜欢[：:、，\s]*([^。，\n]+)", text)
    if like_match:
        like_text = like_match.group(1)
        for keyword, category in _KEYWORD_INTERESTS.items():
            if keyword in like_text:
                found.add(category)

    return list(found)


def _extract_pace(text: str) -> str:
    """Extract travel pace."""
    if any(k in text for k in ("轻松", "悠闲", "慢", "放松", "不累", "休闲")):
        return "relaxed"
    if any(k in text for k in ("紧凑", "抓紧", "多去", "充实", "高效")):
        return "intensive"
    return "moderate"


def _extract_must_visit(text: str) -> list[str]:
    """Extract must-visit places."""
    must: list[str] = []

    # 想去/必去/一定要去 xx
    patterns = [
        r"(?:想去|必去|一定要去|必须去|推荐去)\s*(\w+)",
        r"(?:想去|必去|一定要去|必须去)\s*(?:的\s*)?(\w+)",
    ]
    for pat in patterns:
        for m in re.finditer(pat, text):
            place = m.group(1)
            if place and len(place) >= 2:
                must.append(place)

    return must


def _extract_companion_info(text: str) -> str:
    """Extract companion relationship info."""
    patterns = [
        (r"带\s*(父母|老人|爸妈|孩子|小孩|娃|女朋友|男朋友|对象|家人|全家)", r"\1"),
        (r"(情侣|夫妻|蜜月|闺蜜|朋友|同事|团建|亲子)", r"\1"),
    ]
    for pat, _ in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    return ""


def _check_missing(intent: TravelIntent) -> list[str]:
    """Check which essential fields are missing."""
    missing = []
    if not intent.destination:
        missing.append("destination")
    if intent.start_date is None and (not intent.duration_days or intent.duration_days == 0):
        missing.append("date_or_duration")
    return missing


# ── Memory-aware preference merging ──

_LABEL_TO_CATEGORY: dict[str, POICategory] = {
    "景点": POICategory.ATTRACTION,
    "美食": POICategory.RESTAURANT,
    "购物": POICategory.SHOPPING,
    "文化场馆": POICategory.MUSEUM,
    "历史": POICategory.MUSEUM,
    "自然风光": POICategory.PARK,
    "户外": POICategory.PARK,
    "娱乐": POICategory.ENTERTAINMENT,
    "夜生活": POICategory.NIGHTLIFE,
    "住宿品质": POICategory.HOTEL,
}

_MEMORY_COMPANIONS: dict[str, int] = {
    "独自出行": 1,
    "双人出行": 2,
    "小团体出行": 3,
    "多人出行": 5,
}

_MEMORY_PACE: dict[str, str] = {
    "轻松": "relaxed",
    "适中": "moderate",
    "紧凑": "intensive",
}


def _parse_memory_preferences(text: str) -> dict:
    """Extract structured preferences from the memory context section.

    Parses lines like:
      🍽️ 美食偏好: 川菜、火锅
      🏛️ 兴趣偏好: 景点、美食、文化场馆
      💰 预算习惯: 舒适型
      👥 出行人数: 双人出行
      👣 出行节奏: 轻松

    Returns:
        dict with keys:
          - interests: list[POICategory]
          - cuisines: list[str]
          - companions: int (0 if not found)
          - pace: str ("" if not found)
    """
    result: dict = {"interests": [], "cuisines": [], "companions": 0, "pace": ""}

    if "=== 你的旅行记忆 ===" not in text:
        return result

    memory_section = text.split("=== 你的旅行记忆 ===", 1)[1]
    if "===" in memory_section:
        memory_section = memory_section.split("===", 1)[0]

    for line in memory_section.split("\n"):
        line = line.strip()
        if ":" not in line:
            continue

        label, values_str = line.split(":", 1)
        values = [v.strip() for v in values_str.replace("、", ",").replace("，", ",").split(",") if v.strip()]

        # ── Interest preferences ──
        if "兴趣偏好" in label:
            for v in values:
                cat = _LABEL_TO_CATEGORY.get(v)
                if cat and cat not in result["interests"]:
                    result["interests"].append(cat)

        # ── Cuisine preferences ──
        if "美食偏好" in label:
            for v in values:
                if v not in result["cuisines"]:
                    result["cuisines"].append(v)

        # ── Companion habits ──
        if "出行人数" in label:
            for v in values:
                c = _MEMORY_COMPANIONS.get(v, 0)
                if c:
                    result["companions"] = c
                    break

        # ── Pace ──
        if "出行节奏" in label:
            for v in values:
                p = _MEMORY_PACE.get(v)
                if p:
                    result["pace"] = p
                    break

    return result
