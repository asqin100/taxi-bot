# Claude Code Configuration for taxi-bot

## Project Overview

Taxi-bot - Telegram бот для таксистов в Москве. Помогает отслеживать коэффициенты спроса по зонам, получать AI-советы, управлять сменами и находить выгодные мероприятия.

## Tech Stack

- **Backend**: Python 3.11+, Aiogram 3.x, SQLAlchemy (async)
- **Database**: SQLite (dev), PostgreSQL (production ready)
- **Web**: Aiohttp (admin panel)
- **APIs**: Yandex Maps, KudaGo, OpenAI
- **Deployment**: Ubuntu 24.04, systemd

## Project Structure

```
taxi-bot/
├── bot/
│   ├── handlers/          # Telegram handlers (FSM states)
│   ├── services/          # Business logic
│   ├── models/            # SQLAlchemy models
│   ├── database/          # DB connection
│   ├── web/              # Admin panel (aiohttp)
│   └── main.py           # Entry point
├── webapp/               # Admin panel HTML/CSS/JS
├── data/                 # Database, venues.json
├── tests/               # Pytest tests
└── alembic/             # Database migrations
```

## Key Files

- `bot/main.py` - Bot initialization, scheduler setup
- `bot/config.py` - Environment configuration
- `bot/services/yandex_api.py` - Coefficient fetching
- `bot/services/event_parser.py` - KudaGo API integration
- `bot/services/event_notifier.py` - Event notifications (runs every minute)
- `webapp/admin_dashboard.html` - Admin panel UI
- `data/venues.json` - Venue to zone mappings (110+ venues)

## Development Workflow

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run bot
python -m bot.main

# Run tests
pytest tests/

# Database migrations
alembic upgrade head
```

### Deployment to Production

Server: `root@5.42.110.16`
Path: `/opt/taxibot`

```bash
# Deploy
cd /opt/taxibot && git pull origin main && sudo systemctl restart taxibot

# Check logs
sudo journalctl -u taxibot -f

# Database optimization (after adding indexes)
cd /opt/taxibot && sqlite3 data/bot.db < add_indexes.sql
```

## Important Patterns

### 1. Database Performance
- Always use indexes for frequently queried columns
- Use `joinedload()` to avoid N+1 queries
- Async sessions via `get_session()` context manager

### 2. Event System
- Events fetched from KudaGo API every 6 hours
- Notifications sent 20 minutes before event ends (paid users only)
- Venue mapping via `data/venues.json`

### 3. Admin Panel
- Cache-Control headers to prevent browser caching
- Use `addEventListener` instead of inline event handlers
- Template literals without escaped dollar signs

### 4. Error Handling
- Always log errors with context
- Graceful degradation for external APIs
- User-friendly error messages in Russian

## Code Style

- Russian comments and docstrings
- Type hints for function signatures
- Async/await for all I/O operations
- F-strings for string formatting
- Descriptive variable names in English

## Testing

- Unit tests for services
- Integration tests for handlers
- Load testing for 500+ concurrent users
- Manual QA for admin panel

## Performance Targets

- Response time P99: <100ms
- Support 500-1000 concurrent users
- Database queries: <50ms average
- Event notifications: <5s latency

## Security

- No sensitive data in logs
- Environment variables for secrets
- Input validation for all user data
- SQL injection prevention via SQLAlchemy
- XSS prevention in admin panel

## Monitoring

- Systemd service status
- Log aggregation via journalctl
- Manual health checks on admin panel
- Event notification delivery tracking

## Common Tasks

### Adding a new feature
1. Create handler in `bot/handlers/`
2. Add service logic in `bot/services/`
3. Update models if needed
4. Add tests
5. Update admin panel if UI needed

### Fixing a bug
1. Reproduce locally
2. Add test case
3. Fix code
4. Verify test passes
5. Deploy to production

### Database changes
1. Create Alembic migration
2. Test migration locally
3. Backup production DB
4. Run migration on production
5. Verify data integrity

## gstack Integration

This project uses gstack for specialized workflow modes. Available skills:

- `/plan-ceo-review` - Product thinking mode
- `/plan-eng-review` - Technical architecture mode
- `/review` - Paranoid code review mode
- `/ship` - Release automation
- `/retro` - Weekly retrospective
- `/document-release` - Documentation updates
- `/plan-design-review` - Design audit mode
- `/design-consultation` - Design system creation

**Note**: Browser-based skills (`/browse`, `/qa`, `/qa-only`) require the browse binary which has compilation issues on Windows. Use the non-browser skills listed above.

Custom taxi-bot skills:
- `/taxi-deploy` - Production deployment automation
- `/taxi-test` - Comprehensive testing suite

### Recommended Workflow

1. New feature → `/plan-eng-review` → implement → `/review` → `/ship`
2. Bug fix → reproduce → fix → `/review` → `/ship`
3. Admin panel changes → implement → `/qa` → `/ship`
4. Weekly → `/retro` for team analysis

## Notes

- Уведомления за 20 минут - только для платных пользователей (премиум-функция)
- База данных оптимизирована 14 индексами (см. `add_indexes.sql`)
- KudaGo API загружает реальные мероприятия автоматически
- Бот протестирован на 500 одновременных пользователей (100% success rate)
