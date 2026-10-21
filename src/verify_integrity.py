"""Run this any time to check whether Votes.csv has been tampered with.

Usage:
    python src/verify_integrity.py
    python src/verify_integrity.py --csv path/to/Votes.csv

Try it live in a demo: open Votes.csv, hand-edit one vote's party, save,
then re-run this script — it will point at the exact row that no longer
matches its hash.
"""

import argparse
import os
import sys

sys.path.append(os.path.dirname(__file__))
from ledger import verify_chain  # noqa: E402

DEFAULT_CSV = os.path.join(os.path.dirname(__file__), '..', 'Votes.csv')


def main():
    parser = argparse.ArgumentParser(description="Verify the tamper-evident vote ledger.")
    parser.add_argument('--csv', default=DEFAULT_CSV, help='Path to Votes.csv')
    args = parser.parse_args()

    ok, bad_row, message = verify_chain(args.csv)
    print("Integrity check:", "VALID" if ok else "TAMPERED")
    print(message)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
