from job_utils import Job, SchoolQualif, JobTree, SecurityClearance

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

teacher_assistant = Job(
	name = "Teacher Assistant",
	tree = "Education",
	req_qualifications = [SchoolQualif.HIGH_SCHOOL],
	req_experience = 0,
	salary = 25_000,
	salary_variance = 5
)

teacher = Job(
	name = "Teacher",
	tree = "Education",
	req_qualifications = [SchoolQualif.BATCHELOR],
	req_experience = 2,
	salary = 40_000,
	salary_variance = 10
)

university_lecturer = Job(
	name = "University Lecturer",
	tree = "Education",
	req_qualifications = [SchoolQualif.BATCHELOR],
	req_experience = 5,
	salary = 50_000,
	salary_variance = 10
)

associate_professor = Job(
	name = "Associate Professor",
	tree = "Education",
	req_qualifications = [SchoolQualif.MASTER],
	req_experience = 7,
	salary = 70_000,
	salary_variance = 15
)

professor = Job(
	name = "Professor",
	tree = "Education",
	req_qualifications = [SchoolQualif.MASTER],
	req_experience = 10,
	salary = 90_000,
	salary_variance = 20
)

distinguished_professor = Job(
	name = "Distinguished Professor",
	tree = "Education",
	req_qualifications = [SchoolQualif.PHD],
	req_experience = 15,
	salary = 120_000,
	salary_variance = 25
)

education_tree = JobTree(
	name = "Education",
	jobs = [
		teacher_assistant,
		teacher,
		university_lecturer,
		associate_professor,
		professor,
		distinguished_professor
	]
)

# Engineering Jobs
engineering_intern = Job(
	name = "Engineering Intern",
	tree = "Engineering",
	req_qualifications = [SchoolQualif.HIGH_SCHOOL],
	req_experience = 0,
	salary = 0,
	salary_variance = 0,
	experience_multiplier = 2
)

apprentice_engineer = Job(
	name = "Apprentice Engineer",
	tree = "Engineering",
	req_qualifications = [SchoolQualif.ASSOCIATE],
	req_experience = 0,
	salary = 30_000,
	salary_variance = 0
)

junior_engineer = Job(
	name = "Junior Engineer",
	tree = "Engineering",
	req_qualifications = [SchoolQualif.ASSOCIATE],
	req_experience = 1,
	salary = 50_000,
	salary_variance = 5
)

flight_systems_engineer = Job(
	name = "Flight Systems Engineer",
	tree = "Engineering",
	req_qualifications = [SchoolQualif.MASTER],
	req_experience = 3,
	salary = 70_000,
	salary_variance = 10
)

orbital_analyst_engineer = Job(
	name = "Orbital Analyst Engineer",
	tree = "Engineering",
	req_qualifications = [SchoolQualif.MASTER],
	req_experience = 5,
	salary = 70_000,
	salary_variance = 10
)

avionics_engineer = Job(
	name = "Avionics Engineer",
	tree = "Engineering",
	req_qualifications = [SchoolQualif.MASTER],
	req_experience = 7,
	salary = 70_000,
	salary_variance = 10
)

lead_aerospace_engineer = Job(
	name = "Lead Aerospace Engineer",
	tree = "Engineering",
	req_qualifications = [SchoolQualif.PHD, SecurityClearance.TOP_SECRET],
	req_experience = 10,
	salary = 100_000,
	salary_variance = 15
)

aerospace_engineering_director = Job(
	name = "Director of Aerospace Engineering",
	tree = "Engineering",
	req_qualifications = [SchoolQualif.PHD, SecurityClearance.TS_SCI],
	req_experience = 15,
	salary = 150_000,
	salary_variance = 20
)

engineering_tree = JobTree(
	name = "Engineering",
	jobs = [
		[engineering_intern, apprentice_engineer],
		junior_engineer,
		flight_systems_engineer,
		orbital_analyst_engineer,
		avionics_engineer,
		lead_aerospace_engineer,
		aerospace_engineering_director
	]
)

private = Job(
	name = "Private",
	tree = "Enlisted_Army",
	req_qualifications = [SchoolQualif.HIGH_SCHOOL],
	req_experience = 0,
	salary = 30_000,
	salary_variance = 5
)

private_first_class = Job(
	name = "Private First Class",
	tree = "Enlisted_Army",
	req_qualifications = [SchoolQualif.HIGH_SCHOOL],
	req_experience = 1,
	salary = 32_000,
	salary_variance = 5
)

corporal = Job(
	name = "Corporal",
	tree = "Enlisted_Army",
	req_qualifications = [SchoolQualif.HIGH_SCHOOL],
	req_experience = 2,
	salary = 35_000,
	salary_variance = 5
)

specialist = Job(
	name = "Specialist",
	tree = "Enlisted_Army",
	req_qualifications = [SchoolQualif.HIGH_SCHOOL],
	req_experience = 2,
	salary = 35_000,
	salary_variance = 5
)

sergeant = Job(
	name = "Sergeant",
	tree = "Enlisted_Army",
	req_qualifications = [SchoolQualif.HIGH_SCHOOL],
	req_experience = 4,
	salary = 40_000,
	salary_variance = 10
)

staff_sergeant = Job(
	name = "Staff Sergeant",
	tree = "Enlisted_Army",
	req_qualifications = [SchoolQualif.HIGH_SCHOOL],
	req_experience = 6,
	salary = 45_000,
	salary_variance = 10
)

seargeant_first_class = Job(
	name = "Sergeant First Class",
	tree = "Enlisted_Army",
	req_qualifications = [SchoolQualif.HIGH_SCHOOL],
	req_experience = 8,
	salary = 50_000,
	salary_variance = 10
)

master_sergeant = Job(
	name = "Master Sergeant",
	tree = "Enlisted_Army",
	req_qualifications = [SchoolQualif.HIGH_SCHOOL],
	req_experience = 10,
	salary = 60_000,
	salary_variance = 15
)

first_sergeant = Job(
	name = "First Sergeant",
	tree = "Enlisted_Army",
	req_qualifications = [SchoolQualif.HIGH_SCHOOL],
	req_experience = 10,
	salary = 60_000,
	salary_variance = 15
)

sergeant_major = Job(
	name = "Sergeant Major",
	tree = "Enlisted_Army",
	req_qualifications = [SchoolQualif.HIGH_SCHOOL],
	req_experience = 12,
	salary = 70_000,
	salary_variance = 20
)

command_sergeant_major = Job(
	name = "Command Sergeant Major",
	tree = "Enlisted_Army",
	req_qualifications = [SchoolQualif.HIGH_SCHOOL],
	req_experience = 12,
	salary = 70_000,
	salary_variance = 20
)

seargeant_major_of_the_army = Job(
	name = "Sergeant Major of the Army",
	tree = "Enlisted_Army",
	req_qualifications = [SchoolQualif.HIGH_SCHOOL],
	req_experience = 15,
	salary = 90_000,
	salary_variance = 25
)

enlisted_army_tree = JobTree(
	name = "Enlisted_Army",
	jobs = [
		private,
		private_first_class,
		[corporal, specialist],
		sergeant,
		staff_sergeant,
		seargeant_first_class,
		[master_sergeant, first_sergeant],
		[sergeant_major, command_sergeant_major],
		seargeant_major_of_the_army
	]
)

warrant_officer_1 = Job(
	name = "Warrant Officer 1",
	tree = "Commissioned_Officer_Army",
	req_qualifications = [SchoolQualif.BATCHELOR],
	req_experience = 0,
	salary = 30_000,
	salary_variance = 5
)

warrant_officer_2 = Job(
	name = "Warrant Officer 2",
	tree = "Commissioned_Officer_Army",
	req_qualifications = [SchoolQualif.BATCHELOR],
	req_experience = 2,
	salary = 32_500,
	salary_variance = 5
)

warrant_officer_3 = Job(
	name = "Warrant Officer 3",
	tree = "Commissioned_Officer_Army",
	req_qualifications = [SchoolQualif.BATCHELOR],
	req_experience = 4,
	salary = 35_000,
	salary_variance = 10
)

warrant_officer_4 = Job(
	name = "Warrant Officer 4",
	tree = "Commissioned_Officer_Army",
	req_qualifications = [SchoolQualif.BATCHELOR],
	req_experience = 6,
	salary = 40_000,
	salary_variance = 10
)

warrant_officer_5 = Job(
	name = "Warrant Officer 5",
	tree = "Commissioned_Officer_Army",
	req_qualifications = [SchoolQualif.BATCHELOR],
	req_experience = 8,
	salary = 45_000,
	salary_variance = 10
)

second_lieutenant = Job(
	name = "Second Lieutenant",
	tree = "Commissioned_Officer_Army",
	req_qualifications = [SchoolQualif.BATCHELOR],
	req_experience = 10,
	salary = 50_000,
	salary_variance = 15
)

first_lieutenant = Job(
	name = "First Lieutenant",
	tree = "Commissioned_Officer_Army",
	req_qualifications = [SchoolQualif.BATCHELOR],
	req_experience = 12,
	salary = 55_000,
	salary_variance = 15
)

captain = Job(
	name = "Captain",
	tree = "Commissioned_Officer_Army",
	req_qualifications = [SchoolQualif.BATCHELOR],
	req_experience = 14,
	salary = 60_000,
	salary_variance = 15
)

major = Job(
	name = "Major",
	tree = "Commissioned_Officer_Army",
	req_qualifications = [SchoolQualif.BATCHELOR],
	req_experience = 16,
	salary = 70_000,
	salary_variance = 20
)

lieutenant_colonel = Job(
	name = "Lieutenant Colonel",
	tree = "Commissioned_Officer_Army",
	req_qualifications = [SchoolQualif.BATCHELOR],
	req_experience = 18,
	salary = 80_000,
	salary_variance = 20
)

colonel = Job(
	name = "Colonel",
	tree = "Commissioned_Officer_Army",
	req_qualifications = [SchoolQualif.MASTER],
	req_experience = 20,
	salary = 90_000,
	salary_variance = 20
)

brigadier_general = Job(
	name = "Brigadier General",
	tree = "Commissioned_Officer_Army",
	req_qualifications = [SchoolQualif.MASTER],
	req_experience = 22,
	salary = 100_000,
	salary_variance = 25
)

major_general = Job(
	name = "Major General",
	tree = "Commissioned_Officer_Army",
	req_qualifications = [SchoolQualif.MASTER],
	req_experience = 24,
	salary = 110_000,
	salary_variance = 25
)

lieutenant_general = Job(
	name = "Lieutenant General",
	tree = "Commissioned_Officer_Army",
	req_qualifications = [SchoolQualif.MASTER],
	req_experience = 26,
	salary = 120_000,
	salary_variance = 30
)

general = Job(
	name = "General",
	tree = "Commissioned_Officer_Army",
	req_qualifications = [SchoolQualif.MASTER],
	req_experience = 28,
	salary = 130_000,
	salary_variance = 30
)

Commissioned_Officer_Army_tree = JobTree(
	name = "Commissioned_Officer_Army",
	jobs = [
		warrant_officer_1,
		warrant_officer_2,
		warrant_officer_3,
		warrant_officer_4,
		warrant_officer_5,
		second_lieutenant,
		first_lieutenant,
		captain,
		major,
		lieutenant_colonel,
		colonel,
		brigadier_general,
		major_general,
		lieutenant_general,
		general
	]
)

