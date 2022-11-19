import time
from locust import HttpUser, task, between
class QuickstartUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def gethtml(self):
        self.client.get("/generatetoken")
        self.client.get("/activateacc")

    @task(3)
    def view_items(self):
        self.client.post("/generatetoken")