import re


def validate_signup(full_name, email, password, confirm_password, terms):
    errors = {}

    if not full_name:
        errors["full_name"] = "יש להזין שם מלא."

    email_pattern = r"^[^@]+@[^@]+\.[^@]+$"
    if not email:
        errors["email"] = "יש להזין כתובת אימייל."
    elif not re.match(email_pattern, email):
        errors["email"] = "כתובת האימייל אינה תקינה."

    if not password:
        errors["password"] = "יש להזין סיסמה."
    elif len(password) < 8:
        errors["password"] = "הסיסמה חייבת להכיל לפחות 8 תווים."

    if not confirm_password:
        errors["confirm_password"] = "יש להזין אימות סיסמה."
    elif password != confirm_password:
        errors["confirm_password"] = "הסיסמאות אינן תואמות."

    if not terms:
        errors["terms"] = "יש לאשר את תנאי השימוש ומדיניות הפרטיות."

    return errors
