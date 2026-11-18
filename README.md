# ElectroFIMS — Factory Information Management System

React + Vite frontend and FastAPI + SQLAlchemy REST backend for a factory workflow training/demo application. Uses fictional records only. This is an information system; it does not control PLCs, robots, machine start/stop, or safety interlocks.

## Highlights
- Public marketing homepage with Home, About, Features, Modules and Contact sections. **No login form is shown on the homepage.**
- Login navigation opens a separate page with Admin Login and User Login choices.
- User self-registration saves a hashed password; newly registered users receive the least-privileged `machine_operator` role and must sign in with the registered email/password.
- Administrator accounts cannot be publicly self-registered. An existing administrator creates admin/privileged accounts from User Management. This avoids public privilege escalation.
- Seven roles: Administrator, Production Manager, Production Supervisor, Machine Operator, Storekeeper, Quality Inspector and Maintenance Technician.
- JWT authentication, password hashing, backend role authorization, audit events, dashboard summaries, production work orders/entries, inventory movements, quality inspections, maintenance tasks, downtime and reports.
- Responsive interface, hover/3D-style landing visual, charts, tables, forms and success/error feedback.
- SQLite works out of the box for local demos. MySQL can be configured with `DATABASE_URL`.

## Requirements
- Python 3.11+
- Node.js 20+
- MySQL 8+ (optional; SQLite is the default local database)

## Backend setup
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
uvicorn app.main:app --reload
```
API health: http://localhost:8000/health  
Swagger/OpenAPI: http://localhost:8000/docs

The app creates tables and fictional demo records on first startup. Default demo password for all seeded demo accounts is `Demo@12345`:
| Role | Email |
|---|---|
| Administrator | admin@electrofims.demo |
| Production Manager | manager@electrofims.demo |
| Production Supervisor | supervisor@electrofims.demo |
| Machine Operator | operator@electrofims.demo |
| Storekeeper | storekeeper@electrofims.demo |
| Quality Inspector | quality@electrofims.demo |
| Maintenance Technician | maintenance@electrofims.demo |

Change demo passwords and `SECRET_KEY` before any shared deployment. Do not use the demo credentials in production.

### MySQL configuration
Create a database, install the MySQL driver (included in requirements), and set for example:
```env
DATABASE_URL=mysql+pymysql://USER:PASSWORD@localhost:3306/electrofims
SECRET_KEY=replace-with-a-long-random-secret
CORS_ORIGINS=http://localhost:5173
```
Never commit real credentials.

## Frontend setup
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. To use another backend URL, create `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000/api
```
Production build: `npm run build`.

## Account and access behavior
- Homepage Login button routes to the dedicated login page; there is no embedded login form on the homepage.
- Admin Login accepts only an account whose backend role is `administrator`.
- User Login accepts non-administrator roles. Public account creation creates a Machine Operator account only.
- Admins can create accounts and assign any of the seven roles using User Management API `POST /api/users`; they can update roles and active status using `PATCH /api/users/{id}`.
- Logout clears the local session and returns the user to the public homepage.
- Frontend navigation is role-filtered; protected API endpoints independently enforce role permissions.

## Factory location
The contact map currently displays a clearly labelled **Hyderabad demo-area marker**, not a verified factory address. The actual factory address/coordinates were not supplied. Replace the demo marker and contact details with the verified site location before presenting this as a real factory location. Do not treat the demo marker as an actual plant address.

## Important implementation scope
This is a demo foundation, not a certified production deployment. Review the acceptance checklist, complete any site-specific master data and test every workflow with the target database. The UI must not be connected to physical machinery or safety systems.

## Administrator self-registration (optional)

Public self-registration always creates the least-privileged `machine_operator` role. To enable the separate **Admin Login → Create Account** flow, set a private key in `backend/.env`:

```env
ADMIN_REGISTRATION_KEY=use-a-long-private-random-value
```

Restart FastAPI, then enter that same key in the Administrator Create Account form. The API validates the key and creates the account as `administrator`; the user can then sign in using the exact email and password they registered. Do not publish or share this key. If the key is blank, admin self-registration is disabled; an existing administrator can still create administrator accounts from User Management.

## Role/action alignment

Work-order creation is shown only to Administrator and Production Manager. Production Supervisors can run permitted work-order status transitions; Machine Operators can record output but cannot create or administer work orders. The UI hides actions that the API will reject, and the API remains the permission authority.


## Admin and User account registration (DEMO)

The login page offers separate Admin Login and User Login paths. Both paths include Create Account. Admin registration stores the account with the `administrator` role; User registration stores it with the `machine_operator` role. After successful registration, sign in using the exact same email and password. No Administrator Setup Key is required in this local demo build.

**Demo credentials** (created automatically at backend startup):
- Admin: `admin@electrofims.demo` / `Demo@12345`
- User: `operator@electrofims.demo` / `Demo@12345`

Security note: unrestricted admin self-registration is enabled only to satisfy this training/demo request. Before any public deployment, restrict administrator creation to an existing administrator or a one-time bootstrap process.
