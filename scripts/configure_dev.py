"""Initialize missing local signing secret without displaying it or replacing existing values."""

import secrets
from pathlib import Path

from dotenv import dotenv_values, set_key


def main() -> None:
    path = Path(__file__).resolve().parents[1] / ".env"
    if not path.exists():
        raise SystemExit("Create .env from .env.example first")
    values = dotenv_values(path)
    if not values.get("JWT_SECRET"):
        set_key(str(path), "JWT_SECRET", secrets.token_urlsafe(48))
        print("JWT_SECRET generated in .env (value not displayed).")
    else:
        print("Existing JWT_SECRET preserved.")


if __name__ == "__main__":
    main()
