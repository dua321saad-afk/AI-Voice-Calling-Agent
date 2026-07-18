"""
Multi-Domain LLM Voice Agent - Intelligent Edition
---------------------------------------------------
Key improvements:
  - Domain switching mid-conversation via LLM re-classification every turn
  - LLM-first intelligent responses (no keyword trapping)
  - Anti-loop frontend with proper state management
  - Full conversation context for coherent multi-turn dialogue

Two completely separate login systems:
  USER SIDE (public): /signup, /login, /services, /agent
  ADMIN SIDE (staff): /admin/login, /admin, /admin/domain/<key>, etc.
"""

import os
import uuid
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, session, abort,
)
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config, validate_config
import database as db
from data.knowledge_base import get_domain, list_domains, DOMAINS
from services import agent_service

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

db.init_db()


def user_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("account_id"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Public landing
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    if session.get("account_id"):
        return redirect(url_for("services"))
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# USER SIDE: signup / login / logout
# ---------------------------------------------------------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if session.get("account_id"):
        return redirect(url_for("services"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not password:
            flash("Please fill in all fields.", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
        elif password != confirm_password:
            flash("Passwords do not match.", "error")
        else:
            try:
                db.create_account(username, generate_password_hash(password))
                flash("Account created! Please log in.", "success")
                return redirect(url_for("login"))
            except ValueError:
                flash("That username is already taken.", "error")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("account_id"):
        return redirect(url_for("services"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        account = db.get_account_by_username(username)

        if account and check_password_hash(account["password_hash"], password):
            session["account_id"] = account["id"]
            session["account_username"] = account["username"]
            return redirect(url_for("services"))
        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("account_id", None)
    session.pop("account_username", None)
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# USER SIDE: services + live agent
# ---------------------------------------------------------------------------

@app.route("/services")
@user_login_required
def services():
    return render_template("services.html", domains=DOMAINS)


@app.route("/agent")
@user_login_required
def agent_page():
    return render_template("agent.html")


# ---------------------------------------------------------------------------
# USER SIDE: browser agent API
# ---------------------------------------------------------------------------

@app.route("/api/session/start", methods=["POST"])
@user_login_required
def api_session_start():
    session_id = str(uuid.uuid4())
    account_id = session["account_id"]
    account_username = session["account_username"]

    call_id = db.start_session(session_id, account_id, account_username)

    greeting = "Hello! How may I assist you?"
    db.log_message(call_id, "agent", greeting, source="greeting", confidence=100)

    return jsonify({"call_id": call_id, "greeting": greeting})


@app.route("/api/session/<int:call_id>/message", methods=["POST"])
@user_login_required
def api_session_message(call_id):
    call = db.get_call_by_id(call_id)
    if not call or call["account_id"] != session["account_id"]:
        return jsonify({"error": "Session not found"}), 404

    speech_text = (request.json or {}).get("message", "").strip()
    if speech_text:
        db.log_message(call_id, "user", speech_text)

    history = db.get_conversation_history(call_id)

    # Add domain_key to history entries for context
    for msg in history:
        msg["domain_key"] = call.get("domain_key")

    result = agent_service.process_turn(speech_text, call["domain_key"], history)

    db.log_message(
        call_id, "agent", result["text"],
        source=result["source"], confidence=result["confidence"],
    )

    # Handle domain switching
    if result["domain_key"] and result["domain_key"] != call["domain_key"]:
        domain = get_domain(result["domain_key"])
        db.set_session_domain(call_id, result["domain_key"], domain["label"])

        # Log the switch for admin visibility
        if result.get("switched"):
            db.log_message(
                call_id, "system", 
                f"Domain switched to {domain['label']}",
                source="domain_switch", confidence=100
            )

    if result["is_goodbye"]:
        db.end_session(call_id)

    return jsonify({
        "text": result["text"],
        "domain_key": result["domain_key"],
        "is_goodbye": result["is_goodbye"],
        "source": result["source"],
        "switched": result.get("switched", False),
    })


@app.route("/api/session/<int:call_id>/end", methods=["POST"])
@user_login_required
def api_session_end(call_id):
    call = db.get_call_by_id(call_id)
    if not call or call["account_id"] != session["account_id"]:
        return jsonify({"error": "Session not found"}), 404
    db.end_session(call_id)
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# ADMIN SIDE: auth
# ---------------------------------------------------------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin username or password.", "error")

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


# ---------------------------------------------------------------------------
# ADMIN SIDE: dashboards
# ---------------------------------------------------------------------------

@app.route("/admin")
@admin_login_required
def admin_dashboard():
    warnings = validate_config()
    accounts = db.get_all_accounts()
    calls = db.get_all_calls(limit=20)
    stats = db.get_domain_stats()
    domains = list_domains()
    return render_template(
        "dashboard.html",
        warnings=warnings,
        accounts=accounts,
        calls=calls,
        stats=stats,
        domains=domains,
    )


@app.route("/admin/domain/<domain_key>")
@admin_login_required
def domain_dashboard(domain_key):
    domain = get_domain(domain_key)
    if not domain:
        abort(404)
    calls = db.get_calls_by_domain(domain_key, limit=50)
    return render_template(
        "domain_dashboard.html",
        domain_key=domain_key,
        domain=domain,
        calls=calls,
    )


@app.route("/admin/conversation/<int:call_id>")
@admin_login_required
def conversation(call_id):
    call = db.get_call_by_id(call_id)
    if not call:
        abort(404)
    messages = db.get_messages_for_call(call_id)
    domain = get_domain(call["domain_key"]) if call["domain_key"] else None
    return render_template(
        "conversation.html",
        call=call,
        messages=messages,
        domain=domain,
    )


# ---------------------------------------------------------------------------
# ADMIN SIDE: delete authority
# ---------------------------------------------------------------------------

@app.route("/api/call/<int:call_id>", methods=["DELETE"])
@admin_login_required
def api_delete_call(call_id):
    deleted = db.delete_call(call_id)
    if not deleted:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"ok": True})


@app.route("/api/calls/clear", methods=["DELETE"])
@admin_login_required
def api_clear_calls():
    domain_key = request.args.get("domain_key")
    count = db.delete_all_calls(domain_key)
    return jsonify({"ok": True, "deleted": count})


# ---------------------------------------------------------------------------
# ADMIN SIDE: API endpoints for dashboard polling
# ---------------------------------------------------------------------------

@app.route("/api/stats")
@admin_login_required
def api_stats():
    return jsonify({
        "accounts": db.get_all_accounts(limit=50),
        "calls": db.get_all_calls(limit=30),
        "stats": db.get_domain_stats(),
    })


@app.route("/api/domain/<domain_key>/calls")
@admin_login_required
def api_domain_calls(domain_key):
    return jsonify({"calls": db.get_calls_by_domain(domain_key, limit=50)})


@app.route("/api/conversation/<int:call_id>")
@admin_login_required
def api_conversation(call_id):
    call = db.get_call_by_id(call_id)
    if not call:
        return jsonify({"error": "Not found"}), 404
    return jsonify({
        "call": call,
        "messages": db.get_messages_for_call(call_id),
    })


# ---------------------------------------------------------------------------
# Health check for Render/Railway
# ---------------------------------------------------------------------------

@app.route("/health")
def health():
    return jsonify({"status": "ok", "domains": list(DOMAINS.keys())})


if __name__ == "__main__":
    port = Config.PORT
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)