# Hermes Schedule Agent

Events, tasks, contacts, and an agenda for Hermes.

This plugin connects Hermes to Schedule Agent's local SQLite database. Ask Hermes
to check your schedule, move an appointment, create a task, or look up a contact.
Hermes starts the MCP server as a child process. The CLI reads and writes the same
database and handles Org/ICS imports, exports, and backups.

[Features](#features) · [Install](#install) · [Usage](#usage) ·
[Org and ICS files](#org-and-ics-files) · [Tools](#tools) · [Skills](#skills) ·
[Storage](#storage) · [Troubleshooting](#troubleshooting) ·
[Development](#development) · [License](#license)

## Features

- **Agenda.** Read events and tasks for a day, week, or date range. Find undated
  and completed tasks separately.
- **Appointments.** Create timed meetings, appointments without an end time,
  all-day events, and anniversaries. Move or cancel one occurrence of a timed
  recurring event, change future occurrences, or edit the whole series.
- **Tasks.** Set scheduled dates and deadlines, mark tasks blocked or complete,
  and reopen them. Completing tasks with Org repeaters advances their dates.
- **Contacts.** Store names, email addresses, phone numbers, and notes. Use email
  identifiers when adding participants to timed events.
- **Org and ICS.** Load existing schedules and export either format through the CLI.
  Imports preview changes before saving them.
- **Separate profiles.** Each Hermes profile has its own database and settings.
  CLI commands select a profile explicitly with `--profile NAME`.

## Install

You need **Hermes**, **Python 3.11–3.13**, **Git**, and internet access during setup.
The installer downloads Schedule Agent from GitHub at the commit pinned in
[runtime-requirements.txt](runtime-requirements.txt). No local Schedule Agent
checkout is required.

### Install the plugin

The commands below use Python 3.12 and the default Hermes profile:

```bash
hermes --profile default plugins install 54rt1n/hermes-schedule-agent --no-enable
hermes profile show default
```

The plugin is installed under the profile's `plugins/hermes-schedule-agent/`
directory. Use the absolute **Path** printed by `profile show` below:

```bash
PROFILE_HOME=/absolute/path/from/profile/show
PLUGIN_DIR="$PROFILE_HOME/plugins/hermes-schedule-agent"

python3.12 "$PLUGIN_DIR/scripts/setup_runtime.py"
hermes --profile default plugins validate "$PLUGIN_DIR"
hermes --profile default plugins enable hermes-schedule-agent
```

Setup creates the plugin's `.venv/` and installs core, CLI, and MCP from the pinned
GitHub revision, plus the Hermes profile adapter. It does not replace an existing
environment. These are shell examples for Linux and macOS. Use a new Hermes session
after enabling the plugin. For another profile, use that profile's name and directory.

### Initialize the schedule

Put the plugin's CLI on your PATH:

```bash
export PATH="$PLUGIN_DIR/.venv/bin:$PATH"
schedule --profile default init --timezone America/Chicago
schedule --profile default status
```

Choose your timezone. For an existing calendar, change it with
`schedule --profile default config set --timezone America/Chicago`.
A running MCP server reads changed settings on its next start.

## Usage

In a Hermes session using the configured profile, try requests such as:

- “Show my agenda for this week.”
- “Move Friday's planning meeting to 11 a.m.”
- “Create a task to send the proposal, due Tuesday.”
- “Mark the proposal task complete.”
- “Find Alex's email address.”

The bundled skills guide Hermes through looking up records before changing them,
choosing recurrence scope, and checking saved results. Saving a contact or event
participant does not send a message or invitation.

The CLI works with the same profile database:

Its agenda is formatted for people, with weekday/date headings and local am/pm
times. `--details` adds readable notes and participants; use the global `--json`
flag for structured records and IDs.

```bash
schedule --profile default agenda --week --details
schedule --profile default tasks list --state TODO
schedule --profile default tasks create --title "Send proposal" --deadline 2030-01-08
schedule --profile default contacts create --name Alex --email alex@example.com
```

Use the IDs returned by create/list commands for updates and completion:

```bash
schedule --profile default events update EVENT-ID --location "Main office"
schedule --profile default tasks update TASK-ID --state BLOCKED
schedule --profile default tasks complete TASK-ID
schedule --profile default contacts update CONTACT-ID --clear phone
```

Replace the example date and IDs with your own. Global options such as `--profile`
and `--json` go before the command. Create/update commands use field flags;
optional `--data` accepts JSON, `@file.json`, or `-` for stdin. Do not combine
`--data` with field flags. Use `schedule COMMAND --help` for the available flags.

## Org and ICS files

Import and export through the CLI. Both formats are supported; Org is the default.
Imports preview changes unless you add `--apply`:

```bash
schedule --profile default import calendar.org
schedule --profile default import calendar.org --apply

schedule --profile default import calendar.ics --format ics
schedule --profile default import calendar.ics --format ics --apply
```

To load a directory of Org files, add `--recursive`:

```bash
schedule --profile default import ./org-files --recursive
schedule --profile default import ./org-files --recursive --apply
```

Export to a new file:

```bash
schedule --profile default export --format org --output exported.org
schedule --profile default export --format ics --output exported.ics
```

Imports never rewrite the source documents, and exports refuse existing output
files. Keep Org IDs or ICS UIDs so later imports can match existing records.
Imports report unsupported entries; `--on-unsupported skip` skips them explicitly.
Import is a command you run, not automatic synchronization with your files.

Use a SQLite backup to preserve all stored data and settings:

```bash
schedule --profile default backup create /path/to/new-backup
schedule --profile default backup inspect /path/to/new-backup
```

See the [Schedule Agent README](https://github.com/54rt1n/schedule-agent#readme) and
[CLI guide](https://github.com/54rt1n/schedule-agent/blob/master/docs/cli.md) for saved
import plans, supported Org forms, recurrence limits, occurrence exports, and restore commands.

## Tools

The plugin exposes twelve MCP tools:

| Tools | Purpose |
| --- | --- |
| `query_schedule` | Read stored events and tasks, or an agenda for a date range |
| `create_event`, `update_event`, `delete_event` | Create, change, and remove appointments |
| `create_task`, `update_task`, `complete_task`, `delete_task` | Create, change, complete, and remove tasks |
| `query_contacts`, `create_contact`, `update_contact`, `delete_contact` | Read and maintain contact details |

`query_schedule` uses `view=definitions` for stored records, including undated and
completed tasks. Use `view=occurrences` for an agenda. A task can appear on both its
scheduled date and deadline with the same ID.

Point, all-day, and anniversary events support whole-series changes. Timed events
also support changes to one occurrence or future occurrences. Task completion has
its own tool. Completing an RRULE-only task completes the whole record; completing
one occurrence of such a task is currently unsupported.

Import/export, availability reports, and database administration are CLI commands.
CLI and MCP use the same application contracts for their shared operations.

## Skills

The plugin bundles a routing skill and three execution guides:

| Skill | Covers |
| --- | --- |
| [schedule-agent](skills/schedule-agent/SKILL.md) | Choose the event, task, or contact guide |
| [schedule-events](skills/schedule-events/SKILL.md) | Read agendas and create or change appointments |
| [schedule-tasks](skills/schedule-tasks/SKILL.md) | Find work, complete tasks, advance repeaters, and reopen tasks |
| [schedule-contacts](skills/schedule-contacts/SKILL.md) | Resolve people and maintain contact details |

Each skill can be discovered separately. The event guide links to a
[recurrence reference](skills/schedule-events/references/recurrence.md) when needed.
Workspace-specific skills can define document paths, relationship history, and
rules for when an agent may make changes.

## Storage

Hermes supplies a profile-specific `PLUGIN_DATA` directory to the MCP child.
That directory contains `schedule-agent.db` and `config.json`. The CLI's profile
adapter asks Hermes to resolve the profile and selects the same directory:

```bash
schedule --profile default status
schedule profiles show default
```

Keep the installation name `hermes-schedule-agent`: the CLI adapter uses that name
to find the plugin's data directory. A custom installation name requires explicit
`--data-dir PATH` for CLI access. The adapter reports an error if Hermes cannot
resolve the profile; it does not substitute another profile.

The plugin environment is separate from Hermes' Python environment. CLI commands
run directly; MCP runs as a Hermes-managed child. No separately deployed service
or model API key is needed for these scheduling operations.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| Plugin is not listed | Check the installation in the selected profile's `plugins/` directory and run `hermes plugins list` for that profile. |
| Tools are unavailable | Enable the plugin in the selected profile and open a new session. Check Hermes' MCP startup logs. |
| Runtime is missing | Run `scripts/setup_runtime.py` with Python 3.11–3.13 from the installed plugin directory. |
| Setup refuses `.venv` | Inspect the existing environment. Move it aside before intentionally rebuilding it. |
| `schedule` is not found | Add the plugin's `.venv/bin` to PATH or use its absolute `schedule` path. |
| CLI and agent show different schedules | Check the selected profile and `schedule --profile NAME status`; confirm the installation name is `hermes-schedule-agent`. |
| Profile lookup fails | Check `hermes profile show NAME` and that `hermes` is on PATH. |

## Development

Local source installs are optional. To develop against a Schedule Agent checkout,
run this from a plugin checkout without an existing `.venv/`:

```bash
python3.12 scripts/setup_runtime.py --editable-source /path/to/schedule-agent
```

This installs the three Schedule Agent packages and the profile adapter editable.
Keep both development checkouts at their installed paths. `--source PATH` builds
an installed copy of local Schedule Agent source instead. Normal installation uses
the GitHub pins in `runtime-requirements.txt`; update those three pins together when
releasing against a newer Schedule Agent commit.

Keep `plugin.json` and `mcp.json` as the plugin manifests. Adding `plugin.yaml`
changes which plugin format Hermes discovers. The plugin installs core, CLI, and
MCP; the separate HTTP, A2A, and NLP packages are not needed here.

Run the smoke test from the plugin checkout:

```bash
.venv/bin/python scripts/smoke.py
```

It checks real MCP discovery, agenda reads, writes, and persistence across child
process restarts using a temporary calendar. Run Schedule Agent's tests from its
checkout with `scripts/run_tests.sh` and that project's test environment.

## License

GNU Affero General Public License v3 or later — see [LICENSE](LICENSE).

Martin Bukowski · [54rt1n](https://github.com/54rt1n)
