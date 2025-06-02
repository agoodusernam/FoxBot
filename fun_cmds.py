import discord
import random

import main


async def dice_roll(client: main.MyClient, message: discord.Message) -> None:
	nums: list[int | str] = message.content.replace("dice", "").replace("roll", "").split()
	if len(nums) < 2:
		await message.channel.send("Please choose 2 numbers to roll the dice, e.g. `dice 1 6`", delete_after=client.del_after)
		return
	nums = list(map(int, nums))

	await message.channel.send(f"You rolled a {random.randint(nums[0], nums[1])}")
	return