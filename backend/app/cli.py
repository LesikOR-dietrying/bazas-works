import argparse
from getpass import getpass

from pydantic import SecretStr
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import create_database_engine
from app.core.errors import DomainError
from app.modules.users.schemas import UserCreate
from app.modules.users.service import bootstrap_admin
from app.seed import seed_demo


def main() -> None:
    parser = argparse.ArgumentParser(description="BAZA administration")
    parser.add_argument("command", choices=["create-admin", "seed-demo"])
    parser.add_argument("--name", help="Administrator full name")
    parser.add_argument("--username", help="Administrator username")
    parser.add_argument("--email", help="Optional administrator contact email")
    arguments = parser.parse_args()
    settings = get_settings()
    if arguments.command == "create-admin":
        name = arguments.name or input("Full name: ").strip()
        username = arguments.username or input("Username: ").strip()
        email = arguments.email
        password = getpass("Password (at least 12 characters): ")
        if password != getpass("Repeat password: "):
            raise SystemExit("Passwords do not match")
        data = UserCreate(
            full_name=name, username=username, email=email, password=SecretStr(password)
        )
        engine = create_database_engine(settings)
        try:
            with Session(engine) as session:
                bootstrap_admin(session, data)
            print("Administrator created. Sign in through the web interface.")
        except DomainError as error:
            raise SystemExit(error.message) from None
        finally:
            engine.dispose()
    elif arguments.command == "seed-demo":
        engine = create_database_engine(settings)
        try:
            with Session(engine) as session:
                counts = seed_demo(session, settings)
            print(
                "Development demo data is ready: "
                + ", ".join(f"{name}={count}" for name, count in counts.items())
            )
        except DomainError as error:
            raise SystemExit(error.message) from None
        finally:
            engine.dispose()


if __name__ == "__main__":
    main()
