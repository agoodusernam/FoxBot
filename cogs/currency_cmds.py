import random
import typing

import discord
from discord.ext import commands

import currency.curr_utils
from command_utils.CContext import CContext
from command_utils.checks import is_dev
from currency import curr_utils, curr_config, shop_items, job_utils, jobs
from currency.curr_config import currency_name, loan_interest_rate, income_tax, DrugItem, BlackMarketItem, GunItem, \
    ShopItem, HouseItem, Profile, base_fire_chance
from currency.curr_utils import get_shop_item
from currency.job_utils import SchoolQualif, SecurityClearance
from currency.jobs import job_trees

salary_offers: dict[int, dict[str, int]] = {}


# Create pagination view
class ShopView(discord.ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=60)  # 60 second timeout
        self.embeds = embeds
        self.current_page = 0
    
    @discord.ui.button(label='Previous', style=discord.ButtonStyle.gray)  # type: ignore
    async def previous_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page])  # type: ignore
        else:
            await interaction.response.defer()  # type: ignore
    
    @discord.ui.button(label='Next', style=discord.ButtonStyle.gray)  # type: ignore
    async def next_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page])  # type: ignore
        else:
            await interaction.response.defer()  # type: ignore
    
    async def on_timeout(self):
        # Disable all buttons when the view times out
        for item in self.children:
            item.disabled = True
    # View will be automatically removed from the message


#TODO: Add other money making activities like hunting, fishing and others
#TODO: Add illegal jobs
class CurrencyCmds(commands.Cog, name='Currency', command_attrs=dict(add_check=is_dev, hidden=True)):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='balance', aliases=['bal'],
                      brief='Check your balance',
                      help='Check your current money and bank balance')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def balance_cmd(self, ctx: CContext):
        profile = curr_utils.get_profile(ctx.author)
        wallet = profile['wallet']
        bank = profile['bank']
        await ctx.send(f'**Balance:**\nWallet: {wallet}\nBank: {bank}\nTotal: {wallet + bank}')
    
    @commands.command(name='baltop', aliases=['balance_top', 'bal_top'],
                      brief='Check the top balances',
                      help='Check the top users with the highest balances',
                      usage='f!baltop')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def baltop_cmd(self, ctx: CContext):
        top_users = curr_utils.get_top_balances()
        if not top_users:
            await ctx.send('Not enough users found in the database.')
            return
        
        top_list = '\n'
        for user, balance in top_users:
            top_list += f'{discord.utils.get(ctx.bot.get_all_members(), id=user).display_name}: {balance} {currency_name}\n'
        await ctx.send(f'**Top Wallet Balances:**\n{top_list}')
    
    @commands.command(name='deposit', aliases=['dep'],
                      brief='Deposit money into your bank',
                      help='Deposit some of your money from your wallet into your bank',
                      usage='f!deposit <amount>')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def deposit_cmd(self, ctx: CContext, amount: int):
        if amount <= 0:
            await ctx.send('You must deposit a positive amount!')
            return
        profile = curr_utils.get_profile(ctx.author)
        if profile['wallet'] < amount:
            await ctx.send('You do not have enough money in your wallet!')
            return
        profile['wallet'] -= amount
        profile['bank'] += amount
        curr_utils.set_profile(ctx.author, profile)
        await ctx.send(f'Deposited {amount} {currency_name} into your bank!')
    
    @commands.command(name='withdraw', aliases=['with'],
                      brief='Withdraw money from your bank',
                      help='Withdraw some of your money from your bank into your wallet',
                      usage='f!withdraw <amount>')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def withdraw_cmd(self, ctx: CContext, amount: int):
        if amount <= 0:
            await ctx.send('You must withdraw a positive amount!')
            return
        profile = curr_utils.get_profile(ctx.author)
        if profile['bank'] < amount:
            await ctx.send('You do not have enough money in your bank!')
            return
        
        profile['bank'] -= amount
        profile['wallet'] += amount
        curr_utils.set_profile(ctx.author, profile)
        await ctx.send(f'Withdrew {amount} {currency_name} from your bank!')
    
    @commands.command(name='pay', aliases=['give'],
                      brief='Pay another user',
                      help='Pay another user some of your money',
                      usage='f!pay <user> <amount>')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def pay_cmd(self, ctx: CContext, user: discord.Member, amount: int):
        if user is None:
            await ctx.send('You must specify a valid user to pay!')
            return
        
        if user.id == ctx.author.id:
            await ctx.send('You cannot pay yourself!')
            return
        if amount <= 0:
            await ctx.send('You must pay a positive amount!')
            return
        payer_profile = curr_utils.get_profile(ctx.author)
        if payer_profile['wallet'] < amount:
            await ctx.send('You do not have enough money in your wallet!')
            return
        
        recipient_profile = curr_utils.get_profile(user)
        payer_profile['wallet'] -= amount
        recipient_profile['wallet'] += amount
        curr_utils.set_profile(ctx.author, payer_profile)
        curr_utils.set_profile(user, recipient_profile)
        await ctx.send(f'Paid {user.mention} {amount} {currency_name}!')
    
    @commands.command(name='work',
                      brief='Work to earn money',
                      help='Work to earn some money. You can do this every day.')
    @commands.cooldown(1, 24 * 60 * 60, commands.BucketType.user)  # type: ignore
    async def work_cmd(self, ctx: CContext):
        #TODO: Check for promotions and raises
        profile = curr_utils.get_profile(ctx.author)
        if profile['work_income'] <= 0:
            await ctx.send(f'You have no job! Choose a job first using `{ctx.bot.command_prefix}job`.')
            return
        earnings: int = int(profile['work_income'] * (1 - income_tax)) // 12
        # work_income is yearly, so divide by 12 for monthly income
        
        profile['age'] += 1
        fired = profile['fire_risk'] > random.random()
        if fired:
            await ctx.send('You were fired from your job! You need to find a new job using the `job` command.')
            await ctx.send('A severance package has been deposited into your wallet.')
            profile['work_income'] = 0
            profile['work_str'] = 'Unemployed'
            profile['work_tree'] = 'None'
            profile['fire_risk'] = 0
            profile['work_experience'] = profile['work_experience'] // 2
            profile['wallet'] += earnings * 2  # Severance package is 2 months of income
            curr_utils.set_profile(ctx.author, profile)
            return
        
        job_obj = job_utils.job_from_name(profile['work_str'], jobs.job_trees)
        if job_obj is None:
            raise discord.ext.commands.CommandError('Job not found in database, contact the bot developer.')
        
        if profile['debt'] > 0:
            profile['debt'] = int(profile['debt'] * (1 + loan_interest_rate))
            
        profile['wallet'] += earnings
        profile['work_experience'] += 1 * job_obj.experience_multiplier
        profile['next_income_mult'] = 1.0 # Reset income multiplier after working
        profile['fire_risk'] *= 0.8  # Working reduces fire risk
        
        if profile['fire_risk'] < base_fire_chance:
            # If the fire risk is very low, increase it slightly
            profile['fire_risk'] = base_fire_chance
        
        if profile['work_experience'] % 12 == 11:
            # Every year of experience, give them a raise between 1 and 5%
            raise_amount = random.uniform(0.01, 0.05)
            profile['work_income'] = int(profile['work_income'] * (1 + raise_amount))
            await ctx.send(f'You have been a good employee and received a {raise_amount*100:.1f}% raise!')
        
        school_qualif = SchoolQualif.from_string(profile['qualifications'][0])
        clearance = SecurityClearance.from_string(profile['qualifications'][1])
        
        next_job = job_obj.get_next_job()
        if next_job is None:
            # No next job available
            curr_utils.set_profile(ctx.author, profile)
            await ctx.send(f'You worked hard and earned {earnings} {currency_name}!')
            return
            
        exp_qualified = False
        school_qualified = False
        clearance_qualified = False
        if profile['work_experience'] >= next_job.req_experience:
            exp_qualified = True
        if school_qualif >= next_job.school_requirement:
            school_qualified = True
        if clearance.value >= next_job.security_clearance.value:
            clearance_qualified = True
        
        if exp_qualified and school_qualified and clearance_qualified:
            profile['work_str'] = next_job.name
            profile['work_tree'] = next_job.tree
            salary_multiplier = 1 + (random.randint(0, next_job.salary_variance * 10) /1000)
            # Salary multiplier to 0.1% precision
            profile['work_income'] = int(next_job.salary * salary_multiplier)
            await ctx.send(f'Congratulations! You have been promoted to {next_job.name}!')
            await ctx.send(f'New income: {profile["work_income"]} {currency_name} per year.')
            
        elif not exp_qualified:
            # Don't notify if they wouldn't have the experience to get a promotion
            pass
        
        elif not school_qualified:
            await ctx.send(f'You need a higher school qualification to be promoted to {next_job.name}.')
            await ctx.send(f'Required: {next_job.school_requirement.to_string()}, You have: {school_qualif.to_string()}')
            await ctx.send(f'Use `{ctx.bot.command_prefix}school` to study for a higher qualification.')
            
        elif not clearance_qualified:
            await ctx.send(f'You need a higher security clearance to be promoted to {next_job.name}.')
            await ctx.send(f'Required: {next_job.security_clearance.to_string()}, You have: {clearance.to_string()}')
            await ctx.send(f"Use `{ctx.bot.command_prefix}clearance` to apply for a higher clearance level.")
        
        
        curr_utils.set_profile(ctx.author, profile)
        await ctx.send(f'You worked hard and earned {earnings} {currency_name}')
    
    @commands.command(name='quit',
                      brief='Quit your current job',
                      help='Quit your current job so you can get a new one',
                      usage='f!quit')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def quit_cmd(self, ctx: CContext):
        profile = curr_utils.get_profile(ctx.author)
        if profile['work_income'] <= 0:
            await ctx.send('You have no job to quit! Choose a job first using `job`.')
            return
        
        profile['work_income'] = 0
        profile['work_tree'] = 'None'
        profile['work_str'] = 'Unemployed'
        profile['fire_risk'] = 0
        
        curr_utils.set_profile(ctx.author, profile)
        await ctx.send('You have quit your job. You can now choose a new job using the `job` command.')
    
    @commands.command(name='debt',
                      brief='Check your debt',
                      help='Check how much debt you have')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def debt_cmd(self, ctx: CContext):
        profile = curr_utils.get_profile(ctx.author)
        if profile['debt'] <= 0:
            await ctx.send('You have no debt!')
        else:
            await ctx.send(f'You currently owe {profile['debt']} {currency_name} in loans.')
    
    @commands.command(name='pay_debt', aliases=['payloan', 'pay_loan', 'repay', 'paydebt'],
                      brief='Pay off your debt',
                      help='Pay off some of your debt from loans',
                      usage='f!pay_debt <amount>')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def pay_debt_cmd(self, ctx: CContext, amount: int):
        if amount <= 0:
            await ctx.send('You must pay a positive amount!')
            return
        profile = curr_utils.get_profile(ctx.author)
        if profile['debt'] < amount:
            amount = profile['debt']  # If they try to pay more than they owe, pay off the entire debt
        
        if profile['wallet'] < amount:
            await ctx.send('You do not have enough money in your wallet to pay off that much debt!')
            return
        
        intrest = int(profile['debt'] * loan_interest_rate)
        if amount >= intrest:
            profile['credit_score'] = min(profile['credit_score'] + 1, 800)
        
        elif amount < (intrest * 0.75):
            profile['credit_score'] = max(profile['credit_score'] - 1, 100)
        
        profile['debt'] -= amount
        profile['wallet'] -= amount
        
        if profile['debt'] > 0:
            await ctx.send(f'Paid off {amount} {currency_name} of your debt!')
        else:
            await ctx.send(f'You have paid off all your {amount} {currency_name} debt!')
        
        curr_utils.set_profile(ctx.author, profile)
    
    @commands.command(name='get_loan', aliases=['loan'],
                      brief='Get a loan',
                      help='Get a loan to increase your wallet balance',
                      usage='f!get_loan <amount>')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def get_loan_cmd(self, ctx: CContext, amount: typing.Union[int, str]) -> None:
        if isinstance(amount, str):
            # discord.py tries to convert to int first, if that fails we just get the string
            await ctx.send("You must specify a valid integer amount to get a loan")
            return
            
        if amount <= 0:
            await ctx.send('You must request a positive loan amount!')
            return
        
        profile = curr_utils.get_profile(ctx.author)
        if profile['debt'] > 0:
            await ctx.send('You already have an outstanding loan! Pay it off first.')
            return
        
        if curr_utils.calculate_max_loan(profile) < amount:
            await ctx.send(f'You cannot take a loan of {amount} {currency_name}. ')
            await ctx.send(f'Increase max loan size by increasing income or credit score.')
            return
        
        profile['debt'] = amount
        profile['wallet'] += amount
        curr_utils.set_profile(ctx.author, profile)
        await ctx.send(f'You have taken a loan of {amount} {currency_name}. Remember to pay it back with interest!')
        return
    
    @commands.command(name='credit_score', aliases=['credit'],
                      brief='Check your credit score',
                      help='Check your current credit score',
                      usage='f!credit_score')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def credit_score_cmd(self, ctx: CContext):
        profile = curr_utils.get_profile(ctx.author)
        credit_score = profile['credit_score']
        await ctx.send(f'Your current credit score is {credit_score}. ' +
                       f'Improve it by paying off loans and maintaining a good balance.')
        return
    
    @commands.command(name='shop', aliases=['store'],
                      brief='View the shop',
                      help='View the items available for purchase in the shop',
                      usage='f!shop')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def shop_cmd(self, ctx: CContext):
        embed = discord.Embed(title='Shop', description='Items available for purchase', colour=discord.Colour.green())
        embed.set_thumbnail(url=ctx.guild.icon.url)
        categories = shop_items.categories
        
        # Create list to store category embeds
        embeds: list[discord.Embed] = []
        
        # Add regular categories
        for category in categories:
            category_embed = discord.Embed(
                    title=f'Shop - {category.name}',
                    description=category.description,
                    colour=discord.Colour.green()
            )
            
            # Safely set thumbnail
            if hasattr(ctx.guild, 'icon') and ctx.guild.icon:
                category_embed.set_thumbnail(url=ctx.guild.icon.url)
            
            # Add items for this category
            for item in category.items:
                item_desc = f'{item.description}\nPrice: {item.price:,} {currency_name}'
                if item.stock != -1:
                    item_desc += f'\nStock: {item.stock}'
                category_embed.add_field(name=item.name, value=item_desc, inline=False)
            
            # Add page number to footer
            total_pages = len(categories)
            category_embed.set_footer(text=f'Page {len(embeds) + 1}/{total_pages}')
            embeds.append(category_embed)
        
        # Send the first page with navigation
        if embeds:
            view = ShopView(embeds)
            await ctx.send(embed=embeds[0], view=view)
        else:
            await ctx.send('No items available in the shop.')
        
        return
    
    @commands.command(name='blackmarket', aliases=['bm'],
                      brief='View the black market',
                      help='View the items available for purchase in the black market',
                      usage='f!blackmarket')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def blackmarket_cmd(self, ctx: CContext):
        embed = discord.Embed(title='Black Market', description='Items available for purchase',
                              colour=discord.Colour.dark_red())
        embed.set_thumbnail(url=ctx.guild.icon.url)
        categories = shop_items.bm_categories
        
        # Create list to store category embeds
        embeds: list[discord.Embed] = []
        
        for category in categories:
            category_embed = discord.Embed(
                    title=f'Black Market - {category.name}',
                    description=category.description,
                    colour=discord.Colour.dark_red()
            )
            
            if hasattr(ctx.guild, 'icon') and ctx.guild.icon:
                category_embed.set_thumbnail(url=ctx.guild.icon.url)
            
            for item in category.items:
                item_desc = f'{item.description}\nPrice: {item.price:,} {currency_name}'
                if item.stock != -1:
                    item_desc += f'\nStock: {item.stock}'
                category_embed.add_field(name=item.name, value=item_desc, inline=False)
            
            total_pages = len(categories)
            category_embed.set_footer(text=f'Page {len(embeds) + 1}/{total_pages}')
            embeds.append(category_embed)
        
        if embeds:
            view = ShopView(embeds)
            await ctx.send(embed=embeds[0], view=view)
        else:
            await ctx.send('No items available in the black market.')
        
        return
    
    @commands.command(name='buy', aliases=['purchase'],
                      brief='Buy an item from the shop',
                      help='Buy an item from the shop or black market',
                      usage='f!buy <item_name> [quantity]')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def buy_cmd(self, ctx: CContext, *, arg: str):
        # Split the arguments into item name and quantity
        args: list[str] = arg.strip().split()
        if len(args) < 1:
            await ctx.send('You must specify an item to buy')
            return
        
        try:
            quantity = int(args[-1])
            
            if quantity <= 0:
                await ctx.send('You must buy a positive quantity of the item!')
                return
            q_given = True
        except ValueError:
            quantity = 1
            q_given = False
        
        if q_given:
            item_name = ' '.join(args[:-1]).lower()
        else:
            item_name = ' '.join(args).lower()
        
        item = get_shop_item(item_name)
        if item is None:
            await ctx.send(f"No item found with name '{item_name}'")
            return
        stock = curr_utils.get_stock(item)
        if stock != -1:
            if stock < quantity:
                await ctx.send(f'Not enough stock for {item.name}. Available: {stock}, Requested: {quantity}')
                return
        total_price = int((item.price * curr_config.sales_tax) * quantity)
        profile = curr_utils.get_profile(ctx.author)
        
        if profile['wallet'] < total_price:
            await ctx.send(f'You do not have enough money in your wallet! You need {total_price} {currency_name}.')
            return
        
        # Deduct the price from the user's wallet
        curr_utils.set_wallet(ctx.author, profile['wallet'] - total_price)
        # Update the stock in the database
        if stock != -1:
            # If the item has a stock limit, reduce the stock
            curr_utils.set_stock(item, stock - quantity)
        
        illegal = False
        if isinstance(item, BlackMarketItem):
            # check if the user gets scammed
            scam_chance = random.random()
            if scam_chance <= item.scam_risk:
                await ctx.send(f'You got scammed while trying to buy {item.name}!')
                return
            # check if the user gets caught by cops
            cops_chance = random.random()
            if cops_chance <= item.cops_risk:
                await ctx.send(f'You got caught by the cops while trying to buy {item.name}! \nYou have been fined ' +
                               f'5,000 {currency_name} for illegal activity, remember to pay it off with ' +
                               f'`{ctx.bot.command_prefix}pay_debt`.')
                
                curr_utils.set_fire_risk(ctx.author, 0.3)
                curr_utils.set_debt(ctx.author, profile['debt'] + 5000)  # Add a fine to the user's debt
                return
            illegal = True
        
        # Add the item to the user's inventory
        curr_utils.add_to_inventory(ctx.author, item.name.lower(), quantity, illegal=illegal)
        await ctx.send(f'Successfully bought {quantity}x {item.name} for {total_price} {currency_name}!')
        return
    
    @commands.command(name='inventory', aliases=['inv'],
                      brief='Check your inventory',
                      help='Check the items you own in your inventory',
                      usage='f!inventory')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def inventory_cmd(self, ctx: CContext):
        profile = curr_utils.get_profile(ctx.author)
        inventory = profile['inventory']
        if not inventory:
            await ctx.send('Your inventory is empty.')
            return
        
        inv_list = '\n'.join(f'{item}: {quantity}' for item, quantity in inventory.items())
        await ctx.send(f'**Your Inventory:**\n{inv_list}')
        
        illegal_items = profile['illegal_items']
        if illegal_items:
            illegal_list = '\n'.join(f'{item}: {quantity}' for item, quantity in illegal_items.items())
            await ctx.send(f'**Illegal Items:**\n{illegal_list}')
        return
    
    @commands.command(name='use', aliases=['use_item'],
                      brief='Use an item from your inventory',
                      help='Use an item from your inventory to gain its benefits',
                      usage='f!use <item_name>')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def use_cmd(self, ctx: CContext, *, item_name: str):
        profile: Profile = curr_utils.get_profile(ctx.author)
        inventory: dict[str, int] = profile['inventory']
        illegal_items: dict[str, int] = profile['illegal_items']
        item_name = item_name.lower()
        illegal: bool = False
        if item_name not in [key.lower() for key in inventory.keys()] and item_name not in [key.lower() for key in
                                                                                            illegal_items.keys()]:
            await ctx.send(f'You do not own any {item_name}!')
            return
        if item_name in illegal_items:
            illegal = True
            inventory = illegal_items
        
        item_quantity: int = inventory[item_name]
        if item_quantity <= 0:
            await ctx.send(f'You do not own any {item_name}!')
            return
        
        item: ShopItem | None = get_shop_item(item_name)
        if item is None:
            await ctx.send(f"No item found with name '{item_name}'")
            return
        
        # Decrease the quantity in the inventory
        remove: bool = False
        if not isinstance(item, GunItem):
            inventory[item_name] -= 1
            if inventory[item_name] <= 0:
                del inventory[item_name]
                remove = True
        else:
            remove = False
        
        if remove:
            if illegal:
                curr_utils.remove_illegal_item(ctx.author, item_name)
            else:
                curr_utils.remove_from_inventory(ctx.author, item_name)
        
        else:
            if illegal:
                curr_utils.set_illegal_items(ctx.author, item_name, inventory[item_name])
            else:
                curr_utils.set_inventory(ctx.author, item_name, inventory[item_name])
        
        if isinstance(item, DrugItem):
            od = random.random() <= item.od_chance
            if od:
                await ctx.send(f'You used {item.name} and overdosed! You died.')
                curr_utils.set_wallet(ctx.author, profile['wallet'] // 4)
                curr_utils.set_bank(ctx.author, profile['bank'] // 4)
                curr_utils.clear_inventory(ctx.author)
                return
            else:
                await ctx.send(f'You used {item.name} and felt its effects.')
                curr_utils.set_next_income_multiplier(ctx.author, item.income_multiplier)
                currency.curr_utils.set_fire_risk(ctx.author, item.work_catch_risk)
                return
        
        elif isinstance(item, GunItem):
            await ctx.send(f'You cannot use guns directly.')
            await ctx.send(f'Use them in a command that requires a gun, like `hunt` or `rob`.')
        return
    
    @commands.command(name='sell',
                      brief='Sell an item from your inventory',
                      help='Sell an item from your inventory for money',
                      usage='f!sell <item_name> [quantity]')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def sell_cmd(self, ctx: CContext, *, arg: str):
        # Split the arguments into item name and quantity
        args: list[str] = arg.strip().split()
        if len(args) < 1:
            await ctx.send('You must specify an item to sell')
            return
        try:
            quantity = int(args[-1])
            if quantity <= 0:
                await ctx.send('You must sell a positive quantity of the item!')
                return
            q_given = True
        except ValueError:
            quantity = 1
            q_given = False
        if q_given:
            item_name = ' '.join(args[:-1]).lower()
        else:
            item_name = ' '.join(args).lower()
        
        profile = curr_utils.get_profile(ctx.author)
        inventory = profile['inventory']
        illegal_items = profile['illegal_items']
        if item_name not in inventory.keys() and item_name not in illegal_items.keys():
            await ctx.send(f'You do not own any {item_name}!')
            return
        
        illegal = False
        if item_name in illegal_items:
            inventory = illegal_items
            illegal = True
        item_quantity = inventory[item_name]
        if item_quantity <= 0:
            await ctx.send(f'You do not own any {item_name}!')
            return
        
        if item_quantity < quantity:
            await ctx.send(
                    f'You do not own enough {item_name} to sell! You have {item_quantity}, but requested {quantity}.')
            return
        
        item: ShopItem | None = get_shop_item(item_name)
        if item is None:
            await ctx.send(f"No item found with name '{item_name}'")
            return
        
        # Calculate the total price
        if isinstance(item, BlackMarketItem):
            total_price = int(item.price * item.resale_mult * quantity)
        elif isinstance(item, HouseItem):
            total_price = int(item.price * 0.9 * quantity)
        else:
            total_price = int(item.price * 0.5 * quantity)
        
        # Add the price to the user's wallet
        curr_utils.set_wallet(ctx.author, profile['wallet'] + total_price)
        # Update the inventory
        if illegal:
            inventory[item_name] -= quantity
            if inventory[item_name] <= 0:
                curr_utils.remove_illegal_item(ctx.author, item_name)
            else:
                curr_utils.set_illegal_items(ctx.author, item_name, inventory[item_name])
        else:
            inventory[item_name] -= quantity
            if inventory[item_name] <= 0:
                curr_utils.remove_from_inventory(ctx.author, item_name)
            else:
                curr_utils.set_inventory(ctx.author, item_name, inventory[item_name])
        
        await ctx.send(f'Sold {quantity}x {item.name} for {total_price} {currency_name}!')
        return
    
    @commands.command(name='jobs',
                      brief='View available jobs',
                      help='View the jobs you can take to earn money',
                      usage='f!jobs')
    @commands.cooldown(1, 4 * 60 * 60, commands.BucketType.user)  # type: ignore
    async def jobs_cmd(self, ctx: CContext):
        global salary_offers
        salary_offers[ctx.author.id] = {}
        profile = curr_utils.get_profile(ctx.author)
        school_qualif = SchoolQualif.from_string(profile['qualifications'][0])
        clearance = SecurityClearance.from_string(profile['qualifications'][1])
        
        embed = discord.Embed(title='Available Jobs', colour=discord.Colour.blue())
        embed.set_thumbnail(url=ctx.guild.icon.url if hasattr(ctx.guild, 'icon') and ctx.guild.icon else None)
        
        for tree in job_trees:
            # Make a copy of the jobs list to safely reverse it
            jobs_reversed = list(tree.jobs)
            jobs_reversed.reverse()
            
            # Process jobs from most advanced to most basic
            for job_or_job_list in jobs_reversed:
                # Handle both individual jobs and lists of jobs
                if isinstance(job_or_job_list, list):
                    job_list = job_or_job_list
                else:
                    job_list = [job_or_job_list]
                
                # Check if user qualifies for any job at this level
                qualified_jobs = []
                for job in job_list:
                    if (profile['work_experience'] >= job.req_experience and
                            school_qualif >= job.school_requirement and
                            clearance >= job.security_clearance):
                        qualified_jobs.append(job)
                
                # If we found qualified jobs at this level, add them and break
                if qualified_jobs:
                    for job in qualified_jobs:
                        if job.tree == profile['work_tree']:
                            continue
                        # Calculate the salary with variance to 0.01% precision
                        salary_mult = 1 + (random.randint(0,
                                                          job.salary_variance * 10) / 1000)  # salary variance is an int for percentage
                        salary = int(job.salary * salary_mult)
                        salary_offers[ctx.author.id][job.name] = salary
                        value = (f'Yearly salary: {salary} {currency_name}\n'
                                 f'Required Work Experience: {job.req_experience} years\n')
                        if job.school_requirement != SchoolQualif.HIGH_SCHOOL:
                            value += f'School Requirement: {job.school_requirement.to_string()}\n'
                        if job.security_clearance != SecurityClearance.NONE:
                            value += f'Clearance: {job.security_clearance.to_string()}\n'
                        if job.experience_multiplier > 1.0:
                            value += f'Work Experience Multiplier: {job.experience_multiplier}x'
                        
                        embed.add_field(
                                name=f'{job.name} ({tree.name.replace('_', ' ').title()})',
                                value=value,
                                inline=False
                        )
                    # Break after finding the highest level with qualified jobs
                    break
        
        if len(embed.fields) == 0:
            embed.description = 'No jobs available for your qualifications yet.'
        
        await ctx.send(embed=embed)
        return
    
    @commands.command(name='job',
                      brief='Apply for a job',
                      help='Apply for a job from the available jobs list',
                      usage='f!job <job_name>')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def job_cmd(self, ctx: CContext, *, job_name: str):
        global salary_offers
        if ctx.author.id not in salary_offers or not salary_offers[ctx.author.id]:
            await ctx.send('You have no job offers currently. View available jobs using `jobs` command.')
            return
        
        profile = curr_utils.get_profile(ctx.author)
        if profile['work_income'] > 0:
            await ctx.send('You already have a job! Quit your current job first using `quit` command.')
            return
        
        job_name = job_name.strip().lower()
        matched_job = None
        for offered_job in salary_offers[ctx.author.id].keys():
            if offered_job.lower() == job_name:
                matched_job = offered_job
                break
        
        if matched_job is None:
            await ctx.send(
                    f'No job offer found with name "{job_name}". Please check the available jobs using `jobs` command.')
            return
        
        job_obj = job_utils.job_from_name(matched_job, job_trees)
        if job_obj is None:
            await ctx.send('An error occurred while processing the command. Please try again later.')
            return
        
        # Assign the job to the user
        salary = salary_offers[ctx.author.id][matched_job]
        curr_utils.set_job(ctx.author, job_obj, salary)
        curr_utils.inc_age(ctx.author)
        # Clear the job offers after applying
        salary_offers[ctx.author.id] = {}
        await ctx.send(
                f'Congratulations! You have been hired as a {matched_job} with a salary of {salary} {currency_name}.')
        return
    
    @commands.command(name='profile',
                      brief='Check your profile',
                      help='Check your job, income, qualifications, and other details',
                      usage='f!profile')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def profile_cmd(self, ctx: CContext):
        profile = curr_utils.get_profile(ctx.author)
        embed = discord.Embed(title=f"{ctx.author.display_name}'s Profile", colour=discord.Colour.purple())
        embed.set_thumbnail(url=ctx.author.display_avatar.url if hasattr(ctx.author,
                                                                         'display_avatar') and ctx.author.display_avatar else None)
        
        embed.add_field(name='Job', value=profile['work_tree'] if profile['work_income'] > 0 else 'Unemployed',
                        inline=True)
        embed.add_field(name='Income', value=f"{profile['work_income'] // 12} {currency_name} per month " +
                                             f"including tax" if profile['work_income'] > 0 else 'N/A', inline=True)
        embed.add_field(name='Work Experience', value=f"{profile['work_experience'] // 12} years", inline=True)
        embed.add_field(name='Qualifications', value=', '.join(profile['qualifications'])
        if profile['qualifications'][0] != 'None' else '', inline=False)
        embed.add_field(name='Debt', value=f"{profile['debt']} {currency_name}" if profile['debt'] > 0 else 'No debt',
                        inline=True)
        embed.add_field(name='Age', value=f"{profile['age'] // 12} years", inline=True)
        
        await ctx.send(embed=embed)
        return


async def setup(bot: commands.Bot) -> None:
    pass
    # await bot.add_cog(CurrencyCmds(bot))
