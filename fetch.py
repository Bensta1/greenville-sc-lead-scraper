import csv
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

URL = "https://www.greenvillecounty.org/appsas400/taxsale/"


def get_run_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def scrape_tax_sale() -> list[dict]:
    print("Getting tax sale leads...")

    try:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Failed to load page: {exc}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")

    if not table:
        print("No table found.")
        return []

    rows = table.find_all("tr")
    leads = []
    run_timestamp = get_run_timestamp()

    for row in rows:
        cols = row.find_all("td")

        if len(cols) < 4:
            continue

        item = cols[0].get_text(strip=True)
        parcel = cols[1].get_text(strip=True)
        owner = cols[2].get_text(strip=True)
        amount = cols[3].get_text(strip=True)

        leads.append(
            {
                "generated_at": run_timestamp,
                "Item": item,
                "Owner": owner,
                "Parcel": parcel,
                "Amount": amount,
            }
        )

    print(f"Found {len(leads)} leads")
    return leads


def save_csv(leads: list[dict], filename: str = "leads.csv") -> None:
    if not leads:
        print("No leads to save")
        return

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["generated_at", "Item", "Owner", "Parcel", "Amount"],
        )
        writer.writeheader()
        writer.writerows(leads)

    print(f"Saved {filename}")


if __name__ == "__main__":
    data = scrape_tax_sale()
    save_csv(data)
