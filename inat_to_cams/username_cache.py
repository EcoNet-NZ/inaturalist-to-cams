#  ====================================================================
#  Copyright 2023 EcoNet.NZ
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#  ====================================================================

import logging
import sqlite3
import os
import pyinaturalist
from retry import retry


class UsernameCache:
    """Cache for iNaturalist usernames to reduce API calls"""
    
    def __init__(self, cache_file='inat_username_cache.sqlite'):
        self.cache_file = cache_file
        self._init_cache()
    
    def _init_cache(self):
        """Initialize the SQLite cache database"""
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS username_cache (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def get_username(self, user_id):
        """Get username from cache or fetch from API if not cached"""
        if not user_id:
            return None
            
        # Try to get from cache first
        cached_username = self._get_from_cache(user_id)
        if cached_username:
            logging.debug(f"Using cached username for user_id {user_id}: {cached_username}")
            return cached_username
        
        # Fetch from API and cache
        username = self._fetch_username_from_api(user_id)
        if username:
            self._store_in_cache(user_id, username)
            logging.info(f"Cached new username for user_id {user_id}: {username}")
        
        return username
    
    def _get_from_cache(self, user_id):
        """Retrieve username from cache"""
        try:
            conn = sqlite3.connect(self.cache_file)
            cursor = conn.cursor()
            cursor.execute('SELECT username FROM username_cache WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception as e:
            logging.warning(f"Error reading from username cache: {e}")
            return None
    
    def _store_in_cache(self, user_id, username):
        """Store username in cache"""
        try:
            conn = sqlite3.connect(self.cache_file)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO username_cache (user_id, username, cached_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, username))
            conn.commit()
            conn.close()
        except Exception as e:
            logging.warning(f"Error storing username in cache: {e}")
    
    @retry(delay=5, tries=3)
    def _fetch_username_from_api(self, user_id):
        """Fetch username from iNaturalist API"""
        try:
            client = pyinaturalist.iNatClient()
            user = client.users(user_id)
            if user and hasattr(user, 'login'):
                return user.login
            elif user and hasattr(user, 'name'):
                return user.name
        except Exception as e:
            logging.warning(f"Could not fetch username for user_id {user_id}: {e}")
        
        return f"user_{user_id}"  # Fallback to user_id if username fetch fails
    
    def clear_cache(self):
        """Clear all cached usernames"""
        try:
            conn = sqlite3.connect(self.cache_file)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM username_cache')
            conn.commit()
            conn.close()
            logging.info("Username cache cleared")
        except Exception as e:
            logging.error(f"Error clearing username cache: {e}")
    
    def get_cache_stats(self):
        """Get statistics about the cache"""
        try:
            conn = sqlite3.connect(self.cache_file)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM username_cache')
            count = cursor.fetchone()[0]
            conn.close()
            return {'cached_usernames': count}
        except Exception as e:
            logging.error(f"Error getting cache stats: {e}")
            return {'cached_usernames': 0}


# Global cache instance
_username_cache = None

def get_username_cache():
    """Get the global username cache instance"""
    global _username_cache
    if _username_cache is None:
        _username_cache = UsernameCache()
    return _username_cache
