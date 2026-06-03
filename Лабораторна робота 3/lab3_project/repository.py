from typing import Generic, List, TypeVar, Optional

T = TypeVar("T")


class Repository(Generic[T]):
    def __init__(self, connection_string: str = "", table_name: str = "", timeout: int = 30, page_size: int = 50):
        self.connection_string = connection_string
        self.table_name = table_name
        self.timeout = timeout
        self.page_size = page_size
        self.is_connected = False
        self._storage: List[T] = []

    def _connect(self) -> None:
        self.is_connected = True

    def save(self, entity: T) -> bool:
        if not self.is_connected:
            self._connect()
        self._storage.append(entity)
        return True

    def find_by_id(self, id_value) -> Optional[T]:
        for entity in self._storage:
            if getattr(entity, "id", None) == id_value:
                return entity
        return None

    def find_all(self, filter_value: str = "") -> List[T]:
        if not filter_value:
            return list(self._storage)
        return [entity for entity in self._storage if filter_value in str(entity)]

    def update(self, entity: T) -> bool:
        found = self.find_by_id(getattr(entity, "id", None))
        if found is not None:
            index = self._storage.index(found)
            self._storage[index] = entity
            return True
        return False

    def delete(self, id_value) -> bool:
        entity = self.find_by_id(id_value)
        if entity is not None:
            self._storage.remove(entity)
            return True
        return False
