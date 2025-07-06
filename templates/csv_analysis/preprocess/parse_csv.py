import pandas as pd
import sys

def parse_csv(csv_file):
    df = pd.read_csv(csv_file)
    total_sales = df['sales'].sum()
    avg_price = df['price'].mean()
    top_product = df.groupby('product')['sales'].sum().idxmax()
    summary = (
        f"Total Sales: ${total_sales:,.2f}\n"
        f"Average Price: ${avg_price:,.2f}\n"
        f"Top Product: {top_product}"
    )
    return summary

if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "sales.csv"
    print(parse_csv(csv_file))
