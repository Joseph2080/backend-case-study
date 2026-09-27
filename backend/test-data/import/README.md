# Import payloads

- **`minimal-en.json`** — small `CVData` file in this folder for quick tests.
- **Full scenario CVs** — use **`../../examples/`** (`cv-en.json`, `cv-de.json`, `cv-en-varied.json`, `cv-en-other-person.json`).

All import IDs in the JSON are replaced on `POST /cv/import`; they only need to be valid UUIDs in the request body.
