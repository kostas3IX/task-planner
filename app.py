import streamlit as st
import sqlite3
import pandas as pd
from reportlab.pdfgen import canvas

# 📌 Σύνδεση με βάση δεδομένων SQLite
conn = sqlite3.connect("tasks.db")
cursor = conn.cursor()

# 📌 Δημιουργία πίνακα αν δεν υπάρχει
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

# 📌 Προεπιλεγμένες εργασίες ανά μήνα
default_tasks = {
    "Σεπτέμβριος": [
        ("1/9", "Πράξη ανάληψης υπηρεσίας"),
        ("1-5/9", "Προγραμματισμός αγιασμού - ενημέρωση γονέων - ανάρτηση στην ιστοσελίδα"),
        ("έως 10/9", "Πρακτικά: Ανάθεση τμημάτων, Εφημερίες, Εξωδιδακτικές αρμοδιότητες"),
    ],
    "Οκτώβριος": [
        ("1/10", "Επιβεβαίωση Δεδομένων Myschool"),
        ("4/10", "Παγκόσμια ημέρα των ζώων"),
        ("5/10", "Παγκόσμια Ημέρα Εκπαιδευτικών"),
    ],
    # Προσθήκη αντίστοιχων tasks για κάθε μήνα
}

# 📌 Ανάκτηση εργασιών από τη βάση δεδομένων
def get_tasks_from_db(month):
    cursor.execute("SELECT id, date, title, task, completed FROM tasks WHERE user_name = ? AND month = ?", 
                   (st.session_state.user_name, month))
    return cursor.fetchall()

# 📌 Αρχικοποίηση της εφαρμογής
if "user_name" not in st.session_state:
    st.session_state.user_name = "Κώστας"  

# 📌 Ρύθμιση Streamlit UI
st.set_page_config(page_title="Προγραμματισμός Ενεργειών", page_icon="📋", layout="wide")

# 📌 Κεφαλίδα
st.markdown(f"## 👋 Γεια σου, {st.session_state.user_name}!")
st.markdown("### 📋 Παρακολούθηση Μηνιαίων Εργασιών")

# 📌 Επιλογή μήνα
months = list(default_tasks.keys())
selected_month = st.selectbox("📅 Επιλέξτε Μήνα:", months)

# 📌 Ανάκτηση εργασιών από τη βάση
tasks = get_tasks_from_db(selected_month)

# 📌 Προσθήκη προεπιλεγμένων εργασιών αν δεν υπάρχουν
if not tasks:
    for date, title in default_tasks.get(selected_month, []):
        cursor.execute("INSERT INTO tasks (user_name, month, date, title, task, completed) VALUES (?, ?, ?, ?, ?, ?)",
                       (st.session_state.user_name, selected_month, date, title, "", 0))
    conn.commit()
    tasks = get_tasks_from_db(selected_month)

# 📌 Μπάρα προόδου
completed_tasks = sum(task[4] for task in tasks)
progress = (completed_tasks / len(tasks)) * 100 if tasks else 0
st.progress(progress / 100)

# 📌 Εμφάνιση εργασιών με τσεκάρισμα
st.markdown("### 📌 Λίστα εργασιών")
for task_id, date, title, task, completed in tasks:
    task_key = f"{selected_month}_{task_id}"
    col1, col2 = st.columns([1, 4])

    with col1:
        if st.checkbox("", key=task_key, value=bool(completed)):
            cursor.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
        else:
            cursor.execute("UPDATE tasks SET completed = 0 WHERE id = ?", (task_id,))
        conn.commit()

    with col2:
        tag_color = "🟢" if completed else "🔴"
        st.markdown(f"**{date} | {title}** {tag_color}")

st.markdown("---")
st.markdown("*Σύστημα Παρακολούθησης Εργασιών Διευθυντή*")
