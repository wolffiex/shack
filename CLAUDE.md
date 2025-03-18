# SHACK Project Guidelines

## Commands
- Run server: `python manage.py runserver`
- Run tests: `python manage.py test`
- Run specific test module: `python manage.py test pushbyt.test.test_generate`
- Run specific test class: `python manage.py test pushbyt.test.test_generate.GenerationTestCase`
- Run specific test method: `python manage.py test pushbyt.test.test_generate.GenerationTestCase.test_get_segment_start_no_animations`
- Lint code: `ruff check .`
- Fix lint issues: `ruff check --fix .`
- Format code: `ruff format`
- Clear animation data: `python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('DELETE FROM pushbyt_animation'); print('Animations cleared')"`

Note: This project does not use mypy for type checking despite having type annotations in the code.

## Style Guide
- Type annotations: Use typing for function parameters and return values
- Imports: Group standard library, then Django, then third-party, then local imports
- Naming: Snake case for variables/functions, PascalCase for classes
- Error handling: Use try/except blocks with specific exceptions
- Exception handling: Log exceptions but don't crash (especially for IntegrityError)
- Models: Define full_clean/clean methods for validation
- Async: Use httpx for HTTP requests, asyncio.gather() for concurrency
- Dictionary merge: Use | operator for dict merging
- String formatting: Use f-strings
- Logging: Use module-level logger from logging package
- Timing: Keep timing values consistent across the system (12-second intervals)
- Documentation: Add detailed docstrings for complex algorithms

## Project Structure
- Django project with two main apps: pushbyt and ha
- PostgreSQL database backend
- Rich console logging
- Test structure: Tests live in app/test/ directories rather than app/tests/

## Animation Timing System
- Animation duration: 15 seconds 
- Animation timing: Aligned to 12-second intervals (0, 12, 24, 36, 48 seconds)
- Frame rate: 10 frames per second (FRAME_TIME = 100ms)
- Pre-generation: Animations created in 90-second batches
- Generation optimization: System checks for sufficient future coverage before creating new animations
- Prioritization hierarchy:
  1. Doorbell animations (highest priority)
  2. Unserved real-time content (hasn't been shown yet, no scheduled start time)
  3. Upcoming unserved timed animations (sorted by earliest start time)
  4. Most recently served animations (for continuity of viewing experience)
- Main endpoints: 
  - `/pushbyt/v1/preview.webp` - Serves animations to Tidbyt device
  - `/pushbyt/command/generate` - Creates new animations
- Animation sources: STATIC, RAYS, SPOTIFY, TIMER, DOORBELL, RADAR
- Device behavior: Tidbyt device polls approximately every 12 seconds

## Simulator
- URL path: `/pushbyt/simulator`
- Mimics actual Tidbyt device behavior by requesting `/pushbyt/v1/preview.webp`
- Automatically refreshes content every 15 seconds (actual device polls every ~12 seconds)
- Triggers generate endpoint every 60 seconds to create new animations
- Displays WebP animations at 64x32 resolution, scaled up
- Supports custom animation paths via text input for testing
- Uses cache busting with timestamp query parameters for fresh content
- Developer workflow: Make changes → View in simulator → Deploy to device
- Production debugging: Check logs for animation selection and generation patterns

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