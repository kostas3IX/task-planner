import streamlit as st
import sqlite3
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# 📌 Ρύθμιση Streamlit UI (πρώτη εντολή Streamlit)
st.set_page_config(
    page_title="Προγραμματισμός Ενεργειών",
    page_icon="📋",
    layout="wide"
)

# 📌 Custom CSS για μοντέρνο και λιτό UI
st.markdown("""
<style>
    .stApp {
        background-color: #f5f7fa;
        font-family: 'Arial', sans-serif;
    }
    .title {
        color: #2c3e50;
        font-size: 2.5em;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5em;
    }
    .subtitle {
        color: #34495e;
        font-size: 1.2em;
        text-align: center;
        margin-bottom: 1em;
    }
    .clock {
        color: #34495e;
        font-size: 1em;
        text-align: center;
        margin-bottom: 2em;
    }
    .month-select {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        max-width: 300px;
        margin: 0 auto;
    }
    .task-container {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .task-container:hover {
        transform: translateY(-2px);
    }
    .task-title {
        color: #2c3e50;
        font-weight: 600;
        font-size: 1.0em;
    }
    .task-date {
        color: #7f8c8d;
        font-size: 0.8em;
    }
    .task-status {
        font-size: 1.0em;
    }
    .progress-container {
        margin: 15px 0;
        text-align: center;
    }
    .stProgress > div > div {
        background-color: #3498db;
    }
    .stButton > button {
        background-color: #3498db;
        color: white;
        border-radius: 8px;
        padding: 5px 10px;
        border: none;
        transition: background-color 0.2s;
        font-size: 0.9em;
    }
    .stButton > button:hover {
        background-color: #2980b9;
    }
    .edit-button {
        background-color: #f39c12;
    }
    .edit-button:hover {
        background-color: #e67e22;
    }
    .check-all-button {
        background-color: #2ecc71;
        margin-right: 10px;
    }
    .check-all-button:hover {
        background-color: #27ae60;
    }
    .uncheck-all-button {
        background-color: #e74c3c;
    }
    .uncheck-all-button:hover {
        background-color: #c0392b;
    }
</style>
""", unsafe_allow_html=True)

# 📌 JavaScript για εμφάνιση και ενημέρωση ώρας
st.markdown("""
<div class="clock" id="clock"></div>
<script>
function updateClock() {
    const now = new Date();
    const options = {
        timeZone: 'Europe/Athens',
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    };
    const formatter = new Intl.DateTimeFormat('el-GR', options);
    const parts = formatter.formatToParts(now);
    const weekday = parts.find(p => p.type === 'weekday').value;
    const day = parts.find(p => p.type === 'day').value;
    const month = parts.find(p => p.type === 'month').value;
    const year = parts.find(p => p.type === 'year').value;
    const hour = parts.find(p => p.type === 'hour').value;
    const minute = parts.find(p => p.type === 'minute').value;
    const second = parts.find(p => p.type === 'second').value;
    document.getElementById('clock').innerText = `${hour}:${minute}:${second} EEST, ${weekday}, ${day} ${month} ${year}`;
}
setInterval(updateClock, 1000);
updateClock();
</script>
""", unsafe_allow_html=True)

# 📌 Σύνδεση με βάση δεδομένων SQLite
conn = sqlite3.connect("tasks.db", check_same_thread=False)
cursor = conn.cursor()

# 📌 Δημιουργία πίνακα
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT,
    month TEXT,
    date TEXT,
    title TEXT,
    task TEXT,
    completed INTEGER
)
""")
conn.commit()

# 📌 Προκαθορισμένες εργασίες ανά μήνα
predefined_tasks = {
    "Σεπτέμβριος": [
        ("1/9", "Πράξη ανάληψης υπηρεσίας"),
        ("1-5/9", "Προγραμματισμός αγιασμού - ενημέρωση γονέων - ανάρτηση στην ιστοσελίδα"),
        ("έως 10/9", "Πρακτικό: Ανάθεση τμημάτων - διδασκαλιών - ολοήμερου - ΠΖ"),
        ("έως 10/9", "Πρακτικό: Διαμόρφωση ομίλων στο αναβαθμισμένο πρόγραμμα ολοημέρου"),
        ("έως 10/9", "Πρακτικό: Εξωδιδακτικές αρμοδιότητες"),
        ("έως 10/9", "Πρακτικό: Ανάθεση σχολικών εορτών, επετείων, ομιλιών"),
        ("έως 10/9", "Πρακτικό: Εφημερίες - ασφάλεια μαθητών"),
        ("έως 10/9", "Πρακτικό: Αναπλήρωση απόντων εκπαιδευτικών"),
        ("έως 10/9", "Πρακτικό: Επιλογή βιβλίων Β’ ξένης γλώσσας"),
        ("έως 10/9", "Εσωτερικός κανονισμός λειτουργίας - επικαιροποίηση"),
        ("έως 10/9", "Σχολικό Συμβούλιο; Κοινή συνεδρίαση συστεγαζόμενων"),
        ("έως 10/9", "Οργάνωση του Myschool"),
        ("11/9", "Ωρολόγιο πρόγραμμα - (έστω προσωρινό)"),
        ("11/9", "Ωρολόγιο πρόγραμμα εξ αποστάσεως"),
        ("11/9", "Αγιασμός. Καλωσόρισμα - υποδοχή γονέων Α’ τάξης"),
        ("12/9", "Αποστολή δηλώσεων στους γονείς για το αναβαθμισμένο ολοήμερο"),
        ("15/9", "Επιβεβαίωση Δεδομένων Myschool"),
        ("έως 20", "Ορισμός συντονιστών"),
        ("έως 20", "Ορισμός μέντορα"),
        ("έως 20", "Προαιρετική Συγκρότηση Εκπαιδευτικών Ομίλων"),
        ("έως 20/9", "Προγραμματισμός συναντήσεων με γονείς"),
        ("έως 30/9", "Ειδική συνεδρίαση για το ετήσιο Σχέδιο Δράσης"),
        ("έως 30/9", "Προγραμματισμός 15ωρων ενδοσχολικών"),
        ("έως 30/9", "Έλεγχος μαθητικών λογαριασμών στο sch.gr"),
        ("έως 30/9", "Προγραμματισμός Α’ τριμήνου"),
        ("έως 30/9", "Διαδικασία ανάθεσης για συμπλήρωση διδακτικού ωραρίου"),
        ("30/9-3/10", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"),
    ],
    "Οκτώβριος": [
        ("1/10", "Επιβεβαίωση Δεδομένων Myschool"),
        (None, "1η παιδαγωγική συνεδρίαση"),
        ("4/10", "Παγκόσμια ημέρα των ζώων"),
        ("5/10", "Παγκόσμια Ημέρα Εκπαιδευτικών"),
        ("έως 10/10", "Μνημόνιο ενεργειών εκτάκτων αναγκών"),
        ("έως 10/10", "Συνεδρίαση για τον Συλλογικό Προγραμματισμό"),
        ("15/10", "Επιβεβαίωση Δεδομένων Myschool"),
        ("έως 20/10", "Καταχώρηση τίτλων & σχεδίων δράσης"),
        ("έως 21/10", "Επιλογή σημαιοφόρων"),
        ("31/10-3/11", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"),
    ],
    "Νοέμβριος": [
        ("1/11", "Επιβεβαίωση Δεδομένων Myschool"),
        (None, "2η παιδαγωγική συνεδρίαση"),
        ("έως 10/11", "Σχολικό Συμβούλιο"),
        ("15/11", "Επιβεβαίωση Δεδομένων Myschool"),
        ("20/11", "Παγκόσμια Ημέρα για τα δικαιώματα του Παιδιού"),
        ("30/11-2/12", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"),
    ],
    "Δεκέμβριος": [
        ("1/12", "Επιβεβαίωση Δεδομένων Myschool"),
        ("3/12", "Παγκόσμια Ημέρα Ατόμων με Αναπηρία"),
        ("έως 10/12", "Καταχώρηση του Σχεδιασμού Δράσης"),
        (None, "3η παιδαγωγική συνεδρίαση"),
        ("10/12", "Λήξη Α’ τριμήνου"),
        (None, "Επίδοση ελέγχων"),
        ("15/12", "Επιβεβαίωση Δεδομένων Myschool"),
        ("23/12-9/1/23", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"),
        ("23/12 έως και 7/1", "Διακοπές Χριστουγέννων"),
    ],
    "Ιανουάριος": [
        ("9/1", "Επιβεβαίωση Δεδομένων Myschool"),
        (None, "4η παιδαγωγική συνεδρίαση"),
        ("έως 15/1", "Σχολικό Συμβούλιο"),
        ("15/1", "Επιβεβαίωση Δεδομένων Myschool"),
        ("31/1-3/2", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"),
    ],
    "Φεβρουάριος": [
        ("1/2", "Επιβεβαίωση Δεδομένων Myschool"),
        (None, "Ημέρα Ασφαλούς Διαδικτύου – Safer Internet Day"),
        (None, "5η παιδαγωγική συνεδρίαση"),
        ("15/2", "Επιβεβαίωση Δεδομένων Myschool"),
        ("28/2-3/3", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"),
    ],
    "Μάρτιος": [
        ("1/3", "Επιβεβαίωση Δεδομένων Myschool"),
        ("έως 10/3", "Σχολικό Συμβούλιο"),
        ("1-20/3", "Εγγραφές-Αποστολή στοιχείων στη ΔΙΠΕ"),
        ("6/3", "Πανελλήνια Ημέρα κατά της σχολικής βίας"),
        (None, "6η παιδαγωγική συνεδρίαση"),
        ("10/3", "Λήξη Β΄ τριμήνου"),
        (None, "Επίδοση ελέγχων"),
        ("15/3", "Επιβεβαίωση Δεδομένων Myschool"),
        ("21/3", "Παγκόσμια Ημέρα Ποίησης"),
        ("31/3-3/4", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"),
    ],
    "Απρίλιος": [
        ("1/4", "Επιβεβαίωση Δεδομένων Myschool"),
        ("2/4", "Παγκόσμια Ημέρα Παιδικού Βιβλίου"),
        (None, "7η παιδαγωγική συνεδρίαση"),
        ("27/4-12/5", "Διακοπές Πάσχα"),
        ("22/4", "Ημέρα της Γης"),
        ("23/4", "Παγκόσμια Ημέρα Βιβλίου"),
        ("24/4", "Επιβεβαίωση Δεδομένων Myschool"),
        ("28/4-3/5", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"),
    ],
    "Μάιος": [
        ("1/5", "Επιβεβαίωση Δεδομένων Myschool"),
        (None, "8η παιδαγωγική συνεδρίαση"),
        ("9/5", "Ημέρα της Ευρώπης"),
        ("15/5", "Επιβεβαίωση Δεδομένων Myschool"),
        ("19/5", "Ημέρα Μνήμης για τη Γενοκτονία των Ελλήνων"),
        (None, "Λήξη ενεργειών προγραμματισμού Ολοήμερου"),
        ("έως 31/5", "Υλοποίηση και καταχώρηση αποτίμησης δράσεων"),
        ("έως 31/5", "Σχολικό Συμβούλιο"),
        ("31/5-2/6", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"),
    ],
    "Ιούνιος": [
        ("1/6", "Επιβεβαίωση Δεδομένων Myschool"),
        (None, "9η παιδαγωγική συνεδρίαση"),
        ("5/6", "Παγκόσμια Ημέρα Περιβάλλοντος"),
        ("15/6", "Λήξη Σχολικού έτους"),
        (None, "Επίδοση τίτλων"),
        ("έως 21/6", "Άνοιγμα νέου σχολικού έτους στο Myschool"),
        ("21/6-23/6", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"),
        ("έως 25/6", "Καταχώρηση Έκθεσης Εσωτερικής Αξιολόγησης"),
        (None, "Δημιουργία νέου σχολικού έτους"),
    ],
    "Ιούλιος": [],
    "Αύγουστος": [],
}

# 📌 Συνάρτηση για την προσθήκη προκαθορισμένων εργασιών
def add_predefined_tasks(user_name):
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_name = ?", (user_name,))
    count = cursor.fetchone()[0]
    if count == 0:
        for month, tasks in predefined_tasks.items():
            for date, task_desc in tasks:
                title = task_desc
                cursor.execute("INSERT INTO tasks (user_name, month, date, title, task, completed) VALUES (?, ?, ?, ?, ?, ?)",
                               (user_name, month, date, title, task_desc, 0))
        conn.commit()
        return True
    return False

# 📌 Ανάκτηση εργασιών από τη βάση δεδομένων
def get_tasks_from_db(user_name, month):
    cursor.execute("SELECT id, date, title, task, completed FROM tasks WHERE user_name = ? AND month = ? ORDER BY date",
                   (user_name, month))
    return cursor.fetchall()

# 📌 Ενημέρωση εργασίας στη βάση δεδομένων (μόνο date και title)
def update_task(task_id, date, title):
    cursor.execute("UPDATE tasks SET date = ?, title = ? WHERE id = ?",
                   (date, title, task_id))
    conn.commit()

# 📌 Ενημέρωση όλων των εργασιών (check/uncheck all)
def check_all_tasks(user_name, month):
    cursor.execute("UPDATE tasks SET completed = 1 WHERE user_name = ? AND month = ?",
                   (user_name, month))
    conn.commit()

def uncheck_all_tasks(user_name, month):
    cursor.execute("UPDATE tasks SET completed = 0 WHERE user_name = ? AND month = ?",
                   (user_name, month))
    conn.commit()

# 📌 Αρχικοποίηση session state
if "user_name" not in st.session_state:
    st.session_state.user_name = "Κώστας"
    if add_predefined_tasks(st.session_state.user_name):
        st.info("Προσθήκη προκαθορισμένων εργασιών...")

if "edit_task_id" not in st.session_state:
    st.session_state.edit_task_id = None

# 📌 Κεφαλίδα
st.markdown('<div class="title">📋 Προγραμματισμός Ενεργειών</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">Γεια σου, {st.session_state.user_name}! Παρακολούθησε τις μηνιαίες σου εργασίες.</div>', unsafe_allow_html=True)

# 📌 Επιλογή μήνα
months = list(predefined_tasks.keys())
with st.container():
    st.markdown('<div class="month-select">', unsafe_allow_html=True)
    selected_month = st.selectbox("📅 Επιλέξτε Μήνα:", months, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

# 📌 Ανάκτηση εργασιών
tasks = get_tasks_from_db(st.session_state.user_name, selected_month)

# 📌 Υπολογισμός προόδου
total_tasks = len(tasks)
completed_tasks = sum(1 for task in tasks if task[4] == 1)
progress_percentage = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0

# 📌 Εμφάνιση προόδου
st.markdown(f'<div class="progress-container"><strong>Πρόοδος {selected_month}</strong></div>', unsafe_allow_html=True)
if total_tasks > 0:
    st.progress(progress_percentage / 100.0)
    st.markdown(f'<div class="progress-container">{completed_tasks}/{total_tasks} εργασίες ({progress_percentage:.0f}%)</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="progress-container">Καμία εργασία για εμφάνιση</div>', unsafe_allow_html=True)

# 📌 Κουμπιά Check All / Uncheck All
if tasks:
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Επιλογή Όλων", key="check_all", help="Επιλέγει όλες τις εργασίες του μήνα"):
                check_all_tasks(st.session_state.user_name, selected_month)
                st.rerun()
        with col2:
            if st.button("❌ Αποεπιλογή Όλων", key="uncheck_all", help="Αποεπιλέγει όλες τις εργασίες του μήνα"):
                uncheck_all_tasks(st.session_state.user_name, selected_month)
                st.rerun()

# 📌 Εμφάνιση εργασιών
st.markdown(f"### 📌 Εργασίες {selected_month}")
if not tasks:
    st.info(f"Δεν υπάρχουν εργασίες για τον {selected_month}.")
else:
    for task_id, date, title, task, completed in tasks:
        task_key = f"task_{task_id}_{selected_month}"
        with st.container():
            st.markdown('<div class="task-container">', unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns([0.5, 5, 0.5, 0.5])
            with col1:
                is_completed = completed == 1
                st.checkbox("", key=task_key, value=is_completed, on_change=lambda tid=task_id, state=is_completed: (
                    cursor.execute("UPDATE tasks SET completed = ? WHERE id = ?", (0 if state else 1, tid)),
                    conn.commit(),
                    st.rerun()
                ))
            with col2:
                tag_color = "🟢" if completed else "🔴"
                display_date = date if date else "Χωρίς Ημ."
                st.markdown(f'<span class="task-title">{title}</span> <span class="task-status">{tag_color}</span>', unsafe_allow_html=True)
                st.markdown(f'<span class="task-date">{display_date}</span>', unsafe_allow_html=True)
                if title != task:
                    st.write(task)
            with col3:
                if st.button("🗑️", key=f"delete_{task_key}", help="Διαγραφή"):
                    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                    conn.commit()
                    st.rerun()
            with col4:
                if st.button("✏️", key=f"edit_{task_key}", help="Επεξεργασία εργασίας"):
                    st.session_state.edit_task_id = task_id
            st.markdown('</div>', unsafe_allow_html=True)

# 📌 Φόρμα επεξεργασίας εργασίας (μόνο ημερομηνία και τίτλος)
if st.session_state.edit_task_id is not None:
    task_id = st.session_state.edit_task_id
    cursor.execute("SELECT date, title FROM tasks WHERE id = ?", (task_id,))
    task_data = cursor.fetchone()
    if task_data:
        st.markdown("### ✏️ Επεξεργασία Εργασίας")
        with st.form(f"edit_task_form_{task_id}", clear_on_submit=True):
            edit_date = st.text_input("📅 Ημερομηνία (π.χ. 15/9, έως 20/9):", value=task_data[0] or "", key=f"edit_date_{task_id}")
            edit_title = st.text_input("📌 Τίτλος Εργασίας:", value=task_data[1], key=f"edit_title_{task_id}")
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ Αποθήκευση"):
                    update_task(task_id, edit_date, edit_title)
                    st.session_state.edit_task_id = None
                    st.success("Η εργασία ενημερώθηκε επιτυχώς!")
                    st.rerun()
            with col2:
                if st.form_submit_button("❌ Ακύρωση"):
                    st.session_state.edit_task_id = None
                    st.rerun()

# 📌 Εκτύπωση σε PDF με υποστήριξη ελληνικών χαρακτήρων
def save_pdf(user_name):
    pdf_filename = f"{user_name}_all_tasks.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=A4)

    # Εγγραφή γραμματοσειράς DejaVuSans για ελληνικούς χαρακτήρες
    font_path = "/tmp/DejaVuSans.ttf"
    if not os.path.exists(font_path):
        import urllib.request
        url = "https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version-2.37/dejavu-fonts-ttf-2.37.tar.bz2"
        urllib.request.urlretrieve(url, "/tmp/dejavu-fonts.tar.bz2")
        import tarfile
        with tarfile.open("/tmp/dejavu-fonts.tar.bz2", "r:bz2") as tar:
            tar.extract("dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf", path="/tmp")
        os.rename("/tmp/dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf", font_path)

    pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
    c.setFont("DejaVuSans", 12)
    c.drawString(100, 800, f"Προγραμματισμός Ενεργειών για {user_name}")
    c.setFont("DejaVuSans", 10)

    cursor.execute("SELECT month, date, title, task, completed FROM tasks WHERE user_name = ? ORDER BY CASE month WHEN 'Σεπτέμβριος' THEN 1 WHEN 'Οκτώβριος' THEN 2 WHEN 'Νοέμβριος' THEN 3 WHEN 'Δεκέμβριος' THEN 4 WHEN 'Ιανουάριος' THEN 5 WHEN 'Φεβρουάριος' THEN 6 WHEN 'Μάρτιος' THEN 7 WHEN 'Απρίλιος' THEN 8 WHEN 'Μάιος' THEN 9 WHEN 'Ιούνιος' THEN 10 WHEN 'Ιούλιος' THEN 11 WHEN 'Αύγουστος' THEN 12 END, date", (user_name,))
    all_user_tasks_ordered = cursor.fetchall()
    y = 780
    current_month_pdf = None
    for month_pdf, date_pdf, title_pdf, task_pdf, completed_pdf in all_user_tasks_ordered:
        if month_pdf != current_month_pdf:
            current_month_pdf = month_pdf
            y -= 30
            if y < 50:
                c.showPage()
                c.setFont("DejaVuSans", 10)
                y = 800
            c.setFont("DejaVuSans", 12)
            c.drawString(100, y, month_pdf)
            c.setFont("DejaVuSans", 10)
            y -= 15
        date_str_pdf = date_pdf if date_pdf else "Χωρίς Ημ."
        completed_status_pdf = "✓" if completed_pdf else "✗"
        task_line = f"{date_str_pdf}: {title_pdf} ({completed_status_pdf})"
        max_width = 450
        lines = []
        current_line = ""
        words = task_line.split(' ')
        for word in words:
            if current_line and c.stringWidth(current_line + " " + word, "DejaVuSans", 10) > max_width:
                lines.append(current_line)
                current_line = word
            else:
                current_line = (current_line + " " + word).strip()
        if current_line:
            lines.append(current_line)
        for line in lines:
            y -= 15
            if y < 50:
                c.showPage()
                c.setFont("DejaVuSans", 10)
                y = 800
            c.drawString(110, y, line)
    c.save()
    return pdf_filename

if st.button("🖨️ Εξαγωγή σε PDF"):
    pdf_file = save_pdf(st.session_state.user_name)
    with open(pdf_file, "rb") as f:
        st.download_button("📄 Λήψη PDF", f, pdf_file, "application/pdf")

st.markdown("---")
st.markdown("*Σύστημα Παρακολούθησης Εργασιών Διευθυντή*")
