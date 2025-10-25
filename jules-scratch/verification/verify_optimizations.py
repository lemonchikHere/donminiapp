import asyncio
from playwright.async_api import async_playwright

# This script will be injected into the page to mock the Telegram WebApp object.
mock_telegram_script = """
    window.Telegram = {
        WebApp: {
            initDataUnsafe: {
                user: {
                    id: '123456789'
                }
            },
            colorScheme: 'light',
            onEvent: () => {},
            offEvent: () => {},
            requestLocation: (callback) => {
                callback({ latitude: 48.015, longitude: 37.802 });
            }
        }
    };
"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Listen for console events and print them
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.text}"))

        try:
            # Add the mock script before navigating to the page
            await page.add_init_script(mock_telegram_script)

            await page.goto("http://localhost:8000", wait_until="networkidle")

            # Wait for the button to be visible before clicking
            search_button = page.get_by_role("button", name="🔍 Найти недвижимость")
            await search_button.wait_for(state="visible", timeout=10000) # Increased timeout
            await search_button.click()

            # Fill search form
            await page.get_by_label("Купить").check()
            await page.get_by_label("Квартира").check()
            await page.get_by_role("button", name="Отправить заявку").click()

            # Wait for results to load
            await page.wait_for_selector(".results-list")

            # Scroll down to trigger infinite scroll
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000) # wait for new results

            # Take screenshot
            await page.screenshot(path="jules-scratch/verification/verification.png")
            print("Screenshot taken successfully.")

        except Exception as e:
            print(f"An error occurred: {e}")
            await page.screenshot(path="jules-scratch/verification/error.png")
            print("Error screenshot taken.")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
