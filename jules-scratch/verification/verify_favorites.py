import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Mock the Telegram WebApp API
        await page.add_init_script("""
            window.Telegram = {
                WebApp: {
                    initDataUnsafe: { user: { id: 12345 } },
                    colorScheme: 'light',
                    onEvent: () => {},
                    offEvent: () => {},
                    requestLocation: (callback) => {
                        callback({ latitude: 48.015, longitude: 37.802 });
                    }
                }
            };
        """)

        await page.goto("http://localhost:8000")

        # Wait for the preloader to disappear
        await page.wait_for_selector("#preloader", state="hidden")

        # Wait for the main screen to load
        await page.wait_for_selector(".main-buttons")

        # Click the "Favorites" button
        await page.get_by_role("button", name="❤️ Избранное").click()

        # Wait for the favorites screen to load and take a screenshot
        await page.wait_for_selector(".results-list")
        await page.screenshot(path="jules-scratch/verification/favorites_screen.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
