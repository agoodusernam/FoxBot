import discord

from utils import db_stuff


def create_new_profile(member: discord.Member):
	new_data = {
		'user_id':      str(member.id),
		'wallet':       1_000,
		'bank':         0,
		'income':       0,
		'debt':         0,
		'credit_score': 400,  # Starting credit score
		'inventory':    {},
	}

	db_stuff.send_to_db(collection_name = 'currency', data = new_data)
	return new_data


def get_profile(member: discord.Member) -> dict:
	profile_ = db_stuff.get_from_db(collection_name = 'currency', query = {'user_id': str(member.id)})
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
	top_balances = db_stuff.get_many_from_db(collection_name = 'currency', query = {}, sort_by = 'wallet',
											 direction = "d",
											 limit = limit)
	return [{'user_id': profile['user_id'], 'wallet': profile['wallet']} for profile in top_balances]


def calculate_max_loan(member: discord.Member) -> int:
	"""
	Calculates the maximum loan amount based on the member's income and debt.
	:param member: The Discord member for whom to calculate the maximum loan.
	:return: The maximum loan amount.
	"""
	profile = get_profile(member)
	if profile['debt'] > 0:
		return 0
	credit_factor = 0.5 + (profile["credit_score"] / 800)
	return int(profile['income'] * credit_factor * 12) + 10_000
