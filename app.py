import secrets
import math
from flask import Flask, render_template, request, redirect, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
import db
import config

app = Flask(__name__)
app.secret_key = config.secret_key

# ---------------------
# Apufunktiot
# ---------------------
def require_login():
    if "user_id" not in session:
        abort(403)

def check_csrf(form_token):
    if form_token != session.get("csrf_token"):
        abort(403)

# ---------------------
# Käyttäjien käsittely
# ---------------------
def create_user(username, password):
    pw_hash = generate_password_hash(password)
    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, pw_hash])
        return True
    except:
        return False

def check_login(username, password):
    sql = "SELECT id, password_hash FROM users WHERE username=?"
    rows = db.query(sql, [username])
    if len(rows) == 0:
        return None
    user_id = rows[0]["id"]
    pw_hash = rows[0]["password_hash"]
    if check_password_hash(pw_hash, password):
        return user_id
    return None

# ---------------------
# Luokat (Categories)
# ---------------------
def get_categories():
    sql = "SELECT id, name FROM categories ORDER BY name"
    return db.query(sql)

# ---------------------
# Sets: Kysymyssarjat
# ---------------------
def create_set(user_id, title, description, category_id):
    sql = """INSERT INTO sets (title, description, user_id, category_id, created_at)
             VALUES (?, ?, ?, ?, datetime('now'))"""
    return db.execute(sql, [title, description, user_id, category_id])

def get_set(set_id):
    sql = """SELECT s.id, s.title, s.description, s.user_id, s.category_id, s.created_at,
                    c.name as category_name, u.username
             FROM sets s
             LEFT JOIN categories c ON s.category_id = c.id
             JOIN users u ON s.user_id = u.id
             WHERE s.id=?"""
    rows = db.query(sql, [set_id])
    if not rows:
        return None
    return rows[0]

def list_sets():
    sql = """SELECT s.id, s.title, s.description, s.created_at, s.category_id,
                    c.name as category_name, u.username
             FROM sets s
             JOIN users u ON s.user_id = u.id
             LEFT JOIN categories c ON s.category_id = c.id
             ORDER BY s.id DESC
          """
    return db.query(sql)

def update_set(set_id, title, description, category_id):
    sql = """UPDATE sets
             SET title=?, description=?, category_id=?
             WHERE id=?"""
    db.execute(sql, [title, description, category_id, set_id])

def delete_set(set_id):
    # Poista ensin kysymykset
    sql = "DELETE FROM questions WHERE set_id=?"
    db.execute(sql, [set_id])
    # Poista kommentit
    sql = "DELETE FROM comments WHERE set_id=?"
    db.execute(sql, [set_id])
    # Poista sitten set
    sql = "DELETE FROM sets WHERE id=?"
    db.execute(sql, [set_id])

def search_sets(keyword, category):
    param = f"%{keyword}%"
    sql = """SELECT s.id, s.title, s.description, s.created_at, s.category_id,
                    c.name as category_name, u.username
             FROM sets s
             JOIN users u ON s.user_id = u.id
             LEFT JOIN categories c ON s.category_id = c.id
             WHERE (s.title LIKE ? OR s.description LIKE ?)
          """
    params = [param, param]
    if category:
        sql += " AND s.category_id = ?"
        params.append(category)
    sql += " ORDER BY s.id DESC"
    return db.query(sql, params)

# ---------------------
# Kysymykset (3 vastausvaihtoehtoa)
# ---------------------
def add_question(set_id, question_text, answer1, answer2, answer3, correct):
    sql = """INSERT INTO questions (set_id, question_text,
                                    answer1, answer2, answer3,
                                    correct_answer)
             VALUES (?, ?, ?, ?, ?, ?)"""
    db.execute(sql, [set_id, question_text, answer1, answer2, answer3, correct])

def get_questions(set_id):
    sql = """SELECT id, question_text,
                    answer1, answer2, answer3,
                    correct_answer
             FROM questions
             WHERE set_id=?"""
    return db.query(sql, [set_id])

# ---------------------
# Kommentit
# ---------------------
def get_comments_for_set(set_id):
    sql = """SELECT cm.id, cm.comment_text, cm.created_at, u.username
             FROM comments cm
             JOIN users u ON cm.user_id = u.id
             WHERE cm.set_id = ?
             ORDER BY cm.created_at DESC"""
    return db.query(sql, [set_id])

# ---------------------
# Käyttäjän setit (profiili)
# ---------------------
def get_user_sets(user_id):
    sql = """SELECT s.id, s.title, s.description, s.created_at, s.category_id, c.name as category_name
             FROM sets s
             LEFT JOIN categories c ON s.category_id = c.id
             WHERE s.user_id = ?
             ORDER BY s.created_at DESC"""
    return db.query(sql, [user_id])

# ---------------------
# Reitit
# ---------------------
@app.route("/")
def index():
    sets_data = list_sets()
    return render_template("index.html", sets=sets_data)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", filled={})
    else:
        username = request.form["username"]
        pw1 = request.form["password1"]
        pw2 = request.form["password2"]
        if pw1 != pw2:
            flash("Salasanat eivät täsmää!")
            return render_template("register.html", filled={"username": username})
        if not create_user(username, pw1):
            flash("Tunnus on jo varattu.")
            return render_template("register.html", filled={"username": username})
        flash("Tunnus luotu! Voit kirjautua.")
        return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", next_page=request.referrer)
    else:
        username = request.form["username"]
        password = request.form["password"]
        next_page = request.form.get("next_page") or "/"
        user_id = check_login(username, password)
        if user_id:
            session["user_id"] = user_id
            session["csrf_token"] = secrets.token_hex(16)
            flash("Kirjautuminen onnistui!")
            return redirect(next_page)
        else:
            flash("Väärä tunnus tai salasana.")
            return render_template("login.html", next_page=next_page)

@app.route("/logout")
def logout():
    del session["user_id"]
    del session["csrf_token"]
    flash("Olet kirjautunut ulos.")
    return redirect("/")

@app.route("/new_set", methods=["GET", "POST"])
def new_set():
    require_login()
    if request.method == "GET":
        cats = get_categories()
        return render_template("new_set.html", categories=cats)
    else:
        check_csrf(request.form["csrf_token"])
        title = request.form["title"]
        desc = request.form["description"]
        category_id = request.form.get("category_id")
        if not title or not desc or not category_id:
            flash("Otsikko, kuvaus ja kategoria ovat pakollisia!")
            return redirect("/new_set")
        set_id = create_set(session["user_id"], title, desc, category_id)
        flash("Uusi setti luotu. Voit lisätä kysymyksiä.")
        return redirect(f"/edit_set/{set_id}")

@app.route("/set/<int:set_id>")
def show_set(set_id):
    s = get_set(set_id)
    if not s:
        abort(404)
    questions = get_questions(set_id)
    comments = get_comments_for_set(set_id)
    return render_template("show_set.html", s=s, questions=questions, comments=comments)

@app.route("/edit_set/<int:set_id>", methods=["GET", "POST"])
def edit_set(set_id):
    require_login()
    s = get_set(set_id)
    if not s:
        abort(404)
    if s["user_id"] != session["user_id"]:
        abort(403)

    if request.method == "GET":
        cats = get_categories()
        return render_template("edit_set.html", s=s, categories=cats)
    else:
        check_csrf(request.form["csrf_token"])
        title = request.form["title"]
        desc = request.form["description"]
        category_id = request.form.get("category_id")
        update_set(set_id, title, desc, category_id)

        # Lisätään uusi kysymys, jos annettu
        qtext = request.form["question_text"].strip()
        if qtext:
            answer1 = request.form["answer1"]
            answer2 = request.form["answer2"]
            answer3 = request.form["answer3"]
            correct_str = request.form["correct"]
            try:
                correct_int = int(correct_str)
                if correct_int < 1 or correct_int > 3:
                    flash("Virhe: oikea vastaus on 1–3.")
                else:
                    add_question(set_id, qtext, answer1, answer2, answer3, correct_int)
                    flash("Kysymys lisätty.")
            except ValueError:
                flash("Virheellinen arvo kentässä 'Oikea vastaus'.")

        flash("Setti päivitetty.")
        return redirect(f"/edit_set/{set_id}")

@app.route("/remove_set/<int:set_id>", methods=["POST"])
def remove_set(set_id):
    require_login()
    check_csrf(request.form["csrf_token"])
    s = get_set(set_id)
    if not s:
        abort(404)
    if s["user_id"] != session["user_id"]:
        abort(403)
    delete_set(set_id)
    flash("Setti poistettu.")
    return redirect("/")

@app.route("/search")
def search():
    query = request.args.get("query", "")
    category = request.args.get("category")
    cats = get_categories()
    results = []
    if query or category:
        results = search_sets(query, category)
    return render_template("search.html", query=query, category=category, results=results, categories=cats)

@app.route("/attempt_set/<int:set_id>", methods=["GET", "POST"])
def attempt_set(set_id):
    s = get_set(set_id)
    if not s:
        abort(404)
    questions = get_questions(set_id)

    if request.method == "GET":
        return render_template("attempt_set.html", s=s, questions=questions)
    else:
        results = []
        for q in questions:
            qid = q["id"]
            correct = q["correct_answer"]
            user_ans_str = request.form.get(f"question_{qid}", "")
            try:
                user_ans = int(user_ans_str)
            except:
                user_ans = -1

            is_correct = (user_ans == correct)
            item = {
                "question_text": q["question_text"],
                "answer1": q["answer1"],
                "answer2": q["answer2"],
                "answer3": q["answer3"],
                "correct": correct,
                "user_answer": user_ans,
                "is_correct": is_correct
            }
            results.append(item)

        return render_template("attempt_results.html", s=s, results=results)

@app.route("/add_comment/<int:set_id>", methods=["POST"])
def add_comment(set_id):
    require_login()
    check_csrf(request.form["csrf_token"])
    comment_text = request.form.get("comment_text", "").strip()
    if not comment_text:
        flash("Kommentti ei voi olla tyhjä.")
        return redirect(f"/set/{set_id}")
    sql = """INSERT INTO comments (set_id, user_id, comment_text, created_at)
             VALUES (?, ?, ?, datetime('now'))"""
    db.execute(sql, [set_id, session["user_id"], comment_text])
    flash("Kommentti lisätty.")
    return redirect(f"/set/{set_id}")

@app.route("/profile")
def profile():
    require_login()
    user_id = session["user_id"]
    user_sets = get_user_sets(user_id)
    # Muunnetaan jokainen rivi sanakirjaksi ja lisätään kommentit
    user_sets_with_comments = []
    for s in user_sets:
        s_dict = dict(s)
        s_dict["comments"] = get_comments_for_set(s["id"])
        user_sets_with_comments.append(s_dict)
    return render_template("profile.html", sets=user_sets_with_comments)

if __name__ == "__main__":
    app.run(debug=True)
