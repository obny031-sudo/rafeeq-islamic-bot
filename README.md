# Rafeeq - Islamic Telegram Super App v2.0

A highly scalable, enterprise-grade Islamic platform built inside Telegram using a plugin-based architecture. Features prayer times, Quran reading, memorization tracking, Adhkar, and much more.

## 🏗️ Enterprise Plugin Architecture

Rafeeq uses a modular plugin-based architecture that allows for easy extension and maintenance. Each feature is implemented as a self-contained plugin with its own routers, services, models, and handlers.

```
Rafeeq/
├── bot/                          # Core bot infrastructure
│   ├── core/                    # Base classes and middleware
│   │   ├── base_plugin.py       # Abstract plugin interface
│   │   ├── plugin_manager.py    # Plugin lifecycle management
│   │   └── rbac.py             # Role-Based Access Control
│   ├── plugins/                 # Modular feature plugins
│   │   ├── prayer/             # Prayer times plugin
│   │   ├── quran/              # Quran reading plugin
│   │   └── adhkar/             # Adhkar supplications plugin
│   └── main.py                 # Bot entry point
├── config/                      # Hierarchical Pydantic configuration
│   ├── base.py                 # Base configuration classes
│   ├── prayer.py               # Prayer module settings
│   ├── quran.py                # Quran module settings
│   ├── adhkar.py               # Adhkar module settings
│   └── settings.py            # Main settings aggregator
├── repositories/                # Data access layer (Repository Pattern)
│   ├── base.py                 # Generic repository base class
│   ├── user_repository.py      # User-specific operations
│   └── metrics_repository.py   # Metrics and analytics operations
├── cache/                       # Redis abstraction layer
│   ├── base.py                 # Cache backend interface
│   └── decorator.py            # Caching decorators for API calls
├── services/                    # Domain-specific services
│   ├── prayer_service.py       # Prayer API integration
│   └── scheduler_service.py    # Task scheduling service
├── models/                      # Database models
│   ├── base.py                 # SQLAlchemy base
│   ├── user.py                 # User model with RBAC
│   └── metrics.py              # Metrics and achievements
├── utils/                       # Utility functions
│   ├── logger.py               # Structured logging system
│   ├── database.py             # Database session management
│   └── redis_client.py         # Redis client for FSM
├── middleware/                  # Custom middleware
│   └── error_handler.py        # Global error handling
├── keyboards/                   # Inline keyboard layouts
│   └── main_menu.py            # Main menu keyboards
├── handlers/                    # Core handlers (non-plugin)
│   └── start.py                # /start command
├── logs/                        # Structured log files
│   ├── app.log                 # Application logs
│   ├── error.log               # Error logs
│   ├── api.log                 # API call logs
│   └── scheduler.log           # Scheduler logs
├── assets/                      # Static assets
├── tests/                       # Unit and integration tests
├── requirements.txt             # Python dependencies
├── .env.example                # Environment variables template
└── README.md                   # This file
```

## 🎯 Architecture Layers

### 1. Handler Layer (Input/Output)
- Processes Telegram updates and user interactions
- Uses Aiogram routers for message and callback handling
- Implements user interface logic

### 2. Service Layer (Business Logic)
- Contains domain-specific business logic
- Integrates with external APIs (Aladhan, Quran API)
- Implements caching strategies

### 3. Repository Layer (Data Access)
- Abstracts database operations using Repository Pattern
- Provides async CRUD operations
- Includes metrics collection and analytics

### 4. Cache Layer (Redis-First)
- Redis abstraction for all external API calls
- Decorator-based caching with TTL support
- Automatic cache invalidation

## 🚀 Core Features

### Plugin System
- **Modular Architecture**: Each feature is a self-contained plugin
- **Hot-Loading**: Plugins can be enabled/disabled at runtime
- **Lifecycle Management**: Automatic initialization and shutdown
- **Dependency Injection**: Plugins receive bot instance on init

### Configuration System
- **Pydantic-Based**: Type-safe hierarchical configuration
- **Environment Variables**: All settings configurable via .env
- **Module-Specific**: Separate configs for each plugin
- **Validation**: Automatic validation on startup

### Caching Layer
- **Redis-First**: All API calls cached in Redis
- **Decorator-Based**: Easy caching with `@cached` decorator
- **TTL Support**: Configurable time-to-live for cached data
- **Cache Invalidation**: Automatic invalidation on updates

### Repository Layer
- **Async Operations**: All database operations are async
- **Generic Base**: Reusable base repository class
- **Metrics Collection**: Built-in usage tracking
- **Type Safety**: Full type hints for all operations

### RBAC System
- **Role Hierarchy**: User < Premium < Admin < Super Admin
- **Middleware Integration**: Automatic role injection
- **Decorator-Based**: Easy permission checking
- **Permission Helpers**: Utility functions for role checks

### Structured Logging
- **Separate Log Files**: app.log, error.log, api.log, scheduler.log
- **Log Rotation**: Automatic rotation with size limits
- **Structured Format**: Consistent log format across all modules
- **Performance**: Async logging for minimal overhead

### Metrics & Analytics
- **User Metrics**: Track messages, Quran reading, prayers, Adhkar
- **Module Usage**: Track which features are used most
- **Achievements**: Gamification with XP and levels
- **Analytics Ready**: Repository layer for analytics queries

## 🔧 Installation

### 1. Prerequisites
- Python 3.10 or higher
- PostgreSQL 14 or higher
- Redis 7 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))

### 2. Clone and Setup
```bash
cd d:/Rafeeq
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Database Setup
```sql
CREATE DATABASE rafeeq;
```

### 4. Configure Environment
```bash
copy .env.example .env
```

Edit `.env` with your credentials:
```env
BOT_TOKEN=your_telegram_bot_token_here
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/rafeeq
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your_openai_api_key_here
LOG_LEVEL=INFO
LOG_DIR=logs
```

### 5. Start Services
```bash
# Start Redis
redis-server

# Start PostgreSQL (if not running)
# Start the bot
python bot/main.py
```

## 🎮 Usage

### Adding a New Plugin

1. Create plugin directory in `bot/plugins/your_plugin/`
2. Implement plugin class inheriting from `BasePlugin`
3. Register plugin in `bot/main.py`

```python
from bot.core.base_plugin import BasePlugin
from aiogram import Router, Bot

class YourPlugin(BasePlugin):
    name = "your_plugin"
    version = "1.0.0"
    description = "Your plugin description"
    
    def __init__(self):
        super().__init__()
        self.router = Router()
        self._setup_handlers()
    
    def _setup_handlers(self):
        # Define your handlers here
        pass
    
    async def initialize(self, bot: Bot):
        # Initialize plugin resources
        pass
    
    async def shutdown(self):
        # Cleanup plugin resources
        pass
    
    def get_router(self) -> Router:
        return self.router
```

### Using Caching

```python
from cache import cached, CacheKeyBuilder

@cached(cache=redis_cache, ttl=3600)
async def get_data(param):
    # This will be cached for 1 hour
    return await api_call(param)
```

### Using Repositories

```python
from repositories import UserRepository

async def handler(message, db):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    
    if not user:
        user = await user_repo.create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username
        )
```

### RBAC Usage

```python
from bot.core import require_role, Role

@require_role(Role.ADMIN, Role.SUPER_ADMIN)
async def admin_handler(message, user_role: Role):
    # Only accessible by admins
    pass
```

## 🗄️ Database Schema

### User Model
- **id**: Telegram User ID (Primary Key)
- **username**: Telegram username
- **first_name/last_name**: User's name
- **role**: User role (USER, PREMIUM, ADMIN, SUPER_ADMIN)
- **latitude/longitude**: Location for prayer times
- **language**: Preferred language (en/ar)
- **streak_days**: Consecutive days of activity
- **last_read_surah/ayah**: Quran reading position
- **prayer_method/asr_method**: Prayer calculation settings
- **created_at/updated_at**: Timestamps

### Metrics Models
- **UserMetrics**: User-specific metrics (messages, Quran read, prayers, XP)
- **ModuleUsage**: Module usage tracking
- **Achievement**: Achievement definitions
- **UserAchievement**: User achievement progress

## 🔮 Current Plugins

### Prayer Plugin
- Location-based prayer times via Aladhan API
- Multiple calculation methods (ISNA, MWL, Makkah, etc.)
- Cached API responses for performance
- Location management

### Quran Plugin
- Quran reading with pagination
- API integration with alquran.cloud
- Save last reading position
- Resume reading functionality

### Adhkar Plugin
- Morning/Evening/General Adhkar
- Random Adhkar selection
- Daily reminder scheduling
- Arabic text with transliteration and translation

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Aiogram 3.x
- **Database**: PostgreSQL 14+ with SQLAlchemy 2.0 (async)
- **Cache**: Redis 7+ with multiple databases
- **Configuration**: Pydantic Settings
- **Logging**: Structured logging with rotation
- **APIs**: Aladhan API, Quran API
- **Task Scheduling**: APScheduler with Redis job store
- **HTTP Client**: httpx (async)

## 📝 Development Guidelines

### Code Style
- Follow PEP 8 guidelines
- Use type hints for all functions
- Add docstrings for all classes and methods
- Use async/await for all I/O operations
- Log using structured logger, not print

### Layer Separation
- Handlers should only handle I/O
- Services contain business logic
- Repositories handle data access
- Cache layer for external API calls

### Testing
- Write unit tests for repositories
- Write integration tests for services
- Test plugin lifecycle
- Mock external API calls

## 🐛 Troubleshooting

### Plugin Not Loading
Check plugin logs in `logs/app.log` for initialization errors.

### Cache Issues
Clear Redis cache: `redis-cli FLUSHDB`

### Database Migration
The bot automatically creates tables on startup. For schema changes, use Alembic.

## 📄 License

This project is open source and available for educational purposes.

## 🤝 Contributing

Contributions are welcome! Please follow the existing architecture patterns and code style.

---

**Built with ❤️ for the Muslim Ummah - Enterprise Plugin Architecture v2.0**
