"""
Tamper-evident vote ledger.

Every vote row is chained to the row before it, the same idea a blockchain
uses: each row stores the SHA-256 hash of the previous row (PREV_HASH) plus
its own hash (HASH) computed over its own fields + PREV_HASH. Editing or
deleting any past row breaks the chain from that point onward, which
verify_chain() (and src/verify_integrity.py) will detect.

This does not require any blockchain library or network — it's a single
CSV file plus hashlib, which keeps the project dependency-free while giving
a genuine, demonstrable integrity guarantee: edit Votes.csv by hand and
verify_integrity.py will flag exactly which row was tampered with.
"""

import csv
import hashlib
import os

COL_NAMES = ['NAME', 'VOTE', 'DATE', 'TIME', 'PREV_HASH', 'HASH']
GENESIS_HASH = '0' * 64


def _row_hash(name, vote, date, timestamp, prev_hash):
    payload = f"{name}|{vote}|{date}|{timestamp}|{prev_hash}".encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def _get_last_hash(csv_path):
    if not os.path.isfile(csv_path):
        return GENESIS_HASH
    with open(csv_path, 'r', newline='') as f:
        rows = list(csv.reader(f))
    if len(rows) <= 1:
        return GENESIS_HASH
    return rows[-1][-1]  # HASH column of the last row


def append_vote(csv_path, name, vote, date, timestamp):
    """Append one vote, chained to the previous row's hash. Returns the new
    row's hash."""
    exists = os.path.isfile(csv_path)
    prev_hash = _get_last_hash(csv_path)
    row_hash = _row_hash(name, vote, date, timestamp, prev_hash)

    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(COL_NAMES)
        writer.writerow([name, vote, date, timestamp, prev_hash, row_hash])

    return row_hash


def verify_chain(csv_path):
    """Recomputes the hash chain from scratch. Returns (is_valid, bad_row_number_or_None, message)."""
    if not os.path.isfile(csv_path):
        return True, None, "No votes recorded yet."

    with open(csv_path, 'r', newline='') as f:
        rows = list(csv.reader(f))

    if len(rows) <= 1:
        return True, None, "No votes recorded yet."

    expected_prev = GENESIS_HASH
    for i, row in enumerate(rows[1:], start=2):  # 1 = header row
        if len(row) != 6:
            return False, i, f"Row {i}: unexpected column count — file structure was modified."

        name, vote, date, timestamp, prev_hash, stored_hash = row

        if prev_hash != expected_prev:
            return False, i, (
                f"Row {i}: PREV_HASH does not match the previous row's HASH — "
                f"the chain is broken (a row was likely inserted, deleted, or reordered)."
            )

        recomputed = _row_hash(name, vote, date, timestamp, prev_hash)
        if recomputed != stored_hash:
            return False, i, f"Row {i}: stored HASH does not match the recomputed hash — this row's data was edited after the vote was cast."

        expected_prev = stored_hash

    return True, None, f"Chain verified: {len(rows) - 1} vote(s), no tampering detected."
