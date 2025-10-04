from locust import HttpUser, task, between

# ------------------------------------------------------------
# locust -f load_tests/locustfile.py --host http://127.0.0.1:8000
# ------------------------------------------------------------

class FastAPIGatewayUser(HttpUser):
    wait_time = between(1, 3)  # tempo random tra richieste
    token_data = {}  # memorizza token per utente

    def on_start(self):
        """Eseguito all'avvio di ogni utente virtuale."""
        self.register_and_login()

    # ------------------------------------------------------------
    # Flusso base: registrazione + login
    # ------------------------------------------------------------
    def register_and_login(self):
        username = f"user_{self.environment.runner.user_count}"
        user_data = {
            "username": username,
            "name": "Test",
            "surname": "User",
            "email": f"{username}@example.com",
            "password": "test1234"
        }

        # Tentativo di registrazione
        self.client.post("/api/v1/auth/register", json=user_data)

        # Login
        response = self.client.post("/api/v1/auth/login", json={
            "username": username,
            "password": "test1234"
        })

        if response.status_code == 200:
            tokens = response.json()
            self.token_data = {
                "access_token": tokens.get("access_token"),
                "refresh_token": tokens.get("refresh_token")
            }

    # ------------------------------------------------------------
    # TASKS — simulate user behavior
    # ------------------------------------------------------------

    @task(2)
    def check_health(self):
        """Controlla l’endpoint /health"""
        self.client.get("/health")

    @task(2)
    def refresh_token(self):
        """Richiede nuovo token"""
        if "refresh_token" in self.token_data:
            self.client.post("/api/v1/auth/refresh", json={
                "token": self.token_data["refresh_token"]
            })

    @task(1)
    def update_user_self(self):
        """Aggiorna info utente corrente"""
        if "access_token" not in self.token_data:
            return
        headers = {"Authorization": f"Bearer {self.token_data['access_token']}"}
        self.client.patch("/api/v1/users/", json={"name": "Updated"}, headers=headers)

    @task(1)
    def change_password(self):
        """Simula cambio password"""
        if "access_token" not in self.token_data:
            return
        headers = {"Authorization": f"Bearer {self.token_data['access_token']}"}
        self.client.post(
            "/api/v1/users/change_password",
            json={"old_password": "test1234", "new_password": "newpass123"},
            headers=headers
        )

    @task(1)
    def test_rabbitmq(self):
        """Chiama endpoint test RabbitMQ"""
        self.client.get("/api/v1/users/testrabbit")

    @task(1)
    def logout(self):
        """Logout"""
        if "refresh_token" not in self.token_data:
            return
        self.client.post("/api/v1/auth/logout", json={
            "token": self.token_data["refresh_token"]
        })
