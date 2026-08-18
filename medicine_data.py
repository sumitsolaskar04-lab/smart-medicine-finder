data = [
    {
        "medicine_name": "P-500 Tablet",
        "price": {
            "value": 11.43,
            "currency": "INR",
            "symbol": "₹"
        },
        "mrp": {
            "value": 14.65,
            "currency": "INR",
            "symbol": "₹"
        },
        "manufacturer": "APEX LABORATORIES PRIVATE LIMITED",
        "dosage": "TABLET",
        "salt_content": "Paracetamol / Acetaminophen(500.0 Mg)",
        "availability": "April 2029",
        "uses": "To treat fever and pain"
    }
]

print("Medicine Name: ", data[0]["medicine_name"])

x = data[0]["price"]["value"]
y = data[0]["mrp"]["value"]

discount = ((y - x) / y) * 100

print("\nMedicine Price: ", x)
print("MRP: ", y)
print(f"Discount Applied: {discount:.2f}%")

print("Manufacturer: ", data[0]["manufacturer"])
print("Use Case: ", data[0]["uses"])

