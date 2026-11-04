---
name: schedule-events
description: Execute appointment, agenda, availability and recurring-event workflows with Schedule Agent. Use schedule-tasks for task inventory and completion.
---
# Events and agenda

Use MCP for supported operations in the connected profile. For an explicitly different
profile, use the CLI with `--profile NAME` before the command. Follow the workspace's
authorization workflow.

## Read the schedule

Resolve relative dates against the real local date and timezone. Use the occurrence
view for an agenda and definitions to inspect a stored event or its recurrence.
A successful empty agenda does not establish an empty task inventory: undated and
completed tasks require definitions. Load `schedule-tasks` for open or overdue work.
A task may appear at both its scheduled date and deadline; preserve both dates but
count its stable ID once when counting commitments.

## Create or change an event

1. Find the existing commitment before creating a similar one. Resolve identity from
   title, calendar, date/time and context; use its ID for corrections.
2. Choose timed when both bounds are known, point for a known time without duration,
   all-day for a date or exclusive-ended date range, and anniversary for a yearly date.
   Do not turn an uncertain meeting into a confirmed appointment or invent its duration.
3. Read the current record and patch only the requested fields. For recurring changes,
   load [recurrence](references/recurrence.md) before selecting scope.
4. Check the successful result and any returned record, then query the affected
   window; for deletion, verify absence. For a move, check both old and new windows.
   A conflict response means the change was rejected; resolve
   the conflict before retrying rather than treating the proposal as booked.

Point, all-day and anniversary events support whole-series edits/deletes only.
Do not substitute that for an unsupported occurrence-only change. Participants and
descriptions currently apply to timed events. Contact references resolve to email
identifiers; saving participants neither sends invitations nor synchronizes later
contact changes. Load `schedule-contacts` when participant identity needs resolving.

After a create times out, its ID may be unknown. Search definitions using the supplied
title, calendar and location, and inspect candidate dates and fields. Do not repeat
the create unless you establish it did not succeed; if matches remain ambiguous,
report the uncertainty. For an uncertain update or delete, query the known ID and,
for recurring changes, the original occurrence identity before retrying. Do not
delete/recreate a series to recover. Read back records when the response is missing
or does not provide enough evidence to verify the requested change.

For conflict inspection or finding available time, load
[recurrence and planning](references/recurrence.md).
