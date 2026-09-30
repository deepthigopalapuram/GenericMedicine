import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

def match_brand_to_generic(supabase_client, search_query: str):
    """
    Searches for a brand name in Supabase using case-insensitive partial matching (ilike).
    If an error or failure occurs, it displays the input query and the exact reason.
    """
    if not supabase_client:
        print(f"Input Query: '{search_query}' | Failure Reason: Supabase client is not initialized.")
        return []

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
                
    except Exception as e:
        # Catch any database or network errors and display input + exact reason
        print(f"Input Query: '{search_query}' | Exact Failure Reason: {str(e)}")
        
    return []
