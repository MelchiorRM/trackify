"""
Real-browser Phase 1 checkpoint against the shadcn-redesigned UI: 404 page,
empty-form validation, register -> logout -> login -> reload (refresh-token
restore) -> logout, with the navbar (not the old dashboard body) as the
logout entry point. Requires the backend (:8000), frontend (:3000),
Postgres, and Redis already running:

    ./scripts/local-services.sh start
    cd trackify-app/backend && source ../../venv/bin/activate && uvicorn app.main:app --port 8000 &
    cd trackify-app/frontend && npm run dev &

Needs Playwright + a Chromium build. If `playwright install chromium`
fails on missing shared libs without sudo (libnspr4/libnss3), see
.local-services/chromium-libs/ — those were extracted from the matching
.deb packages without installing them system-wide; LD_LIBRARY_PATH below
points at them. Delete that export if your environment has the libs
installed normally.
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
    username = f"e2euser{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    password = "password123"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("console", lambda msg: msg.type == "error" and print(f"[console:error] {msg.text}"))

        # 0a. 404 page (NotFound.jsx)
        page.goto(f"{BASE_URL}/this-route-does-not-exist")
        page.wait_for_selector("text=Page not found", timeout=5000)
        page.click("text=Go home")
        page.wait_for_url(f"{BASE_URL}/", timeout=5000)
        print("PASS: unknown route -> 404 page -> Go home returns to /")

        # 0b. Empty-form validation (FormField/Label/Input composition)
        page.goto(f"{BASE_URL}/login")
        page.click("button[type=submit]")
        page.wait_for_selector("text=Email is required", timeout=5000)
        page.wait_for_selector("text=Password is required", timeout=5000)
        print("PASS: empty login form -> FormField validation errors shown")

        # 1. Register — get_by_label exercises the new Label/Input htmlFor<->id wiring
        page.goto(f"{BASE_URL}/register")
        page.get_by_label("Username").fill(username)
        page.get_by_label("Email").fill(email)
        page.get_by_label("Password").fill(password)
        page.click("button[type=submit]")
        page.wait_for_url(f"{BASE_URL}/", timeout=10000)
        page.wait_for_selector(f"text=Welcome back, {username}", timeout=10000)
        print("PASS: register -> redirected to dashboard, greeting shown")

        # 2. Navbar shows the username and a Log out button (moved out of the
        # dashboard body and into the nav during the redesign)
        nav = page.locator("nav")
        nav.get_by_text(username).wait_for(timeout=10000)
        nav.get_by_role("button", name="Log out").click()
        page.wait_for_url(f"{BASE_URL}/login", timeout=10000)
        print("PASS: navbar shows username; logout -> redirected to /login")

        # 3. Log back in
        page.get_by_label("Email").fill(email)
        page.get_by_label("Password").fill(password)
        page.click("button[type=submit]")
        page.wait_for_url(f"{BASE_URL}/", timeout=10000)
        page.wait_for_selector(f"text=Welcome back, {username}", timeout=10000)
        print("PASS: login -> redirected to dashboard, greeting shown")

        # 4. Reload the page and confirm the session survives (refresh-token flow)
        page.reload()
        page.wait_for_selector(f"text=Welcome back, {username}", timeout=10000)
        print("PASS: reload -> still logged in (refresh-token restore worked)")

        # 5. Confirm the access token is NOT in localStorage (memory-only, per plan)
        local_storage_dump = page.evaluate("() => JSON.stringify(window.localStorage)")
        assert "access_token" not in local_storage_dump
        print("PASS: access token not present in localStorage")

        # 6. Final logout via the navbar to leave a clean state
        page.locator("nav").get_by_role("button", name="Log out").click()
        page.wait_for_url(f"{BASE_URL}/login", timeout=5000)
        print("PASS: final logout -> redirected to /login")

        browser.close()

    print("\nALL PHASE 1 BROWSER CHECKS PASSED")


if __name__ == "__main__":
    main()
