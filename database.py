import sqlite3
from pathlib import Path

# ==========================================
# DATABASE CONFIGURATION
# ==========================================

DATABASE_PATH = Path(__file__).resolve().parent / "company.db"


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    # Enable foreign key relationships
    connection.execute("PRAGMA foreign_keys = ON")
    # Return rows as dictionary-like objects
    connection.row_factory = sqlite3.Row
    return connection


# ==========================================
# CREATE DATABASE TABLES & INSERT DATA
# ==========================================

def create_and_populate_database():
    connection = get_connection()
    cursor = connection.cursor()

    # 1. Clear existing tables to start fresh (optional, but good for tutorials)
    cursor.execute("DROP TABLE IF EXISTS employees")
    cursor.execute("DROP TABLE IF EXISTS departments")

    # 2. Create Departments Table
    cursor.execute('''
        CREATE TABLE departments (
            department_id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_name TEXT NOT NULL,
            location TEXT NOT NULL
        )
    ''')

    # 3. Create Employees Table
    cursor.execute('''
        CREATE TABLE employees (
            employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name TEXT NOT NULL,
            email TEXT NOT NULL,
            salary REAL NOT NULL,
            department_id INTEGER,
            designation TEXT NOT NULL,
            joining_year INTEGER,
            FOREIGN KEY (department_id) REFERENCES departments (department_id)
        )
    ''')

    # 4. Insert Sample Departments
    departments_data = [
        ('IT', 'New York'),
        ('HR', 'San Francisco'),
        ('Finance', 'Chicago'),
        ('Marketing', 'Austin'),
        ('Sales', 'Seattle')
    ]
    cursor.executemany('INSERT INTO departments (department_name, location) VALUES (?, ?)', departments_data)

    # 5. Insert Sample Employees (20 records)
    # Note: department_id 1=IT, 2=HR, 3=Finance, 4=Marketing, 5=Sales
    employees_data = [
        ('Rahul Sharma', 'rahul.sharma@company.com', 85000, 1, 'Software Engineer', 2020),
        ('Priya Reddy', 'priya.reddy@company.com', 78000, 1, 'Data Analyst', 2019),
        ('Arjun Kumar', 'arjun.kumar@company.com', 92000, 1, 'Senior Developer', 2018),
        ('Sneha Gupta', 'sneha.gupta@company.com', 72000, 1, 'Junior Developer', 2022),
        ('Vikram Singh', 'vikram.singh@company.com', 110000, 1, 'Tech Lead', 2017),
        
        ('Ananya S', 'ananya.s@company.com', 65000, 2, 'HR Coordinator', 2021),
        ('Rohan P', 'rohan.p@company.com', 70000, 2, 'Recruiter', 2020),
        ('Meera J', 'meera.j@company.com', 82000, 2, 'HR Manager', 2019),
        
        ('Karan M', 'karan.m@company.com', 95000, 3, 'Financial Analyst', 2020),
        ('Divya S', 'divya.s@company.com', 105000, 3, 'Senior Accountant', 2018),
        ('Raj T', 'raj.t@company.com', 88000, 3, 'Budget Planner', 2021),
        
        ('Isha N', 'isha.n@company.com', 68000, 4, 'Marketing Specialist', 2022),
        ('Varun K', 'varun.k@company.com', 75000, 4, 'Content Strategist', 2020),
        ('Pooja L', 'pooja.l@company.com', 80000, 4, 'Digital Marketing Lead', 2019),
        
        ('Aditya B', 'aditya.b@company.com', 72000, 5, 'Sales Associate', 2021),
        ('Nisha R', 'nisha.r@company.com', 74000, 5, 'Account Executive', 2020),
        ('Sanjay V', 'sanjay.v@company.com', 90000, 5, 'Sales Manager', 2018),
        ('Amit D', 'amit.d@company.com', 69000, 5, 'Junior Sales Rep', 2022),
        ('Priti K', 'priti.k@company.com', 85000, 5, 'Senior Sales Manager', 2017),
    ]
    cursor.executemany('''
        INSERT INTO employees 
        (employee_name, email, salary, department_id, designation, joining_year) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', employees_data)

    connection.commit()
    
    # ==========================================
    # VERIFICATION / DEBUG PRINT
    # ==========================================
    print("✅ Database initialized successfully!\n")
    print("EMPLOYEE RECORDS")
    print("-" * 80)
    
    # Fetch all employees for display
    rows = cursor.execute('SELECT * FROM employees').fetchall()
    for row in rows:
        print(f"{row['employee_id']} {row['employee_name']:15} {row['salary']:>10.2f} {row['department_name'] if 'department_name' in row.keys() else 'N/A'} {row['designation']}")
        # Note: The above print might need adjustment if we don't join the table. Let's do a simpler print.
    
    # Simpler print for the chat user
    print("\nDETAILED VIEW:")
    for row in rows:
        dept_id = row['department_id']
        name = row['employee_name']
        salary = row['salary']
        desk = row['designation']
        # Get department name manually for display
        dept_name = cursor.execute('SELECT department_name FROM departments WHERE department_id=?', (dept_id,)).fetchone()[0]
        print(f"ID: {row['employee_id']} | Name: {name:15} | Salary: ${salary:>10.2f} | Dept: {dept_name:10} | Role: {desk}")

    print("-" * 80)
    print(f"Total employees: {len(rows)}")
    
    connection.close()

# ==========================================
# MAIN EXECUTION
# ==========================================

if __name__ == "__main__":
    create_and_populate_database()