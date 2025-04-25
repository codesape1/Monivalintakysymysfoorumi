import secrets
import sqlite3
from flask import Flask, render_template, request, redirect, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
import db
import config

app = Flask(__name__)
app.secret_key = config.secret_key


# ──────────────────────────────────────────────────────────────
# Apufunktiot
# ──────────────────────────────────────────────────────────────
def require_login():
    if "user_id" not in session:
        abort(403)


def check_csrf(form_token):
    if form_token != session.get("csrf_token"):
        abort(403)


# ──────────────────────────────────────────────────────────────
# Käyttäjät
# ──────────────────────────────────────────────────────────────
def create_user(username, password):
    pw_hash = generate_password_hash(password)
    try:
        db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                   [username, pw_hash])
        return True
    except Exception:
        return False


def check_login(username, password):
    rows = db.query("SELECT id, password_hash FROM users WHERE username=?", [username])
    if not rows:
        return None
    if check_password_hash(rows[0]["password_hash"], password):
        return rows[0]["id"]
    return None


# ──────────────────────────────────────────────────────────────
# Luokat
# ──────────────────────────────────────────────────────────────
def get_categories():
    return db.query("SELECT id, name FROM categories ORDER BY name")


# ──────────────────────────────────────────────────────────────
# Sets
# ──────────────────────────────────────────────────────────────
def create_set(user_id, title, description, category_id):
    return db.execute(
        """INSERT INTO sets (title, description, user_id, category_id, created_at)
           VALUES (?, ?, ?, ?, datetime('now'))""",
        [title, description, user_id, category_id],
    )


def get_set(set_id):
    rows = db.query(
        """SELECT s.id, s.title, s.description, s.user_id, s.category_id, s.created_at,
                  c.name AS category_name, u.username
           FROM sets s
           LEFT JOIN categories c ON s.category_id = c.id
           JOIN users u ON s.user_id = u.id
           WHERE s.id=?""",
        [set_id],
    )
    return rows[0] if rows else None


def list_sets():
    return db.query(
        """SELECT s.id, s.title, s.description, s.created_at, s.category_id,
                  c.name AS category_name, u.username
           FROM sets s
           JOIN users u ON s.user_id = u.id
           LEFT JOIN categories c ON s.category_id = c.id
           ORDER BY s.id DESC"""
    )


def update_set(set_id, title, description, category_id):
    db.execute(
        "UPDATE sets SET title=?, description=?, category_id=? WHERE id=?",
        [title, description, category_id, set_id],
    )


def delete_set(set_id):
    """Yritä poistaa setti kerralla. Jos viiteavain estää operaation,
    poista ensin kysymykset ja kommentit ja kokeile uudestaan."""
    try:
        db.execute("DELETE FROM sets WHERE id=?", [set_id])
    except sqlite3.IntegrityError:
        # Vanha tietokanta ilman ON DELETE CASCADEa
        db.execute("DELETE FROM questions WHERE set_id=?", [set_id])
        db.execute("DELETE FROM comments WHERE set_id=?", [set_id])
        db.execute("DELETE FROM sets WHERE id=?", [set_id])


def search_sets(keyword, category):
    param = f"%{keyword}%"
    sql = """SELECT s.id, s.title, s.description, s.created_at, s.category_id,
                    c.name AS category_name, u.username
             FROM sets s
             JOIN users u ON s.user_id = u.id
             LEFT JOIN categories c ON s.category_id = c.id
             WHERE (s.title LIKE ? OR s.description LIKE ?)"""
    params = [param, param]
    if category:
        sql += " AND s.category_id = ?"
        params.append(category)
    sql += " ORDER BY s.id DESC"
    return db.query(sql, params)


# ──────────────────────────────────────────────────────────────
# Kysymykset
# ──────────────────────────────────────────────────────────────
def add_question(set_id, question_text, answer1, answer2, answer3, correct):
    db.execute(
        """INSERT INTO questions (set_id, question_text,
                                  answer1, answer2, answer3,
                                  correct_answer)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [set_id, question_text, answer1, answer2, answer3, correct],
    )


def get_questions(set_id):
    return db.query(
        """SELECT id, question_text, answer1, answer2, answer3, correct_answer
           FROM questions WHERE set_id=?""",
        [set_id],
    )


# ──────────────────────────────────────────────────────────────
# Kommentit
# ──────────────────────────────────────────────────────────────
def get_comments_for_set(set_id):
    return db.query(
        """SELECT cm.id, cm.comment_text, cm.created_at, u.username
           FROM comments cm
           JOIN users u ON cm.user_id = u.id
           WHERE cm.set_id = ?
           ORDER BY cm.created_at DESC""",
        [set_id],
    )


def get_user_sets(user_id):
    return db.query(
        """SELECT s.id, s.title, s.description, s.created_at,
                  s.category_id, c.name AS category_name
           FROM sets s
           LEFT JOIN categories c ON s.category_id = c.id
           WHERE s.user_id = ?
           ORDER BY s.created_at DESC""",
        [user_id],
    )


# ──────────────────────────────────────────────────────────────
# Reitit
# ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html", sets=list_sets())


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", filled={})

    username = request.form["username"].strip()
    pw1, pw2 = request.form["password1"], request.form["password2"]

    if not username or not pw1:
        flash("Käyttäjänimi ja salasana eivät saa olla tyhjiä.")
        return render_template("register.html", filled={"username": username})

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

    username = request.form["username"]
    password = request.form["password"]
    next_page = request.form.get("next_page") or "/"
    user_id = check_login(username, password)

    if user_id:
        session.update(
            user_id=user_id,
            username=username,
            csrf_token=secrets.token_hex(16),
        )
        flash("Kirjautuminen onnistui!")
        return redirect(next_page)

    flash("Väärä tunnus tai salasana.")
    return render_template("login.html", next_page=next_page)


@app.route("/logout", methods=["POST"])
def logout():
    check_csrf(request.form["csrf_token"])
    session.clear()
    flash("Olet kirjautunut ulos.")
    return redirect("/")


@app.route("/new_set", methods=["GET", "POST"])
def new_set():
    require_login()
    if request.method == "GET":
        return render_template("new_set.html", categories=get_categories())

    check_csrf(request.form["csrf_token"])
    title = request.form["title"].strip()
    desc = request.form["description"].strip()
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
    return render_template(
        "show_set.html",
        s=s,
        questions=get_questions(set_id),
        comments=get_comments_for_set(set_id),
    )


@app.route("/edit_set/<int:set_id>", methods=["GET", "POST"])
def edit_set(set_id):
    require_login()
    s = get_set(set_id)
    if not s or s["user_id"] != session["user_id"]:
        abort(404 if not s else 403)

    if request.method == "GET":
        return render_template("edit_set.html", s=s, categories=get_categories())

    check_csrf(request.form["csrf_token"])
    update_set(
        set_id,
        request.form["title"],
        request.form["description"],
        request.form.get("category_id"),
    )

    # uusi kysymys?
    qtext = request.form["question_text"].strip()
    if qtext:
        a1, a2, a3 = (request.form[k] for k in ("answer1", "answer2", "answer3"))
        try:
            correct = int(request.form["correct"])
            if 1 <= correct <= 3:
                add_question(set_id, qtext, a1, a2, a3, correct)
                flash("Kysymys lisätty.")
            else:
                flash("Virhe: oikea vastaus on 1–3.")
        except ValueError:
            flash("Virheellinen arvo kentässä 'Oikea vastaus'.")

    flash("Setti päivitetty.")
    return redirect(f"/edit_set/{set_id}")


@app.route("/remove_set/<int:set_id>", methods=["POST"])
def remove_set(set_id):
    require_login()
    check_csrf(request.form["csrf_token"])
    s = get_set(set_id)
    if not s or s["user_id"] != session["user_id"]:
        abort(404 if not s else 403)
    delete_set(set_id)
    flash("Setti poistettu.")
    return redirect("/")


@app.route("/search")
def search():
    query = request.args.get("query", "")
    category = request.args.get("category")
    results = search_sets(query, category) if (query or category) else []
    return render_template(
        "search.html",
        query=query,
        category=category,
        results=results,
        categories=get_categories(),
    )


@app.route("/attempt_set/<int:set_id>", methods=["GET", "POST"])
def attempt_set(set_id):
    s = get_set(set_id)
    if not s:
        abort(404)
    qs = get_questions(set_id)

    if request.method == "GET":
        return render_template("attempt_set.html", s=s, questions=qs)

    results = []
    for q in qs:
        try:
            user_ans = int(request.form.get(f"question_{q['id']}", ""))
        except ValueError:
            user_ans = -1
        results.append(
            {
                "question_text": q["question_text"],
                "answer1": q["answer1"],
                "answer2": q["answer2"],
                "answer3": q["answer3"],
                "correct": q["correct_answer"],
                "user_answer": user_ans,
                "is_correct": user_ans == q["correct_answer"],
            }
        )
    return render_template("attempt_results.html", s=s, results=results)


@app.route("/add_comment/<int:set_id>", methods=["POST"])
def add_comment(set_id):
    require_login()
    check_csrf(request.form["csrf_token"])
    comment_text = request.form.get("comment_text", "").strip()
    if not comment_text:
        flash("Kommentti ei voi olla tyhjä.")
        return redirect(f"/set/{set_id}")
    db.execute(
        "INSERT INTO comments (set_id, user_id, comment_text, created_at) "
        "VALUES (?, ?, ?, datetime('now'))",
        [set_id, session["user_id"], comment_text],
    )
    flash("Kommentti lisätty.")
    return redirect(f"/set/{set_id}")


@app.route("/profile")
def profile():
    require_login()
    enriched = [
        dict(s, comments=get_comments_for_set(s["id"]))
        for s in get_user_sets(session["user_id"])
    ]
    return render_template("profile.html", sets=enriched)


if __name__ == "__main__":
    app.run(debug=True)
