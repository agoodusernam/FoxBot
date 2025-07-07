import enum
from dataclasses import dataclass


class SchoolQualif(enum.Enum):
	"""
	Enum to represent different qualifications required for jobs, cost per year, and length of study in years.
	"""
	HIGH_SCHOOL = [0, 0, 0]
	ASSOCIATE = [1, 3_885, 2]
	BACHELOR = [2, 15_419, 4]
	MASTER = [3, 20_000, 2]
	PHD = [4, 18_030, 6]
	DOCTORATE = PHD
	POLYMATH = [5, 50_000, 10]  # Special fictional qualification, not required for any job but gives a salary boost


def str_to_school_qualif(s: str) -> SchoolQualif:
	"""
	Converts a string to a SchoolQualif enum member.
	:param s: The string representation of the qualification.
	:return: The corresponding SchoolQualif enum member.
	"""
	try:
		return SchoolQualif[s.upper().replace(' ', '_')]
	except KeyError:
		raise ValueError(f"Invalid school qualification: {s}")

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


def str_to_security_clearance(s: str) -> SecurityClearance:
	"""
	Converts a string to a SecurityClearance enum member.
	:param s: The string representation of the security clearance.
	:return: The corresponding SecurityClearance enum member.
	"""
	try:
		return SecurityClearance[s.upper().replace(" ", "_")]
	except KeyError:
		raise ValueError(f"Invalid security clearance: {s}")


@dataclass
class Job:
	"""
	Dataclass to represent a job.
	Attributes:
		name (str): The name of the job.
		tree (str): The Job tree to which the job belongs.
		req_qualifications (list[str]): List of qualifications required for the job.
		req_experience (int): Years of experience required for the job.
		salary (int): Salary offered per year.
		salary_variance (int): Variance in salary in per cent
	"""
	name: str
	tree: str
	req_qualifications: list[SchoolQualif | SecurityClearance]
	req_experience: int
	salary: int
	salary_variance: int
	experience_multiplier: float | int = 1


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
	
	def __iter__(self) -> iter:
		"""
		Iterates over the jobs in the job tree.
		Returns:
			Iterator over the jobs in the job tree.
		"""
		for job in self.jobs:
			if isinstance(job, list):
				yield from job
			else:
				yield job
