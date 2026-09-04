from locust import HttpUser, between, task


class NewsUser(HttpUser):
    wait_time = between(0.1, 0.3)

    @task(3)
    def article_list(self):
        self.client.get("/articles/")

    @task(1)
    def article_detail(self):
        self.client.get("/articles/1/")

    @task(1)
    def trending(self):
        self.client.get("/articles/trending/")
