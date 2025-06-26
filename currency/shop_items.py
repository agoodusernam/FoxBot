import perks
from curr_config import ShopItem, ShopCategory, HouseItem, BlackMarketItem, DrugItem

CIVILIAN_GUN_RESALE_MULT = 0.7
MILITARY_GUN_RESALE_MULT = 0.9

# Shop Items

# Special Items
private_vc = ShopItem(
		name = "Private VC",
		description = "A private voice channel for you and your friends.",
		price = 10_000,
		stock = -1,
		perk = [perks.create_private_vc]  # Duration in days
)

rich_role = ShopItem(
		name = "Rich Role",
		description = "A special role for those who are very rich.",
		price = 1_000_000,
		stock = -1,
		perk = [perks.give_rich_role]
)

send_announce = ShopItem(
		name = "Send Announcement",
		description = "Allows you to send an announcement in the server.",
		price = 100_000,
		stock = -1,
		perk = [perks.send_announcement]
)

special_perks = ShopCategory(
		name = "Special Items",
		description = "Unique perks that enhance your experience.",
		items = [private_vc, rich_role, send_announce]
)

# Properties
small_house = HouseItem(
		name = "Small House",
		description = "A cozy small house to call your own.",
		price = 250_000,
		stock = -1,
		perk = None,
		rent_cost = 1_000,
		rent_income = 800,
)

medium_house = HouseItem(
		name = "Medium House",
		description = "A spacious medium house for your family.",
		price = 350_000,
		stock = -1,
		perk = None,
		rent_cost = 1_500,
		rent_income = 1_250,
)

large_house = HouseItem(
		name = "Large House",
		description = "A luxurious large house with all the amenities.",
		price = 750_000,
		stock = -1,
		perk = None,
		rent_cost = 2_500,
		rent_income = 2_000,
)

mansion = HouseItem(
		name = "Mansion",
		description = "A grand mansion with opulent features.",
		price = 1_500_000,
		stock = -1,
		perk = None,
		rent_cost = -1,  # Cannot be rented, only owned
		rent_income = 9_000,
)

properties = ShopCategory(
		name = "Properties",
		description = "Houses and properties you can buy or rent.",
		items = [small_house, medium_house, large_house, mansion]
)
# Black Market Items
white_powder = DrugItem(
		name = "White Powder",
		description = "A small bag of mysterious white powder.",
		price = 200,
		stock = -1,
		perk = None,
		resale_mult = 0.1,
		cops_risk = 0.05,
		scam_risk = 0,
		trace_back = False,
		income_multiplier = 0.4,
		work_catch_risk = 0.15,
		od_chance = 0.3,
		uses = 5,
)

cocaine = DrugItem(
		name = "Cocaine",
		description = "A small bag of cocaine.",
		price = 500,
		stock = -1,
		perk = None,
		resale_mult = 0.2,
		cops_risk = 0.1,
		scam_risk = 0.05,
		trace_back = False,
		income_multiplier = 0.8,
		work_catch_risk = 0.3,
		uses = 10,
)

lsd = DrugItem(
		name = "LSD",
		description = "A small bottle of LSD pills.",
		price = 400,
		stock = -1,
		perk = None,
		resale_mult = 0.15,
		cops_risk = 0.08,
		scam_risk = 0.03,
		trace_back = False,
		income_multiplier = 0.5,
		work_catch_risk = 0.2,
		uses = 10,
)

weed = DrugItem(
		name = "Weed",
		description = "A small bag of weed.",
		price = 100,
		stock = -1,
		perk = None,
		resale_mult = 0.1,
		cops_risk = 0,
		scam_risk = 0,
		trace_back = False,
		income_multiplier = 0.6,
		work_catch_risk = 0.1,
		uses = 5,
)

meth = DrugItem(
		name = "Meth",
		description = "A small bag of meth.",
		price = 300,
		stock = -1,
		perk = None,
		resale_mult = 0.15,
		cops_risk = 0.1,
		scam_risk = 0.05,
		trace_back = False,
		income_multiplier = 1.3,
		work_catch_risk = 0.25,
		uses = 10,
		od_chance = 0.1
)

fentanyl = DrugItem(
		name = "Fentanyl",
		description = "A very small bag of fentanyl.",
		price = 50,
		stock = -1,
		perk = None,
		resale_mult = 0.2,
		cops_risk = 0.15,
		scam_risk = 0.1,
		trace_back = False,
		income_multiplier = 1.5,
		work_catch_risk = 0.3,
		uses = 1,
		od_chance = 0.8
)

ominous_knife = BlackMarketItem(
		name = "Ominous Knife",
		description = "An ominous knife made of bone.",
		price = 50_000,
		stock = 1,
		perk = None,
		resale_mult = 0,
		cops_risk = 0,
		scam_risk = 0,
		trace_back = False
)

sig_p320_m1 = BlackMarketItem(
		name = "SIG P320 M1",
		description = "A SIG P320 M1 with the serial number scraped off.",
		price = 1_000,
		stock = -1,
		perk = None,
		resale_mult = 0.8,
		cops_risk = 0.1,
		scam_risk = 0.05,
		trace_back = True
)

m1911_a1 = BlackMarketItem(
		name = "M1911 A1",
		description = "Dean Winchester's M1911 A1.",
		price = 50_000,
		stock = 1,
		perk = None,
		resale_mult = 0,
		cops_risk = 0,
		scam_risk = 0,
		trace_back = False
)

the_colt = BlackMarketItem(
		name = "The Colt",
		description = "The Colt made by Samuel Colt. It can kill all but 5 beings in existence.",
		price = 1_000_000,
		stock = 1,
		perk = None,
		resale_mult = 0,
		cops_risk = 0,
		scam_risk = 0,
		trace_back = False
)

glock_17_gen5 = BlackMarketItem(
		name = "Glock 17 Gen5",
		description = "A Glock 17 Gen5 with the serial number scratched off.",
		price = 500,
		stock = -1,
		perk = None,
		resale_mult = 0.85,
		cops_risk = 0.12,
		scam_risk = 0.07,
		trace_back = True
)

mr556 = BlackMarketItem(
		name = "MR556A1",
		description = "A HK MR556A1 semi-automatic rifle with acid burns where the serial number used to be.",
		price = 3_500,
		stock = -1,
		perk = None,
		resale_mult = CIVILIAN_GUN_RESALE_MULT,
		cops_risk = 0.15,
		scam_risk = 0.1,
		trace_back = False
)

sig_mcx_spear = BlackMarketItem(
		name = "SIG MCX Spear",
		description = "A SIG MCX Spear semi-automatic rifle with a suppressor and a 20-inch barrel.",
		price = 4_000,
		stock = -1,
		perk = None,
		resale_mult = CIVILIAN_GUN_RESALE_MULT,
		cops_risk = 0.2,
		scam_risk = 0.15,
		trace_back = False
)

hk417 = BlackMarketItem(
		name = "HK417",
		description = "A HK417 fully automatic rifle.",
		price = 10_000,
		stock = -1,
		perk = None,
		resale_mult = MILITARY_GUN_RESALE_MULT,
		cops_risk = 0.2,
		scam_risk = 0.05,
		trace_back = True
)

sig_mx7 = BlackMarketItem(
		name = "SIG MX7",
		description = "A SIG MX7 fully automatic rifle with a suppressor.",
		price = 12_000,
		stock = -1,
		perk = None,
		resale_mult = MILITARY_GUN_RESALE_MULT,
		cops_risk = 0.25,
		scam_risk = 0.05,
		trace_back = True
)
