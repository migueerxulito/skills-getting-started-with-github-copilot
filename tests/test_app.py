import pytest


class TestActivitiesEndpoint:
    """Tests para GET /activities"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Verifica que el endpoint retorna todas las actividades"""
        # Arrange
        expected_activities = 9  # Total de actividades en la app
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert len(data) == expected_activities
        
    def test_get_activities_contains_chess_club(self, client):
        """Verifica que Chess Club está en las actividades"""
        # Arrange
        expected_activity = "Chess Club"
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert expected_activity in data
    
    def test_get_activities_contains_required_fields(self, client):
        """Verifica que cada actividad tiene los campos requeridos"""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Campo {field} falta en {activity_name}"
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Tests para POST /activities/{activity_name}/signup"""
    
    def test_signup_successful(self, client):
        """Verifica que un estudiante puede registrarse en una actividad"""
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Basketball%20Club"
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in response.json()["message"]
    
    def test_signup_duplicate_student_fails(self, client):
        """Verifica que un estudiante no puede registrarse dos veces"""
        # Arrange
        email = "duplicate@mergington.edu"
        activity = "Tennis%20Club"
        
        # Act - Primer registro
        response_first = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert primer registro
        assert response_first.status_code == 200
        
        # Act - Segundo registro (debe fallar)
        response_second = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert segundo registro
        assert response_second.status_code == 400
        assert "already signed up" in response_second.json()["detail"]
    
    def test_signup_invalid_activity_returns_404(self, client):
        """Verifica que registrarse en actividad inexistente retorna 404"""
        # Arrange
        email = "test@mergington.edu"
        activity = "Nonexistent%20Activity"
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_signup_activity_full_fails(self, client):
        """Verifica que no se puede registrar en una actividad llena"""
        # Arrange
        activity = "Drama%20Club"  # max_participants: 25
        emails = [f"student{i}@mergington.edu" for i in range(25)]
        
        # Act - Registrar 25 estudiantes
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Act - Intentar registrar otro cuando está llena
        response_full = client.post(f"/activities/{activity}/signup?email=extra@mergington.edu")
        
        # Assert
        assert response_full.status_code == 400
        assert "full" in response_full.json()["detail"]


class TestRemoveParticipantEndpoint:
    """Tests para DELETE /activities/{activity_name}/remove"""
    
    def test_remove_participant_successful(self, client):
        """Verifica que se puede remover un participante registrado"""
        # Arrange
        email = "remove_test@mergington.edu"
        activity = "Science%20Club"
        
        # Act - Registrar estudiante
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Act - Remover estudiante
        response = client.delete(f"/activities/{activity}/remove?email={email}")
        
        # Assert
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]
        assert email in response.json()["message"]
    
    def test_remove_non_registered_student_fails(self, client):
        """Verifica que no se puede remover a un estudiante no registrado"""
        # Arrange
        email = "notregistered@mergington.edu"
        activity = "Debate%20Club"
        
        # Act
        response = client.delete(f"/activities/{activity}/remove?email={email}")
        
        # Assert
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_remove_from_invalid_activity_fails(self, client):
        """Verifica que remover de actividad inexistente retorna 404"""
        # Arrange
        email = "test@mergington.edu"
        activity = "Fake%20Activity"
        
        # Act
        response = client.delete(f"/activities/{activity}/remove?email={email}")
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_remove_participant_updates_availability(self, client):
        """Verifica que remover un participante actualiza las plazas disponibles"""
        # Arrange
        email = "availability_test@mergington.edu"
        activity = "Music%20Club"
        
        # Act - Obtener actividades antes
        response_before = client.get("/activities")
        participants_before = len(response_before.json()[activity.replace("%20", " ")]["participants"])
        
        # Act - Registrar y remover
        client.post(f"/activities/{activity}/signup?email={email}")
        client.delete(f"/activities/{activity}/remove?email={email}")
        
        # Act - Obtener actividades después
        response_after = client.get("/activities")
        participants_after = len(response_after.json()[activity.replace("%20", " ")]["participants"])
        
        # Assert
        assert participants_after == participants_before


class TestRootEndpoint:
    """Tests para GET /"""
    
    def test_root_redirects_to_static_index(self, client):
        """Verifica que la raíz redirige a /static/index.html"""
        # Arrange
        expected_location = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_location


class TestIntegrationScenarios:
    """Tests de integración con escenarios completos"""
    
    def test_full_signup_and_removal_workflow(self, client):
        """Verifica el flujo completo: obtener actividades, registrarse, y remover"""
        # Arrange
        email = "workflow@mergington.edu"
        activity = "Programming%20Class"
        activity_name = "Programming Class"
        
        # Act - Obtener actividades
        response_activities = client.get("/activities")
        activities_before = response_activities.json()
        participants_before = len(activities_before[activity_name]["participants"])
        
        # Act - Registrarse
        response_signup = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert registro
        assert response_signup.status_code == 200
        
        # Act - Verificar que está registrado
        response_check = client.get("/activities")
        activities_after_signup = response_check.json()
        participants_after_signup = len(activities_after_signup[activity_name]["participants"])
        
        # Assert verificación
        assert participants_after_signup == participants_before + 1
        assert email in activities_after_signup[activity_name]["participants"]
        
        # Act - Remover
        response_remove = client.delete(f"/activities/{activity}/remove?email={email}")
        
        # Assert remoción
        assert response_remove.status_code == 200
        
        # Act - Verificar que fue removido
        response_final = client.get("/activities")
        activities_final = response_final.json()
        participants_final = len(activities_final[activity_name]["participants"])
        
        # Assert final
        assert participants_final == participants_before
        assert email not in activities_final[activity_name]["participants"]
