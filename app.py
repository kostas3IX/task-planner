import streamlit as st
import sqlite3
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime, timedelta
import icalendar
from io import BytesIO
import json
import urllib.request # Προστέθηκε για την λήψη του font
import tarfile # Προστέθηκε για την αποσυμπίεση του font

# 📌 Ρύθμιση Streamlit UI
st.set_page_config(
    page_title="Προγραμματισμός Ενεργειών",
    page_icon="📋",
    layout="wide"
)

# 📌 Custom CSS
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
    .task-urgent {
        background-color: #ffe6e6;
        border-left: 4px solid #e74c3c;
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

# 📌 JavaScript για ώρα
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

# -------- ΜΕΤΑΦΟΡΑ ΑΡΧΙΚΟΠΟΙΗΣΗΣ ΒΑΣΗΣ ΔΕΔΟΜΕΝΩΝ ΕΔΩ --------
# 📌 Σύνδεση με SQLite
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
# --------------------------------------------------------------

# 📌 FullCalendar με δυναμικά events
def get_calendar_events(user_name):
    cursor.execute("SELECT month, date, title, completed FROM tasks WHERE user_name = ?", (user_name,))
    tasks = cursor.fetchall()
    month_map = {
        "Σεπτέμβριος": 9, "Οκτώβριος": 10, "Νοέμβριος": 11, "Δεκέμβριος": 12,
        "Ιανουάριος": 1, "Φεβρουάριος": 2, "Μάρτιος": 3, "Απρίλιος": 4,
        "Μάιος": 5, "Ιούνιος": 6, "Ιούλιος": 7, "Αύγουστος": 8
    }
    events = []
    current_year = datetime.now().year # Χρήση τρέχοντος έτους για ευελιξία ή μπορείτε να ορίσετε συγκεκριμένο
    # Για τις ανάγκες των προκαθορισμένων tasks που έχουν ημερομηνίες /2025, κρατάμε το 2025
    # Αν οι εργασίες αναφέρονται στο τρέχον σχολικό έτος, ίσως χρειαστεί πιο δυναμικός χειρισμός του έτους.
    target_year_for_dates = 2025

    for month_name, date_str_db, title, completed in tasks:
        if date_str_db and month_name in month_map:
            try:
                # Προσπάθεια εξαγωγής μόνο της ημέρας/μήνα
                # Χειρισμός "έως DD/MM" και "DD-DD/MM"
                if "έως" in date_str_db:
                    actual_date_part = date_str_db.split("έως")[-1].strip()
                elif "-" in date_str_db and "/" in date_str_db: # π.χ. "1-5/9"
                     actual_date_part = date_str_db.split("-")[-1].strip() # Παίρνουμε την τελευταία ημερομηνία του εύρους
                else: # απλή ημερομηνία "DD/MM"
                    actual_date_part = date_str_db.strip()

                # Αφαίρεση τυχόν χαρακτήρων που δεν είναι μέρος της ημερομηνίας
                actual_date_part = actual_date_part.split("/")[0] + "/" + str(month_map[month_name])

                event_date = datetime.strptime(f"{actual_date_part}/{target_year_for_dates}", "%d/%m/%Y")

                events.append({
                    "title": title,
                    "start": event_date.strftime("%Y-%m-%d"),
                    "color": "#2ecc71" if completed else "#e74c3c"
                })
            except ValueError:
                # st.warning(f"Δεν ήταν δυνατή η ανάλυση της ημερομηνίας για το ημερολόγιο: '{date_str_db}' στον μήνα '{month_name}' με τίτλο '{title}'. Παράλειψη.")
                continue # Παράλειψη αυτού του event αν η ημερομηνία δεν είναι έγκυρη
            except Exception as e:
                # st.error(f"Άγνωστο σφάλμα κατά την επεξεργασία ημερομηνίας για ημερολόγιο: {e} για '{date_str_db}'")
                continue
    return events

calendar_events = get_calendar_events("Κώστας") # Αυτό καλείται τώρα αφού έχει οριστεί ο cursor
st.markdown(f"""
<link href='https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.css' rel='stylesheet' />
<script src='https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.js'></script>
<script src='https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/locales/el.js'></script>
<div id='calendar'></div>
<script>
document.addEventListener('DOMContentLoaded', function() {{
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {{
        initialView: 'dayGridMonth',
        locale: 'el',
        height: '500px',
        events: {json.dumps(calendar_events)},
        eventClick: function(info) {{
            alert('Εργασία: ' + info.event.title + '\\nΗμερομηνία: ' + new Date(info.event.start).toLocaleDateString('el-GR'));
        }}
    }});
    calendar.render();
}});
</script>
""", unsafe_allow_html=True)

# 📌 Προκαθορισμένες εργασίες
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
        ("έως 20/9", "Ορισμός συντονιστών"), # Άλλαξα το "έως 20" σε "έως 20/9" για συνέπεια
        ("έως 20/9", "Ορισμός μέντορα"), # Άλλαξα το "έως 20" σε "έως 20/9"
        ("έως 20/9", "Προαιρετική Συγκρότηση Εκπαιδευτικών Ομίλων"), # Άλλαξα το "έως 20" σε "έως 20/9"
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
        ("23/12-9/1", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"), # Διόρθωση έτους "23/12-9/1/23" σε "23/12-9/1" για συνέπεια, το έτος θα είναι το target_year_for_dates + 1
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
        ("27/4-12/5", "Διακοπές Πάσχα"), # Το έτος για τις διακοπές Πάσχα μπορεί να διαφέρει
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

# 📌 Προσθήκη προκαθορισμένων εργασιών
def add_predefined_tasks(user_name):
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_name = ?", (user_name,))
    count = cursor.fetchone()[0]
    if count == 0:
        for month, tasks_list in predefined_tasks.items():
            for date_val, task_desc in tasks_list:
                title = task_desc
                cursor.execute("INSERT INTO tasks (user_name, month, date, title, task, completed) VALUES (?, ?, ?, ?, ?, ?)",
                               (user_name, month, date_val, title, task_desc, 0))
        conn.commit()
        return True
    return False

# 📌 Ανάκτηση εργασιών
def get_tasks_from_db(user_name, month):
    cursor.execute("SELECT id, date, title, task, completed FROM tasks WHERE user_name = ? AND month = ? ORDER BY CASE WHEN date IS NULL THEN 1 ELSE 0 END, date",
                   (user_name, month)) # ORDER BY για να έρχονται οι εργασίες χωρίς ημερομηνία τελευταίες ή πρώτες
    return cursor.fetchall()

# 📌 Ενημέρωση εργασίας
def update_task(task_id, date_val, title_val): # άλλαξα τα ονόματα των παραμέτρων για αποφυγή σύγκρουσης
    cursor.execute("UPDATE tasks SET date = ?, title = ? WHERE id = ?",
                   (date_val, title_val, task_id))
    conn.commit()

# 📌 Προσθήκη νέου task
def add_task(user_name, month, date_val, title_val): # άλλαξα τα ονόματα των παραμέτρων
    cursor.execute("INSERT INTO tasks (user_name, month, date, title, task, completed) VALUES (?, ?, ?, ?, ?, ?)",
                   (user_name, month, date_val, title_val, title_val, 0)) # το task παίρνει την τιμή του title αρχικά
    conn.commit()

# 📌 Check/Uncheck all
def check_all_tasks(user_name, month):
    cursor.execute("UPDATE tasks SET completed = 1 WHERE user_name = ? AND month = ?",
                   (user_name, month))
    conn.commit()

def uncheck_all_tasks(user_name, month):
    cursor.execute("UPDATE tasks SET completed = 0 WHERE user_name = ? AND month = ?",
                   (user_name, month))
    conn.commit()

# 📌 Έλεγχος προθεσμίας
def is_task_urgent(date_str):
    if not date_str: # Αν δεν υπάρχει date_str, δεν είναι επείγον
        return False

    target_year_for_dates = 2025 # Συγχρονισμός με το έτος που χρησιμοποιείται στο get_calendar_events

    # Χειρισμός για "έως DD/MM"
    if "έως" in date_str:
        end_date_part = date_str.split("έως")[-1].strip()
        try:
            # Προσπάθεια να πάρουμε μήνα από το predefined_tasks αν δεν υπάρχει στο string
            day_part, month_part_str = end_date_part.split('/')
            end_date = datetime.strptime(f"{day_part}/{month_part_str}/{target_year_for_dates}", "%d/%m/%Y")
            today = datetime.now()
            return 0 <= (end_date - today).days <= 2
        except ValueError:
            return False # Λάθος μορφή ημερομηνίας
    # Χειρισμός για εύρος "DD-DD/MM" ή "DD/MM-DD/MM"
    elif "-" in date_str and "/" in date_str:
        try:
            # Παίρνουμε την τελευταία ημερομηνία του εύρους
            if date_str.count('/') == 1: # Μορφή DD-DD/MM
                range_part, month_part_str = date_str.split('/')
                day_part = range_part.split('-')[-1]
            else: # Μορφή DD/MM-DD/MM
                _, end_range_part = date_str.split('-')
                day_part, month_part_str = end_range_part.strip().split('/')

            end_date = datetime.strptime(f"{day_part}/{month_part_str}/{target_year_for_dates}", "%d/%m/%Y")
            today = datetime.now()
            return 0 <= (end_date - today).days <= 2
        except ValueError:
            return False # Λάθος μορφή ημερομηνίας
    # Χειρισμός για απλή ημερομηνία "DD/MM"
    elif "/" in date_str:
        try:
            end_date = datetime.strptime(f"{date_str}/{target_year_for_dates}", "%d/%m/%Y")
            today = datetime.now()
            # Μια απλή ημερομηνία δεν θεωρείται "επείγουσα" με την έννοια της προθεσμίας, εκτός αν το θέλουμε
            # return (end_date - today).days == 0 # Αν θέλουμε να επισημαίνεται την ίδια μέρα
            return False # Για τώρα, οι απλές ημερομηνίες δεν είναι "urgent" με την έννοια της προθεσμίας
        except ValueError:
            return False
    return False


# 📌 Εξαγωγή σε ICS
def export_to_ics(user_name):
    cal = icalendar.Calendar()
    cal.add('prodid', '-//My Task Calendar//mxm.dk//')
    cal.add('version', '2.0')
    cursor.execute("SELECT month, date, title, completed FROM tasks WHERE user_name = ?", (user_name,))
    tasks = cursor.fetchall()
    month_map = {
        "Σεπτέμβριος": 9, "Οκτώβριος": 10, "Νοέμβριος": 11, "Δεκέμβριος": 12,
        "Ιανουάριος": 1, "Φεβρουάριος": 2, "Μάρτιος": 3, "Απρίλιος": 4,
        "Μάιος": 5, "Ιούνιος": 6, "Ιούλιος": 7, "Αύγουστος": 8
    }
    target_year_for_dates = 2025 # Συγχρονισμός έτους

    for month_name, date_str_db, title, completed in tasks:
        if date_str_db and month_name in month_map:
            try:
                actual_date_part = ""
                if "έως" in date_str_db:
                    actual_date_part = date_str_db.split("έως")[-1].strip()
                elif "-" in date_str_db and "/" in date_str_db:
                     actual_date_part = date_str_db.split("-")[-1].strip()
                else:
                    actual_date_part = date_str_db.strip()

                # Εξασφάλιση ότι έχουμε και τον μήνα στην actual_date_part για το strptime
                if '/' not in actual_date_part: # π.χ. "20" από "έως 20"
                    actual_date_part = f"{actual_date_part}/{month_map[month_name]}"
                elif actual_date_part.count('/') == 0 : # π.χ. "20" από "έως 20"
                     actual_date_part = f"{actual_date_part}/{month_map[month_name]}"


                # Αν το actual_date_part είναι μόνο ημέρα, προσθέτουμε τον μήνα
                if actual_date_part.count('/') == 0:
                    day_only = actual_date_part
                    actual_date_part = f"{day_only}/{month_map[month_name]}"


                event_date = datetime.strptime(f"{actual_date_part}/{target_year_for_dates}", "%d/%m/%Y")

                event = icalendar.Event()
                event.add('summary', title)
                event.add('dtstart', event_date.date()) # Χρήση .date() για ολοήμερο γεγονός
                event.add('dtend', (event_date + timedelta(days=1)).date()) # Το dtend είναι αποκλειστικό
                event.add('description', f"Κατάσταση: {'Ολοκληρωμένο' if completed else 'Εκκρεμές'}")
                cal.add_component(event)
            except ValueError:
                # st.warning(f"Δεν ήταν δυνατή η ανάλυση της ημερομηνίας για ICS: '{date_str_db}'. Παράλειψη.")
                continue
            except Exception as e:
                # st.error(f"Άγνωστο σφάλμα κατά την επεξεργασία ημερομηνίας για ICS: {e} για '{date_str_db}'")
                continue
    buffer = BytesIO()
    buffer.write(cal.to_ical())
    buffer.seek(0)
    return buffer, "tasks.ics"

# 📌 Αρχικοποίηση session state
if "user_name" not in st.session_state:
    st.session_state.user_name = "Κώστας" # Προεπιλεγμένος χρήστης
    if add_predefined_tasks(st.session_state.user_name):
        st.success("Οι προκαθορισμένες εργασίες προστέθηκαν για τον χρήστη Κώστα.") # Χρησιμοποιούμε st.success για θετικό μήνυμα

if "edit_task_id" not in st.session_state:
    st.session_state.edit_task_id = None

# 📌 Κεφαλίδα
st.markdown('<div class="title">📋 Προγραμματισμός Ενεργειών</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">Γεια σου, {st.session_state.user_name}! Παρακολούθησε τις μηνιαίες σου εργασίες.</div>', unsafe_allow_html=True)

# 📌 Επιλογή μήνα
months = list(predefined_tasks.keys())
with st.container(): # Χρήση container για καλύτερη ομαδοποίηση αν χρειαστεί
    st.markdown('<div class="month-select">', unsafe_allow_html=True)
    selected_month = st.selectbox("Επιλέξτε Μήνα:", months, label_visibility="visible") # label_visibility αντί για collapsed
    st.markdown('</div>', unsafe_allow_html=True)

# 📌 Φόρμα προσθήκης task
st.markdown("### ➕ Προσθήκη Νέου Task")
with st.form("add_task_form", clear_on_submit=True):
    new_date = st.text_input("Ημερομηνία (π.χ. 15/9, έως 20/9, 1-5/9):", key="new_date_input") # Άλλαξα το key για αποφυγή σύγκρουσης
    new_title = st.text_input("Τίτλος Εργασίας:", key="new_title_input") # Άλλαξα το key
    if st.form_submit_button("Προσθήκη Task"):
        if new_date and new_title:
            add_task(st.session_state.user_name, selected_month, new_date, new_title)
            st.success("Το task προστέθηκε επιτυχώς!")
            st.rerun() # Χρήση rerun για άμεση ανανέωση
        else:
            st.error("Παρακαλώ συμπληρώστε όλα τα πεδία.")

# 📌 Ανάκτηση εργασιών
tasks = get_tasks_from_db(st.session_state.user_name, selected_month)

# 📌 Υπολογισμός προόδου
total_tasks = len(tasks)
completed_tasks_count = sum(1 for task_item in tasks if task_item[4] == 1) # Άλλαξα το όνομα της μεταβλητής
progress_percentage = (completed_tasks_count / total_tasks) * 100 if total_tasks > 0 else 0

# 📌 Εμφάνιση προόδου
st.markdown(f'<div class="progress-container"><strong>Πρόοδος {selected_month}</strong></div>', unsafe_allow_html=True)
if total_tasks > 0:
    st.progress(progress_percentage / 100.0)
    st.markdown(f'<div class="progress-container">{completed_tasks_count}/{total_tasks} εργασίες ({progress_percentage:.0f}%)</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="progress-container">Καμία εργασία για εμφάνιση</div>', unsafe_allow_html=True)

# 📌 Κουμπιά Check All / Uncheck All
if tasks: # Εμφάνιση κουμπιών μόνο αν υπάρχουν tasks
    # Χρήση st.columns για καλύτερη διάταξη των κουμπιών
    col_check, col_uncheck, col_export_ics, col_export_pdf = st.columns([1,1,1.5,1.5]) # Δίνουμε βάρη στις στήλες

    with col_check:
        if st.button("Επιλογή Όλων", key="check_all_btn", help="Επιλέγει όλες τις εργασίες του μήνα", use_container_width=True):
            check_all_tasks(st.session_state.user_name, selected_month)
            st.rerun()
    with col_uncheck:
        if st.button("Αποεπιλογή Όλων", key="uncheck_all_btn", help="Αποεπιλέγει όλες τις εργασίες του μήνα", use_container_width=True):
            uncheck_all_tasks(st.session_state.user_name, selected_month)
            st.rerun()
    # 📌 Εξαγωγή σε Google Calendar (ICS)
    with col_export_ics:
        ics_file, ics_filename = export_to_ics(st.session_state.user_name) # Καλείται πάντα για να έχουμε τα δεδομένα
        st.download_button(
            label="Λήψη ICS Ημερολογίου",
            data=ics_file,
            file_name=ics_filename,
            mime="text/calendar",
            help="Εξαγωγή όλων των tasks σε ICS αρχείο για Google Calendar",
            use_container_width=True
        )
    # 📌 Κουμπί Εξαγωγής σε PDF (μετακινήθηκε εδώ για καλύτερη ομαδοποίηση)
    with col_export_pdf:
        # Η συνάρτηση save_pdf θα κληθεί μόνο όταν πατηθεί το κουμπί download
        # Για να γίνει αυτό, χρειαζόμαστε το περιεχόμενο του PDF ως bytes.
        # Η save_pdf γράφει σε αρχείο, οπότε θα την προσαρμόσουμε ή θα διαβάσουμε το αρχείο.
        if st.button("Εξαγωγή σε PDF", help="Εξαγωγή όλων των tasks σε PDF", key="export_pdf_btn", use_container_width=True):
            pdf_filename_tmp = save_pdf(st.session_state.user_name) # Αυτό δημιουργεί το αρχείο
            with open(pdf_filename_tmp, "rb") as fp:
                btn = st.download_button( # Αυτό το κουμπί εμφανίζεται *μετά* το κλικ του "Εξαγωγή σε PDF"
                    label="Λήψη PDF Τώρα", # Εμφανίζεται αφού δημιουργηθεί το PDF
                    data=fp,
                    file_name=os.path.basename(pdf_filename_tmp), # Χρήση basename για να πάρουμε μόνο το όνομα αρχείου
                    mime="application/pdf",
                    key="download_pdf_final"
                )
            # Δεν χρειάζεται st.rerun() εδώ, εκτός αν θέλουμε να εξαφανιστεί το "Λήψη PDF Τώρα" αμέσως
            # Το download_button από μόνο του χειρίζεται τη λήψη.

st.markdown("---") # Οριζόντια γραμμή πριν τις εργασίες

# 📌 Εμφάνιση εργασιών
st.markdown(f"### 📌 Εργασίες {selected_month}")
if not tasks:
    st.info(f"Δεν υπάρχουν εργασίες για τον μήνα {selected_month}.") # Πιο φιλικό μήνυμα
else:
    for task_id, date_val, title_val, task_desc, completed_status in tasks: # Καλύτερα ονόματα μεταβλητών
        task_key_prefix = f"task_{task_id}_{selected_month.replace(' ', '_')}" # Πιο ασφαλές key
        is_urgent = is_task_urgent(date_val)

        container_class = "task-container"
        if is_urgent:
            container_class += " task-urgent"

        with st.container(): # Κάθε task σε δικό του container
            st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)
            cols = st.columns([0.5, 5, 0.5, 0.5]) # Χρήση cols αντί για col1, col2...

            with cols[0]: # Checkbox
                is_checked = completed_status == 1
                st.checkbox(
                    f"##{task_id}", # Κρυφό label με ##
                    value=is_checked,
                    key=f"cb_{task_key_prefix}",
                    on_change=(lambda tid, current_status: (
                        cursor.execute("UPDATE tasks SET completed = ? WHERE id = ?", (0 if current_status else 1, tid)),
                        conn.commit(),
                        st.rerun() # Άμεση ανανέωση
                    )),
                    args=(task_id, is_checked), # Περνάμε τα ορίσματα στο on_change
                    label_visibility="collapsed"
                )
            with cols[1]: # Τίτλος και ημερομηνία
                status_emoji = "🟢" if completed_status else "🔴"
                display_date_str = date_val if date_val else "Χωρίς Ημ/νία"
                st.markdown(f'<span class="task-title">{title_val}</span> <span class="task-status">{status_emoji}</span>', unsafe_allow_html=True)
                st.markdown(f'<span class="task-date">{display_date_str}</span>', unsafe_allow_html=True)
                if title_val != task_desc and task_desc: # Εμφάνιση περιγραφής αν διαφέρει και υπάρχει
                    st.caption(task_desc) # Χρήση caption για την περιγραφή
                if is_urgent:
                    st.markdown('<span style="color: #e74c3c; font-size: 0.9em;">⚠️ Επείγουσα προθεσμία!</span>', unsafe_allow_html=True)

            with cols[2]: # Κουμπί διαγραφής
                if st.button("🗑️", key=f"delete_{task_key_prefix}", help="Διαγραφή Εργασίας"):
                    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                    conn.commit()
                    st.rerun()
            with cols[3]: # Κουμπί επεξεργασίας
                if st.button("✏️", key=f"edit_{task_key_prefix}", help="Επεξεργασία Εργασίας"):
                    st.session_state.edit_task_id = task_id
                    st.rerun() # Για να εμφανιστεί η φόρμα επεξεργασίας αμέσως
            st.markdown('</div>', unsafe_allow_html=True)


# 📌 Φόρμα επεξεργασίας
if st.session_state.edit_task_id is not None:
    active_task_id = st.session_state.edit_task_id
    cursor.execute("SELECT date, title FROM tasks WHERE id = ?", (active_task_id,))
    task_data_to_edit = cursor.fetchone()

    if task_data_to_edit:
        st.markdown("### ✏️ Επεξεργασία Εργασίας")
        with st.form(f"edit_task_form_{active_task_id}", clear_on_submit=True):
            edit_date_val = st.text_input("Ημερομηνία (π.χ. 15/9, έως 20/9):", value=task_data_to_edit[0] or "", key=f"edit_date_{active_task_id}")
            edit_title_val = st.text_input("Τίτλος Εργασίας:", value=task_data_to_edit[1], key=f"edit_title_{active_task_id}")

            form_cols = st.columns(2)
            with form_cols[0]:
                if st.form_submit_button("Αποθήκευση"):
                    update_task(active_task_id, edit_date_val, edit_title_val)
                    st.session_state.edit_task_id = None # Καθαρισμός ID μετά την αποθήκευση
                    st.success("Η εργασία ενημερώθηκε επιτυχώς!")
                    st.rerun()
            with form_cols[1]:
                if st.form_submit_button("Ακύρωση"):
                    st.session_state.edit_task_id = None # Καθαρισμός ID κατά την ακύρωση
                    st.rerun()
    else: # Αν για κάποιο λόγο το task ID δεν βρεθεί (π.χ. διαγράφηκε εν τω μεταξύ)
        st.session_state.edit_task_id = None
        st.warning("Η εργασία προς επεξεργασία δεν βρέθηκε. Παρακαλώ ανανεώστε.")
        st.rerun()


# 📌 Εκτύπωση σε PDF
def save_pdf(user_name):
    # Δημιουργία μοναδικού ονόματος αρχείου για την αποφυγή caching προβλημάτων στο st.download_button
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    pdf_filename = f"{user_name}_all_tasks_{timestamp}.pdf"
    
    font_dir = "/tmp/dejavu-fonts-ttf-2.37/ttf/"
    font_path = os.path.join(font_dir, "DejaVuSans.ttf")

    if not os.path.exists(font_path):
        os.makedirs(font_dir, exist_ok=True) # Δημιουργία καταλόγου αν δεν υπάρχει
        st.info("Κατεβάζοντας γραμματοσειρά για το PDF (DejaVuSans)...")
        try:
            font_url = "https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version-2.37/dejavu-fonts-ttf-2.37.tar.bz2"
            font_archive_path = "/tmp/dejavu-fonts.tar.bz2"
            urllib.request.urlretrieve(font_url, font_archive_path)
            with tarfile.open(font_archive_path, "r:bz2") as tar:
                # Εξαγωγή μόνο του συγκεκριμένου αρχείου γραμματοσειράς
                member_path = "dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf"
                tar.extract(member_path, path="/tmp")
            # Μετακίνηση του αρχείου στον σωστό υποκατάλογο που περιμένουμε
            # os.rename(os.path.join("/tmp", member_path), font_path) # Αυτό δεν είναι σωστό, το extract το βάζει ήδη εκεί.
            # Η παραπάνω γραμμή os.rename είναι περιττή αν το extract path είναι /tmp
            # και το member_path είναι το πλήρες path μέσα στο tar.
            # Το font_path είναι /tmp/dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf
            # Το extract βγάζει το dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf μέσα στο /tmp
            # Άρα το αρχείο είναι στο /tmp/dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf
            st.success("Η γραμματοσειρά φορτώθηκε.")
        except Exception as e:
            st.error(f"Σφάλμα κατά τη λήψη/εξαγωγή γραμματοσειράς: {e}")
            # Εναλλακτική γραμματοσειρά αν αποτύχει η λήψη (π.χ. Helvetica)
            # pdfmetrics.registerFont(TTFont("Helvetica", "Helvetica")) # Χρειάζεται έλεγχο αν είναι διαθέσιμη
            # return None # ή χειρισμός του σφάλματος αλλιώς
            pass # Επιτρέπουμε να συνεχίσει, μπορεί να χρησιμοποιήσει default font

    try:
        pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
    except Exception as e:
        st.warning(f"Δεν ήταν δυνατή η καταχώρηση της γραμματοσειράς DejaVuSans: {e}. Θα χρησιμοποιηθεί προεπιλεγμένη.")
        # Δεν χρειάζεται να κάνουμε τίποτα άλλο, η reportlab θα χρησιμοποιήσει μια default αν μπορεί.

    c = canvas.Canvas(pdf_filename, pagesize=A4)
    c.setFont("DejaVuSans", 12 if "DejaVuSans" in pdfmetrics.getRegisteredFontNames() else "Helvetica", 12)
    
    page_width, page_height = A4
    margin = 50
    y_position = page_height - margin
    line_height = 18

    def draw_header(canvas_obj, user):
        canvas_obj.setFont("DejaVuSans" if "DejaVuSans" in pdfmetrics.getRegisteredFontNames() else "Helvetica", 16)
        canvas_obj.drawCentredString(page_width / 2, y_position, f"Προγραμματισμός Ενεργειών για {user}")
        return y_position - line_height * 2

    def check_page_break(canvas_obj, current_y):
        if current_y < margin + line_height: # Προσθήκη χώρου για υποσέλιδο αν υπάρχει
            canvas_obj.showPage()
            canvas_obj.setFont("DejaVuSans" if "DejaVuSans" in pdfmetrics.getRegisteredFontNames() else "Helvetica", 10)
            return page_height - margin
        return current_y

    y_position = draw_header(c, user_name)

    c.setFont("DejaVuSans" if "DejaVuSans" in pdfmetrics.getRegisteredFontNames() else "Helvetica", 10)
    
    # Σωστή ταξινόμηση μηνών
    month_order = {name: i for i, name in enumerate(predefined_tasks.keys())}

    cursor.execute("SELECT month, date, title, task, completed FROM tasks WHERE user_name = ? ", (user_name,))
    all_user_tasks = cursor.fetchall()
    
    # Ταξινόμηση με βάση την προσαρμοσμένη σειρά μηνών και μετά την ημερομηνία
    # Πρώτα μετατρέπουμε τις ημερομηνίες σε datetime objects για σωστή σύγκριση, όπου είναι δυνατόν
    def sort_key_for_tasks(task_item):
        month_idx = month_order.get(task_item[0], 99) # 99 για μήνες εκτός λίστας
        date_str = task_item[1]
        parsed_date = None
        if date_str:
            try:
                # Πιο ανθεκτική ανάλυση ημερομηνίας για ταξινόμηση
                if "έως" in date_str:
                    date_part_to_parse = date_str.split("έως")[-1].strip()
                elif "-" in date_str and "/" in date_str:
                    date_part_to_parse = date_str.split("-")[-1].strip() # Παίρνουμε την τελευταία ημερομηνία του εύρους
                else:
                    date_part_to_parse = date_str.strip()
                
                if '/' not in date_part_to_parse: # Αν είναι μόνο ημέρα π.χ. "20" από "έως 20"
                    month_number = month_map.get(task_item[0])
                    if month_number:
                       date_part_to_parse = f"{date_part_to_parse}/{month_number}"

                parsed_date = datetime.strptime(date_part_to_parse + "/2025", "%d/%m/%Y") # Χρήση σταθερού έτους για ταξινόμηση
            except:
                parsed_date = datetime.min # Αν δεν μπορεί να αναλυθεί, τοποθέτησέ το στην αρχή ή στο τέλος
        return (month_idx, parsed_date if parsed_date else datetime.min)

    all_user_tasks_ordered = sorted(all_user_tasks, key=sort_key_for_tasks)
    
    current_month_pdf = None
    for month_pdf, date_pdf, title_pdf, task_pdf_desc, completed_pdf in all_user_tasks_ordered:
        y_position = check_page_break(c, y_position)
        if month_pdf != current_month_pdf:
            current_month_pdf = month_pdf
            y_position -= line_height # Επιπλέον κενό πριν τον νέο μήνα
            y_position = check_page_break(c, y_position)
            c.setFont("DejaVuSans" if "DejaVuSans" in pdfmetrics.getRegisteredFontNames() else "Helvetica", 12) # Μεγαλύτερη γραμματοσειρά για τον μήνα
            c.drawString(margin, y_position, month_pdf)
            c.setFont("DejaVuSans" if "DejaVuSans" in pdfmetrics.getRegisteredFontNames() else "Helvetica", 10)
            y_position -= line_height * 1.5

        date_str_pdf = date_pdf if date_pdf else "Χωρίς Ημ/νία"
        completed_status_pdf = "✓ (Ολοκληρωμένο)" if completed_pdf else "✗ (Εκκρεμές)"
        
        text_object = c.beginText(margin + 10, y_position) # Λίγο πιο μέσα οι εργασίες
        text_object.setFont("DejaVuSans" if "DejaVuSans" in pdfmetrics.getRegisteredFontNames() else "Helvetica", 10)
        
        # Γραμμή 1: Ημερομηνία και Τίτλος
        line1 = f"{date_str_pdf}: {title_pdf}"
        text_object.textLine(line1)
        y_position -= line_height

        # Γραμμή 2: Κατάσταση
        text_object.setFillColorRGB(0.2, 0.2, 0.2) # Πιο απαλό χρώμα για την κατάσταση
        text_object.textLine(f"   Κατάσταση: {completed_status_pdf}")
        y_position -= line_height
        text_object.setFillColorRGB(0, 0, 0) # Επαναφορά στο μαύρο

        # Γραμμή 3 (προαιρετικά): Περιγραφή αν υπάρχει και διαφέρει
        if title_pdf != task_pdf_desc and task_pdf_desc:
            # Wrap text for description
            max_width = page_width - 2 * (margin + 10)
            desc_lines = []
            current_line = "   Περιγραφή: "
            words = task_pdf_desc.split(' ')
            for word in words:
                if c.stringWidth(current_line + word, "DejaVuSans" if "DejaVuSans" in pdfmetrics.getRegisteredFontNames() else "Helvetica", 10) <= max_width:
                    current_line += word + " "
                else:
                    desc_lines.append(current_line.strip())
                    current_line = "     " + word + " " # Indent subsequent lines
            desc_lines.append(current_line.strip())

            for line_desc in desc_lines:
                y_position = check_page_break(c, y_position) # Έλεγχος πριν κάθε γραμμή της περιγραφής
                text_object.setTextOrigin(margin + 10, y_position) # Επανατοποθέτηση για κάθε γραμμή
                text_object.textLine(line_desc)
                y_position -= line_height
        
        c.drawText(text_object)
        y_position -= line_height * 0.5 # Μικρό κενό μεταξύ των εργασιών
        
    c.save()
    return pdf_filename


st.markdown("---")
st.markdown("*Σύστημα Παρακολούθησης Εργασιών Διευθυντή*")
