# The AI pipeline

This document exists to answer one question directly: **is the AI real, or is it
a chatbot with a lookup table?**

It is real. Here is exactly how, and how to verify it yourself.

---

## 1. The prototype's fake tutor is gone

The original `js/app.js` answered questions like this:

```js
// DELETED — this no longer exists anywhere in the repository
function generateTutorReply(question, topic) {
  const q = question.toLowerCase();
  if (q.includes("example")) return "Here's an example: ...";
  if (q.includes("mistake")) return topic.content.mistakes[0];
  return "Great question! " + topic.content.intro;
}
```

Keyword matching against pre-written strings. It could not answer anything its
author hadn't anticipated.

`tools/audit.py` fails the build if that function name, the string `Local demo`,
or an `alert()`-based response path reappears anywhere outside tests and docs.

## 2. What replaced it

Every tutor message now takes this path:

```
browser
  └─ POST /api/ai/tutor  { message, topic, conversation }
       └─ routes/tutor.py
            ├─ deps.current_user        who is asking (from the token)
            ├─ deps.assert_no_active_quiz  server-side tutor lockout
            ├─ deps.ai_rate_limit
            └─ services/tutor_service.answer()
                 ├─ load the topic's real learning content from Postgres
                 ├─ load this student's measured mastery for the topic
                 ├─ load their weak topics across the subject
                 ├─ (documents) retrieve the top-k relevant chunks
                 └─ services/ai_provider → HTTPS → the model
```

`services/ai_provider.py` makes an actual HTTPS request:

- **Anthropic**: `POST https://api.anthropic.com/v1/messages`
- **OpenAI**: `POST https://api.openai.com/v1/chat/completions`

There is no branch anywhere in the codebase that returns a pre-written answer to
a student's question.

## 3. What the model is told

The tutor is not a bare chat window. `tutor_service.build_topic_context()`
assembles:

| Included | Why |
|---|---|
| Subject and topic name | scope |
| The topic's actual intro, concepts, practical explanation, common mistakes | so it teaches *this* curriculum, not generic internet knowledge |
| The student's mastery % and band for this topic | so a 32% student and an 88% student get different explanations |
| Their weak topics across the subject | so it can connect a gap to its real cause |
| The last 12 conversation turns | so follow-ups work |

The system prompt instructs it to teach rather than dump answers, to use the
student's measured level, and to say plainly when something is outside the
material rather than inventing it.

This is why the tutor is meaningfully better than pasting the question into a
generic chatbot: it knows what you got wrong last Tuesday.

## 4. No credentials means an error, not a fake answer

This is the important design decision, and it is enforced by a test.

```python
def test_no_canned_ai_response_is_ever_returned(...):
    monkeypatch.setattr(config, "AI_API_KEY", "")
    body = client.post("/api/ai/tutor", ...).json()
    assert "reply" not in body     # 503 AI_NOT_CONFIGURED
```

If `AI_API_KEY` is missing the API returns:

```json
{ "error": "AI_NOT_CONFIGURED",
  "message": "The AI Tutor isn't available: AI_API_KEY is not set on the backend." }
```

A demo that silently degrades into a scripted chatbot is worse than one that
says it isn't configured. So it says it isn't configured.

## 5. Verify it yourself

Four independent checks, in increasing order of certainty:

**a. The code path**
```bash
grep -rn "generateTutorReply\|Local demo" frontend/ backend/   # no results
python3 tools/audit.py                                          # PASS on fake AI
```

**b. It fails without a key**
```bash
# with AI_API_KEY unset in backend/.env
curl -s -X POST http://localhost:8000/api/ai/tutor \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message":"explain polymorphism","topic":"java-oop"}'
# => {"error":"AI_NOT_CONFIGURED", ...}
```
A fake chatbot would happily answer. This one refuses.

**c. It answers things nobody scripted**

Ask the tutor something absurd and specific:
> "Explain Java inheritance using only cooking metaphors, in exactly four sentences."

No keyword table produces that. A model does.

**d. Watch the network call**

Set `LOG_LEVEL=debug` on the backend and watch the outbound request to
`api.anthropic.com` in the logs.

## 6. Where else the AI is real

| Feature | Endpoint | Model use |
|---|---|---|
| AI Tutor (topics) | `POST /api/ai/tutor` | text, grounded in curriculum + mastery |
| AI Tutor (documents) | `POST /api/uploads/{id}/ask` | text, grounded in retrieved chunks |
| Roadmap generation | inside `complete` / `recompute` | structured JSON, validated, with fallback |
| Result explanation | `POST /api/ai/explain` | text, grounded in the real score breakdown |
| Document summary | `POST /api/uploads/{id}/summary` | text over extracted + vision content |
| Document quiz | `POST /api/uploads/{id}/quiz` | structured JSON, strictly validated |
| Page vision analysis | during upload processing | **vision**, on diagram/scanned pages |

## 7. The vision half

Vision is not applied blindly to every page — that would be slow and expensive.
`document_parser.classify_page()` labels each page and only some qualify:

| Quality | Meaning | Vision? |
|---|---|---|
| `text_rich` | plenty of extractable text, no significant images | no |
| `sparse` | very little text — probably a slide of diagrams | **yes** |
| `scanned` | no text layer at all | **yes** |
| `mixed` | substantial text *and* substantial images | **yes** |
| `empty` | nothing there | skipped entirely |

Selected pages are rendered to PNG and sent to the vision model, capped at
`MAX_VISION_PAGES` (default 12), prioritising `scanned` over `sparse` over
`mixed`. Source-code uploads never use vision.

The vision prompt asks for *meaning*, not description — "this ER diagram shows a
many-to-many between Student and Course resolved by Enrollment", not "there is a
diagram with boxes".

Results are cached by content hash, so re-processing the same page is free.

## 8. Why the AI can't corrupt your progress

The model orders and explains. It never measures.

```python
# roadmap_service.validate_ai_roadmap — the model claims 99%, we measured 32%
result["priority_topics"][0]["mastery"] == 32   # ours wins, always
```

Validation rejects any roadmap that references a topic or resource ID that
doesn't exist, clamps absurd time estimates to 180 minutes, and normalises
unknown step kinds to `learn`. On rejection: one repair retry, then the
deterministic fallback planner — which is still personalized by measured
mastery.

Tests: `test_ai_cannot_overwrite_mastery_numbers`,
`test_hallucinated_topic_id_is_rejected`, `test_falls_back_when_ai_hallucinates_ids`.
