import os
from urllib.parse import urlparse

# These tests do not call OpenAI; a placeholder satisfies startup configuration.
os.environ["OPENAI_API_KEY"] = "test-key"

test_db_url = os.environ.get("TEST_DB_URL")
if test_db_url:
    parsed = urlparse(test_db_url)
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"} or not parsed.path.endswith("_test"):
        raise ValueError("TEST_DB_URL must point to a local disposable database whose name ends in _test")
    os.environ["DB_URL"] = test_db_url
