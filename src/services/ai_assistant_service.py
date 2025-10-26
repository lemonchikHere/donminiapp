import openai
from typing import Dict, Any
from src.config import settings
from src.database import get_db
from src.models.property import Property
from sqlalchemy.orm import Session

openai.api_key = settings.OPENAI_API_KEY

class AIAssistantService:
    def __init__(self, db: Session):
        self.db = db

    async def get_response(self, user_query: str) -> Dict[str, Any]:
        """
        Processes a user query using OpenAI's Function Calling to determine
        the user's intent and extract relevant information.
        """
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_properties",
                    "description": "Searches for real estate properties based on user criteria.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "transaction_type": {"type": "string", "enum": ["sell", "rent"]},
                            "property_type": {"type": "string", "enum": ["apartment", "house", "commercial"]},
                            "rooms": {"type": "integer"},
                            "district": {"type": "string"},
                            "budget_min": {"type": "number"},
                            "budget_max": {"type": "number"},
                        },
                        "required": [],
                    },
                },
            }
        ]

        try:
            response = openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a real estate assistant for Don Estate. You can answer questions about the agency and search for properties."},
                    {"role": "user", "content": user_query},
                ],
                tools=tools,
                tool_choice="auto",
            )
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                # For now, we only handle the first tool call
                tool_call = tool_calls[0]
                if tool_call.function.name == "search_properties":
                    import json
                    args = json.loads(tool_call.function.arguments)
                    return await self._perform_property_search(args)

            # If no tool call, return the text response
            return {"type": "text", "content": response_message.content}

        except Exception as e:
            print(f"Error communicating with OpenAI: {e}")
            return {"type": "error", "content": "Sorry, I'm having trouble connecting to my brain right now."}

    async def _perform_property_search(self, args: Dict) -> Dict[str, Any]:
        """
        Performs a database search based on the arguments extracted by the AI.
        """
        query_text = " ".join(filter(None, [
            args.get('transaction_type'),
            args.get('property_type'),
            f"{args.get('rooms')} комнат" if args.get('rooms') else None,
            args.get('district')
        ]))

        # Generate embedding for semantic search
        query_embedding = None
        if query_text:
            try:
                response = openai.embeddings.create(model="text-embedding-3-small", input=query_text)
                query_embedding = response.data[0].embedding
            except Exception as e:
                print(f"Could not generate embedding for search: {e}")

        # Build query
        query = self.db.query(Property)
        if args.get('transaction_type'):
            query = query.filter(Property.transaction_type == args.get('transaction_type'))
        if args.get('property_type'):
            query = query.filter(Property.property_type == args.get('property_type'))
        # ... add other filters from args

        if query_embedding:
            query = query.order_by(Property.embedding.cosine_distance(query_embedding))

        results = query.limit(3).all() # Return top 3 results for the chat

        return {
            "type": "property_list",
            "properties": [self._format_property_for_chat(p) for p in results],
            "summary": f"Нашел {len(results)} варианта по вашему запросу."
        }

    def _format_property_for_chat(self, prop: Property) -> Dict:
        return {
            "id": str(prop.id),
            "title": f"{prop.rooms or ''}-комн {prop.property_type or ''}",
            "price_usd": prop.price_usd,
            "address": prop.address,
            "photo_url": prop.photos[0] if prop.photos else None
        }

def get_ai_assistant_service(db: Session = next(get_db())) -> AIAssistantService:
    return AIAssistantService(db)
