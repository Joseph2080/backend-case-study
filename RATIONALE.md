# Career details across CVs — rationale and notes

## The problem (short version)

Users often upload several CVs for the same person: English and German versions, older drafts, or versions tailored for a job. Private career details (salary, hours, direct reports) should only need to be entered once per role.

The same account can also hold CVs for different people. Those careers must stay separate—even if they worked at the same company or had similar job titles.

In the original backend, details were tied to one employment line on one CV. A new upload created new lines, so the details disappeared and had to be typed again.

## What has been implemented

Private details sit on a shared **work experience** record inside the account. Matching employment lines from different CVs point at that same record.

- `work_experiences` — one row per real-world role for a person in this account  
- `cv_items.work_experience_id` — employment lines link to that shared role  
- `career_details` — salary, currency, hours, and reports live on the shared role  

The API is unchanged: clients still call `/career-details/{cv_item_id}`. The service resolves that item to the shared work experience and reads or writes the details there.

Updating details through any matching CV entry makes the same values available on the others.

Migration: `backend/src/db/migrations/003_share_career_details.sql`.

## How matching works

Jobs are matched **inside the same account** only, in two steps:

1. **Same person?**  
   Prefer email. If there is no email, use first name (first word), last name, and date of birth. That way “Maya” and “Maya Alexandra” can still line up when the email matches or when name + DOB match.

2. **Same role?** (only if step 1 says yes)  
   Same employer after cleaning (e.g. “Northstar AG” → “northstar”), and dates that roughly line up (start years close; both current, or end years close).

Identical job titles are **not** required. That is on purpose: German titles and tailored English titles should still count as the same role. Different jobs at the same company stay apart because their dates don’t overlap (e.g. manager from 2024 vs engineer 2020–2023).

**Important trap:** Mia and Maya both have “Engineering Manager” at Northstar from 2024. They must not share details. Person matching (different emails) stops that before employer or dates are compared.

Matching runs after import, upload, duplicate, and CV update, and again when career details are fetched or saved—so CVs already in the database get linked without re-uploading.

## Why this approach

| Option | Why it was not chosen |
| --- | --- |
| Copy details onto every new CV item | Edits drift apart; no single place that owns the truth |
| Match only on job title | Breaks on translation; wrongly links Mia and Maya |
| Ask an LLM on every import | Slower, costlier, harder to test; not needed for these cases |
| Full “person profile” product + merge UI | Good later; too heavy for this timebox with a fixed API |

Priorities for this change:

- Different people never share details  
- Same role across CVs shares one set of details  
- Existing API and CLI keep working  
- Clear Postgres schema and a real migration  
- Matching that is easy to explain and unit-test without calling OpenAI  

Simple rules fit best here: fast, predictable, and enough for the example CVs once person is matched first, then employer and dates.

## Limitations

- Two real concurrent jobs at the same company with almost the same dates could be merged by mistake (titles are not forced to match).  
- One “current” job and one “ended” job at the same company will not match—that avoids collapsing a promotion into one row by accident.  
- Weak person signals (no email, vague names, no DOB) make person matching harder.  
- Rematching on every career-details read is fine at this size; a bigger product would rematch only what changed.  
- Empty work-experience rows with no remaining CV lines are not cleaned up yet.  
- Existing databases need the SQL migration; creating tables on startup alone will not fix old schemas.

## How to check it

From `backend/`:

```sh
uv run cli.py cv import examples/cv-en.json
uv run cli.py cv import examples/cv-de.json
uv run cli.py cv import examples/cv-en-varied.json
uv run cli.py cv import examples/cv-en-other-person.json

uv run cli.py career-details set <MAYA_CV_ID>
uv run cli.py career-details show <OTHER_MAYA_CV_ID>   # same numbers on the matching role
uv run cli.py career-details show <MIA_CV_ID>          # must not show Maya’s numbers
```

In Swagger, use the employment item `id` from `GET /cv/{cv_id}` (under `employment`), not the CV id.  
`GET /career-details/...` returning `null` means “nothing saved yet,” not a failure.

```sh
uv run pytest tests/test_career_details_matching.py -q
uv run pyright
```

## Further considerations

1. **Clear “person” objects** in an account, with a way for users to confirm or split automatic matches.  
2. **Optional LLM help** when employer names or titles are messy—keep the rules as the default, use the model when confidence is low.  
3. **“Same role” / “different role” controls** so users can fix bad merges without a database change.  
4. **Smarter signals** — city as a soft hint, overlap of date ranges, maybe description similarity.  
5. **Faster rematch** — only the people or CVs that changed; background jobs for large accounts.  
6. **Cleanup and audit** — remove unused work experiences; log changes to salary-related fields.  
7. **Smarter duplicates** — when duplicating a CV, carry links from the parent, then rematch to double-check.

## Bottom line

Private career details belong to the **role a person held**, not to one line on one PDF or JSON upload. Matching employment lines link to one shared record. Matching is **person first**, then **employer and dates**. The API stays the same, with room later for smarter matching and user overrides.
