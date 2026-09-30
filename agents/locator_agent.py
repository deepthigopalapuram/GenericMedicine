def find_nearest_stores_safely(supabase_client, lat, lon):
    # Progressive radius fallback: 5km -> 10km -> 20km
    radii = [5000, 10000, 20000]
    
    for radius in radii:
        response = supabase_client.rpc("nearest_stores", {
            "user_lat": lat,
            "user_lon": lon,
            "radius_meters": radius
        }).execute()
        
        if response.data and len(response.data) > 0:
            return response.data, radius # Returns stores and the radius that worked
    return [], 0
