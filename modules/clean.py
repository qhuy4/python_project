import pandas as pd
df = pd.read_csv("data/processed.cleveland.data", header=None, na_values='?')
df.dropna(inplace=True)
df = df.astype(float)