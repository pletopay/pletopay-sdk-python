"""Cursor pagination. Results are newest first; ``meta.next_cursor`` is ``None`` on the last page."""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from typing import Generic, TypeVar

from pletopay._response import ListMeta, ResponseInfo

T = TypeVar("T")


class SyncPage(Generic[T]):
    """One page of a list. Iterating the page yields its items; ``auto_paging_iter()`` walks every page."""

    def __init__(self, data: list[T], response: ResponseInfo, fetch_next: Callable[[str], SyncPage[T]]) -> None:
        self.data = data
        self.response = response
        self.meta: ListMeta = response.meta or ListMeta(has_more=False, next_cursor=None, url="")
        self._fetch_next = fetch_next

    @property
    def has_more(self) -> bool:
        return self.meta.has_more and self.meta.next_cursor is not None

    @property
    def next_cursor(self) -> str | None:
        return self.meta.next_cursor

    def __iter__(self) -> Iterator[T]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, index: int) -> T:
        return self.data[index]

    def __repr__(self) -> str:
        return f"SyncPage(data={self.data!r}, has_more={self.has_more}, next_cursor={self.next_cursor!r})"

    def next_page(self) -> SyncPage[T] | None:
        """The next page, or ``None`` on the last one."""
        if not self.has_more or self.meta.next_cursor is None:
            return None
        return self._fetch_next(self.meta.next_cursor)

    def pages(self) -> Iterator[SyncPage[T]]:
        page: SyncPage[T] | None = self
        while page is not None:
            yield page
            page = page.next_page()

    def auto_paging_iter(self) -> Iterator[T]:
        """Every item from this page on, fetching further pages as needed."""
        for page in self.pages():
            yield from page.data

    def auto_paging_list(self, *, limit: int | None = None) -> list[T]:
        """Collects items across pages, up to ``limit``. Pass a limit for large lists."""
        items: list[T] = []
        for item in self.auto_paging_iter():
            items.append(item)
            if limit is not None and len(items) >= limit:
                break
        return items


class AsyncPage(Generic[T]):
    """The async twin of :class:`SyncPage`: ``await page.next_page()``, ``async for item in page.auto_paging_iter()``."""

    def __init__(
        self, data: list[T], response: ResponseInfo, fetch_next: Callable[[str], Awaitable[AsyncPage[T]]]
    ) -> None:
        self.data = data
        self.response = response
        self.meta: ListMeta = response.meta or ListMeta(has_more=False, next_cursor=None, url="")
        self._fetch_next = fetch_next

    @property
    def has_more(self) -> bool:
        return self.meta.has_more and self.meta.next_cursor is not None

    @property
    def next_cursor(self) -> str | None:
        return self.meta.next_cursor

    def __iter__(self) -> Iterator[T]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, index: int) -> T:
        return self.data[index]

    def __repr__(self) -> str:
        return f"AsyncPage(data={self.data!r}, has_more={self.has_more}, next_cursor={self.next_cursor!r})"

    async def next_page(self) -> AsyncPage[T] | None:
        if not self.has_more or self.meta.next_cursor is None:
            return None
        return await self._fetch_next(self.meta.next_cursor)

    async def pages(self) -> AsyncIterator[AsyncPage[T]]:
        page: AsyncPage[T] | None = self
        while page is not None:
            yield page
            page = await page.next_page()

    async def auto_paging_iter(self) -> AsyncIterator[T]:
        async for page in self.pages():
            for item in page.data:
                yield item

    async def auto_paging_list(self, *, limit: int | None = None) -> list[T]:
        items: list[T] = []
        async for item in self.auto_paging_iter():
            items.append(item)
            if limit is not None and len(items) >= limit:
                break
        return items
