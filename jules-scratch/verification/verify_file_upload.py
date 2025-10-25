import asyncio
from playwright.async_api import async_playwright, expect

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        # Mock the Telegram WebApp object
        await page.add_init_script("""
            window.Telegram = {
                WebApp: {
                    initDataUnsafe: { user: { id: 123456789 } },
                    colorScheme: 'light',
                    onEvent: () => {},
                    offEvent: () => {},
                    ready: () => {},
                    expand: () => {},
                }
            };
        """)

        import os
        path = os.path.abspath('static/index.html')
        await page.goto(f'file://{path}')

        # Wait for the app to render
        await expect(page.get_by_role("button", name="🏠 Предложить объект")).to_be_visible(timeout=10000)
        await page.get_by_role("button", name="🏠 Предложить объект").click()

        # --- Fill the form ---
        await page.get_by_label("Продать").check()
        await page.get_by_label("Тип недвижимости").select_option("Квартира")
        await page.get_by_label("Адрес").fill("Улица Пушкина, дом Колотушкина")
        await page.get_by_label("Ваше имя").fill("Тестировщик")
        await page.get_by_label("Номер телефона").fill("+79998887766")

        # --- Set files to upload ---
        # Create a dummy file in memory for upload
        dummy_content = b'0' * (1024 * 1024) # 1MB file
        await page.locator('input[type="file"][multiple]').set_input_files([
            {'name': 'photo1.jpg', 'mimeType': 'image/jpeg', 'buffer': dummy_content},
            {'name': 'photo2.jpg', 'mimeType': 'image/jpeg', 'buffer': dummy_content},
        ])

        # Mock the API response and simulate slow upload
        await page.route(
            "**/api/offers/",
            lambda route: asyncio.sleep(2) and route.fulfill(status=201, json={"status": "pending_moderation", "property_id": "mock-uuid"})
        )

        # --- Submit and capture progress ---
        # Click submit to start the upload
        await page.get_by_role("button", name="Отправить заявку").click()

        # Wait for the progress bar to appear and reach ~50%
        await expect(page.locator('.upload-progress-bar')).to_be_visible()
        # We can't easily assert 50% width, so we'll just take a screenshot while it's in progress
        await page.wait_for_timeout(500) # Give it a moment to show progress

        await page.screenshot(path="jules-scratch/verification/01_upload_progress.png")

        # Wait for success modal
        await expect(page.get_by_text("✅ Заявка успешно отправлена на модерацию!")).to_be_visible()
        await page.screenshot(path="jules-scratch/verification/02_upload_success.png")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
