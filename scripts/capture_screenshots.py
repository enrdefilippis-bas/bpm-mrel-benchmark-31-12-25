"""Playwright-based screenshot capture for Dash pages.

Captures PNGs of each registered Dash page for README embedding.

Setup (one-time):
    pip install playwright && playwright install chromium

Usage:
    python scripts/capture_screenshots.py

Requirements:
    - Dash app running at http://localhost:8050
    - Run `python -m app.app` in another terminal before executing this script
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print(
        "playwright not found. Install with:\n"
        "  pip install playwright && playwright install chromium"
    )
    sys.exit(1)


PAGES = [
    ("", "home"),
    ("/cushion", "cushion"),
    ("/composition", "composition"),
    ("/maturity", "maturity"),
    ("/trend", "trend"),
    ("/creditor-rank", "creditor-rank"),
    ("/country", "country"),
    ("/outliers", "outliers"),
]
APP_URL = "http://localhost:8050"
OUTPUT_DIR = Path("docs/screenshots")
VIEWPORT_WIDTH = 1400
VIEWPORT_HEIGHT = 900
SCREENSHOT_DELAY = 1.0  # seconds


async def capture_screenshots() -> None:
    """Capture one screenshot per page."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}
        )
        page = await context.new_page()

        for route_path, slug in PAGES:
            url = f"{APP_URL}{route_path}"
            try:
                print(f"Capturing {slug}...", end=" ", flush=True)
                await page.goto(url, wait_until="networkidle", timeout=10000)
                await page.wait_for_timeout(int(SCREENSHOT_DELAY * 1000))

                output_file = OUTPUT_DIR / f"{slug}.png"
                await page.screenshot(path=str(output_file), full_page=False)
                print(f"✓ {output_file}")
            except Exception as e:
                print(f"✗ Error: {e}")

        await context.close()
        await browser.close()


async def check_connection() -> bool:
    """Check if the Dash app is running at localhost:8050."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            await page.goto(APP_URL, timeout=15000)
            await context.close()
            await browser.close()
            return True
        except Exception:
            await context.close()
            await browser.close()
            return False


async def main() -> None:
    """Entry point."""
    print(f"Checking connection to {APP_URL}...")
    if not await check_connection():
        print(
            f"\nError: Could not connect to {APP_URL}\n\n"
            "Make sure the Dash app is running:\n"
            "  python -m app.app\n"
        )
        sys.exit(1)

    print(f"Connected. Capturing {len(PAGES)} pages...\n")
    await capture_screenshots()
    print(f"\nScreenshots saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    asyncio.run(main())
