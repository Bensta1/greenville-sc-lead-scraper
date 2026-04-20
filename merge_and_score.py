def build_master():
    tax_leads = load_csv("leads.csv")
    probate_leads = load_csv("probate_leads.csv")

    run_timestamp = datetime.now(timezone.utc).isoformat()

    records_map = {}

    # --- PROCESS TAX LEADS ---
    for row in tax_leads:
        owner_key = row.get("Owner", "").lower().strip()

        amount = parse_amount(row.get("Amount", ""))

        score = 30
        tags = ["Tax Sale"]

        if amount >= 5000:
            score += 10
            tags.append("High Tax Amount")

        if any(x in owner_key for x in ["llc", "inc", "corp"]):
            score += 10
            tags.append("Business Owner")

        records_map[owner_key] = {
            "owner": row.get("Owner", ""),
            "parcel": row.get("Parcel", ""),
            "amount_due": row.get("Amount", ""),
            "amount_due_num": amount,
            "case_number": row.get("Item", ""),
            "tax_sale": "YES",
            "probate": "NO",
            "score": score,
            "tags": tags,
            "generated_at": run_timestamp
        }

    # --- PROCESS PROBATE LEADS ---
    for row in probate_leads:
        owner_key = row.get("Owner", "").lower().strip()

        if owner_key in records_map:
            # 🔥 STACKED MATCH
            records_map[owner_key]["probate"] = "YES"
            records_map[owner_key]["score"] += 40
            records_map[owner_key]["tags"].append("Probate")
            records_map[owner_key]["tags"].append("STACKED")

        else:
            # probate only
            records_map[owner_key] = {
                "owner": row.get("Owner", ""),
                "parcel": "",
                "amount_due": "",
                "amount_due_num": 0,
                "case_number": "",
                "tax_sale": "NO",
                "probate": "YES",
                "score": 40,
                "tags": ["Probate"],
                "generated_at": run_timestamp
            }

    records = list(records_map.values())

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