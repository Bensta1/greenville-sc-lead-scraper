import csv
import json
from datetime import datetime, timezone


def load_csv(filename):
    try:
        with open(filename, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        print(f"{filename} not found")
        return []


def parse_amount(val):
    try:
        return float(val.replace("$", "").replace(",", "").strip())
    except:
        return 0.0


def score_lead(record):
    score = 0
    tags = []

    amount = parse_amount(record.get("Amount", ""))

    # Tax sale = base signal
    if record.get("Item"):
        score += 30
        tags.append("Tax Sale")

    # High amount
    if amount >= 5000:
        score += 10
        tags.append("High Tax Amount")

    # Business owner
    owner = record.get("Owner", "").lower()
    if any(x in owner for x in ["llc", "inc", "corp"]):
        score += 10
        tags.append("Business Owner")

    return score, tags


def build_master():
    tax_leads = load_csv("leads.csv")
    probate_leads = load_csv("probate_leads.csv")

    records = []
    run_timestamp = datetime.now(timezone.utc).isoformat()

    # --- TAX LEADS ---
    for row in tax_leads:
        score, tags = score_lead(row)

        records.append({
            "owner": row.get("Owner", ""),
            "parcel": row.get("Parcel", ""),
            "amount_due": row.get("Amount", ""),
            "amount_due_num": parse_amount(row.get("Amount", "")),
            "case_number": row.get("Item", ""),
            "tax_sale": "YES",
            "probate": "NO",
            "score": score,
            "tags": tags,
            "generated_at": row.get("generated_at") or run_timestamp
        })

    # --- PROBATE LEADS ---
    for row in probate_leads:
        records.append({
            "owner": row.get("Owner", ""),
            "parcel": row.get("Parcel", ""),
            "amount_due": "",
            "amount_due_num": 0,
            "case_number": "",
            "tax_sale": "NO",
            "probate": "YES",
            "score": 40,
            "tags": ["Probate"],
            "generated_at": run_timestamp
        })

    # --- SUMMARY ---
    total_leads = len(records)
    tax_count = sum(1 for r in records if r["tax_sale"] == "YES")
    probate_count = sum(1 for r in records if r["probate"] == "YES")
    stacked_count = sum(1 for r in records if r["tax_sale"] == "YES" and r["probate"] == "YES")
    high_score_count = sum(1 for r in records if r["score"] >= 70)

    output = {
        "generated_at": run_timestamp,
        "total_leads": total_leads,
        "tax_sale_leads": tax_count,
        "probate_leads": probate_count,
        "stacked_leads": stacked_count,
        "high_score_leads": high_score_count,
        "records": records
    }

    with open("master_leads.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("master_leads.json updated")


if __name__ == "__main__":
    build_master()
