import discord
from discord.ext import commands

import utils.utils
from currency import curr_utils
from currency import shop_items
from currency.curr_config import currency_name, loan_interest_rate, income_tax
from command_utils.checks import not_blacklisted


# Create pagination view
class ShopView(discord.ui.View):
	def __init__(self, embeds):
		super().__init__(timeout = 60)  # 60 second timeout
		self.embeds = embeds
		self.current_page = 0

	@discord.ui.button(label = "Previous", style = discord.ButtonStyle.gray)
	async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		if self.current_page > 0:
			self.current_page -= 1
			await interaction.response.edit_message(embed = self.embeds[self.current_page])
		else:
			await interaction.response.defer()

	@discord.ui.button(label = "Next", style = discord.ButtonStyle.gray)
	async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		if self.current_page < len(self.embeds) - 1:
			self.current_page += 1
			await interaction.response.edit_message(embed = self.embeds[self.current_page])
		else:
			await interaction.response.defer()

	async def on_timeout(self):
		# Disable all buttons when the view times out
		for item in self.children:
			item.disabled = True
		# View will be automatically removed from the message

class CurrencyCmds(commands.Cog, name = "Currency", command_attrs = dict(add_check = not_blacklisted)):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	@commands.command(name = "balance", aliases = ["bal"],
					  brief = "Check your balance",
					  help = "Check your current money and bank balance")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def balance_cmd(self, ctx: commands.Context):
		profile = curr_utils.get_profile(ctx.author)
		wallet = profile['wallet']
		bank = profile['bank']
		await ctx.send(f"**Balance:**\nWallet: {wallet}\nBank: {bank}\nTotal: {wallet + bank}")

	@commands.command(name = "baltop", aliases = ["balance_top", "bal_top"],
					  brief = "Check the top balances",
					  help = "Check the top users with the highest balances",
					  usage = "baltop")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def baltop_cmd(self, ctx: commands.Context):
		top_users = curr_utils.get_top_balances()
		if not top_users:
			await ctx.send("No users found in the database.")
			return

		top_list = "\n"
		for user, balance in top_users:
			top_list += f"{discord.utils.get(ctx.bot.get_all_members(), id = user).display_name}: {balance} {currency_name}\n"
		await ctx.send(f"**Top Wallet Balances:**\n{top_list}")

	@commands.command(name = "deposit", aliases = ["dep"],
					  brief = "Deposit money into your bank",
					  help = "Deposit some of your money from your wallet into your bank",
					  usage = "deposit <amount>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def deposit_cmd(self, ctx: commands.Context, amount: int):
		if amount <= 0:
			await ctx.send("You must deposit a positive amount!")
			return
		profile = curr_utils.get_profile(ctx.author)
		if profile['wallet'] < amount:
			await ctx.send("You do not have enough money in your wallet!")
			return
		curr_utils.set_wallet(ctx.author, profile['wallet'] - amount)
		curr_utils.set_bank(ctx.author, profile['bank'] + amount)
		await ctx.send(f"Deposited {amount} {currency_name} into your bank!")

	@commands.command(name = "withdraw", aliases = ["with"],
					  brief = "Withdraw money from your bank",
					  help = "Withdraw some of your money from your bank into your wallet",
					  usage = "withdraw <amount>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def withdraw_cmd(self, ctx: commands.Context, amount: int):
		if amount <= 0:
			await ctx.send("You must withdraw a positive amount!")
			return
		profile = curr_utils.get_profile(ctx.author)
		if profile['bank'] < amount:
			await ctx.send("You do not have enough money in your bank!")
			return
		curr_utils.set_wallet(ctx.author, profile['wallet'] + amount)
		curr_utils.set_bank(ctx.author, profile['bank'] - amount)
		await ctx.send(f"Withdrew {amount} {currency_name} from your bank!")

	@commands.command(name = "pay", aliases = ["give"],
					  brief = "Pay another user",
					  help = "Pay another user some of your money",
					  usage = "pay <user> <amount>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def pay_cmd(self, ctx: commands.Context, user: str, amount: int):
		recipient = discord.utils.get(ctx.guild.members, name = utils.utils.get_id_from_str(user))
		if recipient is None or recipient is False:
			await ctx.send("Invalid user ID or mention!")
			return

		if recipient.id == ctx.author:
			await ctx.send("You cannot pay yourself!")
			return
		if amount <= 0:
			await ctx.send("You must pay a positive amount!")
			return
		payer_profile = curr_utils.get_profile(ctx.author)
		if payer_profile['wallet'] < amount:
			await ctx.send("You do not have enough money in your wallet!")
			return

		recipient_profile = curr_utils.get_profile(recipient)
		curr_utils.set_wallet(ctx.author, payer_profile['wallet'] - amount)
		curr_utils.set_wallet(recipient, recipient_profile['wallet'] + amount)
		await ctx.send(f"Paid {recipient.mention} {amount} {currency_name}!")

	@commands.command(name = "work",
					  brief = "Work to earn money",
					  help = "Work to earn some money. You can do this every day.")
	@commands.cooldown(1, 24 * 60 * 60, commands.BucketType.user)  # 24-hour cooldown
	async def work_cmd(self, ctx: commands.Context):
		profile = curr_utils.get_profile(ctx.author)

		earnings = int(profile['income'] * (1 - income_tax))
		debt = int(profile['debt'] * (1 + loan_interest_rate))
		if earnings <= 0:
			await ctx.send(f"You have no job! Choose a job first using `{ctx.bot.command_prefix}job`.")
			return
		wallet = earnings + profile['wallet']
		curr_utils.set_wallet(ctx.author, wallet)
		curr_utils.set_debt(ctx.author, debt)
		await ctx.send(f"You worked hard and earned {earnings} {currency_name}!")

	@commands.command(name = "debt",
					  brief = "Check your debt",
					  help = "Check how much debt you have")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def debt_cmd(self, ctx: commands.Context):
		profile = curr_utils.get_profile(ctx.author)
		debt = profile['debt']
		if debt <= 0:
			await ctx.send("You have no debt!")
		else:
			await ctx.send(f"You currently owe {debt} {currency_name} in loans.")

	@commands.command(name = "pay_debt", aliases = ["payloan", "pay_load", "repay", "paydebt"],
					  brief = "Pay off your debt",
					  help = "Pay off some of your debt from loans",
					  usage = "pay_debt <amount>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def pay_debt_cmd(self, ctx: commands.Context, amount: int):
		if amount <= 0:
			await ctx.send("You must pay a positive amount!")
			return
		profile = curr_utils.get_profile(ctx.author)
		if profile['debt'] < amount:
			amount = profile['debt']  # If they try to pay more than they owe, pay off the entire debt

		if profile['wallet'] < amount:
			await ctx.send("You do not have enough money in your wallet to pay off that much debt!")
			return
		intrest = int(profile['debt'] * loan_interest_rate)
		if amount >= intrest:
			new_credit_score = min(profile['credit_score'] + 1, 800)
			if new_credit_score > profile['credit_score']:
				curr_utils.set_credit_score(ctx.author, new_credit_score)

		elif amount < intrest * 0.75:
			new_credit_score = max(profile['credit_score'] - 1, 100)
			if new_credit_score < profile['credit_score']:
				curr_utils.set_credit_score(ctx.author, new_credit_score)

		curr_utils.set_wallet(ctx.author, int(profile['wallet'] - amount))
		curr_utils.set_debt(ctx.author, int(profile['debt'] - amount))

		await ctx.send(f"Paid off {amount} {currency_name} of your debt!")

	@commands.command(name = "get_loan", aliases = ["loan"],
					  brief = "Get a loan",
					  help = "Get a loan to increase your wallet balance",
					  usage = "get_loan <amount>")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def get_loan_cmd(self, ctx: commands.Context, amount: int):
		if amount <= 0:
			await ctx.send("You must request a positive loan amount!")
			return
		profile = curr_utils.get_profile(ctx.author)
		if profile['debt'] > 0:
			await ctx.send("You already have an outstanding loan! Pay it off first.")
			return

		if curr_utils.calculate_max_loan(profile) < amount:
			await ctx.send(f"You cannot take a loan of {amount} {currency_name}. ")
			await ctx.send(f"Increase max loan size by increasing income or credit score.")
			return

		curr_utils.set_wallet(ctx.author, profile['wallet'] + amount)
		curr_utils.set_debt(ctx.author, amount)
		await ctx.send(f"You have taken a loan of {amount} {currency_name}. Remember to pay it back with interest!")

	@commands.command(name = "credit_score", aliases = ["credit"],
					  brief = "Check your credit score",
					  help = "Check your current credit score",
					  usage = "credit_score")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def credit_score_cmd(self, ctx: commands.Context):
		profile = curr_utils.get_profile(ctx.author)
		credit_score = profile['credit_score']
		await ctx.send(f"Your current credit score is {credit_score}. "
					   f"Improve it by paying off loans and maintaining a good balance.")

	@commands.command(name = "shop", aliases = ["store"],
					  brief = "View the shop",
					  help = "View the items available for purchase in the shop",
					  usage = "shop")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def shop_cmd(self, ctx: commands.Context):
		embed = discord.Embed(title="Shop", description="Items available for purchase", color=discord.Color.green())
		embed.set_thumbnail(url=ctx.guild.icon.url)
		categories = shop_items.categories
		# bm_categories = shop_items.bm_categories

		# Create list to store category embeds
		embeds = []

		# Add regular categories
		for category in categories:
			category_embed = discord.Embed(
					title = f"Shop - {category.name}",
					description = category.description,
					color = discord.Color.green()
			)

			# Safely set thumbnail
			if hasattr(ctx.guild, 'icon') and ctx.guild.icon:
				category_embed.set_thumbnail(url = ctx.guild.icon.url)

			# Add items for this category
			for item in category.items:
				item_desc = f"{item.description}\nPrice: {item.price} {currency_name}"
				if item.stock != -1:
					item_desc += f"\nStock: {item.stock}"
				category_embed.add_field(name = item.name, value = item_desc, inline = False)

			# Add page number to footer
			total_pages = len(categories)
			category_embed.set_footer(text = f"Page {len(embeds) + 1}/{total_pages}")
			embeds.append(category_embed)


		# Send the first page with navigation
		if embeds:
			view = ShopView(embeds)
			await ctx.send(embed = embeds[0], view = view)
		else:
			await ctx.send("No items available in the shop.")


	@commands.command(name = "blackmarket", aliases = ["bm"],
					  brief = "View the black market",
					  help = "View the items available for purchase in the black market",
					  usage = "blackmarket")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def blackmarket_cmd(self, ctx: commands.Context):
		embed = discord.Embed(title="Black Market", description="Items available for purchase", color=discord.Color.dark_red())
		embed.set_thumbnail(url=ctx.guild.icon.url)
		categories = shop_items.bm_categories

		# Create list to store category embeds
		embeds = []

		for category in categories:
			category_embed = discord.Embed(
					title = f"Black Market - {category.name}",
					description = category.description,
					color = discord.Color.dark_red()
			)

			if hasattr(ctx.guild, 'icon') and ctx.guild.icon:
				category_embed.set_thumbnail(url = ctx.guild.icon.url)

			for item in category.items:
				item_desc = f"{item.description}\nPrice: {item.price} {currency_name}"
				if item.stock != -1:
					item_desc += f"\nStock: {item.stock}"
				category_embed.add_field(name = item.name, value = item_desc, inline = False)

			total_pages = len(categories)
			category_embed.set_footer(text = f"Page {len(embeds) + 1}/{total_pages}")
			embeds.append(category_embed)

		if embeds:
			view = ShopView(embeds)
			await ctx.send(embed = embeds[0], view = view)
		else:
			await ctx.send("No items available in the black market.")

	@commands.command(name = "buy", aliases = ["purchase"],
					  brief = "Buy an item from the shop",
					  help = "Buy an item from the shop or black market",
					  usage = "buy <item_name> [quantity]")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def buy_cmd(self, ctx: commands.Context, *, args: str):
		# Split the arguments into item name and quantity
		args = args.strip().split()
		if len(args) < 1:
			await ctx.send("You must specify an item to buy")
			return

		try:
			quantity = int(args[-1])

			if quantity <= 0:
				await ctx.send("You must buy a positive quantity of the item!")
				return
			q_given = True
		except ValueError:
			quantity = 1
			q_given = False

		if q_given:
			item_name = " ".join(args[:-1]).lower()
		else:
			item_name = " ".join(args).lower()
		print(item_name)
		all_items = shop_items.all_items
		item = next((i for i in all_items if i.name.lower() == item_name), None)
		print(item)
		if item is None:
			await ctx.send(f"No item found with name '{item_name}'")
			return
		stock = curr_utils.get_stock(item)
		if stock != -1:
			if stock < quantity:
				await ctx.send(f"Not enough stock for {item.name}. Available: {stock}, Requested: {quantity}")
				return
		total_price = item.price * quantity
		profile = curr_utils.get_profile(ctx.author)
		if profile['wallet'] < total_price:
			await ctx.send(f"You do not have enough money in your wallet! You need {total_price} {currency_name}.")
			return

		# Deduct the price from the user's wallet
		curr_utils.set_wallet(ctx.author, profile['wallet'] - total_price)
		# Update the stock in the database
		if stock != -1:
			# If the item has a stock limit, reduce the stock
			curr_utils.set_stock(item, stock - quantity)
		# Add the item to the user's inventory
		curr_utils.add_to_inventory(ctx.author, item.name, quantity)
		await ctx.send(f"Successfully bought {quantity}x {item.name} for {total_price} {currency_name}!")

	@commands.command(name = "inventory", aliases = ["inv"],
					  brief = "Check your inventory",
					  help = "Check the items you own in your inventory",
					  usage = "inventory")
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def inventory_cmd(self, ctx: commands.Context):
		profile = curr_utils.get_profile(ctx.author)
		inventory = profile['inventory']
		if not inventory:
			await ctx.send("Your inventory is empty.")
			return

		inv_list = "\n".join(f"{item}: {quantity}" for item, quantity in inventory.items())
		await ctx.send(f"**Your Inventory:**\n{inv_list}")



async def setup(bot: commands.Bot) -> None:
	pass
	#await bot.add_cog(CurrencyCmds(bot))
