import dataclasses
from collections.abc import Callable, Awaitable

import discord.ext.commands

loan_interest_rate: float = 0.09 / 12  # Monthly interest rate
currency_name: str = "FoxCoins"
retirement_age: int = 65 * 12  # Age at which a member can retire
income_tax: float = 0.15  # Tax rate on income
sales_tax: float = 0.08375  # Sales tax rate on purchases


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
		resale_mult (float): Multiplier for resale value of black market items.
		cops_risk (float): How likely it is to get caught when buying/selling this item.
		scam_risk (float): How likely it is to be scammed when buying/selling this item.
		trace_back (bool | float): Whether the item can be traced back to the buyer or seller. This can also be a
		float representing the chance of being traced back.
	"""
	resale_mult: float = 0.5
	cops_risk: float = 0.1
	scam_risk: float = 0.1
	trace_back: bool | float = True


@dataclasses.dataclass
class GunItem(BlackMarketItem):
	"""
	Represents a gun item in the black market.
	Gun items may have additional properties or effects compared to regular black market items.
	Attributes:
		name (str): The name of the gun item.
		description (str): A brief description of the gun item.
		price (int): The price of the gun item in currency.
		stock (int): The number of gun items available in stock.
		perk (list[Callable[[discord.ext.commands.Context, discord.Member], Awaitable[None]]] | None): A list of
			async functions that will be called when the gun item is purchased. They should take a discord.Context and a
			discord.Member as parameters and return None.
		resale_mult (float): Multiplier for resale value of gun items.
		cops_risk (float): How likely it is to get caught when buying/selling this gun item.
		scam_risk (float): How likely it is to be scammed when buying/selling this gun item.
		trace_back (bool | float): Whether the gun item can be traced back to the buyer or seller. This can also be a
			float representing the chance of being traced back.
		suppressed (bool): Whether the gun is suppressed or not, affects cops_risk and trace_back. cops risk goes up
		by 10% and trace back chance goes down by 10% if suppressed.
	"""
	suppressed: bool = False

@dataclasses.dataclass
class DrugItem(BlackMarketItem):
	"""
	Represents a drug item in the black market.
	Drugs may have additional effects or properties compared to regular black market items.
	Attributes:
		name (str): The name of the drug item.
		description (str): A brief description of the drug item.
		price (int): The price of the drug item in currency.
		stock (int): The number of drug items available in stock.
		perk (list[Callable[[discord.ext.commands.Context, discord.Member], Awaitable[None]]] | None): A list of
			async functions that will be called when the drug item is purchased. They should take a discord.Context and a
			discord.Member as parameters and return None.
		resale_mult (float): Multiplier for resale value of drug items.
		cops_risk (float): How likely it is to get caught when buying/selling this drug item.
		scam_risk (float): How likely it is to be scammed when buying/selling this drug item.
		trace_back (bool | float): Whether the drug item can be traced back to the buyer or seller. This can also be a
			float representing the chance of being traced back.
		income_multiplier (float): Multiplier for income generated from working while under using this drug.
		work_catch_risk (float): Risk of getting caught while working under the influence of this drug.
		uses (int): Number of uses before the drug item is consumed.
		od_chance (float): Chance of overdosing when using this drug item.
	"""
	income_multiplier: float = 0.5
	work_catch_risk: float = 0.1
	uses: int = 1
	od_chance: float = 0.05


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

	def item_names(self) -> list[str]:
		"""
		Returns a list of item names in this category.
		:return: A list of item names.
		"""
		return [item.name for item in self.items]


@dataclasses.dataclass
class BlackMarketCategory:
	"""
	Represents a category of items in the black market.
	Attributes:
		name (str): The name of the black market category.
		description (str): A brief description of the black market category.
		items (list[BlackMarketItem]): A list of BlackMarketItems in this category.
	"""
	name: str
	description: str
	items: list[BlackMarketItem]


def get_default_profile(member_id: int | str) -> dict[str, int | float | str | dict[str, int]]:
	"""
	Generates a default currency profile for a new member.
	:param member_id: The ID of the member for whom to create the profile.
	:return: A dictionary containing the default profile data.
	"""
	default = {
		'user_id':          str(member_id),
		'wallet':           1_000,
		'bank':             0,
		'work_income':      0,
		'other_income':     0,
		'next_income_mult': 1.0,
		'work_experience':  0,  # Experience in current job, will increase income
		'fire_risk':        0.0,  # Risk of being fired from work, will be increased by certain items or perks
		'debt':             0,
		'credit_score':     400,  # Starting credit score
		'age':              18 * 12,  # Starting age (in months)
		'inventory':        {},
		'illegal_items':    {},
	}
	return default
