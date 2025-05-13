import streamlit as st
import sqlite3
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

# 📌 Υπολογισμός ποσοστού ολοκλήρωσης ανά μήνα
def get_completion_percentage(month):
    tasks = get_tasks_from_db(month)
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task[4])
    return (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

# 📌 Μετατροπή ονόματος σε κλητική πτώση
def to_vocative(name):
    if name.endswith("ς"):
        return name[:-1]
    return name

# 📌 Αρχικοποίηση της εφαρμογής
if "user_name" not in st.session_state:
    st.session_state.user_name = "Κώστας"  # Προσαρμόζεται δυναμικά αν θέλουμε

# 📌 Ρύθμιση Streamlit UI
st.set_page_config(
    page_title="Προγραμματισμός Ενεργειών",
    page_icon="📋",
    layout="wide"
)

# 📌 Κεφαλίδα με όνομα στην κλητική
vocative_name = to_vocative(st.session_state.user_name)
st.markdown(f"## 👋 Γεια σου, {vocative_name}!")
st.markdown("### 📋 Προγραμματισμός ενεργειών διευθυντή")
st.write("**Παρακολούθηση Μηνιαίων Εργασιών**")

# 📌 Επιλογή μήνα με ποσοστά ολοκλήρωσης
months = ["Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος",
          "Ιούλιος", "Αύγουστος", "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"]
month_options = [f"{month} ({get_completion_percentage(month):.1f}%)" for month in months]
selected_month_with_percentage = st.selectbox("📅 Επιλέξτε Μήνα:", month_options)
selected_month = selected_month_with_percentage.split(" (")[0]  # Εξαγωγή του ονόματος του μήνα

# 📌 Ανάκτηση εργασιών από τη βάση
tasks = get_tasks_from_db(selected_month)

# 📌 Υπολογισμός ποσοστού ολοκλήρωσης για τον επιλεγμένο μήνα
total_tasks = len(tasks)
completed_tasks = sum(1 for task in tasks if task[4])
completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

# 📌 Εμφάνιση μπάρας προόδου για τον επιλεγμένο μήνα
st.markdown(f"### 📊 Ποσοστό Ολοκλήρωσης για {selected_month}: {completion_percentage:.1f}%")
st.progress(completion_percentage / 100)

# 📌 Εμφάνιση εργασιών με τίτλο & περιγραφή
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
        st.write(task)

# 📌 Προσθήκη νέας εργασίας με δυναμικό κλείσιμο πεδίων
with st.form("new_task_form", clear_on_submit=True):
    new_task_title = st.text_input("📌 Τίτλος Εργασίας:")
    new_task_date = st.text_input("📅 Ημερομηνία (προαιρετικό):")
    new_task_text = st.text_area("📝 Περιγραφή Εργασίας:")
    submitted = st.form_submit_button("✅ Προσθήκη Εργασίας")

    if submitted and new_task_text:
        cursor.execute("INSERT INTO tasks (user_name, month, date, title, task, completed) VALUES (?, ?, ?, ?, ?, ?)",
                       (st.session_state.user_name, selected_month, new_task_date, new_task_title, new_task_text, 0))
        conn.commit()
        st.rerun()  # 🔄 Ανανεώνει την εφαρμογή και κλείνει τα πεδία

# 📌 Εκτύπωση σε PDF
def save_pdf(user_name, tasks):
    pdf_filename = f"{user_name}_tasks.pdf"
    c = canvas.Canvas(pdf_filename)
    
    c.drawString(100, 800, f"Εργασίες για {to_vocative(user_name)}")
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

st.markdown("---")
st.markdown("*Σύστημα Παρακολούθησης Εργασιών Διευθυντή*")
