from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any
import discord

from currency import shop_items
from currency.currency_types import Job, Profile, DBProfile
from utils import db_stuff


def validate_db_profile(profile: Mapping[str, Any]) -> DBProfile:
    return DBProfile(
            user_id=profile['user_id'],
            wallet=profile['wallet'],
            bank=profile['bank'],
            work_income=profile['work_income'],
            work_str=profile['work_str'],
            other_income=profile['other_income'],
            next_income_mult=profile['next_income_mult'],
            work_experience=profile['work_experience'],
            school_qualification=profile['school_qualification'],
            security_clearance=profile['security_clearance'],
            fire_chance=profile['fire_chance'],
            debt=profile['debt'],
            credit_score=profile['credit_score'],
            age=profile['age'],
            lottery_tickets=profile['lottery_tickets'],
            inventory=profile['inventory'],
            illegal_items=profile['illegal_items']
            )

def user_has_gun(profile: Profile) -> bool:
    """
    Checks if a member has a gun in their inventory.
    :param profile: The profile of the member to check.
    :return: True if the member has a gun, False otherwise.
    """
    return any(map(lambda v: v in shop_items.all_guns, list(profile.illegal_items.keys())))


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
                                             direction="d", limit=limit)
    if top_balances is None:
        return None
    return [{'user_id': profile['user_id'], 'wallet': profile['wallet']} for profile in top_balances]
