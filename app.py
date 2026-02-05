import streamlit as st
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_BREAK
from io import BytesIO
from datetime import datetime
import re
import copy


def replace_placeholders(doc, replacements):
    """
    Replace placeholders in the document with actual values.
    Placeholders format: [NAME], [DOB]
    """
    # Replace in paragraphs
    for paragraph in doc.paragraphs:
        for key, value in replacements.items():
            if key in paragraph.text:
                # Replace placeholder in runs to preserve formatting
                for run in paragraph.runs:
                    if key in run.text:
                        run.text = run.text.replace(key, value)
    
    # Replace in tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for key, value in replacements.items():
                        if key in paragraph.text:
                            for run in paragraph.runs:
                                if key in run.text:
                                    run.text = run.text.replace(key, value)
    
    # Replace in headers
    for section in doc.sections:
        header = section.header
        for paragraph in header.paragraphs:
            for key, value in replacements.items():
                if key in paragraph.text:
                    for run in paragraph.runs:
                        if key in run.text:
                            run.text = run.text.replace(key, value)
        
        # Replace in footers
        footer = section.footer
        for paragraph in footer.paragraphs:
            for key, value in replacements.items():
                if key in paragraph.text:
                    for run in paragraph.runs:
                        if key in run.text:
                            run.text = run.text.replace(key, value)
    
    return doc


def generate_certificate(template_bytes, name, dob):
    """
    Generate a certificate from template with provided data.
    Returns a Document object (not bytes).
    """
    # Load template from bytes
    doc = Document(BytesIO(template_bytes))
    
    # Define replacements
    replacements = {
        '[NAME]': name,
        '[DOB]': dob
    }
    
    # Replace placeholders
    doc = replace_placeholders(doc, replacements)
    
    return doc


def generate_multi_certificate(template_bytes, people_list):
    """
    Generate multiple certificates in a single document.
    Each certificate on a separate page.
    """
    if not people_list:
        return None
    
    # Start with the first certificate - this preserves all template styling
    first_person = people_list[0]
    final_doc = generate_certificate(
        template_bytes,
        first_person['name'],
        first_person['dob']
    )
    
    # Add remaining certificates with page breaks
    for person in people_list[1:]:
        # Load fresh template for this person
        temp_doc = Document(BytesIO(template_bytes))
        
        # Define replacements
        replacements = {
            '[NAME]': person['name'],
            '[DOB]': person['dob']
        }
        
        # Replace placeholders in temp_doc
        temp_doc = replace_placeholders(temp_doc, replacements)
        
        # Copy all elements from temp_doc to final_doc
        first_element = True
        for element in temp_doc.element.body:
            # Skip section properties
            if element.tag.endswith('sectPr'):
                continue
            
            # Deep copy the element
            new_element = copy.deepcopy(element)
            
            # Add page break to the first paragraph element
            if first_element and new_element.tag.endswith('p'):
                from docx.oxml import OxmlElement
                run = OxmlElement('w:r')
                br = OxmlElement('w:br')
                br.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type', 'page')
                run.append(br)
                # Insert at the beginning of the paragraph
                new_element.insert(0, run)
                first_element = False
            
            # Append to final document
            final_doc.element.body.append(new_element)
    
    # Save to BytesIO
    output = BytesIO()
    final_doc.save(output)
    output.seek(0)
    
    return output


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
        
        # Test button to add 8 sample people
        if st.button("🧪 Add 8 Test People", type="secondary"):
            st.session_state.people_list = [
                {'name': 'Jan Novák', 'dob': '01. 01. 1990'},
                {'name': 'Petr Dvořák', 'dob': '15. 03. 1985'},
                {'name': 'Marie Svobodová', 'dob': '22. 07. 1992'},
                {'name': 'Eva Černá', 'dob': '10. 12. 1988'},
                {'name': 'Tomáš Procházka', 'dob': '05. 05. 1995'},
                {'name': 'Jana Kučerová', 'dob': '18. 09. 1991'},
                {'name': 'Pavel Horák', 'dob': '28. 02. 1987'},
                {'name': 'Lucie Málková', 'dob': '14. 11. 1993'}
            ]
            st.rerun()
        
        with st.form("certificate_form"):
            col1, col2 = st.columns(2)
            
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
            
            col_a, col_b = st.columns(2)
            with col_a:
                add_person = st.form_submit_button("➕ Add Person", type="secondary")
            with col_b:
                clear_all = st.form_submit_button("🗑️ Clear All", type="secondary")
            
            if add_person:
                if not name or not dob:
                    st.error("⚠️ Please fill in all fields!")
                else:
                    # Format date in Czech format
                    formatted_dob = dob.strftime("%d. %m. %Y")
                    
                    # Add to list
                    st.session_state.people_list.append({
                        'name': name,
                        'dob': formatted_dob
                    })
                    st.success(f"✅ Added {name}")
                    st.rerun()
            
            if clear_all:
                st.session_state.people_list = []
                st.rerun()
        
        # Display current list
        if st.session_state.people_list:
            st.subheader("3. Certificate Holders List")
            
            # Display as table
            for idx, person in enumerate(st.session_state.people_list):
                col1, col2, col3 = st.columns([3, 3, 1])
                with col1:
                    st.text(person['name'])
                with col2:
                    st.text(person['dob'])
                with col3:
                    if st.button("🗑️", key=f"del_{idx}", help="Remove"):
                        st.session_state.people_list.pop(idx)
                        st.rerun()
            
            st.divider()
            
            # Generate all certificates button
            st.subheader("4. Generate Certificates")
            if st.button("📄 Generate All Certificates", type="primary", use_container_width=True):
                try:
                    # Generate multi-certificate document
                    certificate_bytes = generate_multi_certificate(
                        st.session_state.template,
                        st.session_state.people_list
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
        
        2. **Upload** the template using the file uploader
        
        3. **Add people** - Enter name and date of birth, then click "Add Person"
           - Add as many people as needed
           - Review the list before generating
        
        4. **Generate** all certificates in a single document
           - Each certificate will be on a separate page
        
        5. **Download** the single file with all certificates
        
        6. **Repeat** - The template is preserved for future use!
        """)
        
        st.divider()
        st.caption("Version 0.2 - Multi-certificate support")


if __name__ == "__main__":
    main()
