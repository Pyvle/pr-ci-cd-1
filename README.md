# ПР7 CI/CD — шаблон проекта под микросервисы (Товар/Каталог/Цена/Остаток/Отзывы/Медиа)

Этот проект — готовая заготовка, чтобы выполнить **Практическую работу №7 (CI/CD)** из методички.

## Что уже сделано в репозитории
- 6 минимальных микросервисов (FastAPI) с `Dockerfile` и `requirements.txt`
- GitHub Actions workflow, который **собирает и пушит ВСЕ сервисы в DockerHub**
- Отдельный workflow, который **собирает pricing-service и деплоит в Yandex Serverless Containers** (через YC Container Registry)

## 1) Как выполнить ПР7 (по методичке)
Методичка требует:
1) Для **одного** сервиса настроить CI + доставку в **DockerHub**.
2) Для **второго** сервиса настроить CI + **развёртывание** в виде serverless-контейнера в Яндекс.Облаке.

В этом шаблоне:
- `product-service` и остальные сервисы пушатся в DockerHub
- `pricing-service` деплоится в Serverless Containers (YC)

## 2) Подготовка DockerHub
1. Создай аккаунт/репозитории в DockerHub (можно без предварительного создания репо — DockerHub создаст автоматически при push).
2. В GitHub репозитории открой: **Settings → Secrets and variables → Actions → Secrets**
3. Добавь секреты:
   - `DOCKER_USERNAME`
   - `DOCKER_PASSWORD`

## 3) Подготовка Яндекс.Облака (YC)
Нужно сделать то, что описано в методичке:
1. Container Registry: создай/выбери реестр.
2. Service Account: создай/выбери сервисный аккаунт и **создай авторизованный ключ** (json).
3. Serverless Containers: создай serverless container. В методичке указано, что **имя контейнера должно начинаться с фамилии студента**.
4. В GitHub Secrets добавь:
   - `YC_KEYS` — содержимое json-ключа
   - `YC_REGISTRY_ID` — id реестра
   - `YC_FOLDER_ID` — id каталога
   - `YC_SA_ID` — id сервисного аккаунта
   - `YC_CONTAINER_NAME` — имя serverless container для pricing-service

## 4) Проверка локально (не обязательно, но полезно)
```bash
cd services/product-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```
Открой `http://localhost:8080/docs`.

## 5) Как запустить CI/CD
1. Закоммить и запушь проект в GitHub.
2. При пуше в `main/master` GitHub Actions:
   - `dockerhub-all-services.yml` соберёт и отправит 6 образов в DockerHub.
   - `pricing-yc-deploy.yml` соберёт pricing-service, загрузит образ в YC Registry и сделает deploy в Serverless Containers.

> Если хочешь деплоить в YC не только pricing-service — просто клонируй workflow и поменяй имя сервиса/образ.
