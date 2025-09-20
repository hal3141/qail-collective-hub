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

    # Player only sees their chats
    # Count unread chats
    all_chats = load_json(MESSAGES_FILE)
    visible_chats = {
    name: chat for name, chat in all_chats.items()
    if user in chat.get("participants", [])
    }
    unread_count = sum(
        1 for chat in visible_chats.values()
        for m in chat["messages"]
        if isinstance(m, dict) and not m.get("read") and m.get("from") != user
    )

    return render_template(
        "dashboard.html",
        user=user,
        t=t,
        news=news,
        hacking_data=hacking_data,
        unread_count=unread_count  # <-- FIX: now always available
    )

@app.route("/news", methods=["POST"])
def post_news():
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    all_news = load_json(NEWS_FILE)

    if "news" not in all_news:
        all_news["news"] = []

    content = request.form.get("news_content")
    if not content:
        return redirect(url_for("dashboard"))

    # Author handling
    if user == GM_USER:
        author = request.form.get("author") or GM_USER
    else:
        author = user

    title = request.form.get("title")

    timestamp = datetime.now().strftime("%H:%M - %d-%m") + "-130 NVS"

    new_entry = {
        "author": author,
        "title": title,
        "content": content,
        "timestamp": timestamp
    }

    all_news["news"].append(new_entry)
    save_json(NEWS_FILE, all_news)

    # Redirect depending on source
    source = request.form.get("source")
    if user == GM_USER and source == "gm_dashboard":
        return redirect(url_for("gm_dashboard", tab="news-tab"))
    else:
        return redirect(url_for("dashboard"))


@app.route("/messages", methods=["GET", "POST"])
def messages():
    if "user" not in session or session["user"] == GM_USER:
        return redirect(url_for("login"))

    user = session["user"]
    all_chats = load_json(MESSAGES_FILE)

    # --- Handle sending new messages ---
    if request.method == "POST":
        chat_name = request.form.get("chat_name")
        recipient = request.form.get("recipient")
        message_text = request.form.get("message")

        if not message_text:
            return redirect(url_for("messages"))

        new_message = {
            "from": user,
            "content": message_text,
            "read": False
        }

        # Case 1: new chat
        if recipient and not chat_name:
            new_id = 0
            for chat in all_chats:
                if chat.id >= new_id:
                    new_id = chat.id + 1

            chat_name = f"Chat: {request.form.get('new_chat_name') or recipient} "
            chat_title = f"Chat: {request.form.get('new_chat_name') or recipient} "
            participants = [user, recipient]
            if "NPC" in recipient or recipient == GM_USER:
                if GM_USER not in participants:
                    participants.append(GM_USER)
            all_chats[chat_name] = {
                "id": new_id,
                "participants": participants,
                "messages": [new_message]
            }

        # Case 2: reply to existing
        elif chat_name in all_chats:
            chat = all_chats[chat_name]
            if user in chat["participants"]:
                chat["messages"].append(new_message)

        save_json(MESSAGES_FILE, all_chats)
        return redirect(url_for("messages", chat=chat_name))

    # --- Handle viewing chats ---
    selected_chat = request.args.get("chat")

    # Player only sees their chats
    visible_chats = {
        name: chat for name, chat in all_chats.items()
        if user in chat.get("participants", [])
    }

    # Mark messages as read
    if selected_chat and selected_chat in visible_chats:
        for m in visible_chats[selected_chat]["messages"]:
            if isinstance(m, dict) and m.get("from") != user:
                m["read"] = True
        save_json(MESSAGES_FILE, all_chats)

    # Count unread
    unread_count = sum(
        1 for chat in visible_chats.values()
        for m in chat["messages"]
        if isinstance(m, dict) and not m.get("read") and m.get("from") != user
    )

    return render_template(
        "messages.html",
        user=user,
        chats=visible_chats,
        characters = characters,
        chat_name=selected_chat,
        unread_count=unread_count,
        t=load_translation(session["lang"])
    )


@app.route("/gm_dashboard", methods=["GET", "POST"])
def gm_dashboard():
    if "user" not in session or session["user"] != GM_USER:
        return redirect(url_for("login"))

    all_chats = load_json(MESSAGES_FILE)

    if request.method == "POST":
        chat_name = request.form.get("chat_name")
        recipient = request.form.get("recipient")
        message_text = request.form.get("message")
        from_name = request.form.get("from_name", GM_USER)

        if not message_text:
            return redirect(url_for("gm_dashboard"))

        new_message = {
            "from": from_name,
            "content": message_text,
            "read": False
        }

        # --- New Chat ---
        if recipient and not chat_name:
            new_id = 0
            for chat in all_chats:
                if chat.id >= new_id:
                    new_id = chat.id + 1
            chat_name = f"Chat: {request.form.get('new_chat_name') or recipient}"
            participants = [recipient, GM_USER]
            all_chats[chat_name] = {
                "id": new_id,
                "participants": participants,
                "messages": [new_message]
            }

        # --- Reply to Existing Chat ---
        elif chat_name in all_chats:
            chat = all_chats[chat_name]
            chat["messages"].append(new_message)

        save_json(MESSAGES_FILE, all_chats)
        return redirect(url_for("gm_dashboard", tab="messages-tab"))

    return render_template(
        "gm_dashboard.html",
        user=GM_USER,
        chats=all_chats,
        t=load_translation(session["lang"])
    )


@app.route("/files/<filetype>", methods=["GET", "POST"])
def files(filetype):
    if "user" not in session or session["user"] == GM_USER:
        return redirect(url_for("login"))

    user = session["user"]

    messages = load_json(MESSAGES_FILE)
    user_chats = messages.get(user, {})

    # Player only sees their chats
    # Count unread chats
    all_chats = load_json(MESSAGES_FILE)
    visible_chats = {
    name: chat for name, chat in all_chats.items()
    if user in chat.get("participants", [])
    }
    unread_count = sum(
        1 for chat in visible_chats.values()
        for m in chat["messages"]
        if isinstance(m, dict) and not m.get("read") and m.get("from") != user
    )

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
        unread_count=unread_count,
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
