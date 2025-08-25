import pandas as pd

# קובץ רשמי של נאסד"ק עם כל הסימבולים
url = "https://ftp.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"
df = pd.read_csv(url, sep="|")

# רק מניות אמיתיות (לא טסטים/מכשירים פיננסיים)
df = df[df["Test Issue"] == "N"]

tickers = df["NASDAQ Symbol"].dropna().unique().tolist()

# שמירה ל-csv
with open("tickers.csv", "w") as f:
    for t in tickers:
        f.write(t + "\n")

print(f"נשמרו {len(tickers)} מניות ל-tickers.csv")
