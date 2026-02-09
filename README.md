# Certificate Generator

A Streamlit web application for generating personalized certificates from Word document templates. Create multiple certificates in a single document with full formatting preservation.

## Features

- Upload .docx certificate templates with full style preservation
- Add multiple certificate holders to a list
- **CSV bulk import** with COUNTER,Surname,Name,DOB format
- **Automatic gender detection** from Czech first names database (7,164 names from Ministry of Interior)
- ⚠️ **Visual indicators** for unrecognized names requiring manual verification
- 🔵🔴 **Color-coded names** for easy gender review (blue for male, pink for female)
- **Gender selection with automatic verb conjugation (Czech)**
- **Certificate numbering with auto-increment counter**
- **Automatic year insertion**
- Replace placeholders with personalized data
- Generate all certificates in a single document (one certificate per page)
- Preserves all template formatting: fonts, styles, watermarks, headings
- Czech date format support (D. M. YYYY - no leading zeros)
- Test data generator for quick testing
- Download single file containing all certificates

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
streamlit run app.py
```

2. Open your browser at `http://localhost:8501`

3. Upload a certificate template (.docx) with placeholders:
   - `[NAME]` - for the certificate holder's full name
   - `[DOB]` - for the date of birth

4. Add certificate holders:
   - **Option A: Manual Entry** - Enter Full Name and Date of Birth
   - **Option B: CSV Upload** - Upload CSV file with COUNTER,Surname,Name,DOB format
   - Use "Add 8 Test People" button for quick testing

5. Review the list of certificate holders:
   - Names with ⚠️ indicator require gender verification
   - Toggle gender with 👩 Žena / 👨 Muž buttons
   - Remove individuals if needed using the delete button

6. Click "Generate All Certificates"

7. Download the single .docx file containing all certificates

## Template Placeholders

### Basic Placeholders
- `[NAME]` - Will be replaced with the full name
- `[DOB]` - Will be replaced with the date of birth in DD. MM. YYYY format
- `[COUNTER]` - Certificate number (auto-increments for each person in batch)
- `[YEAR]` - Current year (automatic)

### Gender-Dependent Placeholders (Czech)

These placeholders automatically conjugate based on the person's gender:

- `[ZÍSKAL/A]` → získal (male) / získala (female)
- `[ABSOLVOVAL/A]` → absolvoval / absolvovala
- `[NAROZEN/A]` → narozen / narozena

**Default gender:** Female (Žena)

## CSV Format

CSV file should have **no headers** and follow this format:
```
COUNTER,Surname,Name,DOB
15,Novák,Jan,01.01.1990
16,Dvořáková,Marie,15.03.1985
```

**Gender Auto-Detection:**
- The app automatically detects gender from Czech first names (7,164 names from Ministry of Interior)
- Unrecognized names show ⚠️ indicator - please verify manually
- Names default to female if not recognized
- You can always toggle gender with the 👩 / 👨 buttons

## Updating Name Database

The Czech names database is sourced from the Ministry of Interior's official registry:
- **Source:** https://mv.gov.cz/clanek/seznam-rodove-neutralnich-jmen.aspx
- **Current file:** `OpenData_-_seznam_jmen_k_2026-01-31_v2.csv`

**To update the name database:**

1. Download the latest CSV from the Ministry website
2. Replace `OpenData_-_seznam_jmen_k_2026-01-31_v2.csv` with the new file
3. (Optional) Edit the CSV to reclassify neutral names (NEUTRAL → MUZ or ZENA)
4. Run the extraction script:
   ```bash
   python extract_names_csv.py
   ```
5. This regenerates `czech_names.py` with the updated names

**Note:** The database includes neutral names (like Andrea, Karel, Pavla) which are skipped during extraction. You can manually edit the CSV to assign them to male (MUZ) or female (ZENA) categories as needed.

## Example Template

Create a Word document with content like:

```
Certificate of Completion

Certificate No. [COUNTER]/[YEAR]

This is to certify that [NAME], born on [DOB], has successfully completed...

[NAME] [ABSOLVOVAL/A] kurz a [ZÍSKAL/A] certifikát.
```

The template can include any formatting: custom fonts, watermarks, headers, footers, styles, and more. All formatting will be preserved in the generated certificates.

## Features in Detail

### Certificate Numbering
- Set starting certificate number for each batch
- Counter automatically increments for each person
- Year placeholder automatically uses current year
- No persistence needed - user manages series manually

### Multi-Certificate Generation
- Generate multiple certificates in one document
- Each certificate appears on a separate page
- All original template styling preserved across all certificates

### Template Preservation
- Original template is kept in memory for reuse
- Generate multiple batches without re-uploading
- All formatting elements preserved: fonts, styles, watermarks, headings

### Batch Processing
- Add multiple people to a list before generating
- Review and edit the list before generation
- Single download for all certificates

## Local Distribution (Portable App)

To create a portable version for distribution to other users:

### Building the Executable

1. Install PyInstaller (one-time setup):
   ```bash
   pip install pyinstaller
   ```

2. Run the build script:
   ```bash
   build.bat
   ```

3. This creates a `dist` folder with `CertificateGenerator.exe`

### Distributing to Users

Package and share these files/folders:
- `dist/CertificateGenerator.exe` - The launcher
- `app.py` - The main application
- `requirements.txt` - Dependencies list
- Any template files (optional)

**Important:** Users need Python installed on their machine, or you can include a portable Python distribution.

### User Instructions

1. Extract all files to a folder
2. Double-click `CertificateGenerator.exe`
3. The app will open in the default browser
4. Close the terminal window to stop the app

**Note:** The source code (app.py) is visible and editable. This is suitable for trusted users (family, colleagues) but not for public/commercial distribution.

## Azure App Service Deployment

To deploy on Azure App Service:

1. Use a Linux App Service plan
2. Add startup command: `streamlit run app.py --server.port $PORT`
3. Ensure `requirements.txt` is included in deployment
4. Configure port binding in Azure portal

## Version History

- **0.5** (2025-02-08)
  - Refactored code into modular structure (certificate_generator.py, data_utils.py)
  - Separated UI components into focused functions
  - Added automatic gender detection from Czech names database (7,164 names from Ministry of Interior)
  - Switched to CSV-based name source for easier maintenance
  - Visual indicators (⚠️) for unrecognized names
  - Color-coded names: 🔵 blue for males, 🔴 pink for females
  - Date format without leading zeros (D. M. YYYY)
  - Improved code maintainability and testability

- **0.4** (2025-02-06)
  - Certificate counter with auto-increment
  - Year placeholder [YEAR]
  - CSV upload functionality

- **0.3** (2025-02-04)
  - Gender selection and automatic Czech verb conjugation

- **0.2** (2025-02-03)
  - Multi-certificate support, batch generation, test data feature

- **0.1** (2025-02-01)
  - Initial release
