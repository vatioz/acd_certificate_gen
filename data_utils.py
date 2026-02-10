"""
Data Utilities Module

Handles data processing and formatting utilities.
Includes date formatting, CSV parsing, and gender detection.
"""

from io import StringIO
import csv
from czech_names import MALE_NAMES, FEMALE_NAMES


def format_date_no_leading_zeros(day, month, year):
    """
    Formats date as "D. M. YYYY" (no leading zeros)
    
    Args:
        day: Day as integer
        month: Month as integer
        year: Year as string or integer
        
    Returns:
        Formatted date string
    """
    return f"{day}. {month}. {year}"


def detect_gender_from_name(full_name):
    """
    Detect gender based on Czech first name.
    
    Args:
        full_name: Full name or first name to check
        
    Returns:
        Tuple of (gender, detected_bool):
        - gender: 'male', 'female', or None if not recognized
        - detected_bool: True if gender was auto-detected, False otherwise
    """
    # Extract first name (assume it's the first word)
    first_name = full_name.strip().split()[0] if full_name else ""
    
    # Normalize to uppercase for matching
    first_name_upper = first_name.upper()
    
    if first_name_upper in MALE_NAMES:
        return 'male', True
    elif first_name_upper in FEMALE_NAMES:
        return 'female', True
    else:
        return None, False


def parse_csv_file(csv_file):
    """
    Parses CSV file and returns list of people with their data.
    Expected CSV format: COUNTER,PRE,Surname,Name,POST,DOB (no headers)
    
    Auto-detects gender based on Czech first name database.
    
    Args:
        csv_file: Uploaded CSV file object
        
    Returns:
        Tuple of (people_list, first_counter)
        - people_list: List of dicts with 'name', 'dob', 'gender', 'gender_detected', 'pre', 'post'
        - first_counter: Integer counter from first row, or None
    """
    # Read CSV with UTF-8 encoding and strip BOM if present
    content = csv_file.read().decode('utf-8-sig')  # utf-8-sig automatically removes BOM
    csv_reader = csv.reader(StringIO(content))
    
    imported_people = []
    first_counter = None
    
    for row in csv_reader:
        if len(row) >= 6:
            counter = row[0].strip()
            pre = row[1].strip()
            surname = row[2].strip()
            name = row[3].strip()
            post = row[4].strip()
            dob = row[5].strip()
            
            # Store first counter value
            if first_counter is None:
                try:
                    first_counter = int(counter)
                except ValueError:
                    pass
            
            # Format DOB: DD.MM.YYYY -> D. M. YYYY (no leading zeros)
            parts = dob.split('.')
            if len(parts) == 3:
                day = int(parts[0])
                month = int(parts[1])
                year = parts[2]
                formatted_dob = format_date_no_leading_zeros(day, month, year)
            else:
                formatted_dob = dob  # Fallback to original if parsing fails
            
            # Combine name: "Name Surname"
            full_name = f"{name} {surname}"
            
            # Auto-detect gender from first name
            detected_gender, gender_detected = detect_gender_from_name(name)
            
            imported_people.append({
                'name': full_name,
                'dob': formatted_dob,
                'gender': detected_gender if detected_gender else 'female',  # Default to female if unknown
                'gender_detected': gender_detected,  # Track if auto-detected
                'pre': pre,  # Prefix (e.g., "Dr.")
                'post': post  # Suffix (e.g., "Ph.D.")
            })
    
    return imported_people, first_counter
