import math

from app.agents.embeddings import embed


def test_embedding_is_unit_normalised():
    vec = embed("maturity date issue date tenor")
    norm = math.sqrt(sum(v * v for v in vec))
    assert abs(norm - 1.0) < 1e-6


def test_identical_text_gives_identical_vector():
    assert embed("security deposit release") == embed("security deposit release")


def test_related_text_scores_higher_than_unrelated():
    def cosine(a, b):
        return sum(x * y for x, y in zip(a, b, strict=True))

    base = embed("security deposit release eligibility maturity")
    related = embed("release of security deposit on maturity")
    unrelated = embed("orange banana fruit basket recipe")

    assert cosine(base, related) > cosine(base, unrelated)


def test_empty_text_does_not_divide_by_zero():
    """The old lexical hash's `embed("")` returned an all-zero vector
    (nothing to tokenise, so nothing to sum before normalising). A real
    sentence-embedding model still produces a meaningful unit vector for
    an empty string — it doesn't special-case "no tokens" the way a
    bag-of-words hash does. What must still hold, for either
    implementation, is: no exception and no NaN/zero-norm output."""
    vec = embed("")
    norm = math.sqrt(sum(v * v for v in vec))
    assert math.isfinite(norm)
    assert norm > 0.0
