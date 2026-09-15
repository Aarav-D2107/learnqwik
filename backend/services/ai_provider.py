"""
AI provider abstraction.

Nothing else in the codebase knows which vendor is in use. Swap providers by
changing AI_PROVIDER / AI_API_KEY / TEXT_MODEL / VISION_MODEL in the
environment — no code change.

    AIProvider
      ├── generate_text()
      ├── analyze_image()
      ├── generate_structured_output()
      └── create_embedding()

If credentials are missing we raise AINotConfiguredError. We never return a
canned response pretending to be a model. Callers decide how to degrade
(the roadmap engine, for instance, falls back to its deterministic planner).
"""
import base64
import json
import logging

import config

# httpx is imported lazily so that the pure-logic modules (validation, question
# shaping, page selection) can be imported and unit-tested on a machine with no
# third-party packages installed at all. See tools/selfcheck.py.
try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None


def _require_httpx():
    if httpx is None:
        raise AIUnavailableError(
            "The 'httpx' package is not installed. Run: pip install -r requirements.txt"
        )

log = logging.getLogger("learnqwik.ai")


class AIError(Exception):
    """Base class for all AI failures. Carries a stable machine-readable code."""
    code = "AI_SERVICE_ERROR"
    http_status = 502

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class AINotConfiguredError(AIError):
    code = "AI_NOT_CONFIGURED"
    http_status = 503


class AIUnavailableError(AIError):
    code = "AI_SERVICE_UNAVAILABLE"
    http_status = 503


class AIInvalidOutputError(AIError):
    code = "AI_INVALID_OUTPUT"
    http_status = 502


def _strip_fences(text):
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1] if "\n" in t else t
        if t.endswith("```"):
            t = t[:-3]
        t = t.replace("```json", "").replace("```", "")
    return t.strip()


def extract_json(text):
    """Best-effort JSON recovery from a model response."""
    cleaned = _strip_fences(text)
    try:
        return json.loads(cleaned)
    except (ValueError, TypeError):
        pass
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(cleaned[start:end + 1])
        except ValueError:
            pass
    raise AIInvalidOutputError("Model response was not valid JSON")


class AIProvider:
    """Interface. Subclasses implement the four primitives."""

    name = "base"

    async def generate_text(self, prompt, system=None, max_tokens=None, temperature=0.3):
        raise NotImplementedError

    async def analyze_image(self, image_bytes, prompt, media_type="image/png", system=None):
        raise NotImplementedError

    async def generate_structured_output(self, prompt, system=None, max_tokens=None):
        raw = await self.generate_text(
            prompt,
            system=(system or "") + "\n\nRespond with a single valid JSON object and nothing else. "
                                    "No prose, no markdown fences.",
            max_tokens=max_tokens,
            temperature=0.1,
        )
        return extract_json(raw)

    async def create_embedding(self, text):
        raise NotImplementedError


class AnthropicProvider(AIProvider):
    name = "anthropic"
    API = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key, text_model, vision_model, base_url=None):
        self.api_key = api_key
        self.text_model = text_model
        self.vision_model = vision_model
        self.url = (base_url.rstrip("/") + "/v1/messages") if base_url else self.API

    def _headers(self):
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    async def _post(self, body):
        _require_httpx()
        try:
            async with httpx.AsyncClient(timeout=config.AI_TIMEOUT_SECONDS) as client:
                resp = await client.post(self.url, headers=self._headers(), json=body)
        except httpx.RequestError as exc:
            log.warning("AI transport failure: %s", type(exc).__name__)
            raise AIUnavailableError("Could not reach the AI provider.")
        if resp.status_code == 401:
            raise AINotConfiguredError("The AI API key was rejected by the provider.")
        if resp.status_code == 429:
            raise AIUnavailableError("The AI provider is rate limiting requests. Try again shortly.")
        if resp.status_code >= 400:
            # Never log the response body: it can echo prompt content.
            log.warning("AI provider returned HTTP %s", resp.status_code)
            raise AIUnavailableError("The AI service returned an error. Please try again.")
        return resp.json()

    @staticmethod
    def _text_of(data):
        parts = []
        for block in data.get("content", []) or []:
            if block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts).strip()

    async def generate_text(self, prompt, system=None, max_tokens=None, temperature=0.3):
        body = {
            "model": self.text_model,
            "max_tokens": max_tokens or config.AI_MAX_OUTPUT_TOKENS,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            body["system"] = system
        return self._text_of(await self._post(body))

    async def analyze_image(self, image_bytes, prompt, media_type="image/png", system=None):
        body = {
            "model": self.vision_model,
            "max_tokens": config.AI_MAX_OUTPUT_TOKENS,
            "temperature": 0.2,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image", "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": base64.b64encode(image_bytes).decode("ascii"),
                    }},
                    {"type": "text", "text": prompt},
                ],
            }],
        }
        if system:
            body["system"] = system
        return self._text_of(await self._post(body))

    async def create_embedding(self, text):
        raise AINotConfiguredError(
            "This provider has no embedding endpoint configured. "
            "LearnQwik falls back to keyword retrieval automatically."
        )


class OpenAIProvider(AIProvider):
    name = "openai"
    BASE = "https://api.openai.com/v1"

    def __init__(self, api_key, text_model, vision_model, embedding_model=None, base_url=None):
        self.api_key = api_key
        self.text_model = text_model
        self.vision_model = vision_model
        self.embedding_model = embedding_model
        self.base = (base_url or self.BASE).rstrip("/")

    def _headers(self):
        return {"Authorization": "Bearer %s" % self.api_key, "Content-Type": "application/json"}

    async def _post(self, path, body):
        _require_httpx()
        try:
            async with httpx.AsyncClient(timeout=config.AI_TIMEOUT_SECONDS) as client:
                resp = await client.post(self.base + path, headers=self._headers(), json=body)
        except httpx.RequestError as exc:
            log.warning("AI transport failure: %s", type(exc).__name__)
            raise AIUnavailableError("Could not reach the AI provider.")
        if resp.status_code == 401:
            raise AINotConfiguredError("The AI API key was rejected by the provider.")
        if resp.status_code == 429:
            raise AIUnavailableError("The AI provider is rate limiting requests. Try again shortly.")
        if resp.status_code >= 400:
            log.warning("AI provider returned HTTP %s", resp.status_code)
            raise AIUnavailableError("The AI service returned an error. Please try again.")
        return resp.json()

    @staticmethod
    def _text_of(data):
        try:
            return (data["choices"][0]["message"]["content"] or "").strip()
        except (KeyError, IndexError, TypeError):
            raise AIInvalidOutputError("Unexpected response shape from the AI provider.")

    async def generate_text(self, prompt, system=None, max_tokens=None, temperature=0.3):
        messages = ([{"role": "system", "content": system}] if system else []) + \
                   [{"role": "user", "content": prompt}]
        data = await self._post("/chat/completions", {
            "model": self.text_model,
            "max_tokens": max_tokens or config.AI_MAX_OUTPUT_TOKENS,
            "temperature": temperature,
            "messages": messages,
        })
        return self._text_of(data)

    async def analyze_image(self, image_bytes, prompt, media_type="image/png", system=None):
        data_url = "data:%s;base64,%s" % (media_type, base64.b64encode(image_bytes).decode("ascii"))
        messages = ([{"role": "system", "content": system}] if system else []) + [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": data_url}},
                {"type": "text", "text": prompt},
            ],
        }]
        data = await self._post("/chat/completions", {
            "model": self.vision_model,
            "max_tokens": config.AI_MAX_OUTPUT_TOKENS,
            "temperature": 0.2,
            "messages": messages,
        })
        return self._text_of(data)

    async def create_embedding(self, text):
        if not self.embedding_model:
            raise AINotConfiguredError("EMBEDDING_MODEL is not set.")
        data = await self._post("/embeddings", {"model": self.embedding_model, "input": text})
        try:
            return data["data"][0]["embedding"]
        except (KeyError, IndexError, TypeError):
            raise AIInvalidOutputError("Unexpected embedding response shape.")


_provider_cache = {}


def get_provider():
    """Factory. Raises AINotConfiguredError when credentials are absent."""
    if not config.AI_API_KEY:
        raise AINotConfiguredError(
            "AI is not configured. Set AI_PROVIDER and AI_API_KEY on the backend "
            "(see backend/.env.example) to enable the AI Tutor, document summaries, "
            "Vision analysis, document quizzes and AI roadmap generation."
        )

    key = (config.AI_PROVIDER, config.TEXT_MODEL, config.VISION_MODEL)
    if key in _provider_cache:
        return _provider_cache[key]

    if config.AI_PROVIDER == "anthropic":
        provider = AnthropicProvider(
            config.AI_API_KEY, config.TEXT_MODEL, config.VISION_MODEL,
            base_url=config.AI_BASE_URL or None,
        )
    elif config.AI_PROVIDER in ("openai", "openai-compatible", "azure-openai"):
        provider = OpenAIProvider(
            config.AI_API_KEY, config.TEXT_MODEL, config.VISION_MODEL,
            embedding_model=config.EMBEDDING_MODEL or None,
            base_url=config.AI_BASE_URL or None,
        )
    else:
        raise AINotConfiguredError(
            "Unknown AI_PROVIDER %r. Supported values: anthropic, openai, "
            "openai-compatible." % config.AI_PROVIDER
        )

    _provider_cache[key] = provider
    return provider


def reset_provider_cache():
    """Used by tests when swapping in a mock provider."""
    _provider_cache.clear()
