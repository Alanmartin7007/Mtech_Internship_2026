import pandas as pd

df = pd.read_csv(r"D:\MTECH\Internship\Sales_Data\salesdata\train.csv")

print(df.head())

df = df.drop_duplicates()

df = df.dropna()

df['Order Date'] = pd.to_datetime(
    df['Order Date'],
    format="%d/%m/%Y",
    errors="coerce"
)

# Save cleaned data
df.to_csv("cleaned_sales.csv", index=False)

print("Data cleaned successfully.")
print(df.info())