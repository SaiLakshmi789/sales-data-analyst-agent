import pandas as pd

class KPIAgent:
    def run(self, df: pd.DataFrame) -> dict:
        sales = df[~df["is_return"]].copy()
        returns = df[df["is_return"]].copy()

        # Revenue
        gross_revenue = float(sales["line_revenue"].sum())
        return_revenue = float(abs(returns["line_revenue"].sum()))
        net_revenue = gross_revenue - return_revenue

        # Orders & units (sales only)
        orders = int(sales["InvoiceNo"].nunique())
        units_sold = float(sales["Quantity"].sum())

        # Basket metrics
        aov = float(net_revenue / orders) if orders else 0.0
        asp = float(gross_revenue / units_sold) if units_sold else 0.0

        # Monthly KPIs
        sales["month"] = sales["InvoiceDate"].dt.to_period("M").astype(str)
        monthly = (
            sales.groupby("month")
            .agg(
                revenue=("line_revenue", "sum"),
                orders=("InvoiceNo", "nunique"),
                units=("Quantity", "sum"),
            )
            .reset_index()
            .sort_values("month")
        )
        monthly["mom_revenue_growth_pct"] = monthly["revenue"].pct_change() * 100
        monthly["mom_orders_growth_pct"] = monthly["orders"].pct_change() * 100

        # Product KPIs
        product = (
            sales.groupby(["StockCode", "Description"])
            .agg(
                revenue=("line_revenue", "sum"),
                units=("Quantity", "sum"),
                orders=("InvoiceNo", "nunique"),
            )
            .reset_index()
            .sort_values("revenue", ascending=False)
        )

        # Customer KPIs (CustomerID may be missing)
        cust = sales.dropna(subset=["CustomerID"]).copy()
        active_customers = int(cust["CustomerID"].nunique())

        if active_customers:
            inv_per_customer = cust.groupby("CustomerID")["InvoiceNo"].nunique()
            repeat_customer_rate = float((inv_per_customer >= 2).mean())
            revenue_per_customer = float(net_revenue / active_customers)
        else:
            repeat_customer_rate = 0.0
            revenue_per_customer = 0.0

        return {
            "gross_revenue": gross_revenue,
            "return_revenue": return_revenue,
            "net_revenue": net_revenue,
            "orders": orders,
            "units_sold": units_sold,
            "aov": aov,
            "asp": asp,
            "active_customers": active_customers,
            "repeat_customer_rate": repeat_customer_rate,
            "revenue_per_customer": revenue_per_customer,
            "monthly_df": monthly,
            "product_df": product,
        }
