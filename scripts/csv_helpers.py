"""
CSV Helper Functions
Atomic CSV operations with file locking
"""

import csv
import os
import sys
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import List, Dict, Optional

# Platform-specific imports
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False
    try:
        import msvcrt
        HAS_MSVCRT = True
    except ImportError:
        HAS_MSVCRT = False


@contextmanager
def file_lock(file_obj):
    """
    Cross-platform file locking context manager
    Uses fcntl on Unix, msvcrt on Windows
    """
    if HAS_FCNTL:
        # Unix/Linux/Mac
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)
    elif HAS_MSVCRT:
        # Windows
        msvcrt.locking(file_obj.fileno(), msvcrt.LK_LOCK, 1)
        try:
            yield
        finally:
            msvcrt.locking(file_obj.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        # Fallback (no locking available)
        yield


def atomic_append_csv(filepath: str, row: List[str], create_if_missing: bool = False) -> bool:
    """
    Atomically append a row to CSV file with file locking
    
    Args:
        filepath: Path to CSV file
        row: List of values to append
        create_if_missing: Create file with header if it doesn't exist
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Check if file exists
        file_exists = os.path.exists(filepath)
        
        if not file_exists and not create_if_missing:
            raise FileNotFoundError(f"CSV file not found: {filepath}")
        
        # Open in append mode
        mode = 'a' if file_exists else 'w'
        with open(filepath, mode, newline='') as f:
            with file_lock(f):
                writer = csv.writer(f)
                writer.writerow(row)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
        
        return True
    
    except Exception as e:
        print(f"Error appending to CSV: {e}", file=sys.stderr)
        return False


def read_csv(filepath: str) -> List[Dict[str, str]]:
    """
    Read CSV file and return list of dictionaries
    
    Args:
        filepath: Path to CSV file
    
    Returns:
        List of row dictionaries
    """
    if not os.path.exists(filepath):
        return []
    
    try:
        with open(filepath, 'r', newline='') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        print(f"Error reading CSV: {e}", file=sys.stderr)
        return []


def write_csv(filepath: str, rows: List[Dict[str, str]], fieldnames: List[str]) -> bool:
    """
    Write entire CSV file atomically
    
    Args:
        filepath: Path to CSV file
        rows: List of row dictionaries
        fieldnames: CSV header fields
    
    Returns:
        True if successful
    """
    try:
        # Write to temp file first
        temp_path = filepath + '.tmp'
        
        with open(temp_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            f.flush()
            os.fsync(f.fileno())
        
        # Atomic rename
        os.replace(temp_path, filepath)
        return True
    
    except Exception as e:
        print(f"Error writing CSV: {e}", file=sys.stderr)
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False


def get_utc_timestamp() -> str:
    """
    Get current UTC timestamp in ISO-8601 format
    
    Returns:
        Timestamp string like: 2026-02-04T10:30:45.123Z
    """
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def validate_csv_headers(filepath: str, expected_headers: List[str]) -> bool:
    """
    Validate CSV file has expected headers
    
    Args:
        filepath: Path to CSV file
        expected_headers: List of expected header names
    
    Returns:
        True if headers match exactly
    """
    if not os.path.exists(filepath):
        return False
    
    try:
        with open(filepath, 'r', newline='') as f:
            reader = csv.reader(f)
            actual_headers = next(reader)
            return actual_headers == expected_headers
    except Exception:
        return False


def count_csv_rows(filepath: str, exclude_header: bool = True) -> int:
    """
    Count rows in CSV file
    
    Args:
        filepath: Path to CSV file
        exclude_header: Don't count header row
    
    Returns:
        Number of rows
    """
    if not os.path.exists(filepath):
        return 0
    
    try:
        with open(filepath, 'r', newline='') as f:
            reader = csv.reader(f)
            if exclude_header:
                next(reader, None)  # Skip header
            return sum(1 for _ in reader)
    except Exception:
        return 0


def sanitize_product_id(product_id: str) -> Optional[str]:
    """
    Sanitize product ID for CSV safety
    
    Args:
        product_id: Raw product ID
    
    Returns:
        Sanitized product ID or None if invalid
    """
    if not product_id:
        return None
    
    # Only allow alphanumeric and hyphens
    import re
    if not re.match(r'^[A-Za-z0-9-]+$', product_id):
        return None
    
    return product_id.strip().upper()


def validate_quantity(qty: any) -> Optional[int]:
    """
    Validate and convert quantity to integer
    
    Args:
        qty: Quantity value (str or int)
    
    Returns:
        Valid integer or None
    """
    try:
        qty_int = int(qty)
        if qty_int <= 0 or qty_int > 1000:
            return None
        return qty_int
    except (ValueError, TypeError):
        return None
