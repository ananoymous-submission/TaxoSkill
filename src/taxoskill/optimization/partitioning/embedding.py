"""Embed agent tasks with Qwen3-Embedding for clustering.

Two format-compatible backends that construct identical input strings:

- ``RemoteTaskEmbedder`` — calls an OpenAI-compatible ``/v1/embeddings`` endpoint (e.g. the Modal
  deployment of Qwen3-Embedding-8B). This is the default: fast, no local GPU.
- ``TaskEmbedder`` — loads the model locally via sentence-transformers (offline / verification).

Correct Qwen3-Embedding usage (verified against the model's own sentence-transformers config and
confirmed against the endpoint):

- **last-token pooling** and **L2-normalized** output, so cosine similarity is a dot product;
- **instruction-aware**: each text is formatted as ``Instruct: {instruction}\nQuery:{text}``. The
  OpenAI embeddings API has no separate instruction field, so the instruction is *prepended into
  the input string* — that prepended string is the mechanism, identical for both backends. The
  instruction states the clustering intent and is the one semantic lever of this method.

The default model sizes differ (remote 8B, local 4B), so their vectors are not output-equivalent and
their model identities produce different cache fingerprints.

What we embed per task is exactly the task instruction. Initial observations and environment
metadata are excluded so every clustering method has the same instruction-only input.

Partitioning commands select the backend through ``build_embedder``. The remote backend reads
``QWEN3_EMBED_URL`` from the environment; the local backend uses sentence-transformers.
"""

from __future__ import annotations

import json
import hashlib
import os
import time
import urllib.request
from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np

LOCAL_MODEL_NAME = "Qwen/Qwen3-Embedding-4B"
REMOTE_MODEL_NAME = "Qwen/Qwen3-Embedding-8B"
ENDPOINT_ENV = "QWEN3_EMBED_URL"
API_KEY_ENV = "QWEN3_EMBED_API_KEY"

# The clustering intent: what "same group" means. This is the only semantic input to the embedding.
CLUSTERING_INSTRUCTION = (
    "Identify the procedure the task requires the agent to carry out — the actions, tools and "
    "intermediate goals needed to complete it — so that tasks solved by the same procedure are "
    "grouped together, regardless of the specific objects, quantities, locations or wording."
)

TASK_TEMPLATE = "Task: {instruction}"

# Qwen3-Embedding query format (the model's own config ends the query prompt with "Query:").
_PROMPT_TEMPLATE = "Instruct: {instruction}\nQuery:"


# --- shared formatting (identical across backends) --------------------------------------------


def build_prompt(instruction: str = CLUSTERING_INSTRUCTION) -> str:
    """The exact instruction prompt prepended to every task text."""
    return _PROMPT_TEMPLATE.format(instruction=instruction)


def format_task(instruction: str) -> str:
    """The task text (before the Qwen instruction prompt is prepended)."""
    instruction = instruction.strip()
    if not instruction:
        raise ValueError("task instruction must be non-empty")
    return TASK_TEMPLATE.format(instruction=instruction)


def build_inputs(
    instructions: Sequence[str],
    instruction: str = CLUSTERING_INSTRUCTION,
) -> list[str]:
    """The exact strings sent to the model: instruction prompt + task text, one per task."""
    if len(instructions) == 0:
        raise ValueError("cannot embed an empty task list")
    prompt = build_prompt(instruction)
    return [prompt + format_task(instruction_text) for instruction_text in instructions]


def _l2_normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    if (norms == 0).any():
        raise ValueError("encountered a zero embedding vector")
    return (vectors / norms).astype(np.float32)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True)
class EmbeddingManifest:
    env: str
    task_ids: tuple[str, ...]
    task_file_sha256: str
    instruction_sha256: str
    formatted_input_sha256: str
    embedder: dict
    normalization: str
    shape: tuple[int, int]
    array_sha256: str
    fingerprint: str

    def to_dict(self) -> dict:
        value = asdict(self)
        value["task_ids"] = list(self.task_ids)
        value["shape"] = list(self.shape)
        return value


def input_fingerprint(
    *,
    env: str,
    task_ids: Sequence[str],
    instructions: Sequence[str],
    embedder: dict,
    task_file_sha256: str = "",
) -> tuple[str, str, str]:
    if len(task_ids) != len(instructions):
        raise ValueError("task ids and instructions must align")
    inputs = build_inputs(instructions)
    instruction_hash = _sha256_bytes(_canonical_json(list(zip(task_ids, instructions))))
    formatted_hash = _sha256_bytes(_canonical_json(list(zip(task_ids, inputs))))
    payload = {
        "env": env,
        "task_ids": list(task_ids),
        "task_file_sha256": task_file_sha256,
        "instruction_sha256": instruction_hash,
        "formatted_input_sha256": formatted_hash,
        "embedder": embedder,
        "normalization": "l2",
    }
    return _sha256_bytes(_canonical_json(payload))[:20], instruction_hash, formatted_hash


def create_manifest(
    *,
    env: str,
    task_ids: Sequence[str],
    instructions: Sequence[str],
    vectors: np.ndarray,
    embedder: dict,
    task_file_sha256: str = "",
) -> EmbeddingManifest:
    """Describe and fingerprint one immutable instruction-only embedding matrix."""
    if len(task_ids) != len(instructions) or len(task_ids) != len(vectors):
        raise ValueError("task ids, instructions, and embedding rows must align")
    if vectors.ndim != 2:
        raise ValueError("embedding array must be two-dimensional")
    fingerprint, instruction_hash, formatted_hash = input_fingerprint(
        env=env,
        task_ids=task_ids,
        instructions=instructions,
        embedder=embedder,
        task_file_sha256=task_file_sha256,
    )
    return EmbeddingManifest(
        env=env,
        task_ids=tuple(task_ids),
        task_file_sha256=task_file_sha256,
        instruction_sha256=instruction_hash,
        formatted_input_sha256=formatted_hash,
        embedder=embedder,
        normalization="l2",
        shape=(int(vectors.shape[0]), int(vectors.shape[1])),
        array_sha256=_sha256_bytes(np.ascontiguousarray(vectors).tobytes()),
        fingerprint=fingerprint,
    )


# --- remote backend (OpenAI-compatible /v1/embeddings) ----------------------------------------


@dataclass
class RemoteTaskEmbedder:
    endpoint_url: str | None = None  # None -> $QWEN3_EMBED_URL
    model: str = REMOTE_MODEL_NAME
    instruction: str = CLUSTERING_INSTRUCTION
    api_key: str | None = None  # None -> $QWEN3_EMBED_API_KEY if set, else no auth header
    batch_size: int = 32
    timeout: float = 300.0
    max_retries: int = 4

    def __post_init__(self) -> None:
        self.endpoint_url = self.endpoint_url or os.environ.get(ENDPOINT_ENV)
        if not self.endpoint_url:
            raise ValueError(
                f"no embedding endpoint: pass endpoint_url or set ${ENDPOINT_ENV}"
            )
        self.api_key = self.api_key or os.environ.get(API_KEY_ENV)

    def full_input(self, instruction: str) -> str:
        return build_prompt(self.instruction) + format_task(instruction)

    def describe(self) -> dict:
        return {
            "backend": "remote",
            "model": self.model,
            "batch_size": self.batch_size,
            "instruction": self.instruction,
            "prompt": build_prompt(self.instruction),
            "task_template": TASK_TEMPLATE,
        }

    def _post(self, batch: list[str]) -> list[list[float]]:
        payload = json.dumps({"model": self.model, "input": batch}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                request = urllib.request.Request(self.endpoint_url, data=payload, headers=headers)
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    body = json.load(response)
                rows = sorted(body["data"], key=lambda item: item["index"])
                if len(rows) != len(batch):
                    raise ValueError(f"endpoint returned {len(rows)} vectors for {len(batch)} inputs")
                return [row["embedding"] for row in rows]
            except Exception as error:  # network / transient server errors: retry with backoff
                last_error = error
                if attempt == self.max_retries:
                    break
                wait = 2.0 * attempt
                print(
                    f"[embed] request failed ({error}); retry {attempt}/{self.max_retries} in {wait:.0f}s",
                    flush=True,
                )
                time.sleep(wait)
        raise RuntimeError(f"embedding endpoint failed after {self.max_retries} attempts: {last_error}")

    def encode(
        self, instructions: Sequence[str], *, show_progress: bool = True
    ) -> np.ndarray:
        """Return an ``(n_tasks, dim)`` array of L2-normalized task embeddings."""
        inputs = build_inputs(instructions, self.instruction)
        vectors: list[list[float]] = []
        total = len(inputs)
        for start in range(0, total, self.batch_size):
            batch = inputs[start : start + self.batch_size]
            vectors.extend(self._post(batch))
            done = min(start + self.batch_size, total)
            if show_progress:
                print(f"[embed] {done}/{total}", flush=True)
        return _l2_normalize(np.asarray(vectors, dtype=np.float32))


# --- local backend (sentence-transformers) ----------------------------------------------------


def _select_device() -> str:
    import torch

    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


@dataclass
class TaskEmbedder:
    """Local Qwen3-Embedding via sentence-transformers (offline / to verify the remote backend)."""

    instruction: str = CLUSTERING_INSTRUCTION
    model_name: str = LOCAL_MODEL_NAME
    device: str | None = None  # None -> auto (mps > cuda > cpu)
    max_seq_length: int = 1024
    batch_size: int = 16

    def __post_init__(self) -> None:
        import torch
        from sentence_transformers import SentenceTransformer

        self.device = self.device or _select_device()
        dtype = torch.float32 if self.device == "cpu" else torch.float16
        self._model = SentenceTransformer(
            self.model_name, device=self.device, model_kwargs={"torch_dtype": dtype}
        )
        self._model.max_seq_length = self.max_seq_length
        self._dtype = str(dtype).replace("torch.", "")

    def full_input(self, instruction: str) -> str:
        return build_prompt(self.instruction) + format_task(instruction)

    def describe(self) -> dict:
        pooling, normalize = self._model[1], self._model[-1]
        pooling_config = pooling.get_config_dict()
        return {
            "backend": "local",
            "model": self.model_name,
            "device": self.device,
            "dtype": self._dtype,
            "embedding_dim": self._model.get_embedding_dimension(),
            "max_seq_length": self._model.max_seq_length,
            "pooling_mode": pooling_config.get("pooling_mode", "unknown"),
            "normalize_module": type(normalize).__name__,
            "instruction": self.instruction,
            "prompt": build_prompt(self.instruction),
            "task_template": TASK_TEMPLATE,
        }

    def encode(
        self, instructions: Sequence[str], *, show_progress: bool = True
    ) -> np.ndarray:
        texts = [format_task(instruction) for instruction in instructions]
        if not texts:
            raise ValueError("cannot embed an empty task list")
        embeddings = self._model.encode(
            texts,
            prompt=build_prompt(self.instruction),
            batch_size=self.batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return np.asarray(embeddings, dtype=np.float32)


def build_embedder(backend: str):
    if backend == "remote":
        return RemoteTaskEmbedder()
    if backend == "local":
        return TaskEmbedder()
    raise ValueError(f"unknown backend {backend!r}; use 'remote' or 'local'")
