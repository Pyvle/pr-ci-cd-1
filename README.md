
# Два микросервиса по диаграммам + CI/CD (DockerHub и Yandex Cloud Serverless Containers)

В репозитории 2 сервиса, сделанные по вашим диаграммам:

1) **reviews-service** — управление отзывами о товаре  
2) **media-service** — управление медиа-объектами товара (изображения/видео)

Оба сервиса — **FastAPI** + **SQLite**, запускаются в контейнерах.

## Структура
```
.
├─ reviews-service/
├─ media-service/
└─ .github/workflows/
```

## Локальный запуск (без Docker)
### reviews-service
```bash
cd reviews-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### media-service
```bash
cd media-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8081
```

## Запуск через Docker
### reviews-service
```bash
docker build -t reviews-service:local ./reviews-service
docker run -p 8080:8080 -e DATABASE_URL=sqlite:////data/reviews.db -v $(pwd)/data:/data reviews-service:local
```

### media-service
```bash
docker build -t media-service:local ./media-service
docker run -p 8081:8081 -e DATABASE_URL=sqlite:////data/media.db -v $(pwd)/data:/data media-service:local
```

## Секреты GitHub Actions

### 1) Workflow для DockerHub (reviews-service)
В **Settings → Secrets and variables → Actions → Secrets** добавьте:
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`

### 2) Workflow для Yandex Cloud (media-service)
Добавьте:
- `YC_KEYS` — содержимое файла ключей сервисного аккаунта (json)
- `YC_REGISTRY_ID`
- `YC_FOLDER_ID`
- `YC_CONTAINER_NAME`
- `YC_SA_ID`

Опционально:
- `ADMIN_TOKEN` — токен администратора (используется сервисами при проверке админ-эндпоинтов)

## Эндпоинты (кратко)
- У каждого сервиса есть `GET /health`.
- Документация Swagger:
  - reviews-service: `http://localhost:8080/docs`
  - media-service: `http://localhost:8081/docs`
