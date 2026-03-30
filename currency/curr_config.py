from typing import Final
from decimal import Decimal

CENTRAL_INTEREST_RATE: Final[Decimal] = Decimal('0.02')
INTEREST_RATE: Final[Decimal] = Decimal('0.06') / 12  # Monthly interest rate
CURRENCY_NAME: Final[str] = 'FoxCoins'
RETIREMENT_AGE: Final[int] = 65 * 12  # Age at which a member can retire
INCOME_TAX: Final[Decimal] = Decimal('0.15')  # Tax rate on income
SALES_TAX: Final[Decimal] = Decimal('0.08375')  # Sales tax rate on purchases
BASE_FIRE_CHANCE: Final[float] = 0.003546099 # probability to get fired, on average, twice in an entire lifetime
BASE_CREDIT_SCORE: Final[int] = 400
CIVILIAN_GUN_RESALE_MULT: Final[Decimal] = Decimal(0.7)
MILITARY_GUN_RESALE_MULT: Final[Decimal] = Decimal(0.9)
