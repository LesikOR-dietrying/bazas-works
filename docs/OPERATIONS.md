# Експлуатація, backup і відновлення

BAZA зберігає узгоджений стан у двох місцях: PostgreSQL (`postgres_data`) та
файловому сховищі (`file_storage`). Backup має містити обидві частини з одного
вікна обслуговування. `.env`, дампи та архіви storage містять чутливі дані й не
повинні потрапляти до Git.

## Backup

Створіть локальну папку `backup`, тимчасово зупиніть запис бізнес-даних і
виконайте з кореня проєкту:

```powershell
docker compose stop frontend backend
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > backup/baza.dump
docker compose run --rm --no-deps backend tar -C /data/storage -czf - . > backup/storage.tar.gz
docker compose up -d --wait
```

Перевірте, що обидва файли ненульового розміру, та зберігайте їх разом із
датою й копією версії застосунку. Регулярно перевіряйте restore на окремому
development stack; наявність архіву сама по собі не доводить відновлюваність.

## Restore

Restore замінює поточні дані. Спочатку зробіть актуальний backup, зупиніть
frontend/backend і відновіть БД та storage з одного комплекту. Для binary input
на Windows зручно виконати redirect через `cmd /c`:

```powershell
docker compose stop frontend backend
cmd /c "docker compose exec -T db pg_restore -U baza -d baza --clean --if-exists < backup\baza.dump"
cmd /c "docker compose run --rm --no-deps backend tar -C /data/storage -xzf - < backup\storage.tar.gz"
docker compose up -d --wait
```

Якщо у `.env` змінені `POSTGRES_USER` або `POSTGRES_DB`, підставте їх замість
`baza`. Після відновлення перевірте `docker compose ps`, `/api/health/ready`,
вхід, завантаження кількох вкладень і поточну Alembic revision.

## Файлове сховище

Backend генерує opaque імена, перевіряє containment шляху та розмір потоку.
Nginx і застосунок обмежують upload; metadata створюється лише після успішного
запису файла. Видалення спочатку фіксується в БД, тому збій фізичного видалення
може залишити orphan object, але не посилання на відсутній файл. Такі об’єкти
можна прибирати лише після порівняння з `attachments.storage_path`, із запасом
часу для незавершених upload-транзакцій та після backup.

## Development seed

Demo-дані не створюються автоматично. У development встановіть окремий
`SEED_PASSWORD` щонайменше з 12 символів і виконайте:

```powershell
docker compose exec backend python -m app.cli seed-demo
```

Команда idempotent, не змінює паролі наявних користувачів і відмовляється
працювати поза `APP_ENV=development`. Demo password не використовуйте у
production. Створюються логіни `demo-admin`, `demo-engineer` і `demo-employee`.
