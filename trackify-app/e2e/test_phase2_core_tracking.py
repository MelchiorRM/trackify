"""
Real-browser Phase 2 checkpoint: search a real movie (live TMDB call, not
mocked) -> open its detail page -> add to library -> mark completed (which
auto-logs a diary entry) -> log an explicit rewatch -> write a star rating +
review -> confirm it all shows up on /library too.

Requires the backend (:8000), frontend (:3000), Postgres, and Redis already
running — see scripts/local-services.sh and trackify-app/e2e/test_phase1_auth.py
for the startup commands. Also requires TMDB_API_KEY/TMDB_BEARER_TOKEN set
in trackify-app/backend/.env, since this hits the real TMDB search API.
"""

import os
import uuid
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"

CHROMIUM_LIBS = Path(__file__).resolve().parents[2] / ".local-services" / "chromium-libs"
if CHROMIUM_LIBS.is_dir():
    os.environ["LD_LIBRARY_PATH"] = f"{CHROMIUM_LIBS}:{os.environ.get('LD_LIBRARY_PATH', '')}"


def main():
    username = f"e2ep2{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    password = "password123"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("console", lambda msg: msg.type == "error" and print(f"[console:error] {msg.text}"))

        # 0. Register a fresh user
        page.goto(f"{BASE_URL}/register")
        page.get_by_label("Username").fill(username)
        page.get_by_label("Email").fill(email)
        page.get_by_label("Password").fill(password)
        page.click("button[type=submit]")
        page.wait_for_url(f"{BASE_URL}/", timeout=5000)
        print("PASS: registered fresh user")

        # 1. Search for a real movie (live TMDB call)
        # Two inputs share this placeholder (navbar SearchBar + the page's
        # own) — .last is the page-body one, rendered after the navbar.
        page.goto(f"{BASE_URL}/search")
        page.get_by_placeholder("Search movies, books, music...").last.fill("The Dark Knight")
        page.get_by_role("button", name="Movies", exact=True).click()
        page.wait_for_selector("text=The Dark Knight", timeout=15000)
        print("PASS: search returned real results from TMDB")

        # 2. Open the item detail page
        page.get_by_text("The Dark Knight", exact=True).first.click()
        page.wait_for_url(f"{BASE_URL}/item/movie/155", timeout=10000)
        page.wait_for_selector("h1:has-text('The Dark Knight')", timeout=10000)
        print("PASS: opened item detail page")

        # 3. Add to library
        page.get_by_role("button", name="Add to library").click()
        page.wait_for_selector("select", timeout=10000)
        print("PASS: added to library (status picker appeared)")

        # 4. Mark completed -> should auto-log a diary entry
        page.locator("select").select_option("completed")
        page.wait_for_selector("text=No sessions logged yet.", state="detached", timeout=10000)
        print("PASS: marking completed auto-logged a diary entry")

        # 5. Log an explicit rewatch
        page.get_by_label("Rewatch").check()
        page.get_by_role("button", name="Log session").click()
        page.wait_for_selector("text=Rewatch", timeout=10000)
        print("PASS: logged an explicit rewatch diary entry")

        # 6. Write a star rating + review
        page.get_by_role("button", name="Rate 4.5 stars").click()
        page.get_by_placeholder("Write your review (optional)").fill("Genuinely great, holds up.")
        page.get_by_role("button", name="Save review").click()
        page.wait_for_selector("text=Genuinely great, holds up.", timeout=10000)
        print("PASS: wrote a star rating + review")

        # 7. Confirm it shows up on /library too
        page.goto(f"{BASE_URL}/library")
        page.wait_for_selector("text=The Dark Knight", timeout=10000)
        print("PASS: item appears on the library page")

        browser.close()

    print("\nALL PHASE 2 BROWSER CHECKS PASSED")


if __name__ == "__main__":
    main()
