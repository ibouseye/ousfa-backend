def test_home_page_loads(test_client):
    """
    GIVEN un client de test Flask
    WHEN la page d'accueil ('/') est requêtée (GET)
    THEN vérifier que la réponse a un statut 200 (OK)
    """
    response = test_client.get('/', url_scheme='https')
    assert response.status_code == 200
