"""Supabase database client singleton."""

from supabase import create_client, Client
from app.config import settings

_supabase_client: Client | None = None


def get_supabase() -> Client:
    """Get or create the Supabase client instance."""
    global _supabase_client
    if _supabase_client is None:
        if not settings.supabase_url or not settings.supabase_key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY environment variables must be set. "
                "Add them to your Railway service or .env file."
            )
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_key,
        )
    return _supabase_client
