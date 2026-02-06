import streamlit as st
from datetime import datetime

# Import from local modules
from certificate_generator import generate_multi_certificate
from data_utils import format_date_no_leading_zeros, parse_csv_file


def main():
    st.set_page_config(
        page_title="Certificate Generator",
        page_icon="📜",
        layout="centered"
    )
    
    st.title("📜 Certificate Generator")
    st.markdown("Upload a certificate template and generate personalized certificates")
    
    # Initialize session state for template
    if 'template' not in st.session_state:
        st.session_state.template = None
        st.session_state.template_name = None
    
    # Initialize session state for people list
    if 'people_list' not in st.session_state:
        st.session_state.people_list = []
    
    # Initialize session state for starting counter
    if 'starting_counter' not in st.session_state:
        st.session_state.starting_counter = 1
    
    # Initialize session state for CSV upload tracking
    if 'csv_uploaded' not in st.session_state:
        st.session_state.csv_uploaded = False
    
    # File uploader
    st.subheader("1. Upload Certificate Template")
    uploaded_file = st.file_uploader(
        "Choose a .docx template file",
        type=['docx'],
        help="Upload a Word document with placeholders [NAME] and [DOB]"
    )
    
    # Store template in session state
    if uploaded_file is not None:
        st.session_state.template = uploaded_file.read()
        st.session_state.template_name = uploaded_file.name
        st.success(f"✅ Template '{uploaded_file.name}' loaded successfully!")
    
    # Show form only if template is loaded
    if st.session_state.template is not None:
        st.subheader("2. Add Certificate Holders")
        
        # Only show CSV uploader if not already uploaded
        if not st.session_state.people_list or st.button("🔄 Clear and Upload New CSV", type="secondary"):
            st.session_state.people_list = []
            st.session_state.csv_uploaded = False
        
        if not st.session_state.csv_uploaded:
            # CSV Upload option
            st.markdown("**Option A: Upload CSV File**")
            csv_file = st.file_uploader(
                "Upload CSV (COUNTER,Surname,Name,DOB - no headers)",
                type=['csv'],
                help="Format: COUNTER,Surname,Name,DOB (e.g., 15,Novák,Jan,01.01.1990)",
                key="csv_uploader"
            )
            
            if csv_file is not None:
                try:
                    imported_people, first_counter = parse_csv_file(csv_file)
                    
                    if imported_people:
                        st.session_state.people_list = imported_people
                        st.session_state.csv_uploaded = True
                        if first_counter is not None:
                            st.session_state.starting_counter = first_counter
                        st.success(f"✅ Imported {len(imported_people)} people from CSV")
                        if first_counter is not None:
                            st.info(f"📊 Starting counter set to: {first_counter}")
                        st.rerun()
                    else:
                        st.error("⚠️ No valid rows found in CSV")
                        
                except Exception as e:
                    st.error(f"❌ Error reading CSV: {str(e)}")
            
            st.markdown("**Option B: Manual Entry**")
        else:
            st.info(f"📊 CSV loaded with {len(st.session_state.people_list)} people. Use the button above to upload a different CSV.")
        
        # Manual entry section - only show if CSV not uploaded
        if not st.session_state.csv_uploaded:
            st.markdown("**Option B: Manual Entry**")
            
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
                        # Format date in Czech format (no leading zeros)
                        formatted_dob = format_date_no_leading_zeros(dob.day, dob.month, dob.year)
                        
                        # Add to list
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
        
        # Display current list
        if st.session_state.people_list:
            st.subheader("3. Certificate Holders List")
            
            # Display as table
            for idx, person in enumerate(st.session_state.people_list):
                col1, col2, col3, col4 = st.columns([3, 3, 1.5, 1])
                with col1:
                    st.text(person['name'])
                with col2:
                    st.text(person['dob'])
                with col3:
                    # Gender toggle button
                    current_gender = person.get('gender', 'female')
                    gender_icon = '👩 Žena' if current_gender == 'female' else '👨 Muž'
                    if st.button(gender_icon, key=f"gender_{idx}", help="Klikněte pro změnu pohlaví"):
                        # Toggle gender
                        new_gender = 'male' if current_gender == 'female' else 'female'
                        st.session_state.people_list[idx]['gender'] = new_gender
                        st.rerun()
                with col4:
                    if st.button("🗑️", key=f"del_{idx}", help="Remove"):
                        st.session_state.people_list.pop(idx)
                        st.rerun()
            
            st.divider()
            
            # Generate all certificates button
            st.subheader("4. Generate Certificates")
            
            # Counter input
            col_counter, col_year = st.columns([2, 2])
            with col_counter:
                starting_counter = st.number_input(
                    "Starting Certificate Number",
                    min_value=1,
                    value=st.session_state.starting_counter,
                    step=1,
                    key='counter_input',
                    help=f"First certificate will be numbered with this value, then increments for each person"
                )
                st.session_state.starting_counter = starting_counter
            with col_year:
                current_year = datetime.now().year
                st.info(f"📅 Year: {current_year}")
            
            if st.button("📄 Generate All Certificates", type="primary", use_container_width=True):
                try:
                    # Generate multi-certificate document with counter
                    certificate_bytes = generate_multi_certificate(
                        st.session_state.template,
                        st.session_state.people_list,
                        starting_counter
                    )
                    
                    # Generate filename
                    if len(st.session_state.people_list) == 1:
                        filename = f"certificate_{st.session_state.people_list[0]['name'].replace(' ', '_')}.docx"
                    else:
                        filename = f"certificates_batch_{len(st.session_state.people_list)}.docx"
                    
                    # Store in session state for download
                    st.session_state.generated_cert = certificate_bytes.getvalue()
                    st.session_state.cert_filename = filename
                    
                    st.success(f"✅ Generated {len(st.session_state.people_list)} certificate(s) successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Error generating certificates: {str(e)}")
        
        # Download button (outside form to avoid re-generation)
        if 'generated_cert' in st.session_state and st.session_state.people_list:
            st.subheader("5. Download Certificates")
            st.download_button(
                label=f"📥 Download {len(st.session_state.people_list)} Certificate(s)",
                data=st.session_state.generated_cert,
                file_name=st.session_state.cert_filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="secondary",
                use_container_width=True
            )
    else:
        st.info("👆 Please upload a certificate template to begin.")
    
    # Sidebar with instructions
    with st.sidebar:
        st.header("ℹ️ Instructions")
        st.markdown("""
        1. **Prepare your template**: Create a Word document (.docx) with placeholders:
           - `[NAME]` - for the certificate holder's name
           - `[DOB]` - for the date of birth
           - `[COUNTER]` - certificate number (auto-increments)
           - `[YEAR]` - current year (automatic)
           - Gender-dependent verbs (Czech):
             - `[ZÍSKAL/A]` → získal / získala
             - `[ABSOLVOVAL/A]` → absolvoval / absolvovala
             - `[DOKONČIL/A]` → dokončil / dokončila
             - `[SPLNIL/A]`, `[SLOŽIL/A]`, `[VYKONAL/A]`, etc.
        
        2. **Upload** the template using the file uploader
        
        3. **Add people** - Choose one of the options:
           - **Option A: Upload CSV** - Format: COUNTER,Surname,Name,DOB
             - Example: `15,Novák,Jan,01.01.1990`
             - No headers, UTF-8 encoding, comma-separated
             - Counter from first row sets starting number
           - **Option B: Manual Entry** - Enter individually
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
        st.caption("Version 0.5 - Refactored & Modular")        

if __name__ == "__main__":
    main()
