import csv
import json
import os
import re

INPUT_FILE = "1.csv"
MASTER_JSON = "master_leads.json"

OUTPUT_ALL = "Cleaned_ALL.csv"
OUTPUT_WIRELESS = "Jarvis_Ready_Wireless.csv"
OUTPUT_RESKIP = "No_Wireless_Reskip.csv"

FINAL_HEADERS = [
    "associated_property_address_full",
    "first_name",
    "last_name",
    "middle_initial",
    "primary_mailing_address",
    "primary_mailing_city",
    "primary_mailing_state",
    "primary_mailing_zip",
    "contact_flags",
    "email_address_1",
    "email_address_2",
    "email_address_3",
    "PHONE",
    "PHONE 2",
    "PHONE 3",
    "ADDRESS",
    "CITY",
    "STATE",
    "POSTAL CODE",
    "COUNTY",
    "APN",
    "SIZE",
    "SCORE",
    "TAGS",
    "TAX SALE",
    "PROBATE",
    "CASE NUMBER",
    "AMOUNT DUE",
    "SOURCE COUNT",
    "STACKED DISTRESS"
]


def clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def excel_safe_text(value):
    value = clean_text(value)
    if not value:
        return ""
    return f'="{value}"'


def normalize_text(value):
    value = clean_text(value).upper()
    value = re.sub(r"[^A-Z0-9\s]", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_apn(value):
    value = clean_text(value).upper()
    value = re.sub(r"[^A-Z0-9]", "", value)
    return value


def normalize_owner_name(first_name="", last_name="", full_name=""):
    if full_name:
        return normalize_text(full_name)

    combined = f"{clean_text(first_name)} {clean_text(last_name)}".strip()
    return normalize_text(combined)


def is_wireless(phone_type):
    pt = clean_text(phone_type).lower()
    return "wireless" in pt or "mobile" in pt or "cell" in pt


def get_wireless_numbers(row):
    numbers = []
    seen = set()

    phone_pairs = [
        ("phone_1", "phone_1_type"),
        ("phone_2", "phone_2_type"),
        ("phone_3", "phone_3_type"),
    ]

    for phone_col, type_col in phone_pairs:
        phone = clean_text(row.get(phone_col, ""))
        phone_type = clean_text(row.get(type_col, ""))

        if not phone:
            continue

        if is_wireless(phone_type):
            if phone not in seen:
                seen.add(phone)
                numbers.append(phone)

    return numbers[:3]


def load_master_indexes():
    apn_index = {}
    owner_index = {}

    if not os.path.exists(MASTER_JSON):
        print(f"Warning: {MASTER_JSON} not found. Distress fields will be blank.")
        return apn_index, owner_index

    with open(MASTER_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = data.get("records", [])

    for record in records:
        parcel = normalize_apn(record.get("parcel", ""))
        owner = normalize_text(record.get("owner", ""))

        if parcel and parcel not in apn_index:
            apn_index[parcel] = record

        if owner and owner not in owner_index:
            owner_index[owner] = record

    return apn_index, owner_index


def find_master_match(row, apn_index, owner_index):
    raw_apn = row.get("associated_property_apn_parcel_id", "")
    apn_key = normalize_apn(raw_apn)

    if apn_key and apn_key in apn_index:
        return apn_index[apn_key]

    owner_key = normalize_owner_name(
        first_name=row.get("first_name", ""),
        last_name=row.get("last_name", "")
    )

    if owner_key and owner_key in owner_index:
        return owner_index[owner_key]

    return None


def format_tags(tags):
    if isinstance(tags, list):
        return ", ".join([clean_text(t) for t in tags if clean_text(t)])
    return clean_text(tags)


def build_output_row(row, master_match):
    wireless_numbers = get_wireless_numbers(row)

    score = ""
    tags = ""
    tax_sale = ""
    probate = ""
    case_number = ""
    amount_due = ""
    source_count = ""
    stacked_distress = ""

    if master_match:
        score = master_match.get("score", "")
        tags = format_tags(master_match.get("tags", []))
        tax_sale = clean_text(master_match.get("tax_sale", ""))
        probate = clean_text(master_match.get("probate", ""))
        case_number = clean_text(master_match.get("case_number", ""))
        amount_due = clean_text(master_match.get("amount_due", ""))
        source_count = clean_text(master_match.get("source_count", ""))

        if tax_sale == "YES" and probate == "YES":
            stacked_distress = "YES"
        else:
            stacked_distress = "NO"

    output = {
        "associated_property_address_full": clean_text(row.get("associated_property_address_full", "")),
        "first_name": clean_text(row.get("first_name", "")),
        "last_name": clean_text(row.get("last_name", "")),
        "middle_initial": clean_text(row.get("middle_initial", "")),
        "primary_mailing_address": clean_text(row.get("primary_mailing_address", "")),
        "primary_mailing_city": clean_text(row.get("primary_mailing_city", "")),
        "primary_mailing_state": clean_text(row.get("primary_mailing_state", "")),
        "primary_mailing_zip": clean_text(row.get("primary_mailing_zip", "")),
        "contact_flags": clean_text(row.get("contact_flags", "")),
        "email_address_1": clean_text(row.get("email_address_1", "")),
        "email_address_2": clean_text(row.get("email_address_2", "")),
        "email_address_3": clean_text(row.get("email_address_3", "")),
        "PHONE": wireless_numbers[0] if len(wireless_numbers) > 0 else "",
        "PHONE 2": wireless_numbers[1] if len(wireless_numbers) > 1 else "",
        "PHONE 3": wireless_numbers[2] if len(wireless_numbers) > 2 else "",
        "ADDRESS": clean_text(row.get("associated_property_address_line_1", "")),
        "CITY": clean_text(row.get("associated_property_address_city", "")),
        "STATE": clean_text(row.get("associated_property_address_state", "")),
        "POSTAL CODE": clean_text(row.get("associated_property_address_zipcode", "")),
        "COUNTY": clean_text(row.get("associated_property_address_county", "")),
        "APN": excel_safe_text(row.get("associated_property_apn_parcel_id", "")),
        "SIZE": clean_text(row.get("lot_acreage", "")),
        "SCORE": score,
        "TAGS": tags,
        "TAX SALE": tax_sale,
        "PROBATE": probate,
        "CASE NUMBER": case_number,
        "AMOUNT DUE": amount_due,
        "SOURCE COUNT": source_count,
        "STACKED DISTRESS": stacked_distress,
    }

    return output


def has_wireless(output_row):
    return any([
        clean_text(output_row.get("PHONE", "")),
        clean_text(output_row.get("PHONE 2", "")),
        clean_text(output_row.get("PHONE 3", "")),
    ])


def sort_rows(rows):
    def score_key(row):
        try:
            return float(clean_text(row.get("SCORE", 0)) or 0)
        except:
            return 0.0

    rows.sort(key=score_key, reverse=True)
    return rows


def save_csv(filename, rows):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FINAL_HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        return

    apn_index, owner_index = load_master_indexes()

    cleaned_all = []
    wireless_ready = []
    no_wireless_reskip = []

    with open(INPUT_FILE, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            master_match = find_master_match(row, apn_index, owner_index)
            output_row = build_output_row(row, master_match)

            cleaned_all.append(output_row)

            if has_wireless(output_row):
                wireless_ready.append(output_row)
            else:
                no_wireless_reskip.append(output_row)

    cleaned_all = sort_rows(cleaned_all)
    wireless_ready = sort_rows(wireless_ready)
    no_wireless_reskip = sort_rows(no_wireless_reskip)

    save_csv(OUTPUT_ALL, cleaned_all)
    save_csv(OUTPUT_WIRELESS, wireless_ready)
    save_csv(OUTPUT_RESKIP, no_wireless_reskip)

    print(f"Saved {len(cleaned_all)} rows to {OUTPUT_ALL}")
    print(f"Saved {len(wireless_ready)} rows to {OUTPUT_WIRELESS}")
    print(f"Saved {len(no_wireless_reskip)} rows to {OUTPUT_RESKIP}")
    print("Done.")


if __name__ == "__main__":
    main()