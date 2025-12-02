#!/usr/bin/env python3
"""
Assign all vehicles and alerts to a specific user
Usage: python scripts/assign_vehicles_to_user.py user@example.com
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

def assign_vehicles_to_user(email):
    """Assign all vehicles to the specified user"""
    conn = get_db_connection()
    if not conn:
        print("Error: Database connection failed.")
        return False
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get user_id
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            user_result = cur.fetchone()
            
            if not user_result:
                print(f"Error: User '{email}' not found.")
                print("Available users:")
                cur.execute("SELECT email, role FROM users")
                for row in cur.fetchall():
                    print(f"  - {row['email']} ({row['role']})")
                return False
            
            user_id = user_result['user_id']
            
            # Count vehicles before
            cur.execute("SELECT COUNT(*) as count FROM vehicle WHERE owner_id = %s", (user_id,))
            before_count = cur.fetchone()['count']
            
            # Assign all vehicles to this user
            cur.execute("""
                UPDATE vehicle 
                SET owner_id = %s 
                WHERE owner_id IS NULL OR owner_id != %s
            """, (user_id, user_id))
            
            updated_count = cur.rowcount
            conn.commit()
            
            # Count vehicles after
            cur.execute("SELECT COUNT(*) as count FROM vehicle WHERE owner_id = %s", (user_id,))
            after_count = cur.fetchone()['count']
            
            print(f"✓ Assigned {updated_count} vehicle(s) to {email}")
            print(f"✓ Total vehicles for {email}: {after_count}")
            
            # Show vehicles
            cur.execute("""
                SELECT vehicle_id, make, model, status 
                FROM vehicle 
                WHERE owner_id = %s
                ORDER BY created_at DESC
            """, (user_id,))
            
            vehicles = cur.fetchall()
            if vehicles:
                print("\nVehicles assigned:")
                for v in vehicles:
                    print(f"  - {v['vehicle_id']} ({v['make']} {v['model']}) - {v['status']}")
            
            # Count alerts for these vehicles
            if vehicles:
                vehicle_ids = [v['vehicle_id'] for v in vehicles]
                placeholders = ','.join(['%s'] * len(vehicle_ids))
                cur.execute(f"""
                    SELECT COUNT(*) as count 
                    FROM alert 
                    WHERE vehicle_id IN ({placeholders})
                """, vehicle_ids)
                alert_count = cur.fetchone()['count']
                print(f"\n✓ Total alerts for these vehicles: {alert_count}")
            
            return True
            
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/assign_vehicles_to_user.py user@example.com")
        print("\nThis script assigns all vehicles (and their alerts) to the specified user.")
        sys.exit(1)
    
    email = sys.argv[1]
    print(f"Assigning all vehicles to: {email}")
    print("="*60)
    
    if assign_vehicles_to_user(email):
        print("\n" + "="*60)
        print("SUCCESS!")
        print("="*60)
        print(f"All vehicles are now assigned to {email}")
        print("You should now see alerts in the dashboard.")
    else:
        print("\n" + "="*60)
        print("FAILED!")
        print("="*60)
        sys.exit(1)

