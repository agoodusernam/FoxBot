import discord

from utils import db_stuff
from currency.curr_config import get_default_profile


def create_new_profile(member: discord.Member):
	new_data = get_default_profile(member.id)
	db_stuff.send_to_db(collection_name='currency', data=new_data)
	return new_data


def get_profile(member: discord.Member) -> dict[str, int | str | dict[str, int]]:
	profile_ = db_stuff.get_from_db(collection_name='currency', query={'user_id': str(member.id)})
	if not profile_ or profile_ is None:
		return create_new_profile(member)
	return profile_


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

	profile['income'] = amount
	db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'income': amount})


def set_debt(member: discord.Member, amount: int) -> None:
	profile = get_profile(member)

	profile['debt'] = amount
	db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'debt': amount})

def set_credit_score(member: discord.Member, score: int) -> None:
	profile = get_profile(member)

	profile['credit_score'] = score
	db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'credit_score': score})


def update_inventory(member: discord.Member, item: str, amount: int) -> None:
	profile = get_profile(member)

	profile['inventory'][item] = amount

	db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'inventory': profile['inventory']})


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


def calculate_max_loan(profile: dict[str, int | str | dict[str, int]]) -> int:
	"""
	Calculates the maximum loan amount based on the member's income, debt, and credit score.
	:param profile: The Discord member's profile for whom to calculate the maximum loan.
	:return: The maximum loan amount.
	"""
	if profile['debt'] > 0:
		return 0
	credit_factor = 0.5 + (profile["credit_score"] / 800)
	return min(int(profile['income'] * 12 * credit_factor) + 10_000, 1_000_000)
