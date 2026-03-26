from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import ceil
from typing import Deque, Generic, Iterable, TypeVar

T = TypeVar("T")


@dataclass
class PreEventBuffer(Generic[T]):
    fps: int
    seconds: float

    def __post_init__(self) -> None:
        if self.fps <= 0:
            raise ValueError("fps must be positive")
        if self.seconds <= 0:
            raise ValueError("seconds must be positive")
        self.max_frames = max(1, ceil(self.fps * self.seconds))
        self._items: Deque[T] = deque(maxlen=self.max_frames)

    def append(self, item: T) -> None:
        self._items.append(item)

    def extend(self, items: Iterable[T]) -> None:
        self._items.extend(items)

    def snapshot(self) -> list[T]:
        return list(self._items)

    def clear(self) -> None:
        self._items.clear()

    def __len__(self) -> int:
        return len(self._items)

    @property
    def is_full(self) -> bool:
        return len(self._items) == self.max_frames
