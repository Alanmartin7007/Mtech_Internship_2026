import sqlite3

# Connect to SQLite database (creates it if it doesn't exist)
connection = sqlite3.connect("addressbook.db")

# Create a cursor object
cursor = connection.cursor()

# Create AddressBook table
create_table_query = """
CREATE TABLE IF NOT EXISTS AddressBook (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Phone TEXT NOT NULL,
    Email TEXT,
    Address TEXT
);
"""

cursor.execute(create_table_query)

# Sample data
address_data = [
    ("Alan Martin", "9876543210", "alan@gmail.com", "Kochi"),
    ("John Doe", "9123456780", "john@gmail.com", "Bangalore"),
    ("Jane Smith", "9988776655", "jane@gmail.com", "Chennai"),
    ("Rahul Kumar", "9012345678", "rahul@gmail.com", "Hyderabad"),
    ("Anjali Nair", "9876501234", "anjali@gmail.com", "Trivandrum")
]

# Insert data
insert_query = """
INSERT INTO AddressBook (Name, Phone, Email, Address)
VALUES (?, ?, ?, ?)
"""

cursor.executemany(insert_query, address_data)

# Save changes
connection.commit()

# Fetch all records
cursor.execute("SELECT * FROM AddressBook")
records = cursor.fetchall()

# Display records
print("Address Book Records")
print("-" * 70)
print(f"{'ID':<5}{'Name':<20}{'Phone':<15}{'Email':<25}{'Address'}")
print("-" * 70)

for record in records:
    print(f"{record[0]:<5}{record[1]:<20}{record[2]:<15}{record[3]:<25}{record[4]}")

# Close connection
connection.close()