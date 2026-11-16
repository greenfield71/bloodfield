#!/usr/bin/env python3
"""SQLite Container Inspector & Reassembler for CTF Forensics.

When challenge payloads, memory dumps, or CT scans are packaged into a SQLite DB
(e.g., L3akCTF 'You Scanned WHAT?!?' and 'You Scanned HOW?!?!'):
- Enumerate tables and column schemas
- Extract numeric 2-D arrays (sinograms) stored across tables
- Reassemble binary blobs / file streams split across rows

Usage:
    python3 -I sqlite_container.py dump-tables database.db
    python3 -I sqlite_container.py extract-blobs database.db table_name blob_column out.bin
    python3 -I sqlite_container.py extract-matrix database.db table_name out.npy
    python3 -I sqlite_container.py --test
"""
import sqlite3
import sys
import numpy as np


def list_tables(db_path):
    """Return a list of all table names in the database."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [r[0] for r in cur.fetchall()]
    conn.close()
    return tables


def table_info(db_path, table_name):
    """Return column info: [(cid, name, type, notnull, dflt_value, pk), ...]."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info(\"{table_name}\");")
    cols = cur.fetchall()
    cur.execute(f"SELECT COUNT(*) FROM \"{table_name}\";")
    count = cur.fetchone()[0]
    conn.close()
    return cols, count


def extract_table_matrix(db_path, table_name):
    """Read all numeric rows of a table into a 2D float NumPy array."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM \"{table_name}\";")
    rows = cur.fetchall()
    conn.close()
    return np.array(rows, dtype=float)


def extract_blob_stream(db_path, table_name, blob_column, order_by=None):
    """Concatenate binary blob rows from a table into a single bytes object."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    query = f"SELECT \"{blob_column}\" FROM \"{table_name}\""
    if order_by:
        query += f" ORDER BY \"{order_by}\""
    cur.execute(query)
    chunks = [r[0] for r in cur.fetchall() if r[0] is not None]
    conn.close()
    return b"".join(chunks)


def _self_test():
    # Test in-memory SQLite container
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()

    # Create numeric slice tables (like sinogram slices in medical CT CTFs)
    for i in range(3):
        tname = f"slice_{i:03d}"
        cur.execute(f"CREATE TABLE {tname} (c0 REAL, c1 REAL, c2 REAL);")
        for row in range(4):
            cur.execute(f"INSERT INTO {tname} VALUES (?, ?, ?);", (i * 1.0, row * 1.0, (i + row) * 1.0))

    # Create blob table
    cur.execute("CREATE TABLE file_chunks (id INT, chunk BLOB);")
    cur.execute("INSERT INTO file_chunks VALUES (1, ?);", (b"CTF{sqlite_",))
    cur.execute("INSERT INTO file_chunks VALUES (2, ?);", (b"container_reconstructed}",))
    conn.commit()

    # Verify tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [r[0] for r in cur.fetchall()]
    assert len(tables) == 4, f"Unexpected table count: {len(tables)}"

    # Verify blob reassembly
    cur.execute("SELECT chunk FROM file_chunks ORDER BY id;")
    stream = b"".join(r[0] for r in cur.fetchall())
    assert stream == b"CTF{sqlite_container_reconstructed}", f"Blob mismatch: {stream}"

    # Verify numeric table extraction
    cur.execute("SELECT * FROM slice_001;")
    mat = np.array(cur.fetchall(), dtype=float)
    assert mat.shape == (4, 3), f"Shape mismatch: {mat.shape}"
    assert mat[2, 1] == 2.0

    conn.close()
    print("[ok] sqlite_container self-test passed: tables, matrices, and blob reassembly verified")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        _self_test()
    elif len(sys.argv) > 2 and sys.argv[1] == "dump-tables":
        db = sys.argv[2]
        tables = list_tables(db)
        print(f"Found {len(tables)} tables:")
        for t in tables[:50]:
            _, count = table_info(db, t)
            print(f"  {t} ({count} rows)")
        if len(tables) > 50:
            print(f"  ... and {len(tables) - 50} more tables")
    elif len(sys.argv) > 4 and sys.argv[1] == "extract-blobs":
        db, tbl, col, out = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
        data = extract_blob_stream(db, tbl, col)
        with open(out, "wb") as f:
            f.write(data)
        print(f"Wrote {len(data)} bytes to {out}")
    elif len(sys.argv) > 3 and sys.argv[1] == "extract-matrix":
        db, tbl, out = sys.argv[2], sys.argv[3], sys.argv[4]
        mat = extract_table_matrix(db, tbl)
        np.save(out, mat)
        print(f"Saved matrix shape {mat.shape} to {out}")
    else:
        print(__doc__)
