import os
import sqlite3
from functools import wraps

from flask import (
    Flask,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)
from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "nexora-development-secret"
)

DATABASE = "nexora.db"


# ============================================================
# DATABASE
# ============================================================

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def init_db():

    db = get_db()

    # Utilisateurs
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Publications
    db.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Likes
    db.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, post_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (post_id) REFERENCES posts(id)
        )
    """)

    # Commentaires
    db.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (post_id) REFERENCES posts(id)
        )
    """)

    db.commit()
    db.close()


# ============================================================
# AUTHENTIFICATION
# ============================================================

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


# ============================================================
# CSS
# ============================================================

CSS = """
<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f4f6f8;
    color: #17202a;
}

nav {
    background: #111827;
    color: white;
    padding: 15px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 24px;
    font-weight: bold;
}

nav a {
    color: white;
    text-decoration: none;
    margin-left: 15px;
}

.container {
    width: min(700px, 94%);
    margin: 30px auto;
}

.card {
    background: white;
    padding: 22px;
    border-radius: 14px;
    margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
}

input,
textarea {
    width: 100%;
    padding: 12px;
    margin: 8px 0 14px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 16px;
}

textarea {
    min-height: 90px;
    resize: vertical;
}

button {
    background: #2563eb;
    color: white;
    border: none;
    padding: 10px 16px;
    border-radius: 8px;
    cursor: pointer;
}

button:hover {
    opacity: 0.9;
}

.post {
    margin-top: 20px;
}

.username {
    font-weight: bold;
    font-size: 17px;
}

.date {
    color: #6b7280;
    font-size: 13px;
}

.actions {
    display: flex;
    gap: 10px;
    margin-top: 15px;
}

.like-button {
    background: #ef4444;
}

.comment {
    background: #f3f4f6;
    padding: 10px;
    border-radius: 8px;
    margin-top: 8px;
}

.comment-user {
    font-weight: bold;
}

.center {
    text-align: center;
}

.error {
    background: #fee2e2;
    color: #991b1b;
    padding: 10px;
    border-radius: 8px;
}

</style>
"""


# ============================================================
# NAVIGATION
# ============================================================

NAV = """
<nav>

    <div class="logo">
        Nexora 🚀
    </div>

    <div>

        {% if session.get("user_id") %}

            <a href="{{ url_for('feed') }}">
                Accueil
            </a>

            <a href="{{ url_for(
                'profile',
                username=session.get('username')
            ) }}">
                Profil
            </a>

            <a href="{{ url_for('logout') }}">
                Déconnexion
            </a>

        {% else %}

            <a href="{{ url_for('login') }}">
                Connexion
            </a>

            <a href="{{ url_for('register') }}">
                Inscription
            </a>

        {% endif %}

    </div>

</nav>
"""


# ============================================================
# ACCUEIL
# ============================================================

@app.route("/")
def home():

    if session.get("user_id"):
        return redirect(url_for("feed"))

    return render_template_string(
        CSS + NAV + """

        <div class="container">

            <div class="card center">

                <h1>
                    Bienvenue sur Nexora 🚀
                </h1>

                <p>
                    Le réseau social nouvelle génération.
                </p>

                <a href="{{ url_for('register') }}">
                    <button>
                        Créer un compte
                    </button>
                </a>

                <br><br>

                <a href="{{ url_for('login') }}">
                    Se connecter
                </a>

            </div>

        </div>
        """
    )


# ============================================================
# INSCRIPTION
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not username or not email or not password:

            return render_template_string(
                CSS + NAV + """

                <div class="container">

                    <div class="card">

                        <div class="error">
                            Tous les champs sont obligatoires.
                        </div>

                        <h2>
                            Créer un compte
                        </h2>

                        <form method="POST">

                            <input
                                name="username"
                                placeholder="Nom d'utilisateur"
                                required
                            >

                            <input
                                name="email"
                                type="email"
                                placeholder="Email"
                                required
                            >

                            <input
                                name="password"
                                type="password"
                                placeholder="Mot de passe"
                                required
                            >

                            <button>
                                Créer mon compte
                            </button>

                        </form>

                    </div>

                </div>
                """
            )

        password_hash = generate_password_hash(
            password
        )

        db = get_db()

        try:

            db.execute(
                """
                INSERT INTO users
                (username, email, password)
                VALUES (?, ?, ?)
                """,
                (
                    username,
                    email,
                    password_hash
                )
            )

            db.commit()

        except sqlite3.IntegrityError:

            db.close()

            return render_template_string(
                CSS + NAV + """

                <div class="container">

                    <div class="card">

                        <div class="error">
                            Ce nom d'utilisateur
                            ou cet email existe déjà.
                        </div>

                        <a href="{{ url_for('register') }}">
                            Réessayer
                        </a>

                    </div>

                </div>
                """
            )

        db.close()

        return redirect(
            url_for("login")
        )

    return render_template_string(
        CSS + NAV + """

        <div class="container">

            <div class="card">

                <h2>
                    Créer un compte 🚀
                </h2>

                <form method="POST">

                    <input
                        name="username"
                        placeholder="Nom d'utilisateur"
                        required
                    >

                    <input
                        name="email"
                        type="email"
                        placeholder="Email"
                        required
                    >

                    <input
                        name="password"
                        type="password"
                        placeholder="Mot de passe"
                        required
                    >

                    <button>
                        Créer mon compte
                    </button>

                </form>

                <p>
                    Déjà inscrit ?

                    <a href="{{ url_for('login') }}">
                        Se connecter
                    </a>
                </p>

            </div>

        </div>
        """
    )


# ============================================================
# CONNEXION
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        db = get_db()

        user = db.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        db.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect(
                url_for("feed")
            )

        return render_template_string(
            CSS + NAV + """

            <div class="container">

                <div class="card">

                    <div class="error">
                        Email ou mot de passe incorrect.
                    </div>

                    <h2>
                        Connexion
                    </h2>

                    <form method="POST">

                        <input
                            name="email"
                            type="email"
                            placeholder="Email"
                            required
                        >

                        <input
                            name="password"
                            type="password"
                            placeholder="Mot de passe"
                            required
                        >

                        <button>
                            Se connecter
                        </button>

                    </form>

                </div>

            </div>
            """
        )

    return render_template_string(
        CSS + NAV + """

        <div class="container">

            <div class="card">

                <h2>
                    Connexion 🔐
                </h2>

                <form method="POST">

                    <input
                        name="email"
                        type="email"
                        placeholder="Email"
                        required
                    >

                    <input
                        name="password"
                        type="password"
                        placeholder="Mot de passe"
                        required
                    >

                    <button>
                        Se connecter
                    </button>

                </form>

                <p>
                    Pas encore de compte ?

                    <a href="{{ url_for('register') }}">
                        Inscription
                    </a>
                </p>

            </div>

        </div>
        """
    )


# ============================================================
# DÉCONNEXION
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# ============================================================
# FIL D'ACTUALITÉ
# ============================================================

@app.route("/feed")
@login_required
def feed():

    db = get_db()

    posts = db.execute(
        """
        SELECT
            posts.id,
            posts.content,
            posts.created_at,
            users.username
        FROM posts
        JOIN users
        ON posts.user_id = users.id
        ORDER BY posts.id DESC
        """
    ).fetchall()

    post_data = []

    for post in posts:

        like_count = db.execute(
            """
            SELECT COUNT(*)
            FROM likes
            WHERE post_id = ?
            """,
            (post["id"],)
        ).fetchone()[0]

        user_like = db.execute(
            """
            SELECT id
            FROM likes
            WHERE post_id = ?
            AND user_id = ?
            """,
            (
                post["id"],
                session["user_id"]
            )
        ).fetchone()

        comments = db.execute(
            """
            SELECT
                comments.content,
                comments.created_at,
                users.username
            FROM comments
            JOIN users
            ON comments.user_id = users.id
            WHERE comments.post_id = ?
            ORDER BY comments.id ASC
            """,
            (post["id"],)
        ).fetchall()

        post_data.append(
            {
                "post": post,
                "likes": like_count,
                "liked": user_like is not None,
                "comments": comments
            }
        )

    db.close()

    return render_template_string(
        CSS + NAV + """

        <div class="container">

            <div class="card">

                <h2>
                    Fil d'actualité 📰
                </h2>

                <form
                    method="POST"
                    action="{{ url_for('create_post') }}"
                >

                    <textarea
                        name="content"
                        placeholder="Quoi de neuf ?"
                        maxlength="1000"
                        required
                    ></textarea>

                    <button>
                        Publier 🚀
                    </button>

                </form>

            </div>


            {% for item in post_data %}

                <div class="card post">

                    <div class="username">
                        @{{ item.post["username"] }}
                    </div>

                    <div class="date">
                        {{ item.post["created_at"] }}
                    </div>

                    <p>
                        {{ item.post["content"] }}
                    </p>


                    <!-- LIKE -->

                    <div class="actions">

                        <form
                            method="POST"
                            action="{{ url_for(
                                'toggle_like',
                                post_id=item.post['id']
                            ) }}"
                        >

                            {% if item.liked %}

                                <button class="like-button">
                                    ❤️ J'aime
                                </button>

                            {% else %}

                                <button>
                                    🤍 J'aime
                                </button>

                            {% endif %}

                        </form>

                        <span>
                            ❤️ {{ item.likes }}
                        </span>

                    </div>


                    <!-- COMMENTAIRES -->

                    <h3>
                        💬 Commentaires
                    </h3>

                    {% for comment in item.comments %}

                        <div class="comment">

                            <div class="comment-user">
                                @{{ comment["username"] }}
                            </div>

                            <div>
                                {{ comment["content"] }}
                            </div>

                            <div class="date">
                                {{ comment["created_at"] }}
                            </div>

                        </div>

                    {% else %}

                        <p>
                            Aucun commentaire.
                        </p>

                    {% endfor %}


                    <!-- AJOUTER COMMENTAIRE -->

                    <form
                        method="POST"
                        action="{{ url_for(
                            'add_comment',
                            post_id=item.post['id']
                        ) }}"
                    >

                        <input
                            name="content"
                            placeholder="Écrire un commentaire..."
                            maxlength="500"
                            required
                        >

                        <button>
                            Commenter 💬
                        </button>

                    </form>

                </div>

            {% else %}

                <div class="card center">

                    <p>
                        Aucune publication pour le moment.
                    </p>

                </div>

            {% endfor %}

        </div>
        """,
        post_data=post_data
    )


# ============================================================
# CRÉER UNE PUBLICATION
# ============================================================

@app.route("/post", methods=["POST"])
@login_required
def create_post():

    content = request.form.get(
        "content",
        ""
    ).strip()

    if content:

        db = get_db()

        db.execute(
            """
            INSERT INTO posts
            (user_id, content)
            VALUES (?, ?)
            """,
            (
                session["user_id"],
                content
            )
        )

        db.commit()
        db.clo
