import json
import random

# Load the JSON file
with open("employee_info_data.json", "r") as f:
    data = json.load(f)

# Keep track of used numbers to ensure uniqueness
used_numbers = set()

def unique_3digit():
    while True:
        n = random.randint(100, 999)  # random 3-digit number
        if n not in used_numbers:
            used_numbers.add(n)
            return n

# Iterate over all objects and replace the phone
for obj in data:
    if "fields" in obj and obj["fields"].get("phone") == "01911000":
        obj["fields"]["phone"] = f'01911000{unique_3digit()}'

# Save the updated JSON back
with open("employee_info_data_1.json", "w") as f:
    json.dump(data, f, indent=2)

print("Phone numbers updated successfully!")
