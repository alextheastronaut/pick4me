"""
Run with: uv run python -m app.seed
"""
import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import MenuItem, MenuItemTag, QuizAnswer, QuizQuestion, Restaurant, Tag

TAGS = [
    # dietary
    {"key": "vegan",          "category": "dietary", "display_name": "Vegan"},
    {"key": "vegetarian",     "category": "dietary", "display_name": "Vegetarian"},
    {"key": "gluten_free",    "category": "dietary", "display_name": "Gluten-Free"},
    {"key": "contains_nuts",  "category": "dietary", "display_name": "Contains Nuts"},
    {"key": "contains_dairy", "category": "dietary", "display_name": "Contains Dairy"},
    # protein
    {"key": "chicken", "category": "protein", "display_name": "Chicken"},
    {"key": "beef",    "category": "protein", "display_name": "Beef"},
    {"key": "pork",    "category": "protein", "display_name": "Pork"},
    {"key": "fish",    "category": "protein", "display_name": "Fish & Seafood"},
    {"key": "tofu",    "category": "protein", "display_name": "Tofu"},
    # flavor
    {"key": "spicy",  "category": "flavor", "display_name": "Spicy"},
    {"key": "sweet",  "category": "flavor", "display_name": "Sweet"},
    {"key": "savory", "category": "flavor", "display_name": "Savory"},
    {"key": "umami",  "category": "flavor", "display_name": "Umami"},
    # profile
    {"key": "light",       "category": "profile", "display_name": "Light"},
    {"key": "filling",     "category": "profile", "display_name": "Filling"},
    {"key": "adventurous", "category": "profile", "display_name": "Adventurous"},
    {"key": "comforting",  "category": "profile", "display_name": "Comforting"},
    # price
    {"key": "budget",  "category": "price", "display_name": "Budget-Friendly"},
    {"key": "mid",     "category": "price", "display_name": "Mid-Range"},
    {"key": "premium", "category": "price", "display_name": "Premium"},
]

# fmt: off
MENU_ITEMS = [
    # --- Appetizers ---
    {
        "name": "Garlic Butter Chicken Wings",
        "description": "Crispy golden wings tossed in our signature rich garlic butter sauce.",
        "price_cents": 1200,
        "is_signature": True,
        "popularity_score": 8.3,
        "tags": [("chicken", 1.5), ("savory", 1.5), ("light", 1.5), ("budget", 1.0)],
    },
    {
        "name": "Shrimp Tempura",
        "description": "Plump shrimp dipped in a light, airy batter and fried until golden crisp.",
        "price_cents": 1200,
        "is_signature": False,
        "popularity_score": 7.0,
        "tags": [("fish", 1.0), ("savory", 1.0), ("light", 1.5), ("budget", 1.0)],
    },
    {
        "name": "Fried Gyoza",
        "description": "Japanese-style dumplings filled with savory pork and vegetables, pan-fried for a crispy bite.",
        "price_cents": 900,
        "is_signature": False,
        "popularity_score": 6.5,
        "tags": [("pork", 1.0), ("savory", 1.0), ("light", 1.5), ("budget", 1.5)],
    },
    {
        "name": "Veggie Spring Rolls",
        "description": "Crispy rolls filled with a fresh vegetable mix, fried golden and perfect for sharing.",
        "price_cents": 900,
        "is_signature": False,
        "popularity_score": 6.0,
        "tags": [("vegan", 1.0), ("vegetarian", 1.0), ("savory", 1.0), ("light", 1.5), ("budget", 1.5)],
    },
    # --- Entrees (served with rice & salad) ---
    {
        "name": "Garlic Butter Shrimp",
        "description": "A North Shore classic. Large shrimp sautéed in plenty of butter and fresh chopped garlic. Served with rice and salad.",
        "price_cents": 1800,
        "is_signature": True,
        "popularity_score": 9.5,
        "tags": [("fish", 2.0), ("savory", 2.0), ("umami", 1.5), ("comforting", 1.5), ("mid", 1.0)],
    },
    {
        "name": "BBQ Chicken",
        "description": "Boneless chicken thighs marinated in island spices and grilled with our house BBQ sauce. Served with rice and salad.",
        "price_cents": 1600,
        "is_signature": True,
        "popularity_score": 8.8,
        "tags": [("chicken", 2.0), ("savory", 2.0), ("comforting", 1.5), ("filling", 1.0), ("mid", 1.0)],
    },
    {
        "name": "Kalbi (Korean Short Ribs)",
        "description": "Tender beef short ribs marinated in a sweet and savory soy-ginger glaze, grilled to perfection. Served with rice and salad.",
        "price_cents": 1900,
        "is_signature": True,
        "popularity_score": 9.2,
        "tags": [("beef", 2.0), ("savory", 1.5), ("sweet", 1.0), ("umami", 1.5), ("filling", 2.0), ("premium", 1.0)],
    },
    {
        "name": "Salted Egg Yolk Shrimp",
        "description": "A rich, umami-packed favorite. Crispy shrimp coated in a savory cured egg yolk sauce. Served with rice and salad.",
        "price_cents": 1800,
        "is_signature": True,
        "popularity_score": 8.5,
        "tags": [("fish", 1.5), ("savory", 1.5), ("umami", 2.0), ("adventurous", 2.0), ("mid", 1.0)],
    },
    {
        "name": "Garlic Chicken",
        "description": "Crispy fried chicken chunks tossed in a savory and sweet garlic soy glaze. Served with rice and salad.",
        "price_cents": 1500,
        "is_signature": False,
        "popularity_score": 7.5,
        "tags": [("chicken", 1.5), ("savory", 1.5), ("comforting", 1.0), ("mid", 1.0)],
    },
    {
        "name": "Honey Coconut Shrimp",
        "description": "Crispy shrimp coated in a creamy, sweet tropical sauce with a hint of coconut. Served with rice and salad.",
        "price_cents": 1800,
        "is_signature": False,
        "popularity_score": 7.2,
        "tags": [("fish", 1.0), ("sweet", 2.0), ("adventurous", 1.5), ("mid", 1.0)],
    },
    {
        "name": "Pork Chop",
        "description": "Juicy pork chops simply seasoned and pan-fried until golden brown. Served with rice and salad.",
        "price_cents": 1600,
        "is_signature": False,
        "popularity_score": 7.0,
        "tags": [("pork", 1.5), ("savory", 1.5), ("filling", 1.5), ("comforting", 1.0), ("mid", 1.0)],
    },
    {
        "name": "Salt & Pepper Shrimp",
        "description": "Wok-tossed with fresh chili peppers, garlic, and sea salt for a crispy, spicy kick. Served with rice and salad.",
        "price_cents": 1700,
        "is_signature": False,
        "popularity_score": 7.8,
        "tags": [("fish", 1.5), ("spicy", 2.0), ("savory", 1.0), ("mid", 1.0)],
    },
    {
        "name": "Steak",
        "description": "Juicy slices of beef seared hot and served with rice and salad.",
        "price_cents": 2000,
        "is_signature": False,
        "popularity_score": 7.5,
        "tags": [("beef", 1.5), ("savory", 1.5), ("filling", 2.0), ("premium", 1.5)],
    },
    {
        "name": "Garlic Butter Fish Fillet",
        "description": "Tender white fish fillets pan-seared and smothered in our famous garlic butter sauce. Served with rice and salad.",
        "price_cents": 1700,
        "is_signature": False,
        "popularity_score": 7.3,
        "tags": [("fish", 2.0), ("savory", 1.5), ("comforting", 1.5), ("mid", 1.0)],
    },
    {
        "name": "Fried Rice",
        "description": "Wok-tossed jasmine rice with eggs, vegetables, and savory seasonings.",
        "price_cents": 1100,
        "is_signature": False,
        "popularity_score": 6.5,
        "tags": [("savory", 1.0), ("light", 1.0), ("budget", 1.5)],
    },
]
# fmt: on

QUIZ_QUESTIONS = [
    {
        "key": "diet",
        "prompt": "Any dietary restrictions?",
        "order_index": 0,
        "answers": [
            {"key": "no_restrictions", "label": "No restrictions", "order_index": 0},
            {"key": "vegetarian",      "label": "Vegetarian",      "order_index": 1},
            {"key": "vegan",           "label": "Vegan",           "order_index": 2},
            {"key": "gluten_free",     "label": "Gluten-free",     "order_index": 3},
        ],
    },
    {
        "key": "protein",
        "prompt": "What protein are you feeling?",
        "order_index": 1,
        "answers": [
            {"key": "chicken", "label": "Chicken",        "order_index": 0},
            {"key": "beef",    "label": "Beef",           "order_index": 1},
            {"key": "fish",    "label": "Shrimp or fish", "order_index": 2},
            {"key": "no_meat", "label": "No meat",        "order_index": 3},
        ],
    },
    {
        "key": "flavor",
        "prompt": "What flavor profile sounds good?",
        "order_index": 2,
        "answers": [
            {"key": "savory", "label": "Savory & umami", "order_index": 0},
            {"key": "spicy",  "label": "Spicy & bold",   "order_index": 1},
            {"key": "sweet",  "label": "Sweet & tropical","order_index": 2},
            {"key": "mild",   "label": "Mild & simple",  "order_index": 3},
        ],
    },
    {
        "key": "appetite",
        "prompt": "How hungry are you?",
        "order_index": 3,
        "answers": [
            {"key": "light",       "label": "Just a snack",         "order_index": 0},
            {"key": "hearty",      "label": "Full plate for me",    "order_index": 1},
            {"key": "adventurous", "label": "Surprise me",          "order_index": 2},
            {"key": "comforting",  "label": "Something comforting", "order_index": 3},
        ],
    },
    {
        "key": "budget",
        "prompt": "What's your budget?",
        "order_index": 4,
        "answers": [
            {"key": "budget",  "label": "Keep it under $13", "order_index": 0},
            {"key": "mid",     "label": "Mid-range ($13–$18)","order_index": 1},
            {"key": "splurge", "label": "I want to splurge",  "order_index": 2},
        ],
    },
]


async def seed(session: AsyncSession) -> None:
    result = await session.execute(select(Restaurant).where(Restaurant.slug == "osun-grill"))
    if result.scalar_one_or_none():
        print("Already seeded: O'Sun Grill")
        return

    restaurant = Restaurant(
        id=uuid.uuid4(),
        slug="osun-grill",
        name="O'Sun Grill",
        tagline="Hawaii plate lunches. Asian roots. Open late.",
        menu_url="https://www.osungrill.com/menu",
    )
    session.add(restaurant)
    await session.flush()

    tag_by_key: dict[str, Tag] = {}
    for t in TAGS:
        tag = Tag(id=uuid.uuid4(), **t)
        session.add(tag)
        tag_by_key[t["key"]] = tag
    await session.flush()

    for item_data in MENU_ITEMS:
        item_tags = item_data.pop("tags")
        item = MenuItem(id=uuid.uuid4(), restaurant_id=restaurant.id, **item_data)
        session.add(item)
        await session.flush()
        for tag_key, weight in item_tags:
            session.add(MenuItemTag(menu_item_id=item.id, tag_id=tag_by_key[tag_key].id, weight=weight))

    for q_data in QUIZ_QUESTIONS:
        answers = q_data.pop("answers")
        question = QuizQuestion(
            id=uuid.uuid4(),
            restaurant_id=None,
            key=q_data["key"],
            prompt=q_data["prompt"],
            order_index=q_data["order_index"],
        )
        session.add(question)
        await session.flush()
        for a_data in answers:
            session.add(QuizAnswer(id=uuid.uuid4(), question_id=question.id, **a_data))

    await session.commit()
    print("Seeded: O'Sun Grill")


async def main() -> None:
    async with AsyncSessionLocal() as session:
        await seed(session)


if __name__ == "__main__":
    asyncio.run(main())
