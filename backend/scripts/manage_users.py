#!/usr/bin/env python3
"""
User management script for Smart Car Surveillance Platform
"""
import os
import sys
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import uuid

# Add parent directory to path to import services
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_db_connection():
    """Get database connection"""
    # Use port 5433 for Docker PostgreSQL
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        DATABASE_URL = 'postgresql://smart_car_user:SecurePassword123!@127.0.0.1:5433/smart_car_surveillance'
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print(f"Tried connecting to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")
        return None

def list_users():
    conn = get_db_connection()
    if not conn:
        print("Error: Database connection failed.")
        return

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT user_id, email, full_name, role, created_at, last_login FROM users ORDER BY created_at DESC")
            users = cur.fetchall()
            if users:
                print("\n--- Existing Users ---")
                for user in users:
                    print(f"ID: {user['user_id']}")
                    print(f"  Email: {user['email']}")
                    print(f"  Name: {user['full_name'] or 'N/A'}")
                    print(f"  Role: {user['role']}")
                    print(f"  Created: {user['created_at']}")
                    print(f"  Last Login: {user['last_login'] or 'N/A'}")
                    print("-" * 20)
            else:
                print("No users found in the database.")
    except Exception as e:
        print(f"Error listing users: {e}")
    finally:
        conn.close()

def create_user(email, password, full_name=None, role='owner'):
    conn = get_db_connection()
    if not conn:
        print("Error: Database connection failed.")
        return

    try:
        with conn.cursor() as cur:
            # Check if user exists
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            existing = cur.fetchone()
            if existing:
                # User exists - update password and role
                user_id = existing[0]
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cur.execute("""
                    UPDATE users 
                    SET password_hash = %s, role = %s, full_name = COALESCE(%s, full_name)
                    WHERE user_id = %s
                """, (password_hash, role, full_name, user_id))
                conn.commit()
                print(f"✓ Updated existing user: {email} with role '{role}'")
                return

            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Get or create default tenant
            cur.execute("SELECT tenant_id FROM tenant LIMIT 1")
            tenant_row = cur.fetchone()
            if not tenant_row:
                tenant_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO tenant (tenant_id, name, email)
                    VALUES (%s, %s, %s)
                """, (tenant_id, 'Default Tenant', 'default@tenant.com'))
                print(f"Created default tenant: {tenant_id}")
            else:
                tenant_id = tenant_row[0]

            # Create user
            user_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO users (user_id, tenant_id, email, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, tenant_id, email, password_hash, full_name, role))
            conn.commit()
            print(f"✓ Successfully created user: {email} with role '{role}'")
    except Exception as e:
        conn.rollback()
        print(f"Error creating user: {e}")
    finally:
        conn.close()

def reset_password(email, new_password):
    conn = get_db_connection()
    if not conn:
        print("Error: Database connection failed.")
        return

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            user_row = cur.fetchone()
            if not user_row:
                print(f"Error: User with email '{email}' not found.")
                return

            user_id = user_row[0]
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            cur.execute("UPDATE users SET password_hash = %s WHERE user_id = %s", (password_hash, user_id))
            conn.commit()
            print(f"✓ Successfully reset password for user: {email}")
    except Exception as e:
        conn.rollback()
        print(f"Error resetting password: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Manage users in the Smart Car Surveillance Platform database.")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List command
    list_parser = subparsers.add_parser('list', help='List all existing users.')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new user.')
    create_parser.add_argument('email', type=str, help='Email for the new user.')
    create_parser.add_argument('password', type=str, help='Password for the new user.')
    create_parser.add_argument('--name', type=str, default=None, help='Full name of the new user.')
    create_parser.add_argument('--role', type=str, default='owner', choices=['owner', 'admin'], help='Role of the new user (default: owner).')

    # Reset password command
    reset_parser = subparsers.add_parser('reset', help='Reset password for an existing user.')
    reset_parser.add_argument('email', type=str, help='Email of the user to reset password for.')
    reset_parser.add_argument('new_password', type=str, help='New password for the user.')

    args = parser.parse_args()

    if args.command == 'list':
        list_users()
    elif args.command == 'create':
        create_user(args.email, args.password, args.name, args.role)
    elif args.command == 'reset':
        reset_password(args.email, args.new_password)
    else:
        parser.print_help()

