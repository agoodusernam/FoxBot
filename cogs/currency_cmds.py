import random
import typing
from decimal import Decimal

import discord
from discord.ext import commands

from command_utils.CContext import CContext
from command_utils.checks import is_dev
from currency import collector, curr_utils
from currency.currency_types import BlackMarketItem, DrugItem, GunItem, HouseItem, JobTree, Profile, SchoolQualif, SecurityClearance, ShopItem
from currency.curr_config import CURRENCY_NAME, INTEREST_RATE, SALES_TAX

salary_offers: dict[int, dict[str, int]] = {}
cached_profiles: dict[str, Profile] = {}

async def get_profile(user_id: int | str | discord.User | discord.Member) -> Profile:
    key: str
    if isinstance(user_id, int):
        key = str(user_id)
    elif isinstance(user_id, (discord.User, discord.Member)):
        key = str(user_id.id)
    else:
        key = user_id
    if key not in cached_profiles:
        cached_profiles[key] = await Profile.fetch_from_user_id(key)
    return cached_profiles[key]

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
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def balance_cmd(self, ctx: CContext):
        profile = await get_profile(ctx.author.id)
        wallet = int(profile.wallet)
        bank = int(profile.bank)
        await ctx.send(f'**Balance:**\nWallet: {wallet}\nBank: {bank}\nTotal: {wallet + bank}')
    
    @commands.command(name='baltop', aliases=['balance_top', 'bal_top'],
                      brief='Check the top balances',
                      help='Check the top users with the highest balances',
                      usage='f!baltop')
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def baltop_cmd(self, ctx: CContext):
        top_users = await curr_utils.get_top_balances()
        if not top_users:
            await ctx.send('Not enough users found in the database.')
            return
        
        top_list = '\n'
        for entry in top_users:
            user = discord.utils.get(ctx.bot.get_all_members(), id=entry['user_id'])
            if user is None:
                continue
            top_list += f"{user.display_name}: {entry['wallet']} {CURRENCY_NAME}\n"
        await ctx.send(f'**Top Wallet Balances:**\n{top_list}')
    
    @commands.command(name='deposit', aliases=['dep'],
                      brief='Deposit money into your bank',
                      help='Deposit some of your money from your wallet into your bank',
                      usage='f!deposit <amount>')
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def deposit_cmd(self, ctx: CContext, amount: int):
        if amount <= 0:
            await ctx.send('You must deposit a positive amount!')
            return
        profile = await get_profile(ctx.author)
        if profile.wallet < amount:
            await ctx.send('You do not have enough money in your wallet!')
            return
        profile.wallet -= amount
        profile.bank += amount
 
        await ctx.send(f'Deposited {amount} {CURRENCY_NAME} into your bank!')
    
    @commands.command(name='withdraw', aliases=['with'],
                      brief='Withdraw money from your bank',
                      help='Withdraw some of your money from your bank into your wallet',
                      usage='f!withdraw <amount>')
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def withdraw_cmd(self, ctx: CContext, amount: int):
        if amount <= 0:
            await ctx.send('You must withdraw a positive amount!')
            return
        profile = await get_profile(ctx.author)
        if profile.bank < amount:
            await ctx.send('You do not have enough money in your bank!')
            return
        
        profile.bank -= amount
        profile.wallet += amount
 
        await ctx.send(f'Withdrew {amount} {CURRENCY_NAME} from your bank!')
    
    @commands.command(name='pay', aliases=['give'],
                      brief='Pay another user',
                      help='Pay another user some of your money',
                      usage='f!pay <user> <amount>')
    @commands.cooldown(1, 5, commands.BucketType.user)  
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
        payer_profile = await get_profile(ctx.author)
        if payer_profile.wallet < amount:
            await ctx.send('You do not have enough money in your wallet!')
            return
        
        recipient_profile = await get_profile(user)
        payer_profile.wallet -= amount
        recipient_profile.wallet += amount
        await ctx.send(f'Paid {user.mention} {amount} {CURRENCY_NAME}!')
    
    @commands.command(name='work',
                      brief='Work to earn money',
                      help='Work to earn some money. You can do this every day.')
    @commands.cooldown(1, 24 * 60 * 60, commands.BucketType.user)  
    async def work_cmd(self, ctx: CContext):
        #TODO: Check for promotions and raises
        profile = await get_profile(ctx.author)
        if profile.work_income <= 0:
            await ctx.send(f'You have no job! Choose a job first using `{ctx.bot.command_prefix}job`.')
            return
            
        profile.inc_age()
        fired = profile.fire_chance > random.random()
        if fired:
            await ctx.send('You were fired from your job! You need to find a new job using the `job` command.')
            await ctx.send('A severance package has been deposited into your wallet.')
            profile.fire()
     
            return
        
        with profile.batch():
            if profile.debt > 0:
                profile.debt = profile.debt * (1 + INTEREST_RATE)
                
            profile.wallet += profile.work_income
            profile.work_experience += 1 * profile.job.experience_multiplier
            profile.next_income_mult = 1.0 # Reset income multiplier after working
            profile.fire_chance *= 0.8  # Working reduces fire risk
        
        if profile.work_experience % 12 == 11:
            # Every year of experience, give them a raise between 1 and 5%
            raise_amount = random.uniform(0.01, 0.05)
            profile.work_income = profile.work_income * Decimal(1 + raise_amount)
            await ctx.send(f'You have been a good employee and received a {raise_amount*100:.1f}% raise!')
        
        next_job = profile.job.get_next_job()
        if isinstance(next_job, list):
            next_job = next_job[0]
        
        if next_job is None:
            await ctx.send(f'You worked hard and earned {profile.earnings} {CURRENCY_NAME}!')
            return
            
        exp_qualified = False
        school_qualified = False
        clearance_qualified = False
        if profile.work_experience >= next_job.req_experience:
            exp_qualified = True
        if profile.school_qualification >= next_job.req_school:
            school_qualified = True
        if profile.security_clearance >= next_job.req_clearance:
            clearance_qualified = True
        
        if exp_qualified and school_qualified and clearance_qualified:
            profile.job = next_job
            salary_multiplier = 1 + (random.randint(0, next_job.salary_variance * 10) /1000)
            # Salary multiplier to 0.1% precision
            profile.work_income = next_job.salary * Decimal(salary_multiplier)
            await ctx.send(f'Congratulations! You have been promoted to {next_job.name}!')
            await ctx.send(f'New income: {profile.work_income} {CURRENCY_NAME} per year.')
            
        elif not exp_qualified:
            # Don't notify if they wouldn't have the experience to get a promotion
            pass
        
        elif not school_qualified:
            await ctx.send(f'You need a higher school qualification to be promoted to {next_job.name}.')
            await ctx.send(f'Required: {next_job.req_school.to_string()}, You have: {profile.school_qualification.to_string()}')
            await ctx.send(f'Use `{ctx.bot.command_prefix}school` to study for a higher qualification.')
            
        elif not clearance_qualified:
            await ctx.send(f'You need a higher security clearance to be promoted to {next_job.name}.')
            await ctx.send(f'Required: {next_job.req_clearance.to_string()}, You have: {profile.security_clearance.to_string()}')
            await ctx.send(f"Use `{ctx.bot.command_prefix}clearance` to apply for a higher clearance level.")
        
        
 
        await ctx.send(f'You worked hard and earned {profile.earnings} {CURRENCY_NAME}')
    
    @commands.command(name='quit',
                      brief='Quit your current job',
                      help='Quit your current job so you can get a new one',
                      usage='f!quit')
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def quit_cmd(self, ctx: CContext):
        profile = await get_profile(ctx.author)
        if profile.work_income <= 0:
            await ctx.send('You have no job to quit! Choose a job first using `job`.')
            return
        
        profile.reset_job()
        
        await ctx.send('You have quit your job. You can now choose a new job using the `job` command.')
    
    @commands.command(name='debt',
                      brief='Check your debt',
                      help='Check how much debt you have')
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def debt_cmd(self, ctx: CContext):
        profile = await get_profile(ctx.author)
        if profile.debt <= 0:
            await ctx.send('You have no debt!')
        else:
            await ctx.send(f'You currently owe {profile.debt} {CURRENCY_NAME} in loans.')
    
    @commands.command(name='pay_debt', aliases=['payloan', 'pay_loan', 'repay', 'paydebt'],
                      brief='Pay off your debt',
                      help='Pay off some of your debt from loans',
                      usage='f!pay_debt <amount>')
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def pay_debt_cmd(self, ctx: CContext, amount: int):
        if amount <= 0:
            await ctx.send('You must pay a positive amount!')
            return
        profile = await get_profile(ctx.author)
        if profile.debt < amount:
            amount = int(profile.debt)  # If they try to pay more than they owe, pay off the entire debt
        
        if profile.wallet < amount:
            await ctx.send('You do not have enough money in your wallet to pay off that much debt!')
            return
        
        intrest = int(profile.debt * INTEREST_RATE)
        if amount >= intrest:
            profile.credit_score = min(profile.credit_score + 1, 800)
        
        elif amount < (intrest * 0.75):
            profile.credit_score = max(profile.credit_score - 1, 100)
        
        profile.debt -= amount
        profile.wallet -= amount
        
        if profile.debt > 0:
            await ctx.send(f'Paid off {amount} {CURRENCY_NAME} of your debt!')
        else:
            await ctx.send(f'You have paid off all your {amount} {CURRENCY_NAME} debt!')
        
 
    
    @commands.command(name='get_loan', aliases=['loan'],
                      brief='Get a loan',
                      help='Get a loan to increase your wallet balance',
                      usage='f!get_loan <amount>')
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def get_loan_cmd(self, ctx: CContext, amount: typing.Union[int, str]) -> None:
        if isinstance(amount, str):
            # discord.py tries to convert to int first, if that fails we just get the string
            await ctx.send("You must specify a valid integer amount to get a loan")
            return
            
        if amount <= 0:
            await ctx.send('You must request a positive loan amount!')
            return
        
        profile = await get_profile(ctx.author)
        if profile.debt > 0:
            await ctx.send('You already have an outstanding loan! Pay it off first.')
            return
        
        if profile.max_loan < amount:
            await ctx.send(f'You cannot take a loan of {amount} {CURRENCY_NAME}. ')
            await ctx.send(f'Increase max loan size by increasing income or credit score.')
            return
        
        profile.debt = Decimal(amount)
        profile.wallet += amount
 
        await ctx.send(f'You have taken a loan of {amount} {CURRENCY_NAME}. Remember to pay it back with interest!')
        return
    
    @commands.command(name='credit_score', aliases=['credit'],
                      brief='Check your credit score',
                      help='Check your current credit score',
                      usage='f!credit_score')
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def credit_score_cmd(self, ctx: CContext):
        profile = await get_profile(ctx.author)
        credit_score = profile.credit_score
        await ctx.send(f'Your current credit score is {credit_score}. ' +
                       f'Improve it by paying off loans and maintaining a good balance.')
        return
    
    @commands.command(name='shop', aliases=['store'],
                      brief='View the shop',
                      help='View the items available for purchase in the shop',
                      usage='f!shop')
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def shop_cmd(self, ctx: CContext):
        embed = discord.Embed(title='Shop', description='Items available for purchase', colour=discord.Colour.green())
        if ctx.guild is not None and hasattr(ctx.guild, 'icon') and ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        categories = collector.all_normal_shop_categories
        
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
            if ctx.guild is not None and hasattr(ctx.guild, 'icon') and ctx.guild.icon:
                category_embed.set_thumbnail(url=ctx.guild.icon.url)
            
            # Add items for this category
            for item in category.items:
                item_desc = f'{item.description}\nPrice: {item.price:,} {CURRENCY_NAME}'
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
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def blackmarket_cmd(self, ctx: CContext):
        embed = discord.Embed(title='Black Market', description='Items available for purchase',
                              colour=discord.Colour.dark_red())
        if ctx.guild is not None and hasattr(ctx.guild, 'icon') and ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        categories = collector.all_bm_shop_categories
        
        # Create list to store category embeds
        embeds: list[discord.Embed] = []
        
        for category in categories:
            category_embed = discord.Embed(
                    title=f'Black Market - {category.name}',
                    description=category.description,
                    colour=discord.Colour.dark_red()
            )
            
            if ctx.guild is not None and hasattr(ctx.guild, 'icon') and ctx.guild.icon:
                category_embed.set_thumbnail(url=ctx.guild.icon.url)
            
            for item in category.items:
                item_desc = f'{item.description}\nPrice: {item.price:,} {CURRENCY_NAME}'
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
    @commands.cooldown(1, 5, commands.BucketType.user)  
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
        
        item = collector.item_from_str(item_name)
        if item is None:
            await ctx.send(f"No item found with name '{item_name}'")
            return
        stock = await curr_utils.get_stock(item)
        if stock != -1:
            if stock < quantity:
                await ctx.send(f'Not enough stock for {item.name}. Available: {stock}, Requested: {quantity}')
                return
        total_price: Decimal = (item.price * SALES_TAX) * quantity
        profile = await get_profile(ctx.author)
        
        if profile.wallet < total_price:
            await ctx.send(f'You do not have enough money in your wallet! You need {round(total_price, 2)} {CURRENCY_NAME}.')
            return
        
        # Deduct the price from the user's wallet
        profile.wallet -= total_price
        # Update the stock in the database
        if stock != -1:
            # If the item has a stock limit, reduce the stock
            await curr_utils.set_stock(item, stock - quantity)
        
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
                               f'5,000 {CURRENCY_NAME} for illegal activity, remember to pay it off with ' +
                               f'`{ctx.bot.command_prefix}pay_debt`.')
                
                profile.fire_chance = 0.3
                profile.debt += 5000
                return
            illegal = True
        
        # Add the item to the user's inventory
        if illegal:
            profile.add_bm_item(item.name, quantity)
        else:
            profile.add_normal_item(item.name, quantity)
        await ctx.send(f'Successfully bought {quantity}x {item.name} for {total_price} {CURRENCY_NAME}!')
        return
    
    @commands.command(name='inventory', aliases=['inv'],
                      brief='Check your inventory',
                      help='Check the items you own in your inventory',
                      usage='f!inventory')
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def inventory_cmd(self, ctx: CContext):
        profile = await get_profile(ctx.author)
        inventory = profile.inventory
        if not inventory:
            await ctx.send('Your inventory is empty.')
            return
        
        inv_list = '\n'.join(f'{item}: {quantity[1]}' for item, quantity in inventory.items())
        await ctx.send(f'**Your Inventory:**\n{inv_list}')
        
        illegal_items = profile.bm_inventory
        if illegal_items:
            illegal_list = '\n'.join(f'{item}: {quantity[1]}' for item, quantity in illegal_items.items())
            await ctx.send(f'**Illegal Items:**\n{illegal_list}')
        return
    
    @commands.command(name='use', aliases=['use_item'],
                      brief='Use an item from your inventory',
                      help='Use an item from your inventory to gain its benefits',
                      usage='f!use <item_name>')
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def use_cmd(self, ctx: CContext, *, item_name: str) -> None:
        profile: Profile = await get_profile(ctx.author)
        item_name = item_name.lower()
        active_inv: dict[str, tuple[BlackMarketItem | ShopItem, int]]
        active_inv = profile.inventory
        illegal: bool = False
        if item_name not in profile.inventory and item_name not in profile.bm_inventory:
            await ctx.send(f'You do not own any {item_name}!')
            return
        if item_name in profile.bm_inventory:
            illegal = True
            active_inv = profile.bm_inventory # type: ignore
        
        item_quantity: int = active_inv[item_name][1]
        if item_quantity <= 0:
            await ctx.send(f'You do not own any {item_name}!')
            return
        
        item = active_inv[item_name][0]
        
        
        if illegal:
            profile.remove_bm_item(item_name)
        else:
            profile.remove_normal_item(item_name)
        
        
        if isinstance(item, DrugItem):
            od = random.random() <= item.od_chance
            if od:
                await ctx.send(f'You used {item.name} and overdosed! You died.')
                with profile.batch():
                    profile.wallet /= 4
                    profile.bank /= 4
                    profile.clear_inventory()
                    profile.clear_bm_inventory()
                return
            else:
                await ctx.send(f'You used {item.name} and felt its effects.')
                with profile.batch():
                    profile.next_income_mult = item.ranged_income_mult()
                    profile.fire_chance =  item.work_catch_risk
                return
        
        elif isinstance(item, GunItem):
            await ctx.send(f'You cannot use guns directly.')
            await ctx.send(f'Use them in a command that requires a gun, like `hunt` or `rob`.')
        return
    
    @commands.command(name='sell',
                      brief='Sell an item from your inventory',
                      help='Sell an item from your inventory for money',
                      usage='f!sell <item_name> [quantity]')
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def sell_cmd(self, ctx: CContext, item_name: str, amount: int = 1):
        # Split the arguments into item name and quantity
        item_name = item_name.lower().strip()
        
        profile = await get_profile(ctx.author)
        if item_name not in profile.inventory and item_name not in profile.bm_inventory:
            await ctx.send(f'You do not own any {item_name}!')
            return
        
        item: ShopItem | BlackMarketItem
        
        if item_name in profile.bm_inventory:
            illegal = True
            item, item_quantity = profile.bm_inventory[item_name]
        else:
            illegal = False
            item, item_quantity = profile.inventory[item_name]
        if item_quantity <= 0:
            await ctx.send(f'You do not own any {item_name}!')
            return
            
        # Calculate the total price
        if isinstance(item, BlackMarketItem):
            total_price = Decimal(item.price * item.resale_mult * amount)
        elif isinstance(item, HouseItem):
            total_price = Decimal(item.price * 0.9 * amount)
        else:
            total_price = Decimal(item.price * 0.5 * amount)
        
        # Add the price to the user's wallet
        profile.wallet += total_price
        item_quantity = min(item_quantity, amount)
        # Update the inventory
        if illegal:
            profile.remove_bm_item(item_name, item_quantity)
        else:
            profile.remove_normal_item(item_name, item_quantity)
        
        await ctx.send(f'Sold {item_quantity}x {item.name} for {total_price} {CURRENCY_NAME}!')
        return
    
    @commands.command(name='jobs',
                      brief='View available jobs',
                      help='View the jobs you can take to earn money',
                      usage='f!jobs')
    @commands.cooldown(1, 4 * 60 * 60, commands.BucketType.user)
    async def jobs_cmd(self, ctx: CContext):
        global salary_offers
        salary_offers[ctx.author.id] = {}
        profile = await get_profile(ctx.author)
        
        embed = discord.Embed(title='Available Jobs', colour=discord.Colour.blue())
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        
        for tree in collector.all_job_trees:
            best_jobs = self._get_best_qualified_jobs(tree, profile)

            for job in best_jobs:
                if job.name == profile.job.name:
                    continue

                salary_mult = 1 + (random.randint(0, job.salary_variance * 10) / 1000)
                salary = int(job.salary * salary_mult)
                salary_offers[ctx.author.id][job.name] = salary

                value = (f'Yearly salary: {salary} {CURRENCY_NAME}\n'
                         f'Required Work Experience: {job.req_experience} years\n')
                if job.req_school != SchoolQualif.HIGH_SCHOOL:
                    value += f'School Requirement: {job.req_school.to_string()}\n'
                if job.req_clearance != SecurityClearance.NONE:
                    value += f'Clearance: {job.req_clearance.to_string()}\n'
                if job.experience_multiplier > 1.0:
                    value += f'Work Experience Multiplier: {job.experience_multiplier}x'

                embed.add_field(
                    name=f"{job.name} ({tree.name.replace('_', ' ').title()})",
                    value=value,
                    inline=False
                )

        if len(embed.fields) == 0:
            embed.description = 'No jobs available for your qualifications yet.'

        await ctx.send(embed=embed)

    @staticmethod
    def _get_best_qualified_jobs(tree: 'JobTree', profile: 'Profile') -> list:
        """Walk the tree from highest level to lowest. Return the jobs at the
        first (i.e. best) level the user fully qualifies for."""
        for level in reversed(tree.jobs):
            jobs_at_level = level if isinstance(level, list) else [level]

            qualified = [
                job for job in jobs_at_level
                if (profile.work_experience >= job.req_experience
                    and profile.school_qualification >= job.req_school
                    and profile.security_clearance >= job.req_clearance)
            ]

            if qualified:
                return qualified

        return []
    
    @commands.command(name='job',
                      brief='Apply for a job',
                      help='Apply for a job from the available jobs list',
                      usage='f!job <job_name>')
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def job_cmd(self, ctx: CContext, *, job_name: str):
        global salary_offers
        if ctx.author.id not in salary_offers or not salary_offers[ctx.author.id]:
            await ctx.send('You have no job offers currently. View available jobs using `jobs` command.')
            return
        
        profile = await get_profile(ctx.author)
        if profile.work_income > 0:
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
        
        job_obj = collector.job_from_str(matched_job)
        if job_obj is None:
            await ctx.send('An error occurred while processing the command. Please try again later.')
            return
        
        # Assign the job to the user
        salary = salary_offers[ctx.author.id][matched_job]
        profile.set_job(job_obj, salary)
        profile.inc_age()
        # Clear the job offers after applying
        salary_offers[ctx.author.id] = {}
        await ctx.send(
                f'Congratulations! You have been hired as a {matched_job} with a salary of {salary} {CURRENCY_NAME}.')
        return
    
    @commands.command(name='profile',
                      brief='Check your profile',
                      help='Check your job, income, qualifications, and other details',
                      usage='f!profile')
    @commands.cooldown(1, 5, commands.BucketType.user)  
    async def profile_cmd(self, ctx: CContext):
        profile = await get_profile(ctx.author)
        embed = discord.Embed(title=f"{ctx.author.display_name}'s Profile", colour=discord.Colour.purple())
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        
        embed.add_field(name='Job', value=profile.job.name, inline=True)
        embed.add_field(name='Income', value=f"{profile.work_income // 12} {CURRENCY_NAME} per month " +
                                             f"before taxes" if profile.work_income > 0 else '0', inline=True)
        embed.add_field(name='Work Experience', value=f"{profile.work_experience // 12} years", inline=True)
        embed.add_field(name='School qualification', value=profile.school_qualification.to_string(), inline=True)
        if profile.security_clearance != SecurityClearance.NONE:
            embed.add_field(name='Security Clearance', value=profile.security_clearance.to_string(), inline=True)
        embed.add_field(name='Age', value=profile.age, inline=True)
        embed.add_field(name='Bank Balance', value=f"{profile.bank} {CURRENCY_NAME}", inline=True)
        embed.add_field(name='Wallet Balance', value=f"{profile.wallet} {CURRENCY_NAME}", inline=True)
        embed.add_field(name='Debt', value=f"{profile.debt} {CURRENCY_NAME}", inline=True)
        embed.add_field(name='Inventory', value=f"{len(profile.inventory)} items", inline=True)
        embed.add_field(name='Debt', value=f"{profile.debt} {CURRENCY_NAME}" if profile.debt > 0 else 'No debt',
                        inline=True)
        embed.add_field(name='Age', value=f"{profile.age // 12} years", inline=True)
        
        await ctx.send(embed=embed)
        return


async def setup(bot: commands.Bot) -> None:
    pass
    # await bot.add_cog(CurrencyCmds(bot))
