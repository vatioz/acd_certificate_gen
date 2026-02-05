# Certificate Generator

A Streamlit web application for generating personalized certificates from Word document templates. Create multiple certificates in a single document with full formatting preservation.

## Features

- Upload .docx certificate templates with full style preservation
- Add multiple certificate holders to a list
- Replace placeholders with personalized data
- Generate all certificates in a single document (one certificate per page)
- Preserves all template formatting: fonts, styles, watermarks, headings
- Czech date format support (DD. MM. YYYY)
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
   - Enter Full Name and Date of Birth
   - Click "Add Person" to add to the list
   - Repeat for all certificate holders
   - Use "Add 8 Test People" button for quick testing

5. Review the list of certificate holders
   - Remove individuals if needed using the delete button

6. Click "Generate All Certificates"

7. Download the single .docx file containing all certificates

## Template Placeholders

- `[NAME]` - Will be replaced with the full name
- `[DOB]` - Will be replaced with the date of birth in DD. MM. YYYY format

## Example Template

Create a Word document with content like:

```
Certificate of Completion

This is to certify that [NAME], born on [DOB], has successfully completed...
```

The template can include any formatting: custom fonts, watermarks, headers, footers, styles, and more. All formatting will be preserved in the generated certificates.

## Features in Detail

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

- **0.2** - Multi-certificate support, batch generation, test data feature
- **0.1** - Initial release
