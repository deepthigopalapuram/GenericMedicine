import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

def match_brand_to_generic(supabase_client, search_query: str):
    """
    Searches for a brand name in Supabase using case-insensitive partial matching (ilike).
    Returns matching rows or a detailed diagnostic dictionary on empty/error states.
    """
    if not supabase_client:
        return {
            "error": "Supabase client is not initialized.",
            "query_attempted": search_query,
            "table": "medicines",
            "filter": f"ilike brand_name %{search_query}%"
        }

    query_cleaned = search_query.strip()
    target_table = "medicines"
    
    # Properly format wildcard string for Supabase ilike
    wildcard_query = f"%{query_cleaned}%"
    filter_desc = f"ilike brand_name {wildcard_query}"
    
    try:
        # 1. Try a case-insensitive partial match on the full query string
        response = (
            supabase_client.table(target_table)
            .select("*")
            .ilike("brand_name", wildcard_query)
            .execute()
        )
        
        if response.data and len(response.data) > 0:
            return response.data

        # 2. Fallback: If multi-word query, try searching by the first primary keyword
        words = query_cleaned.split()
        if len(words) > 1:
            primary_word = words[0]
            fallback_wildcard = f"%{primary_word}%"
            fallback_filter = f"ilike brand_name {fallback_wildcard}"
            
            fallback_response = (
                supabase_client.table(target_table)
                .select("*")
                .ilike("brand_name", fallback_wildcard)
                .execute()
            )
            if fallback_response.data and len(fallback_response.data) > 0:
                return fallback_response.data
            else:
                return {
                    "error": "Zero rows returned from Supabase for both full query and primary keyword fallback.",
                    "query_attempted": query_cleaned,
                    "table": target_table,
                    "filter_tried": f"1) {filter_desc} | 2) {fallback_filter}",
                    "response_data": fallback_response.data
                }
                
        # If single word and 0 rows found
        return {
            "error": "Zero rows found matching this query in the database.",
            "query_attempted": query_cleaned,
            "table": target_table,
            "filter": filter_desc,
            "response_data": response.data
        }
                
    except Exception as e:
        # Capture exact backend/SQL/API exceptions
        return {
            "error": str(e),
            "query_attempted": query_cleaned,
            "table": target_table,
            "filter": filter_desc
        }
