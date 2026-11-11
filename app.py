
from flask import Flask, render_template, request, redirect, url_for

from datetime import date, datetime, timedelta

from storage import load_data, save_data
from models.task import Task
from models.subject import Subject

app = Flask(__name__)

timer_state = {
    "status": "idle",
    "end_time": None,
    "remaining": 1500,
    "subject": "",
    "duration": 25
}


@app.route("/")
def home():

    all_tasks = load_data("tasks.json")

    # Count all tasks
    total_tasks = len(all_tasks)

    # Count completed tasks
    completed_tasks = sum(
        1 for task in all_tasks
        if task.get("completion_status", False)
    )

    # Calculate pending tasks
    pending_tasks = total_tasks - completed_tasks

    # Calculate completion percentage
    if total_tasks > 0:
        progress = round((completed_tasks / total_tasks) * 100)
    else:
        progress = 0

    # Find the two closest upcoming deadlines
    today = date.today().isoformat()

    upcoming_tasks = [
        task for task in all_tasks
        if task.get("deadline")
        and task["deadline"] >= today
        and not task.get("completion_status", False)
    ]

    upcoming_tasks.sort(key=lambda task: task["deadline"])

    closest_tasks = upcoming_tasks[:2]

    return render_template(
        "index.html",
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        progress=progress,
        closest_tasks=closest_tasks
    )



# Display tasks and add new tasks
@app.route("/tasks", methods=["GET", "POST"])
def tasks():

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        subject = request.form.get("subject", "").strip()
        description = request.form.get("description", "").strip()
        deadline = request.form.get("deadline", "")

        all_subjects = load_data("subjects.json")

        # Check whether the user selected Other
        if subject == "Other":

            new_subject_name = request.form.get(
                "new_subject", ""
            ).strip()

            if new_subject_name:

                # Check whether this subject already exists
                existing_subject = next(
                    (
                        s for s in all_subjects
                        if s["name"].lower() == new_subject_name.lower()
                    ),
                    None
                )

                if existing_subject:
                    subject = existing_subject["name"]

                else:
                    new_subject = Subject(new_subject_name)

                    subject_data = {
                        "name": new_subject.name,
                        "description": new_subject.description
                    }

                    all_subjects.append(subject_data)
                    save_data("subjects.json", all_subjects)

                    subject = new_subject_name

            else:
                return redirect(url_for("tasks"))

        else:
            valid_subjects = [
                s["name"] for s in all_subjects
            ]

            if subject not in valid_subjects:
                return redirect(url_for("tasks"))

        # Save the task
        if title and subject:

            new_task = Task(
                title,
                subject,
                description,
                deadline
            )

            task_data = {
                "title": new_task.title,
                "subject": new_task.subject,
                "description": new_task.description,
                "deadline": new_task.deadline,
                "completion_status": new_task.completion_status
            }

            all_tasks = load_data("tasks.json")
            all_tasks.append(task_data)

            save_data("tasks.json", all_tasks)

        return redirect(url_for("tasks"))

    # Load tasks and subjects for the page
    all_tasks = load_data("tasks.json")
    all_subjects = load_data("subjects.json")

    return render_template(
        "tasks.html",
        tasks=all_tasks,
        subjects=all_subjects
    )


# Mark a task as complete
@app.route("/tasks/complete/<int:task_index>", methods=["POST"])
def complete_task(task_index):

    all_tasks = load_data("tasks.json")

    if 0 <= task_index < len(all_tasks):
        all_tasks[task_index]["completion_status"] = True
        save_data("tasks.json", all_tasks)

    return redirect(url_for("tasks"))


# Delete a task
@app.route("/tasks/delete/<int:task_index>", methods=["POST"])
def delete_task(task_index):

    all_tasks = load_data("tasks.json")

    if 0 <= task_index < len(all_tasks):
        all_tasks.pop(task_index)
        save_data("tasks.json", all_tasks)

    return redirect(url_for("tasks"))

# Display subjects and add new subjects
@app.route("/subjects", methods=["GET", "POST"])
def subjects():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if name:

            all_subjects = load_data("subjects.json")

            # Avoid duplicate subject names
            already_exists = any(
                subject["name"].lower() == name.lower()
                for subject in all_subjects
            )

            if not already_exists:

                new_subject = Subject(name, description)

                subject_data = {
                    "name": new_subject.name,
                    "description": new_subject.description
                }

                all_subjects.append(subject_data)
                save_data("subjects.json", all_subjects)

        return redirect(url_for("subjects"))

    all_subjects = load_data("subjects.json")

    return render_template("subjects.html", subjects=all_subjects)


# Delete a subject
@app.route("/subjects/delete/<int:subject_index>", methods=["POST"])
def delete_subject(subject_index):

    all_subjects = load_data("subjects.json")

    if 0 <= subject_index < len(all_subjects):
        all_subjects.pop(subject_index)
        save_data("subjects.json", all_subjects)

    return redirect(url_for("subjects"))


@app.route("/subjects/edit/<int:subject_index>", methods=["GET", "POST"])
def edit_subject(subject_index):

    all_subjects = load_data("subjects.json")

    if not (0 <= subject_index < len(all_subjects)):
        return redirect(url_for("subjects"))

    subject = all_subjects[subject_index]

    if request.method == "POST":

        new_name = request.form.get("name", "").strip()
        new_description = request.form.get("description", "").strip()

        if new_name:

            # Check whether another subject already has this name
            duplicate = any(
                s["name"].lower() == new_name.lower()
                for i, s in enumerate(all_subjects)
                if i != subject_index
            )

            if not duplicate:

                old_name = subject["name"]

                # Update the subject
                subject["name"] = new_name
                subject["description"] = new_description

                save_data("subjects.json", all_subjects)

                # Update tasks linked to the old subject name
                all_tasks = load_data("tasks.json")

                for task in all_tasks:
                    if task["subject"] == old_name:
                        task["subject"] = new_name

                save_data("tasks.json", all_tasks)

                return redirect(url_for("subjects"))

    return render_template(
        "edit_subject.html",
        subject=subject,
        subject_index=subject_index
    )


# Deadline Tracker
@app.route("/deadlines")
def deadlines():

    all_tasks = load_data("tasks.json")

    today = date.today().isoformat()

    overdue_tasks = []
    upcoming_deadlines = []
    completed_deadlines = []

    for task in all_tasks:

        deadline = task.get("deadline", "")
        is_completed = task.get("completion_status", False)

        if is_completed:
            completed_deadlines.append(task)

        elif deadline and deadline < today:
            overdue_tasks.append(task)

        elif deadline and deadline >= today:
            upcoming_deadlines.append(task)

    # Arrange deadlines from earliest to latest
    overdue_tasks.sort(key=lambda task: task["deadline"])
    upcoming_deadlines.sort(key=lambda task: task["deadline"])

    return render_template(
        "deadlines.html",
        overdue_tasks=overdue_tasks,
        upcoming_deadlines=upcoming_deadlines,
        completed_deadlines=completed_deadlines
    )




# Study Timer
@app.route("/timer", methods=["GET", "POST"])
def timer():

    global timer_state

    if request.method == "POST":

        action = request.form.get("action")

        # Start a new timer
        if action == "start":

            try:
                minutes = int(request.form.get("minutes", 25))
            except ValueError:
                minutes = 25

            # Keep duration within a reasonable range
            minutes = max(1, min(minutes, 180))

            subject = request.form.get("subject", "")

            timer_state["status"] = "running"
            timer_state["duration"] = minutes
            timer_state["remaining"] = minutes * 60
            timer_state["subject"] = subject

            timer_state["end_time"] = (
                datetime.now() + timedelta(minutes=minutes)
            )

        # Pause the timer
        elif action == "pause":

            if timer_state["status"] == "running":

                remaining = (
                    timer_state["end_time"] - datetime.now()
                ).total_seconds()

                timer_state["remaining"] = max(0, int(remaining))
                timer_state["status"] = "paused"
                timer_state["end_time"] = None

        # Resume the timer
        elif action == "resume":

            if timer_state["status"] == "paused":

                timer_state["end_time"] = (
                    datetime.now()
                    + timedelta(seconds=timer_state["remaining"])
                )

                timer_state["status"] = "running"

        # Reset the timer
        elif action == "reset":

            timer_state["status"] = "idle"
            timer_state["end_time"] = None
            timer_state["remaining"] = (
                timer_state["duration"] * 60
            )

        return redirect(url_for("timer"))

    # Get subjects for the dropdown
    all_subjects = load_data("subjects.json")

    # Calculate remaining time
    if timer_state["status"] == "running":

        remaining = (
            timer_state["end_time"] - datetime.now()
        ).total_seconds()

        timer_state["remaining"] = max(0, int(remaining))

        if remaining <= 0:
            timer_state["status"] = "finished"
            timer_state["remaining"] = 0
            timer_state["end_time"] = None

    # Convert seconds into MM:SS
    minutes = timer_state["remaining"] // 60
    seconds = timer_state["remaining"] % 60

    time_display = f"{minutes:02d}:{seconds:02d}"

    return render_template(
        "timer.html",
        subjects=all_subjects,
        timer_state=timer_state,
        time_display=time_display
    )


if __name__ == "__main__":
    app.run(debug=True)
