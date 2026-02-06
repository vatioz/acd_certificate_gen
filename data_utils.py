"""
Data Utilities Module

Handles data processing and formatting utilities.
Includes date formatting and CSV parsing functions.
"""

from io import StringIO
import csv


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


def parse_csv_file(csv_file):
    """
    Parses CSV file and returns list of people with their data.
    Expected CSV format: COUNTER,Surname,Name,DOB (no headers)
    
    Args:
        csv_file: Uploaded CSV file object
        
    Returns:
        Tuple of (people_list, first_counter)
        - people_list: List of dicts with 'name', 'dob', 'gender'
        - first_counter: Integer counter from first row, or None
    """
    # Read CSV with UTF-8 encoding
    content = csv_file.read().decode('utf-8')
    csv_reader = csv.reader(StringIO(content))
    
    imported_people = []
    first_counter = None
    
    for row in csv_reader:
        if len(row) >= 4:
            counter = row[0].strip()
            surname = row[1].strip()
            name = row[2].strip()
            dob = row[3].strip()
            
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
            
            imported_people.append({
                'name': full_name,
                'dob': formatted_dob,
                'gender': 'female'  # Default to female
            })
    
    return imported_people, first_counter
