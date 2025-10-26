import uuid
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional

from src.models.property import Property

class OfferService:
    def __init__(self, db: Session):
        self.db = db
        self.media_path = Path("media")
        self.media_path.mkdir(exist_ok=True)

    async def save_file(self, file: UploadFile) -> str:
        """Saves a file to the media directory and returns its public URL."""
        filename = f"{uuid.uuid4()}{Path(file.filename).suffix}"
        file_path = self.media_path / filename
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        return f"/{self.media_path}/{filename}"

    def _map_property_type(self, prop_type_ru: str) -> Optional[str]:
        mapping = {
            "Квартира": "apartment",
            "Дом": "house",
            "Коммерческая недвижимость": "commercial",
        }
        return mapping.get(prop_type_ru)

    async def create_offer_property(
        self,
        offer_data: dict,
        photos: Optional[List[UploadFile]] = None,
        video: Optional[UploadFile] = None,
    ) -> Property:
        """
        Creates a new Property instance for the offer with status 'moderation'.
        """
        photo_urls = []
        if photos:
            for photo in photos:
                if photo.filename:
                    photo_urls.append(await self.save_file(photo))

        video_url = None
        if video and video.filename:
            video_url = await self.save_file(video)

        new_property = Property(
            transaction_type='sell' if offer_data.get('transactionType') == 'Продать' else 'rent',
            property_type=self._map_property_type(offer_data.get('propertyType', '')),
            address=offer_data.get('address'),
            area_sqm=float(offer_data['area']) if offer_data.get('area') else None,
            floor=offer_data.get('floors'),
            rooms=int(offer_data['rooms']) if offer_data.get('rooms') else None,
            price_usd=float(offer_data['price']) if offer_data.get('price') else None,
            description=offer_data.get('description'),
            photos=photo_urls,
            video_url=video_url,
            status='moderation'
        )

        self.db.add(new_property)
        self.db.commit()
        self.db.refresh(new_property)

        return new_property
