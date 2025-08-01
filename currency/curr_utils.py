from typing import TypedDict, cast

import discord

from currency import shop_items
from currency.curr_config import get_default_profile, ShopItem
from utils import db_stuff
from utils.db_stuff import get_from_db


class Profile(TypedDict):
    user_id: str
    wallet: int
    bank: int
    work_income: int
    work_str: str
    work_tree: str
    other_income: int
    next_income_mult: float
    work_experience: int
    qualifications: tuple[str, str]
    fire_risk: float
    debt: int
    credit_score: int
    age: int  # Age in months
    inventory: dict[str, int]
    illegal_items: dict[str, int]


def create_new_profile(member: discord.Member) -> Profile:
    new_data = get_default_profile(member.id)
    db_stuff.send_to_db(collection_name='currency', data=dict(new_data))
    return cast(Profile, new_data)


def get_profile(member: discord.Member) -> Profile:
    profile_ = db_stuff.get_from_db(collection_name='currency', query={'user_id': str(member.id)})
    if not profile_ or profile_ is None:
        return create_new_profile(member)
    return cast(Profile, profile_)


def get_lottery_tickets(member: discord.Member) -> int:
    """
    Retrieves the number of lottery tickets a member has.
    :param member: The Discord member whose lottery tickets are being checked.
    :return: The number of lottery tickets the member has.
    """
    lottery_profile = db_stuff.get_from_db(collection_name='lottery', query={'user_id': str(member.id)})
    if lottery_profile is None:
        return 0
    return lottery_profile['lottery_tickets']


def set_lottery_tickets(member: discord.Member, amount: int) -> None:
    """
    Sets the number of lottery tickets a member has.
    :param member: The Discord member whose lottery tickets are being set.
    :param amount: The number of lottery tickets to set.
    """
    db_stuff.del_db_entry(collection_name='lottery', query={'user_id': str(member.id)})
    new_data = {
        'user_id':         str(member.id),
        'lottery_tickets': amount
    }
    db_stuff.send_to_db(collection_name='lottery', data=new_data)


def delete_all_lottery_tickets() -> int:
    """
    Deletes all lottery tickets from the database.
    :return: The number of deleted lottery tickets.
    """
    return db_stuff.del_many_db_entries(collection_name='lottery', query={})


def delete_profile(member: discord.Member) -> None:
    """
    Deletes the currency profile of a specific member.
    :param member: The Discord member whose profile is to be deleted.
    """
    db_stuff.del_db_entry(collection_name='currency', query={'user_id': str(member.id)})
    return


def user_has_gun(profile: dict[str, int | float | str | dict[str, int]]) -> bool:
    """
    Checks if a member has a gun in their inventory.
    :param profile: The profile of the member to check.
    :return: True if the member has a gun, False otherwise.
    """
    return any(map(lambda v: v in shop_items.all_guns, list(profile['illegal_items'].keys())))


def get_stock(item: ShopItem) -> int:
    """
    Fetches the stock of a specific item from the currency collection.
    :param item: The name of the item to check stock for.
    :return: The stock amount of the item, or 0 if not found.
    """
    item_from_db = get_from_db(collection_name='shop_items', query={'item_name': item.name})
    if item_from_db is None or item_from_db is False:
        db_stuff.send_to_db(collection_name='shop_items', data={"item_name": item.name, "stock": item.stock})
        return item.stock
    return item_from_db['stock']


def set_stock(item: ShopItem, amount: int) -> None:
    """
    Sets the stock of a specific item in the currency collection.
    :param item: The ShopItem whose stock is to be set.
    :param amount: The new stock amount to set for the item.
    """
    db_stuff.edit_db_entry('shop_items', {'item_name': item.name}, {'stock': amount})
    return


def set_wallet(member: discord.Member, amount: int) -> None:
    profile = get_profile(member)
    
    profile['wallet'] = amount
    db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'wallet': amount})


def set_bank(member: discord.Member, amount: int) -> None:
    profile = get_profile(member)
    
    profile['bank'] = amount
    db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'bank': amount})


def set_income(member: discord.Member, amount: int) -> None:
    profile = get_profile(member)
    
    profile['work_income'] = amount
    db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'work_income': amount})


def set_other_income(member: discord.Member, amount: int) -> None:
    profile = get_profile(member)
    
    profile['other_income'] = amount
    db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'other_income': amount})


def set_next_income_multiplier(member: discord.Member, multiplier: float) -> None:
    profile = get_profile(member)
    
    profile['next_income_mult'] = multiplier
    db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'next_income_mult': multiplier})


def set_fire_risk(member: discord.Member, risk: float) -> None:
    profile = get_profile(member)
    
    profile['fire_risk'] = risk
    db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'fire_risk': risk})


def set_debt(member: discord.Member, amount: int) -> None:
    profile = get_profile(member)
    
    profile['debt'] = amount
    db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'debt': amount})


def set_credit_score(member: discord.Member, score: int) -> None:
    profile = get_profile(member)
    
    profile['credit_score'] = score
    db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'credit_score': score})


def add_lottery_tickets(member: discord.Member, amount: int) -> None:
    """
    Adds a specified amount of lottery tickets to the member's profile.
    :param member: The Discord member whose lottery tickets are being updated.
    :param amount: The number of lottery tickets to add.
    """
    tickets = get_lottery_tickets(member)
    db_stuff.edit_db_entry('currency', {'user_id': str(member.id)},
                           {'lottery_tickets': tickets + amount})


def inc_age(member: discord.Member) -> None:
    """
    Increments the age of the member in their currency profile.
    :param member: The Discord member whose age is to be incremented.
    """
    profile = get_profile(member)
    
    profile['age'] += 1
    db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'age': profile['age']})


def set_experience(member: discord.Member, amount: int) -> None:
    """
    Sets the work experience of the member in their currency profile.
    :param member: The Discord member whose work experience is to be set.
    :param amount: The amount of work experience to set.
    """
    profile = get_profile(member)
    
    profile['work_experience'] = amount
    db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'work_experience': amount})


def add_to_inventory(member: discord.Member, item: str, amount: int, illegal: bool = False) -> None:
    """
    Adds a specified amount of an item to the member's inventory.
    :param member: The Discord member whose inventory is being updated.
    :param item: The name of the item to add.
    :param amount: The amount of the item to add.
    :param illegal: Whether the item is illegal (default is False).
    """
    profile = get_profile(member)
    
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
        
        db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'illegal_items': profile['illegal_items']})
    else:
        # Update the database with the new inventory
        db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'inventory': profile['inventory']})


def set_inventory(member: discord.Member, item: str, amount: int) -> None:
    profile = get_profile(member)
    
    profile['inventory'][item] = amount
    
    db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'inventory': profile['inventory']})


def set_illegal_items(member: discord.Member, item: str, amount: int) -> None:
    """
    Sets the amount of an illegal item in the member's inventory.
    :param member: The Discord member whose illegal items are being updated.
    :param item: The name of the illegal item to set.
    :param amount: The amount of the illegal item to set.
    """
    profile = get_profile(member)
    
    profile['illegal_items'][item] = amount
    
    db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'illegal_items': profile['illegal_items']})


def remove_from_inventory(member: discord.Member, item: str) -> None:
    """
    Removes an item from the member's inventory.
    :param member: The Discord member whose inventory is being updated.
    :param item: The name of the item to remove.
    """
    profile = get_profile(member)
    
    if item in profile['inventory']:
        del profile['inventory'][item]
    
    db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'inventory': profile['inventory']})


def remove_illegal_item(member: discord.Member, item: str) -> None:
    """
    Removes an illegal item from the member's inventory.
    :param member: The Discord member whose illegal items are being updated.
    :param item: The name of the illegal item to remove.
    """
    profile = get_profile(member)
    
    if item in profile['illegal_items']:
        del profile['illegal_items'][item]
    
    db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'illegal_items': profile['illegal_items']})


def clear_inventory(member: discord.Member) -> None:
    """
    Clears the entire inventory of the member.
    :param member: The Discord member whose inventory is being cleared.
    """
    profile = get_profile(member)
    
    profile['inventory'] = {}
    
    db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'inventory': profile['inventory']})


def clear_illegal_items(member: discord.Member) -> None:
    """
    Clears all illegal items from the member's inventory.
    :param member: The Discord member whose illegal items are being cleared.
    """
    profile = get_profile(member)
    
    profile['illegal_items'] = {}
    
    db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'illegal_items': profile['illegal_items']})


def get_top_balances(limit: int = 10) -> list[dict[str, int]]:
    """
    Fetches the top balances from the currency collection.
    :param limit: The number of top balances to fetch.
    :return: A list of dictionaries containing user IDs and their wallet balances.
    """
    top_balances = db_stuff.get_many_from_db(collection_name='currency', query={}, sort_by='wallet',
                                             direction="d",
                                             limit=limit)
    return [{'user_id': profile['user_id'], 'wallet': profile['wallet']} for profile in top_balances]


def calculate_max_loan(profile: Profile) -> int:
    """
    Calculates the maximum loan amount based on the member's income, debt, and credit score.
    :param profile: The Discord member's profile for whom to calculate the maximum loan.
    :return: The maximum loan amount.
    """
    if profile['debt'] > 0:
        return 0
    credit_factor = 0.5 + (profile["credit_score"] / 800)
    return min(int(profile['work_income'] * 12 * credit_factor) + 10_000, 1_000_000)


def get_shop_item(item_name: str) -> ShopItem | None:
    """
    Retrieves a shop item by its name from the database.
    :param item_name: The name of the shop item to retrieve.
    :return: The ShopItem object if found, otherwise None.
    """
    return next((i for i in shop_items.all_items if i.name.lower() == item_name), None)
