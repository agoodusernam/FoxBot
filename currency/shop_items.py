from curr_config import ShopItem, ShopCategory, HouseItem
import perks
from currency.curr_config import BlackMarketItem

CIVILIAN_GUN_RESALE_MULT = 0.7

# Shop Items

# Special Items
private_vc = ShopItem(
	name="Private VC",
	description="A private voice channel for you and your friends.",
	price=10_000,
	stock=-1,
	perk=[perks.create_private_vc]  # Duration in days
)

rich_role = ShopItem(
	name="Rich Role",
	description="A special role for those who are very rich.",
	price=1_000_000,
	stock=-1,
	perk=[perks.give_rich_role]
)

send_announce = ShopItem(
	name="Send Announcement",
	description="Allows you to send an announcement in the server.",
	price=100_000,
	stock=-1,
	perk=[perks.send_announcement]
)

special_perks = ShopCategory(
	name="Special Items",
	description="Unique perks that enhance your experience.",
	items=[private_vc, rich_role, send_announce]
)

# Properties
small_house = HouseItem(
	name="Small House",
	description="A cozy small house to call your own.",
	price=250_000,
	stock=-1,
	perk=None,
	rent_cost=1_000,
	rent_income=800,
)

medium_house = HouseItem(
	name="Medium House",
	description="A spacious medium house for your family.",
	price=350_000,
	stock=-1,
	perk=None,
	rent_cost=1_500,
	rent_income=1_250,
)

large_house = HouseItem(
	name="Large House",
	description="A luxurious large house with all the amenities.",
	price=750_000,
	stock=-1,
	perk=None,
	rent_cost=2_500,
	rent_income=2_000,
)

mansion = HouseItem(
	name="Mansion",
	description="A grand mansion with opulent features.",
	price=1_500_000,
	stock=-1,
	perk=None,
	rent_cost=-1,  # Cannot be rented, only owned
	rent_income=9_000,
)

properties = ShopCategory(
	name="Properties",
	description="Houses and properties you can buy or rent.",
	items=[small_house, medium_house, large_house, mansion]
)

# Black Market Items
white_powder = BlackMarketItem(
	name="White Powder",
	description="A small bag of white powder.",
	price=200,
	stock=-1,
	perk=None,
	resale_mult=0.1,
	cops_risk=0.05,
	scam_risk=0
)

sig_p320_m1 = BlackMarketItem(
	name="Pistol",
	description="A SIG P320 M1 with the serial number scraped off.",
	price=1_000,
	stock=-1,
	perk=None,
	resale_mult=0.8,
	cops_risk=0.1,
	scam_risk=0.05,
	trace_back=True
)

glock_17_gen5 = BlackMarketItem(
	name="Glock 17 Gen5",
	description="A Glock 17 Gen5 with the serial number scratched off.",
	price=500,
	stock=-1,
	perk=None,
	resale_mult=0.85,
	cops_risk=0.12,
	scam_risk=0.07,
	trace_back=True
)

mr556 = BlackMarketItem(
	name="MR556A1",
	description="A HK MR556A1 semi-automatic rifle with acid burns where the serial number used to be.",
	price=3_500,
	stock=-1,
	perk=None,
	resale_mult=CIVILIAN_GUN_RESALE_MULT,
	cops_risk=0.15,
	scam_risk=0.1,
	trace_back=False
)

sig_mcx_spear = BlackMarketItem(
	name="SIG MCX Spear",
	description="A SIG MCX Spear semi-automatic rifle with a suppressor and a 20-inch barrel.",
	price=4_000,
	stock=-1,
	perk=None,
	resale_mult=CIVILIAN_GUN_RESALE_MULT,
	cops_risk=0.2,
	scam_risk=0.15,
	trace_back=False
)
