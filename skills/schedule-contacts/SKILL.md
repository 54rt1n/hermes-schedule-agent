---
name: schedule-contacts
description: Resolve contact identity and create or update current contact details with Schedule Agent.
---
# Contacts

Use MCP for contact operations in the connected profile; use CLI with an explicit
`--profile NAME` for another profile. Workspace skills own relationship-history files,
backlinks and document conventions; follow those only when the request involves them.

## Resolve identity

Search supplied name/email, then retrieve candidate records by ID. Use supplied
context or verified links to distinguish people. Similar names or shared addresses
do not justify merging. Resolve remaining ambiguity before changing a candidate.
A unique-email conflict calls for inspecting the existing contact, not inventing an
alternate address or creating a duplicate.

## Save current details

Reuse a verified ID for corrections and leave unknown values absent. Notes updates
replace the whole field: read the latest value, preserve unrelated details and
backlinks, then patch the intended complete value. Organization or preferred contact
method can live in notes when supplied; they are not structured query fields.
Check the returned contact against the requested changes; read it again if the
response is missing or incomplete.

Changing a contact email does not update existing event participant email identifiers.
If propagation is requested, use `schedule-events` to inspect and update the affected
series. Saving a contact or participant does not send a message or invitation.

After an uncertain response, query before retrying a create or update. If contact
creation succeeded but a requested document/link step failed, retain the contact ID
and resume only the failed step under the workspace guide. Deleting a contact does
not prove that linked documents or event participant addresses were removed.
