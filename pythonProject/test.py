from core.parsers import parse_jma

jma_file = "data/bst_all.txt"

df = parse_jma(jma_file)

print(f"{len(df)}")
print(df.head())