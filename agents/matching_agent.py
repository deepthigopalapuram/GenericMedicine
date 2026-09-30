import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

def match_brand_to_generic(supabase_client, search_query: str):
    """
    Searches for a brand name in Supabase using case-insensitive partial matching (ilike).
    Returns matching rows or a structured error dictionary with query and exception details.
    """
    if not supabase_client:
        return {
            "error": "Supabase client is not initialized.",
            "query_attempted": search_query,
            "table": "medicines",
            "filter": f"ilike brand_name %{search_query}%"
        }

    query_cleaned = search_query.strip()
    
    try:
        # 1. Try a case-insensitive partial match on the full query string
        response = (
            supabase_client.table("medicines")
            .select("*")
            .ilike("brand_name", f"%{query_cleaned}%")
            .execute()
        )
        
        if response.data and len(response.data) > 0:
            return response.data

        # 2. Fallback: If multi-word query, try searching by the first primary keyword
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
                
        return []
                
    except Exception as e:
        # Capture the exact exception and query context for transparency
        return {
            "error": str(e),
            "query_attempted": query_cleaned,
            "table": "medicines",
            "filter": f"ilike brand_name %{query_cleaned}%"
        }
