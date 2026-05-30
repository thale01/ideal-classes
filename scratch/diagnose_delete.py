import sys
import os
import django

# Add the project directory to sys.path to run from any working directory
sys.path.append(r'C:\Users\siddh\OneDrive\Desktop\IDEAL-CLASSES')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ideal_class.settings')
django.setup()

from django.db import connection

def diagnose():
    print("=== Starting Database Diagnostics ===")
    with connection.cursor() as cursor:
        # 1. Check Active Table Locks
        print("\n--- Checking Active Table Locks on 'education_note' ---")
        cursor.execute("""
            SELECT l.pid, relation::regclass, mode, granted, query
            FROM pg_locks l
            JOIN pg_stat_activity a ON a.pid = l.pid
            WHERE relation::regclass::text LIKE '%note%';
        """)
        locks = cursor.fetchall()
        if not locks:
            print("No active locks found on tables matching 'note'.")
        for lock in locks:
            print(f"PID: {lock[0]}, Relation: {lock[1]}, Mode: {lock[2]}, Granted: {lock[3]}")
            print(f"Query: {lock[4]}\n")

        # 2. Check All Active Queries that are Active/Waiting
        print("\n--- Checking All Active/Hanging Database Queries ---")
        cursor.execute("""
            SELECT pid, age(clock_timestamp(), query_start), state, query
            FROM pg_stat_activity
            WHERE state != 'idle' AND pid != pg_backend_pid();
        """)
        queries = cursor.fetchall()
        if not queries:
            print("No other active queries running right now.")
        for q in queries:
            print(f"PID: {q[0]}, Age: {q[1]}, State: {q[2]}")
            print(f"Query: {q[3]}\n")

        # 3. Check Constraints and Foreign Keys on 'education_note'
        print("\n--- Checking Foreign Keys pointing to 'education_note' ---")
        cursor.execute("""
            SELECT conname, pg_get_constraintdef(c.oid)
            FROM pg_constraint c
            JOIN pg_namespace n ON n.oid = c.connamespace
            WHERE conrelid::regclass::text LIKE '%note%' OR confrelid::regclass::text LIKE '%note%';
        """)
        constraints = cursor.fetchall()
        if not constraints:
            print("No constraints found on 'education_note'.")
        for c in constraints:
            print(f"Constraint Name: {c[0]}\nDefinition: {c[1]}\n")

if __name__ == '__main__':
    diagnose()
