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
    if len(rows)==0:
        return None
    user_id = rows[0]["id"]
    pw_hash = rows[0]["password_hash"]
    if check_password_hash(pw_hash, password):
        return user_id
    return None

# ---------------------
# Sets: Kysymyssarjat
# ---------------------
def create_set(user_id, title, description):
    sql = """INSERT INTO sets (title, description, user_id, created_at)
             VALUES (?, ?, ?, datetime('now'))"""
    return db.execute(sql, [title, description, user_id])

def get_set(set_id):
    sql = """SELECT s.id, s.title, s.description,
                    s.user_id, s.created_at,
                    u.username
             FROM sets s, users u
             WHERE s.id=? AND s.user_id=u.id
          """
    rows = db.query(sql, [set_id])
    if not rows:
        return None
    return rows[0]

def list_sets():
    sql = """SELECT s.id, s.title, s.description,
                    s.created_at, u.username
             FROM sets s, users u
             WHERE s.user_id=u.id
             ORDER BY s.id DESC
          """
    return db.query(sql)

def update_set(set_id, title, description):
    sql = """UPDATE sets
             SET title=?, description=?
             WHERE id=?"""
    db.execute(sql, [title, description, set_id])

def delete_set(set_id):
    # Poista ensin kysymykset
    sql = "DELETE FROM questions WHERE set_id=?"
    db.execute(sql, [set_id])
    # Poista sitten set
    sql = "DELETE FROM sets WHERE id=?"
    db.execute(sql, [set_id])

def search_sets(keyword):
    param = f"%{keyword}%"
    sql = """SELECT s.id, s.title, s.description,
                    s.created_at, u.username
             FROM sets s, users u
             WHERE s.user_id=u.id
               AND (s.title LIKE ? OR s.description LIKE ?)
             ORDER BY s.id DESC
          """
    return db.query(sql, [param, param])

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
             WHERE set_id=?
          """
    return db.query(sql, [set_id])

# ---------------------
# Reitit
# ---------------------

@app.route("/")
def index():
    # Listaa kaikki setit
    sets_data = list_sets()
    return render_template("index.html", sets=sets_data)

# --- Rekisteröityminen ---
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="GET":
        return render_template("register.html", filled={})
    else:
        username = request.form["username"]
        pw1 = request.form["password1"]
        pw2 = request.form["password2"]
        if pw1 != pw2:
            flash("Salasanat eivät täsmää!")
            return render_template("register.html", filled={"username":username})
        if not create_user(username, pw1):
            flash("Tunnus on jo varattu.")
            return render_template("register.html", filled={"username":username})
        flash("Tunnus luotu! Voit kirjautua.")
        return redirect("/login")

# --- Kirjautuminen ---
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="GET":
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

# --- Uusi set ---
@app.route("/new_set", methods=["GET","POST"])
def new_set():
    require_login()
    if request.method=="GET":
        return render_template("new_set.html")
    else:
        check_csrf(request.form["csrf_token"])
        title = request.form["title"]
        desc = request.form["description"]
        if not title or not desc:
            flash("Otsikko ja kuvaus ovat pakollisia!")
            return redirect("/new_set")
        set_id = create_set(session["user_id"], title, desc)
        flash("Uusi setti luotu. Voit lisätä kysymyksiä.")
        return redirect(f"/edit_set/{set_id}")

# --- Näytä set ---
@app.route("/set/<int:set_id>")
def show_set(set_id):
    s = get_set(set_id)
    if not s:
        abort(404)
    questions = get_questions(set_id)
    return render_template("show_set.html", s=s, questions=questions)

# --- Muokkaa set ---
@app.route("/edit_set/<int:set_id>", methods=["GET","POST"])
def edit_set(set_id):
    require_login()
    s = get_set(set_id)
    if not s:
        abort(404)
    if s["user_id"] != session["user_id"]:
        abort(403)

    if request.method=="GET":
        return render_template("edit_set.html", s=s)
    else:
        check_csrf(request.form["csrf_token"])
        title = request.form["title"]
        desc = request.form["description"]
        update_set(set_id, title, desc)

        # Lisätään uusi kysymys jos annettu
        qtext = request.form["question_text"].strip()
        if qtext:
            answer1 = request.form["answer1"]
            answer2 = request.form["answer2"]
            answer3 = request.form["answer3"]
            correct_str = request.form["correct"]
            try:
                correct_int = int(correct_str)
                if correct_int<1 or correct_int>3:
                    flash("Virhe: oikea vastaus on 1–3.")
                else:
                    add_question(set_id, qtext, answer1, answer2, answer3, correct_int)
                    flash("Kysymys lisätty.")
            except ValueError:
                flash("Virheellinen arvo kentässä 'Oikea vastaus'.")

        flash("Setti päivitetty.")
        return redirect(f"/edit_set/{set_id}")

# --- Poista set ---
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

# --- Haku ---
@app.route("/search")
def search():
    query = request.args.get("query","")
    results = []
    if query:
        results = search_sets(query)
    return render_template("search.html", query=query, results=results)

# --- Pelaa setti (/attempt_set) ---
@app.route("/attempt_set/<int:set_id>", methods=["GET","POST"])
def attempt_set(set_id):
    """Sivu, jossa käyttäjä valitsee vastaukset (1–3).
       Lähetettäessä näytetään punavihreä palaute."""
    s = get_set(set_id)
    if not s:
        abort(404)
    questions = get_questions(set_id)

    if request.method=="GET":
        # Näytetään lomake + linkit ankkureihin
        return render_template("attempt_set.html", s=s, questions=questions)
    else:
        # Käyttäjä on vastannut
        results = []
        for q in questions:
            qid = q["id"]
            correct = q["correct_answer"]
            user_ans_str = request.form.get(f"question_{qid}","")
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

# Käynnistys
if __name__=="__main__":
    app.run(debug=True)
