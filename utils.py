
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash("Admin access required", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return wrapper

def validate_password_policy(pw):
    # simple policy: min 8, at least 1 number and 1 letter
    import re
    if len(pw) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[0-9]", pw):
        return False, "Password must include at least one number."
    if not re.search(r"[A-Za-z]", pw):
        return False, "Password must include letters."
    return True, ""

