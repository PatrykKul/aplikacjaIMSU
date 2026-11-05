"""Administrative commands for course content.

python -m app.modules.content.cli import-course content/courses/percentages [--dry-run]
"""

import argparse
import sys
from pathlib import Path

from app.core.db import SessionLocal
from app.modules.content.importer import format_report, import_package
from app.modules.content.package import PackageError, load_package


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.modules.content.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    import_parser = commands.add_parser(
        "import-course", help="Validate a course package and import it into the database"
    )
    import_parser.add_argument("path", type=Path, help="directory containing course.yaml")
    import_parser.add_argument(
        "--dry-run", action="store_true", help="validate and report changes without saving"
    )
    args = parser.parse_args(argv)

    try:
        package = load_package(args.path)
    except PackageError as error:
        print(f"Invalid course package: {args.path}", file=sys.stderr)
        for message in error.errors:
            print(f"  - {message}", file=sys.stderr)
        return 1

    with SessionLocal() as db:
        report = import_package(db, package, dry_run=args.dry_run)
    print(f"Course {package.course.key}")
    print(format_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
