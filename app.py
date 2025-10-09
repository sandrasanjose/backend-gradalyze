import logging
import os
from typing import Optional

from dotenv import load_dotenv

from app import create_app


def initialize_logging() -> None:
    """Configure application-wide logging.

    LOG_LEVEL can be overridden via environment (e.g., DEBUG, INFO, WARNING).
    """
    log_level_name: str = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_level: int = getattr(logging, log_level_name, logging.INFO)

    logging.basicConfig(
        level=log_level,
        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )

    # Align Werkzeug (Flask dev server) logger with our config
    logging.getLogger('werkzeug').setLevel(log_level)


def try_load_env() -> None:
    """Attempt to load .env without failing hard if encoding is off."""
    try:
        load_dotenv()
    except Exception as error:  # pragma: no cover - defensive
        logging.warning('Could not load .env file: %s', error)


def test_postgres_connection() -> None:
    """Try connecting to Supabase Postgres using DATABASE_URL.

    Expected format (with SSL):
    postgresql://postgres:YOUR-PASSWORD@HOST:5432/postgres?sslmode=require
    """
    if os.getenv('SKIP_DB_CHECK', 'false').lower() == 'true':
        logging.info('Skipping Postgres connectivity test because SKIP_DB_CHECK=true')
        return
    database_url: Optional[str] = os.getenv('DATABASE_URL')
    if not database_url:
        logging.info('DATABASE_URL not set; skipping Postgres connectivity test.')
        return

    try:
        import psycopg2  # type: ignore
        logging.info('Testing Postgres connectivity...')
        with psycopg2.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
                logging.info('Postgres connectivity OK. SELECT 1 -> %s', result)
    except Exception as error:  # pragma: no cover - relies on external service
        logging.exception('Postgres connectivity failed: %s', error)


def test_supabase_client() -> None:
    """Create Supabase client if config present and run a lightweight check.

    This is optional and will be skipped if SUPABASE_URL/ANON_KEY are not provided.
    """
    url: Optional[str] = os.getenv('SUPABASE_URL')
    key: Optional[str] = os.getenv('SUPABASE_ANON_KEY') or os.getenv('SUPABASE_KEY')
    if not url or not key:
        logging.info('SUPABASE_URL/ANON_KEY not set; skipping Supabase client check.')
        return

    try:
        from supabase import create_client  # type: ignore

        logging.info('Initializing Supabase client...')
        client = create_client(url, key)

        # Perform a quick metadata call by selecting zero rows to validate auth
        # Note: This assumes a public table named "users" exists; if it does not, we only
        # validate client initialization without executing a query.
        try:
            client.table('users').select('id').limit(1).execute()
            logging.info('Supabase client OK. Test query executed on table "users" (limit 1).')
        except Exception:
            logging.info('Supabase client initialized. Skipping test query (table may not exist).')
    except Exception as error:  # pragma: no cover - relies on external service
        logging.exception('Supabase client initialization failed: %s', error)


def main() -> None:
    initialize_logging()
    try_load_env()
    test_postgres_connection()
    test_supabase_client()

    app = create_app()
    debug_enabled = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(debug=debug_enabled, host='0.0.0.0', port=5000)
if __name__ == '__main__':
    main()
