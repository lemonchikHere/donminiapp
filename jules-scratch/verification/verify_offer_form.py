import asyncio
from playwright.async_api import async_playwright
import os

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

        await page.goto("http://localhost:8001")

        # Wait for the button to appear, then click it
        offer_button = page.get_by_role("button", name="🏠 Предложить объект")
        await offer_button.wait_for(state="visible", timeout=60000)
        await offer_button.click()

        # Wait for the form to be visible
        await page.wait_for_selector("form")

        # Fill out the form
        await page.select_option('select[name="transactionType"]', 'Продать')
        await page.select_option('select[name="propertyType"]', 'Квартира')
        await page.fill('input[name="address"]', "ул. Артема, 123")
        await page.fill('input[name="area"]', "75")
        await page.fill('input[name="floors"]', "5/9")
        await page.fill('input[name="rooms"]', "3")
        await page.fill('input[name="price"]', "50000")
        await page.fill('textarea[name="description"]', "Отличная квартира в центре города.")
        await page.fill('input[name="name"]', "Иван Иванов")
        await page.fill('input[name="phone"]', "+380711234567")

        # Take a screenshot of the form
        await page.screenshot(path="jules-scratch/verification/offer_form.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
