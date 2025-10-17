import sys
from app import create_app, db
from app.models import PageVisit

app = create_app()

with app.app_context():
    try:
        visit_count = db.session.query(PageVisit).count()
        print(f"SUCCESS: Nombre total de visites enregistrees : {visit_count}")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: Erreur lors de la verification des visites : {e}")
        sys.exit(1)
