import streamlit as st
import sqlite3
import os
from reportlab.pdfgen import canvas

# Σύνδεση με βάση δεδομένων SQLite
conn = sqlite3.connect("tasks.db")
cursor = conn.cursor()

# Δημιουργία πίνακα αν δεν υπάρχει
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT,
    month TEXT,
    date TEXT,
    task TEXT,
    completed INTEGER
)
""")
conn.commit()

# Αποθήκευση νέας εργασίας
def save_task(user_name, month, date, task):
    cursor.execute("INSERT INTO tasks (user_name, month, date, task, completed) VALUES (?, ?, ?, ?, ?)",
                   (user_name, month, date, task, 0))
    conn.commit()

# Ανάκτηση εργασιών
def get_tasks(user_name, month):
    cursor.execute("SELECT id, date, task, completed FROM tasks WHERE user_name = ? AND month = ?", (user_name, month))
    return cursor.fetchall()

# Ενημέρωση ολοκλήρωσης
def update_task_status(task_id, status):
    cursor.execute("UPDATE tasks SET completed = ? WHERE id = ?", (status, task_id))
    conn.commit()

# Ρύθμιση της εφαρμογής Streamlit
st.set_page_config(
    page_title="Προγραμματισμός Ενεργειών",
    page_icon="📋",
    layout="wide"
)

# Εισαγωγή ονόματος χρήστη
if "user_name" not in st.session_state:
    with st.form("user_form"):
        user_name = st.text_input("Παρακαλώ εισάγετε το όνομά σας:")
        submitted = st.form_submit_button("Υποβολή")
        if submitted and user_name:
            st.session_state.user_name = user_name
            st.rerun()

# Αν δεν έχει καταχωρηθεί όνομα, σταματάμε εδώ
if "user_name" not in st.session_state:
    st.stop()

st.title(f"📋 Προγραμματισμός Ενεργειών - {st.session_state.user_name}")
st.subheader("Παρακολούθηση Μηνιαίων Εργασιών")

# Επιλογή μήνα
months = ["Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος",
          "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"]
selected_month = st.selectbox("Επιλέξτε Μήνα:", months)

# Εμφάνιση εργασιών
tasks = get_tasks(st.session_state.user_name, selected_month)

for task_id, date, task, completed in tasks:
    task_key = f"{selected_month}_{task_id}"
    if st.checkbox(f"**{date}** {task}" if date else task, key=task_key, value=completed):
        update_task_status(task_id, 1)
    else:
        update_task_status(task_id, 0)

# Υπολογισμός ποσοστού προόδου
total_tasks = len(tasks)
completed_tasks = sum(1 for task in tasks if task[3] == 1)  # Αν completed == 1, σημαίνει ότι είναι ολοκληρωμένο
progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
st.progress(progress / 100)
st.write(f"Πρόοδος: {progress:.1f}%")

# Φόρμα προσθήκης εργασίας
with st.form("task_form"):
    task_date = st.text_input("Ημερομηνία (προαιρετικό):")
    task_text = st.text_area("Περιγραφή εργασίας:")
    submitted = st.form_submit_button("Προσθήκη")
    if submitted and task_text:
        save_task(st.session_state.user_name, selected_month, task_date, task_text)
        st.rerun()

# Δημιουργία PDF και Άνοιγμα παραθύρου εκτύπωσης
def save_pdf(user_name, tasks, filename="tasks.pdf"):
    c = canvas.Canvas(filename)
    c.setFont("Helvetica", 14)
    c.drawString(100, 800, f"Εργασίες για {user_name}")

    y_position = 780
    for date, task, completed in tasks:
        status = "✓" if completed else "✗"
        c.drawString(100, y_position, f"{date} - {task} ({status})")
        y_position -= 20

    c.save()

# Κουμπί εκτύπωσης
if st.button("🖨️ Εκτύπωση"):
    save_pdf(st.session_state.user_name, tasks)  # Δημιουργία PDF
    os.startfile("tasks.pdf", "print")  # Άνοιγμα παραθύρου εκτύπωσης στα Windows

# Υποσημείωση
st.markdown("---")
st.markdown("*Σύστημα Παρακολούθησης Εργασιών*")
