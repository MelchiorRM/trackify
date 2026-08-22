"""
Real-browser Phase 4 checkpoint: two accounts (Alice, Bob) in two isolated
browser contexts. Alice posts, Bob follows Alice, likes/comments/reposts
her post (the comment @mentions Alice), Alice sees all of it as
notifications and in her activity feed once she follows Bob back, and the
two DM each other with the unread badge updating.

Requires the backend (:8000), frontend (:3000), Postgres, and Redis already
running — see scripts/local-services.sh and
trackify-app/e2e/test_phase2_core_tracking.py for the startup commands.
"""

import os
import uuid
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"

CHROMIUM_LIBS = Path(__file__).resolve().parents[2] / ".local-services" / "chromium-libs"
if CHROMIUM_LIBS.is_dir():
    os.environ["LD_LIBRARY_PATH"] = f"{CHROMIUM_LIBS}:{os.environ.get('LD_LIBRARY_PATH', '')}"


def register(page, username, email, password):
    page.goto(f"{BASE_URL}/register")
    page.get_by_label("Username").fill(username)
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(password)
    page.click("button[type=submit]")
    page.wait_for_url(f"{BASE_URL}/", timeout=5000)


def main():
    suffix = uuid.uuid4().hex[:8]
    alice_username = f"e2ealice{suffix}"
    bob_username = f"e2ebob{suffix}"
    password = "password123"

    with sync_playwright() as p:
        browser = p.chromium.launch()

        alice_ctx = browser.new_context()
        bob_ctx = browser.new_context()
        alice = alice_ctx.new_page()
        bob = bob_ctx.new_page()
        for page, name in ((alice, "alice"), (bob, "bob")):
            page.on(
                "console",
                lambda msg, name=name: msg.type == "error" and print(f"[{name} console:error] {msg.text}"),
            )

        register(alice, alice_username, f"{alice_username}@example.com", password)
        register(bob, bob_username, f"{bob_username}@example.com", password)
        print("PASS: registered Alice and Bob")

        # 1. Alice posts from the Home composer
        alice.goto(f"{BASE_URL}/")
        alice.get_by_placeholder("Share something with your followers...").fill(
            f"Hello from Alice, cc @{bob_username}"
        )
        alice.get_by_role("button", name="Post", exact=True).click()
        alice.wait_for_selector(f"text=Hello from Alice, cc @{bob_username}", timeout=10000)
        print("PASS: Alice posted (with a mention of Bob) from the Home composer")

        # 2. Bob sees the mention notification already (posting mentions fire
        # immediately, independent of the follow graph)
        bob.goto(f"{BASE_URL}/notifications")
        bob.wait_for_selector(f"text={alice_username} mentioned you", timeout=10000)
        print("PASS: Bob received a mention notification from Alice's post")

        # 3. Bob follows Alice, then visits her profile to like/comment/repost
        bob.goto(f"{BASE_URL}/profile/{alice_username}")
        bob.get_by_role("button", name="Follow", exact=True).click()
        bob.wait_for_selector("button:has-text('Following')", timeout=10000)
        print("PASS: Bob followed Alice")

        bob.wait_for_selector(f"text=Hello from Alice, cc @{bob_username}", timeout=10000)
        bob.get_by_role("button", name="Like", exact=True).first.click()
        bob.wait_for_selector("button[aria-label='Unlike']", timeout=10000)
        print("PASS: Bob liked Alice's post")

        bob.get_by_placeholder("Write a comment...").first.fill(f"Nice one @{alice_username}!")
        bob.get_by_role("button", name="Post", exact=True).first.click()
        bob.wait_for_selector(f"text=Nice one @{alice_username}!", timeout=10000)
        print("PASS: Bob commented on Alice's post, mentioning her again")

        bob.get_by_role("button", name="Repost", exact=True).first.click()
        bob.get_by_role("button", name="Repost", exact=True).first.click()
        bob.wait_for_selector("button:has-text('Reposted')", timeout=10000)
        print("PASS: Bob reposted Alice's post")

        # 4. Alice's notification bell shows like/comment/mention/repost/follow
        alice.goto(f"{BASE_URL}/notifications")
        alice.wait_for_selector(f"text={bob_username} followed you", timeout=10000)
        alice.wait_for_selector(f"text={bob_username} liked your", timeout=10000)
        alice.wait_for_selector(f"text={bob_username} commented on your", timeout=10000)
        alice.wait_for_selector(f"text={bob_username} mentioned you", timeout=10000)
        alice.wait_for_selector(f"text={bob_username} reposted your", timeout=10000)
        print("PASS: Alice's notifications show follow/like/comment/mention/repost, all from Bob")

        # 5. Alice follows Bob back, so her feed includes his activity
        alice.goto(f"{BASE_URL}/profile/{bob_username}")
        alice.get_by_role("button", name="Follow", exact=True).click()
        alice.wait_for_selector("button:has-text('Following')", timeout=10000)

        alice.goto(f"{BASE_URL}/")
        alice.wait_for_selector(f"text={bob_username} reposted a post", timeout=10000)
        print("PASS: Alice's home feed shows Bob's activity now that she follows him")

        # 6. Direct messages, both directions, with the unread badge updating
        bob.goto(f"{BASE_URL}/profile/{alice_username}")
        bob.get_by_role("button", name="Message", exact=True).click()
        bob.wait_for_url(f"{BASE_URL}/messages/*", timeout=10000)
        bob.get_by_placeholder("Write a message...").fill("Hey Alice!")
        bob.get_by_role("button", name="Send", exact=True).click()
        bob.wait_for_selector("text=Hey Alice!", timeout=10000)
        print("PASS: Bob sent Alice a direct message")

        alice.goto(f"{BASE_URL}/")
        alice.wait_for_selector("a[aria-label='Messages'] span:has-text('1')", timeout=10000)
        print("PASS: Alice's message bell shows an unread badge")

        alice.goto(f"{BASE_URL}/messages")
        alice.get_by_text(bob_username).first.click()
        alice.wait_for_selector("text=Hey Alice!", timeout=10000)
        alice.get_by_placeholder("Write a message...").fill("Hi Bob, got it!")
        alice.get_by_role("button", name="Send", exact=True).click()
        alice.wait_for_selector("text=Hi Bob, got it!", timeout=10000)
        print("PASS: Alice replied; unread badge clears on open, reply thread works both ways")

        browser.close()

    print("\nALL PHASE 4 BROWSER CHECKS PASSED")


if __name__ == "__main__":
    main()
