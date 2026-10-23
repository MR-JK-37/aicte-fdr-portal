from app.documents.security_scan import check_magic_bytes, sanitise_pdf
from tests.fixtures import random_fdr_fields, render_fdr_pdf


def test_magic_bytes_accepts_real_pdf():
    data = render_fdr_pdf(random_fdr_fields(seed=1), 0)
    result = check_magic_bytes(data, "application/pdf")
    assert result.passed is True


def test_magic_bytes_rejects_mismatched_declared_type():
    data = render_fdr_pdf(random_fdr_fields(seed=1), 0)
    result = check_magic_bytes(data, "image/png")
    assert result.passed is False


def test_magic_bytes_rejects_disallowed_type():
    # A renamed-extension attack: real content is a shell script, not a
    # document, regardless of what the client claims.
    data = b"#!/bin/sh\necho pwned\n"
    result = check_magic_bytes(data, "application/pdf")
    assert result.passed is False


def test_sanitise_pdf_round_trips_a_clean_pdf():
    data = render_fdr_pdf(random_fdr_fields(seed=2), 0)
    result, sanitised = sanitise_pdf(data)
    assert result.passed is True
    assert sanitised is not None
    assert sanitised.startswith(b"%PDF")


def test_sanitise_pdf_rejects_garbage():
    result, sanitised = sanitise_pdf(b"not a pdf at all")
    assert result.passed is False
    assert sanitised is None
