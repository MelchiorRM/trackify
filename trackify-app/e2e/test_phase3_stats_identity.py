"""
Real-browser Phase 3 checkpoint: view the stats dashboard, pin a favorite via
the profile page, toggle the profile's grid/list view, create a shareable
collection and add an item to it from the item detail page, then confirm
the collection's URL works when visited directly (as a public visitor would)
and that settings loads with the current account's details.

Requires the backend (:8000), frontend (:3000), Postgres, and Redis already
running — see scripts/local-services.sh and
trackify-app/e2e/test_phase2_core_tracking.py for the startup commands. Also
requires TMDB_API_KEY/TMDB_BEARER_TOKEN in trackify-app/backend/.env, since
this hits the real TMDB search API (same movie as the Phase 2 checkpoint).
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
    username = f"e2ep3{uuid.uuid4().hex[:8]}"
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

        # 1. Search a real movie, add it, mark completed (feeds the stats
        # endpoint some real data). Only one <select> exists on the item
        # page at this point (no collections yet, so AddToListMenu renders
        # nothing) — safe to target it unscoped, as the Phase 2 test does.
        page.goto(f"{BASE_URL}/search")
        page.get_by_placeholder("Search movies, books, music...").last.fill("The Dark Knight")
        page.get_by_role("button", name="Movies", exact=True).click()
        page.wait_for_selector("text=The Dark Knight", timeout=15000)
        page.get_by_text("The Dark Knight", exact=True).first.click()
        page.wait_for_url(f"{BASE_URL}/item/movie/155", timeout=10000)
        page.get_by_role("button", name="Add to library").click()
        page.wait_for_selector("select", timeout=10000)
        page.locator("select").select_option("completed")
        page.wait_for_selector("text=No sessions logged yet.", state="detached", timeout=10000)
        print("PASS: added and completed an item (stats now has real data)")

        # 2. Stats dashboard reflects it
        page.goto(f"{BASE_URL}/stats")
        page.wait_for_selector("h1:has-text('Your stats')", timeout=10000)
        page.wait_for_selector("text=Completion rate", timeout=10000)
        page.wait_for_selector("text=100%", timeout=10000)
        print("PASS: stats dashboard shows 100% completion rate")

        # 3. Create a shareable collection
        page.goto(f"{BASE_URL}/collections")
        page.get_by_role("button", name="New list").click()
        page.get_by_label("Name").fill("Favorites Watchlist")
        page.get_by_role("button", name="Create list").click()
        page.wait_for_selector("text=Favorites Watchlist", timeout=10000)
        collection_href = page.locator("a[href^='/collections/']").first.get_attribute("href")
        print(f"PASS: created collection at {collection_href}")

        # 4. Add the tracked item to that list from the item detail page.
        # Two <select> elements exist now (status + add-to-list) — scope by
        # the add-to-list option text to avoid a strict-mode ambiguity error.
        page.goto(f"{BASE_URL}/item/movie/155")
        add_to_list_select = page.locator("select").filter(has_text="Add to a list")
        add_to_list_select.select_option(label="Favorites Watchlist")
        page.get_by_role("button", name="Add", exact=True).click()
        page.wait_for_selector("button:has-text('Added')", timeout=10000)
        print("PASS: added item to the collection from the item detail page")

        # 5. Collection URL works when visited directly (shareable by URL)
        page.goto(f"{BASE_URL}{collection_href}")
        page.wait_for_selector("h1:has-text('Favorites Watchlist')", timeout=10000)
        page.wait_for_selector("text=The Dark Knight", timeout=10000)
        print("PASS: collection detail page works when the URL is visited directly")

        # 6. Profile: grid view (default), pin a favorite, list view toggle
        page.goto(f"{BASE_URL}/profile/{username}")
        page.wait_for_selector(f"h1:has-text('{username}')", timeout=10000)
        page.wait_for_selector("img[alt='The Dark Knight']", timeout=10000)
        print("PASS: profile grid view shows the tracked item's cover art")

        page.get_by_role("button", name="Edit favorites").click()
        page.get_by_alt_text("The Dark Knight").first.click()
        page.get_by_role("button", name="Save favorites").click()
        page.wait_for_selector("button:has-text('Edit favorites')", timeout=10000)
        print("PASS: pinned a favorite from the profile page")

        page.get_by_role("button", name="List", exact=True).click()
        page.wait_for_selector("text=Completed", timeout=10000)
        print("PASS: profile list-view toggle shows status detail")

        # 7. Settings loads with the current account's details
        page.goto(f"{BASE_URL}/settings")
        page.wait_for_selector("text=Settings", timeout=10000)
        username_value = page.get_by_label("Username").input_value()
        assert username_value == username, f"expected {username!r}, got {username_value!r}"
        print("PASS: settings page prefilled with the logged-in account's details")

        browser.close()

    print("\nALL PHASE 3 BROWSER CHECKS PASSED")


if __name__ == "__main__":
    main()
