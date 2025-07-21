"""
Blacklist management utilities
"""
import json
from pathlib import Path


class BlacklistManager:
    """Manages user blacklist with automatic file sync"""
    
    def __init__(self, blacklist_path: Path = Path("blacklist_users.json")):
        self.blacklist_path = blacklist_path
        self._blacklist_ids: list[int] = []
        self.load()
    
    def load(self) -> None:
        """Load blacklist from file"""
        if not self.blacklist_path.exists():
            self._blacklist_ids = []
            self.save()
            return
        
        try:
            with open(self.blacklist_path, "r", encoding="utf-8") as f:
                self._blacklist_ids = json.load(f)
        except Exception as e:
            print(f"Error loading blacklist: {e}")
            self._blacklist_ids = []
    
    def save(self) -> None:
        """Save blacklist to file"""
        with open(self.blacklist_path, "w", encoding="utf-8") as f:
            json.dump(self._blacklist_ids, f, indent=4)
    
    def add_user(self, user_id: int) -> bool:
        """Add user to blacklist. Returns True if user was added, False if already blacklisted"""
        if user_id not in self._blacklist_ids:
            self._blacklist_ids.append(user_id)
            self.save()
            return True
        return False
    
    def remove_user(self, user_id: int) -> bool:
        """Remove user from blacklist. Returns True if user was removed, False if not in blacklist"""
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
        self._blacklist_ids.clear()
        self.save()
