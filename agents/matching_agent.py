import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def match_brand_to_generic(supabase_client, search_query: str):
    """
    Searches for a brand name in Supabase using case-insensitive partial matching
    and falls back to searching by the primary brand keyword if no full match is found.
    """
    query_cleaned = search_query.strip()
    
    # 1. Try a case-insensitive partial match on the full query string
    response = (
        supabase_client.table("medicines")
        .select("*")
        .ilike("brand_name", f"%{query_cleaned}%")
        .execute()
    )
    
    if response.data and len(response.data) > 0:
        return response.data

    # 2. Fallback: If multi-word (e.g., "Augmentin 650 Duo"), try searching by the first main word (e.g., "Augmentin")
    words = query_cleaned.split()
    if len(words) > 1:
        primary_word = words[0]
        fallback_response = (
            supabase_client.table("medicines")
            .select("*")
            .ilike("brand_name", f"%{primary_word}%")
            .execute()
        )
        if fallback_response.data and len(fallback_response.data) > 0:
            return fallback_response.data

    # Return empty list if nothing matches
    return []
