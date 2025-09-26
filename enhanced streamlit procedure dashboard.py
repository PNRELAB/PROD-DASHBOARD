import streamlit as st
import os
import json
from pathlib import Path
from streamlit_autorefresh import st_autorefresh

#---------------------------------------------
# CONFIGURATION
#---------------------------------------------
SHARED_FOLDER = r"\\mpl-op-genmp01.wdc.com\PN-RELAB\RE Ctrl Nasuni\Digitalization"
TESTS_FILE = os.path.join(SHARED_FOLDER, "tests.json")
PROCEDURES_FOLDER = os.path.join(SHARED_FOLDER, "TestProcedures")
os.makedirs(PROCEDURES_FOLDER, exist_ok=True)

#----------------------------------------------
# JSON READ/WRITE
#----------------------------------------------
def read_json(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def write_json(file_path, data):
    temp_file = file_path + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    os.replace(temp_file, file_path)

#---------------------------------------------
# TEST MANAGEMENT
#---------------------------------------------
def load_tests():
    return read_json(TESTS_FILE)

def add_test(test_name):
    if not test_name:
        return
    tests = load_tests()
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

#--------------------------------------------
# PROCEDURE MANAGEMENT
#--------------------------------------------
def load_procedures(test_name):
    proc_file = os.path.join(PROCEDURES_FOLDER, f"{test_name}_procedures.json")
    return read_json(proc_file)

def add_procedure(test_name, procedure_text):
    if not test_name or not procedure_text:
        return
    proc_file = os.path.join(PROCEDURES_FOLDER, f"{test_name}_procedures.json")
    procedures = read_json(proc_file)
    procedures.append(procedure_text)
    write_json(proc_file, procedures)

def delete_procedure(test_name, index):
    proc_file = os.path.join(PROCEDURES_FOLDER, f"{test_name}_procedures.json")
    procedures = read_json(proc_file)
    if 0 <= index < len(procedures):
        procedures.pop(index)
        write_json(proc_file, procedures)

#--------------------------------------------
# STREAMLIT DASHBOARD
#--------------------------------------------
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

st.markdown('<div class="header-bar">RE Lab Test Procedures Dashboard</div>', unsafe_allow_html=True)

# Track Last procedures for highlights
if "last_procs" not in st.session_state:
    st.session_state.last_procs = {}

#---------SIDEBAR: Tests & Actions-----------
with st.sidebar:
    st.subheader("🔹 Tests Management")
    tests = load_tests()
    selected_test = st.selectbox("Select Test", options=tests)

    with st.expander("➕ Add New Test"):
        new_test_name = st.text_input("Test Name")
        if st.button("Add Test", key="add_test"):
            add_test(new_test_name)
            st.rerun()

    with st.expander("🗑️ Delete Test"):
        if selected_test:
            if st.button(f"Delete '{selected_test}' Test", key="del_test"):
                delete_test(selected_test)
                st.rerun()

    st.markdown("---")
    st.subheader("🔹 Procedure Actions")
    with st.expander("➕ Add Procedure"):
        new_proc = st.text_input("Procedure Description")
        if st.button("Add Procedure", key="add_proc") and selected_test and new_proc:
            add_procedure(selected_test, new_proc)
            st.rerun()

    with st.expander("🗑️ Delete Procedure"):
        procedures = load_procedures(selected_test) if selected_test else []
        if procedures:
            del_proc = st.selectbox("Select procedure to delete", procedures)
            if st.button("Delete Procedure", key="del_proc_btn"):
                delete_procedure(selected_test, procedures.index(del_proc))
                st.rerun()

    with st.expander("ℹ️ Instructions"):
        st.markdown("""
        **How to use this dashboard:**
        1. Select or add a test.
        2. Add procedures using the 'Add Procedure' section.
        3. Delete procedures safely if needed.
        4. Click 'Open' to view any associated PDF/DOC file.
        5. New procedures from other users are highlighted automatically.
        """)

#--------MAIN AREA: Procedures Table-----------
st.subheader(f"Procedures for: {selected_test if selected_test else 'None'}")
procedures = load_procedures(selected_test) if selected_test else []
old_procs = st.session_state.last_procs.get(selected_test, [])

if procedures:
    for idx, proc in enumerate(procedures):
        col1, col2 = st.columns([4, 1])
        row_class = "proc-row"

        # Highlight new
        if proc not in old_procs:
            col1.markdown(f"<span style='background-color: #fff176; padding:2px; border-radius:4px;'>{proc} 🔔</span>", unsafe_allow_html=True)
            # Beep notification
            st.components.v1.html("""
                <script>
                var ctx = new (window.AudioContext || window.webkitAudioContext)();
                var oscillator = ctx.createOscillator();
                oscillator.type = "sine";
                oscillator.frequency.setValueAtTime(600, ctx.currentTime);
                oscillator.connect(ctx.destination);
                oscillator.start();
                oscillator.stop(ctx.currentTime + 0.2);
                </script>
            """, height=0)
        else:
            col1.markdown(f"<div class='{row_class}'>{proc}</div>", unsafe_allow_html=True)

        # Procedure file link
        possible_ext = ['.pdf', '.docx', '.doc']
        file_link = None
        for ext in possible_ext:
            path = os.path.join(PROCEDURES_FOLDER, f"{selected_test}_{proc}{ext}")
            if os.path.exists(path):
                file_link = path
                break

        if file_link:
            col2.markdown(f"[📄 Open]({Path(file_link).as_uri()})", unsafe_allow_html=True)
        else:
            col2.write("N/A")
else:
    st.info("No procedures available for this test.")

# Update session state
st.session_state.last_procs[selected_test] = procedures

#----------Auto-refresh every 5s--------
st_autorefresh(interval=5000, key="refresh")