import matplotlib.pyplot as plt

class VizAgent:
    def plot_monthly_revenue(self, monthly_df, charts_dir):
        fig = plt.figure()
        plt.plot(monthly_df["month"], monthly_df["revenue"])
        plt.xticks(rotation=45, ha="right")
        plt.title("Monthly Revenue (Sales Only)")
        plt.xlabel("Month")
        plt.ylabel("Revenue")
        out = charts_dir / "monthly_revenue.png"
        fig.tight_layout()
        fig.savefig(out, dpi=160)
        plt.close(fig)
        return str(out)

    def plot_monthly_orders(self, monthly_df, charts_dir):
        fig = plt.figure()
        plt.plot(monthly_df["month"], monthly_df["orders"])
        plt.xticks(rotation=45, ha="right")
        plt.title("Monthly Orders (Sales Only)")
        plt.xlabel("Month")
        plt.ylabel("Orders")
        out = charts_dir / "monthly_orders.png"
        fig.tight_layout()
        fig.savefig(out, dpi=160)
        plt.close(fig)
        return str(out)

    def plot_top_products(self, product_df, charts_dir, n=10):
        top = product_df.head(n).copy()
        fig = plt.figure()
        plt.barh(top["Description"].astype(str), top["revenue"])
        plt.title(f"Top {n} Products by Revenue")
        plt.xlabel("Revenue")
        plt.gca().invert_yaxis()
        out = charts_dir / "top_products.png"
        fig.tight_layout()
        fig.savefig(out, dpi=160)
        plt.close(fig)
        return str(out)
