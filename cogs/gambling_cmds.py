from discord.ext import commands

import command_utils.gambling_utils as gambling_utils
from command_utils.CContext import CContext
from command_utils.checks import is_dev
from currency import curr_utils, gambling_config, curr_config


class GamblingCmds(commands.Cog, name='Gambling', command_attrs=dict(add_check=is_dev, hidden=True)):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='slot', aliases=['slots'],
                      brief='Play a slot machine game',
                      help=f'Try your luck with the slot machine! You can win or lose {curr_config.currency_name}.',
                      usage='f!slot <bet_amount>')
    @commands.cooldown(1, 5, commands.BucketType.user)  # type: ignore
    async def slot_cmd(self, ctx: CContext, bet_amount: int):
        if bet_amount <= 0:
            await ctx.send('You must bet a positive amount!')
            return
        if bet_amount < gambling_config.slots_min_bet:
            await ctx.send(f'The minimum bet is {gambling_config.slots_min_bet} {curr_config.currency_name}!')
            return
        profile = curr_utils.get_profile(ctx.author)
        if profile['wallet'] < bet_amount:
            await ctx.send('You do not have enough money in your wallet!')
            return
        curr_utils.set_wallet(ctx.author, profile['wallet'] - bet_amount)
        
        payout = gambling_utils.slots_select_payout(gambling_config.slots_payouts, gambling_config.slots_probabilities)
        payout *= bet_amount
        if payout > 0:
            curr_utils.set_wallet(ctx.author, profile['wallet'] + payout)
            await ctx.send(f'You won {payout} {curr_config.currency_name}! 🎉')
        
        else:
            await ctx.send(f'You lost {bet_amount} {curr_config.currency_name}. Better luck next time! 😢')
    
    @commands.command(name='lottery', aliases=['lotto'],
                      brief='Play the lottery',
                      help=f'Buy a lottery ticket for a chance to win a jackpot! 1 ticket costs 5 {curr_config.currency_name}.',
                      usage='f!lottery <tickets>')
    @commands.cooldown(1, 60, commands.BucketType.user)  # type: ignore
    #TODO: Implement lottery drawing and winner selection using discord.ext.tasks
    async def lottery_cmd(self, ctx: CContext, tickets: int = 1):
        if tickets <= 0:
            await ctx.send('You must buy at least one ticket!')
            return None
        cost = tickets * gambling_config.lottery_ticket_price
        profile = curr_utils.get_profile(ctx.author)
        if profile['wallet'] < cost:
            await ctx.send('You do not have enough money in your wallet!')
            return None
        curr_utils.set_wallet(ctx.author, profile['wallet'] - cost)
        curr_utils.set_lottery_tickets(ctx.author, tickets + curr_utils.get_lottery_tickets(ctx.author))
        await ctx.send(f'You bought {tickets} lottery ticket(s) for {cost} {curr_config.currency_name}.')
        await ctx.send('Winners are drawn every monday! Good luck!')
        return None


async def setup(bot) -> None:
    pass
    # await bot.add_cog(GamblingCmds(bot))
