import dataclasses
from collections.abc import Callable, Awaitable

import discord.ext.commands

loan_interest_rate: float = 0.09 / 12  # Monthly interest rate
currency_name: str = "FoxCoins"
retirement_age: int = 65  # Age at which a member can retire
income_tax: float = 0.15  # Tax rate on income
sales_tax: float = 0.08375  # Sales tax rate on purchases
resale_multiplier: float = 0.8  # Multiplier for resale value of items


@dataclasses.dataclass
class ShopItem:
	"""
	Represents an item in the shop.
	Attributes:
		name (str): The name of the item.
		description (str): A brief description of the item.
		price (int): The price of the item in currency.
		stock (int): The number of items available in stock.
		perk (list[Callable[[discord.ext.commands.Context, discord.Member], Awaitable[None]]] | None): A list of
			async functions that will be called when the item is purchased. They should take a discord.Context and a
			discord.Member as parameters and return None.
	"""

	name: str
	description: str
	price: int
	stock: int
	perk: list[Callable[[discord.ext.commands.Context, discord.Member], Awaitable[None]]] | None


@dataclasses.dataclass
class HouseItem(ShopItem):
	"""
	Represents a house item in the shop.
	Includes additional attributes for house-specific features.
	Attributes:
		rent_cost (int): The cost of renting the house.
		rent_income (int): The income generated from renting the house.
	"""
	rent_cost: int
	rent_income: int

@dataclasses.dataclass
class BlackMarketItem(ShopItem):
	"""
	Represents an item in the black market.
	Black market items are not available in the regular shop and may have unique properties or effects.
	Attributes:
		name (str): The name of the black market item.
		description (str): A brief description of the item.
		price (int): The price of the item in currency.
		stock (int): The number of items available in stock.
		perk (list[Callable[[discord.ext.commands.Context, discord.Member], Awaitable[None]]] | None): A list of
			async functions that will be called when the item is purchased. They should take a discord.Context and a
			discord.Member as parameters and return None.
	"""
	resale_mult: float = 0.5  # Multiplier for resale value of black market items
	cops_risk: float = 0.1  # How likely it is to get caught when buying/selling this item
	scam_risk: float = 0.1  # How likely it is to be scammed when buying/selling this item
	trace_back: bool | float = True  # Whether the item can be traced back to the buyer or seller. This can also be a float denoting the chance of being traced back.

@dataclasses.dataclass
class ShopCategory:
	"""
	Represents a category of items in the shop.
	Attributes:
		name (str): The name of the category.
		description (str): A brief description of the category.
		items (list[ShopItem]): A list of ShopItems in this category.
	"""
	name: str
	description: str
	items: list[ShopItem]


def get_default_profile(member_id: int | str) -> dict[str, int | str | dict[str, int]]:
	"""
	Generates a default currency profile for a new member.
	:param member_id: The ID of the member for whom to create the profile.
	:return: A dictionary containing the default profile data.
	"""
	default = {
		'user_id':      str(member_id),
		'wallet':       1_000,
		'bank':         0,
		'income':       0,
		'debt':         0,
		'credit_score': 400,  # Starting credit score
		'age':          18,  # Starting age
		'inventory':    {},
	}
	return default
