class User:
    def __init__(self, full_name, email, password_hash, role="visitor", role_id=None):
        self.full_name = full_name
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.role_id = role_id
