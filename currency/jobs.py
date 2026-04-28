from currency import collector
from currency.currency_types import Job, SchoolQualif, JobTree, SecurityClearance

# Retail Jobs
cashier = Job(
        name="Cashier",
        req_experience=0,
        salary=20_000,
        salary_variance=5,
)

stock_clerk = Job(
        name="Stock Clerk",
        req_experience=0,
        salary=22_000,
        salary_variance=5,
)

department_supervisor = Job(
        name="Department Supervisor",
        req_experience=2,
        salary=25_000,
        salary_variance=10,
)

store_manager = Job(
        name="Store Manager",
        req_experience=4,
        salary=40_000,
        salary_variance=15,
)

district_manager = Job(
        name="District Manager",
        req_school=SchoolQualif.BACHELOR,
        req_experience=6,
        salary=60_000,
        salary_variance=20,
)

regional_manager = Job(
        name="Regional Manager",
        req_school=SchoolQualif.BACHELOR,
        req_experience=8,
        salary=80_000,
        salary_variance=25,
)

director_of_operations = Job(
        name="Director of Retail Operations",
        req_school=SchoolQualif.BACHELOR,
        req_experience=10,
        salary=90_000,
        salary_variance=30,
)

retail_tree = JobTree(
        name="Retail",
        jobs=[
            [cashier, stock_clerk],
            department_supervisor,
            store_manager,
            district_manager,
            regional_manager,
            director_of_operations,
        ],
)
collector.register_job_tree(retail_tree)

# Information_Technology Jobs
IT_intern = Job(
        name="IT Intern",
        req_experience=0,
        salary=0,
        salary_variance=0,
        experience_multiplier=2,
)

helpdesk = Job(
        name="Helpdesk Technician",
        req_experience=1,
        salary=30_000,
        salary_variance=5,
)

helpdesk_specialist = Job(
        name="Helpdesk Specialist",
        req_school=SchoolQualif.ASSOCIATE,
        req_experience=2,
        salary=40_000,
        salary_variance=5,
)

technician = Job(
        name="IT Technician",
        req_school=SchoolQualif.ASSOCIATE,
        req_experience=3,
        salary=50_000,
        salary_variance=10,
)

j_system_administrator = Job(
        name="Junior System Administrator",
        req_school=SchoolQualif.BACHELOR,
        req_experience=4,
        salary=60_000,
        salary_variance=10,
)

system_administrator = Job(
        name="System Administrator",
        req_school=SchoolQualif.BACHELOR,
        req_experience=6,
        salary=75_000,
        salary_variance=15,
)

supervisor = Job(
        name="IT Supervisor",
        req_school=SchoolQualif.MASTER,
        req_experience=8,
        salary=90_000,
        salary_variance=20,
)

it_manager = Job(
        name="IT Manager",
        req_school=SchoolQualif.MASTER,
        req_experience=10,
        salary=120_000,
        salary_variance=25,
)

it_director = Job(
        name="Director of Information Technology",
        req_school=SchoolQualif.MASTER,
        req_experience=12,
        salary=160_000,
        salary_variance=30,
)

it_tree = JobTree(
        name="Information_Technology",
        jobs=[
            [IT_intern, helpdesk],
            helpdesk_specialist,
            technician,
            j_system_administrator,
            system_administrator,
            supervisor,
            it_manager,
            it_director,
        ],
)
collector.register_job_tree(it_tree)

# Teaching/Education Jobs
teacher_assistant = Job(
        name="Teacher Assistant",
        req_experience=0,
        salary=25_000,
        salary_variance=5,
)

teacher = Job(
        name="Teacher",
        req_school=SchoolQualif.BACHELOR,
        req_experience=2,
        salary=40_000,
        salary_variance=10,
)

university_lecturer = Job(
        name="University Lecturer",
        req_school=SchoolQualif.BACHELOR,
        req_experience=5,
        salary=50_000,
        salary_variance=10,
)

associate_professor = Job(
        name="Associate Professor",
        req_school=SchoolQualif.MASTER,
        req_experience=7,
        salary=70_000,
        salary_variance=15,
)

professor = Job(
        name="Professor",
        req_school=SchoolQualif.MASTER,
        req_experience=10,
        salary=90_000,
        salary_variance=20,
)

distinguished_professor = Job(
        name="Distinguished Professor",
        req_school=SchoolQualif.PHD,
        req_experience=15,
        salary=100_000,
        salary_variance=25,
)

education_tree = JobTree(
        name="Education",
        jobs=[
            teacher_assistant,
            teacher,
            university_lecturer,
            associate_professor,
            professor,
            distinguished_professor,
        ],
)
collector.register_job_tree(education_tree)

# Engineering Jobs
engineering_intern = Job(
        name="Engineering Intern",
        req_experience=0,
        salary=0,
        salary_variance=0,
        experience_multiplier=2,
)

apprentice_engineer = Job(
        name="Apprentice Engineer",
        req_school=SchoolQualif.ASSOCIATE,
        req_experience=0,
        salary=30_000,
        salary_variance=5,
)

junior_engineer = Job(
        name="Junior Engineer",
        req_school=SchoolQualif.BACHELOR,
        req_clearance=SecurityClearance.CONFIDENTIAL,
        req_experience=1,
        salary=50_000,
        salary_variance=5,
)

flight_systems_engineer = Job(
        name="Flight Systems Engineer",
        req_school=SchoolQualif.MASTER,
        req_clearance=SecurityClearance.SECRET,
        req_experience=3,
        salary=70_000,
        salary_variance=10,
)

orbital_analyst_engineer = Job(
        name="Orbital Analyst Engineer",
        req_school=SchoolQualif.MASTER,
        req_clearance=SecurityClearance.SECRET,
        req_experience=5,
        salary=70_000,
        salary_variance=10,
)

avionics_engineer = Job(
        name="Avionics Engineer",
        req_school=SchoolQualif.MASTER,
        req_clearance=SecurityClearance.TOP_SECRET,
        req_experience=7,
        salary=70_000,
        salary_variance=10,
)

lead_aerospace_engineer = Job(
        name="Lead Aerospace Engineer",
        req_school=SchoolQualif.PHD,
        req_clearance=SecurityClearance.TOP_SECRET,
        req_experience=10,
        salary=100_000,
        salary_variance=15,
)

engineering_director = Job(
        name="Director of Engineering",
        req_school=SchoolQualif.PHD,
        req_clearance=SecurityClearance.TS_SCI,
        req_experience=15,
        salary=120_000,
        salary_variance=20,
)

engineering_tree = JobTree(
        name="Engineering",
        jobs=[
            [engineering_intern, apprentice_engineer],
            junior_engineer,
            flight_systems_engineer,
            orbital_analyst_engineer,
            avionics_engineer,
            lead_aerospace_engineer,
            engineering_director,
        ],
)
collector.register_job_tree(engineering_tree)

# Military Jobs
private = Job(
        name="Private",
        req_experience=0,
        salary=30_000,
        salary_variance=5,
)

private_first_class = Job(
        name="Private First Class",
        req_experience=1,
        salary=32_000,
        salary_variance=5,
)

corporal = Job(
        name="Corporal",
        req_school=SchoolQualif.HIGH_SCHOOL,
        req_clearance=SecurityClearance.CONFIDENTIAL,
        req_experience=2,
        salary=35_000,
        salary_variance=5,
)

specialist = Job(
        name="Specialist",
        req_school=SchoolQualif.HIGH_SCHOOL,
        req_clearance=SecurityClearance.CONFIDENTIAL,
        req_experience=2,
        salary=35_000,
        salary_variance=5,
)

sergeant = Job(
        name="Sergeant",
        req_school=SchoolQualif.HIGH_SCHOOL,
        req_clearance=SecurityClearance.SECRET,
        req_experience=4,
        salary=40_000,
        salary_variance=10,
)

staff_sergeant = Job(
        name="Staff Sergeant",
        req_school=SchoolQualif.HIGH_SCHOOL,
        req_clearance=SecurityClearance.SECRET,
        req_experience=6,
        salary=45_000,
        salary_variance=10,
)

seargeant_first_class = Job(
        name="Sergeant First Class",
        req_school=SchoolQualif.HIGH_SCHOOL,
        req_clearance=SecurityClearance.TOP_SECRET,
        req_experience=8,
        salary=50_000,
        salary_variance=10,
)

master_sergeant = Job(
        name="Master Sergeant",
        req_school=SchoolQualif.HIGH_SCHOOL,
        req_clearance=SecurityClearance.TOP_SECRET,
        req_experience=10,
        salary=60_000,
        salary_variance=15,
)

first_sergeant = Job(
        name="First Sergeant",
        req_school=SchoolQualif.HIGH_SCHOOL,
        req_clearance=SecurityClearance.TS_SCI,
        req_experience=10,
        salary=60_000,
        salary_variance=15,
)

sergeant_major = Job(
        name="Sergeant Major",
        req_school=SchoolQualif.HIGH_SCHOOL,
        req_clearance=SecurityClearance.TS_SCI,
        req_experience=12,
        salary=75_000,
        salary_variance=20,
)

command_sergeant_major = Job(
        name="Command Sergeant Major",
        req_school=SchoolQualif.HIGH_SCHOOL,
        req_clearance=SecurityClearance.SPECIAL,
        req_experience=12,
        salary=90_000,
        salary_variance=20,
)

sergeant_major_of_the_army = Job(
        name="Sergeant Major of the Army",
        req_school=SchoolQualif.HIGH_SCHOOL,
        req_clearance=SecurityClearance.SPECIAL,
        req_experience=15,
        salary=100_000,
        salary_variance=25,
)

enlisted_army_tree = JobTree(
        name="Enlisted_Army",
        jobs=[
            private,
            private_first_class,
            [corporal, specialist],
            sergeant,
            staff_sergeant,
            seargeant_first_class,
            [master_sergeant, first_sergeant],
            [sergeant_major, command_sergeant_major],
            sergeant_major_of_the_army,
        ],
)
collector.register_job_tree(enlisted_army_tree)

warrant_officer_1 = Job(
        name="Warrant Officer 1",
        req_experience=0,
        salary=28_000,
        salary_variance=5,
)

warrant_officer_2 = Job(
        name="Warrant Officer 2",
        req_school=SchoolQualif.ASSOCIATE,
        req_clearance=SecurityClearance.CONFIDENTIAL,
        req_experience=2,
        salary=32_500,
        salary_variance=5,
)

warrant_officer_3 = Job(
        name="Warrant Officer 3",
        req_school=SchoolQualif.BACHELOR,
        req_clearance=SecurityClearance.SECRET,
        req_experience=4,
        salary=35_000,
        salary_variance=10,
)

warrant_officer_4 = Job(
        name="Warrant Officer 4",
        req_school=SchoolQualif.BACHELOR,
        req_clearance=SecurityClearance.SECRET,
        req_experience=6,
        salary=40_000,
        salary_variance=10,
)

warrant_officer_5 = Job(
        name="Warrant Officer 5",
        req_school=SchoolQualif.BACHELOR,
        req_clearance=SecurityClearance.SECRET,
        req_experience=8,
        salary=45_000,
        salary_variance=10,
)

second_lieutenant = Job(
        name="Second Lieutenant",
        req_school=SchoolQualif.BACHELOR,
        req_clearance=SecurityClearance.SECRET,
        req_experience=10,
        salary=50_000,
        salary_variance=15,
)

first_lieutenant = Job(
        name="First Lieutenant",
        req_school=SchoolQualif.BACHELOR,
        req_clearance=SecurityClearance.TOP_SECRET,
        req_experience=12,
        salary=55_000,
        salary_variance=15,
)

captain = Job(
        name="Captain",
        req_school=SchoolQualif.BACHELOR,
        req_clearance=SecurityClearance.TOP_SECRET,
        req_experience=14,
        salary=60_000,
        salary_variance=15,
)

major = Job(
        name="Major",
        req_school=SchoolQualif.BACHELOR,
        req_clearance=SecurityClearance.TOP_SECRET,
        req_experience=16,
        salary=70_000,
        salary_variance=20,
)

lieutenant_colonel = Job(
        name="Lieutenant Colonel",
        req_school=SchoolQualif.BACHELOR,
        req_clearance=SecurityClearance.TS_SCI,
        req_experience=18,
        salary=80_000,
        salary_variance=20,
)

colonel = Job(
        name="Colonel",
        req_school=SchoolQualif.MASTER,
        req_clearance=SecurityClearance.TS_SCI,
        req_experience=20,
        salary=90_000,
        salary_variance=20,
)

brigadier_general = Job(
        name="Brigadier General",
        req_school=SchoolQualif.MASTER,
        req_clearance=SecurityClearance.SPECIAL,
        req_experience=22,
        salary=100_000,
        salary_variance=25,
)

major_general = Job(
        name="Major General",
        req_school=SchoolQualif.MASTER,
        req_clearance=SecurityClearance.SPECIAL,
        req_experience=24,
        salary=110_000,
        salary_variance=25,
)

lieutenant_general = Job(
        name="Lieutenant General",
        req_school=SchoolQualif.MASTER,
        req_clearance=SecurityClearance.SPECIAL,
        req_experience=26,
        salary=120_000,
        salary_variance=30,
)

general = Job(
        name="General",
        req_school=SchoolQualif.MASTER,
        req_clearance=SecurityClearance.SPECIAL,
        req_experience=28,
        salary=130_000,
        salary_variance=30,
)

army_commissioned_officer_tree = JobTree(
        name="Army_Commissioned_Officer",
        jobs=[
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
            general,
        ],
)
collector.register_job_tree(army_commissioned_officer_tree)

# Healthcare Jobs
certified_nurse_assistant = Job(
        name="Certified Nurse Assistant",
        req_experience=0,
        salary=27_500,
        salary_variance=5,
)

medical_assistant = Job(
        name="Medical Assistant",
        req_experience=0,
        salary=30_000,
        salary_variance=5,
)

registered_nurse = Job(
        name="Registered Nurse",
        req_school=SchoolQualif.ASSOCIATE,
        req_experience=2,
        salary=50_000,
        salary_variance=10,
)

licensed_practical_nurse = Job(
        name="Licensed Practical Nurse",
        req_school=SchoolQualif.ASSOCIATE,
        req_experience=2,
        salary=50_000,
        salary_variance=10,
)

nurse_practitioner = Job(
        name="Nurse Practitioner",
        req_school=SchoolQualif.BACHELOR,
        req_experience=4,
        salary=80_000,
        salary_variance=15,
)

nurse_manager = Job(
        name="Nurse Manager",
        req_school=SchoolQualif.BACHELOR,
        req_experience=6,
        salary=90_000,
        salary_variance=15,
)

healthcare_administrator = Job(
        name="Healthcare Administrator",
        req_school=SchoolQualif.MASTER,
        req_experience=8,
        salary=100_000,
        salary_variance=20,
)

clinical_director = Job(
        name="Clinical Director",
        req_school=SchoolQualif.MASTER,
        req_experience=10,
        salary=120_000,
        salary_variance=25,
)

healthcare_tree = JobTree(
        name="Healthcare",
        jobs=[
            [certified_nurse_assistant, medical_assistant],
            [registered_nurse, licensed_practical_nurse],
            nurse_practitioner,
            nurse_manager,
            healthcare_administrator,
            clinical_director,
        ],
)
collector.register_job_tree(healthcare_tree)

# Finance Jobs
financial_analyst = Job(
        name="Financial Analyst",
        req_school=SchoolQualif.ASSOCIATE,
        req_experience=0,
        salary=50_000,
        salary_variance=5,
)

junior_accountant = Job(
        name="Junior Accountant",
        req_school=SchoolQualif.ASSOCIATE,
        req_experience=0,
        salary=45_000,
        salary_variance=5,
)

senior_financial_analyst = Job(
        name="Senior Financial Analyst",
        req_school=SchoolQualif.BACHELOR,
        req_experience=3,
        salary=70_000,
        salary_variance=10,
)

accountant = Job(
        name="Accountant",
        req_school=SchoolQualif.BACHELOR,
        req_experience=3,
        salary=65_000,
        salary_variance=10,
)

senior_accountant = Job(
        name="Senior Accountant",
        req_school=SchoolQualif.BACHELOR,
        req_experience=5,
        salary=80_000,
        salary_variance=15,
)

financial_manager = Job(
        name="Financial Manager",
        req_school=SchoolQualif.MASTER,
        req_experience=7,
        salary=100_000,
        salary_variance=20,
)

finance_director = Job(
        name="Director of Finance",
        req_school=SchoolQualif.MASTER,
        req_experience=10,
        salary=120_000,
        salary_variance=25,
)

chief_financial_officer = Job(
        name="Chief Financial Officer",
        req_school=SchoolQualif.MASTER,
        req_experience=20,
        salary=150_000,
        salary_variance=45,
)

finance_tree = JobTree(
        name="Finance",
        jobs=[
            [financial_analyst, junior_accountant],
            [senior_financial_analyst, accountant],
            senior_accountant,
            financial_manager,
            finance_director,
            chief_financial_officer,
        ],
)
collector.register_job_tree(finance_tree)

special_agent_trainee = Job(
        name="Special Agent Trainee",
        req_experience=0,
        salary=30_000,
        salary_variance=5,
)

special_agent = Job(
        name="Special Agent",
        req_school=SchoolQualif.ASSOCIATE,
        req_clearance=SecurityClearance.CONFIDENTIAL,
        req_experience=2,
        salary=40_000,
        salary_variance=10,
)

senior_special_agent = Job(
        name="Senior Special Agent",
        req_school=SchoolQualif.ASSOCIATE,
        req_clearance=SecurityClearance.CONFIDENTIAL,
        req_experience=5,
        salary=45_000,
        salary_variance=10,
)

supervisory_special_agent = Job(
        name="Supervisory Special Agent",
        req_school=SchoolQualif.BACHELOR,
        req_clearance=SecurityClearance.SECRET,
        req_experience=8,
        salary=50_000,
        salary_variance=15,
)

special_agent_in_charge = Job(
        name="Special Agent in Charge",
        req_school=SchoolQualif.BACHELOR,
        req_clearance=SecurityClearance.SECRET,
        req_experience=10,
        salary=60_000,
        salary_variance=20,
)

federal_LE_assistant_director = Job(
        name="Assistant Director",
        req_school=SchoolQualif.MASTER,
        req_clearance=SecurityClearance.SECRET,
        req_experience=12,
        salary=70_000,
        salary_variance=25,
)

federal_LE_deputy_director = Job(
        name="Deputy Director",
        req_school=SchoolQualif.MASTER,
        req_clearance=SecurityClearance.SECRET,
        req_experience=15,
        salary=80_000,
        salary_variance=30,
)

federal_LE_director = Job(
        name="Director",
        req_school=SchoolQualif.MASTER,
        req_clearance=SecurityClearance.TOP_SECRET,
        req_experience=20,
        salary=120_000,
        salary_variance=35,
)

federal_law_enforcement_tree = JobTree(
        name="Federal_Law_Enforcement",
        jobs=[
            special_agent_trainee,
            special_agent,
            senior_special_agent,
            supervisory_special_agent,
            special_agent_in_charge,
            federal_LE_assistant_director,
            federal_LE_deputy_director,
            federal_LE_director,
        ],
)
collector.register_job_tree(federal_law_enforcement_tree)

# Local law enforcement jobs
police_cadet = Job(
        name="Police Cadet",
        req_experience=0,
        salary=30_000,
        salary_variance=5,
)

police_officer = Job(
        name="Police Officer",
        req_experience=2,
        salary=40_000,
        salary_variance=10,
)

detective = Job(
        name="Detective",
        req_school=SchoolQualif.BACHELOR,
        req_clearance=SecurityClearance.CONFIDENTIAL,
        req_experience=5,
        salary=50_000,
        salary_variance=10,
)

local_LE_corporal = Job(
        name="Corporal",
        req_school=SchoolQualif.BACHELOR,
        req_clearance=SecurityClearance.CONFIDENTIAL,
        req_experience=7,
        salary=55_000,
        salary_variance=10,
)

local_LE_sergeant = Job(
        name="Sergeant",
        req_school=SchoolQualif.BACHELOR,
        req_clearance=SecurityClearance.SECRET,
        req_experience=10,
        salary=60_000,
        salary_variance=15,
)

local_LE_lieutenant = Job(
        name="Lieutenant",
        req_school=SchoolQualif.BACHELOR,
        req_clearance=SecurityClearance.SECRET,
        req_experience=12,
        salary=70_000,
        salary_variance=15,
)

local_LE_captain = Job(
        name="Captain",
        req_school=SchoolQualif.BACHELOR,
        req_clearance=SecurityClearance.SECRET,
        req_experience=15,
        salary=80_000,
        salary_variance=20,
)

local_LE_commander = Job(
        name="Commander",
        req_school=SchoolQualif.BACHELOR,
        req_clearance=SecurityClearance.SECRET,
        req_experience=18,
        salary=90_000,
        salary_variance=25,
)

local_LE_assistant_chief = Job(
        name="Assistant Chief",
        req_school=SchoolQualif.BACHELOR,
        req_clearance=SecurityClearance.TOP_SECRET,
        req_experience=20,
        salary=100_000,
        salary_variance=30,
)

local_LE_chief = Job(
        name="Chief of Police",
        req_school=SchoolQualif.BACHELOR,
        req_clearance=SecurityClearance.TOP_SECRET,
        req_experience=25,
        salary=120_000,
        salary_variance=35,
)

local_law_enforcement_tree = JobTree(
        name="Local_Law_Enforcement",
        jobs=[
            police_cadet,
            police_officer,
            detective,
            local_LE_corporal,
            local_LE_sergeant,
            local_LE_lieutenant,
            local_LE_captain,
            local_LE_commander,
            local_LE_assistant_chief,
            local_LE_chief,
        ],
)
collector.register_job_tree(local_law_enforcement_tree)
