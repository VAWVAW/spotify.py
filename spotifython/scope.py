class Scope:
    """
    A class to organise the scopes for the spotify api. Take a look at the `api documentation <https://developer.spotify.com/documentation/web-api/reference/>`_ for more information.
    """
    def __init__(
            self,
            user_read_playback_position: bool = False,
            user_read_email: bool = False,
            playlist_modify_private: bool = False,
            playlist_read_private: bool = False,
            user_library_modify: bool = False,
            playlist_read_collaborative: bool = False,
            user_follow_read: bool = False,
            user_read_playback_state: bool = False,
            user_read_currently_playing: bool = False,
            user_read_private: bool = False,
            playlist_modify_public: bool = False,
            playlist_read_public: bool = False,
            user_library_read: bool = False,
            user_top_read: bool = False,
            ugc_image_upload: bool = False,
            user_follow_modify: bool = False,
            user_modify_playback_state: bool = False,
            user_read_recently_played: bool = False
    ):
        self.user_read_playback_position = user_read_playback_position
        self.user_read_email = user_read_email
        self.playlist_modify_private = playlist_modify_private
        self.playlist_read_private = playlist_read_private
        self.user_library_modify = user_library_modify
        self.playlist_read_collaborative = playlist_read_collaborative
        self.user_follow_read = user_follow_read
        self.user_read_playback_state = user_read_playback_state
        self.user_read_currently_playing = user_read_currently_playing
        self.user_read_private = user_read_private
        self.playlist_modify_public = playlist_modify_public
        self.playlist_read_public = playlist_read_public
        self.user_library_read = user_library_read
        self.user_top_read = user_top_read
        self.ugc_image_upload = ugc_image_upload
        self.user_follow_modify = user_follow_modify
        self.user_modify_playback_state = user_modify_playback_state
        self.user_read_recently_played = user_read_recently_played

    def get_permissions(self) -> list[str]:
        permissions = []
        if self.user_read_playback_position:
            permissions.append("user-read-playback-position")
        if self.user_read_email:
            permissions.append("user-read-email")
        if self.playlist_modify_private:
            permissions.append("playlist-modify-private")
        if self.playlist_read_private:
            permissions.append("playlist-read-private")
        if self.user_library_modify:
            permissions.append("user-library-modify")
        if self.playlist_read_collaborative:
            permissions.append("playlist-read-collaborative")
        if self.user_follow_read:
            permissions.append("user-follow-read")
        if self.user_read_playback_state:
            permissions.append("user-read-playback-state")
        if self.user_read_currently_playing:
            permissions.append("user-read-currently-playing")
        if self.user_read_private:
            permissions.append("user-read-private")
        if self.playlist_modify_public:
            permissions.append("playlist-modify-public")
        if self.playlist_read_public:
            permissions.append("playlist-read-public")
        if self.user_library_read:
            permissions.append("user-library-read")
        if self.user_top_read:
            permissions.append("user-top-read")
        if self.ugc_image_upload:
            permissions.append("ugc-image-upload")
        if self.user_follow_modify:
            permissions.append("user-follow-modify")
        if self.user_modify_playback_state:
            permissions.append("user-modify-playback-state")
        if self.user_read_recently_played:
            permissions.append("user-read-recently-played")
        return permissions

    def __str__(self):
        permissions = sorted(self.get_permissions())
        return " ".join(permissions)

    @staticmethod
    def is_equal(scope_str1: str, scope_str2: str) -> bool:
        permissions1 = sorted(scope_str1.split(" "))
        permissions2 = sorted(scope_str2.split(" "))

        return permissions1 == permissions2

    @staticmethod
    def contains(scope_str1: str, scope_str2: str) -> bool:
        """
        checks if the second scope string is contained in the first one
        """
        permissions1 = sorted(scope_str1.split(" "))
        for permission in scope_str2.split(" "):
            if permission not in permissions1:
                return False
        return True
