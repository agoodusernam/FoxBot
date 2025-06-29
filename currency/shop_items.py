from currency import perks
from currency.curr_config import ShopItem, ShopCategory, HouseItem, BlackMarketItem, DrugItem, BlackMarketCategory, \
	GunItem

CIVILIAN_GUN_RESALE_MULT = 0.7
MILITARY_GUN_RESALE_MULT = 0.9

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

# Cars
honda_civic = ShopItem(
		name="Honda Civic",
		description="Reliable, fuel-efficient sedan with modern tech and proven durability.",
		price=24_595,
		stock=-1,
		perk=None,
)

nissan_versa = ShopItem(
		name="Nissan Versa",
		description="Budget-friendly compact with surprising space and excellent fuel economy.",
		price=17_190,
		stock=-1,
		perk=None,
)

toyota_mirai = ShopItem(
		name="Toyota Mirai",
		description="Cutting-edge hydrogen fuel cell vehicle with zero emissions and futuristic styling.",
		price=51_795,
		stock=-1,
		perk=None,
)

bmw_430i = ShopItem(
		name="BMW 430i",
		description="Sporty coupe combining German engineering with elegant design and crisp handling.",
		price=51_500,
		stock=-1,
		perk=None,
)

bmw_740i = ShopItem(
		name="BMW 740i",
		description="Executive sedan offering plush comfort, advanced tech, and commanding presence.",
		price=100_300,
		stock=-1,
		perk=None,
)

mercedes_amg_gt = ShopItem(
		name="Mercedes AMG GT",
		description="Four-door coupe with supercar DNA, thunderous exhaust note, and stunning design.",
		price=101_100,
		stock=-1,
		perk=None,
)

porche_911_gt3_rs = ShopItem(
		name="Porsche 911 GT3 RS",
		description="Track-focused precision machine with racing pedigree and spine-tingling performance.",
		price=241_300,
		stock=-1,
		perk=None,
)

rr_phantom = ShopItem(
		name="Rolls Royce Phantom",
		description="The ultimate statement in luxury, handcrafted with unparalleled attention to detail.",
		price=517_750,
		stock=-1,
		perk=None,
)
ferrari_sf90 = ShopItem(
		name="Ferrari SF90",
		description="Hybrid hypercar with Formula 1 technology and breathtaking Italian styling.",
		price=593_950,
		stock=-1,
		perk=None,
)

bespoke_rr_phantom = ShopItem(
		name="Bespoke Rolls Royce Phantom",
		description="One-of-a-kind masterpiece tailored to your exact specifications and desires.",
		price=1_000_000,
		stock=-1,
		perk=None,
)

bugatti_tourbillon = ShopItem(
		name="Bugatti Tourbillon",
		description="Limited-edition hypercar with astronomical performance and aerospace-level engineering.",
		price=3_800_000,
		stock=250,
		perk=None,
)

cars = ShopCategory(
		name="Cars",
		description="Vehicles to drive around in style.",
		items=[honda_civic, nissan_versa, toyota_mirai, bmw_430i, bmw_740i, mercedes_amg_gt,
			   porche_911_gt3_rs, rr_phantom, ferrari_sf90, bespoke_rr_phantom, bugatti_tourbillon]
)

# Black Market Items
white_powder = DrugItem(
		name="White Powder",
		description="A small bag of mysterious white powder.",
		price=200,
		stock=-1,
		perk=None,
		resale_mult=0.1,
		cops_risk=0.05,
		scam_risk=0,
		trace_back=False,
		income_multiplier=0.4,
		work_catch_risk=0.15,
		od_chance=0.3,
		uses=5,
)

cocaine = DrugItem(
		name="Cocaine",
		description="A small bag of cocaine.",
		price=500,
		stock=-1,
		perk=None,
		resale_mult=0.2,
		cops_risk=0.1,
		scam_risk=0.05,
		trace_back=False,
		income_multiplier=0.8,
		work_catch_risk=0.3,
		uses=10,
)

lsd = DrugItem(
		name="LSD",
		description="A small bottle of LSD pills.",
		price=400,
		stock=-1,
		perk=None,
		resale_mult=0.15,
		cops_risk=0.08,
		scam_risk=0.03,
		trace_back=False,
		income_multiplier=0.5,
		work_catch_risk=0.2,
		uses=10,
)

weed = DrugItem(
		name="Weed",
		description="A small bag of weed.",
		price=100,
		stock=-1,
		perk=None,
		resale_mult=0.1,
		cops_risk=0,
		scam_risk=0,
		trace_back=False,
		income_multiplier=0.6,
		work_catch_risk=0.05,
		od_chance=0,
		uses=5,
)

methamphetamine = DrugItem(
		name="Methamphetamine",
		description="A small bag of Methamphetamine.",
		price=300,
		stock=-1,
		perk=None,
		resale_mult=0.15,
		cops_risk=0.1,
		scam_risk=0.05,
		trace_back=False,
		income_multiplier=1.3,
		work_catch_risk=0.25,
		uses=10,
		od_chance=0.1
)

fentanyl = DrugItem(
		name="Fentanyl",
		description="A very small bag of fentanyl.",
		price=50,
		stock=-1,
		perk=None,
		resale_mult=0.2,
		cops_risk=0.15,
		scam_risk=0.1,
		trace_back=False,
		income_multiplier=1.5,
		work_catch_risk=0.3,
		uses=1,
		od_chance=0.8
)

ominous_knife = BlackMarketItem(
		name="Ominous Knife",
		description="An ominous knife made of... bone...?",
		price=50_000,
		stock=1,
		perk=None,
		resale_mult=0,
		cops_risk=0,
		scam_risk=0,
		trace_back=False
)

sig_p320_m1 = GunItem(
		name="SIG P320 M1",
		description="A SIG P320 M1 with the serial number scraped off.",
		price=1_000,
		stock=-1,
		perk=None,
		resale_mult=0.8,
		cops_risk=0.05,
		scam_risk=0.05,
		trace_back=0.5,
		suppressed=False
)

glock_17_gen5 = GunItem(
		name="Glock 17 Gen5",
		description="A Glock 17 Gen5 with the serial number scratched off.",
		price=500,
		stock=-1,
		perk=None,
		resale_mult=0.85,
		cops_risk=0.05,
		scam_risk=0.07,
		trace_back=0.5,
		suppressed=False
)

m1911_a1 = GunItem(
		name="M1911 A1",
		description="Dean Winchester's M1911 A1.",
		price=50_000,
		stock=1,
		perk=None,
		resale_mult=0,
		cops_risk=0,
		scam_risk=0,
		trace_back=False,
		suppressed=False
)

the_colt = GunItem(
		name="The Colt",
		description="The Colt made by Samuel Colt. It can kill all but 5 beings in existence.",
		price=1_000_000,
		stock=1,
		perk=None,
		resale_mult=0,
		cops_risk=0,
		scam_risk=0,
		trace_back=False,
		suppressed=False
)

mr556 = GunItem(
		name="MR556A1",
		description="A HK MR556A1 semi-automatic rifle.",
		price=3_500,
		stock=-1,
		perk=None,
		resale_mult=CIVILIAN_GUN_RESALE_MULT,
		cops_risk=0.1,
		scam_risk=0.1,
		trace_back=0.15,
		suppressed=False
)

sig_mcx_spear = GunItem(
		name="SIG MCX Spear",
		description="A SIG MCX Spear semi-automatic rifle with a suppressor.",
		price=4_000,
		stock=-1,
		perk=None,
		resale_mult=CIVILIAN_GUN_RESALE_MULT,
		cops_risk=0.1,
		scam_risk=0.15,
		trace_back=0.15,
		suppressed=True
)

hk417 = GunItem(
		name="HK417",
		description="A HK417 fully automatic rifle.",
		price=10_000,
		stock=-1,
		perk=None,
		resale_mult=MILITARY_GUN_RESALE_MULT,
		cops_risk=0.2,
		scam_risk=0.05,
		trace_back=0.2,
		suppressed=False
)

sig_mx7 = GunItem(
		name="SIG MX7",
		description="A SIG MX7 fully automatic rifle with a suppressor.",
		price=12_000,
		stock=-1,
		perk=None,
		resale_mult=MILITARY_GUN_RESALE_MULT,
		cops_risk=0.2,
		scam_risk=0.05,
		trace_back=0.2,
		suppressed=True
)

ak_47 = GunItem(
		name="AK-47",
		description="The working man's fully automatic rifle.",
		price=2_000,
		stock=-1,
		perk=None,
		resale_mult=0.4,
		cops_risk=0.05,
		scam_risk=0.1,
		trace_back=False,
		suppressed=False
)

m39_emr = GunItem(
		name="M39 EMR",
		description="A M39 Enhanced Marksman Rifle.",
		price=3_450,
		stock=-1,
		perk=None,
		resale_mult=MILITARY_GUN_RESALE_MULT,
		cops_risk=0.2,
		scam_risk=0.1,
		trace_back=0.3,
		suppressed=False
)

barrett_m82 = GunItem(
		name="Barrett M82",
		description="A Barrett M82 anti-materiel rifle.",
		price=20_000,
		stock=-1,
		perk=None,
		resale_mult=MILITARY_GUN_RESALE_MULT,
		cops_risk=0.2,
		scam_risk=0.15,
		trace_back=0.5,
		suppressed=False
)

l115a3_awm = GunItem(
		name="L115A3 AWM",
		description="A suppressed L115A3 Arctic Warfare Magnum sniper rifle, used in the longest range confirmed kill in history.",
		price=15_000,
		stock=-1,
		perk=None,
		resale_mult=MILITARY_GUN_RESALE_MULT,
		cops_risk=0.2,
		scam_risk=0.1,
		trace_back=0.2,
		suppressed=True
)

drugs = BlackMarketCategory(
		name="Drugs",
		description="Various drugs that may or may kill you.",
		items=[white_powder, cocaine, lsd, weed, methamphetamine, fentanyl]
)

weapons = BlackMarketCategory(
		name="Weapons",
		description="Weapons that you can use to kill people",
		items=[ominous_knife, sig_p320_m1, glock_17_gen5, m1911_a1, the_colt, mr556, sig_mcx_spear, hk417, sig_mx7,
			   ak_47, m39_emr, barrett_m82, l115a3_awm]
)

categories = [var for var in globals().values() if isinstance(var, ShopCategory)]
bm_categories = [var for var in globals().values() if isinstance(var, BlackMarketCategory)]

all_items = [var for var in globals().values() if isinstance(var, ShopItem)]
all_guns = [var.name for var in globals().values() if isinstance(var, GunItem)]
