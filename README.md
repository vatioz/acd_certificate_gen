# Certificate Generator

A Streamlit web application for generating personalized certificates from Word document templates.

## Features

- Upload .docx certificate templates
- Replace placeholders with personalized data
- Generate multiple certificates using the same template
- Download generated certificates

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

4. Enter the certificate holder's information:
   - Full Name (in "Surname Name" format)
   - Date of Birth (DD.MM.YYYY format)

5. Click "Generate Certificate"

6. Download the generated certificate

## Template Placeholders

- `[NAME]` - Will be replaced with the full name
- `[DOB]` - Will be replaced with the date of birth in DD. MM. YYYY format

## Example Template

Create a Word document with content like:

```
Certificate of Completion

This is to certify that [NAME], born on [DOB], has successfully completed...
```

## Version

0.1 - Initial release
