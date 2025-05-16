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

# 📌 Ανάκτηση εργασιών από τη βάση δεδομένων
def get_tasks_from_db(month):
    cursor.execute("SELECT id, date, title, task, completed FROM tasks WHERE user_name = ? AND month = ?", 
                   (st.session_state.user_name, month))
    return cursor.fetchall()

# 📌 Αρχικοποίηση της εφαρμογής
if "user_name" not in st.session_state:
    st.session_state.user_name = "Κώστας"

# 📌 Ρύθμιση Streamlit UI
st.set_page_config(
    page_title="Προγραμματισμός Ενεργειών",
    page_icon="📋",
    layout="wide"
)

# 📌 Κεφαλίδα
st.markdown(f"## 👋 Γεια σου, {st.session_state.user_name}!")
st.markdown("### 📋 Προγραμματισμός ενεργειών διευθυντή")
st.write("**Παρακολούθηση Μηνιαίων Εργασιών**")

# 📌 Επιλογή μήνα
months = ["Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος",
          "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"]
selected_month = st.selectbox("📅 Επιλέξτε Μήνα:", months)

# 📌 Εισαγωγή εργασιών Σεπτεμβρίου αν δεν υπάρχουν ήδη
september_tasks = [
    ("1/9", "Πράξη ανάληψης υπηρεσίας", "Διαδικασία ανάληψης υπηρεσίας"),
    ("1-5/9", "Προγραμματισμός αγιασμού", "Ενημέρωση γονέων, ανάρτηση στην ιστοσελίδα"),
    ("έως 10/9", "Πρακτικό: Ανάθεση τμημάτων", "Διδασκαλιών, ολοήμερου, ΠΖ"),
    ("έως 10/9", "Πρακτικό: Διαμόρφωση ομίλων", "Προτάσεις από τους διδάσκοντες"),
    ("έως 10/9", "Πρακτικό: Εξωδιδακτικές αρμοδιότητες", ""),
    ("έως 10/9", "Πρακτικό: Ανάθεση σχολικών εορτών", ""),
    ("έως 10/9", "Πρακτικό: Εφημερίες - ασφάλεια μαθητών", ""),
    ("έως 10/9", "Πρακτικό: Αναπλήρωση απόντων εκπαιδευτικών", ""),
    ("έως 10/9", "Πρακτικό: Επιλογή βιβλίων Β’ ξένης γλώσσας", ""),
    ("έως 10/9", "Εσωτερικός κανονισμός λειτουργίας", "Επικαιροποίηση, ανάρτηση στην ιστοσελίδα"),
    ("11/9", "Ωρολόγιο πρόγραμμα", "(έστω προσωρινό)"),
    ("11/9", "Αγιασμός", "Υποδοχή γονέων Α’ τάξης"),
    ("15/9", "Επιβεβαίωση Δεδομένων Myschool", ""),
    ("έως 20/9", "Ορισμός συντονιστών", ""),
    ("έως 30/9", "Ειδική συνεδρίαση Συλλόγου Διδασκόντων", "Καθορισμός ετήσιου Σχεδίου Δράσης"),
]

for date, title, task in september_tasks:
    cursor.execute("INSERT INTO tasks (user_name, month, date, title, task, completed) VALUES (?, ?, ?, ?, ?, ?)",
                   (st.session_state.user_name, "Σεπτέμβριος", date, title, task, 0))
conn.commit()

st.success("Οι εργασίες του Σεπτεμβρίου προστέθηκαν επιτυχώς!")

# 📌 Ανάκτηση εργασιών από τη βάση
tasks = get_tasks_from_db(selected_month)

# 📌 Εμφάνιση εργασιών
st.markdown("### 📌 Λίστα εργασιών")
for task_id, date, title, task, completed in tasks:
    task_key = f"{selected_month}_{task_id}"
    col1, col2 = st.columns([1, 4])

    with col1:
        if st.checkbox("", key=task_key, value=completed):
            cursor.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
        else:
            cursor.execute("UPDATE tasks SET completed = 0 WHERE id = ?", (task_id,))
        conn.commit()

    with col2:
        tag_color = "🟢" if completed else "🔴"
        st.markdown(f"**{date} | {title}** {tag_color}")
        st.write(task)

# 📌 Εκτύπωση σε PDF
def save_pdf(user_name, tasks):
    pdf_filename = f"{user_name}_tasks.pdf"
    c = canvas.Canvas(pdf_filename)
    
    c.drawString(100, 800, f"Εργασίες για {user_name}")

    y = 780
    for task in tasks:
        date = task[1]
        title = task[2]
        text = task[3]
        completed = "✓" if task[4] else "✗"
        c.drawString(100, y, f"{date}: {title} - {text} ({completed})")
        y -= 20
    
    c.save()
    return pdf_filename

if st.button("🖨️ Εκτύπωση PDF"):
    pdf_file = save_pdf(st.session_state.user_name, tasks)
    with open(pdf_file, "rb") as f:
        st.download_button("📄 Λήψη PDF", f, pdf_file, "application/pdf")

# 📌 Εκτύπωση σε CSV
if st.button("📄 Εκτύπωση σε CSV"):
    df = pd.DataFrame([
        {"Ημερομηνία": task[1], "Τίτλος": task[2], "Εργασία": task[3], "Κατάσταση": "✓" if task[4] else "✗"}
        for task in tasks
    ])
    st.download_button("📄 Λήψη ως CSV", df.to_csv(index=False).encode('utf-8-sig'),
                       f"εργασίες_{selected_month}.csv", "text/csv", key='download-csv")

st.markdown("---")
st.markdown("*Σύστημα Παρακολούθησης Εργασιών Διευθυντή*")
