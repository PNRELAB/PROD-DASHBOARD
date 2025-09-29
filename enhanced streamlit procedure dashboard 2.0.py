import streamlit as st
import os
import json
from pathlib import Path
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

#--------------------------------------------------------
# CONFIGURATION - update these paths to match your PC
#---------------------------------------------------------
#Local OneDrive path that syncs with SharePoint (update to your actual OneDrive path)
SHARED_FOLDER = r"C:\Users\1000329829\OneDrive - Western Digital\RE_LAB_PROCEDURE"
TESTS_FILE = os.path.join(SHARED_FOLDER, "tests.json")
PROCEDURES_FOLDER = os.path.join(SHARED_FOLDER, "TestProcedures")
os.makedirs(PROCEDURES_FOLDER, exist_ok=True)

#-------------------------------------------------------
# HELPER FUNCTION: Convert Local path -> SharePoint URL
#-------------------------------------------------------
def local_to_sharepoint(local_path):
    """
    Convert OneDrive local path into a SharePoint URL.
    Adjust base_local and base_sharepoint if your OneDrive/SharePoint root differs.
    """
    #Change these if your OneDrive root is different
    base_local = r"C:\Users\1000329829\OneDrive - Western Digital"
    base_sharepoint = "https://sharedspace-my.sharepoint.com/:f:/r/personal/deveepria_sankaran_wdc_com/Documents/RE_LAB_PROCEDURE?csf=1&web=1&e=OymaqI"

    #Normalize paths for safe startswith check
    norm_local = os.path.normpath(local_path)
    norm_base_local = os.path.normpath(base_local)

    if norm_local.startswith(norm_base_local):
        # Replace the base local segment with sharepoint url and convert backslashes to slashes
        rel = norm_local[len(norm_base_local):].lstrip(r"\\/") #relative path after base_local
        url = base_sharepoint.rstrip("/") + "/" + rel.replace("\\", "/")
        return url
    return local_path

#------------------------------------------------------
# JSON READ/WRITE
#------------------------------------------------------
def read_json(file_path):
    if not os.path.exists(file_path):
        return []   # Return empty list if the file does not exist
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

    
def write_json(file_path, data):
    temp_file = file_path + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    os.replace(temp_file, file_path)

#-----------------------------------------------------
# TEST MANAGEMENT
#----------------------------------------------------
def load_tests():
    return read_json(TESTS_FILE)

def add_test(test_name):
    if not test_name:
        return
    tests = load_tests()
    # If tests.json stores list of names keep that behavior
    if test_name not in tests:
        tests.append(test_name)
        write_json(TESTS_FILE, tests)
        proc_file = os.path.join(PROCEDURES_FOLDER, f"{test_name}_procedures.json")
        write_json(proc_file, [])

def delete_test(test_name):
    tests = load_tests()
    if test_name in tests:
        tests.remove(test_name)
        write_json(TESTS_FILE, tests)
        proc_file = os.path.join(PROCEDURES_FOLDER, f"{test_name}_procedures.json")
        if os.path.exists(proc_file):
            os.remove(proc_file)

#--------------------------------------------------
# PROCEDURE MANAGEMENT
#-------------------------------------------------
def load_procedures(test_name):
    proc_file = os.path.join(PROCEDURES_FOLDER, f"{test_name}_procedures.json")
    return read_json(proc_file)

def add_procedure(test_name, procedure_text, procedure_link=""):
    if not test_name or not procedure_text:
        return
    proc_file = os.path.join(PROCEDURES_FOLDER, f"{test_name}_procedure.json")
    procedures = read_json(proc_file) or []
    #store procedure as dict with 'text' and 'link' (link may be string or dict)
    procedures.append({"text": procedure_text, "link": procedure_link})
    write_json(proc_file, procedures)

def delete_procedure(test_name, index):
    proc_file = os.path.join(PROCEDURES_FOLDER, f"{test_name}_procedures.json")
    procedures = read_json(proc_file) or []
    if 0 <= index < len(procedures):
        procedures.pop(index)
        write_json(proc_file, procedures)

def edit_procedure(test_name, index, new_text=None, new_link=None):
    proc_file = os.path.join(PROCEDURES_FOLDER, f"{test_name}_procedures.json")
    procedures = read_json(proc_file) or []
    if 0 <= index < len(procedures):
        if new_text is not None:
            procedures[index]["text"] = new_text
        if new_link is not None:
            procedures[index]["link"] = new_link
        write_json(proc_file, procedures)

#-------------------------------------------------
# STREAMLIT DASHBOARD
#-------------------------------------------------
st.set_page_config(page_title="RE Lab Test Procedures", layout="wide")


#Custom CSS for professional styling
st.markdown("""
<style>
/* Header bar */
.header-bar {
    background-color: #4B8BBE;
    color: white;
    padding: 12px;
    text-align: center;
    font-size: 28px;
    font-weight: bold;
    border-radius: 8px;
    margin-bottom: 15px;
}

/* Procedure table row hover */
.proc-row:hover {
    background-color: #f0f8ff;
}

/* Alternate row colors */
.proc-row:nth-child(even) {
    background-color: #f9f9f9;
}
.proc-row:nth-child(odd) {
    background-color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-bar">RE Lab Test Procedures</div>', unsafe_allow_html=True)

#Track Last procedures for highlights
if "last_procs" not in st.session_state:
    st.session_state.last_procs = {}

#------------------SIDEBAR: Tests & Actions-----------------
with st.sidebar:
    st.subheader("🔹 Tests Management")
    tests = load_tests()
    #handle empty tests list gracefully
    selected_test = st.selectbox("Select Test", options=tests if tests else ["<No tests yet>"])
    if selected_test == "<No tests yet>":
        selected_test = None

    with st.expander("➕ Add New Test"):
        new_test_name = st.text_input("Test Name")
        if st.button("Add Test", key="add_test"):
            add_test(new_test_name)
            st.session_state["refresh_needed"] = True
            #st.experimental_rerun()

    with st.expander("🗑️ Delete Test"):
        if selected_test:
            if st.button(f"Delete '{selected_test}' Test", key="del_test"):
                delete_test(selected_test)
                st.experimental_rerun()

    st.markdown("---")
    st.subheader("🔹 Procedure Actions")

    #Add Procedure
    with st.expander("➕ Add Procedure"):
        new_proc = st.text_input("Procedure Description")
        new_link = st.text_input("Procedure Link (URL, SharePoint, etc.)")
        uploaded_file = st.file_uploader("Or upload a file", type=["pdf", "docx", "doc"], key="add_upload")

        if st.button("Add Procedure", key="add_proc") and selected_test and new_proc:
            link_to_save = new_link
            if uploaded_file is not None:
                # Save file into TestProcedures folder with test prefix to avoid name collisions
                save_name = f"{selected_test}_{uploaded_file.name}"
                save_path = os.path.join(PROCEDURES_FOLDER, save_name)
                #ensure folder exists
                os.makedirs(PROCEDURES_FOLDER, exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                # store as dict so we can keep both local path (for download) and SharePoint URL   
                link_to_save = {
                    "type": "file",
                    "path": save_path,
                    "name": uploaded_file.name,
                    "url": local_to_sharepoint(save_path)
                }
            add_procedure(selected_test, new_proc, link_to_save)
            st.experimental_rerun()

    #Edit Procedure
    with st.expander("✏️ Edit Procedure"):
        procedures = load_procedures(selected_test) if selected_test else []
        if procedures:
            proc_options = [p["text"] if isinstance(p, dict) else str(p) for p in procedures]
            proc_to_edit = st.selectbox("Select procedure to edit", proc_options, key="proc_to_edit")
            if proc_to_edit:
                idx = proc_options.index(proc_to_edit)
                current_proc = procedures[idx]

                current_text = current_proc.get("text", "") if isinstance(current_proc, dict) else current_proc
                current_link = ""
                if isinstance(current_proc, dict):
                    if isinstance(current_proc.get("link"), str):
                        current_link = current_proc.get("link", "")
                    elif isinstance(current_proc.get("link"), dict):
                        current_link = current_proc.get("link").get("url", "") or current_proc.get("link").get("path", "")

                new_text = st.text_input("Update Description", value=current_text)
                new_link = st.text_input("Update Link (URL, SharePoint, etc.)", value=current_link)
                uploaded_file = st.file_uploader("Or upload new file", type=["pdf", "docx", "doc"], key="edit_file")

                if st.button("Save Changes", key="save_edit"):
                    link_to_save = new_link
                    if uploaded_file is not None:
                        save_name = f"{selected_test}_{uploaded_file.name}"
                        save_path = os.path.join(PROCEDURES_FOLDER, save_name)
                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        link_to_save = {
                            "type": "file",
                            "path": save_path,
                            "name": uploaded_file.name,
                            "url": local_to_sharepoint(save_path)
                        }
                    # If user provided only a URL in new_link, keep it as a string
                    edit_procedure(selected_test, idx, new_text, link_to_save)
                    st.success("Procedure updated successfully ✅")
                    st.experimental_rerun()

    #Delete Procedure
    with st.expander("🗑️ Delete Procedure"):
        procedures = load_procedures(selected_test) if selected_test else []
        if procedures:
            proc_options = [p["text"] if isinstance(p, dict) else str(p) for p in procedures]
            del_proc = st.selectbox("Select procedure to delete", proc_options, key="del_proc")
            if st.button("Delete Procedure", key="del_proc_btn"):
                idx = proc_options.index(del_proc)
                delete_procedure(selected_test, idx)
                st.experimental_rerun()

    with st.expander("ℹ️ Instructions"):
        st.markdown("""
        **How to use this dashboard:**
        1. Select or add a test.
        2. Add procedures with description + link or file.
        3. Edit or delete procedures when needed.
        4. Use the download button for attached files.
        5. New procedures from other users are highlighted automatically.
        """)

#-------MAIN AREA: Procedures Table------------
st.subheader(f"Procedures for: {selected_test if selected_test else 'None'}")
procedures = load_procedures(selected_test) if selected_test else []
old_procs = st.session_state.last_procs.get(selected_test, [])

if procedures:
    for idx, proc in enumerate(procedures):
        col1, col2 = st.columns([4, 2])
        row_class = "proc-row"

        text = proc.get("text", "") if isinstance(proc, dict) else proc
        link = proc.get("link", "") if isinstance(proc, dict) else ""

        # Highlight new
        if proc not in old_procs:
            col1.markdown(f"<span style='background-color: #fff176; padding:2px; border-radius:4px;'>{text} 🔔</span>", unsafe_allow_html=True)
        else:
            col1.markdown(f"<div class='{row_class}'>{text}</div>", unsafe_allow_html=True)

        # Show file download or link
        if isinstance(link, dict) and link.get("type") == "file":
            file_path = link.get("path")
            file_name = link.get("name", "file")
            share_url = link.get("url")
            if file_path and os.path.exists(file_path):
                # Send file bytes to user via download_button (works irrespective of user's access to your server filesystem)
                with open(file_path, "rb") as f:
                    col2.download_button(
                        label=f"⬇️ Download {file_name}",
                        data=f,
                        file_name=file_name
                    )
                # also show SharePoint link next to it
                if share_url:
                    col2.markdown(f"[🔗 Open in SharePoint]({share_url})", unsafe_allow_html=True)
            else:
                # File missing locally — still show SharePoint link if available
                if share_url:
                    col2.markdown(f"[🔗 Open in SharePoint]({share_url})", unsafe_allow_html=True)
                else:
                    col2.write("⚠️ File missing")
        elif isinstance(link, str) and link:
            # simple URL string (external link)
            col2.markdown(f"[📎 Open Link]({link})", unsafe_allow_html=True)
        else:
            col2.write("N/A")
else:
    st.info("No procedures available for this test.")

# Update session state (only if a test is selected)
if selected_test:
    st.session_state.last_procs[selected_test] = procedures

if st.session_state.get("refresh_needed", False):
    st.session_state["refresh_needed"] = False
    st.experimental_rerun()

#--------Auto-refresh every 5s---------------------
st_autorefresh(interval=5000, key="refresh")