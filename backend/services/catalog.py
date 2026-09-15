"""Read access to the seeded curriculum: subjects, topics, questions, resources."""
import db
import errors


async def all_subjects():
    return await db.select("subjects", {"select": "*", "order": "position.asc"})


async def get_subject(subject_id):
    subject = await db.select_one("subjects", {"select": "*", "id": "eq.%s" % subject_id})
    if not subject:
        raise errors.not_found("That subject doesn't exist.", code="SUBJECT_NOT_FOUND")
    return subject


async def topics_for(subject_id):
    return await db.select("topics", {
        "select": "*", "subject_id": "eq.%s" % subject_id, "order": "position.asc",
    })


async def get_topic(topic_id):
    topic = await db.select_one("topics", {"select": "*", "id": "eq.%s" % topic_id})
    if not topic:
        raise errors.not_found("That topic doesn't exist.", code="TOPIC_NOT_FOUND")
    return topic


async def all_topics():
    return await db.select("topics", {"select": "*", "order": "subject_id.asc,position.asc"})


async def questions_for(topic_id):
    return await db.select("questions", {
        "select": "*", "topic_id": "eq.%s" % topic_id, "order": "position.asc",
    })


async def questions_by_ids(ids):
    if not ids:
        return []
    joined = ",".join('"%s"' % i for i in ids)
    return await db.select("questions", {"select": "*", "id": "in.(%s)" % joined})


async def all_resources():
    return await db.select("resources", {"select": "*"})


async def resources_for_subject(subject_id):
    topics = await topics_for(subject_id)
    topic_ids = {t["id"] for t in topics}
    return [r for r in await all_resources() if r.get("topic_id") in topic_ids]


def public_question(row):
    """Strip the answer key. The browser must never receive correct_index."""
    return {
        "id": row["id"],
        "question": row["question"],
        "options": row["options"],
        "difficulty": row.get("difficulty"),
        "topic_id": row.get("topic_id"),
        "source_page": row.get("source_page"),
        "source_type": row.get("source_type"),
    }


def with_answer(row):
    return {
        "id": row["id"],
        "question": row["question"],
        "options": row["options"],
        "correct_index": row["correct_index"],
        "explanation": row.get("explanation"),
        "difficulty": row.get("difficulty"),
        "topic_id": row.get("topic_id"),
        "source_page": row.get("source_page"),
        "source_type": row.get("source_type"),
    }
