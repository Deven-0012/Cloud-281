#!/usr/bin/env python3
"""
Script to fix vehicle ownership - assign unassigned vehicles to a specific user
or reassign all vehicles to their correct owners based on folder names
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

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

def list_unassigned_vehicles():
    """List all vehicles with NULL owner_id"""
    conn = get_db_connection()
    if not conn:
        print("Error: Database connection failed.")
        return []
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT vehicle_id, owner_id FROM vehicle WHERE owner_id IS NULL")
            vehicles = cur.fetchall()
            return vehicles
    except Exception as e:
        print(f"Error listing vehicles: {e}")
        return []
    finally:
        conn.close()

def assign_vehicle_to_user(vehicle_id, user_email):
    """Assign a vehicle to a user by email"""
    conn = get_db_connection()
    if not conn:
        print("Error: Database connection failed.")
        return False
    
    try:
        with conn.cursor() as cur:
            # Get user_id from email
            cur.execute("SELECT user_id FROM users WHERE email = %s", (user_email,))
            user_result = cur.fetchone()
            if not user_result:
                print(f"Error: User with email '{user_email}' not found.")
                return False
            
            user_id = user_result[0]
            
            # Update vehicle
            cur.execute("UPDATE vehicle SET owner_id = %s WHERE vehicle_id = %s", (user_id, vehicle_id))
            conn.commit()
            print(f"✓ Assigned vehicle {vehicle_id} to user {user_email}")
            return True
    except Exception as e:
        conn.rollback()
        print(f"Error assigning vehicle: {e}")
        return False
    finally:
        conn.close()

def show_all_vehicles():
    """Show all vehicles and their owners"""
    conn = get_db_connection()
    if not conn:
        print("Error: Database connection failed.")
        return
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT v.vehicle_id, v.owner_id, u.email as owner_email, u.role as owner_role
                FROM vehicle v
                LEFT JOIN users u ON v.owner_id = u.user_id
                ORDER BY v.vehicle_id
            """)
            vehicles = cur.fetchall()
            
            if vehicles:
                print("\n--- All Vehicles ---")
                for v in vehicles:
                    owner_info = f"{v['owner_email']} ({v['owner_role']})" if v['owner_email'] else "UNASSIGNED"
                    print(f"Vehicle: {v['vehicle_id']} → Owner: {owner_info}")
            else:
                print("No vehicles found.")
    except Exception as e:
        print(f"Error listing vehicles: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix vehicle ownership in the database")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all vehicles and their owners')
    
    # Show unassigned
    unassigned_parser = subparsers.add_parser('unassigned', help='List vehicles with no owner')
    
    # Assign command
    assign_parser = subparsers.add_parser('assign', help='Assign a vehicle to a user')
    assign_parser.add_argument('vehicle_id', type=str, help='Vehicle ID to assign')
    assign_parser.add_argument('user_email', type=str, help='Email of the user to assign to')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        show_all_vehicles()
    elif args.command == 'unassigned':
        vehicles = list_unassigned_vehicles()
        if vehicles:
            print(f"\nFound {len(vehicles)} unassigned vehicles:")
            for v in vehicles:
                print(f"  - {v['vehicle_id']}")
        else:
            print("\nNo unassigned vehicles found.")
    elif args.command == 'assign':
        assign_vehicle_to_user(args.vehicle_id, args.user_email)
    else:
        parser.print_help()

