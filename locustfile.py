from locust import HttpUser, task, between

class TaskManagerUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        # Шаг 1: Получить страницу логина для CSRF-токена
        res = self.client.get("/login/")
        csrf_token = res.cookies.get('csrftoken', '')
        # Шаг 2: Отправить логин с токеном
        self.client.post("/login/", {
            "username": "locust_user",
            "password": "123locust_pass",
            "csrfmiddlewaretoken": csrf_token
        }, headers={"X-CSRFToken": csrf_token})
        # Сохраняем CSRF-токен для дальнейших запросов
        self.csrf_token = self.client.cookies.get('csrftoken', '')

    @task(3)
    def home(self):
        self.client.get("/")

    @task(2)
    def project_detail(self):
        self.client.get("/project/1/")

    @task(1)
    def change_status(self):
        self.client.post("/api/task/1/update-status/",
                         json={"status": "done"},
                         headers={
                             "Content-Type": "application/json",
                             "X-CSRFToken": self.csrf_token
                         })