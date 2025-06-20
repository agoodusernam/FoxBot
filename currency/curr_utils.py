import discord

from utils import db_stuff


def create_new_profile(member: discord.Member):
	new_data = {
		'user_id':          str(member.id),
		'money':         0,
		'bank':          0,
		'income':        0,
		'inventory':    {},
	}

	db_stuff.send_to_db(collection_name='currency', data=new_data)
	return new_data

def get_profile(member: discord.Member) -> dict:
	return db_stuff.get_from_db(collection_name = 'currency', query={'user_id': str(member.id)})

def set_money(member: discord.Member, amount: int) -> None:
	profile = get_profile(member)
	if not profile:
		profile = create_new_profile(member)

	profile['money'] = amount
	db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'money': amount})

def set_bank(member: discord.Member, amount: int) -> None:
	profile = get_profile(member)
	if not profile:
		profile = create_new_profile(member)

	profile['bank'] = amount
	db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'bank': amount})

def set_income(member: discord.Member, amount: int) -> None:
	profile = get_profile(member)
	if not profile:
		profile = create_new_profile(member)

	profile['income'] = amount
	db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'income': amount})

def add_money(member: discord.Member, amount: int) -> None:
	profile = get_profile(member)
	if not profile:
		profile = create_new_profile(member)

	profile['money'] += amount
	db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'money': profile['money']})

def add_bank(member: discord.Member, amount: int) -> None:
	profile = get_profile(member)
	if not profile:
		profile = create_new_profile(member)

	profile['bank'] += amount
	db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'bank': profile['bank']})

def add_income(member: discord.Member, amount: int) -> None:
	profile = get_profile(member)
	if not profile:
		profile = create_new_profile(member)

	profile['income'] += amount
	db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'income': profile['income']})

def add_item(member: discord.Member, item: str, amount: int = 1) -> None:
	profile = get_profile(member)
	if not profile:
		profile = create_new_profile(member)

	if item not in profile['inventory']:
		profile['inventory'][item] = 0

	profile['inventory'][item] += amount
	db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'inventory': profile['inventory']})

def remove_item(member: discord.Member, item: str, amount: int = 1) -> None:
	profile = get_profile(member)
	if not profile:
		profile = create_new_profile(member)

	if item in profile['inventory'] and profile['inventory'][item] >= amount:
		profile['inventory'][item] -= amount
		if profile['inventory'][item] <= 0:
			del profile['inventory'][item]
		db_stuff.edit_db_entry('currency', {'user_id': str(member.id)}, {'inventory': profile['inventory']})
	else:
		print(f"Item {item} not found or insufficient quantity in inventory for user {member.id}.")
