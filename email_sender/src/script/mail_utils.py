from pathlib import Path
import zipfile
import glob
from datetime import datetime, timedelta
import pandas as pd

### ==== Helper function for mail services ====

ROOT_DIR = Path(__file__).resolve().parents[2]
REPORT_DIR = Path(__file__).resolve().parents[3]
Report_folder = REPORT_DIR / "etl_structured" / "data" / "live_reports"

def get_latest_file(report_type=None, provider=None, specific_file=None):

    #case 1
    if specific_file:
        path = Report_folder / specific_file

        if not path.exists():
            raise FileNotFoundError(f"Specific file not found: {path}")

        if path.exists():
            # SAFER metadata extraction
            filename = path.name
            parts = filename.replace(".csv", "").split("_")

            try:
                report_name = parts[0]
                provider_name = parts[-1]
            except IndexError:
                raise ValueError(f"Filename format invalid: {filename}")

            return path, report_name, provider_name

    #case 2
    if not report_type or not provider:
        raise ValueError("report_type and provider are required if specific_file is not provided")

    pattern = f"{report_type}_billing_*_lyraindia_{provider.lower()}.csv"
    files = list(Report_folder.glob(pattern))

    if not files:
        raise FileNotFoundError(
            f"No {report_type} report found for provider {provider}"
        )
    files.sort(key=lambda p: p.stat().st_mtime)

    return files[-1], report_type, provider.lower()

#zip file when it exceeds 12MB
def zip_file(file_path):
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot zip missing file: {file_path}")

    zipped_path = file_path.with_suffix(file_path.suffix + ".zip")

    with zipfile.ZipFile(zipped_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(file_path, arcname=file_path.name)

    return zipped_path

def summary(file_path):
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot summarise missing file: {file_path}")

    df = pd.read_csv(file_path, usecols=['STATUS','NETWORK'],
                     low_memory=False)
    df['STATUS'] = df['STATUS'].str.upper().str.strip()
    df['NETWORK'] = df['NETWORK'].str.upper().str.strip()
    grouped = df.groupby('NETWORK')
    summary = grouped["STATUS"].agg(
        Total_txn="count",
        Success_txn=lambda x: (x == "SUCCESS").sum()
    )
    summary["SR_Percent"] = (
    (summary["Success_txn"] / summary["Total_txn"]) * 100).round(2)

    html_table = summary.reset_index().to_html(index=False)

    return html_table


