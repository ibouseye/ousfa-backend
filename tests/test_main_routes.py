from app.models import ContactMessage

def test_contact_page_loads(test_client):
    """
    GIVEN un client de test Flask
    WHEN la page de contact ('/contact') est requêtée (GET)
    THEN vérifier que la réponse a un statut 200 (OK)
    """
    response = test_client.get('/contact', url_scheme='https')
    assert response.status_code == 200

def test_contact_form_submission(test_client, db):
    """
    GIVEN un client de test Flask
    WHEN le formulaire de contact est soumis (POST) avec des données valides
    THEN vérifier que le message est créé en base de données et que l'utilisateur est redirigé
    """
    # GIVEN
    initial_count = ContactMessage.query.count()

    # WHEN
    form_data = {
        'name': 'Test User',
        'email': 'test@example.com',
        'message': 'This is a test message.'
    }
    response = test_client.post('/contact', data=form_data, follow_redirects=False)

    # THEN
    assert response.status_code == 302
    final_count = ContactMessage.query.count()
    assert final_count == initial_count + 1
