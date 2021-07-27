from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from .models import Note
from . import db
import json

views = Blueprint('views', __name__)

@views.route('/', methods = ['GET', 'POST'])
@login_required
def home():
    if not current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.form:
        if "logout" in request.form:
            return redirect(url_for("logout"))
        elif "delete_task" in list(request.form.keys())[0]:
            task = ToDo.query.filter(ToDo.id == int(request.form[list(request.form.keys())[0]])).first()
            db.session.delete(task)
            db.session.commit()
            return redirect(url_for("todo"))
        elif "completed_task" in list(request.form.keys())[0]:
            task = ToDo.query.filter(ToDo.id == int(request.form[list(request.form.keys())[0]])).first()
            task.completed = not task.completed
            db.session.commit()
            return redirect(url_for("todo"))
        elif "delete_tag" in request.form:
            tag = request.form["delete_tag"]

            db_tags = Tags.query.filter(Tags.user_id == current_user.id).all()
            for db_tag in db_tags:
                if tag == db_tag.tag:
                    db.session.delete(db_tag)
                    db.session.commit()
                    return redirect(url_for("todo"))
            return redirect(url_for("todo"))
        elif "create_todo" in request.form:
            # DD/MM/YYYY
            start_date = None
            due_date = None
            if request.form["todo_start_date"]:
                start_date = request.form["todo_start_date"].split("-")
                start_date = [int(d) for d in start_date]
                start_date = datetime(start_date[0], start_date[1], start_date[2])

            if request.form["todo_due_date"]:
                due_date = request.form["todo_due_date"].split("-")
                due_date = [int(d) for d in due_date]
                due_date = datetime(due_date[0], due_date[1], due_date[2])

            todo_item = ToDo(title=request.form["todo_title"],
                             tag=request.form["todo_tag"],
                             body=request.form["todo_body"],
                             start_date=start_date,
                             due_date=due_date,
                             author=current_user)

            db.session.add(todo_item)
            db.session.commit()
            if len(request.form["todo_tag"]) > 0:
                todo_tag = request.form["todo_tag"].split(",")
                count = todo_tag.count("")
                for x in range (count):
                    todo_tag.remove("")

                db_tags = Tags.query.filter(Tags.user_id == current_user.id).all()
                db_tags = [x.tag for x in db_tags]
                all_tags = []
                for tag in todo_tag:
                    add_this_tag = True
                    for db_tag in db_tags:
                        if db_tag == tag:
                            add_this_tag = False
                            break
                    if add_this_tag:
                        all_tags.append(tag)

                for tag in all_tags:
                    db.session.add(Tags(tag=tag, author=current_user))
                    db.session.commit()
            return redirect(url_for("todo"))
        elif "filter_views" in request.form:
            session["filter_views"] = request.form["filter_views"]
            return redirect(url_for("todo"))
        elif "edit_task_form" in list(request.form.keys()):
            keys = list(request.form.keys())
            keys.remove("edit_task_form")
            char = keys[0].split("_")
            id = int(char[len(char)-1])
            task = ToDo.query.filter(ToDo.id == id).first()
            # title, body, start_date, due_date
            for key in keys:
                if "title" in key:
                    task.title = request.form[key]
                elif "body" in key:
                    task.body = request.form[key]
                elif "start_date" in key and len(request.form[key]) > 0:
                    start_date = request.form[key].split("-")
                    start_date = [int(d) for d in start_date]
                    start_date = datetime(start_date[0], start_date[1], start_date[2])
                    task.start_date = start_date
                elif "due_date" in key and len(request.form[key]) > 0:
                    due_date = request.form[key].split("-")
                    due_date = [int(d) for d in due_date]
                    due_date = datetime(due_date[0], due_date[1], due_date[2])
                    task.due_date = due_date
            db.session.commit()
            return redirect(url_for("todo"))

    user_todos = []
    if (session and "filter_views" in session and
        session["filter_views"] != "filter_date_added"):
        filter_view = session["filter_views"]
        user_todos = current_user.todo_items.all()
        # id, title, tag, body, start_date, due_date, completed, user_id
        if filter_view == "filter_due_date":
            todos_dated = []
            todos_dated_dict = {}
            todos_dated_counter = 0
            todos_undated = []
            for todo in user_todos:
                if todo.due_date:
                    todos_dated.append((todo.due_date, todos_dated_counter))
                    todos_dated_dict[todos_dated_counter] = todo
                    todos_dated_counter += 1
                else:
                    todos_undated.append(todo)
            # Sort by date
            todos_dated.sort()

            user_todos = []
            for todo in todos_dated:
                user_todos.append(todos_dated_dict[todo[1]])
            for todo in todos_undated:
                user_todos.append(todo)
        else:
            # filter_tags_number
            todos_tag = []
            todos_tag_counter = 0
            todos_tag_dict = {}
            for todo in user_todos:
                todos_tag.append((todo.tag.count(","), todos_tag_counter))
                todos_tag_dict[todos_tag_counter] = todo
                todos_tag_counter += 1
            todos_tag.sort()
            user_todos = []
            for todo in todos_tag:
                user_todos.append(todos_tag_dict[todo[1]])

    else:
        user_todos = current_user.todo_items.all()

    todos = []
    for user_todo in user_todos:
        start_date = user_todo.start_date
        due_date = user_todo.due_date
        days_left = ""
        if start_date and due_date:
            today_date = datetime.now()
            if start_date <= today_date <= due_date:
                days_left = due_date-today_date
                if "days" in str(days_left) or "day" in str(days_left):
                    days_left = str(days_left)
                    days_left = days_left[:days_left.find(",")] + " left"
                else:
                    days_left = str(days_left)
                    days_left = days_left.split(":")
                    days_left = [float(x) for x in days_left]

                    hours = days_left[0]
                    minutes = days_left[1]
                    seconds = days_left[2]

                    if hours != 0.0:
                        days_left = str(hours) + " hour" + (hours != 1.0)*"s" + " left"
                    elif minutes != 0.0:
                        days_left = str(minutes) + " minutes" + (minutes !=1.0)*"s" + " left"
                    elif seconds != 0.0:
                        days_left = str(seconds) + " seconds" + (seconds !=1.0)*"s" + " left"
                    else:
                        days_left = ""
        if start_date:
            start_date = start_date.strftime("%d/%m/%Y")
        if due_date:
            due_date = due_date.strftime("%d/%m/%Y")
        todo_tag = []
        if len(user_todo.tag) > 0:
            todo_tag = user_todo.tag.split(",")
            count = todo_tag.count("")
            for x in range(count):
                todo_tag.remove("")
        todos.append({"Title": user_todo.title, "Body": user_todo.body,
                      "Tag": todo_tag, "Start date": start_date,
                      "Due date": due_date, "Days left": days_left,
                      "id": user_todo.id, "completed": user_todo.completed})

    user_tags = current_user.tag_items.all()
    tags = []
    for user_tag in user_tags:
        tags.append(user_tag.tag)

    if session and "filter_views" in session:
        filter_view = session["filter_views"]
        session.pop("filter_views")
        if filter_view == "filter_date_added":
            filter_view = "Sort by date added"
        elif filter_view == "filter_due_date":
            filter_view = "Sort by due date"
        else:
            # filter_tags_number
            filter_view = "Sort by number of tags"
    if request.method == 'POST':
        note = request.form.get('note')
        if len(note)<1:
            flash('Note is too short', category='error')
        else:
            new_note = Note(data = note, user_id = current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note Added!', category = 'success')
    return render_template("home.html", user=current_user)

@views.route('/delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
    return jsonify({})


@views.route('/update-note', methods=['POST'])
def update_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    delete_note()
    return render_template('update.html')

