import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from src.config import settings
from src.services.ai_assistant_service import get_ai_assistant_service

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()
ai_assistant = get_ai_assistant_service()


@dp.message(Command(commands=["start", "help"]))
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply(
        "Привет! Я ассистент агентства недвижимости Don Estate.\n"
        "Вы можете задать мне любой вопрос или описать, "
        "какую недвижимость вы ищете.\n"
        "Например: 'Ищу двухкомнатную квартиру в Ворошиловском районе'."
    )


@dp.message()
async def handle_message(message: types.Message):
    """
    Handle all other messages
    """
    user_query = message.text
    response = await ai_assistant.get_response(user_query)

    if response["type"] == "text":
        await message.answer(response["content"])
    elif response["type"] == "property_list":
        await message.answer(response["summary"])
        for prop in response["properties"]:
            caption = (
                f"<b>{prop['title']}</b>\n"
                f"Адрес: {prop.get('address', 'Не указан')}\n"
                f"Цена: ${prop.get('price_usd', 'Не указана')}"
            )
            if prop["photo_url"]:
                await message.answer_photo(
                    photo=prop["photo_url"],
                    caption=caption,
                    parse_mode="HTML",
                )
            else:
                await message.answer(caption, parse_mode="HTML")
    elif response["type"] == "error":
        await message.answer(response["content"])


async def main():
    # Start the bot
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
