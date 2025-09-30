import streamlit as st
from github import Github
import json

#--------------------------------------------
# CONFIGURATION - GitHub connection
#-------------------------------------------
GITHUB_TOKEN = "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"
REPO_NAME = "PNRELAB/RE_LAB_PROCEDURE" #replace with your GitHub repo
PROCEDURES_FOLDER = "TestProcedures"  #folder inside repo to store procedures

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

#--------------------------------------------
# GITHUB JSON READ/WRITE
#---------------------------------------------
def read_json_from_github(file_path):
    try:
        contents = repo.get_contents(file_path)
        return json.loads(contents.decoded_content.decode())
    except:
        return []  #return empty if file doesn't exist
    
def write_json_to_github(file_path, data, commit_message="Update from Streamlit"):
    try:
        contents = repo.get_contents(file_path)
        repo.update_file(contents.path, commit_message, json.dumps(data, indent=4), contents.sha)
    except:
        repo.create_file(file_path, commit_message, json.dumps(data, indent=4))

#-------------------------------------------
# TEST MANAGEMENT
#--------------------------------------------
def load_tests():
    return read_json_from_github("tests.json")

def add_test(test_name):
    if not test_name:
        return
    tests = load_tests()
    if test_name not in tests:
        tests.append(test_name)
        write_json_to_github("tests.json", tests)
        proc_file = f"{PROCEDURES_FOLDER}/{test_name}_procedures.json"
        write_json_to_github(proc_file, [])

def delete_test(test_name):
    tests = load_tests()
    if test_name in tests:
        tests.remove(test_name)
        write_json_to_github("tests.json", tests)
        proc_file = f"{PROCEDURES_FOLDER}/{test_name}_procedures.json"
        try:
            file_content = repo.get_contents(proc_file)
            repo.delete_file(file_content.path, f"Delete {proc_file}", file_content.sha)
        except:
            pass

#---------------------------------------------
# PROCEDURE MANAGEMENT
#---------------------------------------------
def load_procedures(test_name):
    proc_file = f"{PROCEDURES_FOLDER}/{test_name}_procedures.json"
    return read_json_from_github(proc_file)

def add_procedure(test_name, procedure_text, procedure_link=""):
    if not test_name or not procedure_text:
        return
    proc_file = f"{PROCEDURES_FOLDER}/{test_name}_procedures.json"
    procedures = read_json_from_github(proc_file) or []
    procedures.append({"text": procedure_text, "link": procedure_link})
    write_json_to_github(proc_file, procedures)

def delete_procedure(test_name, index):
    proc_file = f"{PROCEDURES_FOLDER}/{test_name}_procedures.json"
    procedures = read_json_from_github(proc_file) or []
    if 0 <= index < len(procedures):
        procedures.pop(index)
        write_json_to_github(proc_file, procedures)

def edit_procedure(test_name, index, new_text=None, new_link=None):
    proc_file = f"{PROCEDURES_FOLDER}/{test_name}_procedures.json"
    procedures = read_json_from_github(proc_file) or []
    if 0 <= index < len(procedures):
        if new_text is not None:
            procedures[index]["text"] = new_text
        if new_link is not None:
            procedures[index]["link"] = new_link
        write_json_to_github(proc_file, procedures)

#-------------------------------------------------
# STREAMLIT DASHBOARD
#-------------------------------------------------
st.set_page_config(page_title="RE Lab Test Procedures", layout="wide")
st.markdown("""
<style>
.header-bar { background-color: #4B8BBE; color: white; padding: 12px; text-align: center; font-size: 28px; font-weight: bold; border-radius: 8px; margin-bottom: 15px; }
.proc-row:hover { background-color: #f0f8ff; }
.proc-row:nth-child(even) { background-color: #f9f9f9; }
.proc-row:nth-child(odd) { background-color: #ffffff; }
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="header-bar">RE Lab Test Procedures</div>', unsafe_allow_html=True)

if "last_procs" not in st.session_state:
    st.session_state.last_procs = {}

#------------------SIDEBAR-----------------
with st.sidebar:
    st.subheader("🔹 Tests Management")
    tests = load_tests()
    selected_test = st.selectbox("Select Test", options=tests if tests else ["<No tests yet>"])
    if selected_test == "<No tests yet>":
        selected_test = None

    with st.expander("➕ Add New Test"):
        new_test_name = st.text_input("Test Name")
        if st.button("Add Test", key="add_test"):
            add_test(new_test_name)
            st.session_state["refresh_needed"] = True

    with st.expander("🗑️ Delete Test"):
        if selected_test:
            if st.button(f"Delete '{selected_test}' Test", key="del_test"):
                delete_test(selected_test)
                st.session_state["refresh_needed"] = True

    st.markdown("---")
    st.subheader("🔹 Procedure Actions")

    with st.expander("➕ Add Procedure"):
        new_proc = st.text_input("Procedure Description")
        new_link = st.text_input("Procedure Link (URL, SharePoint, etc.)")
        uploaded_file = st.file_uploader("Or upload a file", type=["pdf","docx","doc"], key="add_upload")

        if st.button("Add Procedure", key="add_proc") and selected_test and new_proc:
            link_to_save = new_link
            add_procedure(selected_test, new_proc, link_to_save)
            st.session_state["refresh_needed"] = True

    with st.expander("✏️ Edit Procedure"):
        procedures = load_procedures(selected_test) if selected_test else []
        if procedures:
            proc_options = [p["text"] if isinstance(p, dict) else str(p) for p in procedures]
            proc_to_edit = st.selectbox("Select procedure to edit", proc_options, key="proc_to_edit")
            if proc_to_edit:
                idx = proc_options.index(proc_to_edit)
                current_proc = procedures[idx]
                current_text = current_proc.get("text","") if isinstance(current_proc, dict) else current_proc
                current_link = current_proc.get("link","") if isinstance(current_proc, dict) else ""

                new_text = st.text_input("Update Description", value=current_text)
                new_link = st.text_input("Update Link (URL, SharePoint, etc.)", value=current_link)

                if st.button("Save Changes", key="save_edit"):
                    edit_procedure(selected_test, idx, new_text, new_link)
                    st.success("Procedure updated successfully ✅")
                    st.session_state["refresh_needed"] = True

    with st.expander("🗑️ Delete Procedure"):
        procedures = load_procedures(selected_test) if selected_test else []
        if procedures:
            proc_options = [p["text"] if isinstance(p, dict) else str(p) for p in procedures]
            del_proc = st.selectbox("Select procedure to delete", proc_options, key="del_proc")
            idx_del = proc_options.index(del_proc) if del_proc else None
            if st.button("Delete Procedure", key="del_proc_btn") and idx_del is not None:
                delete_procedure(selected_test, idx_del)
                st.session_state["refresh_needed"] = True

    with st.expander("ℹ️ Instructions"):
        st.markdown("""
        **How to use this dashboard:**
        1. Select or add a test.
        2. Add procedures with description + link or file.
        3. Edit or delete procedures when needed.
        4. New procedures from other users are highlighted automatically.
        """)

#-------MAIN AREA: Procedures Table------------
st.subheader(f"Procedures for: {selected_test if selected_test else 'None'}")
procedures = load_procedures(selected_test) if selected_test else []
old_procs = st.session_state.last_procs.get(selected_test, [])

if procedures:
    for idx, proc in enumerate(procedures):
        col1, col2 = st.columns([4,2])
        row_class = "proc-row"
        text = proc.get("text","") if isinstance(proc, dict) else proc
        link = proc.get("link","") if isinstance(proc, dict) else ""

        if proc not in old_procs:
            col1.markdown(f"<span style='background-color: #fff176; padding:2px; border-radius:4px;'>{text} 🔔</span>", unsafe_allow_html=True)
        else:
            col1.markdown(f"<div class='{row_class}'>{text}</div>", unsafe_allow_html=True)

        if isinstance(link, str) and link:
            col2.markdown(f"[📎 Open Link]({link})", unsafe_allow_html=True)
        else:
            col2.write("N/A")

if selected_test:
    st.session_state.last_procs[selected_test] = procedures

#--------Auto-refresh every 5s---------------------
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=5000, key="refresh")