# Qail Collective Data Hub

A locally hosted Star Wars–inspired data hub for your LARP event.  
Provides secure logins for playable characters and a hidden GM interface.
The hub allows players to access news, exchange private messages, view/edit files, and even perform special in-game actions (like hacking).

---

## 🚀 Features

### 🔑 Login System
- Each **player character** has a **username and 3-digit password**.
- A hidden **GM login (`qail-123`)** gives the Game Master access to send/manage player messages.
- Special rules per character (see below).

---

### 📰 News Dashboard
- Displays in-game **news entries**.
- Styled with a **retro terminal / sci-fi vibe**.
- Accessible to **all players**.
- News updates can be managed via the GM dashboard file.

---

### 💬 Messaging System
- Players can:
  - View **their private messages**.
  - **Reply** to existing chats.
  - **Start new chats** by entering a recipient (player name or NPC name).
    - If recipient is another **player character**, both the GM and that player see the chat.
    - If recipient is a **non-player name**, only the GM sees it.
- The GM can:
  - Start new chats with any player.
  - Assign **chat names**.
  - Choose which **name to represent as** when sending.
- **Unread message counters** are shown in the top bar.

---

### 📂 File Access (Personnel, Security, Medical)
Each player has **3 types of files** stored in `files.json`.

- **Personnel File**
  - Every player sees their own.
  - **Team leads** can access all personnel files.
  - **CEO & Assistant** can view all files (special leadership).
  - **Editing**:  
    - **CEO** → can edit **all files** (personnel, security, medical).  
    - **Assistant** → can edit all personnel files.  
    - Others cannot edit personnel.

- **Security File**
  - Only **security officers** can access their own + all other security files.
  - **Editing**: Security team can edit security files.

- **Medical File**
  - Only **medics** can access all medical files.
  - **Editing**: Medics can edit medical files.

- File selection is handled via a **dropdown menu** for clarity.

---

### 🧑‍💻 Hacking (R. Kesyk only)
- When logged in as a player with hacking abilities, a **special “Initiate Hack” button** appears.
- Triggering it:
  1. Opens a **hacking overlay** (50% screen height).
  2. Displays **random alphanumeric code lines** for 30s (max 5 lines visible at a time).
  3. Includes a **progress bar** filling over 30s.
  4. At the end, the stream clears and **credentials of a random other player** (username + password) are displayed for 3s.
  5. Overlay disappears and the hack button is removed until next login.

---

### 🌐 Multi-language Support
- Static UI texts can be switched between **English** and **German**.
- Language selection is available on the login screen.

---

## 📦 Installation and execution

1. Clone or unzip the project.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
3. Run the Flask app:
   ```bash
   python app.py
4. Open in your browser:
    http://127.0.0.1:5000/

---
