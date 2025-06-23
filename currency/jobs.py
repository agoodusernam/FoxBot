from job_utils import Job, SchoolQualif, JobTree

# Retail Jobs
cashier = Job(
	name = "Cashier",
	tree = "Retail",
	req_qualifications = [SchoolQualif.HIGH_SCHOOL],
	req_experience = 0,
	salary = 20_000,
	salary_variance = 5
)

stock_clerk = Job(
	name = "Stock Clerk",
	tree = "Retail",
	req_qualifications = [SchoolQualif.HIGH_SCHOOL],
	req_experience = 0,
	salary = 22_000,
	salary_variance = 5
)

department_supervisor = Job(
	name = "Department Supervisor",
	tree = "Retail",
	req_qualifications = [SchoolQualif.HIGH_SCHOOL],
	req_experience = 2,
	salary = 25_000,
	salary_variance = 10
)

store_manager = Job(
	name = "Store Manager",
	tree = "Retail",
	req_qualifications = [SchoolQualif.HIGH_SCHOOL],
	req_experience = 4,
	salary = 40_000,
	salary_variance = 15
)

district_manager = Job(
	name = "District Manager",
	tree = "Retail",
	req_qualifications = [SchoolQualif.BATCHELOR],
	req_experience = 6,
	salary = 60_000,
	salary_variance = 20
)

regional_manager = Job(
	name = "Regional Manager",
	tree = "Retail",
	req_qualifications = [SchoolQualif.BATCHELOR],
	req_experience = 8,
	salary = 80_000,
	salary_variance = 25
)

director_of_operations = Job(
	name = "Director of Retail Operations",
	tree = "Retail",
	req_qualifications = [SchoolQualif.MASTER],
	req_experience = 10,
	salary = 100_000,
	salary_variance = 30
)

retail_tree = JobTree(
	name = "Retail",
	jobs = [
		[cashier, stock_clerk],
		department_supervisor,
		store_manager,
		district_manager,
		regional_manager,
		director_of_operations
	]
)

# Information Technology Jobs
IT_intern = Job(
	name = "IT Intern",
	tree = "Information Technology",
	req_qualifications = [SchoolQualif.HIGH_SCHOOL],
	req_experience = 0,
	salary = 0,
	salary_variance = 0,
	experience_multiplier = 2
)

helpdesk = Job(
	name = "Helpdesk Technician",
	tree = "Information Technology",
	req_qualifications = [SchoolQualif.HIGH_SCHOOL],
	req_experience = 1,
	salary = 30_000,
	salary_variance = 5
)

helpdesk_specialist = Job(
	name = "Helpdesk Specialist",
	tree = "Information Technology",
	req_qualifications = [SchoolQualif.ASSOCIATE],
	req_experience = 2,
	salary = 40_000,
	salary_variance = 5
)

technician = Job(
	name = "IT Technician",
	tree = "Information Technology",
	req_qualifications = [SchoolQualif.ASSOCIATE],
	req_experience = 3,
	salary = 50_000,
	salary_variance = 10
)

j_system_administrator = Job(
	name = "Junior System Administrator",
	tree = "Information Technology",
	req_qualifications = [SchoolQualif.BATCHELOR],
	req_experience = 4,
	salary = 60_000,
	salary_variance = 10
)

system_administrator = Job(
	name = "System Administrator",
	tree = "Information Technology",
	req_qualifications = [SchoolQualif.BATCHELOR],
	req_experience = 6,
	salary = 75_000,
	salary_variance = 15
)

supervisor = Job(
	name = "IT Supervisor",
	tree = "Information Technology",
	req_qualifications = [SchoolQualif.MASTER],
	req_experience = 8,
	salary = 90_000,
	salary_variance = 20
)

it_manager = Job(
	name = "IT Manager",
	tree = "Information Technology",
	req_qualifications = [SchoolQualif.MASTER],
	req_experience = 10,
	salary = 120_000,
	salary_variance = 25
)


it_director = Job(
	name = "Director of Information Technology",
	tree = "Information Technology",
	req_qualifications = [SchoolQualif.MASTER],
	req_experience = 12,
	salary = 150_000,
	salary_variance = 30
)

it_tree = JobTree(
	name = "Information Technology",
	jobs = [
		[IT_intern, helpdesk],
		helpdesk_specialist,
		technician,
		j_system_administrator,
		system_administrator,
		supervisor,
		it_manager,
		it_director
	]
)


