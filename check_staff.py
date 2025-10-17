from app import app, db
from models import StaffUser

with app.app_context():
    staff_users = StaffUser.query.all()
    if staff_users:
        print("Membres du personnel dans la base de données:")
        for user in staff_users:
            print(f"ID: {user.id}, Nom d'utilisateur: {user.username}, Email: {user.email}, Rôle: {user.role}")
    else:
        print("Aucun membre du personnel trouvé dans la base de données.")
