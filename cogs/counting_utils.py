import asyncio
import decimal
import logging
import re
import string
import warnings
import signal
from enum import IntEnum
from sys import platform
from typing import Any, overload

import discord

from command_utils.CContext import CoolBot
from utils import utils

__all__ = ["counting_msg", "BitwiseDecimal", "CountStatus", "fail_count", "count_only_allowed_chars", "eval_count_msg"]

logger = logging.getLogger('discord')


class BitwiseDecimal(decimal.Decimal):
    # why can't subclasses just return the subclass...
    def __abs__(self) -> "BitwiseDecimal":
        return BitwiseDecimal(super().__abs__())
    
    def __add__(self, other) -> "BitwiseDecimal":
        return BitwiseDecimal(super().__add__(other))
    
    def __divmod__(self, other) -> tuple["BitwiseDecimal", "BitwiseDecimal"]:
        r = super().__divmod__(other)
        return BitwiseDecimal(r[0]), BitwiseDecimal(r[1])
    
    def __floordiv__(self, other) -> "BitwiseDecimal":
        return BitwiseDecimal(super().__floordiv__(other))
    
    def __mod__(self, other) -> "BitwiseDecimal":
        return BitwiseDecimal(super().__mod__(other))
    
    def __mul__(self, other) -> "BitwiseDecimal":
        return BitwiseDecimal(super().__mul__(other))
    
    def __pow__(self, value, mod=None) -> "BitwiseDecimal":
        return BitwiseDecimal(super().__pow__(value, mod))
    
    def __sub__(self, other) -> "BitwiseDecimal":
        return BitwiseDecimal(super().__sub__(other))
    
    def __truediv__(self, other) -> "BitwiseDecimal":
        return BitwiseDecimal(super().__truediv__(other))
    
    def __radd__(self, other) -> "BitwiseDecimal":
        return BitwiseDecimal(super().__radd__(other))
    
    def __rdivmod__(self, other) -> tuple["BitwiseDecimal", "BitwiseDecimal"]:
        r = super().__rdivmod__(other)
        return BitwiseDecimal(r[0]), BitwiseDecimal(r[1])
    
    def __rfloordiv__(self, other) -> "BitwiseDecimal":
        return BitwiseDecimal(super().__rfloordiv__(other))
    
    def __rmod__(self, other) -> "BitwiseDecimal":
        return BitwiseDecimal(super().__rmod__(other))
    
    def __rmul__(self, other) -> "BitwiseDecimal":
        return BitwiseDecimal(super().__rmul__(other))
    
    def __rpow__(self, value, mod=None) -> "BitwiseDecimal":
        return BitwiseDecimal(super().__rpow__(value, mod))
    
    def __rsub__(self, other) -> "BitwiseDecimal":
        return BitwiseDecimal(super().__rsub__(other))
    
    def __rtruediv__(self, other) -> "BitwiseDecimal":
        return BitwiseDecimal(super().__rtruediv__(other))
    
    def __pos__(self) -> "BitwiseDecimal":
        return BitwiseDecimal(super().__pos__())
    
    def __neg__(self) -> "BitwiseDecimal":
        return BitwiseDecimal(super().__neg__())
    
    def remainder_near(self, other, context=None) -> "BitwiseDecimal":
        return BitwiseDecimal(super().remainder_near(other, context))
    
    @property
    def real(self) -> "BitwiseDecimal":
        return BitwiseDecimal(super().real)
    
    @property
    def imag(self) -> "BitwiseDecimal":
        return BitwiseDecimal(super().imag)
    
    def conjugate(self) -> "BitwiseDecimal":
        return BitwiseDecimal(super().conjugate())
    
    @overload
    def __round__(self) -> int: ...
    
    @overload
    def __round__(self, ndigits: int | None = None) -> "BitwiseDecimal": ...
    
    def __round__(self, ndigits=None) -> "int | BitwiseDecimal":
        if ndigits is None:
            return BitwiseDecimal(super().__round__())
        return BitwiseDecimal(super().__round__(ndigits))
    
    def __and__(self, other) -> "BitwiseDecimal":
        return BitwiseDecimal(round(self) & round(other))
    
    def __or__(self, other) -> "BitwiseDecimal":
        return BitwiseDecimal(round(self) | round(other))
    
    def __xor__(self, other) -> "BitwiseDecimal":
        return BitwiseDecimal(round(self) ^ round(other))
    
    def __invert__(self):
        return BitwiseDecimal(~round(self))
    
    def __lshift__(self, other) -> "BitwiseDecimal":
        return BitwiseDecimal(round(self) << round(other))
    
    def __rshift__(self, other) -> "BitwiseDecimal":
        return BitwiseDecimal(round(self) >> round(other))
    
    def normalize(self, context: decimal.Context | None = None) -> "BitwiseDecimal":
        return BitwiseDecimal(super().normalize(context))


D = BitwiseDecimal


class CountStatus(IntEnum):
    SUCCESS = 0
    TIMEOUT = 1
    INVALID = 2
    OVERFLOW = 3
    ZERO_DIV = 4
    DECIMAL_ERR = 5


def count_only_allowed_chars(s: str) -> bool:
    """
    Checks if the counting string only contains allowed characters.
    Assumes the string is lowercase and has no whitespace.
    """
    allowed: str = "0123456789*/-+.()%^&<>|~#"
    base_definitions: str = "xob"
    hex_allowed: str = "0123456789abcdef"
    in_hex_str: bool = False
    
    s = s.replace(",", ".")
    s = s.replace("_", "")
    
    for i, char in enumerate(s):
        if char not in allowed:
            
            if in_hex_str and char in hex_allowed:
                continue
            
            if in_hex_str and char not in hex_allowed:
                in_hex_str = False
            
            if char not in base_definitions:
                return False
            
            if s[i - 1] != "0":
                return False
            
            if i == 0:
                return False
            
            if char == "x":
                in_hex_str = True
                continue
    
    return True


def convert_to_base10(match: re.Match[str]) -> str:
    num_str: str = match.group(0)
    if num_str.startswith('0b'):
        return str(int(num_str[2:], 2))
    
    elif num_str.startswith('0o'):
        return str(int(num_str[2:], 8))
    
    elif num_str.startswith('0x'):
        return str(int(num_str[2:], 16))
    
    else:
        # This shouldn't happen
        return num_str

def eval_count_msg(message: str) -> tuple[BitwiseDecimal, CountStatus]:
    """
    Returns the evaluated result of a counting message.
    :param message: str: The counting message to evaluate.
    :return: tuple[BitwiseDecimal, CountStatus]: The evaluated result and the status of the evaluation.
    """
    message = message.replace("^", "[POWER_REPLACEMENT\u200B]")
    message = message.replace('#', '^')
    message = message.replace('[POWER_REPLACEMENT\u200B]', '**')
    
    def timeout_handler(signum: int, frame: Any):
        raise TimeoutError
    
    on_linux: bool = platform == "linux" or platform == "linux2"
    
    if not on_linux:
        warnings.warn("Counting timeout is only supported on Linux. Counts may hang indefinitely on other platforms.", RuntimeWarning)
    
    if on_linux:
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)  # type: ignore
        signal.alarm(2)  # type: ignore
    
    try:
        pattern = r"0b[01]+|0o[0-7]+|0x[0-9a-f]+"
        base_10_msg = re.sub(pattern, convert_to_base10, message)
        decimal.getcontext().prec = 2**20 - 1
        expr: str = re.sub(r"(\d+\.\d*|\.\d+|\d+)", r"BitwiseDecimal('\1')", base_10_msg)
        result: BitwiseDecimal = round(eval(expr), 20).normalize()
        
        return result, CountStatus.SUCCESS
    
    except (SyntaxError, ValueError, TypeError):
        return D(0), CountStatus.INVALID
    
    except TimeoutError:
        return D(0), CountStatus.TIMEOUT
    
    except (decimal.DivisionByZero, ZeroDivisionError):
        return D(0), CountStatus.ZERO_DIV
    
    except (OverflowError, decimal.Overflow, MemoryError, decimal.Underflow):
        return D(0), CountStatus.OVERFLOW
    
    except decimal.InvalidOperation:
        return D(0), CountStatus.DECIMAL_ERR
    
    finally:
        if on_linux:
            signal.alarm(0)  # type: ignore
            signal.signal(signal.SIGALRM, old_handler)  # type: ignore  # noqa


async def fail_count_number(message: discord.Message, bot: CoolBot, actual: BitwiseDecimal) -> None:
    actual = round(actual, 5)
    await message.reply(f"<@{message.author.id}> RUINED IT AT **{bot.config.last_count}**!! Next number is **1**. Your message evaluated to **{actual}**.")
    await fail_count(message, bot)
    return None


async def fail_count_user(message: discord.Message, bot: CoolBot) -> None:
    await message.reply(f"<@{message.author.id}> RUINED IT AT **{bot.config.last_count}**!! Next number is **1**. **You can't count two numbers in a row**.")
    await fail_count(message, bot)
    return None


async def fail_count(message: discord.Message, bot: CoolBot) -> None:
    logger.debug(f'Counting fail by user {message.author.id} at message {message.id}')
    assert isinstance(message.author, discord.Member)
    
    bot.config.last_count = 0
    await message.add_reaction("❌")
    
    if not utils.user_has_role(message.author, bot.config.counting_fail_role):
        try:
            await message.author.add_roles(discord.Object(id=bot.config.counting_fail_role))
        except discord.Forbidden:
            logger.error(f"Failed to add counting fail role to user {message.author.display_name}, missing permissions")
        except discord.NotFound:
            logger.error(f"Counting fail role {bot.config.counting_fail_role} not found")
        except discord.HTTPException as e:
            logger.error(f"Failed to add counting fail role to user {message.author.display_name}: {e}")
    
    bot.config.add_counting_fail(message.author.id)
    return None


async def counting_msg(message: discord.Message, bot: CoolBot) -> bool:
    assert isinstance(message.author, discord.Member)
    s = message.content.lower()
    for char in string.whitespace:
        s = s.replace(char, "")
    
    if not count_only_allowed_chars(s):
        return False
    
    result, status = eval_count_msg(s)
    
    if status == CountStatus.INVALID:
        return False
    
    banrole: int = bot.config.counting_ban_role
    
    if banrole != 0 and utils.user_has_role(message.author, banrole):
        await message.reply("You are banned from counting. Your message was not counted.")
        await message.delete()
        return False
    
    if bot.config.last_count_user == message.author.id and bot.config.last_count != 0:
        await fail_count_user(message, bot)
        return False
    
    if status == CountStatus.TIMEOUT:
        await message.reply("Expression took too long to evaluate.")
        return False
    
    if status == CountStatus.OVERFLOW:
        await message.reply("Expression resulted in an under or overflow, likely due to insufficient precision. Try using numbers closer to 0.")
        return False
    
    if status == CountStatus.ZERO_DIV:
        await message.reply("Expression resulted in a division by zero.")
        return False
    
    if status == CountStatus.DECIMAL_ERR:
        await message.reply("Expression resulted in a decimal error, likely due to insufficient precision. Try using numbers closer to 0.")
        return False
    
    int_result: int = round(result)
    
    if result != BitwiseDecimal(bot.config.last_count + 1).normalize():
        if bot.config.last_count != 0:
            await fail_count_number(message, bot, actual=result)
            return False
        
        await message.reply("The next number is **1**.")
        return False
    
    bot.config.user_counted(str(message.author.id), int_result, str(message.id))
    reaction: str = "✅"
    
    bot.config.last_count = int_result
    if int_result > bot.config.highest_count:
        bot.config.highest_count = int_result
        reaction = "☑️"
    
    bot.config.last_count_user = message.author.id
    await asyncio.sleep(0.2)
    await message.add_reaction(reaction)
    return True
