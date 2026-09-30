import streamlit as st
from supabase import create_client
from agents.ocr_agent import extract_text_from_image
from agents.matching_agent import match_brand_to_generic
from agents.locator_agent import find_nearest_stores_safely

# Securely load Supabase credentials
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("WhatToBuy: Generic Medicine Finder")
st.write("Search brand names or upload prescriptions to safely find low-cost generic equivalents and nearby stores.")

# --- Tab 1: Manual Search & Salt Matcher ---
tab1, tab2 = st.tabs(["Manual Brand Search", "Upload Prescription Image"])

with tab1:
    search_query = st.text_input("Enter Brand Name (e.g., Augmentin, Pan 40):")
    if search_query:
        with st.spinner("Matching salt safely..."):
            try:
                match = match_brand_to_generic(supabase, search_query)
                if match:
                    st.success("Generic Substitute Found!")
                    # Handle if match returns a list of items or a single dictionary
                    item = match[0] if isinstance(match, list) and len(match) > 0 else match
                    
                    if isinstance(item, dict):
                        st.write(f"**Brand Name:** {item.get('brand_name')}")
                        st.write(f"**Generic Active Salt:** {item.get('generic_name')}")
                        st.write(f"**Estimated Brand Price:** ₹{item.get('estimated_price_brand')}")
                        st.write(f"**Estimated Generic Price:** ₹{item.get('estimated_price_generic')}")
                        savings = item.get('estimated_price_brand', 0) - item.get('estimated_price_generic', 0)
                        st.info(f"Estimated Savings: ~₹{savings} per strip!")
                    else:
                        st.warning("Match returned an unexpected format.")
                else:
                    st.warning(f"No match found for query: '{search_query}'. Please verify the spelling or check database records.")
            except Exception as err:
                st.error(f"Search failed for input '{search_query}'. Exact reason: {err}")

with tab2:
    uploaded_file = st.file_uploader("Upload prescription image...", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        st.image(uploaded_file, caption="Uploaded Prescription", use_container_width=True)
        
        if st.button("Run OCR Reader Agent"):
            with st.spinner("Extracting tokens with confidence guardrails..."):
                tokens = extract_text_from_image(bytes_data)
                st.write("Extracted Text Tokens:", tokens)

# --- Geospatial Store Locator Section ---
st.divider()
st.subheader("Find Nearest Affordable Generic Store")
col1, col2 = st.columns(2)
with col1:
    user_lat = st.number_input("Your Latitude", value=17.3850) # Default Hyderabad/Secunderabad region
with col2:
    user_lon = st.number_input("Your Longitude", value=78.4867)

if st.button("Locate Nearest Stores"):
    with st.spinner("Calculating via PostGIS spatial router..."):
        try:
            stores, found_radius = find_nearest_stores_safely(supabase, user_lat, user_lon)
            if stores:
                st.success(f"Found {len(stores)} store(s) within {found_radius/1000} km radius!")
                for store in stores:
                    st.write(f"🏪 **{store['store_name']}** — {store['address']} (Distance: {round(store['distance_meters']/1000, 2)} km)")
            else:
                st.warning("No generic stores found within the maximum radius. Please check back later as our database updates.")
        except Exception as locator_err:
            st.error(f"Store lookup failed. Exact reason: {locator_err}")

# --- ISOLATED DEBUG BLOCK ---
with st.expander("🛠️ Developer Sandbox & Raw Data Inspector"):
    st.write("This block runs completely separate from the main search engine.")
    if st.button("Test Raw Supabase Connection"):
        try:
            raw_res = supabase.table("medicines").select("*").limit(3).execute()
            st.success("Connection successful!")
            st.json(raw_res.data)
        except Exception as err:
            st.error(f"Connection error: {err}")
