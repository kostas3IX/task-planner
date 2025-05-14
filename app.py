import streamlit as st
from reportlab.pdfgen import canvas
from io import BytesIO
from task_parser import parse_tasks
from utils import initialize_session_state, get_month_number, get_month_name_greek, save_current_state
from weather_utils import get_weather_icon
from storage_utils import save_task_note, get_task_note, save_custom_task, get_custom_tasks
import pandas as pd

# Set page config
st.set_page_config(
    page_title="Προγραμματισμός Ενεργειών",
    page_icon="📋",
    layout="wide"
)

# Initialize session state
initialize_session_state()

@st.cache_data
def load_tasks():
    with open('attached_assets/Pasted--1-9-1-5-9--1741196315693.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    return parse_tasks(content)

def generate_pdf(tasks, selected_month):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)

    pdf.setFont("Helvetica", 14)
    pdf.drawString(200, 800, f"Εργασίες για τον μήνα {get_month_name_greek(selected_month)}")
    
    y_position = 780
    pdf.setFont("Helvetica", 12)
    for idx, (date, task) in enumerate(tasks):
        status = "✓" if f"{selected_month}_{idx}" in st.session_state.completed_tasks else "✗"
        note = get_task_note(f"{selected_month}_{idx}")
        task_text = f"{date} {task} - Κατάσταση: {status}"
        pdf.drawString(50, y_position, task_text)
        
        if note:
            pdf.drawString(70, y_position - 20, f"Σημείωση: {note}")

        y_position -= 40

    pdf.save()
    buffer.seek(0)
    return buffer

def main():
    if st.session_state.user_name is None:
        with st.form("user_name_form"):
            user_name = st.text_input("Παρακαλώ εισάγετε το όνομά σας:")
            submitted = st.form_submit_button("Υποβολή")
            if submitted and user_name:
                st.session_state.user_name = user_name
                save_current_state()
                st.rerun()

    if st.session_state.user_name:
        col1, col2 = st.columns([3, 1])
        with col1:
            vocative_name = st.session_state.user_name[:-2] + 'ε' if st.session_state.user_name.endswith('ος') else st.session_state.user_name
            st.markdown(f"### Γεια σου, {vocative_name}! {get_weather_icon()}")

    st.title("📋 Προγραμματισμός ενεργειών διευθυντή")
    st.subheader("Παρακολούθηση Μηνιαίων Εργασιών")

    tasks_by_month = load_tasks()

    months = list(tasks_by_month.keys())
    months.sort(key=get_month_number)
    selected_month = st.selectbox(
        "Επιλέξτε Μήνα:",
        months,
        format_func=get_month_name_greek
    )

    if selected_month:
        month_tasks = tasks_by_month[selected_month]

        custom_tasks = get_custom_tasks(selected_month)
        for task in custom_tasks:
            month_tasks.append((task.get('date', ''), task.get('text', '')))

        total_tasks = len(month_tasks)
        completed_tasks = sum(1 for i in range(total_tasks) if f"{selected_month}_{i}" in st.session_state.completed_tasks)
        monthly_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        st.progress(monthly_progress / 100)
        st.write(f"📅 Συνολική πρόοδος {get_month_name_greek(selected_month)}: {monthly_progress:.1f}%")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader(f"Εργασίες {get_month_name_greek(selected_month)}")

            for idx, (date, task) in enumerate(month_tasks):
                task_key = f"{selected_month}_{idx}"

                task_col, note_col = st.columns([8, 2])

                with task_col:
                    if st.checkbox(
                        f"**{date}** {task}" if date else task,
                        key=task_key,
                        value=task_key in st.session_state.completed_tasks
                    ):
                        st.session_state.completed_tasks[task_key] = True
                    else:
                        if task_key in st.session_state.completed_tasks:
                            st.session_state.completed_tasks.pop(task_key, None)

                    save_current_state()

                with note_col:
                    has_note = bool(get_task_note(task_key))
                    note_label = "📝 ✅" if has_note else "📝"
                    if st.button(note_label, key=f"note_{task_key}"):
                        st.session_state.editing_note = task_key

                if getattr(st.session_state, 'editing_note', None) == task_key:
                    with st.expander("Σημειώσεις", expanded=True):
                        note = st.text_area(
                            "Προσθέστε σημείωση:",
                            value=get_task_note(task_key),
                            key=f"note_text_{task_key}"
                        )
                        if st.button("Αποθήκευση", key=f"save_note_{task_key}"):
                            save_task_note(task_key, note)
                            st.session_state.editing_note = None
                            st.rerun()

            if st.button("➕ Προσθήκη Εργασίας"):
                st.session_state.adding_task = True

            if getattr(st.session_state, 'adding_task', False):
                with st.form("new_task_form"):
                    new_task_date = st.text_input("Ημερομηνία (προαιρετικό):")
                    new_task_text = st.text_area("Περιγραφή εργασίας:")
                    submitted = st.form_submit_button("Προσθήκη")
                    if submitted and new_task_text:
                        if "custom_tasks" not in st.session_state:
                            st.session_state["custom_tasks"] = {}

                        if selected_month not in st.session_state["custom_tasks"]:
                            st.session_state["custom_tasks"][selected_month] = []

                        st.session_state["custom_tasks"][selected_month].append({
                            "date": new_task_date,
                            "text": new_task_text
                        })
                        save_current_state()

                        # Κλείσιμο της φόρμας μετά την προσθήκη της εργασίας
                        st.session_state.adding_task = False
                        st.rerun()

        with col2:
            st.subheader("Σύνοψη")
            st.metric("Συνολικές Εργασίες", total_tasks)
            st.metric("Ολοκληρωμένες Εργασίες", completed_tasks)
            st.metric("Εκκρεμείς Εργασίες", total_tasks - completed_tasks)

            pdf_buffer = generate_pdf(month_tasks, selected_month)
            st.download_button(
                "📄 Λήψη ως PDF",
                pdf_buffer,
                f"εργασίες_{selected_month}.pdf",
                "application/pdf",
                key='download-pdf'
            )

    st.markdown("---")
    st.markdown("*Σύστημα Παρακολούθησης Εργασιών Διευθυντή*")

if __name__ == "__main__":
    main()
