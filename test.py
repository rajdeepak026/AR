# Example:
user = User.query.filter_by(email="your_user_email@example.com").first()
print(user.fcm_token)
