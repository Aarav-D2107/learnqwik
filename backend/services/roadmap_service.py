"""
Roadmap engine — the heart of LearnQwik.

Two states:

  STATE 1 (default)      A brand-new user gets the standard curriculum order
                         immediately. No AI, no database history, no waiting.

  STATE 2 (personalized) After an assessment, mastery + the recommendation
                         engine decide the priorities, and the AI orders and
                         explains them. The AI never invents IDs and never
                         decides a number — if its output fails validation we
                         fall back to `build_fallback_roadmap`, which produces
                         a perfectly usable plan on its own.

Pure stdlib. The AI call itself lives in services/ai_service.py.
"""
from config import WEAK_TOPIC_THRESHOLD
from services.mastery_service import band_for
from services.recommendation_service import recommend_for_topic

GENERATED_BY_DEFAULT = "default"
GENERATED_BY_AI = "ai"
GENERATED_BY_FALLBACK = "fallback"


# --------------------------------------------------------------- STATE 1
def build_default_roadmap(subject, topics):
    """
    The 'normal path'. Curriculum order, straight out of the database.
    Deterministic and instantly available to a user with zero history.
    """
    steps = []
    for i, topic in enumerate(sorted(topics, key=lambda t: t.get("position", 0)), start=1):
        steps.append({
            "order": i,
            "topic_id": topic["id"],
            "title": topic["name"],
            "reason": "Standard curriculum order for %s." % subject["name"],
            "estimated_minutes": int(topic.get("estimated_minutes") or 30),
            "resource_ids": [],
            "kind": "learn",
        })
    return {
        "title": "%s Learning Roadmap" % subject["name"],
        "state": "default",
        "subject_id": subject["id"],
        "reason": "This is the standard learning order for %s. Your roadmap will "
                  "adapt once you complete your first assessment." % subject["name"],
        "priority_topics": [],
        "steps": steps,
        "generated_by": GENERATED_BY_DEFAULT,
    }


# --------------------------------------------------------------- Priorities
def build_priority_topics(topics, mastery_by_topic):
    """
    Deterministic priority list. Order:
      1. Weak topics (weakest first)
      2. Struggling topics
      3. Untouched topics in curriculum order
      4. Everything else, mastered last
    Prerequisites are respected: a topic never outranks a prerequisite that is
    itself below the weak threshold.
    """
    ordered = sorted(topics, key=lambda t: t.get("position", 0))
    enriched = []
    for t in ordered:
        row = mastery_by_topic.get(t["id"])
        pct = float(row["mastery_pct"]) if row and row.get("mastery_pct") is not None else None
        enriched.append({
            "topic": t,
            "mastery": pct,
            "assessed": pct is not None,
            "position": t.get("position", 0),
        })

    def sort_key(e):
        if e["mastery"] is None:
            # unassessed: after weak topics, in curriculum order
            return (1, e["position"], 0)
        if e["mastery"] < WEAK_TOPIC_THRESHOLD:
            return (0, e["mastery"], e["position"])
        return (2, e["mastery"], e["position"])

    ranked = sorted(enriched, key=sort_key)

    # Prerequisite guard: pull any unmet prerequisite ahead of its dependent.
    by_id = {e["topic"]["id"]: e for e in ranked}
    final = []
    placed = set()

    def place(entry, depth=0):
        tid = entry["topic"]["id"]
        if tid in placed or depth > 10:
            return
        for prereq_id in entry["topic"].get("prerequisite_topic_ids") or []:
            prereq = by_id.get(prereq_id)
            if prereq and prereq["mastery"] is not None and prereq["mastery"] < WEAK_TOPIC_THRESHOLD:
                place(prereq, depth + 1)
        placed.add(tid)
        final.append(entry)

    for entry in ranked:
        place(entry)

    out = []
    for i, e in enumerate(final, start=1):
        mastery = e["mastery"]
        if mastery is None:
            reason = "Not assessed yet — take a quiz to measure where you stand."
        elif mastery < WEAK_TOPIC_THRESHOLD:
            reason = "Mastery is %d%% (%s), which is your priority gap here." % (
                round(mastery), band_for(mastery))
        else:
            reason = "Mastery is %d%% (%s) — solid enough to move past for now." % (
                round(mastery), band_for(mastery))
        out.append({
            "topic_id": e["topic"]["id"],
            "topic_name": e["topic"]["name"],
            "priority": i,
            "mastery": round(mastery, 1) if mastery is not None else None,
            "band": band_for(mastery) if mastery is not None else None,
            "reason": reason,
        })
    return out


# --------------------------------------------------------------- STATE 2 fallback
def build_fallback_roadmap(subject, topics, mastery_by_topic, resources, trigger_topic_id=None):
    """
    A fully usable personalized roadmap built without any AI at all.

    Used when AI credentials are missing, the provider errors, or the model
    returns structurally invalid output. The user still gets a real,
    mastery-driven plan — the app never degrades to the default roadmap
    just because the AI was unavailable.
    """
    priorities = build_priority_topics(topics, mastery_by_topic)
    topic_by_id = {t["id"]: t for t in topics}
    steps = []
    order = 1

    focus = [p for p in priorities if p["mastery"] is not None and p["mastery"] < WEAK_TOPIC_THRESHOLD]
    if not focus:
        focus = priorities[:2]

    for p in focus[:3]:
        topic = topic_by_id.get(p["topic_id"])
        if not topic:
            continue
        recs = recommend_for_topic(resources, topic["id"], p["mastery"] or 0, limit=2)
        relevant = [r for r in recs if r["components"]["topic_relevance"] >= 1.0]

        steps.append({
            "order": order,
            "topic_id": topic["id"],
            "title": "Rebuild the fundamentals of %s" % topic["name"],
            "reason": p["reason"],
            "estimated_minutes": 30,
            "resource_ids": [],
            "kind": "learn",
        })
        order += 1

        if relevant:
            steps.append({
                "order": order,
                "topic_id": topic["id"],
                "title": "Study: %s" % relevant[0]["title"],
                "reason": relevant[0]["reason"],
                "estimated_minutes": int(relevant[0].get("duration_minutes") or 15),
                "resource_ids": [relevant[0]["resource_id"]],
                "kind": "resource",
            })
            order += 1

        steps.append({
            "order": order,
            "topic_id": topic["id"],
            "title": "Practice: %s drills" % topic["name"],
            "reason": "Retrieval practice is what moves a topic from Struggling to Developing.",
            "estimated_minutes": 20,
            "resource_ids": [r["resource_id"] for r in relevant[1:2]],
            "kind": "practice",
        })
        order += 1

        steps.append({
            "order": order,
            "topic_id": topic["id"],
            "title": "Reassess %s" % topic["name"],
            "reason": "A short targeted reassessment confirms the gap actually closed.",
            "estimated_minutes": 8,
            "resource_ids": [],
            "kind": "reassess",
        })
        order += 1

    # Resume normal progression for the rest of the curriculum.
    for p in priorities:
        if any(s["topic_id"] == p["topic_id"] for s in steps):
            continue
        topic = topic_by_id.get(p["topic_id"])
        if not topic:
            continue
        steps.append({
            "order": order,
            "topic_id": topic["id"],
            "title": "Continue with %s" % topic["name"],
            "reason": p["reason"],
            "estimated_minutes": int(topic.get("estimated_minutes") or 30),
            "resource_ids": [],
            "kind": "learn",
        })
        order += 1

    weakest = focus[0] if focus else None
    if weakest and weakest.get("mastery") is not None:
        reason = ("%s is currently your biggest learning gap at %d%%, so your plan now "
                  "starts there instead of following the standard order."
                  % (weakest["topic_name"], round(weakest["mastery"])))
    else:
        reason = "Your plan is ordered by your measured mastery across %s." % subject["name"]

    return {
        "title": "Personalized %s Roadmap" % subject["name"],
        "state": "personalized",
        "subject_id": subject["id"],
        "reason": reason,
        "priority_topics": priorities,
        "steps": steps,
        "generated_by": GENERATED_BY_FALLBACK,
        "trigger_topic_id": trigger_topic_id,
    }


# --------------------------------------------------------------- AI validation
class RoadmapValidationError(ValueError):
    pass


def validate_ai_roadmap(payload, subject, topics, resources, priorities):
    """
    Hard gate on anything the model produced.

    Rejects: wrong shape, hallucinated topic IDs, hallucinated resource IDs,
    empty step lists, absurd time estimates. Numbers that belong to the backend
    (mastery, priority) are overwritten with the authoritative values rather
    than trusted — the model is only allowed to order and explain.
    """
    if not isinstance(payload, dict):
        raise RoadmapValidationError("AI roadmap was not a JSON object")

    valid_topic_ids = {t["id"] for t in topics}
    valid_resource_ids = {r["id"] for r in resources}
    priority_by_topic = {p["topic_id"]: p for p in priorities}

    raw_steps = payload.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        raise RoadmapValidationError("AI roadmap contained no steps")
    if len(raw_steps) > 30:
        raise RoadmapValidationError("AI roadmap contained too many steps")

    steps = []
    for i, s in enumerate(raw_steps, start=1):
        if not isinstance(s, dict):
            raise RoadmapValidationError("Step %d was not an object" % i)
        topic_id = s.get("topic_id")
        if topic_id not in valid_topic_ids:
            raise RoadmapValidationError("Step %d referenced unknown topic_id %r" % (i, topic_id))
        title = (s.get("title") or "").strip()
        if not title:
            raise RoadmapValidationError("Step %d had no title" % i)

        resource_ids = s.get("resource_ids") or []
        if not isinstance(resource_ids, list):
            raise RoadmapValidationError("Step %d resource_ids was not a list" % i)
        for rid in resource_ids:
            if rid not in valid_resource_ids:
                raise RoadmapValidationError("Step %d referenced unknown resource_id %r" % (i, rid))

        try:
            minutes = int(s.get("estimated_minutes") or 20)
        except (TypeError, ValueError):
            minutes = 20
        minutes = max(5, min(180, minutes))

        kind = s.get("kind") if s.get("kind") in ("learn", "resource", "practice", "reassess") else "learn"

        steps.append({
            "order": i,
            "topic_id": topic_id,
            "title": title[:160],
            "reason": (s.get("reason") or "").strip()[:400],
            "estimated_minutes": minutes,
            "resource_ids": resource_ids[:4],
            "kind": kind,
        })

    # Priority topics: keep the model's ordering only if the IDs are real, but
    # always overwrite mastery with the backend's number.
    out_priorities = []
    raw_priorities = payload.get("priority_topics")
    if isinstance(raw_priorities, list) and raw_priorities:
        for i, p in enumerate(raw_priorities, start=1):
            if not isinstance(p, dict):
                continue
            tid = p.get("topic_id")
            if tid not in valid_topic_ids:
                raise RoadmapValidationError("priority_topics referenced unknown topic_id %r" % tid)
            authoritative = priority_by_topic.get(tid, {})
            out_priorities.append({
                "topic_id": tid,
                "topic_name": authoritative.get("topic_name"),
                "priority": i,
                "mastery": authoritative.get("mastery"),
                "band": authoritative.get("band"),
                "reason": (p.get("reason") or authoritative.get("reason") or "").strip()[:400],
            })
    if not out_priorities:
        out_priorities = priorities

    return {
        "title": (payload.get("title") or "Personalized %s Roadmap" % subject["name"]).strip()[:120],
        "state": "personalized",
        "subject_id": subject["id"],
        "reason": (payload.get("reason") or "").strip()[:600]
                  or "Reordered around your measured mastery.",
        "priority_topics": out_priorities,
        "steps": steps,
        "generated_by": GENERATED_BY_AI,
    }


# --------------------------------------------------------------- Diffing
def diff_roadmaps(previous, current):
    """
    Powers the 'What changed?' panel. Compares step titles so the UI can show
    added / removed lines after an assessment.
    """
    if not previous:
        return {
            "added": [s["title"] for s in current.get("steps", [])][:8],
            "removed": [],
            "reordered": False,
            "is_first_version": True,
        }
    prev_titles = [s.get("title") for s in previous.get("steps", [])]
    curr_titles = [s.get("title") for s in current.get("steps", [])]
    prev_set, curr_set = set(prev_titles), set(curr_titles)
    added = [t for t in curr_titles if t not in prev_set]
    removed = [t for t in prev_titles if t not in curr_set]
    common_prev = [t for t in prev_titles if t in curr_set]
    common_curr = [t for t in curr_titles if t in prev_set]
    return {
        "added": added[:8],
        "removed": removed[:8],
        "reordered": common_prev != common_curr,
        "is_first_version": False,
    }


def total_estimated_minutes(roadmap):
    return sum(int(s.get("estimated_minutes") or 0) for s in roadmap.get("steps", []))


def next_step(roadmap):
    steps = roadmap.get("steps") or []
    return steps[0] if steps else None
