import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Set

# Handler classes.
# I know, I write Python like Rust. sry <3
class LobbyError(Exception):
    pass

class LobbyAlreadyExists(LobbyError):
    pass
class LobbyNotFound(LobbyError):
    pass
class LobbyClosed(LobbyError):
    pass
class LobbyFull(LobbyError):
    pass
class AlreadyJoined(LobbyError):
    pass
class NotInLobby(LobbyError):
    pass

# Define class for single lobby.
@dataclass
class Lobby:
    id: str
    channel_id: int
    host_id: int
    players: Set[int] = field(default_factory = set)
    status: str = "open"
    expires_at: int = 0
    message_id: Optional[int] = None

    @property
    def is_open(self) -> bool:
        return self.status == "open"

    @property
    def is_full(self) -> bool:
        return (len(self.players)) >= 5

# Define class for service.
# Sorta works like a factory I guess?
class ServiceCounterStrikeLobby:
    def __init__(self):
        # key = message_id
        self._lobbies: Dict[int, Lobby] = {}

    # Check if a channel has an open lobby.
    def has_open_lobby_in_channel(self, channel_id: int) -> bool:
        return any(
            lobby.channel_id == channel_id and lobby.status == "open"
            for lobby in self._lobbies.values()
        )

    # Constructor for Lobby type.
    # Creates a lobby in a given channel and starts signups.
    def create_lobby(self, channel_id: int, host_id: int, duration_mins: int = 30) -> Lobby:
        # Fail to create if lobby already exists in the given channel.
        if self.has_open_lobby_in_channel(channel_id):
            raise LobbyAlreadyExists("There is already an open signup in this channel.")

        # Create and return lobby object.
        # This is really awkward for now.
        # TODO: Manage time better here?
        now = int(time.time() * 1000)
        lobby = Lobby(
            id = f"{channel_id}-{now}",
            channel_id = channel_id,
            host_id = host_id,
            players = {host_id},
            status = "open",
            expires_at = now + duration_mins * 60 * 1000,
        )
        return lobby

    def create_lobby_with_expiry(self, channel_id: int, host_id: int, expires_at: int) -> Lobby:
        # Fail to create if lobby already exists in the given channel.
        if self.has_open_lobby_in_channel(channel_id):
            raise LobbyAlreadyExists("There is already an open signup in this channel.")

        now = int(time.time() * 1000)
        # Check lobby must end in the future.
        if expires_at <= now:
            raise LobbyError("The signup end time must be in the future.")

        lobby = Lobby(
            id = f"{channel_id}-{now}",
            channel_id = channel_id,
            host_id = host_id,
            players = {host_id},
            status = "open",
            expires_at = expires_at,
        )
        return lobby

    def attach_message(self, lobby: Lobby, message_id: int):
        lobby.message_id = message_id
        self._lobbies[message_id] = lobby

    def get_lobby_by_message(self, message_id: int) -> Lobby:
        lobby = self._lobbies.get(message_id)
        # Check if lobby exists to ensure users can not join stale lobbies.
        if not lobby:
            raise LobbyNotFound("This signup no longet exists.")
        return lobby

    def join_lobby(self, message_id: int, user_id: int) -> Lobby:
        # Get lobby user wants to join.
        lobby = self.get_lobby_by_message(message_id)

        # Basic safety checks.
        if not lobby.is_open:
            raise LobbyClosed("This signup is closed.")
        if user_id in lobby.players:
            raise AlreadyJoined("You have already joined this lobby.")
        if lobby.is_full:
            raise LobbyFull("This lobby is already full.")

        # Add player' ID to lobby.
        lobby.players.add(user_id)
        return lobby

    def leave_lobby(self, message_id: int, user_id: int) -> Lobby:
        lobby = self.get_lobby_by_message(message_id)

        if user_id not in lobby.players:
            raise NotInLobby("You are not in this lobby.")

        if not lobby.is_open:
            raise LobbyClosed("This signup has already closed.")

        lobby.players.remove(user_id)
        return lobby

    def close_lobby(self, message_id: int, reason: str) -> Lobby:
        lobby = self.get_lobby_by_message(message_id)

        # Check if lobby is open first.
        if not lobby.is_open:
            return lobby

        # Close lobby by setting status to the reason for the close.
        lobby.status = reason
        return lobby

    # Auto-expire/close function.
    def expire_lobby_if_needed(self, message_id: int) -> Optional[Lobby]:
        lobby = self._lobbies.get(message_id)
        if not lobby or not lobby.is_open:
            return None

        # Check if enough time has passed to expire the lobby.
        now = int(time.time() * 1000)
        if now < lobby.expires_at:
            return None
        lobby.status = "expired"
        return lobby

    def minutes_left(self, lobby: Lobby) -> int:
        time_left_ms = max(0, lobby.expires_at - int(time.time() * 1000))
        return max(0, (time_left_ms + 59999) // 60000)
