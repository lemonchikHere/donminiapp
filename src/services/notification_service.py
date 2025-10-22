from sqlalchemy.orm import Session
from aiogram import Bot

from src.models.property import Property
from src.models.saved_search import SavedSearch
from src.models.user import User

class NotificationService:
    def __init__(self, bot: Bot, db: Session):
        self.bot = bot
        self.db = db

    async def notify_on_new_property(self, new_property: Property):
        """
        Finds users with matching saved searches and sends them a notification.
        """
        all_saved_searches = self.db.query(SavedSearch).all()

        for search in all_saved_searches:
            if self._is_match(new_property, search.criteria):
                user = self.db.query(User).filter(User.id == search.user_id).first()
                if user and user.telegram_user_id:
                    await self._send_notification(user.telegram_user_id, new_property)

    def _is_match(self, prop: Property, criteria: dict) -> bool:
        """
        Checks if a property matches the saved search criteria.
        This is a simplified matching logic.
        """
        if criteria.get('transaction_type') and prop.transaction_type != criteria['transaction_type']:
            return False
        if criteria.get('property_types') and prop.property_type not in criteria['property_types']:
            return False
        if criteria.get('rooms') and prop.rooms != criteria['rooms']:
            return False
        if criteria.get('budget_max') and prop.price_usd > criteria['budget_max']:
            return False
        if criteria.get('budget_min') and prop.price_usd < criteria['budget_min']:
            return False
        # A more complex district/address match would be needed for production
        if criteria.get('district') and criteria['district'].lower() not in (prop.address or '').lower():
            return False

        return True

    async def _send_notification(self, telegram_user_id: int, prop: Property):
        """
        Sends a formatted notification message to the user.
        """
        try:
            message_text = (
                f"🔔 **Новый объект по вашему сохраненному поиску!**\n\n"
                f"**{prop.rooms or ''}-комн {prop.property_type or ''}**\n"
                f"📍 Адрес: {prop.address or 'Не указан'}\n"
                f"💰 Цена: ${prop.price_usd or 'Не указана'}"
            )

            # Here you could add a button to open the Mini App at the property page
            # e.g., using InlineKeyboardMarkup

            if prop.photos and prop.photos[0]:
                await self.bot.send_photo(
                    chat_id=telegram_user_id,
                    photo=prop.photos[0],
                    caption=message_text,
                    parse_mode="Markdown"
                )
            else:
                await self.bot.send_message(
                    chat_id=telegram_user_id,
                    text=message_text,
                    parse_mode="Markdown"
                )
        except Exception as e:
            print(f"Failed to send notification to user {telegram_user_id}: {e}")
