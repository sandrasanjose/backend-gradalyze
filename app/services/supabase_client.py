"""
Supabase client configuration and utilities
"""

import os
from supabase import create_client, Client
from typing import Optional

def get_supabase_client() -> Client:
    """Get configured Supabase client"""
    url = os.getenv('SUPABASE_URL')
    # Prefer service role key on the server to avoid RLS issues; fall back to anon key
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or ANON) must be set")
    
    return create_client(url, key)

def create_supabase_client() -> Client:
    """Create Supabase client (alias for get_supabase_client)"""
    return get_supabase_client()
