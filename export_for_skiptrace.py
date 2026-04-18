import json
import csv

INPUT_FILE = "master_leads.json"
OUTPUT_FILE = "skiptrace_export.csv"

DEFAULT_STATE = "SC"
DEFAULT_COUNTY = "Greenville"


def load_records():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("records", [])


def make_excel_safe_text(value):
    value = str(value or "").strip()
    if not value:
        return ""
    return f'="{value}"'


def prepare_skiptrace_rows(records):
    rows = []

    for record in records:
        owner = str(record.get("owner") or "").strip()
        parcel_raw = str(record.get("parcel") or "").strip()
        parcel = make_excel_safe_text(parcel_raw)

        amount_due = str(record.get("amount_due") or "").strip()
        score = record.get("score") or 0
        tax_sale = str(record.get("tax_sale") or "NO").strip()
        probate = str(record.get("probate") or "NO").strip()
        case_number = str(record.get("case_number") or "").strip()

        state = str(record.get("state") or DEFAULT_STATE).strip()
        county = str(record.get("county") or DEFAULT_COUNTY).strip()

        tags = record.get("tags") or []
        if isinstance(tags, list):
            tags_text = ", ".join(tags)
        else:
            tags_text = str(tags)

        if not owner:
            continue

        rows.append({
            "Owner": owner,
            "Parcel": parcel,
            "State": state,
            "County": county,
            "Amount Due": amount_due,
            "Tax Sale": tax_sale,
            "Probate": probate,
            "Case Number": case_number,
            "Score": score,
            "Tags": tags_text
        })

    rows.sort(key=lambda x: float(x["Score"]), reverse=True)
    return rows


def save_csv(rows):
    if not rows:
        print("No rows to export.")
        return

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Owner",
                "Parcel",
                "State",
                "County",
                "Amount Due",
                "Tax Sale",
                "Probate",
                "Case Number",
                "Score",
                "Tags"
            ]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    print("Loading master leads JSON...")
    records = load_records()

    print("Preparing skip trace export...")
    rows = prepare_skiptrace_rows(records)

    print("Saving skip trace CSV...")
    save_csv(rows)

    print("Done.")