# ElectroFIMS acceptance checklist

Use a fresh local database and the demo accounts from README. Record pass/fail and evidence for each item before submission.

## Authentication and roles
- [ ] Public homepage has no visible login form.
- [ ] Login opens the separate Admin Login / User Login chooser.
- [ ] User registration persists the account; correct email/password signs in; incorrect password is rejected.
- [ ] Admin account cannot be publicly registered; administrator creates privileged users through User Management.
- [ ] All seven seeded roles sign in and see the appropriate navigation.
- [ ] Backend returns 401 for unauthenticated protected calls and 403 for unauthorized role actions.
- [ ] Logout returns to homepage and protected routes require a new login.

## Master data
- [ ] Products and materials use unique codes.
- [ ] Work centers, machines, shifts, suppliers and BOM versions/lines are maintained.
- [ ] Master records can be used by downstream plans and work orders.

## Production
- [ ] Production Manager creates a valid plan and work order.
- [ ] Supervisor releases/starts/pauses/completes only valid status transitions.
- [ ] Operator records production output; good + rejected equals produced.
- [ ] Overproduction is blocked unless administrator-authorized with an audit reason.
- [ ] Dashboard/report quantities agree with saved production entries.

## Inventory
- [ ] Storekeeper posts receipt and issue transactions.
- [ ] Stock is derived from receipts less issues/adjustments.
- [ ] Issue exceeding available stock is rejected.
- [ ] Movement history identifies material, type, quantity, reference and user.

## Quality, maintenance and downtime
- [ ] Quality Inspector records inspected/accepted/rejected quantities and defect details.
- [ ] Accepted + rejected cannot exceed inspected quantity.
- [ ] Maintenance Technician schedules and completes tasks.
- [ ] Downtime includes machine, start/end, reason and recorded-by user.
- [ ] Machine status changes require reason and audit event.

## Reporting, reliability and presentation
- [ ] Reports reconcile with saved transactions and filters/pagination are verified.
- [ ] Audit history includes sensitive actions.
- [ ] Responsive layouts, keyboard navigation, loading, empty, validation and error states are checked.
- [ ] No browser console errors or backend tracebacks during the full demo.
- [ ] Factory location is replaced with verified coordinates/address before real-world presentation.
- [ ] Demo data, secrets and demo passwords are not used in production.
