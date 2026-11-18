# Acceptance test checklist

- [ ] Register a User and Admin with distinct email addresses.
- [ ] Login with correct role/email/password; mismatched role returns 403.
- [ ] Duplicate email returns 409; weak password rejected by schema.
- [ ] User cannot access `/api/users`, `/api/reports/summary`, or admin product creation (403).
- [ ] Admin creates one product in each of the four supported categories.
- [ ] Category outside the four allowed values is rejected.
- [ ] Create work order, start it, record output, pause/resume/complete.
- [ ] Output above planned quantity is rejected.
- [ ] Post material receipt; issue within stock; overspending stock is rejected.
- [ ] Quality accepted + rejected cannot exceed inspected quantity.
- [ ] Create maintenance task and verify audit trail.
- [ ] Verify dashboard/report totals reflect saved database records.
- [ ] `npm run build` completes without frontend build errors.
