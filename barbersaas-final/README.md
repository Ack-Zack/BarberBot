# BarberSaaS

BarberSaaS — многопользовательский SaaS для барберов и небольших барбершопов. Основной интерфейс клиента и мастера — Telegram Mini App, backend — FastAPI.

## Что реализовано

### Клиент

- авторизация через Telegram `initData`;
- вход в бизнес по публичной `startapp`-ссылке;
- просмотр услуг и цен;
- выбор барбера;
- выбор даты и свободного времени;
- создание записи;
- просмотр истории записей;
- отмена записи;
- автоматические Telegram-напоминания.

### Владелец/барбер

- первичный onboarding: бизнес → услуга → рабочие часы;
- dashboard с расписанием по дате и мастеру;
- ручное создание записи;
- выбор существующего клиента или создание нового;
- перенос, завершение и отмена записи;
- блокировка времени;
- услуги: создание, редактирование, включение/выключение;
- рабочие часы;
- клиентская база и история посещений;
- команда мастеров;
- одноразовые приглашения барберов;
- настройки бизнеса и часового пояса;
- генерация клиентской ссылки `startapp`.

### Backend

- FastAPI;
- PostgreSQL 18;
- SQLAlchemy 2;
- Alembic;
- Pydantic 2;
- Redis + Celery;
- aiogram;
- Telegram `initData` HMAC-проверка;
- JWT access tokens;
- модульный монолит: API-модули отделены по доменам, а бизнес-правила концентрируются на backend; при росте проекта service/repository-слои можно выделить без изменения публичного API;
- PostgreSQL `EXCLUDE` constraint не допускает пересечение активных записей одного барбера;
- сервер дополнительно проверяет рабочие часы и блокировки;
- роли проверяются на backend.

## Структура

```text
barbersaas/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── bot/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── workers/
│   ├── alembic/
│   ├── alembic.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   └── Dockerfile.prod
├── docker-compose.yml
├── docker-compose.prod.yml
└── .env.example
```

## Локальный запуск

```powershell
Copy-Item .env.example .env
docker compose up --build
```

После запуска:

- Mini App: `http://localhost:5173`
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- Ready: `http://localhost:8000/ready`

Для локальной разработки есть dev-auth:

```text
http://localhost:5173/?mode=onboarding
http://localhost:5173/?mode=barber
http://localhost:5173/?mode=client
http://localhost:5173/?mode=visitor&startapp=b_demo-barbershop
```

Dev-auth доступен только при `ENVIRONMENT=development` и `ALLOW_DEV_AUTH=true`.

Бот запускается отдельным профилем:

```powershell
docker compose --profile telegram up --build
```

## Telegram setup

1. Создайте бота через BotFather.
2. Укажите `TELEGRAM_BOT_TOKEN`.
3. Укажите username бота в `TELEGRAM_BOT_USERNAME` без `@`.
4. Разместите Mini App по HTTPS-адресу.
5. Укажите этот адрес в `TELEGRAM_WEBAPP_URL`.
6. Настройте Mini App у бота в BotFather.
7. Для клиентских ссылок используется формат `https://t.me/<bot>?startapp=b_<slug>`.
8. Для приглашения барбера используется `startapp=i_<one-time-token>`.

Backend никогда не принимает `telegram_id` из frontend как доказательство личности: доверенным источником является проверенный Telegram `initData`.

## Production

Перед первым запуском замени placeholder-секреты и укажи HTTPS-домен Mini App. Production frontend использует nginx как reverse proxy для `/api/*`.


Создайте production `.env` и обязательно задайте реальные секреты:

```text
ENVIRONMENT=production
JWT_SECRET=<длинный случайный секрет>
TELEGRAM_BOT_TOKEN=<реальный токен>
TELEGRAM_BOT_USERNAME=<username>
TELEGRAM_WEBAPP_URL=https://your-domain.example
CORS_ORIGINS=https://your-domain.example
POSTGRES_PASSWORD=<сложный пароль>
```

Запуск:

```powershell
docker compose -f docker-compose.prod.yml up --build -d
```

Production compose сначала выполняет:

```text
alembic upgrade head
```

затем запускает API, worker, bot и nginx.

## Важные бизнес-правила

- клиент не может изменить чужую запись;
- барбер не может менять запись другого барбера;
- барбер не может создавать запись за другого мастера;
- клиент видит только свой бизнес;
- услуги и записи привязаны к конкретному бизнесу;
- прошлое время нельзя забронировать;
- запись не может выйти за рабочие часы;
- заблокированное время нельзя занять;
- активные записи одного мастера не могут пересекаться на уровне PostgreSQL;
- отменённые/завершённые записи не занимают слот;
- цена и длительность сохраняются в записи как исторический snapshot.

## Миграции

После изменения схемы:

```powershell
docker compose run --rm backend alembic upgrade head
```

В development схема создаётся автоматически, но для production используется только Alembic.

## Что не включено в этот MVP

Онлайн-оплата, тарифы SaaS и биллинг, SMS, несколько филиалов, промокоды, лояльность и сложная аналитика сознательно вынесены за пределы первой коммерческой версии. Это отдельный слой продукта, а не причина перегружать ядро записи.

## Проверки в этой среде

Python-источники прошли `compileall`. Полный `docker compose` runtime-тест выполнить здесь нельзя, потому что Docker в среде отсутствует. Полный npm install также не завершился из-за таймаута доступа к registry, поэтому frontend production build здесь не выдаётся за проверенный.
