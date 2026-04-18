import csv
import json
import re

TAX_FILE = "leads.csv"
PROBATE_FILE = "probate_leads.csv"
OUTPUT_CSV = "master_leads.csv"
OUTPUT_JSON = "master_leads.json"


def normalize_name(name):
    if not name:
        return ""

    name = name.upper().strip()
    name = re.sub(r"[^A-Z0-9\s]", "", name)
    name = re.sub(r"\s+", " ", name)

    noise_words = {
        "LLC", "INC", "CORP", "CORPORATION", "COMPANY", "CO",
        "LTD", "LP", "LLP", "ESTATE", "ETAL", "ET", "AL"
    }

    parts = [part for part in name.split() if part not in noise_words]
    return " ".join(parts).strip()


def safe_float_amount(amount_text):
    if not amount_text:
        return 0.0

    cleaned = amount_text.replace("$", "").replace(",", "").strip()

    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def load_tax_leads():
    leads = {}

    with open(TAX_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            owner = row.get("Owner", "").strip()
            parcel = row.get("Parcel", "").strip()
            amount_text = row.get("Amount", "").strip()

            if not owner:
                continue

            norm = normalize_name(owner)
            amount_num = safe_float_amount(amount_text)

            if norm not in leads:
                leads[norm] = {
                    "owner": owner,
                    "normalized_owner": norm,
                    "tax_sale": "YES",
                    "probate": "NO",
                    "parcel": parcel,
                    "amount_due": amount_text,
                    "amount_due_num": amount_num,
                    "case_number": "",
                    "probate_party_type": "",
                    "score": 0,
                    "tags": [],
                    "source_count": 1
                }
            else:
                leads[norm]["tax_sale"] = "YES"
                if amount_num > leads[norm]["amount_due_num"]:
                    leads[norm]["amount_due"] = amount_text
                    leads[norm]["amount_due_num"] = amount_num
                    leads[norm]["parcel"] = parcel

    return leads


def merge_probate(leads):
    with open(PROBATE_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            name = row.get("name", "").strip()
            case_number = row.get("case_number", "").strip()
            party_type = row.get("party_type", "").strip()

            if not name:
                continue

            norm = normalize_name(name)

            if norm in leads:
                if leads[norm]["probate"] != "YES":
                    leads[norm]["source_count"] += 1
                leads[norm]["probate"] = "YES"
                leads[norm]["case_number"] = case_number
                leads[norm]["probate_party_type"] = party_type
            else:
                leads[norm] = {
                    "owner": name,
                    "normalized_owner": norm,
                    "tax_sale": "NO",
                    "probate": "YES",
                    "parcel": "",
                    "amount_due": "",
                    "amount_due_num": 0.0,
                    "case_number": case_number,
                    "probate_party_type": party_type,
                    "score": 0,
                    "tags": [],
                    "source_count": 1
                }

    return leads


def score_leads(leads):
    for _, lead in leads.items():
        score = 0
        tags = []

        if lead["tax_sale"] == "YES":
            score += 30
            tags.append("Tax Sale")

        if lead["probate"] == "YES":
            score += 30
            tags.append("Probate")

        if lead["tax_sale"] == "YES" and lead["probate"] == "YES":
            score += 25
            tags.append("Stacked Distress")

        amount = lead["amount_due_num"]
        if amount >= 5000:
            score += 15
            tags.append("High Tax Amount")
        elif amount >= 3000:
            score += 10
            tags.append("Medium Tax Amount")
        elif amount >= 1500:
            score += 5
            tags.append("Some Tax Amount")

        owner_upper = lead["owner"].upper()
        business_words = ["LLC", "INC", "CORP", "CORPORATION", "COMPANY", "CO", "LTD", "LP", "LLP"]
        if any(word in owner_upper for word in business_words):
            score += 5
            tags.append("Business Owner")

        lead["score"] = score
        lead["tags"] = tags

    return leads


def prepare_rows(leads):
    rows = []

    for lead in leads.values():
        row = {
            "owner": lead["owner"],
            "normalized_owner": lead["normalized_owner"],
            "tax_sale": lead["tax_sale"],
            "probate": lead["probate"],
            "parcel": lead["parcel"],
            "amount_due": lead["amount_due"],
            "amount_due_num": lead["amount_due_num"],
            "case_number": lead["case_number"],
            "probate_party_type": lead["probate_party_type"],
            "score": lead["score"],
            "tags": lead["tags"],
            "source_count": lead["source_count"]
        }
        rows.append(row)

    rows.sort(key=lambda x: x["score"], reverse=True)
    return rows


def save_csv(rows):
    filename = OUTPUT_CSV

    while True:
        try:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "owner",
                        "normalized_owner",
                        "tax_sale",
                        "probate",
                        "parcel",
                        "amount_due",
                        "amount_due_num",
                        "case_number",
                        "probate_party_type",
                        "score",
                        "tags",
                        "source_count"
                    ]
                )
                writer.writeheader()

                for row in rows:
                    csv_row = row.copy()
                    csv_row["tags"] = ", ".join(csv_row["tags"])
                    writer.writerow(csv_row)

            print(f"Saved CSV to {filename}")
            break
        except PermissionError:
            if filename == OUTPUT_CSV:
                filename = "master_leads_1.csv"
            else:
                match = re.search(r"master_leads_(\d+)\.csv", filename)
                next_num = int(match.group(1)) + 1 if match else 1
                filename = f"master_leads_{next_num}.csv"


def save_json(rows):
    payload = {
        "total_leads": len(rows),
        "stacked_leads": sum(1 for row in rows if row["tax_sale"] == "YES" and row["probate"] == "YES"),
        "tax_sale_leads": sum(1 for row in rows if row["tax_sale"] == "YES"),
        "probate_leads": sum(1 for row in rows if row["probate"] == "YES"),
        "high_score_leads": sum(1 for row in rows if row["score"] >= 70),
        "records": rows
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Saved JSON to {OUTPUT_JSON}")


if __name__ == "__main__":
    print("Loading tax leads...")
    leads = load_tax_leads()

    print("Merging probate leads...")
    leads = merge_probate(leads)

    print("Scoring leads...")
    leads = score_leads(leads)

    print("Preparing rows...")
    rows = prepare_rows(leads)

    print("Saving CSV...")
    save_csv(rows)

    print("Saving JSON...")
    save_json(rows)

    print("Done.")