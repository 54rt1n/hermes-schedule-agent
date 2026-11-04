# Recurrence, conflicts and availability

## Select the intended change

For timed recurring events, distinguish one occurrence, the whole series, and that
occurrence and all later occurrences. Resolve ambiguous user intent before a destructive
scope choice. Keep `(series_id, original_start)` from the queried occurrence: a moved
instance's current start is not its identity. Query that original identity when
verifying a move. Future splits may return a new series ID; retain returned IDs and
inspect both the retained past and new future schedule.
Supply occurrence or future scope explicitly with an occurrence timestamp; series
scope rejects that combination for updates and deletes.

Before changing an anchor or recurrence rule, inspect existing exceptions with
CLI `schedule --profile NAME events exceptions list ID`. The service rejects ambiguous remapping. Do not erase
exceptions merely to make an edit pass. Restoring an occurrence via
CLI `schedule --profile NAME events exceptions restore ID --occurrence ORIGINAL-TIME` removes its cancellation
or modification and checks conflicts first. Verify the restored occurrence afterward.

Descriptions, participants and calendar assignment belong to the timed series, not
an occurrence-only patch. Non-timed variants currently reject occurrence/future edits
and deletes; report that limitation instead of silently applying a series change.

## Check conflicts and propose available time

Timed writes reject detected overlaps. Recurring checks cover 366 days and at most
10,000 proposed occurrences; success is not proof of an indefinitely conflict-free
series. For a different horizon, use CLI flags:

```bash
schedule --profile NAME conflicts check --title "Planning" \
  --start START-TIME --end END-TIME --through HORIZON-END
```

Use offset-bearing times and replace placeholders with the requested candidate and
horizon. Optional `--data @event.json` is available for scripts. This report accepts
timed events. Generated nonexistent DST times cause validation errors; do not shift
the appointment silently. Read definitions and resolve the intended rule or dates.

Use CLI `schedule --profile NAME availability busy` for merged busy intervals or
`schedule --profile NAME availability slots` with the
requested duration and window for candidate times. When supplied, use working hours
and the user's timezone. Read CLI help for the JSON working-hours representation.
Busy reporting includes all-day blocks and separately identifies point appointments;
point appointments have no duration and tasks do not automatically reserve time.
Timed-write conflict checking is not a guarantee that every all-day or point
commitment was considered: inspect the agenda alongside availability before proposing
a time. Availability is a report, not a reservation or an invitation.

Verify recurring changes in the immediate window and a representative later window.
Explain the inspected horizon and any unresolved exception conflicts. Do not describe
a proposal as booked until the mutation and verification succeed.
