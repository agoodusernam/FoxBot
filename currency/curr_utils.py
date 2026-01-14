from __future__ import annotations

from typing import cast, Any
import discord

from currency import shop_items
from currency.curr_config import get_default_profile, ShopItem, Profile
from currency.job_utils import Job
from utils import db_stuff


async def create_new_profile(member: discord.abc.Snowflake) -> Profile:
    new_data = get_default_profile(member.id)
    await db_stuff.send_to_db(collection_name='currency', data=dict(new_data))
    return new_data


async def get_profile(member: discord.abc.Snowflake) -> Profile:
    user_profile: dict[str, Any] | None = await db_stuff.get_from_db(collection_name='currency', query={'user_id': str(
            member.id)})
    if user_profile is None:
        return await create_new_profile(member)
    return cast(Profile, cast(object, user_profile))


async def set_profile(member: discord.abc.Snowflake, profile: Profile) -> None:
    await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, dict(profile))
    return


async def get_lottery_tickets(member: discord.abc.Snowflake) -> int:
    """
    Retrieves the number of lottery tickets a member has.
    :param member: The Discord member whose lottery tickets are being checked.
    :return: The number of lottery tickets the member has.
    """
    lottery_profile = await db_stuff.get_from_db(collection_name='lottery', query={'user_id': str(member.id)})
    if lottery_profile is None:
        return 0
    return lottery_profile['lottery_tickets']


async def set_lottery_tickets(member: discord.abc.Snowflake, amount: int) -> None:
    """
    Sets the number of lottery tickets a member has.
    :param member: The Discord member whose lottery tickets are being set.
    :param amount: The number of lottery tickets to set.
    """
    await db_stuff.del_db_entry(collection_name='lottery', query={'user_id': str(member.id)})
    new_data = {
        'user_id':         str(member.id),
        'lottery_tickets': amount
    }
    await db_stuff.send_to_db(collection_name='lottery', data=new_data)


async def delete_all_lottery_tickets() -> int | None:
    """
    Deletes all lottery tickets from the database.
    :return: The number of deleted lottery tickets.
    """
    return await db_stuff.del_many_db_entries(collection_name='lottery', query={})


async def delete_profile(member: discord.abc.Snowflake) -> bool:
    """
    Deletes the currency profile of a specific member.
    :param member: The Discord member whose profile is to be deleted.
    """
    return await db_stuff.del_db_entry(collection_name='currency', query={'user_id': str(member.id)})


async def user_has_gun(profile: Profile) -> bool:
    """
    Checks if a member has a gun in their inventory.
    :param profile: The profile of the member to check.
    :return: True if the member has a gun, False otherwise.
    """
    return any(map(lambda v: v in shop_items.all_guns, list(profile['illegal_items'].keys())))


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


async def set_wallet(member: discord.abc.Snowflake, amount: int) -> None:
    await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'wallet': amount})


async def set_bank(member: discord.abc.Snowflake, amount: int) -> None:
    await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'bank': amount})


async def set_income(member: discord.abc.Snowflake, amount: int) -> None:
    await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'work_income': amount})


async def set_other_income(member: discord.abc.Snowflake, amount: int) -> None:
    await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'other_income': amount})


async def set_next_income_multiplier(member: discord.abc.Snowflake, multiplier: float) -> None:
    await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'next_income_mult': multiplier})


async def set_fire_risk(member: discord.abc.Snowflake, risk: float) -> None:
    await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'fire_risk': risk})


async def set_debt(member: discord.abc.Snowflake, amount: int) -> None:
    await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'debt': amount})


async def set_credit_score(member: discord.abc.Snowflake, score: int) -> None:
    await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'credit_score': score})


async def add_lottery_tickets(member: discord.abc.Snowflake, amount: int) -> None:
    """
    Adds a specified amount of lottery tickets to the member's profile.
    :param member: The Discord member whose lottery tickets are being updated.
    :param amount: The number of lottery tickets to add.
    """
    tickets = await get_lottery_tickets(member)
    await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)},
                           {'lottery_tickets': tickets + amount})


async def inc_age(member: discord.abc.Snowflake) -> None:
    """
    Increments the age of the member in their currency profile.
    :param member: The Discord member whose age is to be incremented.
    """
    profile = await get_profile(member)
    
    profile['age'] += 1
    await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'age': profile['age']})


async def set_experience(member: discord.abc.Snowflake, amount: int) -> None:
    """
    Sets the work experience of the member in their currency profile.
    :param member: The Discord member whose work experience is to be set.
    :param amount: The amount of work experience to set.
    """
    await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'work_experience': amount})


async def set_job(member: discord.abc.Snowflake, job: Job, income: int) -> None:
    """
    Sets the job of the member in their currency profile.
    :param member: The Discord member whose job is to be set.
    :param job: The Job object representing the new job.
    :param income: The income associated with the new job.
    """
    profile = await get_profile(member)
    
    profile['work_str'] = job.name
    profile['work_income'] = income
    profile['work_tree'] = job.tree
    await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, dict(profile))


async def reset_job(member: discord.abc.Snowflake) -> None:
    """
    Resets the job of the member to 'Unemployed' in their currency profile.
    :param member: The Discord member whose job is to be reset.
    """
    profile = await get_profile(member)
    
    profile['work_str'] = 'Unemployed'
    profile['work_income'] = 0
    profile['work_tree'] = "None"
    await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, dict(profile))


async def add_to_inventory(member: discord.abc.Snowflake, item: str, amount: int, illegal: bool = False) -> None:
    """
    Adds a specified amount of an item to the member's inventory.
    :param member: The Discord member whose inventory is being updated.
    :param item: The name of the item to add.
    :param amount: The amount of the item to add.
    :param illegal: Whether the item is illegal (default is False).
    """
    profile = await get_profile(member)
    
    if item in profile['inventory']:
        profile['inventory'][item] += amount
    else:
        profile['inventory'][item] = amount
    
    if illegal:
        if 'illegal_items' not in profile:
            profile['illegal_items'] = {}
        if item in profile['illegal_items']:
            profile['illegal_items'][item] += amount
        else:
            profile['illegal_items'][item] = amount
        
        await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'illegal_items': profile['illegal_items']})
    else:
        # Update the database with the new inventory
        await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'inventory': profile['inventory']})


async def set_inventory(member: discord.abc.User, item: str, amount: int) -> None:
    profile = await get_profile(member)
    
    profile['inventory'][item] = amount
    
    await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'inventory': profile['inventory']})


async def set_illegal_items(member: discord.abc.Snowflake, item: str, amount: int) -> None:
    """
    Sets the amount of an illegal item in the member's inventory.
    :param member: The Discord member whose illegal items are being updated.
    :param item: The name of the illegal item to set.
    :param amount: The amount of the illegal item to set.
    """
    profile = await get_profile(member)
    
    profile['illegal_items'][item] = amount
    
    await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'illegal_items': profile['illegal_items']})


async def remove_from_inventory(member: discord.abc.Snowflake, item: str) -> None:
    """
    Removes an item from the member's inventory.
    :param member: The Discord member whose inventory is being updated.
    :param item: The name of the item to remove.
    """
    profile = await get_profile(member)
    
    if item in profile['inventory']:
        del profile['inventory'][item]
    
    await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'inventory': profile['inventory']})


async def remove_illegal_item(member: discord.abc.Snowflake, item: str) -> None:
    """
    Removes an illegal item from the member's inventory.
    :param member: The Discord member whose illegal items are being updated.
    :param item: The name of the illegal item to remove.
    """
    profile = await get_profile(member)
    
    if item in profile['illegal_items']:
        del profile['illegal_items'][item]
    
    await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'illegal_items': profile['illegal_items']})


async def clear_inventory(member: discord.abc.Snowflake) -> None:
    """
    Clears the entire inventory of the member.
    :param member: The Discord member whose inventory is being cleared.
    """
    profile = await get_profile(member)
    
    profile['inventory'] = {}
    
    await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'inventory': profile['inventory']})


async def clear_illegal_items(member: discord.abc.Snowflake) -> None:
    """
    Clears all illegal items from the member's inventory.
    :param member: The Discord member whose illegal items are being cleared.
    """
    profile = await get_profile(member)
    
    profile['illegal_items'] = {}
    
    await db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'illegal_items': profile['illegal_items']})


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


async def calculate_max_loan(profile: Profile) -> int:
    """
    Calculates the maximum loan amount based on the member's income, debt, and credit score.
    :param profile: The Discord member's profile for whom to calculate the maximum loan.
    :return: The maximum loan amount.
    """
    if profile['debt'] > 0:
        return 0
    credit_factor = 0.5 + (profile["credit_score"] / 800)
    return min(int(profile['work_income'] * 12 * credit_factor) + 10_000, 1_000_000)


async def get_shop_item(item_name: str) -> ShopItem | None:
    """
    Retrieves a shop item by its name from the database.
    :param item_name: The name of the shop item to retrieve.
    :return: The ShopItem object if found, otherwise None.
    """
    return next((i for i in shop_items.all_items if i.name.lower() == item_name), None)
