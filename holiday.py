import json
import pandas as pd

hol = []
df = pd.read_csv("syukujitsu.csv", encoding="SHIFT-JIS")

for a in df.index.values:
    b = str(df.at[a, "国民の祝日・休日月日"])
    b = b.replace("/", "-")
    b = "{}-{:02d}-{:02d}".format(b.split("-")[0], int(b.split("-")[1]), int(b.split("-")[2]))
    if int(b.split("-")[0]) < 2016:
        continue
    hol.append(b)

with open ("syukujitsu.json", "w") as f:
    json.dump (hol, fp=f, indent=2, ensure_ascii=False)

