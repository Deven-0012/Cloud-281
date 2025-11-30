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
    
    parser = argparse.ArgumentParser(description="Reset database and create test user")
    parser.add_argument('--no-reset', action='store_true', help='Skip database reset, only create user')
    args = parser.parse_args()
    
    if not args.no_reset:
        print("="*60)
        print("RESETTING DATABASE")
        print("="*60)
        print("This will delete ALL data except admin users.")
        print("Proceeding with reset...")
        
        if not reset_database():
            print("Failed to reset database.")
            sys.exit(1)
    
    print("\n" + "="*60)
    print("CREATING TEST USER")
    print("="*60)
    if create_test_user():
        print("\n" + "="*60)
        print("SUCCESS!")
        print("="*60)
        show_users()
        print("\nTest User Credentials:")
        print("  Email: testing@gmail.com")
        print("  Password: Test@12345")
        print("\nAdmin Credentials:")
        print("  Email: deven@gmail.com")
        print("  Password: Deven@123")
    else:
        print("Failed to create user.")
        sys.exit(1)

