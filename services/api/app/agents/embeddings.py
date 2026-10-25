"""Local lexical embeddings for the Compliance RAG agent.

**Not a real embeddings model.** No embeddings-capable provider is keyed
in this build (Groq doesn't serve one — confirmed via its live model
list; see config/llm_providers.yaml) — a real gap, documented rather
than hidden (progress.md, Phase 6a). This is a deterministic feature-
hashing bag-of-words vector: it captures lexical overlap (shared
words/terms), not semantic similarity, so retrieval quality is strictly
weaker than a real sentence-embedding model. It exists so the RAG
pipeline's *mechanics* — chunk, embed, store in pgvector, retrieve by
cosine distance, threshold, refuse below threshold, cite — are real and
testable now, with a real embedding model a drop-in swap later (same
`embed(text) -> list[float]` signature, same dimension via
app.models.rag.EMBEDDING_DIM).
"""

import hashlib
import math
import re

from app.models.rag import EMBEDDING_DIM

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

# Without this, a short clause that happens to share only stopwords with
# the query ("the", "on", "a") can out-score a longer, genuinely relevant
# clause after L2 normalisation — found via a real retrieval test that
# returned the wrong clause. Still a lexical, not semantic, signal; this
# just stops the crudest false positives.
_STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "of",
    "in",
    "on",
    "at",
    "to",
    "for",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "it",
    "its",
    "this",
    "that",
    "with",
    "as",
    "by",
    "from",
    "has",
    "have",
    "had",
    "not",
    "no",
    "only",
    "can",
    "when",
    "where",
    "which",
    "who",
    "will",
    "shall",
    "may",
}


_TYPO_MAP = {
    "helo": "hello",
    "hi": "hello",
    "hey": "hello",
    "deposite": "deposit",
}


def _tokenise(text: str) -> list[str]:
    raw_tokens = _TOKEN_PATTERN.findall(text.lower())
    return [_TYPO_MAP.get(t, t) for t in raw_tokens if t not in _STOPWORDS]


def embed(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIM
    for token in _tokenise(text):
        bucket = (
            int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16) % EMBEDDING_DIM
        )
        vector[bucket] += 1.0
    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0:
        return vector
    return [v / norm for v in vector]
