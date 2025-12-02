# 🚗 Smart Car Cloud Platform — Full Manual Setup Guide

This README provides a complete **manual setup guide** for running the Smart Car Cloud Platform, including:

* Docker databases (Postgres, MongoDB, Redis)
* Python backend services
* Flask ingestion API
* Frontend (Vite + React)
* Audio processing worker

Each major component runs in its **own terminal**, simulating a distributed microservices environment.

---

# 📁 Project Structure (Relevant)

```
Cloud-281/
│
├── backend/
│   ├── services/
│   ├── scripts/
│   ├── venv/
│   ├── requirements.txt
│   └── ...
│
├── frontend/
│   └── smartCar/
│
└── model/
    └── my_yamnet_human_model_fixed.keras
```

---

# 🖥 Terminal 1 — Start Databases (Docker)

**Path:** `./Cloud-281`

```bash
dcd ./Cloud-281
docker compose up -d postgres mongodb redis
```

Wait **20 seconds**, then verify all three containers:

```bash
docker compose ps
```

Expected:

* `postgres` → Up (healthy)
* `mongodb` → Up (healthy)
* `redis` → Up

Keep Terminal 1 running.

---

# 🖥 Terminal 2 — Backend Setup & Database Reset

**Path:** `./Cloud-281/backend`

```bash
cd ./Cloud-281/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python scripts/reset_database.py
```

Expected Output:

```
Database cleaned/reset
User created: testing@gmail.com
Admin user created: deven@gmail.com
```

### 🔍 Verify Users

```bash
python -c "
import psycopg2
from psycopg2.extras import RealDictCursor
conn = psycopg2.connect('postgresql://smart_car_user:SecurePassword123!@127.0.0.1:5433/smart_car_surveillance')
cur = conn.cursor(cursor_factory=RealDictCursor)
cur.execute('SELECT email, role FROM users')
for row in cur.fetchall():
    print(f\"{row['email']} - {row['role']}\")
cur.close()
conn.close()
"
```

Keep Terminal 2 open.

---

# 🖥 Terminal 3 — Flask Backend API Service

**Path:** `./Cloud-281/backend`

```bash
cd ./Cloud-281/backend
source venv/bin/activate

export DATABASE_URL='postgresql://smart_car_user:SecurePassword123!@127.0.0.1:5433/smart_car_surveillance'
export FLASK_APP='services/audio_ingestion_service.py'
export FLASK_ENV='development'
export JWT_SECRET='your-secret-key-change-in-production'
export LOCAL_MODE='true'
export MONGODB_URI='mongodb://admin:SecurePassword123!@127.0.0.1:27017/'
export REDIS_URL='redis://127.0.0.1:6379/0'

python -m flask run --host=0.0.0.0 --port=5001
```

### Test API:

```bash
curl http://localhost:5001/health
```

Expected Output:

```
{"status":"ok"}
```

Keep Terminal 3 open.

---

# 🖥 Terminal 4 — Frontend Dashboard (Vite + React)

**Path:** `./Cloud-281/frontend/smartCar`

```bash
cd ./Cloud-281/frontend/smartCar
npm install
export VITE_API_URL='http://localhost:5001'
npm run dev
```

Expected:

```
VITE vX.X.X ready in XXX ms
➜  Local: http://localhost:5173/
```

Open your browser:
👉 **[http://localhost:5173](http://localhost:5173)**

Keep Terminal 4 open.

---

# 🖥 Terminal 5 — Audio Processing Worker

**Path:** `./Cloud-281/backend`

```bash
cd ./Cloud-281/backend
source venv/bin/activate

export DATABASE_URL='postgresql://smart_car_user:SecurePassword123!@127.0.0.1:5433/smart_car_surveillance'
export MODEL_PATH='./Cloud-281/model/my_yamnet_human_model_fixed.keras'
export LOCAL_MODE='true'

./scripts/run_process_audio.sh
```

If not executable:

```bash
chmod +x scripts/run_process_audio.sh
```

Keep Terminal 5 running. This worker processes audio files.

---

# 🎯 Summary of All Terminals

| Terminal | Runs                             | Status                                 |
| -------- | -------------------------------- | -------------------------------------- |
| **1**    | Docker: Postgres, MongoDB, Redis | Required                               |
| **2**    | Database reset + backend env     | Required                               |
| **3**    | Flask backend API (port 5001)    | Required                               |
| **4**    | Frontend (Vite server)           | Required                               |
| **5**    | Audio processing worker          | Optional but needed for audio features |

---

# 🎉 Your System Is Now Fully Operational

You now have:

* A working backend API
* A working database cluster
* A working ML processing pipeline
* A working frontend dashboard
* Microservices running across multiple terminals

If you want this turned into a **PDF**, “**Quick Start**” version, or a **diagram**, just tell me!
