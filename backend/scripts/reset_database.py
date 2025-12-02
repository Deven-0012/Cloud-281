#!/usr/bin/env python3
"""
Reset database - remove all data except admin user
Then create a single test user: testing@gmail.com
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import uuid

def get_db_connection():
    """Get database connection"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        DATABASE_URL = 'postgresql://smart_car_user:SecurePassword123!@127.0.0.1:5433/smart_car_surveillance'
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def reset_database():
    """Remove all data except admin users"""
    conn = get_db_connection()
    if not conn:
        print("Error: Database connection failed.")
        return False
    
    try:
        with conn.cursor() as cur:
            print("Cleaning database...")
            
            # Delete all alerts
            cur.execute("DELETE FROM alert")
            print("  ✓ Deleted all alerts")
            
            # Delete all detections
            cur.execute("DELETE FROM detection")
            print("  ✓ Deleted all detections")
            
            # Delete all ingestion jobs
            cur.execute("DELETE FROM ingestion_job")
            print("  ✓ Deleted all ingestion jobs")
            
            # Delete all vehicles
            cur.execute("DELETE FROM vehicle")
            print("  ✓ Deleted all vehicles")
            
            # Delete all IoT devices
            cur.execute("DELETE FROM iot_device")
            print("  ✓ Deleted all IoT devices")
            
            # Delete all users except deven@gmail.com (the main admin)
            cur.execute("DELETE FROM users WHERE email != 'deven@gmail.com'")
            print("  ✓ Deleted all users except deven@gmail.com (admin)")
            
            conn.commit()
            print("\n✓ Database cleaned successfully!")
            return True
            
    except Exception as e:
        conn.rollback()
        print(f"Error cleaning database: {e}")
        return False
    finally:
        conn.close()

def create_test_user():
    """Create the test user: testing@gmail.com"""
    conn = get_db_connection()
    if not conn:
        print("Error: Database connection failed.")
        return False
    
    try:
        with conn.cursor() as cur:
            # Check if user already exists
            cur.execute("SELECT user_id FROM users WHERE email = %s", ('testing@gmail.com',))
            existing = cur.fetchone()
            
            if existing:
                # Update existing user
                user_id = existing[0]
                password_hash = bcrypt.hashpw('Test@12345'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cur.execute("""
                    UPDATE users 
                    SET password_hash = %s, role = 'owner', full_name = 'Test User'
                    WHERE user_id = %s
                """, (password_hash, user_id))
                conn.commit()
                print("✓ Updated existing user: testing@gmail.com")
            else:
                # Create new user
                # Get or create default tenant
                cur.execute("SELECT tenant_id FROM tenant LIMIT 1")
                tenant_row = cur.fetchone()
                if not tenant_row:
                    tenant_id = str(uuid.uuid4())
                    cur.execute("""
                        INSERT INTO tenant (tenant_id, name, email)
                        VALUES (%s, %s, %s)
                    """, (tenant_id, 'Default Tenant', 'default@tenant.com'))
                else:
                    tenant_id = tenant_row[0]
                
                # Create user
                user_id = str(uuid.uuid4())
                password_hash = bcrypt.hashpw('Test@12345'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cur.execute("""
                    INSERT INTO users (user_id, tenant_id, email, password_hash, full_name, role)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (user_id, tenant_id, 'testing@gmail.com', password_hash, 'Test User', 'owner'))
                conn.commit()
                print("✓ Created user: testing@gmail.com")
            
            return True
            
    except Exception as e:
        conn.rollback()
        print(f"Error creating user: {e}")
        return False
    finally:
        conn.close()

def create_admin_user():
    """Create or update the admin user: deven@gmail.com"""
    conn = get_db_connection()
    if not conn:
        print("Error: Database connection failed.")
        return False
    
    try:
        with conn.cursor() as cur:
            # Check if user already exists
            cur.execute("SELECT user_id FROM users WHERE email = %s", ('deven@gmail.com',))
            existing = cur.fetchone()
            
            # Get or create default tenant
            cur.execute("SELECT tenant_id FROM tenant LIMIT 1")
            tenant_row = cur.fetchone()
            if not tenant_row:
                tenant_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO tenant (tenant_id, name, email)
                    VALUES (%s, %s, %s)
                """, (tenant_id, 'Default Tenant', 'default@tenant.com'))
            else:
                tenant_id = tenant_row[0]
            
            password_hash = bcrypt.hashpw('Deven@123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            if existing:
                # Update existing user
                user_id = existing[0]
                cur.execute("""
                    UPDATE users 
                    SET password_hash = %s, role = 'admin', full_name = 'Deven Admin'
                    WHERE user_id = %s
                """, (password_hash, user_id))
                conn.commit()
                print("✓ Updated existing admin user: deven@gmail.com")
            else:
                # Create new admin user
                user_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO users (user_id, tenant_id, email, password_hash, full_name, role)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (user_id, tenant_id, 'deven@gmail.com', password_hash, 'Deven Admin', 'admin'))
                conn.commit()
                print("✓ Created admin user: deven@gmail.com")
            
            return True
            
    except Exception as e:
        conn.rollback()
        print(f"Error creating admin user: {e}")
        return False
    finally:
        conn.close()

def show_users():
    """Show all users"""
    conn = get_db_connection()
    if not conn:
        print("Error: Database connection failed.")
        return
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT user_id, email, full_name, role FROM users ORDER BY role, email")
            users = cur.fetchall()
            
            if users:
                print("\n--- Current Users ---")
                for user in users:
                    print(f"  {user['email']} ({user['role']}) - {user['full_name']}")
            else:
                print("\nNo users found.")
    except Exception as e:
        print(f"Error listing users: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="Reset database (users register themselves)")
    parser.add_argument('--create-default-users', action='store_true', help='Create default test users (optional, not recommended)')
    args = parser.parse_args()
    
    print("="*60)
    print("RESETTING DATABASE")
    print("="*60)
    print("This will delete ALL data.")
    print("Users must register themselves through the web interface.")
    print("Proceeding with reset...")
    
    if not reset_database():
        print("Failed to reset database.")
        sys.exit(1)
    
    # Only create default users if explicitly requested
    if args.create_default_users:
        print("\n" + "="*60)
        print("CREATING DEFAULT USERS (Optional)")
        print("="*60)
        
        # Create test user
        if not create_test_user():
            print("Failed to create test user.")
            sys.exit(1)
        
        # Create admin user
        if not create_admin_user():
            print("Failed to create admin user.")
            sys.exit(1)
        
        print("\nDefault User Credentials:")
        print("  Test User:")
        print("    Email: testing@gmail.com")
        print("    Password: Test@12345")
        print("  Admin User:")
        print("    Email: deven@gmail.com")
        print("    Password: Deven@123")
        show_users()
    
    print("\n" + "="*60)
    print("SUCCESS!")
    print("="*60)
    print("Database reset complete.")
    print("\nNo default users created.")
    print("Users must register themselves at: /register")
    print("They can choose 'Owner' or 'Admin' role during registration.")
    print("\n" + "="*60)

