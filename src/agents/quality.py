import pandas as pd

class DataQualityAgent:
    def run(self, df: pd.DataFrame, cfg) -> tuple[pd.DataFrame, dict]:
        df = df.copy()

        # Normalize string fields
        df["InvoiceNo"] = df["InvoiceNo"].astype(str)
        df["StockCode"] = df["StockCode"].astype(str)
        df["Description"] = df["Description"].astype(str).str.strip()
        df["Country"] = df["Country"].astype(str).str.strip()

        # CustomerID can be missing
        df["CustomerID"] = df["CustomerID"].astype("string")

        # Type casting
        df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
        df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")

        report = {
            "rows_initial": int(len(df)),
            "null_invoice_date": int(df["InvoiceDate"].isna().sum()),
            "null_quantity": int(df["Quantity"].isna().sum()),
            "null_unitprice": int(df["UnitPrice"].isna().sum()),
            "null_customerid": int(df["CustomerID"].isna().sum()),
        }

        # Drop rows missing core fields
        if cfg.require_core_fields:
            df = df.dropna(
                subset=["InvoiceNo", "StockCode", "InvoiceDate", "Quantity", "UnitPrice"]
            )

        # Identify returns / cancellations
        canceled_invoice = df["InvoiceNo"].str.upper().str.startswith("C")
        negative_values = (df["Quantity"] < 0) | (df["UnitPrice"] < 0)
        df["is_return"] = canceled_invoice | negative_values

        # Line-level revenue
        df["line_revenue"] = df["Quantity"] * df["UnitPrice"]

        # Remove noise rows
        if cfg.drop_zero_quantity:
            df = df[df["Quantity"] != 0]
        if cfg.drop_zero_price:
            df = df[df["UnitPrice"] != 0]

        report.update({
            "rows_after_clean": int(len(df)),
            "return_rows": int(df["is_return"].sum()),
            "sales_rows": int((~df["is_return"]).sum()),
            "canceled_invoices": int(
                df[df["InvoiceNo"].str.upper().str.startswith("C")]["InvoiceNo"].nunique()
            ),
        })

        return df, report
