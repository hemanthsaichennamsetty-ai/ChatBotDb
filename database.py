import sqlite3
import random
from datetime import date, timedelta
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent / "company.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection


def create_and_populate_database():
    random.seed(20261125)
    connection = get_connection()
    cursor = connection.cursor()

    tables_to_drop = [
        "attendance_logs",
        "delivery_incidents",
        "employee_certifications",
        "salary_history",
        "performance_reviews",
        "employee_projects",
        "projects",
        "clients",
        "employees",
        "departments",
    ]
    for tbl in tables_to_drop:
        cursor.execute(f"DROP TABLE IF EXISTS {tbl}")

    # 1. DEPARTMENTS (12 Practices & Delivery Hubs)
    cursor.execute('''
        CREATE TABLE departments (
            department_id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_name TEXT NOT NULL,
            location TEXT NOT NULL,
            region TEXT NOT NULL,
            annual_budget REAL NOT NULL,
            cost_center_code TEXT NOT NULL
        )
    ''')

    # 2. EMPLOYEES (1,000 Staff across CL6 -> CL12)
    cursor.execute('''
        CREATE TABLE employees (
            employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            salary REAL NOT NULL,
            department_id INTEGER NOT NULL,
            manager_id INTEGER,
            career_level TEXT NOT NULL,
            designation TEXT NOT NULL,
            employment_type TEXT NOT NULL,
            joining_year INTEGER NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (department_id) REFERENCES departments (department_id),
            FOREIGN KEY (manager_id) REFERENCES employees (employee_id)
        )
    ''')

    # 3. CLIENTS (18 Enterprise Accounts)
    cursor.execute('''
        CREATE TABLE clients (
            client_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            industry TEXT NOT NULL,
            hq_country TEXT NOT NULL,
            tier TEXT NOT NULL,
            annual_contract_value REAL NOT NULL
        )
    ''')

    # 4. PROJECTS (36 Client & Internal Engagements)
    cursor.execute('''
        CREATE TABLE projects (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            client_id INTEGER NOT NULL,
            department_id INTEGER NOT NULL,
            billing_model TEXT NOT NULL,
            budget REAL NOT NULL,
            status TEXT NOT NULL,
            start_year INTEGER NOT NULL,
            deadline_quarter TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients (client_id),
            FOREIGN KEY (department_id) REFERENCES departments (department_id)
        )
    ''')

    # 5. EMPLOYEE_PROJECTS (Staffing & Billability)
    cursor.execute('''
        CREATE TABLE employee_projects (
            assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            project_id INTEGER NOT NULL,
            role_on_project TEXT NOT NULL,
            allocation_percent INTEGER NOT NULL,
            is_billable INTEGER NOT NULL,
            assigned_date TEXT NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id),
            FOREIGN KEY (project_id) REFERENCES projects (project_id)
        )
    ''')

    # 6. PERFORMANCE_REVIEWS
    cursor.execute('''
        CREATE TABLE performance_reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            review_year INTEGER NOT NULL,
            rating REAL NOT NULL,
            bonus_awarded REAL NOT NULL,
            reviewer_notes TEXT NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
        )
    ''')

    # 7. SALARY_HISTORY
    cursor.execute('''
        CREATE TABLE salary_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            effective_year INTEGER NOT NULL,
            previous_salary REAL NOT NULL,
            new_salary REAL NOT NULL,
            change_reason TEXT NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
        )
    ''')

    # 8. EMPLOYEE_CERTIFICATIONS (Cloud, AI, Security, ERP Credentials)
    cursor.execute('''
        CREATE TABLE employee_certifications (
            cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            certification_name TEXT NOT NULL,
            vendor TEXT NOT NULL,
            issued_year INTEGER NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
        )
    ''')

    # 9. DELIVERY_INCIDENTS (Live Engagement Tickets / Escalations)
    cursor.execute('''
        CREATE TABLE delivery_incidents (
            incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            assigned_employee_id INTEGER NOT NULL,
            severity TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT NOT NULL,
            resolution_hours REAL NOT NULL,
            reported_date TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects (project_id),
            FOREIGN KEY (assigned_employee_id) REFERENCES employees (employee_id)
        )
    ''')

    # 10. ATTENDANCE_LOGS (14 Days of Daily Shift / Work Mode Telemetry)
    cursor.execute('''
        CREATE TABLE attendance_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            work_date TEXT NOT NULL,
            check_in_time TEXT,
            work_mode TEXT NOT NULL,
            hours_logged REAL NOT NULL,
            attendance_status TEXT NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
        )
    ''')

    # Indexes for fast querying on large tables
    cursor.execute('CREATE INDEX idx_emp_dept ON employees(department_id)')
    cursor.execute('CREATE INDEX idx_emp_mgr ON employees(manager_id)')
    cursor.execute('CREATE INDEX idx_emp_cl ON employees(career_level)')
    cursor.execute('CREATE INDEX idx_proj_client ON projects(client_id)')
    cursor.execute('CREATE INDEX idx_proj_dept ON projects(department_id)')
    cursor.execute('CREATE INDEX idx_ep_emp ON employee_projects(employee_id)')
    cursor.execute('CREATE INDEX idx_ep_proj ON employee_projects(project_id)')
    cursor.execute('CREATE INDEX idx_rev_emp ON performance_reviews(employee_id)')
    cursor.execute('CREATE INDEX idx_cert_emp ON employee_certifications(employee_id)')
    cursor.execute('CREATE INDEX idx_inc_proj ON delivery_incidents(project_id)')
    cursor.execute('CREATE INDEX idx_att_emp_date ON attendance_logs(employee_id, work_date)')

    # ---------------------------------------------------------
    # 1. DEPARTMENTS (12 Practices)
    # ---------------------------------------------------------
    departments_data = [
        ('Cloud First & Infrastructure', 'Bengaluru', 'APAC', 18500000, 'ACN-CF-BLR-01'),
        ('Data & AI Practice', 'Bengaluru', 'APAC', 21000000, 'ACN-DAI-BLR-02'),
        ('SAP & Enterprise Platforms', 'Hyderabad', 'APAC', 16400000, 'ACN-SAP-HYD-03'),
        ('Song (Digital & Experience)', 'Mumbai', 'APAC', 12200000, 'ACN-SNG-MUM-04'),
        ('Security & Cyber Defense', 'Hyderabad', 'APAC', 14600000, 'ACN-SEC-HYD-05'),
        ('Strategy & Consulting', 'Gurugram', 'APAC', 15800000, 'ACN-SC-GGN-06'),
        ('Intelligent Operations', 'Chennai', 'APAC', 13500000, 'ACN-IO-CHN-07'),
        ('Application Modernization', 'Pune', 'APAC', 11900000, 'ACN-AM-PUN-08'),
        ('Network & Edge Engineering', 'Bengaluru', 'APAC', 10400000, 'ACN-NE-BLR-09'),
        ('Supply Chain & Sustainability', 'Mumbai', 'APAC', 9800000, 'ACN-SCS-MUM-10'),
        ('Finance, Risk & Legal', 'Gurugram', 'APAC', 7600000, 'ACN-FRL-GGN-11'),
        ('Talent & Workplace Ops', 'Hyderabad', 'APAC', 6500000, 'ACN-TWO-HYD-12'),
    ]
    cursor.executemany(
        'INSERT INTO departments (department_name, location, region, annual_budget, cost_center_code) VALUES (?, ?, ?, ?, ?)',
        departments_data
    )

    # ---------------------------------------------------------
    # 2. EMPLOYEES (1,000 Staff across 12 Practices)
    # ---------------------------------------------------------
    first_names = [
        'Aarav', 'Aditya', 'Arjun', 'Vikram', 'Rohan', 'Karan', 'Varun', 'Nikhil', 'Siddharth', 'Harsh',
        'Ananya', 'Priya', 'Sneha', 'Kavya', 'Meera', 'Pooja', 'Divya', 'Nisha', 'Shruti', 'Tanvi',
        'Karthik', 'Pranav', 'Raghav', 'Sandeep', 'Abhishek', 'Tarun', 'Yash', 'Deepak', 'Gaurav', 'Manoj',
        'Aishwarya', 'Bhavna', 'Chaitra', 'Deepika', 'Gayathri', 'Haritha', 'Jahnavi', 'Keerthi', 'Lavanya', 'Madhuri',
        'Chethan', 'Suresh', 'Ramesh', 'Mahesh', 'Naveen', 'Pavan', 'Sai', 'Teja', 'Vamsi', 'Harsha',
        'Akshay', 'Amol', 'Ashish', 'Bhargav', 'Chandan', 'Dinesh', 'Ganesh', 'Hemanth', 'Jagadish', 'Kiran',
        'Lakshmi', 'Mamatha', 'Nandini', 'Pallavi', 'Rachana', 'Sowmya', 'Spandana', 'Triveni', 'Uma', 'Vaishnavi'
    ]
    last_names = [
        'Reddy', 'Sharma', 'Rao', 'Nair', 'Menon', 'Iyer', 'Patel', 'Gupta', 'Kumar', 'Verma',
        'Joshi', 'Kulkarni', 'Deshmukh', 'Naidu', 'Choudhary', 'Bhat', 'Hegde', 'Shenoy', 'Mishra', 'Tiwari',
        'Chatterjee', 'Banerjee', 'Mukherjee', 'Ghosh', 'Pillai', 'Nambiar', 'Kamat', 'Pai', 'Sastry', 'Murthy'
    ]

    # (career_level, designation, min_sal, max_sal, tier)
    dept_roles = {
        1: [('CL6', 'Senior Manager - Cloud First', 2600000, 3350000, 0), ('CL7', 'Cloud Delivery Manager', 2000000, 2550000, 1), ('CL8', 'Associate Manager - Cloud', 1600000, 1980000, 1), ('CL9', 'Cloud Specialist', 1150000, 1550000, 2), ('CL10', 'Senior Cloud Analyst', 820000, 1120000, 2), ('CL11', 'Cloud Analyst', 550000, 780000, 2)],
        2: [('CL6', 'Senior Manager - Data & AI', 2750000, 3550000, 0), ('CL7', 'AI & Analytics Manager', 2100000, 2650000, 1), ('CL8', 'Associate Manager - GenAI', 1680000, 2080000, 1), ('CL9', 'AI / Data Specialist', 1220000, 1620000, 2), ('CL10', 'Senior Data Analyst', 860000, 1160000, 2), ('CL11', 'Data Analyst', 580000, 810000, 2)],
        3: [('CL6', 'Senior Manager - SAP', 2550000, 3250000, 0), ('CL7', 'SAP Program Manager', 1950000, 2500000, 1), ('CL8', 'Associate Manager - ERP', 1550000, 1920000, 1), ('CL9', 'SAP Consultant', 1100000, 1500000, 2), ('CL10', 'Senior Systems Analyst', 800000, 1080000, 2), ('CL11', 'Systems Analyst', 520000, 750000, 2)],
        4: [('CL6', 'Senior Manager - Song CX', 2450000, 3100000, 0), ('CL7', 'Digital Experience Manager', 1850000, 2350000, 1), ('CL8', 'Associate Manager - UX/Web', 1480000, 1840000, 1), ('CL9', 'Experience Specialist', 1050000, 1420000, 2), ('CL10', 'Senior UX/UI Analyst', 780000, 1040000, 2), ('CL11', 'Digital Analyst', 500000, 720000, 2)],
        5: [('CL6', 'Senior Manager - Cyber Defense', 2650000, 3400000, 0), ('CL7', 'Cybersecurity Manager', 2050000, 2600000, 1), ('CL8', 'Associate Manager - SecOps', 1620000, 2000000, 1), ('CL9', 'Cyber Specialist', 1180000, 1580000, 2), ('CL10', 'Senior Security Analyst', 840000, 1140000, 2), ('CL11', 'Security Analyst', 560000, 780000, 2)],
        6: [('CL6', 'Senior Manager - Strategy', 2850000, 3650000, 0), ('CL7', 'Consulting Manager', 2180000, 2780000, 1), ('CL8', 'Associate Manager - Advisory', 1720000, 2120000, 1), ('CL9', 'Management Consultant', 1260000, 1660000, 2), ('CL10', 'Senior Business Analyst', 880000, 1180000, 2), ('CL11', 'Business Analyst', 600000, 820000, 2)],
        7: [('CL6', 'Senior Manager - Intelligent Ops', 2100000, 2650000, 0), ('CL7', 'Operations Manager', 1600000, 2050000, 1), ('CL8', 'Associate Manager - Ops', 1250000, 1580000, 1), ('CL9', 'Operations Team Lead', 880000, 1200000, 2), ('CL10', 'Senior Ops Analyst', 620000, 850000, 2), ('CL12', 'Associate - Operations', 380000, 560000, 2)],
        8: [('CL6', 'Senior Manager - App Mod', 2500000, 3150000, 0), ('CL7', 'Modernization Manager', 1920000, 2450000, 1), ('CL8', 'Associate Manager - FullStack', 1520000, 1880000, 1), ('CL9', 'App Mod Specialist', 1100000, 1480000, 2), ('CL10', 'Senior Software Analyst', 790000, 1060000, 2), ('CL11', 'Software Analyst', 520000, 740000, 2)],
        9: [('CL6', 'Senior Manager - Network/Edge', 2450000, 3100000, 0), ('CL7', 'Network Delivery Manager', 1880000, 2380000, 1), ('CL8', 'Associate Manager - 5G/Edge', 1500000, 1850000, 1), ('CL9', 'Network Specialist', 1080000, 1450000, 2), ('CL10', 'Senior Network Analyst', 780000, 1050000, 2), ('CL11', 'Network Analyst', 510000, 730000, 2)],
        10: [('CL6', 'Senior Manager - Supply Chain', 2400000, 3050000, 0), ('CL7', 'Supply Chain Manager', 1850000, 2320000, 1), ('CL8', 'Associate Manager - SCM', 1460000, 1800000, 1), ('CL9', 'Supply Chain Specialist', 1040000, 1400000, 2), ('CL10', 'Senior SCM Analyst', 760000, 1020000, 2), ('CL11', 'Supply Chain Analyst', 490000, 700000, 2)],
        11: [('CL6', 'Senior Manager - Finance/Risk', 2450000, 3100000, 0), ('CL7', 'Risk & Finance Manager', 1860000, 2340000, 1), ('CL8', 'Associate Manager - Risk', 1480000, 1820000, 1), ('CL9', 'Risk / Finance Specialist', 1050000, 1420000, 2), ('CL10', 'Senior Risk Analyst', 760000, 1020000, 2), ('CL11', 'Finance Analyst', 490000, 710000, 2)],
        12: [('CL6', 'Senior Manager - Talent/Ops', 2200000, 2750000, 0), ('CL7', 'Talent Delivery Manager', 1650000, 2100000, 1), ('CL8', 'Associate Manager - HR/Ops', 1300000, 1620000, 1), ('CL9', 'Talent / Ops Specialist', 920000, 1240000, 2), ('CL10', 'Senior HR/Ops Analyst', 650000, 880000, 2), ('CL11', 'Corporate Analyst', 450000, 640000, 2)],
    }

    used_emails = set()

    def unique_email(fn, ln):
        base = f"{fn.lower()}.{ln.lower()}"
        email = f"{base}@accenture.com"
        idx = 1
        while email in used_emails:
            email = f"{base}{idx}@accenture.com"
            idx += 1
        used_emails.add(email)
        return email

    practice_heads = {}
    people_leads = {d: [] for d in range(1, 13)}

    # 12 Practice Leads (CL6)
    for d_id in range(1, 13):
        fn, ln = random.choice(first_names), random.choice(last_names)
        cl, desig, lo, hi, _ = dept_roles[d_id][0]
        sal = round(random.randint(lo, hi) / 10000) * 10000
        jyr = random.randint(2015, 2019)
        cursor.execute('''
            INSERT INTO employees (employee_name, email, salary, department_id, manager_id, career_level, designation, employment_type, joining_year, status)
            VALUES (?, ?, ?, ?, NULL, ?, ?, 'Full-Time', ?, 'Active')
        ''', (f"{fn} {ln}", unique_email(fn, ln), sal, d_id, cl, desig, jyr))
        practice_heads[d_id] = cursor.lastrowid

    # 60 People Leads (5 per department: CL7 / CL8)
    for d_id in range(1, 13):
        mgr_pool = [r for r in dept_roles[d_id] if r[4] == 1]
        for _ in range(5):
            fn, ln = random.choice(first_names), random.choice(last_names)
            cl, desig, lo, hi, _ = random.choice(mgr_pool)
            sal = round(random.randint(lo, hi) / 10000) * 10000
            jyr = random.randint(2017, 2022)
            cursor.execute('''
                INSERT INTO employees (employee_name, email, salary, department_id, manager_id, career_level, designation, employment_type, joining_year, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Full-Time', ?, 'Active')
            ''', (f"{fn} {ln}", unique_email(fn, ln), sal, d_id, practice_heads[d_id], cl, desig, jyr))
            people_leads[d_id].append(cursor.lastrowid)

    # 928 Delivery & Corporate Staff (CL9 - CL12)
    for _ in range(928):
        fn, ln = random.choice(first_names), random.choice(last_names)
        d_id = random.randint(1, 12)
        ic_pool = [r for r in dept_roles[d_id] if r[4] == 2]
        cl, desig, lo, hi, _ = random.choice(ic_pool)
        sal = round(random.randint(lo, hi) / 10000) * 10000
        mgr_id = random.choice(people_leads[d_id])
        jyr = random.randint(2019, 2026)
        emp_type = random.choices(['Full-Time', 'Hybrid', 'Contract'], weights=[78, 16, 6])[0]
        status = random.choices(['Active', 'On Leave'], weights=[95, 5])[0]
        cursor.execute('''
            INSERT INTO employees (employee_name, email, salary, department_id, manager_id, career_level, designation, employment_type, joining_year, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (f"{fn} {ln}", unique_email(fn, ln), sal, d_id, mgr_id, cl, desig, emp_type, jyr, status))

    # ---------------------------------------------------------
    # 3. CLIENTS (18 Enterprise Accounts)
    # ---------------------------------------------------------
    clients_data = [
        ('Northstar Global Bank', 'Banking & Capital Markets', 'United Kingdom', 'Platinum', 18500000),
        ('Helvetia Assurance Group', 'Insurance', 'Switzerland', 'Platinum', 14200000),
        ('Nordic Telecom Networks', 'Communications & Media', 'Sweden', 'Gold', 11800000),
        ('Titan Industrial Corp', 'Industrial & Manufacturing', 'Germany', 'Platinum', 16400000),
        ('Apex Consumer Brands', 'Consumer Goods & Retail', 'United States', 'Gold', 10500000),
        ('Veloce Mobility Systems', 'Automotive', 'Japan', 'Gold', 9600000),
        ('Meridian FinTech Holdings', 'Banking & Payments', 'Singapore', 'Gold', 8900000),
        ('Evergreen Health Partners', 'Life Sciences & Health', 'United States', 'Platinum', 15100000),
        ('Aether Supply & Freight', 'Logistics & Transportation', 'Netherlands', 'Silver', 7400000),
        ('Solstice Power & Grid', 'Utilities & Energy', 'United States', 'Gold', 11200000),
        ('Kestrel Aerospace & Defense', 'Aerospace & Defense', 'France', 'Platinum', 13800000),
        ('Banyan Retail India', 'Retail & E-Commerce', 'India', 'Gold', 8200000),
        ('Deccan Core Banking', 'Banking', 'India', 'Gold', 9400000),
        ('Lumina Pharma Labs', 'Life Sciences', 'Switzerland', 'Silver', 6800000),
        ('Harbor Container Lines', 'Logistics', 'Denmark', 'Silver', 7100000),
        ('Crescendo Media Studios', 'Media & Entertainment', 'United States', 'Silver', 6200000),
        ('Veritas Sovereign Cloud', 'Public Sector & Gov', 'United Kingdom', 'Gold', 10900000),
        ('Accenture Internal Programs', 'Internal Enterprise', 'India', 'Internal', 5500000),
    ]
    cursor.executemany(
        'INSERT INTO clients (client_name, industry, hq_country, tier, annual_contract_value) VALUES (?, ?, ?, ?, ?)',
        clients_data
    )

    # ---------------------------------------------------------
    # 4. PROJECTS (36 Client & Internal Engagements)
    # ---------------------------------------------------------
    billing_models = ['Time & Materials', 'Fixed Price', 'Managed Services']
    statuses = ['In Progress', 'Completed', 'Planning']
    quarters = ['Q4 2026', 'Q1 2027', 'Q2 2027', 'Q3 2027']
    projects_data = []

    for idx in range(1, 37):
        d_id = ((idx - 1) % 12) + 1
        c_id = 18 if idx > 33 else ((idx - 1) % 17) + 1
        pname = f"Engagement #{idx:02d} — {departments_data[d_id - 1][0].split('&')[0].strip()} Transformation"
        bmodel = random.choice(billing_models)
        budget = round(random.randint(900000, 5800000) / 50000) * 50000
        pstatus = random.choices(statuses, weights=[68, 22, 10])[0]
        syear = random.randint(2024, 2026)
        dquarter = random.choice(quarters)
        projects_data.append((pname, c_id, d_id, bmodel, budget, pstatus, syear, dquarter))

    cursor.executemany(
        'INSERT INTO projects (project_name, client_id, department_id, billing_model, budget, status, start_year, deadline_quarter) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        projects_data
    )

    # ---------------------------------------------------------
    # 5. EMPLOYEE_PROJECTS (~1,350 Staffing Allocations)
    # ---------------------------------------------------------
    proj_roles = ['Solution Architect', 'Tech Lead', 'Senior Consultant', 'AI / Cloud Specialist', 'Delivery Analyst', 'QA & Automation']
    assignments = []
    seen_pairs = set()

    for emp_id in range(1, 1001):
        num_assign = random.choices([1, 2], weights=[65, 35])[0]
        for pid in random.sample(range(1, 37), num_assign):
            if (emp_id, pid) not in seen_pairs:
                seen_pairs.add((emp_id, pid))
                alloc = 100 if num_assign == 1 else random.choice([40, 50, 60])
                is_bill = 0 if pid > 33 else random.choices([1, 0], weights=[89, 11])[0]
                assigned_dt = (date(2026, 11, 25) - timedelta(days=random.randint(7, 365))).isoformat()
                assignments.append((emp_id, pid, random.choice(proj_roles), alloc, is_bill, assigned_dt))

    cursor.executemany(
        'INSERT INTO employee_projects (employee_id, project_id, role_on_project, allocation_percent, is_billable, assigned_date) VALUES (?, ?, ?, ?, ?, ?)',
        assignments
    )

    # ---------------------------------------------------------
    # 6. PERFORMANCE_REVIEWS (2025 & 2026 Cycles)
    # ---------------------------------------------------------
    notes_pool = [
        'Delivered high-value client outcomes with strong sprint velocity.',
        'Demonstrated career-level leadership, reusable assets, and mentorship.',
        'Consistent SLA adherence and clear stakeholder communication.',
        'Recognized for resolving complex production & architecture bottlenecks.'
    ]
    emp_rows = cursor.execute('SELECT employee_id, salary, joining_year FROM employees').fetchall()
    reviews = []
    sal_hist = []
    reasons = ['Annual Talent Cycle Revision', 'Career Level Promotion', 'Market Benchmark Adjustment', 'Variable & Merit Revision']

    for r in emp_rows:
        eid, sal, jyr = r['employee_id'], r['salary'], r['joining_year']
        for yr in [2025, 2026]:
            if jyr <= yr:
                rating = round(random.uniform(3.2, 5.0), 1)
                pct = 0.15 if rating >= 4.5 else (0.10 if rating >= 4.0 else 0.05)
                bonus = round((sal * pct) / 5000) * 5000
                reviews.append((eid, yr, rating, bonus, random.choice(notes_pool)))

        if jyr < 2026:
            prev_sal = round((sal * random.uniform(0.83, 0.93)) / 10000) * 10000
            sal_hist.append((eid, 2026, prev_sal, sal, random.choice(reasons)))

    cursor.executemany(
        'INSERT INTO performance_reviews (employee_id, review_year, rating, bonus_awarded, reviewer_notes) VALUES (?, ?, ?, ?, ?)',
        reviews
    )
    cursor.executemany(
        'INSERT INTO salary_history (employee_id, effective_year, previous_salary, new_salary, change_reason) VALUES (?, ?, ?, ?, ?)',
        sal_hist
    )

    # ---------------------------------------------------------
    # 7. EMPLOYEE_CERTIFICATIONS (1,600+ Credentials)
    # ---------------------------------------------------------
    certs_catalog = [
        ('AWS Certified Solutions Architect - Associate', 'AWS'),
        ('AWS Certified Machine Learning - Specialty', 'AWS'),
        ('Microsoft Certified: Azure Administrator', 'Microsoft'),
        ('Google Cloud Professional Cloud Architect', 'Google Cloud'),
        ('SAP Certified Application Associate - S/4HANA', 'SAP'),
        ('Certified Kubernetes Administrator (CKA)', 'CNCF'),
        ('Certified Information Systems Security Professional', 'ISC2'),
        ('Databricks Certified Data Engineer Associate', 'Databricks'),
    ]
    cert_rows = []
    for emp in emp_rows:
        eid, jyr = emp['employee_id'], emp['joining_year']
        for cname, vendor in random.sample(certs_catalog, random.randint(1, 2)):
            iyr = random.randint(max(2020, jyr), 2026)
            cstatus = random.choices(['Active', 'Renewal Due'], weights=[88, 12])[0]
            cert_rows.append((eid, cname, vendor, iyr, cstatus))

    cursor.executemany(
        'INSERT INTO employee_certifications (employee_id, certification_name, vendor, issued_year, status) VALUES (?, ?, ?, ?, ?)',
        cert_rows
    )

    # ---------------------------------------------------------
    # 8. DELIVERY_INCIDENTS (450 Live / Historical Tickets)
    # ---------------------------------------------------------
    severities = ['P1 - Critical', 'P2 - High', 'P3 - Medium', 'P4 - Low']
    categories = ['Cloud Latency', 'Pipeline / ETL', 'Security / IAM', 'ERP Config', 'API Integration']
    inc_statuses = ['Resolved', 'In Progress', 'Escalated']
    inc_rows = []

    for _ in range(450):
        pid = random.randint(1, 36)
        emp_id = random.randint(1, 1000)
        sev = random.choices(severities, weights=[8, 22, 45, 25])[0]
        cat = random.choice(categories)
        istatus = random.choices(inc_statuses, weights=[76, 17, 7])[0]
        res_hrs = round(random.uniform(1.5, 48.0), 1)
        rep_dt = (date(2026, 11, 25) - timedelta(days=random.randint(0, 60))).isoformat()
        inc_rows.append((pid, emp_id, sev, cat, istatus, res_hrs, rep_dt))

    cursor.executemany(
        'INSERT INTO delivery_incidents (project_id, assigned_employee_id, severity, category, status, resolution_hours, reported_date) VALUES (?, ?, ?, ?, ?, ?, ?)',
        inc_rows
    )

    # ---------------------------------------------------------
    # 9. ATTENDANCE_LOGS (14 Days = 14,000 Daily Records)
    # ---------------------------------------------------------
    today = date(2026, 11, 25)
    att_rows = []
    for day_offset in range(14):
        d_str = (today - timedelta(days=day_offset)).isoformat()
        for emp in emp_rows:
            eid = emp['employee_id']
            mode = random.choices(['Office', 'WFH', 'Client Site'], weights=[52, 30, 18])[0]
            astatus = random.choices(['Present', 'On Leave', 'Half Day'], weights=[92, 5, 3])[0]
            if astatus == 'On Leave':
                cin, hrs = None, 0.0
            elif astatus == 'Half Day':
                cin, hrs = f"09:{random.randint(10, 45):02d}:00", 4.5
            else:
                cin, hrs = f"{random.randint(8, 10):02d}:{random.randint(0, 59):02d}:00", round(random.uniform(8.0, 9.5), 1)
            att_rows.append((eid, d_str, cin, mode, hrs, astatus))

    cursor.executemany(
        'INSERT INTO attendance_logs (employee_id, work_date, check_in_time, work_mode, hours_logged, attendance_status) VALUES (?, ?, ?, ?, ?, ?)',
        att_rows
    )

    connection.commit()

    print("✅ Vast Accenture-modeled organizational database created: company.db\n")
    for t in tables_to_drop[::-1]:
        cnt = cursor.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        print(f"  • {t:26}: {cnt:>7,} rows")

    connection.close()


if __name__ == "__main__":
    create_and_populate_database()
