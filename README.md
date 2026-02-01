# Subscription Service

Сервис управления подписками пользователей. Позволяет создавать подписки на планы, отслеживать их статус, отменять и инициировать возвраты через интеграцию с Billing Service.

### Основные функции

* Управление планами подписок (Plan)
* Активные/неактивные планы
* Стоимость, валюта, период действия
* Создание подписок (Subscription) для пользователей

**Отслеживание статусов подписок**:

* PENDING_PAYMENT — ожидает оплаты
* ACTIVE — активна
* CANCELLED — отменена пользователем
* REFUND_REQUESTED — запрошен возврат
* REFUNDED — выполнен возврат

Интеграция с платежным сервисом (BillingClient):
* Создания платежа при подписке
* Запроса возврата средств

## Архитектура

FastAPI — REST API

SQLAlchemy — ORM, работа с PostgreSQL

Alembic — миграции базы данных

Kafka — события для фоновых задач (например, recurring billing)

SQLAdmin — административная панель для планов и подписок

## Эндпоинты API
Базовый префикс: /api/v1

| Метод  | Путь                                        | Описание                                                                 |
| ------ | ------------------------------------------- | ------------------------------------------------------------------------ |
| `POST` | `/subscriptions`                            | Создать подписку на план. Параметры: `user_id`, `plan_id`, `return_url`. |
| `POST` | `/subscriptions/{subscription_id}/activate` | Активировать подписку после подтверждения платежа (`payment_id`).        |
| `POST` | `/subscriptions/{subscription_id}/cancel`   | Отменить активную подписку пользователем.                                |
| `POST` | `/subscriptions/{subscription_id}/refund`   | Запросить возврат средств. Параметры: `user_id`, `handler_url`.          |
| `GET`  | `/health`                                   | Проверка работоспособности сервиса.                                      |


## Взаимодействие с Billing Service

**Создание подписки**

Сервис подписок вызывает BillingClient.create_payment()

Передаёт: user_id, amount, currency, return_url, extra_data с ID подписки и плана

Платёж создаётся в Billing Service, пользователь перенаправляется на страницу оплаты

**Запрос возврата**

Сервис подписок вызывает BillingClient.create_refund()

Передаёт: payment_id, amount, currency, handler_url, extra_data с ID подписки

Billing Service обрабатывает возврат, статус подписки обновляется на REFUND_REQUESTED

## Админ-панель

Доступ: /admin

План и подписки можно просматривать и редактировать через SQLAdmin

Авторизация через AdminAuth

## Локальный запуск (Docker Compose)
docker-compose up --build

Postgres: subscription-postgres:5432

Kafka: subscription-kafka-0:9092

API: http://localhost:8000

Nginx: http://localhost:8008

Admin: http://localhost:8008/admin