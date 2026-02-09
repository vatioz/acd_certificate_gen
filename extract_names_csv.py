"""
Extract Czech names from CSV file and generate czech_names.py module.
Source: Czech Statistical Office (ČSÚ) OpenData
"""
import csv


def extract_names_from_csv(csv_file):
    """
    Extract names from CSV file with columns: DRUH_JMENA, JMENO
    
    Args:
        csv_file: Path to CSV file
        
    Returns:
        tuple: (male_names_set, female_names_set)
    """
    male_names = set()
    female_names = set()
    neutral_count = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            gender_category = row['DRUH_JMENA'].strip().upper()
            name = row['JMENO'].strip()
            
            if not name:
                continue
            
            if gender_category == 'MUZ':
                male_names.add(name)
            elif gender_category == 'ZENA':
                female_names.add(name)
            else:
                # Skip neutral names - user will manually assign them
                neutral_count += 1
    
    print(f"Extracted {len(male_names)} male names")
    print(f"Extracted {len(female_names)} female names")
    print(f"Skipped {neutral_count} neutral names")
    
    return male_names, female_names


def generate_python_module(male_names, female_names, output_file='czech_names.py'):
    """Generate Python module with name sets."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('"""\n')
        f.write('Czech first names database from Czech Statistical Office (ČSÚ)\n')
        f.write('Source: OpenData - seznam jmen\n')
        f.write('Generated automatically - do not edit manually\n')
        f.write('"""\n\n')
        
        # Male names
        f.write('MALE_NAMES = {\n')
        for name in sorted(male_names):
            f.write(f'    "{name}",\n')
        f.write('}\n\n')
        
        # Female names
        f.write('FEMALE_NAMES = {\n')
        for name in sorted(female_names):
            f.write(f'    "{name}",\n')
        f.write('}\n')
    
    print(f"\nGenerated {output_file} successfully!")


if __name__ == '__main__':
    # CSV file from Czech Statistical Office
    csv_file = 'OpenData_-_seznam_jmen_k_2026-01-31_v2.csv'
    
    print(f"Processing {csv_file}...")
    male_names, female_names = extract_names_from_csv(csv_file)
    
    generate_python_module(male_names, female_names)
    
    print(f"\nTotal names: {len(male_names) + len(female_names)}")
