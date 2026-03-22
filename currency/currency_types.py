import enum
import functools
from collections.abc import Callable, Coroutine, Iterator
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Self, TypedDict

import discord # type: ignore
import discord.ext.commands

from command_utils.CContext import CContext
from currency.curr_config import base_fire_chance


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
            if not isinstance(job_or_list, list):
                job_or_list.tree = self
                job_or_list.tree_index = i
                continue
            
            for job in job_or_list:
                job.tree = self
                job.tree_index = i
    
    def __iter__(self) -> "Iterator[Job | list[Job]]":
        for job in self.jobs:
            yield job
    
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
    tree: JobTree = JobTree.NONE()
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


def job_from_name(job_name: str, job_trees: list[JobTree]) -> Job | None:
    """
    Finds a job by its name across multiple job trees.
    :param job_name: The name of the job to find.
    :param job_trees: List of JobTree instances to search in.
    :return: The Job instance if found, None otherwise.
    """
    for tree in job_trees:
        for job_or_list in tree.jobs:
            if isinstance(job_or_list, list):
                for job in job_or_list:
                    if job.name.lower() == job_name.lower():
                        return job
            else:
                if job_or_list.name.lower() == job_name.lower():
                    return job_or_list
    return None


@dataclass
class ShopItem:
    """
    Represents an item in the shop.
    Attributes:
        name (str): The name of the item.
        description (str): A brief description of the item.
        price (int): The price of the item in currency.
        stock (int): The number of items available in stock.
        perk (list[Callable[[discord.ext.commands.Context, discord.Member], Awaitable[None]]] | None): A list of
            async functions that will be called when the item is purchased. They should take a discord.Context and a
            discord.Member as parameters and return None.
    """
    
    name: str
    description: str
    price: int
    stock: int
    perk: list[Callable[[CContext, discord.Member], Coroutine[Any, Any, bool]]] | None


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
        perk (list[Callable[[discord.ext.commands.Context, discord.Member], Awaitable[None]]] | None): A list of
            async functions that will be called when the item is purchased. They should take a discord.Context and a
            discord.Member as parameters and return None.
        resale_mult (float): Multiplier for resale value of black market items.
        cops_risk (float): How likely it is to get caught when buying/selling this item.
        scam_risk (float): How likely it is to be scammed when buying/selling this item.
        trace_back (bool | float): Whether the item can be traced back to the buyer or seller. This can also be a
        float representing the chance of being traced back.
    """
    resale_mult: float = 0.5
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
        perk (list[Callable[[discord.ext.commands.Context, discord.Member], Awaitable[None]]] | None): A list of
            async functions that will be called when the gun item is purchased. They should take a discord.Context and a
            discord.Member as parameters and return None.
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
        perk (list[Callable[[discord.ext.commands.Context, discord.Member], Awaitable[None]]] | None): A list of
            async functions that will be called when the drug item is purchased. They should take a discord.Context and a
            discord.Member as parameters and return None.
        resale_mult (float): Multiplier for resale value of drug items.
        cops_risk (float): How likely it is to get caught when buying/selling this drug item.
        scam_risk (float): How likely it is to be scammed when buying/selling this drug item.
        trace_back (bool | float): Whether the drug item can be traced back to the buyer or seller. This can also be a
            float representing the chance of being traced back.
        income_multiplier (float): Multiplier for income generated from working while under using this drug.
        work_catch_risk (float): Risk of getting caught while working under the influence of this drug.
        uses (int): Number of uses before the drug item is consumed.
        od_chance (float): Chance of overdosing when using this drug item.
    """
    income_multiplier: float = 0.5
    work_catch_risk: float = 0.1
    uses: int = 1
    od_chance: float = 0.005


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


@dataclass
class BlackMarketCategory:
    """
    Represents a category of items in the black market.
    Attributes:
        name (str): The name of the black market category.
        description (str): A brief description of the black market category.
        items (list[BlackMarketItem]): A list of BlackMarketItems in this category.
    """
    name: str
    description: str
    items: list[BlackMarketItem]


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
    fire_risk: float
    debt: str
    credit_score: int
    age: int  # Age in months
    inventory: list[tuple[str, int]]
    illegal_items: list[tuple[str, int]]


@dataclass
class Profile:
    user_id: str
    wallet: Decimal
    bank: Decimal
    work_income: Decimal
    job: Job
    other_income: Decimal
    next_income_mult: float
    work_experience: int
    school_qualification: SchoolQualif
    security_clearance: SecurityClearance
    _fire_risk: float
    debt: Decimal
    _credit_score: int
    age: int  # Age in months
    inventory: list[tuple[ShopItem, int]]
    bm_inventory: list[tuple[BlackMarketItem, int]]
    
    @property
    def credit_score(self) -> int:
        return self._credit_score
    
    @credit_score.setter
    def credit_score(self, value: int):
        if not isinstance(value, int):
            raise TypeError('Credit score must be an integer')
        self._credit_score = min(value, 800)
    
    @property
    def fire_risk(self) -> float:
        return self._fire_risk
    
    @fire_risk.setter
    def fire_risk(self, value: float):
        if not isinstance(value, float):
            raise TypeError('Fire risk must be a float')
        self._fire_risk = max(value, base_fire_chance)
    
    def _convert_inventory(self) -> list[tuple[str, int]]:
        converted: list[tuple[str, int]] = []
        for item in self.inventory:
            converted.append((item[0].name, item[1]))
        
        return converted
    
    def _convert_bm_inventory(self) -> list[tuple[str, int]]:
        converted: list[tuple[str, int]] = []
        for item in self.bm_inventory:
            converted.append((item[0].name, item[1]))
        
        return converted
    
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
                fire_risk=self.fire_risk,
                debt=str(self.debt),
                credit_score=self.credit_score,
                age=self.age,  # Age in months
                inventory=self._convert_inventory(),
                illegal_items=self._convert_bm_inventory(),
                )

