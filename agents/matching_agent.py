from difflib import get_close_matches

def match_brand_to_generic(supabase_client, brand_query):
    # Fetch all brand names for fuzzy matching safety layer
    response = supabase_client.table("medicines").select("brand_name").execute()
    if not response.data:
        return None
        
    all_brands = [item['brand_name'] for item in response.data]
    close_matches = get_close_matches(brand_query, all_brands, n=1, cutoff=0.70)
    
    if close_matches:
        matched_brand = close_matches[0]
        # Fetch full record for the matched brand
        detail_response = supabase_client.table("medicines").select("*").eq("brand_name", matched_brand).execute()
        return detail_response.data[0] if detail_response.data else None
    return None
