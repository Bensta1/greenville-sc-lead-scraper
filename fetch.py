import requests
from bs4 import BeautifulSoup
import csv

URL = "https://www.greenvillecounty.org/appsas400/taxsale/"

def scrape_tax_sale():
    print("Getting tax sale leads...")

    response = requests.get(URL)

    if response.status_code != 200:
        print("Failed to load page")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table")

    if not table:
        print("No table found.")
        return []

    rows = table.find_all("tr")
    leads = []

    for row in rows:
        cols = row.find_all("td")

        if len(cols) < 4:
            continue

        item = cols[0].get_text(strip=True)
        parcel = cols[1].get_text(strip=True)
        owner = cols[2].get_text(strip=True)
        amount = cols[3].get_text(strip=True)

        leads.append({
            "Item": item,
            "Owner": owner,
            "Parcel": parcel,
            "Amount": amount
        })

    print(f"Found {len(leads)} leads")
    return leads


def save_csv(leads):
    if not leads:
        print("No leads to save")
        return

    with open("leads.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=leads[0].keys())
        writer.writeheader()
        writer.writerows(leads)

    print("Saved leads.csv")


if __name__ == "__main__":
    data = scrape_tax_sale()
    save_csv(data)