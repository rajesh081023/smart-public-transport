"""Change the seeded administrator password before exposing a deployment."""

from getpass import getpass
import sys

from werkzeug.security import generate_password_hash

from db import query_db


def main():
    password = getpass("New administrator password (12+ characters): ")
    if len(password) < 12:
        print("Password must be at least 12 characters.", file=sys.stderr)
        return 1

    confirmation = getpass("Confirm password: ")
    if password != confirmation:
        print("Passwords do not match.", file=sys.stderr)
        return 1

    result = query_db(
        "UPDATE users SET password_hash = %s WHERE email = %s AND role = 'admin'",
        (generate_password_hash(password), "admin@smartmobility.com"),
        commit=True,
    )
    if result["row_count"] != 1:
        print("The seeded administrator account was not found.", file=sys.stderr)
        return 1

    print("Administrator password updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
