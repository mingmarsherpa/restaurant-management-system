import asyncio

from sqlalchemy import select

from restaurant_api.database import AsyncSessionLocal
from restaurant_api.models.menu import Item, OptionGroup, Option, ItemOption


# Base prices and option prices are written in rupees here.
# The script converts them to paisa before saving.

MENU = [
    {
        "name": "Momo",
        "price": 150,
        "groups": {
            "Filling": {"Veg": 0, "Buff": 20, "Chicken": 50},
            "Cooking Style": {
                "Steamed": 0, "Fried": 20, "Kothey": 20
            },
        },
    },
    {
        "name": "Chowmein",
        "price": 130,
        "groups": {
            "Protein": {"Veg": 0, "Egg": 20, "Buff": 30, "Chicken": 40},
        },
    },
    {
        "name": "Thukpa",
        "price": 160,
        "groups": {
            "Protein": {"Veg": 0, "Buff": 30, "Chicken": 50},
            "Spice Level": {"Mild": 0, "Medium": 0, "Hot": 0},
        },
    },
    {
        "name": "Chicken Burger",
        "price": 250,
        "groups": {
            "Add-ons": {"Cheese": 40, "Extra Patty": 100},
        },
    },
    {
        "name": "Fried Rice",
        "price": 140,
        "groups": {
            "Protein": {"Veg": 0, "Egg": 20, "Buff": 30, "Chicken": 40},
        },
    },
    {
        "name": "Sekuwa",
        "price": 280,
        "groups": {
            "Serving": {"Half": 0, "Full": 200},
            "Spice Level": {"Mild": 0, "Medium": 0, "Hot": 0},
        },
    },
    {
        "name": "Chicken Pizza",
        "price": 350,
        "groups": {
            "Size": {"Regular": 0, "Large": 150},
            "Add-ons": {"Extra Cheese": 50},
        },
    },
    {
        "name": "Chicken Wings",
        "price": 240,
        "groups": {
            "Sauce": {"Plain": 0, "BBQ": 20, "Spicy": 20},
        },
    },
    {
        "name": "Aloo Sadeko",
        "price": 100,
        "groups": {
            "Spice Level": {"Mild": 0, "Medium": 0, "Hot": 0},
        },
    },
    {
        "name": "Spring Rolls",
        "price": 120,
        "groups": {
            "Sauce": {"Tomato": 0, "Spicy": 0},
        },
    },
    {
        "name": "Milk Tea",
        "price": 40,
        "groups": {
            "Size": {"Regular": 0, "Large": 20},
            "Sweetness": {"Normal": 0, "Less Sugar": 0},
        },
    },
    {
        "name": "Lemon Soda",
        "price": 80,
        "groups": {
            "Sweetness": {"Normal": 0, "Less Sugar": 0},
            "Ice": {"With Ice": 0, "No Ice": 0},
        },
    },
]


async def seed_menu():
    async with AsyncSessionLocal() as session:
        # Prevent accidentally inserting duplicate menu items.
        existing = await session.scalar(select(Item.id).limit(1))

        if existing is not None:
            print("Menu already contains items. Seed skipped.")
            return

        groups = {}
        options = {}

        # Create shared groups and options only once.
        for entry in MENU:
            for group_name, choices in entry["groups"].items():
                if group_name not in groups:
                    group = OptionGroup(name=group_name)
                    session.add(group)
                    await session.flush()
                    groups[group_name] = group

                group = groups[group_name]

                for option_name in choices:
                    key = (group_name, option_name)

                    if key not in options:
                        option = Option(
                            name=option_name,
                            group=group,
                        )
                        session.add(option)
                        await session.flush()
                        options[key] = option

        # Create each item and its item-specific prices.
        for entry in MENU:
            item = Item(
                name=entry["name"],
                base_price_paisa=entry["price"] * 100,
            )

            for group_name, choices in entry["groups"].items():
                item.option_groups.append(groups[group_name])

                for option_name, extra_rupees in choices.items():
                    item_option = ItemOption(
                        option=options[(group_name, option_name)],
                        extra_price_paisa=extra_rupees * 100,
                    )
                    item.item_options.append(item_option)

            session.add(item)

        await session.commit()
        print(f"Successfully seeded {len(MENU)} menu items.")


if __name__ == "__main__":
    asyncio.run(seed_menu())