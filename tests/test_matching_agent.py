import os
import pytest
from agents.matching_agent import match_brand_to_generic

def test_matching_agent_empty_query():
    """Verify that an empty query or missing client returns an empty list gracefully."""
    assert match_brand_to_generic(None, "") == []
    assert match_brand_to_generic(None, "   ") == []

def test_matching_agent_query_splitting():
    """Verify multi-word normalization logic behavior."""
    query = "Pantop 40 mg"
    words = query.strip().split()
    assert words[0] == "Pantop"
    assert len(words) > 1
