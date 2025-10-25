import asyncio
from playwright.async_api import async_playwright, expect

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Mock the Telegram WebApp object before navigating
        await page.add_init_script("""
            window.Telegram = {
                WebApp: {
                    initDataUnsafe: {
                        user: { id: 123456789 }
                    },
                    colorScheme: 'light',
                    onEvent: () => {},
                    offEvent: () => {},
                    ready: () => {},
                    expand: () => {},
                    requestLocation: (callback) => {
                        callback({latitude: 48.015, longitude: 37.802});
                    }
                }
            };
        """)

        import os
        path = os.path.abspath('static/index.html')
        await page.goto(f'file://{path}')

        # Wait for the app to render by checking for a main screen button
        await expect(page.get_by_role("button", name="🔍 Найти недвижимость")).to_be_visible(timeout=10000)

        # --- Test 1: Map Spinner ---
        await page.get_by_role("button", name="🗺️ Карта").click()
        # The spinner might be brief, so we wait for the map container to appear first
        await expect(page.locator('#map')).to_be_visible()
        # Then we can check for the spinner if it's still there or just proceed
        await page.screenshot(path="jules-scratch/verification/01_map_screen.png")

        # --- Test 2: Chat Spinner ---
        await page.get_by_role("button", name="◀ Назад").click()
        await page.get_by_role("button", name="💬 Чат с ассистентом").click()
        await page.get_by_placeholder("Спросите что-нибудь...").fill("Привет")
        await page.get_by_role("button", name="➤").click()
        await expect(page.locator('.chat-bubble.bot.typing .spinner')).to_be_visible()
        await page.screenshot(path="jules-scratch/verification/02_chat_spinner.png")

        # --- Test 3: Toast Notification ---
        await page.route("**/api/search", lambda route: route.abort())

        await page.get_by_role("button", name="◀").click()
        await page.get_by_role("button", name="🔍 Найти недвижимость").click()

        await page.get_by_label("Купить").check()
        await page.get_by_label("Квартира").check()
        await page.get_by_label("Ваше имя").fill("Тест")
        await page.get_by_label("Номер телефона").fill("+79999999999")
        await page.get_by_role("button", name="Отправить заявку").click()

        await expect(page.locator('.toast')).to_be_visible()
        await expect(page.locator('.toast')).to_have_text('Не удалось выполнить поиск. Пожалуйста, попробуйте еще раз.')
        await page.screenshot(path="jules-scratch/verification/03_toast_notification.png")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
