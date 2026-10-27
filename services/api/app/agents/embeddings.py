"""Real local sentence embeddings for the Compliance RAG agent.

Uses `fastembed` (ONNX Runtime) running the `BAAI/bge-small-en-v1.5`
model (384 dims) entirely in-process — no network call per request, no
API key, and (unlike every cloud LLM provider in config/llm_providers.yaml)
eligible for Tier S data, since nothing leaves the host. The model
weights (~70MB) are fetched once from Hugging Face Hub on first use and
cached under `~/.cache/fastembed` (override with `FASTEMBED_CACHE_PATH`
or `HF_HOME`); after that, inference is offline.

This replaces an earlier lexical feature-hashing placeholder (deterministic
bag-of-words, no stemming/synonyms) that could not match a real question's
phrasing against clearly relevant stored text — e.g. "what's the penalty
for being late" failed to retrieve a clause titled exactly "Penalty for
delayed submission" because the two share almost no surface tokens. A
real sentence embedding model captures that kind of paraphrase/semantic
similarity, which is the actual job of this function.

Interface is unchanged (`embed(text) -> list[float]`, same
`app.models.rag.EMBEDDING_DIM`), so nothing calling this needed to change.
"""

from functools import lru_cache

MODEL_NAME = "BAAI/bge-small-en-v1.5"


@lru_cache(maxsize=1)
def _model():
    # Imported lazily so importing this module (e.g. at app startup, or
    # anywhere that doesn't actually call embed()) never pays the ~30s
    # one-time model-load cost or requires the model files to exist.
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=MODEL_NAME)


_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


def embed(text: str, *, is_query: bool = False) -> list[float]:
    """`is_query=True` for the user's question, `False` (default) for
    stored clause text. bge models are trained asymmetrically — the
    query side gets this instruction prefix, the passage/document side
    gets none — and skipping that distinction measurably weakens
    retrieval versus using the model as intended."""
    prefixed = f"{_QUERY_INSTRUCTION}{text}" if is_query else text
    (vector,) = _model().embed([prefixed])
    return vector.tolist()
