#!/bin/bash
# Script to create/update admin user: deven@gmail.com

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$BACKEND_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set database URL (use port 5433 for Docker PostgreSQL)
export DATABASE_URL="${DATABASE_URL:-postgresql://smart_car_user:SecurePassword123\!@127.0.0.1:5433/smart_car_surveillance}"

echo "Creating/updating admin user: deven@gmail.com"
python scripts/manage_users.py create deven@gmail.com "Deven@123" --name "Deven Admin" --role admin

echo ""
echo "Admin user created/updated successfully!"
echo "Email: deven@gmail.com"
echo "Password: Deven@123"
echo "Role: admin"

