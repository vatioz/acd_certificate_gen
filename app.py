import streamlit as st
from datetime import datetime
import time
from dotenv import load_dotenv

load_dotenv(override=True)

# Import from local modules
from certificate_generator import generate_multi_certificate
from data_utils import format_date_no_leading_zeros, parse_csv_file, parse_dates_in_people_list
from analyzer_client import (
    AnalyzerApiError,
    AnalyzerConfigError,
    ContentUnderstandingClient,
    delete_blob_from_sas_url,
    map_analyzer_result_to_people,
    upload_pdf_to_blob_and_get_sas_url,
)


def initialize_session_state():
    """Initialize all session state variables."""
    if 'template' not in st.session_state:
        st.session_state.template = None
        st.session_state.template_name = None
    
    if 'people_list' not in st.session_state:
        st.session_state.people_list = []
    
    if 'starting_counter' not in st.session_state:
        st.session_state.starting_counter = 1
    if 'date_format' not in st.session_state:
        st.session_state.date_format = 'Auto-detect (Czech DD/MM/YYYY priority)'
    
    if 'data_input_mode' not in st.session_state:
        st.session_state.data_input_mode = 'Analyzer (PDF)'

    if 'analyzer_status' not in st.session_state:
        st.session_state.analyzer_status = 'idle'
    if 'analyzer_operation_id' not in st.session_state:
        st.session_state.analyzer_operation_id = None
    if 'analyzer_operation_location' not in st.session_state:
        st.session_state.analyzer_operation_location = None
    if 'analyzer_error' not in st.session_state:
        st.session_state.analyzer_error = None
    if 'analyzer_raw_result' not in st.session_state:
        st.session_state.analyzer_raw_result = None
    if 'analyzer_last_poll_ts' not in st.session_state:
        st.session_state.analyzer_last_poll_ts = 0.0
    if 'analyzer_poll_interval_seconds' not in st.session_state:
        st.session_state.analyzer_poll_interval_seconds = 2.0
    if 'analyzer_input_url' not in st.session_state:
        st.session_state.analyzer_input_url = None
    if 'analyzer_blob_cleanup_done' not in st.session_state:
        st.session_state.analyzer_blob_cleanup_done = False


def reset_analyzer_state():
    """Reset analyzer async job state."""
    st.session_state.analyzer_status = 'idle'
    st.session_state.analyzer_operation_id = None
    st.session_state.analyzer_operation_location = None
    st.session_state.analyzer_error = None
    st.session_state.analyzer_raw_result = None
    st.session_state.analyzer_last_poll_ts = 0.0
    st.session_state.analyzer_input_url = None
    st.session_state.analyzer_blob_cleanup_done = False


def apply_imported_people(imported_people, first_counter=None):
    """Apply imported people to the app state and parse dates."""
    st.session_state.people_list = imported_people
    if first_counter is not None:
        st.session_state.starting_counter = first_counter

    st.session_state.people_list = parse_dates_in_people_list(
        st.session_state.people_list,
        st.session_state.date_format
    )


def render_analyzer_uploader():
    """Render Azure Content Understanding analyzer upload and async status UI."""
    st.markdown("**Option A: Azure Analyzer (PDF)**")
    st.caption("Asynchronous parsing using Azure Content Understanding analyzer.")

    source_file = st.file_uploader(
        "Upload participant roster PDF",
        type=['pdf'],
        help="Supported format: PDF",
        key="analyzer_pdf_uploader"
    )

    if source_file is not None:
        detected_type = source_file.type if source_file.type else "unknown"
        st.caption(f"Detected file type: {detected_type} ({source_file.name})")

    col1, col2 = st.columns(2)
    with col1:
        start_analysis = st.button(
            "🤖 Analyze File with Azure",
            type="secondary",
            disabled=source_file is None or st.session_state.analyzer_status == 'running',
            use_container_width=True,
        )
    with col2:
        reset_analysis = st.button(
            "🧹 Reset Analyzer State",
            type="secondary",
            use_container_width=True,
        )

    if reset_analysis:
        if st.session_state.analyzer_input_url and not st.session_state.analyzer_blob_cleanup_done:
            delete_blob_from_sas_url(st.session_state.analyzer_input_url)
        reset_analyzer_state()
        st.rerun()

    if start_analysis and source_file is not None:
        try:
            source_url = upload_pdf_to_blob_and_get_sas_url(
                source_file.read(),
                source_file.name,
            )
            client = ContentUnderstandingClient.from_env()
            submission = client.submit_document(source_url)
            st.session_state.analyzer_status = 'running'
            st.session_state.analyzer_operation_id = submission.get('operation_id')
            st.session_state.analyzer_operation_location = submission.get('operation_location')
            st.session_state.analyzer_input_url = source_url
            st.session_state.analyzer_blob_cleanup_done = False
            st.session_state.analyzer_error = None
            st.session_state.analyzer_raw_result = None
            st.session_state.analyzer_last_poll_ts = 0.0
            st.success("✅ File uploaded to Blob and analysis job submitted. Waiting for results...")
            st.rerun()
        except AnalyzerConfigError as e:
            st.error(f"❌ Analyzer configuration error: {str(e)}")
        except AnalyzerApiError as e:
            st.error(f"❌ Analyzer API error: {str(e)}")
        except Exception as e:
            st.error(f"❌ Unexpected analyzer error: {str(e)}")

    status = st.session_state.analyzer_status

    if status == 'running':
        now = time.time()
        poll_interval = st.session_state.analyzer_poll_interval_seconds
        should_poll = (now - st.session_state.analyzer_last_poll_ts) >= poll_interval

        if should_poll:
            try:
                client = ContentUnderstandingClient.from_env()
                poll_data = client.poll_operation(
                    st.session_state.analyzer_operation_id,
                    st.session_state.analyzer_operation_location,
                )

                st.session_state.analyzer_last_poll_ts = now
                st.session_state.analyzer_status = poll_data['status']
                st.session_state.analyzer_raw_result = poll_data['raw']
                st.session_state.analyzer_error = poll_data.get('error')

                if poll_data['status'] == 'succeeded':
                    imported_people, first_counter = map_analyzer_result_to_people(poll_data['raw'])

                    if imported_people:
                        apply_imported_people(imported_people, first_counter)
                        st.success(f"✅ Analyzer imported {len(imported_people)} people.")
                    else:
                        st.session_state.analyzer_status = 'failed'
                        st.session_state.analyzer_error = "Analyzer succeeded but no participants were detected."
                elif poll_data['status'] == 'failed' and not st.session_state.analyzer_error:
                    st.session_state.analyzer_error = "Analyzer job failed."

            except AnalyzerConfigError as e:
                st.session_state.analyzer_status = 'failed'
                st.session_state.analyzer_error = str(e)
            except AnalyzerApiError as e:
                st.session_state.analyzer_status = 'failed'
                st.session_state.analyzer_error = str(e)
            except Exception as e:
                st.session_state.analyzer_status = 'failed'
                st.session_state.analyzer_error = str(e)

        if st.session_state.analyzer_status == 'running':
            st.info("⏳ Analyzer is running... refreshing status automatically.")
            time.sleep(1.0)
            st.rerun()

    if st.session_state.analyzer_status == 'succeeded':
        st.success(f"✅ Latest analyzer import is ready ({len(st.session_state.people_list)} people loaded).")
        if st.session_state.analyzer_input_url:
            st.caption("Source file was submitted through Azure Blob SAS URL.")

    if st.session_state.analyzer_status == 'failed':
        st.error(f"❌ Analyzer failed: {st.session_state.analyzer_error or 'Unknown error'}")

    if (
        st.session_state.analyzer_status in ('succeeded', 'failed')
        and st.session_state.analyzer_input_url
        and not st.session_state.analyzer_blob_cleanup_done
    ):
        cleanup_ok = delete_blob_from_sas_url(st.session_state.analyzer_input_url)
        st.session_state.analyzer_blob_cleanup_done = True
        if cleanup_ok:
            st.caption("🧹 Temporary Blob source file was deleted.")
        else:
            st.caption("⚠️ Could not delete temporary Blob source file automatically.")


def render_template_uploader():
    """Render the template upload section."""
    st.subheader("1. Upload Certificate Template")
    uploaded_file = st.file_uploader(
        "Choose a .docx template file",
        type=['docx'],
        help="Upload a Word document with placeholders [NAME] and [DOB]"
    )
    
    if uploaded_file is not None:
        st.session_state.template = uploaded_file.read()
        st.session_state.template_name = uploaded_file.name
        st.success(f"✅ Template '{uploaded_file.name}' loaded successfully!")


def render_csv_uploader():
    """Render the CSV upload section."""
    st.markdown("**CSV Upload (backup)**")
    csv_file = st.file_uploader(
        "Upload CSV (COUNTER,PRE,Surname,Name,POST,DOB - no headers)",
        type=['csv'],
        help="Format: COUNTER,PRE,Surname,Name,POST,DOB (e.g., 15,Dr.,Novák,Jan,Ph.D.,01.01.1990)",
        key="csv_uploader"
    )
    
    if csv_file is not None:
        try:
            imported_people, first_counter = parse_csv_file(csv_file)
            
            if imported_people:
                apply_imported_people(imported_people, first_counter)
                
                st.success(f"✅ Imported {len(imported_people)} people from CSV")
                if first_counter is not None:
                    st.info(f"📊 Starting counter set to: {first_counter}")
                st.rerun()
            else:
                st.error("⚠️ No valid rows found in CSV")
                
        except Exception as e:
            st.error(f"❌ Error reading CSV: {str(e)}")


def render_manual_entry_form():
    """Render the manual entry form section."""
    st.markdown("**Manual Entry (backup)**")
    
    # Test button to add 8 sample people
    if st.button("🧪 Add 8 Test People", type="secondary"):
        st.session_state.people_list = [
            {'name': 'Jan Novák', 'dob': '1. 1. 1990', 'gender': 'male'},
            {'name': 'Petr Dvořák', 'dob': '15. 3. 1985', 'gender': 'male'},
            {'name': 'Marie Svobodová', 'dob': '22. 7. 1992', 'gender': 'female'},
            {'name': 'Eva Černá', 'dob': '10. 12. 1988', 'gender': 'female'},
            {'name': 'Tomáš Procházka', 'dob': '5. 5. 1995', 'gender': 'male'},
            {'name': 'Jana Kučerová', 'dob': '18. 9. 1991', 'gender': 'female'},
            {'name': 'Pavel Horák', 'dob': '28. 2. 1987', 'gender': 'male'},
            {'name': 'Lucie Málková', 'dob': '14. 11. 1993', 'gender': 'female'}
        ]
        st.rerun()

    with st.form("certificate_form"):
        col1, col2, col3 = st.columns([3, 3, 2])
        
        with col1:
            name = st.text_input(
                "Full Name",
                placeholder="Jan Novák",
                help="Enter the full name (Surname Name format for filename)"
            )
        
        with col2:
            dob = st.date_input(
                "Date of Birth",
                value=None,
                min_value=datetime(1900, 1, 1),
                max_value=datetime.today(),
                format="DD.MM.YYYY",
                help="Select date of birth"
            )
        
        with col3:
            gender = st.radio(
                "Gender",
                options=['female', 'male'],
                format_func=lambda x: '👩 Žena' if x == 'female' else '👨 Muž',
                index=0,
                help="Default: Žena"
            )
        
        col_a, col_b = st.columns(2)
        with col_a:
            add_person = st.form_submit_button("➕ Add Person", type="secondary")
        with col_b:
            clear_all = st.form_submit_button("🗑️ Clear All", type="secondary")
        
        if add_person:
            if not name or not dob:
                st.error("⚠️ Please fill in all fields!")
            else:
                formatted_dob = format_date_no_leading_zeros(dob.day, dob.month, dob.year)
                st.session_state.people_list.append({
                    'name': name,
                    'dob': formatted_dob,
                    'gender': gender
                })
                gender_label = '👩' if gender == 'female' else '👨'
                st.success(f"✅ Added {gender_label} {name}")
                st.rerun()
        
        if clear_all:
            st.session_state.people_list = []
            st.rerun()


def render_data_input_section():
    """Render data input section with mode selector (Analyzer, CSV, Manual)."""
    st.subheader("2. Add Certificate Holders")

    mode = st.radio(
        "Choose input method",
        options=['Analyzer (PDF)', 'CSV Upload (backup)', 'Manual Entry (backup)'],
        key='data_input_mode',
        horizontal=True,
    )

    if st.session_state.data_input_mode not in ['Analyzer (PDF)', 'CSV Upload (backup)', 'Manual Entry (backup)']:
        st.session_state.data_input_mode = 'Analyzer (PDF)'

    if st.button("🧹 Clear People List", type="secondary"):
        st.session_state.people_list = []

    if mode == 'Analyzer (PDF)':
        st.session_state.date_format = 'YYYY-MM-DD (ISO)'
        render_analyzer_uploader()
    elif mode == 'CSV Upload (backup)':
        render_csv_uploader()
    else:
        render_manual_entry_form()


def render_people_list():
    """Render the list of certificate holders with gender toggles."""
    if not st.session_state.people_list:
        return
    
    st.subheader("3. Certificate Holders List")
    st.markdown(f"**Total: {len(st.session_state.people_list)} people**")
    
    # Date format selector
    date_format_options = [
        'Auto-detect (Czech DD/MM/YYYY priority)',
        'DD.MM.YYYY (Czech dots)',
        'DD/MM/YYYY (European slashes)',
        'MM/DD/YYYY (US)',
        'YYYY-MM-DD (ISO)'
    ]
    
    selected_format = st.selectbox(
        "Date format in imported data",
        options=date_format_options,
        index=date_format_options.index(st.session_state.date_format),
        help="Select the date format used in imported data. Dates shown below are raw values from source."
    )
    
    if selected_format != st.session_state.date_format:
        st.session_state.date_format = selected_format
        # Reparse dates with new format
        st.session_state.people_list = parse_dates_in_people_list(
            st.session_state.people_list,
            selected_format
        )
        st.rerun()
    
    # Header row
    col1, col2, col3, col4 = st.columns([3, 3, 1.5, 1])
    with col1:
        st.markdown("**Name**")
    with col2:
        st.markdown("**Date of Birth**")
    with col3:
        st.markdown("**Gender**")
    with col4:
        st.markdown("**Action**")
    
    st.divider()
    
    # Data rows
    for idx, person in enumerate(st.session_state.people_list):
        current_gender = person.get('gender', 'female')
        
        # Color scheme
        dot = '🔵' if current_gender == 'male' else '🔴'
        text_color = '#1976D2' if current_gender == 'male' else '#C2185B'  # Blue for male, pink for female
        
        col1, col2, col3, col4 = st.columns([3, 3, 1.5, 1])
        
        with col1:
            # Add warning indicator and colored dot + text
            warning = "⚠️ " if not person.get('gender_detected', True) else ""
            st.markdown(f"{warning}{dot} <span style='color: {text_color}; font-weight: 500;'>{person['name']}</span>", unsafe_allow_html=True)
        
        with col2:
            st.text(person.get('dob_raw', person['dob']))
        
        with col3:
            gender_icon = '👩 Žena' if current_gender == 'female' else '👨 Muž'
            if st.button(gender_icon, key=f"gender_{idx}", help="Klikněte pro změnu pohlaví"):
                new_gender = 'male' if current_gender == 'female' else 'female'
                st.session_state.people_list[idx]['gender'] = new_gender
                st.rerun()
        
        with col4:
            if st.button("🗑️", key=f"del_{idx}", help="Odstranit"):
                st.session_state.people_list.pop(idx)
                st.rerun()
    
    st.divider()


def render_certificate_generator():
    """Render the certificate generation section."""
    if not st.session_state.people_list:
        return

    if st.session_state.analyzer_status == 'running':
        st.warning("⏳ Analyzer import is still running. Wait for completion before generating certificates.")
        return
    
    st.subheader("4. Generate Certificates")
    
    col_counter, col_year = st.columns([2, 2])
    
    with col_counter:
        starting_counter = st.number_input(
            "Starting Certificate Number",
            min_value=1,
            value=st.session_state.starting_counter,
            step=1,
            help="First certificate will be numbered with this value, then increments for each person"
        )
        st.session_state.starting_counter = starting_counter
    
    with col_year:
        current_year = datetime.now().year
        certificate_year = st.number_input(
            "Certificate Year",
            min_value=2000,
            max_value=2100,
            value=current_year,
            step=1,
            help="Year to use in certificates (e.g., for certificates from last year)"
        )
    
    if st.button("📄 Generate All Certificates", type="primary", use_container_width=True):
        try:
            certificate_bytes = generate_multi_certificate(
                st.session_state.template,
                st.session_state.people_list,
                starting_counter,
                certificate_year
            )
            
            # Generate filename
            if len(st.session_state.people_list) == 1:
                filename = f"certificate_{st.session_state.people_list[0]['name'].replace(' ', '_')}.docx"
            else:
                filename = f"certificates_batch_{len(st.session_state.people_list)}.docx"
            
            st.session_state.generated_cert = certificate_bytes.getvalue()
            st.session_state.cert_filename = filename
            
            st.success(f"✅ Generated {len(st.session_state.people_list)} certificate(s) successfully!")
            
        except Exception as e:
            st.error(f"❌ Error generating certificates: {str(e)}")


def render_download_section():
    """Render the download section."""
    if 'generated_cert' not in st.session_state or not st.session_state.people_list:
        return
    
    st.subheader("5. Download Certificates")
    st.download_button(
        label=f"📥 Download {len(st.session_state.people_list)} Certificate(s)",
        data=st.session_state.generated_cert,
        file_name=st.session_state.cert_filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="secondary",
        use_container_width=True
    )


def render_sidebar():
    """Render the sidebar with instructions."""
    with st.sidebar:
        st.header("ℹ️ Instructions")
        st.markdown("""
        1. **Prepare your template**: Create a Word document (.docx) with placeholders:
           - `[NAME]` - for the certificate holder's name
           - `[PRE]` - for any title before the name (e.g. Dr. or Ing.)
           - `[POST]` - for any title after the name (e.g., Ph.D.)
           - `[DOB]` - for the date of birth
           - `[COUNTER]` - certificate number (auto-increments)
           - `[YEAR]` - current year (automatic)
           - Gender-dependent verbs (Czech):
             - `[ZISKAL/A]` → získal / získala
             - `[ABSOLVOVAL/A]` → absolvoval / absolvovala
             - `[NAROZEN/A]` → narozen / narozená
        
        2. **Upload** the template using the file uploader
        
        3. **Add people** - Choose one of the options:
                     - **Analyzer (PDF)**
                         - Upload a roster PDF and run asynchronous extraction
                         - Requires Azure Content Understanding environment variables
                     - **CSV Upload (backup)**
                         - Format: Číslo,Titul před,Příjmení,Jméno,Titul za,Datum narození
                         - Example: `15,Ing.,Novák,Jan,PhD.,01.01.1990`
                         - No headers, UTF-8 encoding, comma-separated
                         - Counter from first row sets starting number
                     - **Manual Entry (backup)** - Enter individually
           - **Test Data** - Quick test with 8 sample people
           - All imported people default to 👩 Žena
        
        4. **Review** the list and adjust gender if needed
           - Click gender button to toggle male/female
        
        5. **Set starting number** for the certificate series
           - Counter auto-increments for each person
        
        6. **Generate** all certificates in a single document
           - Each certificate will be on a separate page
        
        7. **Download** the single file with all certificates
        
        8. **Repeat** - The template is preserved for future use!
        """)
        
        st.divider()
        st.caption("Version 0.6 - Analyzer Integration & .env Support")


def main():
    """Main application entry point - orchestrates the UI flow."""
    st.set_page_config(
        page_title="Certificate Generator",
        page_icon="📜",
        layout="centered"
    )
    
    st.title("📜 Certificate Generator")
    st.markdown("Upload a certificate template and generate personalized certificates")
    
    # Initialize application state
    initialize_session_state()
    
    # Render template upload section
    render_template_uploader()
    
    # Show remaining sections only if template is loaded
    if st.session_state.template is not None:
        render_data_input_section()
        render_people_list()
        render_certificate_generator()
        render_download_section()
    else:
        st.info("👆 Please upload a certificate template to begin.")
    
    # Always render sidebar
    render_sidebar()        

if __name__ == "__main__":
    main()
