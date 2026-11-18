# ElectroFIMS update notes

## Fixes in this update
- Added an Administrator Create Account flow guarded by `ADMIN_REGISTRATION_KEY`. Admin credentials created through this flow are stored using the existing password hash flow and can be used immediately for Admin Login.
- Kept public User Create Account restricted to the Machine Operator role. Administrators can assign the other six roles through User Management.
- Hid work-order creation from roles that the API does not authorize (for example, Machine Operator), preventing the 403 banner caused by a visible but forbidden action.
- Restricted work-order status actions to Administrator, Production Manager, and Production Supervisor, and aligned the buttons with the actual status transitions (Planned → Released → In Progress).
- Added browser-side validation requiring Good + Rejected = Produced before submitting a production entry.
- Allowed Maintenance Technician to record downtime, matching the maintenance role workflow.

## Verification status
- Python source syntax compilation passed (`python -m compileall -q backend/app`).
- Frontend production build was not verified in this environment because `npm install` did not complete before timeout. Run `npm install` and `npm run build` on the user's machine.
- Full end-to-end acceptance testing against a fresh database and all seven roles remains required. This update does not claim every item in the supplied Word specification is fully implemented.
