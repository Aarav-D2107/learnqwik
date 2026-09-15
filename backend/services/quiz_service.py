"""
Quiz lifecycle and the post-assessment pipeline.

Completion runs the full intelligence loop in one place:

    validate attempt -> score -> topic mastery -> progress history
    -> recommendations -> AI roadmap -> save roadmap version -> return everything

The frontend gets the updated roadmap in the same response, which is what makes
the "Your roadmap has been updated" moment instant.
"""
import logging
import random
import uuid
from datetime import datetime, timezone

import config
import db
import errors
from services import (
    ai_service,
    catalog,
    mastery_service,
    reassessment_service,
    recommendation_service,
    roadmap_service,
)

log = logging.getLogger("learnqwik.quiz")


def _now():
    return datetime.now(timezone.utc).isoformat()


async def start(user_id, subject_id, topic_id, mode="quiz", question_count=None):
    subject = await catalog.get_subject(subject_id)
    topic = await catalog.get_topic(topic_id)
    if topic["subject_id"] != subject_id:
        raise errors.bad_request("That topic doesn't belong to that subject.")

    pool = await catalog.questions_for(topic_id)
    if not pool:
        raise errors.not_found("No questions are seeded for this topic yet.",
                               code="NO_QUESTIONS")

    if mode == "reassess":
        count = question_count or config.REASSESS_QUESTION_COUNT
        selected = random.sample(pool, min(count, len(pool)))
    else:
        count = question_count or min(config.MAX_QUESTIONS_PER_QUIZ, len(pool))
        count = max(min(count, len(pool)), min(config.MIN_QUESTIONS_PER_QUIZ, len(pool)))
        selected = random.sample(pool, count)

    # Abandon any stale in-progress attempt so the tutor lock can't get stuck.
    await db.update(
        "quiz_attempts",
        {"user_id": "eq.%s" % user_id, "status": "eq.in_progress"},
        {"status": "abandoned", "completed_at": _now()},
    )

    mastery_row = await get_mastery_row(user_id, topic_id)
    attempt_id = str(uuid.uuid4())
    await db.insert("quiz_attempts", {
        "id": attempt_id,
        "user_id": user_id,
        "subject_id": subject_id,
        "topic_id": topic_id,
        "mode": mode,
        "status": "in_progress",
        "started_at": _now(),
        "question_ids": [q["id"] for q in selected],
        "before_mastery_pct": (mastery_row or {}).get("mastery_pct"),
    })

    return {
        "attempt_id": attempt_id,
        "subject": {"id": subject["id"], "name": subject["name"]},
        "topic": {"id": topic["id"], "name": topic["name"]},
        "mode": mode,
        "questions": [catalog.public_question(q) for q in selected],
        "seconds_per_question": config.SECONDS_PER_QUESTION,
        "total_seconds": len(selected) * config.SECONDS_PER_QUESTION,
        "max_fullscreen_violations": config.MAX_FULLSCREEN_VIOLATIONS,
        "before_mastery_pct": (mastery_row or {}).get("mastery_pct"),
    }


async def get_attempt(attempt_id, user_id):
    attempt = await db.select_one("quiz_attempts", {
        "select": "*", "id": "eq.%s" % attempt_id, "user_id": "eq.%s" % user_id,
    })
    if not attempt:
        raise errors.not_found("That attempt doesn't exist.", code="ATTEMPT_NOT_FOUND")
    return attempt


async def questions_for_attempt(attempt_id, user_id):
    attempt = await get_attempt(attempt_id, user_id)
    rows = await catalog.questions_by_ids(attempt.get("question_ids") or [])
    order = {qid: i for i, qid in enumerate(attempt.get("question_ids") or [])}
    rows.sort(key=lambda r: order.get(r["id"], 999))
    return attempt, [catalog.public_question(r) for r in rows]


async def record_answer(attempt_id, user_id, question_id, selected_index, response_time_ms):
    attempt = await get_attempt(attempt_id, user_id)
    if attempt["status"] != "in_progress":
        raise errors.bad_request("That assessment has already been submitted.",
                                 code="ATTEMPT_CLOSED")
    if question_id not in (attempt.get("question_ids") or []):
        raise errors.bad_request("That question isn't part of this assessment.",
                                 code="QUESTION_NOT_IN_ATTEMPT")

    await db.insert("answers", {
        "attempt_id": attempt_id,
        "user_id": user_id,
        "question_id": question_id,
        "selected_index": selected_index,
        "response_time_ms": response_time_ms,
        "answered_at": _now(),
    }, upsert=True, on_conflict="attempt_id,question_id")
    return {"saved": True}


async def get_mastery_row(user_id, topic_id):
    return await db.select_one("topic_mastery", {
        "select": "*", "user_id": "eq.%s" % user_id, "topic_id": "eq.%s" % topic_id,
    })


async def all_mastery(user_id):
    return await db.select("topic_mastery", {"select": "*", "user_id": "eq.%s" % user_id})


async def complete(user_id, attempt_id, fullscreen_violations=0, auto_submitted=False,
                   time_used_seconds=None):
    """The full post-assessment pipeline."""
    attempt = await get_attempt(attempt_id, user_id)
    if attempt["status"] == "completed":
        raise errors.bad_request("That assessment was already submitted.",
                                 code="ATTEMPT_ALREADY_COMPLETED")

    question_rows = await catalog.questions_by_ids(attempt.get("question_ids") or [])
    order = {qid: i for i, qid in enumerate(attempt.get("question_ids") or [])}
    question_rows.sort(key=lambda r: order.get(r["id"], 999))
    questions = [catalog.with_answer(r) for r in question_rows]
    if not questions:
        raise errors.bad_request("This attempt has no questions.", code="ATTEMPT_EMPTY")

    answer_rows = await db.select("answers", {
        "select": "*", "attempt_id": "eq.%s" % attempt_id, "user_id": "eq.%s" % user_id,
    })
    by_question = {a["question_id"]: a for a in answer_rows}
    answers = [by_question.get(q["id"], {}).get("selected_index") for q in questions]

    # ---- 1. Authoritative scoring (server-side, never the browser's number)
    from services import scoring_service
    result = scoring_service.score_attempt(
        answers, questions,
        time_used_seconds=time_used_seconds,
        violations=fullscreen_violations,
    )

    # ---- 2. Mastery
    previous_row = await get_mastery_row(user_id, attempt["topic_id"])
    mastery = mastery_service.apply_attempt(previous_row, result["weighted_percentage"])
    await db.insert("topic_mastery", {
        "user_id": user_id,
        "topic_id": attempt["topic_id"],
        "subject_id": attempt["subject_id"],
        "mastery_pct": mastery["mastery_pct"],
        "mastery_band": mastery["mastery_band"],
        "attempts_count": mastery["attempts_count"],
        "updated_at": _now(),
    }, upsert=True, on_conflict="user_id,topic_id")

    # ---- 3. Attempt record
    await db.update("quiz_attempts", {"id": "eq.%s" % attempt_id}, {
        "status": "completed",
        "completed_at": _now(),
        "raw_score_pct": result["raw_percentage"],
        "weighted_score_pct": result["weighted_percentage"],
        "correct_count": result["correct_count"],
        "incorrect_count": result["incorrect_count"],
        "unanswered_count": result["unanswered_count"],
        "total_questions": result["total_questions"],
        "time_used_seconds": result["time_used_seconds"],
        "fullscreen_violations": fullscreen_violations,
        "auto_submitted": auto_submitted,
        "difficulty_breakdown": result["difficulty_breakdown"],
        "after_mastery_pct": mastery["mastery_pct"],
    })

    # ---- 4. Progress history
    await db.insert("progress_history", {
        "user_id": user_id,
        "subject_id": attempt["subject_id"],
        "topic_id": attempt["topic_id"],
        "attempt_id": attempt_id,
        "mastery_pct": mastery["mastery_pct"],
        "score_pct": result["raw_percentage"],
        "recorded_at": _now(),
    })

    comparison = reassessment_service.compare(
        attempt.get("before_mastery_pct"), mastery["mastery_pct"]
    )

    # ---- 5. Recommendations (deterministic)
    resources = await catalog.resources_for_subject(attempt["subject_id"])
    recommendations = recommendation_service.recommend_for_topic(
        resources, attempt["topic_id"], mastery["mastery_pct"], limit=3
    )

    # ---- 6+7+8. AI roadmap, validated, versioned
    roadmap_result = await recompute_roadmap(
        user_id, attempt["subject_id"],
        trigger={"attempt_id": attempt_id, "topic_id": attempt["topic_id"],
                 "mode": attempt.get("mode"), "comparison": comparison},
    )

    mastery_rows = await all_mastery(user_id)
    topics = await catalog.topics_for(attempt["subject_id"])
    topic_names = {t["id"]: t["name"] for t in topics}
    weak = [
        {**r, "topic_name": topic_names.get(r["topic_id"], r["topic_id"])}
        for r in mastery_service.weak_topics(
            [m for m in mastery_rows if m.get("subject_id") == attempt["subject_id"]]
        )
    ]

    topic = await catalog.get_topic(attempt["topic_id"])
    subject = await catalog.get_subject(attempt["subject_id"])
    missed = [
        {"question": q["question"], "difficulty": q["difficulty"],
         "correct_answer": q["options"][q["correct_index"]]}
        for i, q in enumerate(questions)
        if answers[i] is not None and answers[i] != q["correct_index"]
    ]
    explanation = await ai_service.explain_result(
        subject["name"], topic["name"], result, mastery, comparison, missed
    )

    return {
        "attempt_id": attempt_id,
        "mode": attempt.get("mode"),
        "subject": {"id": subject["id"], "name": subject["name"]},
        "topic": {"id": topic["id"], "name": topic["name"]},
        "score": result,
        "mastery": {
            "topic_id": attempt["topic_id"],
            "mastery_pct": mastery["mastery_pct"],
            "mastery_band": mastery["mastery_band"],
            "previous_mastery_pct": mastery["previous_mastery_pct"],
            "delta": mastery["delta"],
        },
        "comparison": comparison,
        "weak_topics": weak,
        "recommendations": recommendations,
        "explanation": explanation,
        "roadmap": roadmap_result["roadmap"],
        "roadmap_updated": roadmap_result["updated"],
        "roadmap_changes": roadmap_result["changes"],
        "roadmap_version": roadmap_result["version_number"],
        "generated_by": roadmap_result["generated_by"],
        "review": [
            {
                "question": q["question"],
                "options": q["options"],
                "correct_index": q["correct_index"],
                "selected_index": answers[i],
                "explanation": q.get("explanation"),
                "difficulty": q.get("difficulty"),
            }
            for i, q in enumerate(questions)
        ],
    }


# ------------------------------------------------------------------ Roadmap
async def latest_roadmap_version(user_id, subject_id):
    rows = await db.select("roadmap_versions", {
        "select": "*",
        "user_id": "eq.%s" % user_id,
        "subject_id": "eq.%s" % subject_id,
        "order": "version_number.desc",
        "limit": "1",
    })
    return rows[0] if rows else None


async def get_roadmap(user_id, subject_id):
    """
    STATE 1 when the user has no assessment history in this subject,
    STATE 2 once a version exists.
    """
    subject = await catalog.get_subject(subject_id)
    topics = await catalog.topics_for(subject_id)
    latest = await latest_roadmap_version(user_id, subject_id)

    if latest and latest.get("roadmap_json"):
        roadmap = latest["roadmap_json"]
        return {
            "roadmap": roadmap,
            "state": roadmap.get("state", "personalized"),
            "version_number": latest.get("version_number"),
            "generated_by": latest.get("generated_by"),
            "created_at": latest.get("created_at"),
            "total_estimated_minutes": roadmap_service.total_estimated_minutes(roadmap),
            "next_step": roadmap_service.next_step(roadmap),
        }

    default = roadmap_service.build_default_roadmap(subject, topics)
    return {
        "roadmap": default,
        "state": "default",
        "version_number": 0,
        "generated_by": roadmap_service.GENERATED_BY_DEFAULT,
        "created_at": None,
        "total_estimated_minutes": roadmap_service.total_estimated_minutes(default),
        "next_step": roadmap_service.next_step(default),
    }


async def recompute_roadmap(user_id, subject_id, trigger=None, force=False):
    """
    Regenerates and versions the roadmap. Returns the roadmap plus a diff so the
    UI can show "What changed?".
    """
    subject = await catalog.get_subject(subject_id)
    topics = await catalog.topics_for(subject_id)
    resources = await catalog.resources_for_subject(subject_id)

    mastery_rows = [m for m in await all_mastery(user_id) if m.get("subject_id") == subject_id]
    mastery_by_topic = {m["topic_id"]: m for m in mastery_rows}

    if not mastery_by_topic and not force:
        default = roadmap_service.build_default_roadmap(subject, topics)
        return {"roadmap": default, "updated": False, "changes": None,
                "version_number": 0, "generated_by": roadmap_service.GENERATED_BY_DEFAULT}

    priorities = roadmap_service.build_priority_topics(topics, mastery_by_topic)

    previous_version = await latest_roadmap_version(user_id, subject_id)
    previous_roadmap = (previous_version or {}).get("roadmap_json")

    roadmap, generated_by = await ai_service.generate_ai_roadmap(
        subject, topics, priorities, resources, mastery_by_topic,
        previous_roadmap=previous_roadmap, trigger=trigger,
    )

    changes = roadmap_service.diff_roadmaps(previous_roadmap, roadmap)
    version_number = ((previous_version or {}).get("version_number") or 0) + 1

    try:
        await db.insert("roadmap_versions", {
            "user_id": user_id,
            "subject_id": subject_id,
            "version_number": version_number,
            "roadmap_json": roadmap,
            "generated_by": generated_by,
            "trigger_attempt_id": (trigger or {}).get("attempt_id"),
            "changes_json": changes,
            "created_at": _now(),
        })
    except db.DatabaseError:
        log.warning("Roadmap version could not be saved for user/subject %s", subject_id)
        version_number = (previous_version or {}).get("version_number") or 0

    return {
        "roadmap": roadmap,
        "updated": True,
        "changes": changes,
        "version_number": version_number,
        "generated_by": generated_by,
        "priority_topics": priorities,
        "total_estimated_minutes": roadmap_service.total_estimated_minutes(roadmap),
        "next_step": roadmap_service.next_step(roadmap),
    }
