import os
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
                result = match_brand_to_generic(supabase, search_query)
                
                # Check if the result returned a diagnostic / error dictionary
                if isinstance(result, dict) and "error" in result:
                    st.warning("Query Executed, but No Match / Diagnostic Info:")
                    st.markdown(f"**Attempted Table:** `{result.get('table')}`")
                    st.markdown(f"**Query Filter Applied:** `{result.get('filter') or result.get('filter_tried')}`")
                    st.markdown(f"**Detailed Reason / Error:** `{result.get('error')}`")
                    if "response_data" in result:
                        st.write(f"Raw Supabase Response Data: `{result.get('response_data')}`")
                
                elif result and isinstance(result, list):
                    st.success("Generic Substitute Found!")
                    item = result[0]
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
                    st.warning(f"No match found for query: '{search_query}'.")
                    
            except Exception as err:
                st.error(f"Search execution crashed.")
                st.code(str(err), language="text")

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

# --- YOUR EXISTING APP CODE ABOVE ---
# (Search inputs, results display, maps, etc.)


# --- ADD THE AUTO-POPULATE AGENT BLOCK HERE AT THE BOTTOM ---
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

class MedicineRecord(BaseModel):
    brand_name: str = Field(description="Commercial brand name of the medicine, e.g., Augmentin 625 Duo, Pan 40")
    generic_name: str = Field(description="Active pharmaceutical ingredient or salt")
    estimated_price_brand: float = Field(description="Approximate retail brand price in INR")

class MedicineBatch(BaseModel):
    medicines: list[MedicineRecord]

with st.expander("🤖 Admin Agent: Auto-Populate Database"):
    st.write("Clicking this button will instruct the Gemini agent to generate a fresh batch of Indian pharmaceutical records and write them straight to your Supabase `medicines` table.")
    
    if st.button("Run Auto-Ingestion Agent"):
        with st.spinner("Agent is generating and inserting medicine records..."):
            try:
                # Initialize Gemini client securely using your environment secrets or keys
                client = genai.Client(api_key=st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY")))
                
                prompt = """
                Generate a JSON list of 30 widely used Indian prescription and over-the-counter medicines 
                across antibiotics, PPIs, diabetes, pain management, and supplements (e.g., Augmentin 625 Duo, Pan 40, Glycomet-GP 1, Shelcal 500, Azithral 500). 
                Provide accurate brand names, active generic salts, and estimated brand prices in INR.
                """

                response = client.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=MedicineBatch,
                        temperature=0.2,
                    ),
                )

                data = json.loads(response.text)
                records = data.get("medicines", [])
                
                success_count = 0
                for item in records:
                    # Insert directly using your active supabase client
                    supabase.table("medicines").upsert({
                        "brand_name": item["brand_name"],
                        "generic_name": item["generic_name"],
                        "estimated_price_brand": item["estimated_price_brand"]
                    }, on_conflict="brand_name").execute()
                    success_count += 1
                
                st.success(f"Successfully populated {success_count} medicine records into Supabase via the agent!")
                st.balloons()
                
            except Exception as e:
                st.error(f"Agent ingestion failed: {e}")
