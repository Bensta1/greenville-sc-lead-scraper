import csv
import json
import os
from datetime import datetime, timezone


MASTER_FILE = "master_leads.json"


def load_csv(filename):
    try:
        with open(filename, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        print(f"{filename} not found")
        return []


def load_existing_master(filename=MASTER_FILE):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"{filename} is invalid JSON, starting fresh")
        return {}


def parse_amount(val):
    try:
        return float(str(val).replace("$", "").replace(",", "").strip())
    except Exception:
        return 0.0


def score_lead(record):
    score = 0
    tags = []

    amount = parse_amount(record.get("Amount", ""))

    if record.get("Item"):
        score += 30
        tags.append("Tax Sale")

    if amount >= 5000:
        score += 10
        tags.append("High Tax Amount")

    owner = record.get("Owner", "").lower()
    if any(x in owner for x in ["llc", "inc", "corp"]):
        score += 10
        tags.append("Business Owner")

    return score, tags


def make_tax_key(row):
    return f"TAX|{row.get('Parcel', '').strip()}"


def make_probate_key(row):
    owner = row.get("Owner", "").strip()
    parcel = row.get("Parcel", "").strip()
    if parcel:
        return f"PROBATE|{parcel}"
    return f"PROBATE|OWNER|{owner}"


def build_existing_timestamp_lookup(existing_records):
    lookup = {}
    for record in existing_records:
        tax_sale = record.get("tax_sale", "NO")
        probate = record.get("probate", "NO")
        parcel = str(record.get("parcel", "")).strip()
        owner = str(record.get("owner", "")).strip()
        generated_at = record.get("generated_at")

        if tax_sale == "YES":
            key = f"TAX|{parcel}"
            if generated_at:
                lookup[key] = generated_at

        elif probate == "YES":
            if parcel:
                key = f"PROBATE|{parcel}"
            else:
                key = f"PROBATE|OWNER|{owner}"
            if generated_at:
                lookup[key] = generated_at

    return lookup


def build_master():
    tax_leads = load_csv("leads.csv")
    probate_leads = load_csv("probate_leads.csv")

    existing_master = load_existing_master()
    existing_records = existing_master.get("records", [])
    timestamp_lookup = build_existing_timestamp_lookup(existing_records)

    records = []
    run_timestamp = datetime.now(timezone.utc).isoformat()

    # --- TAX LEADS ---
    for row in tax_leads:
        score, tags = score_lead(row)
        record_key = make_tax_key(row)

        generated_at = (
            timestamp_lookup.get(record_key)
            or row.get("generated_at")
            or run_timestamp
        )

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
            "generated_at": generated_at
        })

    # --- PROBATE LEADS ---
    for row in probate_leads:
        record_key = make_probate_key(row)
        generated_at = timestamp_lookup.get(record_key) or run_timestamp

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
            "generated_at": generated_at
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

    with open(MASTER_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("master_leads.json updated")


if __name__ == "__main__":
    build_master()
