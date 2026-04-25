import discord

from currency.currency_types import Profile, ShopItem
from utils import db_stuff

cached_profiles: dict[str, Profile] = {}

async def get_profile(user_id: int | str | discord.User | discord.Member) -> Profile:
    key: str
    if isinstance(user_id, int):
        key = str(user_id)
    elif isinstance(user_id, (discord.User, discord.Member)):
        key = str(user_id.id)
    else:
        key = user_id
    if key not in cached_profiles:
        cached_profiles[key] = await Profile.fetch_from_user_id(key)
    return cached_profiles[key]

async def get_stock(item: ShopItem) -> int:
    """
    Fetches the stock of a specific item from the currency collection.
    :param item: The name of the item to check stock for.
    :return: The stock amount of the item, or 0 if not found.
    """
    item_from_db = await db_stuff.get_from_db(collection_name='shop_items', query={'item_name': item.name})
    if item_from_db is None or item_from_db is False:
        await db_stuff.send_to_db(collection_name='shop_items', data={"item_name": item.name, "stock": item.stock})
        return item.stock
    return item_from_db['stock']


async def set_stock(item: ShopItem, amount: int) -> None:
    """
    Sets the stock of a specific item in the currency collection.
    :param item: The ShopItem whose stock is to be set.
    :param amount: The new stock amount to set for the item.
    """
    await db_stuff.edit_db_entry('shop_items', {'item_name': item.name}, {'stock': amount})
    return

async def get_top_balances(limit: int = 10) -> list[dict[str, int]] | None:
    """
    Fetches the top balances from the currency collection.
    :param limit: The number of top balances to fetch.
    :return: A list of dictionaries containing user IDs and their wallet balances.
    """
    top_balances = await db_stuff.get_many_from_db(collection_name='currency', query={}, sort_by='wallet',
                                             direction="desc", limit=limit)
    if top_balances is None:
        return None
    return [{'user_id': profile['user_id'], 'wallet': profile['wallet']} for profile in top_balances]
