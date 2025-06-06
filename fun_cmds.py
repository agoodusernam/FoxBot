import math
import os
import random

import discord


async def dice_roll(del_after: int, message: discord.Message) -> None:
	nums: list[int | str] = message.content.replace('dice', '').replace('roll', '').split()
	if len(nums) < 2:
		await message.delete()
		await message.channel.send('Please choose 2 numbers to roll the dice, e.g. `dice 1 6`', delete_after=del_after)
		return
	try:
		nums = list(map(int, nums))
	except ValueError:
		await message.delete()
		await message.channel.send('Please provide valid numbers for the dice roll, e.g. `dice 1 6`',
		                           delete_after=del_after)
		return
	if nums[0] > nums[1]:
		num: int | str = random.randint(nums[1], nums[0])
	else:
		num = random.randint(nums[0], nums[1])
	oversize = False
	if math.log10(num) > 1984:
		oversize = True
		num = hex(num)
		if len(num) > 1984:
			await message.channel.send('The output number would be too large to send in discord')
			return

	await message.channel.send(f'You rolled a {num}')
	if oversize:
		await message.channel.send(
				'The number is too large to display in decimal format, so it has been converted to hex.')
	return


def get_karma_pic() -> tuple[str, str] | None:
	karma_pics = [f for f in os.listdir('data/karma_pics') if os.path.isfile(os.path.join('data/karma_pics', f))]
	if not karma_pics:
		return None

	# Choose a random file
	chosen_pic = random.choice(karma_pics)
	file_path = f'data/karma_pics/{chosen_pic}'

	return file_path, chosen_pic

def flip_coin() -> str:
	coin = random.choice(['Heads', 'Tails'])
	return coin
