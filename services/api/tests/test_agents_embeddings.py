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
    vec = embed("")
    assert all(v == 0.0 for v in vec)
