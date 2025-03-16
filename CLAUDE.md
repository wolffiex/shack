# SHACK Project Guidelines

## Commands
- Run server: `python manage.py runserver`
- Run tests: `python manage.py test`
- Run specific test: `python manage.py test ha.tests.TestClass.test_method`
- Type check: `mypy .`  
- Lint code: `ruff check .`
- Fix lint issues: `ruff check --fix .`

## Style Guide
- Type annotations: Use typing for function parameters and return values
- Imports: Group standard library, then Django, then third-party, then local imports
- Naming: Snake case for variables/functions, PascalCase for classes
- Error handling: Use try/except blocks with specific exceptions
- Models: Define full_clean/clean methods for validation
- Async: Use httpx for HTTP requests, asyncio.gather() for concurrency
- Dictionary merge: Use | operator for dict merging
- String formatting: Use f-strings
- Logging: Use module-level logger from logging package

## Project Structure
- Django project with two main apps: pushbyt and ha
- PostgreSQL database backend
- Rich console logging

## Animation Timing System
- Animation duration: 15 seconds (aligned to 0, 15, 30, 45 seconds intervals)
- Frame rate: 10 frames per second (FRAME_TIME = 100ms)
- Pre-generation: Animations created in 90-second batches
- Prioritization: Doorbell > Important > Ephemeral > Earliest start time > Timers > Clocks
- Main endpoints: 
  - `/pushbyt/v1/preview.webp` - Serves animations to Tidbyt device
  - `/pushbyt/command/generate` - Creates new animations
- Animation sources: STATIC, RAYS, SPOTIFY, TIMER, DOORBELL, RADAR

## Simulator
- URL path: `/pushbyt/simulator`
- Mimics actual Tidbyt device behavior by requesting `/pushbyt/v1/preview.webp`
- Automatically refreshes content every 15 seconds
- Triggers generate endpoint every 60 seconds to create new animations
- Displays WebP animations at 64x32 resolution, scaled up
- Supports custom animation paths via text input for testing
- Uses cache busting with timestamp query parameters for fresh content
- Developer workflow: Make changes → View in simulator → Deploy to device

## Home Assistant Integration
- Interaction with Home Assistant via REST API (`ha_api_url = f"http://{HA_HOST}:8123/api"`)
- Authentication via bearer token stored in environment variable `HA_ACCESS_TOKEN`
- Dashboard shows device states (Tidbyt switch, heater switch, temperature, etc.)
- Uses async HTTP requests with httpx for better performance
- Controls entities via services endpoints (/services/switch, /services/script)
- Key endpoints:
  - `/ha/dashboard` - Main dashboard UI for monitoring devices
  - `/ha/control/<name>` - Control Home Assistant entities (switches, scripts)
- Monitors environmental data from PostgreSQL database (co2, temperature, humidity, motion)
- Timer functionality synchronized with animations via `pushbyt.animation.timer`