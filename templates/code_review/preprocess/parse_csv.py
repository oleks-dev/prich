def read_file(filename):
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
