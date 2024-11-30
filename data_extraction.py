import pdfplumber
import pandas as pd

# Open the PDF file
pdf_file = "data/chargesheet.pdf"

# List to store extracted data
data = []

# Use pdfplumber to extract text from the PDF
with pdfplumber.open(pdf_file) as pdf:
    for page in pdf.pages:
        # Extract tables from each page
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                # Remove any empty rows or unwanted characters
                if any(cell for cell in row):
                    cleaned_row = [cell.strip() if cell else "" for cell in row]
                    data.append(cleaned_row)

# Convert the extracted data to a DataFrame for easier manipulation
df = pd.DataFrame(data)

# Show the first few rows to verify extraction
print(df.head())

# Save the data to an Excel file or CSV for cleaning
output_file = "extracted_data.xlsx"
df.to_excel(output_file, index=False)
print(f"Data saved to {output_file}")
