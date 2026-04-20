from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import csv
import time

URL = "https://www.greenvillecounty.org/appsas400/Probate/"
SEARCH_LETTERS = ["A", "B", "C"]
PARTY_TYPE_LABELS = ["Deceased", "Deceased Person"]
OUTPUT_FILE = "probate_leads.csv"


def goto_probate_home(page):
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_load_state("networkidle", timeout=15000)


def get_name_input(page):
    candidates = [
        'input[type="text"]',
        'input[name*="search" i]',
        'input[id*="search" i]',
        'input[name*="name" i]',
        'input[id*="name" i]',
    ]
    for selector in candidates:
        locator = page.locator(selector)
        if locator.count() > 0:
            return locator.first
    raise RuntimeError("Could not find probate name input")


def get_party_type_select(page):
    candidates = [
        'select',
        'select[name*="party" i]',
        'select[id*="party" i]',
        'select[name*="type" i]',
        'select[id*="type" i]',
    ]
    for selector in candidates:
        locator = page.locator(selector)
        if locator.count() > 0:
            return locator.first
    raise RuntimeError("Could not find probate party type dropdown")


def select_party_type(page):
    dropdown = get_party_type_select(page)
    options = dropdown.locator("option")
    available = [options.nth(i).inner_text().strip() for i in range(options.count())]

    for label in PARTY_TYPE_LABELS:
        if label in available:
            dropdown.select_option(label=label)
            return label

    raise RuntimeError(f"Could not find Deceased option. Available options: {available}")


def click_search(page):
    candidates = [
        'input[type="submit"][value*="Search" i]',
        'button[type="submit"]:has-text("Search")',
        'input[value*="Search" i]',
        'button:has-text("Search")',
        'text=Search',
    ]

    for selector in candidates:
        locator = page.locator(selector)
        if locator.count() == 0:
            continue

        for i in range(locator.count()):
            try:
                with page.expect_navigation(wait_until="domcontentloaded", timeout=15000):
                    locator.nth(i).click(force=True)
                page.wait_for_load_state("networkidle", timeout=10000)
                return True
            except Exception:
                continue

    return False


def on_results_page(page):
    return "SearchResults.aspx" in page.url


def has_404_error(page):
    return "404Error.aspx" in page.url or "404" in page.url


def scrape_results(page, letter):
    results = []

    try:
        page.wait_for_selector("table tr", timeout=10000)
    except PlaywrightTimeoutError:
        print(f"{letter}: no table rows found on results page")
        return results

    rows = page.locator("table tr")
    row_count = rows.count()
    print(f"{letter}: found {row_count} total rows")

    for i in range(1, row_count):
        cols = rows.nth(i).locator("td")
        if cols.count() < 3:
            continue

        try:
            case_number = cols.nth(0).inner_text().strip()
            name = cols.nth(1).inner_text().strip()
            party_type = cols.nth(2).inner_text().strip()

            if not case_number and not name:
                continue

            results.append({
                "case_number": case_number,
                "Owner": name,
                "party_type": party_type,
                "search_prefix": letter
            })
        except Exception:
            continue

    return results


def dedupe_rows(rows):
    seen = set()
    clean = []

    for row in rows:
        key = (
            row["case_number"].upper(),
            row["Owner"].upper(),
            row["party_type"].upper(),
            row["search_prefix"].upper()
        )
        if key in seen:
            continue
        seen.add(key)
        clean.append(row)

    return clean


def scrape_probate():
    all_results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for letter in SEARCH_LETTERS:
            print(f"\nOpening probate page for letter: {letter}")

            try:
                goto_probate_home(page)

                name_input = get_name_input(page)
                name_input.fill("")
                name_input.fill(letter)

                selected_label = select_party_type(page)
                print(f"{letter}: selected party type = {selected_label}")

                submitted = click_search(page)
                if not submitted:
                    print(f"{letter}: could not click Search button")
                    continue

                if has_404_error(page):
                    print(f"{letter}: hit 404/error page after submit")
                    continue

                if not on_results_page(page):
                    print(f"{letter}: results page not reached, current URL = {page.url}")
                    continue

                letter_results = scrape_results(page, letter)
                all_results.extend(letter_results)
                time.sleep(1)

            except Exception as e:
                print(f"{letter}: scrape failed: {e}")
                continue

        browser.close()

    return dedupe_rows(all_results)


def save_csv(rows):
    if not rows:
        print("No probate rows found.")
        return

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["case_number", "Owner", "party_type", "search_prefix"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} probate leads to {OUTPUT_FILE}")


if __name__ == "__main__":
    print("Starting automated probate pull...")
    data = scrape_probate()
    save_csv(data)
    print("Done.")