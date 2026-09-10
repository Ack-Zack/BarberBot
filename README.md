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
- SQLite через aiosqlite (для локальной разработки; PostgreSQL остаётся целевым для production);
- SQLAlchemy 2;
- Alembic;
- Pydantic 2;
- Redis + Celery (опционально: только для Telegram-напоминаний);
- aiogram;
- Telegram `initData` HMAC-проверка;
- JWT access tokens;
- модульный монолит: API-модули отделены по доменам, а бизнес-правила концентрируются на backend; при росте проекта service/repository-слои можно выделить без изменения публичного API;
- пересечение активных записей одного барбера блокируется на уровне backend (в SQLite `EXCLUDE`-констрейнт недоступен; при переходе на PostgreSQL верните его по схеме из git-истории);
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
│   └── src/
├── start-backend.bat
├── start-frontend.bat
└── .env.example
```

## Локальный запуск (без Docker)

Требования: Python 3.14+, Node.js 24+. База данных — SQLite, ничего ставить не нужно.

```powershell
Copy-Item .env.example .env
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
cd backend
..\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

Во втором терминале:

```powershell
cd frontend
npm install
npm run dev
```

Или просто запустите `start-backend.bat` и `start-frontend.bat` из корня проекта.

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

Бот запускается отдельным процессом (нужен реальный `TELEGRAM_BOT_TOKEN`):

```powershell
cd backend
python -m app.bot.main
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

Для production рекомендуется PostgreSQL (миграция с SQLite: `alembic` + замена `DATABASE_URL` на `postgresql+asyncpg://...` и возврат `EXCLUDE`-констрейнта). Перед деплоем замени placeholder-секреты и укажи HTTPS-домен Mini App.

Создайте production `.env` и обязательно задайте реальные секреты:

```text
ENVIRONMENT=production
JWT_SECRET=<длинный случайный секрет>
TELEGRAM_BOT_TOKEN=<реальный токен>
TELEGRAM_BOT_USERNAME=<username>
TELEGRAM_WEBAPP_URL=https://your-domain.example
CORS_ORIGINS=https://your-domain.example
```

## Важные бизнес-правила

- клиент не может изменить чужую запись;
- барбер не может менять запись другого барбера;
- барбер не может создавать запись за другого мастера;
- клиент видит только свой бизнес;
- услуги и записи привязаны к конкретному бизнесу;
- прошлое время нельзя забронировать;
- запись не может выйти за рабочие часы;
- заблокированное время нельзя занять;
- активные записи одного мастера не могут пересекаться (backend-проверка; в PostgreSQL дополнительно защищается `EXCLUDE`-констрейнтом);
- отменённые/завершённые записи не занимают слот;
- цена и длительность сохраняются в записи как исторический snapshot.

## Миграции

После изменения схемы:

```powershell
cd backend
alembic upgrade head
```

В development схема создаётся автоматически при старте API, но для production используется только Alembic.

## Что не включено в этот MVP

Онлайн-оплата, тарифы SaaS и биллинг, SMS, несколько филиалов, промокоды, лояльность и сложная аналитика сознательно вынесены за пределы первой коммерческой версии. Это отдельный слой продукта, а не причина перегружать ядро записи.

## Проверки в этой среде

Python-источники проходят `compileall` и pytest. Запуск проверен локально без Docker: API на SQLite (aiosqlite), frontend через `npm run dev`.
