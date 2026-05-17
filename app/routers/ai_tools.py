"""
Async job-based AI tools API.

POST /api/ai-tools/summary/jobs          — start a summary job, returns job_id (HTTP 202)
GET  /api/ai-tools/summary/jobs/{job_id} — poll job status, progress (0-100), and result
"""

import json
import logging
import re
import uuid
from enum import Enum
from typing import Dict, List, Optional

import openai
from fastapi import APIRouter, BackgroundTasks, HTTPException
from json_repair import repair_json
from pydantic import BaseModel, field_validator

from app.config import settings
from app.models.article import Article

logger = logging.getLogger(__name__)
MIN_CONTENT_LENGTH = 50

FREE_MODELS: List[str] = [
    "deepseek/deepseek-r1:free",
    "qwen/qwen3-coder:free",
    "openai/gpt-oss-20b:free",
]

router = APIRouter(prefix="/ai-tools", tags=["ai-tools"])


# ---------------------------------------------------------------------------
# Summary result schema
# ---------------------------------------------------------------------------

class ArticleSummary(BaseModel):
    title: str
    summary: str
    key_points: List[str]
    tags: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# Job schema
# ---------------------------------------------------------------------------

class JobStatus(str, Enum):
    pending   = "pending"
    running   = "running"
    completed = "completed"
    failed    = "failed"


class CreateSummaryJobRequest(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def content_must_be_meaningful(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Content must not be empty.")
        if len(v) < MIN_CONTENT_LENGTH:
            raise ValueError(f"Content too short — minimum {MIN_CONTENT_LENGTH} characters.")
        return v


class CreateJobResponse(BaseModel):
    job_id:   str
    status:   JobStatus
    progress: int
    message:  str


class JobStatusResponse(BaseModel):
    job_id:   str
    status:   JobStatus
    progress: int
    message:  str
    result:   Optional[ArticleSummary] = None
    error:    Optional[str] = None


# ---------------------------------------------------------------------------
# Job store (in-memory)
# ---------------------------------------------------------------------------

class InMemoryJobStore:
    """Process-scoped store. Jobs are lost on restart and not shared across workers."""

    def __init__(self) -> None:
        self._store: Dict[str, dict] = {}

    def create(self, job_id: str) -> None:
        self._store[job_id] = {
            "job_id":   job_id,
            "status":   JobStatus.pending,
            "progress": 0,
            "message":  "Job created",
            "result":   None,
            "error":    None,
        }

    def get(self, job_id: str) -> Optional[dict]:
        return self._store.get(job_id)

    def update(self, job_id: str, **kwargs) -> None:
        if job_id in self._store:
            self._store[job_id].update(kwargs)


job_store = InMemoryJobStore()


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are an expert article summarizer. Read the article the user provides and produce \
a structured summary.

Return ONLY a valid JSON object — no markdown, no explanation — matching this schema exactly:

{
  "title": "<article title, extracted or inferred>",
  "summary": "<2-4 sentence paragraph capturing the main idea and conclusion>",
  "key_points": [
    "<key point 1>",
    "<key point 2>",
    "<key point 3>"
  ],
  "tags": ["<topic tag 1>", "<topic tag 2>"]
}

Rules:
- "title": use the article's own title if present; otherwise infer a concise one.
- "summary": 2-4 sentences. Capture the core argument or narrative and the conclusion.
- "key_points": 3-7 bullet-style strings. Each must be a standalone, informative fact or \
takeaway from the article.
- "tags": 2-5 short lowercase topic tags (e.g. "technology", "health", "climate"). \
Omit or set to null if the topic is too narrow to tag meaningfully.
- Output ONLY the JSON object. No extra text.\
"""


def _build_user_message(content: str) -> str:
    return f"Article:\n{content}"


# ---------------------------------------------------------------------------
# JSON extraction helpers (mirrors itinerary pattern)
# ---------------------------------------------------------------------------

def _strip_reasoning_tags(text: str) -> str:
    return re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()


def _extract_json(text: str) -> dict:
    text = _strip_reasoning_tags(text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    start = text.find("{")
    if start != -1:
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start: i + 1])
                    except json.JSONDecodeError:
                        break

    repaired = repair_json(text, return_objects=True)
    if isinstance(repaired, dict) and repaired:
        return repaired

    raise ValueError("No valid JSON object found in the LLM response.")


# ---------------------------------------------------------------------------
# Background job
# ---------------------------------------------------------------------------

async def _run_summary_job(job_id: str, content: str, article_id: Optional[int] = None) -> None:
    def step(progress: int, message: str) -> None:
        job_store.update(job_id, status=JobStatus.running, progress=progress, message=message)

    try:
        # ── 10% ── Validate ───────────────────────────────────────────────────
        step(10, "Validating request...")

        if not settings.openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured on the server.")

        # ── 25% ── Build prompt ───────────────────────────────────────────────
        step(25, "Preparing prompt...")
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": _build_user_message(content)},
        ]

        # ── 40% ── Call OpenRouter ────────────────────────────────────────────
        step(40, "Calling OpenRouter...")
        client = openai.AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
            timeout=settings.openrouter_timeout,
        )

        raw_text = ""
        last_error = "No models available."

        for model in FREE_MODELS:
            try:
                logger.info("[job %s] Trying model: %s", job_id, model)
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=2048,
                )
            except openai.RateLimitError:
                last_error = f"{model}: rate limited"
                logger.warning("[job %s] Rate limited on %s", job_id, model)
                continue
            except openai.APIStatusError as exc:
                if exc.status_code in (400, 404) or exc.status_code >= 500:
                    last_error = f"{model}: HTTP {exc.status_code}"
                    logger.warning("[job %s] HTTP %s on %s", job_id, exc.status_code, model)
                    continue
                raise RuntimeError(f"OpenRouter error {exc.status_code}: {exc.message}")
            except openai.APITimeoutError:
                last_error = f"{model}: timeout"
                logger.warning("[job %s] Timeout on %s", job_id, model)
                continue
            except openai.APIConnectionError as exc:
                raise RuntimeError(f"Cannot reach OpenRouter: {exc}")
            except openai.AuthenticationError:
                raise RuntimeError("Invalid OpenRouter API key.")

            msg = response.choices[0].message
            raw_text = msg.content or ""

            if not raw_text:
                extra: dict = getattr(msg, "model_extra", None) or {}
                raw_text = (
                    getattr(msg, "reasoning_content", None)
                    or getattr(msg, "reasoning", None)
                    or extra.get("reasoning_content")
                    or extra.get("reasoning")
                    or extra.get("thinking")
                    or ""
                )

            if not raw_text:
                logger.warning(
                    "[job %s] Empty response from %s — model_extra keys: %s",
                    job_id, model,
                    list((getattr(msg, "model_extra", None) or {}).keys()),
                )
                last_error = f"{model}: empty response"
                continue

            logger.info("[job %s] Got response from %s", job_id, model)
            break

        if not raw_text:
            raise RuntimeError(f"All models failed. Last error: {last_error}")

        # ── 70% ── Parse JSON ─────────────────────────────────────────────────
        step(70, "Parsing AI response...")
        try:
            parsed_dict = _extract_json(raw_text)
        except ValueError:
            raise RuntimeError("LLM response could not be parsed as JSON. Raw: " + raw_text[:500])

        # ── 90% ── Validate schema ────────────────────────────────────────────
        step(90, "Validating summary structure...")
        try:
            summary = ArticleSummary(**parsed_dict)
        except Exception as exc:
            raise RuntimeError(f"LLM output does not match summary schema: {exc}")

        # ── 95% ── Persist to MongoDB ─────────────────────────────────────────
        if article_id is not None:
            step(95, "Saving to database...")
            article = await Article.find_one(Article.article_id == article_id)
            if article:
                await article.update({"$set": {
                    "ai_summary":    summary.summary,
                    "ai_key_points": summary.key_points,
                    "ai_tags":       summary.tags,
                }})
                logger.info("[job %s] Saved AI summary to article %s.", job_id, article_id)

        # ── 100% ── Done ──────────────────────────────────────────────────────
        job_store.update(
            job_id,
            status=JobStatus.completed,
            progress=100,
            message="Completed",
            result=summary.model_dump(),
        )
        logger.info("[job %s] Completed successfully.", job_id)

    except Exception as exc:
        logger.exception("[job %s] Failed: %s", job_id, exc)
        job_store.update(
            job_id,
            status=JobStatus.failed,
            message="Job failed",
            error=str(exc),
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/summary/jobs",
    response_model=CreateJobResponse,
    status_code=202,
    summary="Start article summary job",
)
async def create_summary_job(
    request: CreateSummaryJobRequest,
    background_tasks: BackgroundTasks,
) -> CreateJobResponse:
    """
    Immediately returns a `job_id`. Summarisation runs in the background.
    Poll `GET /api/ai-tools/summary/jobs/{job_id}` every few seconds to track progress.
    """
    job_id = str(uuid.uuid4())
    job_store.create(job_id)
    background_tasks.add_task(_run_summary_job, job_id, request.content)

    return CreateJobResponse(
        job_id=job_id,
        status=JobStatus.pending,
        progress=0,
        message="Job created",
    )


@router.get(
    "/summary/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Poll article summary job status",
)
async def get_summary_job_status(job_id: str) -> JobStatusResponse:
    """
    Returns the current status, progress (0-100), and result once completed.
    """
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    result: Optional[ArticleSummary] = None
    if job["result"] is not None:
        result = ArticleSummary(**job["result"])

    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        result=result,
        error=job["error"],
    )
