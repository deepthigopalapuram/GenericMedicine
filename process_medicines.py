import pdfplumber
import pandas as pd

# Open the downloaded Product List PDF
pdf_path = r"C:\Users\deepd\Downloads\Product List.pdf"
all_rows = []

print("Extracting data from PDF...")
with pdfplumber.open(pdf_path) as pdf:
  for page_num, page in enumerate(pdf.pages):
    table = page.extract_table()
    if table:
      # Skip header row if repeated on subsequent pages
      for row in table:
        # Basic validation to ensure it's a data row (e.g. starts with a digit)
        if row and str(row[0]).strip().isdigit():
          all_rows.append(row)

# Convert to DataFrame (adjust column indices based on exact PDF structure)
# Expected structure sample mapping:
# [Drug Code, Generic Name, Unit Size, MRP, Brand Name (if applicable)]
df = pd.DataFrame(all_rows)

# Clean and rename columns to match your schema:
# Columns: Drug Code, Brand Name, Brand Price (in Rs.), Generic Name, Unit Size, MRP (in Rs.)
# (Assuming columns map to: 0: Code, 1: Generic, 2: Unit, 3: MRP)
df = df.iloc[:, :4]  # Adjust as necessary
df.columns = ["Drug Code", "Generic Name", "Unit Size", "MRP (in Rs.)"]

# Clean numeric values and filter out MRP <= 0 or empty values
df["MRP (in Rs.)"] = pd.to_numeric(
    df["MRP (in Rs.)"].astype(str).str.replace(r"[^\d.]", "", regex=True),
    errors="coerce",
)
df = df[df["MRP (in Rs.)"] > 0]

# Add placeholder or mapped columns for Brand Name and Brand Price if separate
df["Brand Name"] = ""  # Map your brand column here if extracted
df["Brand Price (in Rs.)"] = 0.00  # Map your brand price column here if extracted

# Reorder columns to match your preferred format
df = df[
    [
        "Drug Code",
        "Brand Name",
        "Brand Price (in Rs.)",
        "Generic Name",
        "Unit Size",
        "MRP (in Rs.)",
    ]
]

# Export to CSV
output_file = "all_medicines_filtered.csv"
df.to_csv(output_file, index=False)
print(
    f"Successfully exported {len(df)} items with price > 0 to {output_file}!"
)
