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
import urllib.request
import tarfile

# 📌 Ρύθμιση Streamlit UI
st.set_page_config(
    page_title="Προγραμματισμός Ενεργειών",
    page_icon="📋",
    layout="wide"
)

# 📌 Custom CSS
st.markdown("""
<style>
    /* ... (Your CSS remains the same) ... */
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
    const month_js = parts.find(p => p.type === 'month').value;
    const year = parts.find(p => p.type === 'year').value;
    const hour = parts.find(p => p.type === 'hour').value;
    const minute = parts.find(p => p.type === 'minute').value;
    const second = parts.find(p => p.type === 'second').value;
    document.getElementById('clock').innerText = `${hour}:${minute}:${second} EEST, ${weekday}, ${day} ${month_js} ${year}`;
}
setInterval(updateClock, 1000);
updateClock();
</script>
""", unsafe_allow_html=True)

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

month_map = {
    "Σεπτέμβριος": 9, "Οκτώβριος": 10, "Νοέμβριος": 11, "Δεκέμβριος": 12,
    "Ιανουάριος": 1, "Φεβρουάριος": 2, "Μάρτιος": 3, "Απρίλιος": 4,
    "Μάιος": 5, "Ιούνιος": 6, "Ιούλιος": 7, "Αύγουστος": 8
}
target_year_for_dates = datetime.now().year # Χρήση τρέχοντος έτους ή του επόμενου αν είμαστε στο τέλος του έτους
if datetime.now().month > 8 : # Αν είμαστε μετά τον Αύγουστο, οι σχολικές εργασίες αφορούν το επόμενο έτος
    target_year_for_dates = datetime.now().year if datetime.now().month < 9 else datetime.now().year +1


# 📌 Ορισμοί Συναρτήσεων
def get_calendar_events(user_name):
    cursor.execute("SELECT month, date, title, completed FROM tasks WHERE user_name = ?", (user_name,))
    tasks_db = cursor.fetchall()
    events = []
    # Υπολογισμός του έτους για τις ημερομηνίες του ημερολογίου
    # Αν ο τρέχων μήνας είναι π.χ. Σεπτέμβριος-Δεκέμβριος, το έτος είναι το τρέχον.
    # Αν ο τρέχων μήνας είναι Ιανουάριος-Αύγουστος, οι εργασίες Σεπ-Δεκ αναφέρονται στο προηγούμενο έτος ημερολογιακά
    # αλλά στο ίδιο σχολικό έτος. Για απλότητα, θα χρησιμοποιήσουμε μια λογική που κοιτά τον μήνα της εργασίας.
    current_actual_year = datetime.now().year

    for month_name, date_str_db, title, completed in tasks_db:
        if date_str_db and month_name in month_map:
            # Καθορισμός του έτους για το event
            event_year = current_actual_year
            if month_map[month_name] < 9 and datetime.now().month >=9: # π.χ. Είμαστε Οκτώβριος 2024, το task είναι για Ιανουάριο -> 2025
                event_year = current_actual_year + 1
            elif month_map[month_name] >= 9 and datetime.now().month < 9: # π.χ. Είμαστε Μάρτιος 2025, το task είναι για Σεπτέμβριο -> 2024
                event_year = current_actual_year -1


            try:
                actual_date_part = ""
                if "έως" in date_str_db:
                    actual_date_part = date_str_db.split("έως")[-1].strip()
                elif "-" in date_str_db and "/" in date_str_db: # π.χ. "1-5/9"
                    actual_date_part = date_str_db.split("-")[-1].strip() # Παίρνουμε την τελευταία ημερομηνία του εύρους
                else: # απλή ημερομηνία "DD/MM"
                    actual_date_part = date_str_db.strip()

                # Εξασφάλιση ότι το actual_date_part έχει και τον μήνα αν λείπει (π.χ. "20" από "έως 20")
                if '/' not in actual_date_part:
                    actual_date_part = f"{actual_date_part}/{month_map[month_name]}"
                
                # Εξασφάλιση ότι το actual_date_part έχει την μορφή day/month
                parts = actual_date_part.split('/')
                if len(parts) == 2:
                    day_part, month_part_str = parts
                    # Διασφάλιση ότι ο month_part_str είναι αριθμός
                    if not month_part_str.isdigit(): month_part_str = str(month_map[month_name])
                    
                    event_date_obj = datetime.strptime(f"{day_part}/{month_part_str}/{event_year}", "%d/%m/%Y")
                    events.append({
                        "title": title,
                        "start": event_date_obj.strftime("%Y-%m-%d"),
                        "color": "#2ecc71" if completed else "#e74c3c"
                    })
                else: # fallback αν η μορφή δεν είναι η αναμενόμενη
                    # Αυτό το fallback μπορεί να μην είναι ιδανικό, χρειάζεται καλή μορφή ημερομηνίας στη βάση
                    day_only_from_actual = actual_date_part.split('/')[0]
                    event_date_obj = datetime.strptime(f"{day_only_from_actual}/{month_map[month_name]}/{event_year}", "%d/%m/%Y")
                    events.append({
                        "title": title,
                        "start": event_date_obj.strftime("%Y-%m-%d"),
                        "color": "#2ecc71" if completed else "#e74c3c"
                    })
            except ValueError:
                # st.warning(f"Calendar Date Parse Error: '{date_str_db}', Month: '{month_name}'")
                continue
            except Exception:
                # st.error(f"Unknown Calendar Date Error: {e} for '{date_str_db}'")
                continue
    return events


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
        ("έως 20/9", "Ορισμός συντονιστών"), 
        ("έως 20/9", "Ορισμός μέντορα"), 
        ("έως 20/9", "Προαιρετική Συγκρότηση Εκπαιδευτικών Ομίλων"), 
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
        ("23/12-9/1", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"), 
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
month_order = {name: i for i, name in enumerate(predefined_tasks.keys())}


def add_predefined_tasks(user_name):
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_name = ?", (user_name,))
    count = cursor.fetchone()[0]
    if count == 0:
        for month_val, tasks_list in predefined_tasks.items():
            for date_val, task_desc in tasks_list:
                title = task_desc
                cursor.execute("INSERT INTO tasks (user_name, month, date, title, task, completed) VALUES (?, ?, ?, ?, ?, ?)",
                               (user_name, month_val, date_val, title, task_desc, 0))
        conn.commit()
        return True
    return False

def get_tasks_from_db(user_name, month_val):
    cursor.execute("SELECT id, date, title, task, completed FROM tasks WHERE user_name = ? AND month = ? ORDER BY CASE WHEN date IS NULL THEN 1 ELSE 0 END, date",
                   (user_name, month_val))
    return cursor.fetchall()

def update_task(task_id, date_val, title_val):
    cursor.execute("UPDATE tasks SET date = ?, title = ? WHERE id = ?",
                   (date_val, title_val, task_id))
    conn.commit()

def add_task(user_name, month_val, date_val, title_val):
    cursor.execute("INSERT INTO tasks (user_name, month, date, title, task, completed) VALUES (?, ?, ?, ?, ?, ?)",
                   (user_name, month_val, date_val, title_val, title_val, 0))
    conn.commit()

def check_all_tasks(user_name, month_val):
    cursor.execute("UPDATE tasks SET completed = 1 WHERE user_name = ? AND month = ?",
                   (user_name, month_val))
    conn.commit()

def uncheck_all_tasks(user_name, month_val):
    cursor.execute("UPDATE tasks SET completed = 0 WHERE user_name = ? AND month = ?",
                   (user_name, month_val))
    conn.commit()

def is_task_urgent(date_str, task_month_name=None): # Προσθήκη task_month_name για context
    if not date_str:
        return False

    # Υπολογισμός έτους για τον έλεγχο προθεσμίας
    check_year = datetime.now().year
    if task_month_name and month_map[task_month_name] < 9 and datetime.now().month >= 9:
        check_year = datetime.now().year + 1
    elif task_month_name and month_map[task_month_name] >= 9 and datetime.now().month < 9:
         check_year = datetime.now().year -1


    try:
        end_date_part = ""
        if "έως" in date_str:
            end_date_part = date_str.split("έως")[-1].strip()
        elif "-" in date_str and "/" in date_str:
            if date_str.count('/') == 1: 
                range_part, month_part_str_urgent = date_str.split('/')
                day_part_urgent = range_part.split('-')[-1]
                end_date_part = f"{day_part_urgent}/{month_part_str_urgent}"
            else: 
                _, end_range_part = date_str.split('-')
                end_date_part = end_range_part.strip()
        elif "/" in date_str:
             return False 
        else: 
            return False

        if not end_date_part: return False

        if '/' not in end_date_part:
            if task_month_name and task_month_name in month_map:
                end_date_part = f"{end_date_part}/{month_map[task_month_name]}"
            else: # Δεν μπορούμε να προσδιορίσουμε τον μήνα
                return False
        
        end_date_obj = datetime.strptime(f"{end_date_part}/{check_year}", "%d/%m/%Y")
        today = datetime.now()
        return 0 <= (end_date_obj - today).days <= 2 # 0 για την ίδια μέρα, 1 για αύριο, 2 για μεθαύριο
    except ValueError:
        # st.warning(f"Urgent Date Parse Error: '{date_str}', Month: '{task_month_name}'")
        return False
    except Exception:
        return False


def export_to_ics(user_name):
    cal = icalendar.Calendar()
    cal.add('prodid', '-//My Task Calendar//mxm.dk//')
    cal.add('version', '2.0')
    cursor.execute("SELECT month, date, title, completed FROM tasks WHERE user_name = ?", (user_name,))
    tasks_db = cursor.fetchall()
    current_actual_year = datetime.now().year

    for month_name, date_str_db, title, completed in tasks_db:
        if date_str_db and month_name in month_map:
            event_year = current_actual_year
            if month_map[month_name] < 9 and datetime.now().month >=9:
                event_year = current_actual_year + 1
            elif month_map[month_name] >= 9 and datetime.now().month < 9:
                event_year = current_actual_year -1
            try:
                actual_date_part = ""
                if "έως" in date_str_db:
                    actual_date_part = date_str_db.split("έως")[-1].strip()
                elif "-" in date_str_db and "/" in date_str_db:
                     actual_date_part = date_str_db.split("-")[-1].strip()
                else:
                    actual_date_part = date_str_db.strip()

                if '/' not in actual_date_part:
                    actual_date_part = f"{actual_date_part}/{month_map[month_name]}"
                
                parts = actual_date_part.split('/')
                if len(parts) == 2:
                    day_part, month_part_str = parts
                    if not month_part_str.isdigit(): month_part_str = str(month_map[month_name])
                    event_date_obj = datetime.strptime(f"{day_part}/{month_part_str}/{event_year}", "%d/%m/%Y")
                else:
                    day_only_from_actual = actual_date_part.split('/')[0]
                    event_date_obj = datetime.strptime(f"{day_only_from_actual}/{month_map[month_name]}/{event_year}", "%d/%m/%Y")

                event_ics = icalendar.Event()
                event_ics.add('summary', title)
                event_ics.add('dtstart', event_date_obj.date())
                event_ics.add('dtend', (event_date_obj + timedelta(days=1)).date())
                event_ics.add('description', f"Κατάσταση: {'Ολοκληρωμένο' if completed else 'Εκκρεμές'}")
                cal.add_component(event_ics)
            except ValueError:
                # st.warning(f"ICS Date Parse Error: '{date_str_db}', Month: '{month_name}'")
                continue
            except Exception:
                continue
    buffer = BytesIO()
    buffer.write(cal.to_ical())
    buffer.seek(0)
    return buffer, "tasks.ics"

def save_pdf(user_name):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    # Τοποθέτηση του PDF στον τρέχοντα κατάλογο για απλότητα στο Render
    pdf_filename = f"{user_name}_all_tasks_{timestamp}.pdf" 
    
    # Προσωρινή απενεργοποίηση λήψης font για απλοποίηση αν δημιουργεί θέματα στο Render
    # Μπορείτε να το ενεργοποιήσετε αν έχετε τρόπο να διαχειριστείτε τα fonts στο Render
    font_path = None 
    active_font = "Helvetica" # Default σε Helvetica

    # Decomment to enable font download (ensure /tmp is writable on Render)
    # font_dir = "/tmp/dejavu-fonts-ttf-2.37/ttf/"
    # font_path = os.path.join(font_dir, "DejaVuSans.ttf")
    # if not os.path.exists(font_path):
    #     os.makedirs(font_dir, exist_ok=True)
    #     # st.info("Κατεβάζοντας γραμματοσειρά για το PDF (DejaVuSans)...") # Μπορεί να μην εμφανίζεται σωστά στο Render κατά τη δημιουργία PDF
    #     try:
    #         font_url = "https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version-2.37/dejavu-fonts-ttf-2.37.tar.bz2"
    #         font_archive_path = "/tmp/dejavu-fonts.tar.bz2"
    #         urllib.request.urlretrieve(font_url, font_archive_path)
    #         with tarfile.open(font_archive_path, "r:bz2") as tar:
    #             member_path = "dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf"
    #             tar.extract(member_path, path="/tmp")
    #         # st.success("Η γραμματοσειρά φορτώθηκε.")
    #         pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
    #         active_font = "DejaVuSans"
    #     except Exception as e:
    #         # st.error(f"Σφάλμα κατά τη λήψη/εξαγωγή γραμματοσειράς: {e}")
    #         active_font = "Helvetica"
    # else: # Font already exists
    #     try:
    #         pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
    #         active_font = "DejaVuSans"
    #     except Exception:
    #         active_font = "Helvetica"


    c = canvas.Canvas(pdf_filename, pagesize=A4)
    c.setFont(active_font, 12)
    
    page_width, page_height = A4
    margin = 50
    y_position = page_height - margin
    line_height = 18

    def draw_header_pdf(canvas_obj, user, font_name):
        canvas_obj.setFont(font_name, 16)
        canvas_obj.drawCentredString(page_width / 2, y_position, f"Προγραμματισμός Ενεργειών για {user}")
        return y_position - line_height * 2

    def check_page_break_pdf(canvas_obj, current_y, font_name):
        if current_y < margin + line_height:
            canvas_obj.showPage()
            canvas_obj.setFont(font_name, 10)
            return page_height - margin
        return current_y

    y_position = draw_header_pdf(c, user_name, active_font)
    c.setFont(active_font, 10)
    
    cursor.execute("SELECT month, date, title, task, completed FROM tasks WHERE user_name = ? ", (user_name,))
    all_user_tasks = cursor.fetchall()
    
    current_actual_year_pdf = datetime.now().year
    def sort_key_for_tasks(task_item_pdf):
        month_idx = month_order.get(task_item_pdf[0], 99)
        date_str_pdf_sort = task_item_pdf[1]
        parsed_date_pdf = None
        
        task_month_name_pdf = task_item_pdf[0]
        sort_year = current_actual_year_pdf
        if month_map[task_month_name_pdf] < 9 and datetime.now().month >= 9:
            sort_year = current_actual_year_pdf + 1
        elif month_map[task_month_name_pdf] >= 9 and datetime.now().month < 9:
            sort_year = current_actual_year_pdf -1

        if date_str_pdf_sort:
            try:
                actual_date_part_pdf = ""
                if "έως" in date_str_pdf_sort:
                    actual_date_part_pdf = date_str_pdf_sort.split("έως")[-1].strip()
                elif "-" in date_str_pdf_sort and "/" in date_str_pdf_sort:
                     actual_date_part_pdf = date_str_pdf_sort.split("-")[-1].strip()
                else:
                    actual_date_part_pdf = date_str_pdf_sort.strip()
                
                if '/' not in actual_date_part_pdf:
                    month_number_pdf = month_map.get(task_month_name_pdf)
                    if month_number_pdf:
                       actual_date_part_pdf = f"{actual_date_part_pdf}/{month_number_pdf}"
                
                parts_pdf = actual_date_part_pdf.split('/')
                if len(parts_pdf) == 2:
                    day_part_pdf, month_part_str_pdf = parts_pdf
                    if not month_part_str_pdf.isdigit(): month_part_str_pdf = str(month_map[task_month_name_pdf])
                    parsed_date_pdf = datetime.strptime(f"{day_part_pdf}/{month_part_str_pdf}/{sort_year}", "%d/%m/%Y")
                else:
                    day_only_pdf_sort = actual_date_part_pdf.split('/')[0]
                    parsed_date_pdf = datetime.strptime(f"{day_only_pdf_sort}/{month_map[task_month_name_pdf]}/{sort_year}", "%d/%m/%Y")
            except:
                parsed_date_pdf = datetime.min # Για ταξινόμηση, αν αποτύχει η ανάλυση
        return (month_idx, parsed_date_pdf if parsed_date_pdf else datetime.min, task_item_pdf[1] if task_item_pdf[1] else "")


    all_user_tasks_ordered = sorted(all_user_tasks, key=sort_key_for_tasks)
    
    current_month_pdf = None
    for month_pdf_val, date_pdf_val, title_pdf_val, task_pdf_desc, completed_pdf_val in all_user_tasks_ordered:
        y_position = check_page_break_pdf(c, y_position, active_font)
        if month_pdf_val != current_month_pdf:
            current_month_pdf = month_pdf_val
            y_position -= line_height
            y_position = check_page_break_pdf(c, y_position, active_font)
            c.setFont(active_font, 12)
            c.drawString(margin, y_position, month_pdf_val)
            c.setFont(active_font, 10)
            y_position -= line_height * 1.5

        date_str_for_pdf = date_pdf_val if date_pdf_val else "Χωρίς Ημ/νία"
        completed_status_pdf = "✓ (Ολοκληρωμένο)" if completed_pdf_val else "✗ (Εκκρεμές)"
        
        text_object_pdf = c.beginText(margin + 10, y_position)
        text_object_pdf.setFont(active_font, 10)
        
        line1_pdf = f"{date_str_for_pdf}: {title_pdf_val}"
        text_object_pdf.textLine(line1_pdf)
        y_position -= line_height

        text_object_pdf.setFillColorRGB(0.2, 0.2, 0.2)
        text_object_pdf.textLine(f"   Κατάσταση: {completed_status_pdf}")
        y_position -= line_height
        text_object_pdf.setFillColorRGB(0, 0, 0)

        if title_pdf_val != task_pdf_desc and task_pdf_desc:
            max_width_pdf = page_width - 2 * (margin + 10)
            desc_lines_pdf = []
            current_line_pdf = "   Περιγραφή: "
            words_pdf = task_pdf_desc.split(' ')
            for word_pdf in words_pdf:
                if c.stringWidth(current_line_pdf + word_pdf + " ", active_font, 10) <= max_width_pdf: # Προσθήκη κενού για καλύτερο υπολογισμό
                    current_line_pdf += word_pdf + " "
                else:
                    desc_lines_pdf.append(current_line_pdf.strip())
                    current_line_pdf = "     " + word_pdf + " "
            desc_lines_pdf.append(current_line_pdf.strip())

            for line_desc_pdf in desc_lines_pdf:
                y_position = check_page_break_pdf(c, y_position, active_font)
                text_object_pdf.setTextOrigin(margin + 10, y_position)
                text_object_pdf.textLine(line_desc_pdf)
                y_position -= line_height
        
        c.drawText(text_object_pdf)
        y_position -= line_height * 0.5
        
    c.save()
    return pdf_filename

# 📌 FullCalendar Markdown
calendar_events = get_calendar_events("Κώστα") # Κλήση μετά τον ορισμό της συνάρτησης
st.markdown(f"""
<link href='https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.css' rel='stylesheet' />
<script src='https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.js'></script>
<script src='https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/locales/el.js'></script>
<div id='calendar_div_main'></div>
<script>
document.addEventListener('DOMContentLoaded', function() {{
    var calendarEl = document.getElementById('calendar_div_main');
    if (calendarEl && typeof FullCalendar !== 'undefined') {{ // Έλεγχος και για το FullCalendar object
        try {{
            var calendar = new FullCalendar.Calendar(calendarEl, {{
                initialView: 'dayGridMonth',
                locale: 'el',
                height: '550px',
                events: {json.dumps(calendar_events)},
                eventClick: function(info) {{
                    alert('Εργασία: ' + info.event.title + '\\nΗμερομηνία: ' + new Date(info.event.start).toLocaleDateString('el-GR'));
                }},
                dateClick: function(info) {{
                    // Εδώ θα μπορούσατε να ανοίξετε τη φόρμα προσθήκης task για την επιλεγμένη ημερομηνία
                    // st.session_state.selected_date_for_new_task = info.dateStr;
                    // Δεν μπορούμε να καλέσουμε st.session_state απευθείας από JS, χρειάζεται άλλος μηχανισμός
                    // console.log('Date clicked: ' + info.dateStr);
                }}
            }});
            calendar.render();
        }} catch (e) {{
            console.error("Error rendering FullCalendar: ", e);
            calendarEl.innerHTML = "<p>Σφάλμα φόρτωσης ημερολογίου. Ελέγξτε την κονσόλα για λεπτομέρειες.</p>";
        }}
    }} else if (!calendarEl) {{
        console.error("Calendar element not found: calendar_div_main");
    }} else if (typeof FullCalendar === 'undefined') {{
         console.error("FullCalendar library not loaded.");
    }}
}});
</script>
""", unsafe_allow_html=True)


# 📌 Αρχικοποίηση session state
if "user_name" not in st.session_state:
    st.session_state.user_name = "Κώστας"
    if add_predefined_tasks(st.session_state.user_name):
        st.success("Οι προκαθορισμένες εργασίες προστέθηκαν για τον χρήστη Κώστα.")

if "edit_task_id" not in st.session_state:
    st.session_state.edit_task_id = None

# 📌 Κεφαλίδα
st.markdown('<div class="title">📋 Προγραμματισμός Ενεργειών</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">Γεια σου, {st.session_state.user_name}! Παρακολούθησε τις μηνιαίες σου εργασίες.</div>', unsafe_allow_html=True)

# 📌 Επιλογή μήνα
months_list = list(predefined_tasks.keys())
with st.container():
    st.markdown('<div class="month-select">', unsafe_allow_html=True)
    selected_month = st.selectbox("Επιλέξτε Μήνα:", months_list, label_visibility="visible", key="month_selector")
    st.markdown('</div>', unsafe_allow_html=True)

# 📌 Φόρμα προσθήκης task
st.markdown("### ➕ Προσθήκη Νέου Task")
with st.form("add_task_form", clear_on_submit=True):
    new_date = st.text_input("Ημερομηνία (π.χ. 15/9, έως 20/9, 1-5/9):", key="new_date_input_form")
    new_title = st.text_input("Τίτλος Εργασίας:", key="new_title_input_form")
    if st.form_submit_button("Προσθήκη Task"):
        if new_date and new_title:
            add_task(st.session_state.user_name, selected_month, new_date, new_title)
            st.success("Το task προστέθηκε επιτυχώς!")
            # Δεν χρειάζεται st.rerun() εδώ, το form submission το κάνει αυτόματα
        else:
            st.error("Παρακαλώ συμπληρώστε όλα τα πεδία.")

tasks = get_tasks_from_db(st.session_state.user_name, selected_month)

total_tasks = len(tasks)
completed_tasks_count = sum(1 for task_item in tasks if task_item[4] == 1)
progress_percentage = (completed_tasks_count / total_tasks) * 100 if total_tasks > 0 else 0

st.markdown(f'<div class="progress-container"><strong>Πρόοδος {selected_month}</strong></div>', unsafe_allow_html=True)
if total_tasks > 0:
    st.progress(progress_percentage / 100.0)
    st.markdown(f'<div class="progress-container">{completed_tasks_count}/{total_tasks} εργασίες ({progress_percentage:.0f}%)</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="progress-container">Καμία εργασία για εμφάνιση</div>', unsafe_allow_html=True)

if tasks:
    col_check, col_uncheck, col_export_ics, col_export_pdf_col = st.columns([1,1,1.5,1.5])

    with col_check:
        if st.button("Επιλογή Όλων", key="check_all_btn_ui", help="Επιλέγει όλες τις εργασίες του μήνα", use_container_width=True):
            check_all_tasks(st.session_state.user_name, selected_month)
            # Δεν χρειάζεται st.rerun()
    with col_uncheck:
        if st.button("Αποεπιλογή Όλων", key="uncheck_all_btn_ui", help="Αποεπιλέγει όλες τις εργασίες του μήνα", use_container_width=True):
            uncheck_all_tasks(st.session_state.user_name, selected_month)
            # Δεν χρειάζεται st.rerun()
    with col_export_ics:
        ics_file_data, ics_filename_data = export_to_ics(st.session_state.user_name)
        st.download_button(
            label="Λήψη ICS Ημερολογίου",
            data=ics_file_data,
            file_name=ics_filename_data,
            mime="text/calendar",
            help="Εξαγωγή όλων των tasks σε ICS αρχείο για Google Calendar",
            use_container_width=True,
            key="download_ics_btn"
        )
    with col_export_pdf_col:
        if st.button("Εξαγωγή σε PDF", help="Εξαγωγή όλων των tasks σε PDF", key="export_pdf_main_btn", use_container_width=True):
            pdf_filename_tmp = save_pdf(st.session_state.user_name)
            if pdf_filename_tmp:
                with open(pdf_filename_tmp, "rb") as fp:
                    st.download_button( 
                        label="Λήψη PDF Τώρα",
                        data=fp,
                        file_name=os.path.basename(pdf_filename_tmp),
                        mime="application/pdf",
                        key="download_pdf_final_btn",
                        use_container_width=True
                    )
                # Δεν χρειάζεται st.rerun() ούτε εδώ
            else:
                st.error("Αποτυχία δημιουργίας PDF.")

st.markdown("---")

st.markdown(f"### 📌 Εργασίες {selected_month}")
if not tasks:
    st.info(f"Δεν υπάρχουν εργασίες για τον μήνα {selected_month}.")
else:
    for task_id, date_val, title_val, task_desc, completed_status in tasks:
        task_key_prefix = f"task_{task_id}_{selected_month.replace(' ', '_')}"
        is_urgent_task = is_task_urgent(date_val, selected_month) # Περνάμε και τον μήνα για context

        container_class = "task-container"
        if is_urgent_task:
            container_class += " task-urgent"

        with st.container():
            st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)
            cols_display = st.columns([0.5, 5, 0.5, 0.5])

            with cols_display[0]:
                is_checked_val = completed_status == 1
                st.checkbox(
                    f"##{task_id}_cb",
                    value=is_checked_val,
                    key=f"cb_{task_key_prefix}_display",
                    on_change=(lambda tid, current_status_val: ( # Άλλαξα το όνομα current_status
                        cursor.execute("UPDATE tasks SET completed = ? WHERE id = ?", (0 if current_status_val else 1, tid)),
                        conn.commit()
                        # Δεν χρειάζεται st.rerun() εδώ, το on_change το κάνει αυτόματα
                    )),
                    args=(task_id, is_checked_val),
                    label_visibility="collapsed"
                )
            with cols_display[1]:
                status_emoji = "🟢" if completed_status else "🔴"
                display_date_str = date_val if date_val else "Χωρίς Ημ/νία"
                st.markdown(f'<span class="task-title">{title_val}</span> <span class="task-status">{status_emoji}</span>', unsafe_allow_html=True)
                st.markdown(f'<span class="task-date">{display_date_str}</span>', unsafe_allow_html=True)
                if title_val != task_desc and task_desc:
                    st.caption(task_desc)
                if is_urgent_task:
                    st.markdown('<span style="color: #e74c3c; font-size: 0.9em;">⚠️ Επείγουσα προθεσμία!</span>', unsafe_allow_html=True)

            with cols_display[2]:
                if st.button("🗑️", key=f"delete_{task_key_prefix}_display", help="Διαγραφή Εργασίας"):
                    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                    conn.commit()
                    # Δεν χρειάζεται st.rerun()
            with cols_display[3]:
                if st.button("✏️", key=f"edit_{task_key_prefix}_display", help="Επεξεργασία Εργασίας"):
                    st.session_state.edit_task_id = task_id
                    # Δεν χρειάζεται st.rerun() εδώ, η αλλαγή στο session_state θα την πιάσει το επόμενο rerun
            st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.edit_task_id is not None:
    active_task_id = st.session_state.edit_task_id
    cursor.execute("SELECT date, title FROM tasks WHERE id = ?", (active_task_id,))
    task_data_to_edit = cursor.fetchone()

    if task_data_to_edit:
        st.markdown("### ✏️ Επεξεργασία Εργασίας")
        with st.form(f"edit_task_form_{active_task_id}_main", clear_on_submit=True):
            edit_date_val_form = st.text_input("Ημερομηνία (π.χ. 15/9, έως 20/9):", value=task_data_to_edit[0] or "", key=f"edit_date_{active_task_id}_form")
            edit_title_val_form = st.text_input("Τίτλος Εργασίας:", value=task_data_to_edit[1], key=f"edit_title_{active_task_id}_form")

            form_cols_edit = st.columns(2)
            with form_cols_edit[0]:
                if st.form_submit_button("Αποθήκευση", key="save_edit_btn"):
                    update_task(active_task_id, edit_date_val_form, edit_title_val_form)
                    st.session_state.edit_task_id = None
                    st.success("Η εργασία ενημερώθηκε επιτυχώς!")
                    # Δεν χρειάζεται st.rerun()
            with form_cols_edit[1]:
                if st.form_submit_button("Ακύρωση", key="cancel_edit_btn"):
                    st.session_state.edit_task_id = None
                    # Δεν χρειάζεται st.rerun()
    else:
        st.session_state.edit_task_id = None


st.markdown("---")
st.markdown("*Σύστημα Παρακολούθησης Εργασιών Διευθυντή*")
