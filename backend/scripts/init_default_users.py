#!/usr/bin/env python3
"""
Initialize Default Users - Creates default users for first-time setup
This script ensures that testing@gmail.com and deven@gmail.com exist
with their default passwords, so anyone pulling the code can log in.
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
        print(f"Make sure PostgreSQL is running and accessible at: {DATABASE_URL}")
        return None

def ensure_tenant():
    """Ensure default tenant exists"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT tenant_id FROM tenant LIMIT 1")
            tenant_row = cur.fetchone()
            
            if not tenant_row:
                tenant_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO tenant (tenant_id, name, email)
                    VALUES (%s, %s, %s)
                """, (tenant_id, 'Default Tenant', 'default@tenant.com'))
                conn.commit()
                print("✓ Created default tenant")
                return tenant_id
            else:
                return tenant_row[0]
    except Exception as e:
        print(f"Error ensuring tenant: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def create_or_update_user(email, password, full_name, role):
    """Create or update a user with the specified credentials"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            # Check if user exists
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            existing = cur.fetchone()
            
            # Get or create tenant
            tenant_id = ensure_tenant()
            if not tenant_id:
                print(f"Error: Could not get/create tenant")
                return False
            
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            if existing:
                # Update existing user to ensure correct password
                user_id = existing[0]
                cur.execute("""
                    UPDATE users 
                    SET password_hash = %s, role = %s, full_name = %s
                    WHERE user_id = %s
                """, (password_hash, role, full_name, user_id))
                conn.commit()
                print(f"✓ Updated user: {email}")
                return True
            else:
                # Create new user
                user_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO users (user_id, tenant_id, email, password_hash, full_name, role)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (user_id, tenant_id, email, password_hash, full_name, role))
                conn.commit()
                print(f"✓ Created user: {email}")
                return True
            
    except Exception as e:
        conn.rollback()
        print(f"Error creating/updating user {email}: {e}")
        return False
    finally:
        conn.close()

def show_users():
    """Show all users"""
    conn = get_db_connection()
    if not conn:
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
    print("="*60)
    print("INITIALIZING DEFAULT USERS")
    print("="*60)
    print("This script ensures default users exist for login.")
    print("")
    
    # Create test user (owner)
    print("Creating test user (testing@gmail.com)...")
    if not create_or_update_user('testing@gmail.com', 'Test@12345', 'Test User', 'owner'):
        print("Failed to create test user.")
        sys.exit(1)
    
    # Create admin user
    print("\nCreating admin user (deven@gmail.com)...")
    if not create_or_update_user('deven@gmail.com', 'Deven@123', 'Deven Admin', 'admin'):
        print("Failed to create admin user.")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("SUCCESS!")
    print("="*60)
    show_users()
    
    print("\n" + "="*60)
    print("DEFAULT LOGIN CREDENTIALS")
    print("="*60)
    print("\nTest User (Owner):")
    print("  Email: testing@gmail.com")
    print("  Password: Test@12345")
    print("\nAdmin User:")
    print("  Email: deven@gmail.com")
    print("  Password: Deven@123")
    print("\n" + "="*60)
    print("These credentials are now available for login!")
    print("="*60)

