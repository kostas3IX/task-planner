import streamlit as st
import sqlite3
from reportlab.pdfgen import canvas  # Make sure reportlab is installed (`pip install reportlab`)

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
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .task-container:hover {
        transform: translateY(-2px);
    }
    .task-title {
        color: #2c3e50;
        font-weight: 600;
        font-size: 1.1em;
    }
    .task-date {
        color: #7f8c8d;
        font-size: 0.9em;
    }
    .task-status {
        font-size: 1.2em;
    }
    .progress-container {
        margin: 20px 0;
        text-align: center;
    }
    .stProgress > div > div {
        background-color: #3498db;
    }
    .stButton > button {
        background-color: #3498db;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        border: none;
        transition: background-color 0.2s;
    }
    .stButton > button:hover {
        background-color: #2980b9;
    }
</style>
""", unsafe_allow_html=True)

# 📌 Ρύθμιση Streamlit UI
st.set_page_config(
    page_title="Προγραμματισμός Ενεργειών",
    page_icon="📋",
    layout="wide"
)

# 📌 Σύνδεση με βάση δεδομένων SQLite
conn = sqlite3.connect("tasks.db", check_same_thread=False)
cursor = conn.cursor()

# 📌 Δημιουργία πίνακα (χωρίς διαγραφή υπάρχοντος για να αποφευχθεί απώλεια δεδομένων)
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

# 📌 Αρχικοποίηση session state
if "user_name" not in st.session_state:
    st.session_state.user_name = "Κώστας"
    if add_predefined_tasks(st.session_state.user_name):
        st.info("Προσθήκη προκαθορισμένων εργασιών...")

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
st.progress(progress_percentage / 100.0)
st.markdown(f'<div class="progress-container">{completed_tasks}/{total_tasks} εργασίες ({progress_percentage:.0f}%)</div>', unsafe_allow_html=True)

# 📌 Εμφάνιση εργασιών
st.markdown(f"### 📌 Εργασίες {selected_month}")
if not tasks:
    st.info(f"Δεν υπάρχουν εργασίες για τον {selected_month}.")
else:
    for task_id, date, title, task, completed in tasks:
        task_key = f"task_{task_id}_{selected_month}"
        with st.container():
            st.markdown('<div class="task-container">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns([0.5, 6, 0.5])
            with col1:
                is_completed = completed == 1
                st.checkbox("", key=task_key, value=is_completed, on_change=lambda tid=task_id, state=is_completed: cursor.execute("UPDATE tasks SET completed = ? WHERE id = ?", (0 if state else 1, tid)) or conn.commit() or st.rerun())
            with col2:
                tag_color = "🟢" if completed else "🔴"
                display_date = date if date else "Χωρίς Ημ."
                st.markdown(f'<span class="task-title">{title}</span> <span class="task-status">{tag_color}</span>', unsafe_allow_html=True)
                st.markdown(f'<span class="task-date">{display_date}</span>', unsafe_allow_html=True)
                if title != task:
                    st.write(task)
            with col3:
                if st.button("🗑️", key=f"delete_{task_key}"):
                    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                    conn.commit()
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# 📌 Εκτύπωση σε PDF
def save_pdf(user_name):
    pdf_filename = f"{user_name}_all_tasks.pdf"
    c = canvas.Canvas(pdf_filename)
    c.setFont("Helvetica", 12)
    c.drawString(100, 800, f"Προγραμματισμός Ενεργειών για {user_name}")
    c.setFont("Helvetica", 10)
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
                y = 800
            c.setFont("Helvetica-Bold", 12)
            c.drawString(100, y, month_pdf)
            c.setFont("Helvetica", 10)
            y -= 15
        date_str_pdf = date_pdf if date_pdf else "Χωρίς Ημ."
        completed_status_pdf = "✓" if completed_pdf else "✗"
        task_line = f"{date_str_pdf}: {title_pdf} ({completed_status_pdf})"
        max_width = 450
        lines = []
        current_line = ""
        words = task_line.split(' ')
        for word in words:
            if current_line and c.stringWidth(current_line + " " + word) > max_width:
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
                c.setFont("Helvetica", 10)
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
