import pandas as pd

EXPECTED_COLUMNS = {
    "InvoiceNo", "StockCode", "Description", "Quantity",
    "InvoiceDate", "UnitPrice", "CustomerID", "Country"
}

class IngestionAgent:
    def run(self, dataset_path: str) -> tuple[pd.DataFrame, dict]:
        path_lower = dataset_path.lower()

        if path_lower.endswith(".xlsx") or path_lower.endswith(".xls"):
            df = pd.read_excel(dataset_path, engine="openpyxl")
        elif path_lower.endswith(".csv"):
            df = pd.read_csv(dataset_path, encoding="ISO-8859-1")
        else:
            raise ValueError("Unsupported file format. Use .xlsx, .xls, or .csv")

        df.columns = [c.strip() for c in df.columns]

        missing = EXPECTED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(
                "Missing expected columns: "
                f"{sorted(missing)}\n\n"
                f"Found columns: {list(df.columns)}"
            )

        schema = {c: str(df[c].dtype) for c in df.columns}
        meta = {
            "rows": int(len(df)),
            "cols": int(df.shape[1]),
            "schema": schema,
            "dataset_path": dataset_path,
        }
        return df, meta
