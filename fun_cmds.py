import math
import base64

import discord
import random


async def dice_roll(client, message: discord.Message) -> None:
	nums: list[int | str] = message.content.replace("dice", "").replace("roll", "").split()
	if len(nums) < 2:
		await message.delete()
		await message.channel.send("Please choose 2 numbers to roll the dice, e.g. `dice 1 6`", delete_after=client.del_after)
		return
	nums = list(map(int, nums))
	num: int | str = random.randint(nums[0], nums[1])
	oversize = False
	if math.log10(num) > 1900:
		oversize = True
		num = base64.b64encode(str(num).encode()).decode()

	await message.channel.send(f"You rolled a {num}")
	if oversize:
		await message.channel.send("The number is too large to display in decimal format, so it has been converted to base64.")
	return
