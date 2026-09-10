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
- SQLite через aiosqlite;
- SQLAlchemy 2;
- Alembic;
- Pydantic 2;
- Redis + Celery (опционально: только для Telegram-напоминаний);
- aiogram;
- Telegram `initData` HMAC-проверка;
- JWT access tokens;
- модульный монолит: API-модули отделены по доменам, а бизнес-правила концентрируются на backend; при росте проекта service/repository-слои можно выделить без изменения публичного API;
- пересечение активных записей одного барбера блокируется на уровне backend;
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
├── deploy/
│   ├── nginx-barbersaas.conf
│   ├── barbersaas-api.service
│   ├── barbersaas-bot.service
│   └── env.production.example
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

## Деплой на сервер (Ubuntu, без Docker, SQLite)

Подойдёт VPS 1 vCPU / 1–2 GB RAM (Timeweb, Selectel, Beget, Hetzner и т.п.). Для Telegram Mini App нужен домен с HTTPS — Telegram открывает Mini App только по HTTPS.

### Шаг 1. Подготовка сервера

```bash
ssh root@SERVER_IP
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip nginx git certbot python3-certbot-nginx ufw sqlite3
# Node.js 24 (нужен только для сборки frontend):
curl -fsSL https://deb.nodesource.com/setup_24.x | bash -
apt install -y nodejs
```

### Шаг 2. Пользователь и код

```bash
adduser --system --group --home /opt/barbersaas --shell /bin/bash barbersaas
su - barbersaas
git clone <URL_твоего_репозитория> /opt/barbersaas
cd /opt/barbersaas
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
```

### Шаг 3. Production `.env`

```bash
cp deploy/env.production.example .env
nano .env   # заполни реальные значения
```

Обязательно заполни:

- `JWT_SECRET` — сгенерируй: `openssl rand -hex 32`;
- `TELEGRAM_BOT_TOKEN` и `TELEGRAM_BOT_USERNAME` — от бота из BotFather (в production API без токена не стартует);
- `TELEGRAM_WEBAPP_URL` и `CORS_ORIGINS` — твой домен `https://your-domain.example`;
- `ALLOW_DEV_AUTH=false` — обязательно, иначе dev-вход открыт всем.

### Шаг 4. Миграции базы

В production схема **не создаётся автоматически** — только Alembic:

```bash
cd /opt/barbersaas/backend
../.venv/bin/python -m alembic upgrade head
```

### Шаг 5. Сборка frontend

```bash
cd /opt/barbersaas/frontend
npm ci
VITE_API_URL=/api/v1 npm run build
sudo mkdir -p /var/www/barbersaas
sudo cp -r dist/* /var/www/barbersaas/
```

`VITE_API_URL=/api/v1` — фронт будет ходить на тот же домен, nginx проксирует `/api/` на backend.

### Шаг 6. systemd-сервисы (API и бот)

```bash
exit   # выходим обратно в root
cp /opt/barbersaas/deploy/barbersaas-api.service /etc/systemd/system/
cp /opt/barbersaas/deploy/barbersaas-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now barbersaas-api
systemctl enable --now barbersaas-bot   # опционально: только если нужен бот
systemctl status barbersaas-api --no-pager
```

### Шаг 7. nginx

```bash
cp /opt/barbersaas/deploy/nginx-barbersaas.conf /etc/nginx/sites-available/barbersaas
ln -sf /etc/nginx/sites-available/barbersaas /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
```

Если у nginx уже есть свой сайт — не удаляй `default`, а впиши свой `server_name` в конфиг.

### Шаг 8. HTTPS (certbot)

```bash
certbot --nginx -d your-domain.example
```

### Шаг 9. Firewall

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

Порт 8000 наружу не открываем: API доступен только через nginx с localhost.

### Шаг 10. Проверка

- `curl https://your-domain.example/health` → `{"status":"ok"}`;
- `curl https://your-domain.example/ready` → `{"status":"ready"}`;
- открой `https://your-domain.example` — Mini App;
- в BotFather укажи Mini App URL `https://your-domain.example`.

### Обновление версии

```bash
su - barbersaas
cd /opt/barbersaas
git pull
.venv/bin/pip install -r backend/requirements.txt
cd backend && ../.venv/bin/python -m alembic upgrade head
cd ../frontend && npm ci && VITE_API_URL=/api/v1 npm run build
sudo cp -r dist/* /var/www/barbersaas/
exit
systemctl restart barbersaas-api barbersaas-bot
```

### Бэкап базы (SQLite)

```bash
# в crontab root, раз в сутки:
sqlite3 /opt/barbersaas/backend/barbersaas.db ".backup '/var/backups/barbersaas-$(date +\%F).db'"
```

### Напоминания (опционально)

Telegram-напоминания требуют Redis + celery worker. Без них приложение работает полностью, кроме отправки напоминаний:

```bash
apt install -y redis-server && systemctl enable --now redis-server
cd /opt/barbersaas/backend
nohup ../.venv/bin/celery -A app.workers.celery_app.celery_app worker --loglevel=INFO &
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
- активные записи одного мастера не могут пересекаться (проверка на backend);
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
