"""
Blacklist management utilities
"""
import json
from collections.abc import Iterator
from pathlib import Path
import logging

logger = logging.getLogger('discord')


class BlacklistManager:
    """Manages user blacklist with automatic file sync"""
    
    def __init__(self, blacklist_path: Path = Path("blacklist_users.json")):
        self._blacklist_path = blacklist_path
        self._blacklist_ids: list[int] = []
        self.load()
    
    def load(self) -> None:
        """Load blacklist from file"""
        logger.debug(f"Loading blacklist from {self._blacklist_path}")
        if not self._blacklist_path.exists():
            self._blacklist_ids = []
            self.save()
            return
        
        try:
            with open(self._blacklist_path, "r", encoding="utf-8") as f:
                self._blacklist_ids = json.load(f)['ids']
        except Exception as e:
            logger.error(f"Error loading blacklist: {e}")
            self._blacklist_ids = []
    
    def save(self) -> None:
        """Save blacklist to file"""
        logger.debug(f"Saving blacklist to {self._blacklist_path}")
        with open(self._blacklist_path, "w", encoding="utf-8") as f:
            to_save: dict[str, list[int]] = {'ids': self._blacklist_ids}
            json.dump(to_save, f, indent=4)
    
    def add_user(self, user_id: int) -> bool:
        """Add user to blacklist. Returns True if user was added, False if already blacklisted"""
        logger.debug(f"Adding user {user_id} to blacklist")
        if user_id not in self._blacklist_ids:
            self._blacklist_ids.append(user_id)
            self.save()
            return True
        return False
    
    def remove_user(self, user_id: int) -> bool:
        """Remove user from blacklist. Returns True if user was removed, False if not in blacklist"""
        logger.debug(f"Removing user {user_id} from blacklist")
        if user_id in self._blacklist_ids:
            self._blacklist_ids.remove(user_id)
            self.save()
            return True
        return False
    
    def is_blacklisted(self, user_id: int) -> bool:
        """Check if user is blacklisted"""
        return user_id in self._blacklist_ids
    
    @property
    def blacklist_ids(self) -> list[int]:
        """Get copy of blacklist IDs"""
        return self._blacklist_ids.copy()
    
    def clear(self) -> None:
        """Clear all blacklisted users"""
        logger.debug("Clearing blacklist")
        self._blacklist_ids.clear()
        self.save()
        
    def __iter__(self) -> Iterator[int]:
        """Iterate over blacklisted user IDs"""
        return iter(self._blacklist_ids)
