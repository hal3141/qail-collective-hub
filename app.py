from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "qail-secret-key"

# --- Load character credentials ---
characters = {
    "A. Ceeda": "731",
    "F.M. Latatga": "248",
    "J. Latatga": "564",
    "K. Cagla": "119",
    "L. Cagla": "802",
    "G. Kitaff": "393",
    "J. Reltec": "604",
    "R. Eibeqx": "720",
    "W. Proluk": "431",
    "T. Shaaret": "185",
    "Q. Dran": "948",
    "D. Scafcar": "317",
    "H. Lastal": "682",
    "T. Qail": "526",
    "E.P. Rinsmitt": "903",
    "E.T. Jeyik": "257",
    "B.R. Briskat": "666",
    "R. Kesyk": "321",
    "S. Nito": "440",
    "V. Kulata": "774",
    "S. Ceeda": "155",
    "C. So'miss": "506",
    "P. Ceeda": "630"
}

GM_USER = "GM"
GM_PASS = "qail-123"

NEWS_FILE = "data/news.json"
MESSAGES_FILE = "data/messages.json"
FILES_FILE = "data/files.json"


def load_json(filename):
    if not os.path.exists(filename):
        return {} if filename.endswith(".json") else []
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# --- Translation ---
def load_translation(lang):
    path = os.path.join("translations", f"{lang}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


@app.before_request
def ensure_lang():
    if "lang" not in session:
        session["lang"] = "en"


@app.route("/set_lang/<lang>")
def set_lang(lang):
    if lang in ["en", "de"]:
        session["lang"] = lang
    return redirect(request.referrer or url_for("login"))


@app.route("/", methods=["GET", "POST"])
def login():
    t = load_translation(session["lang"])
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == GM_USER and password == GM_PASS:
            session["user"] = GM_USER
            session["just_logged_in"] = True
            return redirect(url_for("gm_dashboard"))
        elif username in characters and characters[username] == password:
            session["user"] = username
            session["just_logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials.", t=t)

    return render_template("login.html", t=t)


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    t = load_translation(session.get("lang", "en"))

    messages = load_json(MESSAGES_FILE)
    user_chats = messages.get(user, {})

    # Load news
    news = load_json(NEWS_FILE)

    # Default: no hacking data
    hacking_data = None
    if user == "R. Kesyk":
        hacking_data = characters

    return render_template(
        "dashboard.html",
        user=user,
        t=t,
        news=news,
        hacking_data=hacking_data,
        unread_count=sum(1 for c in user_chats.values() if c.get("unread"))  # <-- FIX: now always available
    )



@app.route("/messages", methods=["GET", "POST"])
def messages():
    if "user" not in session or session["user"] == GM_USER:
        return redirect(url_for("login"))

    user = session["user"]
    all_messages = load_json(MESSAGES_FILE)
    user_chats = all_messages.get(user, {})

    chat_name = request.args.get("chat")

    # Player replies
    if request.method == "POST" and chat_name and "reply" in request.form:
        reply_text = request.form["reply"]
        new_msg = {
            "from": user,
            "content": reply_text,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

        if chat_name not in all_messages[user]:
            all_messages[user][chat_name] = {"messages": [], "unread": False}
        all_messages[user][chat_name]["messages"].append(new_msg)
        all_messages[user][chat_name]["unread"] = False

        # Deliver to other players in chat (if any)
        for other, chats in all_messages.items():
            if other != user and chat_name in chats and any(m["from"] == user for m in chats[chat_name]["messages"]):
                chats[chat_name]["messages"].append(new_msg)
                chats[chat_name]["unread"] = True

        # Always deliver to GM
        if "GM" not in all_messages:
            all_messages["GM"] = {}
        if chat_name not in all_messages["GM"]:
            all_messages["GM"][chat_name] = {"messages": [], "unread": False}
        all_messages["GM"][chat_name]["messages"].append(new_msg)
        all_messages["GM"][chat_name]["unread"] = True

        save_json(MESSAGES_FILE, all_messages)

    # Player starts a new chat
    elif request.method == "POST" and "start_chat" in request.form:
        recipient = request.form["recipient"].strip()
        chat_name = request.form["chat_name"].strip()
        message_text = request.form["message"].strip()

        new_msg = {
            "from": user,
            "content": message_text,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

        # Sender
        if user not in all_messages:
            all_messages[user] = {}
        all_messages[user][chat_name] = {"messages": [new_msg], "unread": False}

        if recipient in characters:
            if recipient not in all_messages:
                all_messages[recipient] = {}
            all_messages[recipient][chat_name] = {"messages": [new_msg], "unread": True}

        # Always log to GM
        if "GM" not in all_messages:
            all_messages["GM"] = {}
        all_messages["GM"][chat_name] = {"messages": [new_msg], "unread": True}

        save_json(MESSAGES_FILE, all_messages)

    if chat_name:
        chat_thread = user_chats.get(chat_name, {"messages": [], "unread": False})
        chat_thread["unread"] = False
        save_json(MESSAGES_FILE, all_messages)
        t = load_translation(session["lang"])
        return render_template("messages.html", user=user, chat_name=chat_name,
                               messages=chat_thread["messages"], chats=user_chats,
                               unread_count=sum(1 for c in user_chats.values() if c.get("unread")), t=t)
    else:
        unread_count = sum(1 for c in user_chats.values() if c.get("unread"))
        t = load_translation(session["lang"])
        return render_template("messages.html", user=user, chats=user_chats, chat_name=None, unread_count=unread_count, t=t)


@app.route("/gm", methods=["GET", "POST"])
def gm_dashboard():
    if "user" not in session or session["user"] != GM_USER:
        return redirect(url_for("login"))

    news = load_json(NEWS_FILE)
    messages = load_json(MESSAGES_FILE)

    if request.method == "POST":
        if "post_news" in request.form:
            new_entry = {
                "title": request.form["title"],
                "content": request.form["content"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            news.append(new_entry)
            save_json(NEWS_FILE, news)

        elif "send_message" in request.form:
            recipient = request.form["recipient"]
            chat_name = request.form["chat_name"]
            sender_name = request.form["sender_name"].strip()
            new_msg = {
                "from": sender_name if sender_name else "GM",
                "content": request.form["message"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
            }

            if recipient not in messages:
                messages[recipient] = {}
            if chat_name not in messages[recipient]:
                messages[recipient][chat_name] = {"messages": [], "unread": False}
            messages[recipient][chat_name]["messages"].append(new_msg)
            messages[recipient][chat_name]["unread"] = True

            if "GM" not in messages:
                messages["GM"] = {}
            if chat_name not in messages["GM"]:
                messages["GM"][chat_name] = {"messages": [], "unread": False}
            messages["GM"][chat_name]["messages"].append(new_msg)
            messages["GM"][chat_name]["unread"] = False

            save_json(MESSAGES_FILE, messages)

    t = load_translation(session["lang"])
    return render_template("gm_dashboard.html", news=news, messages=messages, players=list(characters.keys()), t=t)

@app.route("/files/<filetype>", methods=["GET", "POST"])
def files(filetype):
    if "user" not in session or session["user"] == GM_USER:
        return redirect(url_for("login"))

    user = session["user"]
    all_files = load_json(FILES_FILE)

    allowed = {}
    error = None

    # --- T. Qail and H. Lastal have special rights ---
    if user in ["T. Qail", "H. Lastal"]:
        allowed = {name: f[filetype] for name, f in all_files.items()}
    else:
        # Team leads: all personnel
        if filetype == "personnel" and user in ["E.P. Rinsmitt", "Q. Dran", "T. Shaaret", "A. Ceeda"]:
            allowed = {name: f["personnel"] for name, f in all_files.items() if name != "T. Qail"}

        # Security team: all security
        elif filetype == "security" and user in ["B.R. Briskat", "E.P. Rinsmitt", "E.T. Jeyik", "J. Latatga", "S. Nito"]:
            allowed = {name: f["security"] for name, f in all_files.items() if name != "T. Qail"}

        # Medics: all medical
        elif filetype == "medical" and user in ["Q. Dran", "D. Scafcar"]:
            allowed = {name: f["medical"] for name, f in all_files.items() if name != "T. Qail"}

        # Own personnel file
        if filetype == "personnel" and user in all_files and user != "T. Qail":
            allowed[user] = all_files[user]["personnel"]

        # Own security file
        if filetype == "security" and user in ["B.R. Briskat", "E.P. Rinsmitt", "E.T. Jeyik", "J. Latatga", "S. Nito"] and user != "T. Qail":
            allowed[user] = all_files[user]["security"]

        # Own medical file
        if filetype == "medical" and user in ["Q. Dran", "D. Scafcar"] and user != "T. Qail":
            allowed[user] = all_files[user]["medical"]

    # --- Handle file updates (POST) ---
    if request.method == "POST":
        selected_char = request.form.get("char")
        if selected_char and selected_char in all_files:
            # T. Qail can edit everything
            if user == "T. Qail":
                for key in all_files[selected_char][filetype]:
                    all_files[selected_char][filetype][key] = request.form.get(key, all_files[selected_char][filetype][key])
                save_json(FILES_FILE, all_files)

            # H. Lastal can edit personnel
            elif filetype == "personnel" and user == "H. Lastal":
                for key in all_files[selected_char]["personnel"]:
                    all_files[selected_char]["personnel"][key] = request.form.get(key, all_files[selected_char]["personnel"][key])
                save_json(FILES_FILE, all_files)

            # Security can edit security
            elif filetype == "security" and user in ["B.R. Briskat", "E.P. Rinsmitt", "E.T. Jeyik", "J. Latatga", "S. Nito"]:
                for key in all_files[selected_char]["security"]:
                    all_files[selected_char]["security"][key] = request.form.get(key, all_files[selected_char]["security"][key])
                save_json(FILES_FILE, all_files)

            # Medics can edit medical
            elif filetype == "medical" and user in ["Q. Dran", "D. Scafcar"]:
                for key in all_files[selected_char]["medical"]:
                    all_files[selected_char]["medical"][key] = request.form.get(key, all_files[selected_char]["medical"][key])
                save_json(FILES_FILE, all_files)

    # --- Handle dropdown selection ---
    selected_char = request.args.get("char") or request.form.get("char")
    selected_file = None
    if selected_char and selected_char in allowed:
        selected_file = {selected_char: allowed[selected_char]}
    elif selected_char == "T. Qail" and error:
        selected_file = {"T. Qail": {"Access Denied": error}}

    return render_template(
        "files.html",
        user=user,
        filetype=filetype,
        files=allowed,
        selected_file=selected_file,
        t=load_translation(session["lang"])
    )

@app.route("/logout")
def logout():
    session["just_logged_out"] = True
    session.pop("user", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(NEWS_FILE):
        save_json(NEWS_FILE, [])
    if not os.path.exists(MESSAGES_FILE):
        save_json(MESSAGES_FILE, {})
    if not os.path.exists(FILES_FILE):
        save_json(FILES_FILE, {})
    app.run(debug=True)
