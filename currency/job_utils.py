from __future__ import annotations

import dataclasses
import enum
import functools
from collections.abc import Iterator
from dataclasses import dataclass
from typing import TypedDict


@functools.total_ordering
class SchoolQualif(enum.Enum):
    """
    Enum to represent different qualifications required for jobs, cost per year, and length of study in years.
    """
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
    
    def __gt__(self, other: 'SchoolQualif') -> bool:
        """
        Compares two SchoolQualif enum members based on their index.
        :param other: The other SchoolQualif member to compare with.
        :return: True if this member is greater than the other, False otherwise.
        """
        return self.value[0] > other.value[0]
    
    def __lt__(self, other: 'SchoolQualif') -> bool:
        """
        Compares two SchoolQualif enum members based on their index.
        :param other: The other SchoolQualif member to compare with.
        :return: True if this member is less than the other, False otherwise.
        """
        return self.value[0] < other.value[0]
    
    def __eq__(self, other: object) -> bool:
        """
        Checks if two SchoolQualif enum members are equal.
        :param other: The other SchoolQualif member to compare with.
        :return: True if both members are equal, False otherwise.
        """
        if not isinstance(other, SchoolQualif):
            return NotImplemented
        return self.value[0] == other.value[0]
    
    @classmethod
    def from_string(cls, s: str) -> 'SchoolQualif':
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
    
    def __gt__(self, other: 'SecurityClearance') -> bool:
        """
        Compares two SecurityClearance enum members based on their index.
        :param other: The other SecurityClearance member to compare with.
        :return: True if this member is greater than the other, False otherwise.
        """
        return self.value > other.value
    
    def __lt__(self, other: object) -> bool:
        """
        Compares two SecurityClearance enum members based on their index.
        :param other: The other SecurityClearance member to compare with.
        :return: True if this member is less than the other, False otherwise.
        """
        if not isinstance(other, SecurityClearance):
            return NotImplemented
        return self.value < other.value
    
    def __eq__(self, other: 'SecurityClearance') -> bool:
        """
        Checks if two SecurityClearance enum members are equal.
        :param other: The other SecurityClearance member to compare with.
        :return: True if both members are equal, False otherwise.
        """
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


@dataclass
class Job:
    """
    Dataclass to represent a job.
    Attributes:
        name (str): The name of the job.
        tree (str): The Job tree to which the job belongs.
        req_qualifications (tuple[str]): List of qualifications required for the job.
        req_experience (int): Years of experience required for the job.
        salary (int): Salary offered per year.
        salary_variance (int): Variance in salary in percent
        experience_multiplier (float | int): Multiplier for experience.
    """
    name: str
    tree: str
    req_qualifications: tuple[SchoolQualif, SecurityClearance]
    req_experience: int
    salary: int
    salary_variance: int
    experience_multiplier: float | int = 1
    parent_tree: JobTree | None = dataclasses.field(default=None, repr=False)
    
    def __post_init__(self):
        
        if not isinstance(self.req_qualifications, tuple):
            raise TypeError("req_qualifications must be a tuple of (SchoolQualif, SecurityClearance)")
        
        if len(self.req_qualifications) != 2:
            raise ValueError("req_qualifications must contain exactly two elements: (SchoolQualif, SecurityClearance)")
        
        if not isinstance(self.req_qualifications[0], SchoolQualif):
            raise TypeError("First element of req_qualifications must be a SchoolQualif enum member")
        
        if not isinstance(self.req_qualifications[1], SecurityClearance):
            raise TypeError("Second element of req_qualifications must be a SecurityClearance enum member")
        
        self.school_requirement = self.req_qualifications[0]
        self.security_clearance = self.req_qualifications[1]
        self.init_complete = True
    
    def get_next_job(self) -> Job | list[Job] | None:
        """
        Finds the next job or list of jobs in the job tree.
        :return: The next job(s) in the sequence, or None if it's the last one.
        """
        if not self.parent_tree:
            return None
        
        for i, job_or_list in enumerate(self.parent_tree.jobs):
            current_jobs = job_or_list if isinstance(job_or_list, list) else [job_or_list]
            if self in current_jobs:
                # Check if there is a next level in the tree
                if i + 1 < len(self.parent_tree.jobs):
                    return self.parent_tree.jobs[i + 1]
                else:
                    return None
        return None
    
    def to_dict(self) -> dict[str, str | int | float | list[str]]:
        """
        Converts the job to a dictionary representation.
        :return: A dictionary representation of the job.
        """
        return {
            "name":                  self.name,
            "tree":                  self.tree,
            "req_qualifications":    [
                self.school_requirement.name,
                self.security_clearance.name
            ],
            "req_experience":        self.req_experience,
            "salary":                self.salary,
            "salary_variance":       self.salary_variance,
            "experience_multiplier": self.experience_multiplier
        }
    
    def to_json(self) -> str:
        """
        Converts the job to a JSON string representation.
        :return: A JSON string representation of the job.
        """
        import json
        
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: dict[str, str | int | float | list[str]]) -> 'Job':
        """
        Creates a Job instance from a dictionary representation.
        :param data: The dictionary representation of the job.
        :return: A Job instance.
        """
        try:
            return cls(
                    name=data["name"],
                    tree=data["tree"],
                    req_qualifications=(
                        SchoolQualif[data["req_qualifications"][0]],
                        SecurityClearance[data["req_qualifications"][1]]
                    ),
                    req_experience=int(data["req_experience"]),
                    salary=int(data["salary"]),
                    salary_variance=int(data["salary_variance"]),
                    experience_multiplier=float(data["experience_multiplier"])
            )
        except (KeyError, ValueError, IndexError) as e:
            raise ValueError(f"Invalid job data: {e}") from e
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Job':
        """
        Creates a Job instance from a JSON string representation.
        :param json_str: The JSON string representation of the job.
        :return: A Job instance.
        """
        import json
        
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}") from e
    
    def __hash__(self) -> int:
        if self.init_complete:
            return hash((self.name, self.salary, self.salary_variance, self.req_experience, self.req_qualifications))
        else:
            raise TypeError("Unhashable type: 'Job' (initialization not complete)")


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
    jobs: list[Job | list[Job]]
    
    def __post_init__(self):
        """
        Post-initialization to set the parent_tree for each job.
        """
        for job_or_list in self.jobs:
            if isinstance(job_or_list, list):
                for job in job_or_list:
                    job.parent_tree = self
            else:  # It's a single Job object
                job_or_list.parent_tree = self
    
    def __iter__(self) -> Iterator[Job | list[Job]]:
        for job in self.jobs:
            yield job


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


class Profile(TypedDict):
    user_id: str
    wallet: int
    bank: int
    work_income: int
    work_str: str
    work_tree: str
    other_income: int
    next_income_mult: float
    work_experience: int
    qualifications: tuple[str, str]
    fire_risk: float
    debt: int
    credit_score: int
    age: int  # Age in months
    inventory: dict[str, int]
    illegal_items: dict[str, int]
