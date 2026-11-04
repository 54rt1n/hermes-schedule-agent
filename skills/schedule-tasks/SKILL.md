---
name: schedule-tasks
description: Execute task creation, editing, overdue review, completion and reopening with Schedule Agent, including Org completion-repeaters.
---
# Tasks

Use MCP for supported operations in the connected profile. Use CLI with an explicit
`--profile NAME` for a different profile. Follow the workspace's authorization workflow. Tasks represent
actions and deadlines; appointments belong to the sibling `schedule-events` guide.

## Find and edit work

Query definitions for open, blocked, completed or undated tasks. Agenda occurrences
cannot provide a complete task inventory. Scheduled and deadline dates are distinct;
a task displayed at both dates still has one ID.

For overdue review, use the real local date, inspect TODO and BLOCKED tasks, and
separate overdue, blocked and undated work. `due_before` includes its boundary date;
exclude today when reporting strictly overdue work. Do not reschedule or complete
tasks merely to clear the report.

Resolve an existing task before creating a similar one. Keep unknown dates absent.
Read before patching dates, state or notes, then check the returned task. Cancellation
retains the record; deletion removes it. Use a TODO update to reopen a completed task;
this clears its completion marker. Reopen before another state transition.

## Complete work

1. Retrieve the task by ID; inspect state, dates, repeat rule and previous completion.
   DONE and CANCELLED tasks cannot be completed again directly.
2. Distinguish Org repeaters from imported RRULE tasks. Completing an RRULE-only task
   marks the entire record DONE and removes all future occurrences from the agenda.
   Do not use it to satisfy a request to complete just one occurrence; explain that
   per-occurrence RRULE task completion is unsupported.
3. Use the dedicated completion operation, not a DONE patch. Use the supplied actual
   completion time when known; otherwise the service uses now in the task timezone.
4. Check the returned task. Ordinary tasks become DONE; Org repeaters advance their dates
   and return to TODO with a completion marker. Verify the next dates and report the
   completed action separately from the next obligation.

Org `+` advances each anchor once, possibly leaving it past-dated; `++` advances each
anchor beyond completion; `.+` calculates each next anchor from completion. If both
scheduled and deadline dates exist, check both returned dates rather than assuming
spacing is preserved. Reopening does not reverse this advancement; correct mistaken
dates from known pre-change values, never by completing again.
Advancement into a nonexistent DST time rejects completion without changing the
task. Resolve a valid next date/time explicitly before retrying.

Completion of a repeating task is not idempotent. After an uncertain response, compare
its completion marker and dates with the pre-call state before retrying. If that does
not establish what happened, resolve the uncertainty before another completion.
