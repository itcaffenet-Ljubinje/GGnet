"""
Sign-in from the server's shell, for when the web UI cannot help:

  python -m app.cli setup-code              the code that creates the first admin
  python -m app.cli reset-password USER     a new password (asked twice); signs USER out
  python -m app.cli create-admin USER       an extra admin, e.g. when every admin is locked out

The installer runs them with GGNET_CONFIG set (ggnet-admin wraps this).
"""

from __future__ import annotations

import argparse
import getpass
import sys

from sqlalchemy import select

from app.db.models import User, UserRole
from app.db.session import get_sessionmaker
from app.services import auth


def _password() -> str:
    first = getpass.getpass("New password: ")
    if first != getpass.getpass("Again: "):
        sys.exit("The passwords differ.")
    if len(first) < auth.PASSWORD_MIN:
        sys.exit(f"At least {auth.PASSWORD_MIN} characters.")
    return first


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ggnet-admin", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("setup-code")
    reset = sub.add_parser("reset-password")
    reset.add_argument("username")
    create = sub.add_parser("create-admin")
    create.add_argument("username")
    args = parser.parse_args(argv)

    with get_sessionmaker()() as db:
        if args.command == "setup-code":
            code = auth.setup_code(db)
            if code is None:
                print("Users already exist: sign in, or use reset-password / create-admin.")
                return 1
            print(code)
            return 0
        username = args.username.strip().lower()
        user = db.scalar(select(User).where(User.username == username))
        if args.command == "reset-password":
            if user is None:
                sys.exit(f"No user '{username}'.")
            user.password_hash = auth.hash_password(_password())
            user.disabled = False
            auth.end_sessions_of(db, user.id)
            db.commit()
            print(f"Password of '{username}' changed.")
            return 0
        if user is not None:
            sys.exit(f"User '{username}' already exists; use reset-password.")
        if not auth.USERNAME_RE.match(username):
            sys.exit("Username: 2-32 of a-z, 0-9, '.', '_', '-'.")
        db.add(User(username=username, password_hash=auth.hash_password(_password()), role=UserRole.ADMIN))
        db.commit()
        auth.setup_code(db)          # the first admin exists now: drop an unused setup code
        print(f"Admin '{username}' created.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
