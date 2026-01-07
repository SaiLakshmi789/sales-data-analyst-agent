import pandas as pd

class EDAAgent:
    def run(self, df: pd.DataFrame) -> dict:
        sales = df[~df["is_return"]].copy()

        # Basic date range
        date_min = sales["InvoiceDate"].min()
        date_max = sales["InvoiceDate"].max()

        # Country revenue (top 15)
        country_rev = (
            sales.groupby("Country")["line_revenue"]
            .sum()
            .sort_values(ascending=False)
            .head(15)
        )

        # Basic distributions
        unitprice_desc = sales["UnitPrice"].describe().to_dict()
        quantity_desc = sales["Quantity"].describe().to_dict()

        out = {
            "date_min": str(date_min),
            "date_max": str(date_max),
            "num_countries": int(sales["Country"].nunique()),
            "top_countries_by_revenue": country_rev.to_dict(),
            "unitprice_desc": unitprice_desc,
            "quantity_desc": quantity_desc,
        }
        return out
