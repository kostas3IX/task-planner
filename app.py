import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import icalendar
from io import BytesIO
import uuid
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 📌 Ρύθμιση Streamlit UI
st.set_page_config(
    page_title="Προγραμματισμός Ενεργειών",
    page_icon="📋",
    layout="wide"
)

# 📌 Custom CSS με μειωμένη απόσταση εργασιών
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
        padding: 8px;
        margin: 2px 0;
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
    .reset-button {
        background-color: #95a5a6;
    }
    .reset-button:hover {
        background-color: #7f8c8d;
    }
    .print-button {
        background-color: #17a2b8;
    }
    .print-button:hover {
        background-color: #138496;
    }
</style>
""", unsafe_allow_html=True)

# 📌 Εμφάνιση τρέχουσας ημερομηνίας
current_time = datetime.now().strftime("%H:%M:%S EEST, %A, %d %B %Y")
st.markdown(f'<div class="clock">{current_time}</div>', unsafe_allow_html=True)

# 📌 Σύνδεση με SQLite
conn = sqlite3.connect("tasks.db", check_same_thread=False)
cursor = conn.cursor()

# 📌 Δημιουργία πίνακα με πεδίο sort_date
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT,
    month TEXT,
    date TEXT,
    title TEXT,
    task TEXT,
    completed INTEGER,
    sort_date DATETIME
)
""")
conn.commit()

month_map = {
    "Σεπτέμβριος": 9, "Οκτώβριος": 10, "Νοέμβριος": 11, "Δεκέμβριος": 12,
    "Ιανουάριος": 1, "Φεβρουάριος": 2, "Μάρτιος": 3, "Απρίλιος": 4,
    "Μάιος": 5, "Ιούνιος": 6, "Ιούλιος": 7, "Αύγουστος": 8
}

month_genitive_map = {
    "Σεπτέμβριος": "Σεπτεμβρίου",
    "Οκτώβριος": "Οκτωβρίου",
    "Νοέμβριος": "Νοεμβρίου",
    "Δεκέμβριος": "Δεκεμβρίου",
    "Ιανουάριος": "Ιανουαρίου",
    "Φεβρουάριος": "Φεβρουαρίου",
    "Μάρτιος": "Μαρτίου",
    "Απρίλιος": "Απριλίου",
    "Μάιος": "Μαΐου",
    "Ιούνιος": "Ιουνίου",
    "Ιούλιος": "Ιουλίου",
    "Αύγουστος": "Αυγούστου"
}

target_year_for_dates = datetime.now().year
if datetime.now().month > 8:
    target_year_for_dates = datetime.now().year if datetime.now().month < 9 else datetime.now().year + 1

# 📌 Ορισμοί Συναρτήσεων
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

def parse_date_for_sort(date_str, month_name, year):
    if not date_str or date_str == "Χωρίς Ημ/νία":
        return datetime(9999, 12, 31)
    try:
        month_num = month_map[month_name]
        actual_date_part = ""
        if "έως" in date_str:
            actual_date_part = date_str.split("έως")[-1].strip()
        elif "-" in date_str and "/" in date_str:
            actual_date_part = date_str.split("-")[-1].strip()
        else:
            actual_date_part = date_str.strip()
        
        if '/' not in actual_date_part:
            actual_date_part = f"{actual_date_part}/{month_num}"
        
        parts = actual_date_part.split('/')
        if len(parts) == 2:
            day_part, month_part_str = parts
            if not month_part_str.isdigit():
                month_part_str = str(month_num)
            return datetime.strptime(f"{day_part}/{month_part_str}/{year}", "%d/%m/%Y")
        else:
            day_only = actual_date_part.split('/')[0]
            return datetime.strptime(f"{day_only}/{month_num}/{year}", "%d/%m/%Y")
    except:
        return datetime(9999, 12, 31)

def add_predefined_tasks(user_name):
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_name = ?", (user_name,))
    count = cursor.fetchone()[0]
    if count == 0:
        current_year = datetime.now().year
        for month_val, tasks_list in predefined_tasks.items():
            month_year = current_year
            if month_map[month_val] < 9 and datetime.now().month >= 9:
                month_year = current_year + 1
            elif month_map[month_val] >= 9 and datetime.now().month < 9:
                month_year = current_year - 1
            for date_val, task_desc in tasks_list:
                title = task_desc
                sort_date = parse_date_for_sort(date_val, month_val, month_year)
                cursor.execute("INSERT INTO tasks (user_name, month, date, title, task, completed, sort_date) VALUES (?,?, ?, ?, ?, ?, ?)",
                               (user_name, month_val, date_val, title, task_desc, 0, sort_date))
        conn.commit()
        return True
    return False

def reset_tasks(user_name):
    cursor.execute("DELETE FROM tasks WHERE user_name = ?", (user_name,))
    conn.commit()
    add_predefined_tasks(user_name)

def get_tasks_from_db(user_name, month_val):
    cursor.execute("SELECT id, date, title, task, completed FROM tasks WHERE user_name = ? AND month = ? ORDER BY sort_date",
                   (user_name, month_val))
    return cursor.fetchall()

def update_task(task_id, date_val, title_val, task_val, month_name):
    current_year = datetime.now().year
    if month_map[month_name] < 9 and datetime.now().month >= 9:
        current_year += 1
    elif month_map[month_name] >= 9 and datetime.now().month < 9:
        current_year -= 1
    sort_date = parse_date_for_sort(date_val, month_name, current_year)
    cursor.execute("UPDATE tasks SET date = ?, title = ?, task = ?, sort_date = ? WHERE id = ?",
                   (date_val, title_val, task_val, sort_date, task_id))
    conn.commit()

def add_task(user_name, month_val, date_val, title_val):
    current_year = datetime.now().year
    if month_map[month_val] < 9 and datetime.now().month >= 9:
        current_year += 1
    elif month_map[month_val] >= 9 and datetime.now().month < 9:
        current_year -= 1
    sort_date = parse_date_for_sort(date_val, month_val, current_year)
    cursor.execute("INSERT INTO tasks (user_name, month, date, title, task, completed, sort_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (user_name, month_val, date_val, title_val, title_val, 0, sort_date))
    conn.commit()

def check_all_tasks(user_name, month_val):
    cursor.execute("UPDATE tasks SET completed = 1 WHERE user_name = ? AND month = ?",
                   (user_name, month_val))
    conn.commit()

def uncheck_all_tasks(user_name, month_val):
    cursor.execute("UPDATE tasks SET completed = 0 WHERE user_name = ? AND month = ?",
                   (user_name, month_val))
    conn.commit()

def is_task_urgent(date_str, task_month_name=None):
    if not date_str:
        return False
    check_year = datetime.now().year
    if task_month_name and month_map[task_month_name] < 9 and datetime.now().month >= 9:
        check_year = datetime.now().year + 1
    elif task_month_name and month_map[task_month_name] >= 9 and datetime.now().month < 9:
        check_year = datetime.now().year - 1
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
        if not end_date_part:
            return False
        if '/' not in end_date_part:
            if task_month_name and task_month_name in month_map:
                end_date_part = f"{end_date_part}/{month_map[task_month_name]}"
            else:
                return False
        end_date_obj = datetime.strptime(f"{end_date_part}/{check_year}", "%d/%m/%Y")
        today = datetime.now()
        return 0 <= (end_date_obj - today).days <= 2
    except ValueError:
        return False
    except Exception:
        return False

def export_to_ics(user_name):
    cal = icalendar.Calendar()
    cal.add('prodid', '-//My Task Calendar//mxm.dk//')
    cal.add('version', '2.0')
    cursor.execute("SELECT month, date, title, completed, sort_date FROM tasks WHERE user_name = ?", (user_name,))
    tasks_db = cursor.fetchall()
    for month_name, date_str_db, title, completed, sort_date in tasks_db:
        if date_str_db and month_name in month_map:
            try:
                event_date_obj = sort_date
                if event_date_obj.year == 9999:
                    continue
                event_ics = icalendar.Event()
                event_ics.add('summary', title)
                event_ics.add('dtstart', event_date_obj.date())
                event_ics.add('dtend', (event_date_obj + timedelta(days=1)).date())
                event_ics.add('description', f"Κατάσταση: {'Ολοκληρωμένο' if completed else 'Εκκρεμές'}")
                cal.add_component(event_ics)
            except ValueError:
                continue
            except Exception:
                continue
    buffer = BytesIO()
    buffer.write(cal.to_ical())
    buffer.seek(0)
    return buffer, "tasks.ics"

def generate_pdf(user_name, selected_month):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 20 * mm
    y_position = height - margin

    # Register DejaVu Sans font
    try:
        pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        font_name = 'DejaVuSans'
    except:
        # Fallback to Helvetica if DejaVuSans is not available
        font_name = 'Helvetica'

    c.setFont(font_name, 16)
    c.drawCentredString(width / 2, y_position, "Προγραμματισμός Ενεργειών")
    y_position -= 15 * mm

    c.setFont(font_name, 12)
    c.drawCentredString(width / 2, y_position, f"Γεια σου, Κώστα! Εργασίες {selected_month}")
    y_position -= 10 * mm

    c.setFont(font_name, 10)
    c.drawCentredString(width / 2, y_position, current_time)
    y_position -= 15 * mm

    c.setFont(font_name, 12)
    c.drawString(margin, y_position, f"Εργασίες {selected_month}")
    y_position -= 10 * mm

    tasks = get_tasks_from_db(user_name, selected_month)
    for task_id, date_val, title_val, task_desc, completed_status in tasks:
        if y_position < margin:
            c.showPage()
            y_position = height - margin
            c.setFont(font_name, 12)
        
        status = "Ολοκληρωμένο" if completed_status else "Εκκρεμές"
        date_display = date_val if date_val else "Χωρίς Ημ/νία"
        is_urgent = is_task_urgent(date_val, selected_month)
        task_text = f"{date_display}: {title_val} ({status})"
        if is_urgent:
            task_text += " ⚠️ Επείγουσα"
        
        # Wrap text to fit within page width
        lines = []
        current_line = ""
        for word in task_text.split():
            if c.stringWidth(current_line + word, font_name, 12) < (width - 2 * margin):
                current_line += word + " "
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())
        
        for line in lines:
            if y_position < margin:
                c.showPage()
                y_position = height - margin
                c.setFont(font_name, 12)
            c.drawString(margin, y_position, line)
            y_position -= 7 * mm

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# 📌 Αρχικοποίηση session state
if "user_name" not in st.session_state:
    st.session_state.user_name = "Κώστας"
    if add_predefined_tasks(st.session_state.user_name):
        st.success("Οι προκαθορισμένες εργασίες προστέθηκαν για τον χρήστη Κώστας.")

if "edit_task_id" not in st.session_state:
    st.session_state.edit_task_id = None

# 📌 Κεφαλίδα
st.markdown('<div class="title">📋 Προγραμματισμός Ενεργειών</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Γεια σου, Κώστα! Παρακολούθησε τις μηνιαίες σου εργασίες.</div>', unsafe_allow_html=True)

# 📌 Επιλογή μήνα
months_list = list(predefined_tasks.keys())
with st.container():
    st.markdown('<div class="month-select">', unsafe_allow_html=True)
    selected_month = st.selectbox("Επιλέξτε Μήνα:", months_list, label_visibility="visible")
    st.markdown('</div>', unsafe_allow_html=True)

# 📌 Φόρμα προσθήκης task
st.markdown("### ➕ Προσθήκη Νέου Task")
with st.form("add_task_form", clear_on_submit=True):
    new_date = st.text_input("Ημερομηνία (π.χ. 15/9, έως 20/9, 1-5/9):")
    new_title = st.text_input("Τίτλος Εργασίας:")
    if st.form_submit_button("Προσθήκη Task"):
        if new_date and new_title:
            add_task(st.session_state.user_name, selected_month, new_date, new_title)
            st.success("Το task προστέθηκε επιτυχώς!")
        else:
            st.error("Παρακαλώ συμπληρώστε όλα τα πεδία.")

tasks = get_tasks_from_db(st.session_state.user_name, selected_month)

total_tasks = len(tasks)
completed_tasks_count = sum(1 for task_item in tasks if task_item[4] == 1)
progress_percentage = (completed_tasks_count / total_tasks) * 100 if total_tasks > 0 else 0

st.markdown(f'<div class="progress-container"><strong>Πρόοδος {month_genitive_map[selected_month]}</strong></div>', unsafe_allow_html=True)
if total_tasks > 0:
    st.progress(progress_percentage / 100.0)
    st.markdown(f'<div class="progress-container">{completed_tasks_count}/{total_tasks} εργασίες ({progress_percentage:.0f}%)</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="progress-container">Καμία εργασία για εμφάνιση</div>', unsafe_allow_html=True)

if tasks:
    col_check, col_uncheck, col_reset, col_export_ics, col_print = st.columns([1, 1, 1, 1.5, 1.5])
    with col_check:
        if st.button("Επιλογή Όλων", help="Επιλέγει όλες τις εργασίες του μήνα", use_container_width=True):
            check_all_tasks(st.session_state.user_name, selected_month)
    with col_uncheck:
        if st.button("Αποεπιλογή Όλων", help="Αποεπιλέγει όλες τις εργασίες του μήνα", use_container_width=True):
            uncheck_all_tasks(st.session_state.user_name, selected_month)
    with col_reset:
        if st.button("Αρχικοποίηση", help="Επαναφέρει τις προκαθορισμένες εργασίες", use_container_width=True):
            st.warning("Όλες οι εργασίες θα διαγραφούν και θα επαναφερθούν οι προκαθορισμένες. Συνέχεια;")
            reset_tasks(st.session_state.user_name)
            st.success("Οι εργασίες επαναφέρθηκαν επιτυχώς!")
    with col_export_ics:
        ics_file_data, ics_filename_data = export_to_ics(st.session_state.user_name)
        st.download_button(
            label="Λήψη ICS Ημερολογίου",
            data=ics_file_data,
            file_name=ics_filename_data,
            mime="text/calendar",
            help="Εξαγωγή όλων των tasks σε ICS αρχείο για Google Calendar",
            use_container_width=True
        )
    with col_print:
        pdf_data = generate_pdf(st.session_state.user_name, selected_month)
        st.download_button(
            label="Εκτύπωση σε PDF",
            data=pdf_data,
            file_name=f"tasks_{selected_month}.pdf",
            mime="application/pdf",
            help="Δημιουργεί και κατεβάζει ένα PDF με τις εργασίες του μήνα",
            use_container_width=True
        )

# 📌 Ενότητα εργασιών
st.markdown(f'<div class="task-section"><h3>📌 Εργασίες {selected_month}</h3></div>', unsafe_allow_html=True)
if not tasks:
    st.markdown(f'<div class="task-section">Δεν υπάρχουν εργασίες για τον μήνα {selected_month}.</div>', unsafe_allow_html=True)
else:
    for task_id, date_val, title_val, task_desc, completed_status in tasks:
        task_key_prefix = f"task_{task_id}_{selected_month.replace(' ', '_')}"
        is_urgent_task = is_task_urgent(date_val, selected_month)
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
                    on_change=(lambda tid, current_status_val: (
                        cursor.execute("UPDATE tasks SET completed = ? WHERE id = ?", (0 if current_status_val else 1, tid)),
                        conn.commit()
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
                    st.rerun()
            with cols_display[3]:
                if st.button("✏️", key=f"edit_{task_key_prefix}_display", help="Επεξεργασία Εργασίας"):
                    st.session_state.edit_task_id = task_id
            st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.edit_task_id is not None:
    active_task_id = st.session_state.edit_task_id
    cursor.execute("SELECT date, title, task FROM tasks WHERE id = ?", (active_task_id,))
    task_data_to_edit = cursor.fetchone()
    if task_data_to_edit:
        st.markdown("### ✏️ Επεξεργασία Εργασίας")
        with st.form(f"edit_task_form_{active_task_id}_main", clear_on_submit=True):
            edit_date_val_form = st.text_input("Ημερομηνία (π.χ. 15/9, έως 20/9):", value=task_data_to_edit[0] or "")
            edit_title_val_form = st.text_input("Τίτλος Εργασίας:", value=task_data_to_edit[1])
            edit_task_val_form = st.text_input("Περιγραφή Εργασίας:", value=task_data_to_edit[2])
            form_cols_edit = st.columns(2)
            with form_cols_edit[0]:
                if st.form_submit_button("Αποθήκευση"):
                    update_task(active_task_id, edit_date_val_form, edit_title_val_form, edit_task_val_form, selected_month)
                    st.session_state.edit_task_id = None
                    st.success("Η εργασία ενημερώθηκε επιτυχώς!")
                    st.rerun()
            with form_cols_edit[1]:
                if st.form_submit_button("Ακύρωση"):
                    st.session_state.edit_task_id = None
                    st.rerun()
    else:
        st.session_state.edit_task_id = None

st.markdown("---")
st.markdown("*Σύστημα Παρακολούθησης Εργασιών Διευθυντή*")
