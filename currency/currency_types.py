import enum
import functools
import logging
import math
import random
from collections.abc import Callable, Coroutine, Iterator, Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Self, TypedDict

import discord  # type: ignore
import discord.ext.commands

from command_utils.CContext import CContext
from currency import collector
from currency.curr_config import BASE_CREDIT_SCORE, BASE_FIRE_CHANCE, INCOME_TAX
from utils import db_stuff
from utils import utils

logger = logging.getLogger('discord')


def _is_invalid_db_item(item: list[str | int]) -> bool:
    logger.debug(f"Checking item: {item}")
    if len(item) != 2:
        logger.error(f"Invalid length for item: {item}, expected 2, got {len(item)}")
        return True
    
    if not isinstance(item[0], str):
        logger.error(f"Invalid type for item name: {item}, expected str, got {type(item[0])}")
        return True
    
    if not isinstance(item[1], int):
        logger.error(f"Invalid type for item value: {item}, expected int, got {type(item[1])}")
        return True
    
    if item[1] <= 0:
        logger.error(f"Invalid value for item: {item}, expected value > 0, got {item[1]}")
        return True
    
    return False


@functools.total_ordering
class SchoolQualif(enum.Enum):
    """
    Enum to represent different qualifications required for jobs, cost per year, and length of study in years.
    """
    # LEVEL, COST PER YEAR, LENGTH OF STUDY (in years)
    HIGH_SCHOOL = (0, 0, 0)
    NONE = HIGH_SCHOOL
    ASSOCIATE = (1, 3_885, 2)
    BACHELOR = (2, 15_419, 4)
    MASTER = (3, 20_000, 2)
    PHD = (4, 18_030, 6)
    DOCTORATE = PHD
    POLYMATH = (5, 50_000, 10)  # Special fictional qualification, not required for any job but gives a salary boost
    
    def __getitem__(self, item):
        return self.value[item]
    
    def __gt__(self, other: object) -> bool:
        """
        Compares two SchoolQualif enum members based on their index.
        :param other: The other SchoolQualif member to compare with.
        :return: True if this member is greater than the other, False otherwise.
        """
        if not isinstance(other, SchoolQualif):
            raise TypeError
        return self.value[0] > other.value[0]
    
    def __lt__(self, other: object) -> bool:
        """
        Compares two SchoolQualif enum members based on their index.
        :param other: The other SchoolQualif member to compare with.
        :return: True if this member is less than the other, False otherwise.
        """
        if not isinstance(other, SchoolQualif):
            raise TypeError
        return self.value[0] < other.value[0]
    
    def __eq__(self, other: object) -> bool:
        """
        Checks if two SchoolQualif enum members are equal.
        :param other: The other SchoolQualif member to compare with.
        :return: True if both members are equal, False otherwise.
        """
        if not isinstance(other, SchoolQualif):
            raise TypeError
        return self.value[0] == other.value[0]
    
    @classmethod
    def from_string(cls, s: str) -> Self:
        """
        Converts a string to a SchoolQualif enum member.
        :param s: The string representation of the qualification.
        :return: The corresponding SchoolQualif enum member.
        """
        try:
            return cls[s.upper().replace(" ", "_")]
        except KeyError:
            raise ValueError(f"Invalid school qualification: {s}")
    
    def to_string(self) -> str:
        """
        Converts a SchoolQualif enum member to its string representation.
        :return: The string representation of the qualification.
        """
        return self.name.replace('_', ' ').title()
    
    def __hash__(self) -> int:
        return super().__hash__()
    
    @property
    def level(self) -> int:
        return self.value[0]
    
    @classmethod
    def from_level(cls, level: int) -> Self:
        for qualif in cls:
            if qualif.level == level:
                return qualif
        
        raise ValueError(f"Invalid school qualification level: {level}")


@functools.total_ordering
class SecurityClearance(enum.Enum):
    """
    Enum to represent different security clearance levels using the US security clearance system.
    """
    NONE = 0
    CONFIDENTIAL = 1
    SECRET = 2
    TOP_SECRET = 3
    TS_SCI = 4
    SPECIAL = 5
    
    def __gt__(self, other: object) -> bool:
        """
        Compares two SecurityClearance enum members based on their index.
        :param other: The other SecurityClearance member to compare with.
        :return: True if this member is greater than the other, False otherwise.
        """
        if not isinstance(other, SecurityClearance):
            raise TypeError
        return self.value > other.value
    
    def __lt__(self, other: object) -> bool:
        """
        Compares two SecurityClearance enum members based on their index.
        :param other: The other SecurityClearance member to compare with.
        :return: True if this member is less than the other, False otherwise.
        """
        if not isinstance(other, SecurityClearance):
            raise TypeError
        return self.value < other.value
    
    def __eq__(self, other: object) -> bool:
        """
        Checks if two SecurityClearance enum members are equal.
        :param other: The other SecurityClearance member to compare with.
        :return: True if both members are equal, False otherwise.
        """
        if not isinstance(other, SecurityClearance):
            raise TypeError
        return self.value == other.value
    
    @classmethod
    def from_string(cls, s: str) -> 'SecurityClearance':
        try:
            return cls[s.upper().replace(" ", "_")]
        except KeyError:
            raise ValueError(f"Invalid security clearance: {s}")
    
    def __str__(self) -> str:
        return self.name.replace('_', ' ').title()
    
    to_string = __str__
    
    def __hash__(self) -> int:
        return super().__hash__()
    
    @property
    def level(self) -> int:
        return self.value


@dataclass
class JobTree:
    """
    Dataclass to represent a job tree.
    Attributes:
        name (str): The name of the job tree.
        jobs (list[Job]): List of jobs in the job tree.

    Typically, Jobs will go from most basic to most advanced, so the first job in the list is the most basic one.
    If there are multiple jobs at the same level, they are grouped in a list.
    """
    name: str
    jobs: "list[Job | list[Job]]"
    
    def __post_init__(self):
        """
        Post-initialisation to set the tree for each job.
        """
        for i, job_or_list in enumerate(self.jobs):
            if isinstance(job_or_list, Job):
                job_or_list.tree = self
                job_or_list.tree_index = i
                continue
            
            for job in job_or_list:
                job.tree = self
                job.tree_index = i
    
    def __iter__(self) -> Iterator["Job | list[Job]"]:
        return iter(self.jobs)
    
    def all_jobs_flat(self) -> "list[Job]":
        jobs: list[Job] = []
        for job in self.jobs:
            if isinstance(job, list):
                jobs.extend(job)
            else:
                jobs.append(job)
        return jobs
    
    @classmethod
    def NONE(cls) -> Self:
        return cls(name='None', jobs=[])


@dataclass
class Job:
    """
    Dataclass to represent a job.
    Attributes:
        name (str): The name of the job.
        tree (str): The Job tree to which the job belongs.
        req_experience (int): Years of experience required for the job.
        salary (int): Salary offered per year.
        salary_variance (int): Variance in salary in percent
        experience_multiplier (float | int): Multiplier for experience.
    """
    name: str
    req_experience: int
    salary: int
    salary_variance: int
    experience_multiplier: int = 1
    tree: JobTree = field(default_factory=JobTree.NONE)
    tree_index: int = 0
    req_school: SchoolQualif = SchoolQualif.NONE
    req_clearance: SecurityClearance = SecurityClearance.NONE
    
    def get_next_job(self) -> "Job | list[Job] | None":
        """
        Finds the next job or list of jobs in the job tree.
        :return: The next job(s) in the sequence, or None if it's the last one.
        """
        if len(self.tree.jobs) == self.tree_index + 1:
            return None
        return self.tree.jobs[self.tree_index + 1]

unemployed_job = Job(
        name="Unemployed",
        req_experience=0,
        salary=0,
        salary_variance=0,
)

@dataclass
class ShopItem:
    """
    Represents an item in the shop.
    Attributes:
        name (str): The name of the item.
        description (str): A brief description of the item.
        price (int): The price of the item in currency.
        stock (int): The number of items available in stock.
    """
    
    name: str
    description: str
    price: int
    stock: int
    
    def __post_init__(self) -> None:
        self.category: "ShopCategory" = ShopCategory.NONE()
        self.invalid: bool = False
        if not hasattr(self, 'resale_mult'):
            self.resale_mult: Decimal = Decimal('0.9')

@dataclass
class PerkItem(ShopItem):
    """
    Represents an item that provides special perks in a shop system.

    This class inherits from ShopItem and is used to represent items that,
    when purchased or used, provide specific benefits or functionalities defined
    as callable functions. Each perk is designed to interact with a given context
    and a Discord member, performing an asynchronous operation.

    Attributes:
        perk: A list of callable objects that take a CContext and a discord.Member
              as parameters and perform asynchronous operations. Each callable
              returns a coroutine evaluating to a boolean.
    """
    perk: list[Callable[[CContext, discord.Member], Coroutine[Any, Any, bool]]]

@dataclass
class HouseItem(ShopItem):
    """
    Represents a house item in the shop.
    Includes additional attributes for house-specific features.
    Attributes:
        rent_cost (int): The cost of renting the house.
        rent_income (int): The income generated from renting the house.
    """
    rent_cost: int
    rent_income: int


@dataclass
class BlackMarketItem(ShopItem):
    """
    Represents an item in the black market.
    Black market items are not available in the regular shop and may have unique properties or effects.
    Attributes:
        name (str): The name of the black market item.
        description (str): A brief description of the item.
        price (int): The price of the item in currency.
        stock (int): The number of items available in stock.
        resale_mult (float): Multiplier for resale value of black market items.
        cops_risk (float): How likely it is to get caught when buying/selling this item.
        scam_risk (float): How likely it is to be scammed when buying/selling this item.
        trace_back (bool | float): Whether the item can be traced back to the buyer or seller. This can also be a
        float representing the chance of being traced back.
    """
    resale_mult: Decimal = Decimal(0.5)
    cops_risk: float = 0.1
    scam_risk: float = 0.1
    trace_back: bool | float = True


@dataclass
class GunItem(BlackMarketItem):
    """
    Represents a gun item in the black market.
    Gun items may have additional properties or effects compared to regular black market items.
    Attributes:
        name (str): The name of the gun item.
        description (str): A brief description of the gun item.
        price (int): The price of the gun item in currency.
        stock (int): The number of gun items available in stock.
        resale_mult (float): Multiplier for resale value of gun items.
        cops_risk (float): How likely it is to get caught when buying/selling this gun item.
        scam_risk (float): How likely it is to be scammed when buying/selling this gun item.
        trace_back (bool | float): Whether the gun item can be traced back to the buyer or seller. This can also be a
            float representing the chance of being traced back.
        suppressed (bool): Whether the gun is suppressed or not, affects cops_risk and trace_back. cops risk goes up
        by 10% and trace back chance goes down by 10% if suppressed.
    """
    suppressed: bool = False


@dataclass
class DrugItem(BlackMarketItem):
    """
    Represents a drug item in the black market.
    Drugs may have additional effects or properties compared to regular black market items.
    Attributes:
        name (str): The name of the drug item.
        description (str): A brief description of the drug item.
        price (int): The price of the drug item in currency.
        stock (int): The number of drug items available in stock.
        resale_mult (float): Multiplier for resale value of drug items.
        cops_risk (float): How likely it is to get caught when buying/selling this drug item.
        scam_risk (float): How likely it is to be scammed when buying/selling this drug item.
        trace_back (bool | float): Whether the drug item can be traced back to the buyer or seller. This can also be a
            float representing the chance of being traced back.
        income_multiplier (float): Multiplier for income generated from working while under using this drug.
        income_multiplier_range (float): How much the income multiplier can vary upwards from the default value.
        work_catch_risk (float): Risk of getting caught while working under the influence of this drug.
        uses (int): Number of uses before the drug item is consumed.
        od_chance (float): Chance of overdosing when using this drug item.
    """
    income_multiplier: float = 0.5
    income_multiplier_range: float = 1.0
    work_catch_risk: float = 0.1
    uses: int = 1
    od_chance: float = 0.005
    
    def ranged_income_mult(self) -> float:
        if math.isclose(self.income_multiplier_range, 1.0, abs_tol=0.001):
            return self.income_multiplier
        range_mult = random.uniform(1.0, self.income_multiplier_range)
        return self.income_multiplier * range_mult


@dataclass
class ShopCategory:
    """
    Represents a category of items in the shop.
    Attributes:
        name (str): The name of the category.
        description (str): A brief description of the category.
        items (list[ShopItem]): A list of ShopItems in this category.
    """
    name: str
    description: str
    items: list[ShopItem]
    
    def item_names(self) -> list[str]:
        """
        Returns a list of item names in this category.
        :return: A list of item names.
        """
        return [item.name for item in self.items]
    
    @classmethod
    def NONE(cls) -> Self:
        return cls(name='None', description='None', items=[])


@dataclass
class BlackMarketCategory(ShopCategory):
    """
    Represents a category of items in the black market.
    Attributes:
        name (str): The name of the black market category.
        description (str): A brief description of the black market category.
        items (list[BlackMarketItem]): A list of BlackMarketItems in this category.
    """
    items: list[BlackMarketItem]  # type: ignore


class DBProfile(TypedDict):
    user_id: str
    wallet: str
    bank: str
    work_income: str
    work_str: str
    other_income: str
    next_income_mult: float
    work_experience: int
    school_qualification: int
    security_clearance: int
    fire_chance: float
    debt: str
    credit_score: int
    age: int
    inventory: dict[str, list[str | int]]
    illegal_items: dict[str, list[str | int]]
    lottery_tickets: int
    # Is it redundant to store the name twice here?
    # Yes. However, it's only like 20 bytes, so I don't really care


def validate_DBProfile(profile: Mapping[str, Any]) -> DBProfile:
    """
    Turn a message from the database into a valid DBProfile.
    Will raise KeyError if the profile is invalid.
    """
    new_profile = DBProfile(user_id=profile['user_id'],
                            wallet=profile.get('wallet', '500'),
                            bank=profile.get('bank', '500'),
                            work_income=profile.get('work_income', '0'),
                            work_str=profile.get('work_str', 'Unemployed'),
                            other_income=profile.get('other_income', '0'),
                            next_income_mult=profile.get('next_income_mult', 1.0),
                            work_experience=profile.get('work_experience', 0),
                            school_qualification=profile.get('school_qualification', 0),
                            security_clearance=profile.get('security_clearance', 0),
                            fire_chance=profile.get('fire_chance', BASE_FIRE_CHANCE),
                            debt=profile.get('debt', '0'),
                            credit_score=profile.get('credit_score', BASE_CREDIT_SCORE),
                            age=profile.get('age', 18 * 12),
                            lottery_tickets=profile.get('lottery_tickets', 0),
                            inventory=profile.get('inventory', {}),
                            illegal_items=profile.get('illegal_items', {}),
                            )
    return new_profile


inventory_type = dict[str, tuple[ShopItem | BlackMarketItem, int]]
normal_inventory_type = dict[str, tuple[ShopItem, int]]
bm_inventory_type = dict[str, tuple[BlackMarketItem, int]]


def transform_val_for_db(val: Any) -> str | int | float:
    """
    Tries to convert the given value to a type suitable for storing in the database.
    Will raise TypeError if the value cannot be converted.
    """
    if isinstance(val, (float, int, str)):
        return val
    if isinstance(val, Decimal):
        return str(val)
    if isinstance(val, Job):
        return str(val.name)
    if isinstance(val, SchoolQualif):
        return val.level
    if isinstance(val, SecurityClearance):
        return val.level
    raise TypeError(f'Invalid type for DB: {type(val)}')

class _BatchContext:
    """Context manager for batching Profile attribute changes into a single DB call."""
    
    def __init__(self, profile: "Profile") -> None:
        self._profile = profile
    
    def __enter__(self) -> None:
        object.__setattr__(self._profile, '_Profile__batching', True)
        object.__setattr__(self._profile, '_Profile__pending_updates', {})
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        object.__setattr__(self._profile, '_Profile__batching', False)
        pending = object.__getattribute__(self._profile, '_Profile__pending_updates')
        if pending:
            # noinspection PyProtectedMember
            utils.make_sync(self._profile._update_db_data(pending))
        object.__setattr__(self._profile, '_Profile__pending_updates', {})


@dataclass
class Profile:
    """
    The profile class for all currency related things.
    Automatically syncs to the database with __setattr__.
    Will not sync any attributes that start with an underscore.
    """
    user_id: str
    wallet: Decimal = Decimal(500)
    bank: Decimal = Decimal(500)
    work_income: Decimal = Decimal(0)
    job: Job = field(default_factory=lambda: unemployed_job)
    other_income: Decimal = Decimal(0)
    next_income_mult: float = 1.0
    work_experience: int = 0
    school_qualification: SchoolQualif = SchoolQualif.NONE
    security_clearance: SecurityClearance = SecurityClearance.NONE
    debt: Decimal = Decimal(0)
    age: int = 18 * 12  # Age in months
    inventory: normal_inventory_type = field(default_factory=dict)
    bm_inventory: bm_inventory_type = field(default_factory=dict)
    lottery_tickets: int = 0
    _credit_score: int = BASE_CREDIT_SCORE
    _fire_chance: float = BASE_FIRE_CHANCE
    
    def __post_init__(self) -> None:
        object.__setattr__(self, '_Profile__initialised', True)
        object.__setattr__(self, '_Profile__batching', False)
        object.__setattr__(self, '_Profile__pending_updates', {})
    
    def __setattr__(self, item: str, value: Any) -> None:
        # Is this scuffed?
        # Yes. Absolutely, however, it's the best option to send to DB every change,
        # at least that I could think of.
        try:
            initialised = object.__getattribute__(self, '_Profile__initialised')
        except AttributeError:
            super().__setattr__('_Profile__initialised', False)
            initialised = False

        super().__setattr__(item, value)

        if not item.startswith('_') and initialised:
            if item == 'inventory':
                new_val = self._inventory_to_basic()
            elif item == 'bm_inventory':
                new_val = self._bm_inventory_to_basic()
            else:
                new_val = transform_val_for_db(getattr(self, item))

            batching = object.__getattribute__(self, '_Profile__batching')
            if batching:
                pending = object.__getattribute__(self, '_Profile__pending_updates')
                pending[item] = new_val
            else:
                utils.make_sync(self._update_db_data({item: new_val}))
    
    def batch(self) -> _BatchContext:
        """
        Context manager to batch multiple attribute changes into a single DB call.

        Usage:
            with profile.batch():
                profile.wallet = Decimal(100)
                profile.bank = Decimal(200)
        """
        return _BatchContext(self)
    
    async def _update_db_data(self, data: Mapping[str, Any]) -> bool:
        return await db_stuff.edit_db_entry('currency', {'user_id': self.user_id}, data)
    
    async def _add_to_db(self) -> bool:
        if await self._self_in_db():
            raise RuntimeError('Profile already in DB')
        return await db_stuff.send_to_db('currency', data=self.to_DBProfile())
    
    @property
    def has_gun(self) -> bool:
        for item, _ in self.bm_inventory.values():
            if isinstance(item, GunItem):
                return True
        return False
    
    @property
    def credit_score(self) -> int:
        return self._credit_score
    
    @credit_score.setter
    def credit_score(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError('Credit score must be an integer')
        self._credit_score = min(value, 800)
    
    @property
    def max_loan(self) -> Decimal:
        if self.debt > 0:
            return Decimal(0)
        
        credit_factor = Decimal(0.5 + (self.credit_score / 800))
        return min((self.work_income * 12 * credit_factor) + 10_000, Decimal(1_000_000))
    
    @property
    def earnings(self) -> Decimal:
        return (self.work_income / Decimal(12)) * Decimal(1 - INCOME_TAX)
    
    @property
    def fire_chance(self) -> float:
        return self._fire_chance
    
    @fire_chance.setter
    def fire_chance(self, value: float) -> None:
        if not isinstance(value, float):
            raise TypeError('Fire risk must be a float')
        self._fire_chance = max(value, BASE_FIRE_CHANCE)
    
    def reset_job(self) -> None:
        self.job = unemployed_job
        self.work_experience = 0
        self.work_income = Decimal(0)
    
    def fire(self) -> None:
        self.wallet += self.earnings * 2 # 2 months severance
        self.work_income = Decimal(0)
        self.job = unemployed_job
        self.fire_chance = BASE_FIRE_CHANCE
        self.work_experience = self.work_experience // 2
    
    def set_job(self, job: Job, income: int | Decimal | float) -> None:
        self.job = job
        self.work_income = Decimal(income) if isinstance(income, (int, float)) else income
    
    def inc_age(self) -> None:
        self.age += 1
    
    def clear_inventory(self) -> None:
        self.inventory = {}
    
    def clear_bm_inventory(self) -> None:
        self.bm_inventory = {}
    
    def remove_normal_item(self, item: ShopItem | str, amount: int = 1) -> int | None:
        """
        Remove an item from the normal inventory.
        Returns the amount removed, or None if the item was not found.
        """
        if amount == 0:
            raise ValueError('Amount may not be 0')
        elif amount == -1:
            # Allow removing all items with -1 as the amount.
            pass
        elif amount < 0:
            raise ValueError('Amount may not be negative')
        
        if isinstance(item, ShopItem):
            item_name = item.name
        else:
            item_name = item
        
        if item not in self.inventory:
            return None
        
        inv_amount = self.inventory[item_name][1]
        if inv_amount <= amount or amount == -1:
            self.inventory.pop(item_name)
            return inv_amount
        
        self.inventory[item_name] = (self.inventory[item_name][0], inv_amount - amount)
        return amount
    
    def remove_bm_item(self, item: BlackMarketItem | str, amount: int = 1) -> int | None:
        """
        Remove an item from the bm inventory.
        Returns the amount removed, or None if the item was not found.
        """
        if amount == 0:
            raise ValueError('Amount may not be 0')
        
        if isinstance(item, BlackMarketItem):
            item_name = item.name
        else:
            item_name = item
        
        if item not in self.bm_inventory:
            return None
        
        inv_amount = self.bm_inventory[item_name][1]
        if inv_amount <= amount:
            self.bm_inventory.pop(item_name)
            return inv_amount
        
        self.bm_inventory[item_name] = (self.bm_inventory[item_name][0], inv_amount - amount)
        return amount
    
    def add_normal_item(self, item: ShopItem | str, amount: int = 1) -> bool:
        if amount <= 0:
            raise ValueError('Amount must be positive')
        
        item_obj: ShopItem | None = None
        if isinstance(item, ShopItem):
            item_obj = item
            item_name = item.name
        else:
            item_name = item
        
        
        
        if item_name in self.inventory:
            self.inventory[item_name] = (self.inventory[item_name][0], self.inventory[item_name][1] + amount)
            return True
        
        if item_obj is not None:
            self.inventory[item_name] = (item_obj, amount)
            return True
        
        item_obj = collector.normal_item_from_str(item_name)
        if item_obj is None:
            logger.error(f'No item with that name was found: {item_name}')
            return False
        
        self.inventory[item_name] = (item_obj, amount)
        return True
    
    def add_bm_item(self, item: BlackMarketItem | str, amount: int = 1) -> None | str:
        if amount <= 0:
            raise ValueError('Amount must be positive')
        
        item_obj: BlackMarketItem | None = None
        if isinstance(item, BlackMarketItem):
            item_obj = item
            item_name = item.name
        else:
            item_name = item
        
        if item_name in self.bm_inventory:
            self.bm_inventory[item_name] = (self.bm_inventory[item_name][0], self.bm_inventory[item_name][1] + amount)
            return None
        
        if item_obj is not None:
            self.bm_inventory[item_name] = (item_obj, amount)
            return None
        
        item_obj = collector.bm_item_from_str(item_name)
        if item_obj is None:
            return 'No item with that name was found.'
        
        self.bm_inventory[item_name] = (item_obj, amount)
        return None
    
    def _inventory_to_basic(self) -> dict[str, list[str | int]]:
        converted: dict[str, list[str | int]] = {}
        for name, item in self.inventory.items():
            converted[name] = [item[0].name, item[1]]
        
        return converted
    
    def _bm_inventory_to_basic(self) -> dict[str, list[str | int]]:
        converted: dict[str, list[str | int]] = {}
        for name, item in self.bm_inventory.items():
            converted[name] = [item[0].name, item[1]]
        
        return converted
    
    def _basic_bm_to_inventory(self, inv: dict[str, list[str | int]]):
        for name, item in inv.items():
            if _is_invalid_db_item(item):
                continue
            obj: BlackMarketItem | None = collector.bm_item_from_str(str(item[0]))
            if obj is None:
                logger.error(f'Item in inventory could not be found: {item[0]}')
                continue
            
            self.bm_inventory[name] = (obj, int(item[1]))
    
    def _basic_to_inventory(self, inv: dict[str, list[str | int]]) -> None:
        for name, item in inv.items():
            if _is_invalid_db_item(item):
                continue
                
            obj: ShopItem | None = collector.normal_item_from_str(str(item[0]))
            if obj is None:
                logger.error(f'Item in inventory could not be found: {item[0]}')
                continue
            
            self.inventory[name] = (obj, int(item[1]))
    
    async def _delete_from_db(self) -> bool:
        return await db_stuff.del_db_entry('currency', {'user_id': self.user_id})
    
    async def reset_db_entry(self) -> bool:
        if not await self._self_in_db():
            return await self._add_to_db()
            
        removed: bool = await self._delete_from_db()
        if not removed:
            logger.error('Profile was not deleted from DB.')
            return False
        if await self._self_in_db():
            logger.error('Profile was deleted from DB, but Profile is still there.')
            return False
        return await self._add_to_db()
    
    async def _self_in_db(self) -> bool:
        return await db_stuff.get_from_db('currency', {'user_id': self.user_id}) is not None
    
    def to_DBProfile(self) -> DBProfile:
        return DBProfile(
                user_id=self.user_id,
                wallet=str(self.wallet),
                bank=str(self.bank),
                work_income=str(self.work_income),
                work_str=self.job.name,
                other_income=str(self.other_income),
                next_income_mult=self.next_income_mult,
                work_experience=self.work_experience,
                school_qualification=self.school_qualification.level,
                security_clearance=self.security_clearance.level,
                fire_chance=self.fire_chance,
                debt=str(self.debt),
                credit_score=self.credit_score,
                age=self.age,
                lottery_tickets=self.lottery_tickets,
                inventory=self._inventory_to_basic(),
                illegal_items=self._bm_inventory_to_basic(),
                )
    
    @classmethod
    def from_DBProfile(cls, profile: DBProfile) -> Self:
        job = collector.job_from_str(profile['work_str'], unemployed_job)
        if job is None:
            raise ValueError(f'Job could not be fetched. {profile["work_str"]}')
        obj = cls(
                user_id=profile['user_id'],
                wallet=Decimal(profile['wallet']),
                bank=Decimal(profile['bank']),
                work_income=Decimal(profile['work_income']),
                job=job,
                other_income=Decimal(profile['other_income']),
                next_income_mult=profile['next_income_mult'],
                work_experience=profile['work_experience'],
                school_qualification=SchoolQualif.from_level(profile['school_qualification']),
                security_clearance=SecurityClearance(profile['security_clearance']),
                debt=Decimal(profile['debt']),
                age=profile['age'],
                lottery_tickets=profile['lottery_tickets'],
                )
        obj.credit_score = profile['credit_score']
        obj.fire_chance = profile['fire_chance']
        obj._basic_to_inventory(profile['inventory'])
        obj._basic_bm_to_inventory(profile['illegal_items'])
        return obj
    
    @classmethod
    async def fetch_from_user_id(cls, user_id: str | int) -> Self:
        if isinstance(user_id, int):
            str_user_id = str(user_id)
        else:
            str_user_id = user_id
        profile = await db_stuff.get_from_db('currency', {'user_id': user_id})
        if profile is None:
            new_profile = cls(user_id=str_user_id)
            await new_profile._add_to_db()
            return new_profile
        return cls.from_DBProfile(validate_DBProfile(profile))
