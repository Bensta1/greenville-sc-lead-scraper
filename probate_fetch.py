from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import csv
import time

URL = "https://www.greenvillecounty.org/appsas400/Probate/"
SEARCH_LETTERS = ["A", "B", "C"]
PARTY_TYPE = "Deceased"
OUTPUT_FILE = "probate_leads.csv"


def wait_for_results(page, timeout=10000):
    try:
        page.wait_for_url("**/SearchResults.aspx**", timeout=timeout)
        return True
    except PlaywrightTimeoutError:
        return False


def try_submit(page):
    # 1. Press Enter in the name field
    try:
        name_input = page.locator('input[type="text"]').first
        name_input.focus()
        name_input.press("Enter")
        if wait_for_results(page, 5000):
            return True
    except Exception:
        pass

    # 2. Try form requestSubmit()
    try:
        ok = page.evaluate("""
            () => {
                const el = document.querySelector('input[type="text"]');
                if (!el || !el.form) return false;
                if (typeof el.form.requestSubmit === 'function') {
                    el.form.requestSubmit();
                } else {
                    el.form.submit();
                }
                return true;
            }
        """)
        if ok and wait_for_results(page, 5000):
            return True
    except Exception:
        pass

    # 3. Try clicking visible buttons/links with "Search"
    click_targets = [
        'input[type="submit"]',
        'button[type="submit"]',
        'button',
        'a',
        'text=Search'
    ]

    for selector in click_targets:
        try:
            locator = page.locator(selector)
            count = locator.count()
            for i in range(count):
                try:
                    locator.nth(i).click(timeout=2000, force=True)
                    if wait_for_results(page, 5000):
                        return True
                except Exception:
                    continue
        except Exception:
            continue

    return False


def scrape_results(page, letter):
    results = []

    try:
        page.wait_for_selector("table tr", timeout=8000)
    except PlaywrightTimeoutError:
        print(f"{letter}: no table found on results page")
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
                "name": name,
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
            row["name"].upper(),
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
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)

            try:
                page.locator('input[type="text"]').first.fill(letter)
                page.locator("select").first.select_option(label=PARTY_TYPE)
            except Exception as e:
                print(f"{letter}: could not fill form: {e}")
                continue

            print(f"{letter}: form filled, submitting...")
            submitted = try_submit(page)

            if not submitted:
                print(f"{letter}: submit failed")
                continue

            if "SearchResults.aspx" not in page.url:
                print(f"{letter}: results page not reached")
                continue

            letter_results = scrape_results(page, letter)
            all_results.extend(letter_results)

            time.sleep(1)

        browser.close()

    return dedupe_rows(all_results)


def save_csv(rows):
    if not rows:
        print("No probate rows found.")
        return

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["case_number", "name", "party_type", "search_prefix"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} probate leads to {OUTPUT_FILE}")


if __name__ == "__main__":
    print("Starting automated probate pull...")
    data = scrape_probate()
    save_csv(data)
    print("Done.")