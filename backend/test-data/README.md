# API test data

Use these JSON bodies with [Swagger UI](http://127.0.0.1:8000/docs). Authorize with **`alice-token`** or **`bob-token`**.

## Existing full CV imports

The repo already ships rich import payloads under **`../examples/`**:

| File | Use case |
| --- | --- |
| `cv-en.json` | Baseline English CV (Maya) |
| `cv-de.json` | German translation of the same person |
| `cv-en-varied.json` | Wording/date variations + extra job |
| `cv-en-other-person.json` | Different person (Mia) — career-details matching trap |

`POST /cv/import` accepts **`CVData`** (same shape as those files). Import always assigns **new** CV, section, and item IDs.

CLI: `uv run cli.py cv import examples/cv-en.json`

## This folder

| Path | Endpoint | Notes |
| --- | --- | --- |
| `import/minimal-en.json` | `POST /cv/import` | Small CV for quick lifecycle runs |
| `requests/create-empty.en.json` | `POST /cv/create-empty` | Empty CV shell |
| `requests/target-country.patch.json` | `PATCH /cv/{cv_id}/target-country` | Body only (trimmed spaces are normalized) |
| `requests/career-details.put.json` | `PUT /career-details/{cv_item_id}` | Replace `{cv_item_id}` with an employment item UUID from `GET /cv/{cv_id}` |
| `fragments/employment-item-new.json` | (part of `PUT /cv/{cv_id}`) | Append to `employment` array; set `"id": null` |
| `fragments/custom-section-new.json` | (part of `PUT /cv/{cv_id}`) | Append to `sections`; set `"id": null` |

## Suggested lifecycle

1. **Import** — `POST /cv/import` with `import/minimal-en.json` or any `examples/*.json`. Save `id` from the response.
2. **Read** — `GET /cv/{cv_id}` — copy the JSON; this is the base for updates (IDs must match).
3. **Update CV** — Edit the copy (rename, change employment text, append fragments with `"id": null`). `PUT /cv/{cv_id}` with body `id` equal to the path `cv_id`. Omitted sections/items are **deleted**.
4. **Duplicate** — `POST /cv/{cv_id}/duplicate` (no body); new IDs everywhere.
5. **Target country** — `PATCH /cv/{cv_id}/target-country` with `requests/target-country.patch.json`.
6. **Career details** — Pick an employment item `id` from the CV JSON. `PUT /career-details/{cv_item_id}` with `requests/career-details.put.json`. `GET` the same path to verify.
7. **Delete** — `DELETE /cv/{cv_id}` or `DELETE /career-details/{cv_item_id}`.

For `PUT /cv/{cv_id}`, do **not** reuse IDs from another CV or from the pre-import file; always start from a fresh `GET` response after import or duplicate.
