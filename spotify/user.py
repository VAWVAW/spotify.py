from .connection import Connection


class User:
    def __init__(self, id: str, connection: Connection, cache_dir: str = None, display_name: str = None):
        #TODO implement User
        pass

    def __dict__(self):
        return {"id": "asdf", "display_name": "asdf"}
