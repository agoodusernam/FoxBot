from discord.ext import commands

from command_utils.CContext import CContext


class AuctionCog(commands.Cog, name='Auction'):
    """Cog for auction-related commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name='start_auction', help='Starts an auction for a specified item.')
    async def start_auction(self, ctx: CContext, item: str, starting_price: int):
        """Starts an auction for a specified item with a starting price."""
        # TODO: Implement auction logic, including storing auction details in a database
        raise NotImplementedError
    
    @commands.command(name='end_auction', help='Ends the current auction and declares a winner.')
    async def end_auction(self, ctx: CContext):
        """Ends the current auction and declares a winner."""
        raise NotImplementedError
    
    @commands.command(name='ah', aliases=['auctionhouse', 'auction_house', 'auctions'],
                      help='Displays the current auction house items.')
    async def auction_house(self, ctx: CContext):
        """Displays the current auction house items."""
        raise NotImplementedError
    
    @commands.command(name='bid', help='Places a bid on the current auction item.')
    async def bid(self, ctx: CContext, amount: int):
        """Places a bid on the current auction item."""
        # TODO: See start_auction()
        raise NotImplementedError


async def setup(bot: commands.Bot) -> None:
    pass
# await bot.add_cog(AuctionCog(bot))
