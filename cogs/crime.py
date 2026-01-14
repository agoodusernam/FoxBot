import math
import random

import discord
from discord.ext import commands

from command_utils.CContext import CContext
from command_utils.checks import is_dev
from currency import curr_utils, curr_config
from currency.curr_config import Profile


async def rob_success(ctx: CContext, profile: Profile, target: discord.Member, target_profile:
                        Profile, min: float = 0.01, max: float = 0.1):
    amount = math.floor(target_profile['wallet'] * random.uniform(min, max))
    if amount > 0:
        await ctx.send(f'You successfully robbed {target.display_name} and stole some money!')
        target_profile['wallet'] -= amount
        profile['wallet'] += amount
        await curr_utils.set_profile(target, target_profile)
        await curr_utils.set_profile(ctx.author, profile)
        await ctx.send(f'You stole {amount} {curr_config.currency_name} from {target.display_name}!')
        return
    else:
        await ctx.send(f'{target.display_name} has no money to steal!')
        return


async def rob_success_og(ctx: CContext, profile: Profile, target: discord.Member,
                         target_profile: Profile):
    await ctx.send(f'You successfully robbed {target.display_name} and stole some money!')
    # Calculate the amount to steal, between 1 and 5% of the target's wallet
    amount = math.floor(target_profile['wallet'] * random.uniform(0.01, 0.05))
    if amount > 0:
        target_profile['wallet'] -= amount
        profile['wallet'] += amount
        await curr_utils.set_wallet(target, target_profile['wallet'])
        await curr_utils.set_wallet(ctx.author, profile['wallet'])
        await ctx.send(f'You stole {amount} {curr_config.currency_name} from {target.display_name}!')
        return
    else:
        await ctx.send(f'{target.display_name} has no money to steal!')
        return


async def got_shot(ctx: CContext, profile: Profile, target: discord.Member):
    await ctx.send(f'You were caught trying to rob {target.display_name} and got shot!')
    # Deduct a random amount from the user's wallet
    amount = random.randint(2000, 20000)
    payable = 0
    added_to_debt = False
    if profile['wallet'] >= amount:
        profile['wallet'] -= amount
        await curr_utils.set_wallet(ctx.author, profile['wallet'])
    elif profile['bank'] >= amount:
        profile['bank'] -= amount
        await curr_utils.set_bank(ctx.author, profile['bank'])
    elif profile['wallet'] + profile['bank'] >= amount:
        # If the user has enough in total, deduct from wallet first, then bank
        remaining_amount = amount - profile['wallet']
        profile['wallet'] = 0
        await curr_utils.set_wallet(ctx.author, profile['wallet'])
        
        if remaining_amount > 0:
            profile['bank'] -= remaining_amount
            await curr_utils.set_bank(ctx.author, profile['bank'])
    elif profile['wallet'] + profile['bank'] < amount:
        # If the user has less than the amount in total, deduct everything and add the rest to debt
        payable = profile['wallet'] + profile['bank']
        profile['wallet'] = 0
        profile['bank'] = 0
        await curr_utils.set_wallet(ctx.author, profile['wallet'])
        await curr_utils.set_bank(ctx.author, profile['bank'])
        profile['debt'] += (amount - payable)
        await curr_utils.set_debt(ctx.author, profile['debt'])
        added_to_debt = True
    
    await ctx.send(f'You had to pay {amount} {curr_config.currency_name} in medical bills.')
    if added_to_debt and payable > 0:
        await ctx.send(
                f"As you couldn't pay it all of at once, {amount - payable} {curr_config.currency_name} was added to " +
                f'your debt, remember to pay it back!'
        )
    return


class CrimeCog(commands.Cog, name='Crime', command_attrs=dict(hidden=True, add_check=is_dev)):
    """
    A cog for handling crime-related commands in the bot.
    """
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='rob', aliases=['steal'],
                      brief='Rob someone',
                      help="Attempt to steal from someone's wallet.",
                      usage='rob <target>')
    @commands.cooldown(1, 24 * 60 * 60, commands.BucketType.user)  # type: ignore
    async def rob_cmd(self, ctx: CContext, target: discord.Member) -> None:
        if target.id == ctx.author.id:
            await ctx.send('You cannot rob yourself!')
            return None
        
        if target is None:
            await ctx.send('You need to specify a valid target to rob.')
            return None
        
        if target.bot:
            await ctx.send('You cannot rob a bot!')
            return None
        
        # target is valid
        profile = await curr_utils.get_profile(ctx.author)
        target_profile = await curr_utils.get_profile(target)
        
        if not await curr_utils.user_has_gun(profile) and not await curr_utils.user_has_gun(target_profile):
            # Neither user has a gun
            winner = random.choice(['user', 'target'])
            if winner == 'user':
                await rob_success(ctx, profile, target, target_profile)
                return None
            else:
                # 50% chance of failure
                await ctx.send(f'You were caught trying to rob {target.display_name} and they ran away!')
                return None
            
        elif not await curr_utils.user_has_gun(profile) and await curr_utils.user_has_gun(target_profile):
            # User has no gun, target has a gun
            # 99% chance of failure
            if random.random() < 0.99:
                await got_shot(ctx, profile, target)
                return None
            else:
                # 5% chance of success
                await rob_success_og(ctx, profile, target, target_profile)
                return None
        
        elif await curr_utils.user_has_gun(profile) and not await curr_utils.user_has_gun(target_profile):
            # User has a gun, target has no gun
            # 75% chance of success
            if random.random() < 0.75:
                await rob_success(ctx, profile, target, target_profile)
                return None
            
            else:
                # 25% chance of failure
                await ctx.send(f'You were caught trying to rob {target.display_name} and they ran away!')
                return None
            
        else:
            # User has a gun, target has a gun
            # 50% chance of success
            if random.random() < 0.5:
                
                await rob_success(ctx, profile, target, target_profile)
                return None
            
            else:
                await got_shot(ctx, profile, target)
                return None


async def setup(bot: commands.Bot):
    pass
    # await bot.add_cog(CrimeCog(bot))
