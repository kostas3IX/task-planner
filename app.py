import streamlit as st
import sqlite3
import pandas as pd
from reportlab.pdfgen import canvas # Make sure reportlab is installed (`pip install reportlab`)

# 📌 Σύνδεση με βάση δεδομένων SQLite
# Χρησιμοποιούμε ένα μονοπάτι που είναι πιο πιθανό να λειτουργήσει σε περιβάλλοντα cloud όπως το Render
# ή μπορείτε να παραμείνετε στο απλό 'tasks.db' αν το Render χειρίζεται σωστά τα αρχεία.
# Για μεγαλύτερη συμβατότητα, ας παραμείνουμε στο απλό όνομα, καθώς το πρόβλημα φαίνεται αλλού.
conn = sqlite3.connect("tasks.db")
cursor = conn.cursor()

# 📌 Δημιουργία πίνακα αν δεν υπάρχει
# Διόρθωση: Αφαιρέθηκε το AUTOINCREMENT. Σε SQLite, ένα INTEGER PRIMARY KEY αυτόματα αυξάνεται (autoincrements)
# χωρίς την ανάγκη της λέξης-κλειδιού AUTOINCREMENT, η οποία είναι πιο αυστηρή και μπορεί
# να προκαλέσει προβλήματα σε ορισμένες υλοποιήσεις ή εκδόσεις του SQLite.
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
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
# Σημείωση: Χρησιμοποιούμε την ημερομηνία/περίοδο για το πεδίο 'date'
# και ολόκληρη την περιγραφή για τα πεδία 'title' και 'task'
# καθώς η αρχική λίστα δεν έχει διακριτό τίτλο και περιγραφή.
predefined_tasks = {
    "Σεπτέμβριος": [
        ("1/9", "Πράξη ανάληψης υπηρεσίας"),
        ("1-5/9", "Προγραμματισμός αγιασμού - ενημέρωση γονέων - ανάρτηση στην ιστοσελίδα"),
        ("έως 10/9", "Πρακτικό: Ανάθεση τμημάτων - διδασκαλιών - ολοήμερου - ΠΖ"),
        ("έως 10/9", "Πρακτικό: Διαμόρφωση ομίλων στο αναβαθμισμένο πρόγραμμα ολοημέρου (προτάσεις από τα άτομα που θα διδάσκουν)"),
        ("έως 10/9", "Πρακτικό: Εξωδιδακτικές αρμοδιότητες"),
        ("έως 10/9", "Πρακτικό: Ανάθεση σχολικών εορτών, επετείων, ομιλιών"),
        ("έως 10/9", "Πρακτικό: Εφημερίες - ασφάλεια μαθητών"),
        ("έως 10/9", "Πρακτικό: Αναπλήρωση απόντων εκπαιδευτικών"),
        ("έως 10/9", "Πρακτικό: Επιλογή βιβλίων Β’ ξένης γλώσσας"),
        ("έως 10/9", "Εσωτερικός κανονισμός λειτουργίας - επικαιροποίηση - ανάρτηση στην ιστοσελίδα του σχολείου"),
        ("έως 10/9", "Σχολικό Συμβούλιο; Κοινή συνεδρίαση συστεγαζόμενων"),
        ("έως 10/9", "Οργάνωση του Myschool (Αναλήψεις υπηρεσίας, έλεγχος-εγγραφή μαθητών Α, τμήματα, Ολοήμερο, Πρωινή Ζώνη, αναθέσεις μαθημάτων, μαθητές με ειδικές εκπαιδευτικές ανάγκες)"),
        ("11/9", "Ωρολόγιο πρόγραμμα - (έστω προσωρινό)"),
        ("11/9", "Ωρολόγιο πρόγραμμα εξ αποστάσεως"),
        ("11/9", "Αγιασμός. Καλωσόρισμα - υποδοχή γονέων Α’ τάξης"),
        ("12/9", "Αποστολή δηλώσεων στους γονείς των παιδιών που επέλεξαν τη συμμετοχή στο αναβαθμισμένο ολοήμερο για την επιλογή των ομίλων."),
        ("15/9", "Επιβεβαίωση Δεδομένων Myschool"),
        ("έως 20", "Ορισμός συντονιστών"),
        ("έως 20", "Ορισμός μέντορα"),
        ("έως 20", "Προαιρετική Συγκρότηση Εκπαιδευτικών Ομίλων"),
        ("έως 20/9", "Προγραμματισμός συναντήσεων με γονείς (οι συναντήσεις μπορούν να γίνουν 26-30/9)"),
        ("έως 30/9", "Ειδική συνεδρίαση του Συλλόγου Διδασκόντων για τον καθορισμό του ετήσιου Σχεδίου Δράσης της σχολικής μονάδας αναφορικά με τα Εργαστήρια Δεξιοτήτων"),
        ("έως 30/9", "Προγραμματισμός 15ωρων ενδοσχολικών (είναι αρμοδιότητα του Διευθυντή αλλά είναι χρήσιμο - και δεσμευτικό - να ερωτάται ο Σύλλογος Διδασκόντων)"),
        ("έως 30/9", "Έλεγχος μαθητικών λογαριασμών των μαθητών της Α τάξης και των εκ μετεγγραφής στο sch.gr"),
        ("έως 30/9", "Προγραμματισμός Α’ τριμήνου (επισκέψεις, εκδρομές, ημέρες και ώρες που οι εκπαιδευτικοί δέχονται γονείς)"),
        ("έως 30/9", "Διαδικασία ανάθεσης και έγκρισης για τη συμπλήρωση του υποχρεωτικού διδακτικού ωραρίου (προτεραιότητα ενισχυτική διδασκαλία, γραμματειακή υποστήριξη) (Ν. 4386/2016, άρθρο 33, παρ. 5, όπως τροποποιήθηκε και ισχύει)"),
        ("30/9-3/10", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"),
    ],
    "Οκτώβριος": [
        ("1/10", "Επιβεβαίωση Δεδομένων Myschool"),
        (None, "1η παιδαγωγική συνεδρίαση"), # No specific date given
        ("4/10", "Παγκόσμια ημέρα των ζώων"),
        ("5/10", "Παγκόσμια Ημέρα Εκπαιδευτικών"),
        ("έως 10/10", "Μνημόνιο ενεργειών εκτάκτων αναγκών - Ενημέρωση γονέων στην ιστοσελίδα."),
        ("έως 10/10", "Συνεδρίαση για τον Συλλογικό Προγραμματισμό όπου προτείνονται Σχέδια Δράσης, συγκροτούνται Ομάδες Δράσης"),
        ("15/10", "Επιβεβαίωση Δεδομένων Myschool"),
        ("έως 20/10", "Καταχώρηση τίτλων & σχεδίων δράσης στην πλατφόρμα"),
        ("έως 21/10", "Επιλογή σημαιοφόρων"),
        ("31/10-3/11", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"),
    ],
    "Νοέμβριος": [
        ("1/11", "Επιβεβαίωση Δεδομένων Myschool"),
        (None, "2η παιδαγωγική συνεδρίαση"), # No specific date given
        ("έως 10/11", "Σχολικό Συμβούλιο"),
        ("15/11", "Επιβεβαίωση Δεδομένων Myschool"),
        ("20/11", "Παγκόσμια Ημέρα για τα δικαιώματα του Παιδιού"),
        ("30/11-2/12", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"),
    ],
    "Δεκέμβριος": [
        ("1/12", "Επιβεβαίωση Δεδομένων Myschool"),
        ("3/12", "Παγκόσμια Ημέρα Ατόμων με Αναπηρία"),
        ("έως 10/12", "Καταχώρηση του Σχεδιασμού Δράσης από τους ΣΥΝΤΟΝΙΣΤΕΣ ΟΜΑΔΩΝ ΔΡΑΣΗΣ"),
        (None, "3η παιδαγωγική συνεδρίαση - Προγραμματισμός Β’ τριμήνου (επισκέψεις, εκδρομές)"), # No specific date given
        ("10/12", "Λήξη Α’ τριμήνου"),
        (None, "Επίδοση ελέγχων"), # No specific date given, follows 10/12
        ("15/12", "Επιβεβαίωση Δεδομένων Myschool"),
        ("23/12-9/1/23", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"),
        ("23/12 έως και 7/1", "Διακοπές Χριστουγέννων"),
    ],
    "Ιανουάριος": [
        ("9/1", "Επιβεβαίωση Δεδομένων Myschool"),
        (None, "4η παιδαγωγική συνεδρίαση"), # No specific date given
        ("έως 15/1", "Σχολικό Συμβούλιο"),
        ("15/1", "Επιβεβαίωση Δεδομένων Myschool"),
        ("31/1-3/2", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"),
    ],
    "Φεβρουάριος": [
        ("1/2", "Επιβεβαίωση Δεδομένων Myschool"),
        (None, "Ημέρα Ασφαλούς Διαδικτύου – Safer Internet Day"), # Date varies
        (None, "5η παιδαγωγική συνεδρίαση"), # No specific date given
        ("15/2", "Επιβεβαίωση Δεδομένων Myschool"),
        ("28/2-3/3", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"),
    ],
    "Μάρτιος": [
        ("1/3", "Επιβεβαίωση Δεδομένων Myschool"),
        ("έως 10/3", "Σχολικό Συμβούλιο"),
        ("1-20/3", "Εγγραφές-Αποστολή στοιχείων στη ΔΙΠΕ"),
        ("6/3", "Πανελλήνια Ημέρα κατά της σχολικής βίας και του εκφοβισμού"),
        (None, "6η παιδαγωγική συνεδρίαση - Προγραμματισμός Γ’ τριμήνου (επισκέψεις, εκδρομές)"), # No specific date given
        ("10/3", "Λήξη Β΄ τριμήνου"),
        (None, "Επίδοση ελέγχων"), # No specific date given, follows 10/3
        ("15/3", "Επιβεβαίωση Δεδομένων Myschool"),
        ("21/3", "Παγκόσμια Ημέρα Ποίησης"),
        ("31/3-3/4", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"), # Corrected range assuming typo
    ],
    "Απρίλιος": [
        ("1/4", "Επιβεβαίωση Δεδομένων Myschool"),
        ("2/4", "Παγκόσμια Ημέρα Παιδικού Βιβλίου"),
        (None, "7η παιδαγωγική συνεδρίαση"), # No specific date given
        ("27/4-12/5", "Διακοπές Πάσχα"), # Dates are examples, vary yearly
        ("22/4", "Ημέρα της Γης"),
        ("23/4", "Παγκόσμια Ημέρα Βιβλίου"),
        ("24/4", "Επιβεβαίωση Δεδομένων Myschool"),
        ("28/4-3/5", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"),
    ],
    "Μάιος": [
        ("1/5", "Επιβεβαίωση Δεδομένων Myschool"),
        (None, "8η παιδαγωγική συνεδρίαση"), # No specific date given
        ("9/5", "Ημέρα της Ευρώπης"),
        ("15/5", "Επιβεβαίωση Δεδομένων Myschool"),
        ("19/5", "Ημέρα Μνήμης για τη Γενοκτονία των Ελλήνων στο Μικρασιατικό Πόντο"),
        (None, "Λήξη ενεργειών προγραμματισμού Ολοήμερου Προγράμματος-Αποστολή στοιχείων στη ΔΙΠΕ"), # No specific date given
        ("έως 31/5", "Υλοποίηση και καταχώρηση της αποτίμησης των δράσεων από τους ΣΥΝΤΟΝΙΣΤΕΣ ΟΜΑΔΩΝ ΔΡΑΣΗΣ"),
        ("έως 31/5", "Σχολικό Συμβούλιο"),
        ("31/5-2/6", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"),
    ],
    "Ιούνιος": [
        ("1/6", "Επιβεβαίωση Δεδομένων Myschool"),
        (None, "9η παιδαγωγική συνεδρίαση για την έκδοση αποτελεσμάτων"), # No specific date given
        ("5/6", "Παγκόσμια Ημέρα Περιβάλλοντος"),
        ("15/6", "Λήξη Σχολικού έτους"),
        (None, "Επίδοση τίτλων"), # No specific date given, follows 15/6
        ("έως 21/6", "Άνοιγμα νέου σχολικού έτους στο Myschool"),
        ("21/6-23/6", "Ανάρτηση παρουσιολογίων ΕΣΠΑ"),
        ("έως 25/6", "Καταχώρηση Έκθεσης Εσωτερικής Αξιολόγησης από τη/τον Διευθύντρια/ντή"),
        (None, "Δημιουργία νέου σχολικού έτους - καταχώριση"), # No specific date given
    ],
     # Ιούλιος και Αύγουστος δεν περιλαμβάνονται στην παρεχόμενη λίστα εργασιών
     "Ιούλιος": [],
     "Αύγουστος": [],
}


# 📌 Συνάρτηση για την προσθήκη προκαθορισμένων εργασιών
def add_predefined_tasks(user_name):
    # Check if any tasks exist for this user in any month
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_name = ?", (user_name,))
    count = cursor.fetchone()[0]

    # Add predefined tasks only if no tasks exist for this user at all.
    # This is a simple check to populate the database on first run per user.
    if count == 0:
        st.info("Adding predefined tasks...") # Ενημέρωση χρήστη
        for month, tasks in predefined_tasks.items():
            for date, task_desc in tasks:
                # For simplicity, using the description as title
                title = task_desc
                cursor.execute("INSERT INTO tasks (user_name, month, date, title, task, completed) VALUES (?, ?, ?, ?, ?, ?)",
                               (user_name, month, date, title, task_desc, 0))
        conn.commit()
        # st.success("Predefined tasks added!") # Επιβεβαίωση - μπορεί να γίνει ενοχλητικό σε κάθε rerun

# 📌 Ανάκτηση εργασιών από τη βάση δεδομένων
def get_tasks_from_db(user_name, month):
    # Ordering by date might put entries like "έως 10/9" and "1/9" out of strict numerical order.
    # A more complex ordering might be needed for perfect chronological sort, but this is often sufficient.
    cursor.execute("SELECT id, date, title, task, completed FROM tasks WHERE user_name = ? AND month = ? ORDER BY date",
                   (user_name, month))
    return cursor.fetchall()

# 📌 Αρχικοποίηση της εφαρμογής και session state
if "user_name" not in st.session_state:
    st.session_state.user_name = "Κώστας"  # Προσαρμόζεται δυναμικά αν θέλουμε
    # Προσθήκη προκαθορισμένων εργασιών για τον αρχικό χρήστη
    add_predefined_tasks(st.session_state.user_name)

# Initialize state for showing the new task form
if 'show_new_task_form' not in st.session_state:
    st.session_state.show_new_task_form = False

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
months = list(predefined_tasks.keys()) # Use keys from predefined tasks for order
selected_month = st.selectbox("📅 Επιλέξτε Μήνα:", months)

# 📌 Ανάκτηση εργασιών από τη βάση για τον επιλεγμένο μήνα και χρήστη
tasks = get_tasks_from_db(st.session_state.user_name, selected_month)

# 📌 Υπολογισμός προόδου για τον τρέχοντα μήνα
total_tasks = len(tasks)
completed_tasks = sum(1 for task in tasks if task[4] == 1)
progress_percentage = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0

# 📌 Εμφάνιση γραμμής προόδου
st.markdown(f"### 📊 Πρόοδος {selected_month}")
st.progress(progress_percentage / 100.0, text=f"{completed_tasks} / {total_tasks} εργασίες ολοκληρώθηκαν ({progress_percentage:.0f}%)")


# 📌 Εμφάνιση εργασιών με checkbox & περιγραφή
st.markdown(f"### 📌 Λίστα εργασιών {selected_month}")
if not tasks:
    st.info(f"Δεν υπάρχουν καταχωρημένες εργασίες για τον μήνα {selected_month}.")
else:
    for task_id, date, title, task, completed in tasks:
        task_key = f"task_{task_id}_{selected_month}" # Unique key for checkbox

        # Use columns for checkbox, task details, and delete button
        # Adjusted column widths for better layout
        col1, col2, col3 = st.columns([0.5, 6, 0.5])

        with col1:
            # The checkbox value needs to reflect the current state from the DB
            is_completed = completed == 1
            # Use on_change to trigger DB update and rerun immediately
            # The lambda function captures task_id and current_state correctly
            st.checkbox("", key=task_key, value=is_completed,
                        on_change=lambda tid=task_id, current_state=is_completed: (
                            cursor.execute("UPDATE tasks SET completed = ?", (0 if current_state else 1, tid)),
                            conn.commit(),
                            st.rerun() # Trigger rerun after update
                        )
                       )


        with col2:
            tag_color = "🟢" if completed else "🔴"
            # Display date, title, and tag
            display_date = date if date else "Χωρίς Ημ."
            # Use title for the main display line, and task for details if they differ
            display_title_line = f"**{display_date} | {title}**"
            st.markdown(f"{display_title_line} {tag_color}")
            # Display the full task description if it's significantly different from the title
            # or if the title was just a summary.
            # A simple heuristic: if task is much longer than title, show task.
            if len(task) > len(title) + 10 or title == task: # Adjust threshold as needed
                 st.write(task)


        with col3:
            # Add a delete button for each task
            if st.button("🗑️", key=f"delete_{task_key}"):
                cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                conn.commit()
                st.rerun() # Rerun to update the task list


# 📌 Κουμπί για εμφάνιση/απόκρυψη της φόρμας προσθήκης νέας εργασίας
if st.button("✨ Προσθήκη Νέας Εργασίας"):
    # Toggle the state
    st.session_state.show_new_task_form = not st.session_state.show_new_task_form
    # If showing the form, clear previous inputs
    if st.session_state.show_new_task_form:
         st.session_state.new_task_date_input = ""
         st.session_state.new_task_title_input = ""
         st.session_state.new_task_text_area = ""
    st.rerun() # Rerun to show/hide the form immediately


# 📌 Φόρμα προσθήκης νέας εργασίας (εμφανίζεται μόνο αν show_new_task_form είναι True)
if st.session_state.show_new_task_form:
    st.markdown("### 📝 Στοιχεία Νέας Εργασίας")
    # Use st.container() or just place elements directly if not using st.form for collapse
    # Since we used st.form, the collapse logic is tied to the state variable and the button click.
    with st.form("new_task_form", clear_on_submit=False): # Set clear_on_submit=False to keep values if validation fails
        # Use session state for form inputs to keep values after rerun if needed
        # Initialize them outside the form or set default values
        new_task_date = st.text_input("📅 Ημερομηνία (π.χ. 15/9, έως 20/9, 1-5/9) - Προαιρετικό:",
                                      value=st.session_state.get('new_task_date_input', ''),
                                      key='new_task_date_input_form') # Use a different key than the toggle button input
        new_task_title = st.text_input("📌 Τίτλος Εργασίας (Χρησιμοποιείται στην περίληψη της λίστας):",
                                       value=st.session_state.get('new_task_title_input', ''),
                                       key='new_task_title_input_form')
        new_task_text = st.text_area("📝 Περιγραφή Εργασίας (Πλήρες κείμενο):",
                                     value=st.session_state.get('new_task_text_area', ''),
                                     key='new_task_text_area_form')

        col_submit, col_cancel = st.columns(2)
        with col_submit:
            submitted = st.form_submit_button("✅ Αποθήκευση Εργασίας")
        with col_cancel:
            cancel_button = st.form_submit_button("❌ Ακύρωση")

        if submitted:
            if new_task_text: # Ensure task description is not empty
                # Use the task text as title if title is empty or short summary
                title_to_insert = new_task_title if new_task_title else (new_task_text[:50] + "...") if len(new_task_text) > 50 else new_task_text
                cursor.execute("INSERT INTO tasks (user_name, month, date, title, task, completed) VALUES (?, ?, ?, ?, ?, ?)",
                               (st.session_state.user_name, selected_month, new_task_date, title_to_insert, new_task_text, 0))
                conn.commit()
                st.success("Η εργασία προστέθηκε επιτυχώς!")
                # Reset form fields and hide the form
                st.session_state.show_new_task_form = False
                st.session_state.new_task_date_input_form = "" # Clear the form keys
                st.session_state.new_task_title_input_form = ""
                st.session_state.new_task_text_area_form = ""
                st.rerun() # 🔄 Ανανεώνει την εφαρμογή
            else:
                st.warning("Παρακαλώ συμπληρώστε την Περιγραφή Εργασίας.")


        if cancel_button:
             # Hide the form and clear fields without saving
            st.session_state.show_new_task_form = False
            st.session_state.new_task_date_input_form = "" # Clear the form keys
            st.session_state.new_task_title_input_form = ""
            st.session_state.new_task_text_area_form = ""
            st.rerun()


# 📌 Εκτύπωση σε PDF (Ενημερωμένη για να τραβάει όλες τις εργασίες του χρήστη)
def save_pdf(user_name):
    # Use a font that supports Greek characters (requires reportlab configuration or a custom font)
    # For simplicity, let's use a basic font that *might* support some Greek depending on the environment,
    # or require installing a specific font like FreeSans and registering it with reportlab.
    # A more robust solution for Greek requires more advanced reportlab setup or a different library.
    # Using Helvetica as a fallback, which might show squares for Greek.
    # To properly support Greek, you'd need:
    # from reportlab.pdfbase import pdfmetrics
    # from reportlab.pdfbase.ttfonts import TTFont
    # pdfmetrics.registerFont(TTFont('FreeSans', 'FreeSans.ttf')) # Need to download FreeSans.ttf or similar
    # c = canvas.Canvas(pdf_filename, fontName="FreeSans", fontSize=10)

    pdf_filename = f"{user_name}_all_tasks.pdf"
    c = canvas.Canvas(pdf_filename) # Basic canvas, might not render Greek correctly

    c.setFont("Helvetica", 12)
    c.drawString(100, 800, f"Προγραμματισμός Ενεργειών για {user_name}")
    c.setFont("Helvetica", 10)

    # Fetch tasks ordered by month and date
    cursor.execute("SELECT month, date, title, task, completed FROM tasks WHERE user_name = ? ORDER BY CASE month WHEN 'Σεπτέμβριος' THEN 1 WHEN 'Οκτώβριος' THEN 2 WHEN 'Νοέμβριος' THEN 3 WHEN 'Δεκέμβριος' THEN 4 WHEN 'Ιανουάριος' THEN 5 WHEN 'Φεβρουάριος' THEN 6 WHEN 'Μάρτιος' THEN 7 WHEN 'Απρίλιος' THEN 8 WHEN 'Μάιος' THEN 9 WHEN 'Ιούνιος' THEN 10 WHEN 'Ιούλιος' THEN 11 WHEN 'Αύγουστος' THEN 12 END, date", (user_name,))
    all_user_tasks_ordered = cursor.fetchall()

    y = 780
    current_month_pdf = None
    for month_pdf, date_pdf, title_pdf, task_pdf, completed_pdf in all_user_tasks_ordered:
        if month_pdf != current_month_pdf:
            current_month_pdf = month_pdf
            y -= 30
            if y < 50: # New page if needed
                 c.showPage()
                 y = 800
                 c.setFont("Helvetica", 10) # Reset font after page break
            c.setFont("Helvetica-Bold", 12)
            c.drawString(100, y, month_pdf)
            c.setFont("Helvetica", 10)
            y -= 15

        date_str_pdf = date_pdf if date_pdf else "Χωρίς Ημ."
        completed_status_pdf = "✓" if completed_pdf else "✗"

        # Format the task string
        # Use the title for the main line in PDF
        task_line = f"{date_str_pdf}: {title_pdf} ({completed_status_pdf})"

        # Handle text wrapping for long descriptions if needed (basic implementation)
        # This is a simplified approach and might cut words.
        max_width = 450 # Max width in points
        lines = []
        current_line = ""
        # Split by space and try to fit words
        words = task_line.split(' ')
        for word in words:
            # Check if adding the next word exceeds max_width
            if current_line and c.stringWidth(current_line + " " + word) > max_width:
                 lines.append(current_line)
                 current_line = word
            else:
                 current_line = (current_line + " " + word).strip()
        if current_line:
            lines.append(current_line)

        for line in lines:
            y -= 15
            if y < 50: # New page if needed
                 c.showPage()
                 c.setFont("Helvetica", 10) # Reset font after page break
                 y = 800
            c.drawString(110, y, line) # Indent tasks slightly


    c.save()
    return pdf_filename

if st.button("🖨️ Εκτύπωση PDF (Όλες οι εργασίες)"):
    pdf_file = save_pdf(st.session_state.user_name)
    with open(pdf_file, "rb") as f:
        st.download_button("📄 Λήψη PDF", f, pdf_file, "application/pdf")

# 📌 Εκτύπωση σε CSV (Ενημερωμένη για να τραβάει όλες τις εργασίες του χρήστη)
if st.button("📄 Εκτύπωση σε CSV (Όλες οι εργασίες)"):
    cursor.execute("SELECT month, date, title, task, completed FROM tasks WHERE user_name = ? ORDER BY CASE month WHEN 'Σεπτέμβριος' THEN 1 WHEN 'Οκτώβριος' THEN 2 WHEN 'Νοέμβριος' THEN 3 WHEN 'Δεκέμβριος' THEN 4 WHEN 'Ιανουάριος' THEN 5 WHEN 'Φεβρουάριος' THEN 6 WHEN 'Μάρτιος' THEN 7 WHEN 'Απρίλιος' THEN 8 WHEN 'Μάιος' THEN 9 WHEN 'Ιούνιος' THEN 10 WHEN 'Ιούλιος' THEN 11 WHEN 'Αύγουστος' THEN 12 END, date", (st.session_state.user_name,))
    all_user_tasks_ordered = cursor.fetchall()

    df = pd.DataFrame([
        {"Μήνας": task[0], "Ημερομηνία": task[1], "Τίτλος": task[2], "Εργασία": task[3], "Κατάσταση": "Ολοκληρώθηκε" if task[4] else "Σε εκκρεμότητα"}
        for task in all_user_tasks_ordered
    ])
    st.download_button("📄 Λήψη ως CSV", df.to_csv(index=False).encode('utf-8-sig'),
                       f"εργασίες_{st.session_state.user_name}.csv", "text/csv", key='download-all-csv')


st.markdown("---")
st.markdown("*Σύστημα Παρακολούθησης Εργασιών Διευθυντή*")

# Κλείσιμο σύνδεσης (προαιρετικό, το Streamlit το διαχειρίζεται)
# conn.close()
