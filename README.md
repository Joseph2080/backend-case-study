# CV workspace backend

A Python backend for importing and editing CVs, with private career details attached
to individual work experiences.

## Setup

Install Python 3.11+ and [uv](https://docs.astral.sh/uv/). Place the supplied `.env`
file in `backend/.env`. It contains the hosted database connection and OpenAI key.

From the repository root:

```sh
cd backend
uv run server.py
```

Open [Swagger UI](http://127.0.0.1:8000/docs) to browse and try the API.
Click **Authorize** and enter `alice-token` or `bob-token`. These are development
accounts with separate data.

The server creates missing tables on startup. Changes to existing tables require
SQL migrations in `backend/src/db/migrations/`.

Access the database directly via external tooling or your agent to perform the migration. (We don't have any tooling in this repo).

## Command line

Run commands from `backend/`. Start the server once to initialize an empty database;
after that, CLI commands work without the server running.

```sh
uv run cli.py cv import examples/cv-en.json
uv run cli.py cv list
uv run cli.py cv duplicate CV_ID

uv run cli.py career-details show CV_ID
uv run cli.py career-details set CV_ID
```

Import and duplicate print the new CV ID. `show` lists the CV's employment entries
and their private details. `set` lets you select an entry by number and enter its
annual salary, currency, weekly hours, and direct reports. All four values are
required. When editing, press Enter to keep an existing value.

Commands default to Alice. Use `--user bob` to switch users:

```sh
uv run cli.py cv list --user bob
```

The examples folder contains four synthetic CVs:

| File | Example |
| --- | --- |
| `cv-en.json` | English CV |
| `cv-de.json` | German version |
| `cv-en-varied.json` | Version with variations |
| `cv-en-other-person.json` | Different person's CV |

Import them under the same account to explore the matching problem. You can also
import your own CVs via PDF:

```sh
uv run cli.py cv import /path/to/cv.pdf
```

An account can contain repeated, translated, or outdated CVs for one person, as well
as CVs for completely different people. `--user` selects the account, not the person
described by a CV.

Currently, career details belong to one employment entry and stay outside the CV
content. The case study asks you to share details across matching experiences for the same person while keeping different people's details separate.

## API routes

Request and response schemas are available in [Swagger UI](http://127.0.0.1:8000/docs).

| Method | Route                          | Purpose                                                 |
| ------ | ------------------------------ | ------------------------------------------------------- |
| GET    | `/ping`                        | Check the database connection                           |
| GET    | `/cv/`                         | List the user's CVs                                     |
| POST   | `/cv/create-empty`             | Create an empty CV with `{"language":"en"}`             |
| POST   | `/cv/import`                   | Import structured CV JSON                               |
| POST   | `/cv/create-from-upload`       | Import a PDF, up to 10MB, as multipart field `file`     |
| GET    | `/cv/{cv_id}`                  | Read a CV                                               |
| PUT    | `/cv/{cv_id}`                  | Replace editable CV content                             |
| DELETE | `/cv/{cv_id}`                  | Delete a CV                                             |
| POST   | `/cv/{cv_id}/duplicate`        | Copy a CV with fresh IDs                                |
| GET    | `/cv/{cv_id}/target-country`   | Read the target country                                 |
| PATCH  | `/cv/{cv_id}/target-country`   | Set the target country                                  |
| GET    | `/career-details/{cv_item_id}` | Read an employment entry's details, or `null` if absent |
| PUT    | `/career-details/{cv_item_id}` | Create or replace all four career-detail fields         |
| DELETE | `/career-details/{cv_item_id}` | Remove the career-details record                        |

For CV updates, keep existing section and item IDs and use `null` for new ones.
Omitted sections and items are removed. Career-detail routes use the employment
item's ID, not the CV's ID.
