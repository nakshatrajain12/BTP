import csv

# We are stubbing a seed csv file for fallback
data = [
    ["scheme_name", "ministry", "funding_type", "max_funding_amount"],
    ["Startup India Seed Fund", "DPIIT", "grant", "5000000"]
]

with open("schemes_seed.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(data)
