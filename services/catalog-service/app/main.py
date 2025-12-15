import os
from fastapi import FastAPI

SERVICE = "catalog-service"
TITLE = "Категория (catalog-service)"

app = FastAPI(title=TITLE)

@app.get("/health")
def health():
    return {"status": "ok", "service": SERVICE}

@app.get("/")
def root():
    return {
        "service": SERVICE,
        "title": TITLE,
        "docs": "/docs",
        "note": "Минимальный сервис для ПР7 (CI/CD).",
    }

# Заглушки под контекстные операции (для демонстрации структуры API)
@app.get("/demo/actions")
def demo_actions():
    return {
        "service": SERVICE,
        "actions": [
            "create", "update", "activate/deactivate", "list", "delete"  # varies per service
        ],
    }

# Для Serverless Containers важно слушать порт из переменной окружения.
# В Dockerfile порт фиксирован 8080, но при необходимости можно переопределить.
PORT = int(os.getenv("PORT", "8080"))
