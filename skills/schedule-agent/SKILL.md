---
name: schedule-agent
description: Route mixed Schedule Agent requests to event, task or contact execution guides.
---
# Schedule Agent

Load the guide for the work; each is independently discoverable.

| Work | Guide |
|---|---|
| Appointments, agenda and recurring events | [schedule-events](../schedule-events/SKILL.md) |
| Actions, deadlines and task completion | [schedule-tasks](../schedule-tasks/SKILL.md) |
| Contact identity and current details | [schedule-contacts](../schedule-contacts/SKILL.md) |

Use the qualified sibling names supplied by Hermes discovery or the bundle banner.
Load references only when the selected workflow needs them.

Use MCP for supported event, task and contact operations in the connected profile.
Use the CLI for additional features such as availability, import/export and backups,
or for an explicitly different profile with `schedule --profile NAME`. Prefer ordinary
CLI flags; JSON input is optional. Do not substitute another profile if it is unavailable.
Workspace skills own local document conventions and authorization workflows.
