"""Cursor pagination. Results are newest first; ``meta.next_cursor`` is ``None`` on the last page.

A list started with ``ending_before`` is *backward*: it walks from that object towards newer ones. Each
page's ``data`` is still newest first, the next page is the one newer than this page's first item, and
``auto_paging_iter()`` yields oldest to newest so the order is the same across pages.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Iterator, Sequence
from typing import Any, Generic, TypeVar

from pletopay._response import ListMeta, ResponseInfo

T = TypeVar("T")


def _next_cursor(data: Sequence[Any], meta: ListMeta, backward: bool) -> str | None:
    """The cursor the next page continues from: ``meta.next_cursor`` (to pass as ``starting_after``), or on a
    backward list the id of the first item (to pass as ``ending_before``; ``meta.next_cursor`` means nothing
    in that direction)."""
    if not backward:
        return meta.next_cursor
    if not meta.has_more or not data:
        return None
    newest = data[0].get("id") if isinstance(data[0], dict) else getattr(data[0], "id", None)
    return newest if isinstance(newest, str) else None


class SyncPage(Generic[T]):
    """One page of a list. Iterating the page yields its items; ``auto_paging_iter()`` walks every page."""

    def __init__(
        self,
        data: list[T],
        response: ResponseInfo,
        fetch_next: Callable[[str], SyncPage[T]],
        *,
        backward: bool = False,
    ) -> None:
        self.data = data
        self.response = response
        self.meta: ListMeta = response.meta or ListMeta(has_more=False, next_cursor=None, url="")
        self._fetch_next = fetch_next
        self._backward = backward

    @property
    def has_more(self) -> bool:
        return self.meta.has_more and self.next_cursor is not None

    @property
    def next_cursor(self) -> str | None:
        """The cursor ``next_page()`` continues from, or ``None`` on the last page. Pass it as
        ``starting_after``, or as ``ending_before`` on a list that was started with ``ending_before``."""
        return _next_cursor(self.data, self.meta, self._backward)

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
        cursor = self.next_cursor
        if not self.has_more or cursor is None:
            return None
        return self._fetch_next(cursor)

    def pages(self) -> Iterator[SyncPage[T]]:
        page: SyncPage[T] | None = self
        while page is not None:
            yield page
            page = page.next_page()

    def auto_paging_iter(self) -> Iterator[T]:
        """Every item from this page on, fetching further pages as needed (oldest to newest on a list
        started with ``ending_before``, newest to oldest otherwise)."""
        for page in self.pages():
            yield from reversed(page.data) if self._backward else page.data

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
        self,
        data: list[T],
        response: ResponseInfo,
        fetch_next: Callable[[str], Awaitable[AsyncPage[T]]],
        *,
        backward: bool = False,
    ) -> None:
        self.data = data
        self.response = response
        self.meta: ListMeta = response.meta or ListMeta(has_more=False, next_cursor=None, url="")
        self._fetch_next = fetch_next
        self._backward = backward

    @property
    def has_more(self) -> bool:
        return self.meta.has_more and self.next_cursor is not None

    @property
    def next_cursor(self) -> str | None:
        return _next_cursor(self.data, self.meta, self._backward)

    def __iter__(self) -> Iterator[T]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, index: int) -> T:
        return self.data[index]

    def __repr__(self) -> str:
        return f"AsyncPage(data={self.data!r}, has_more={self.has_more}, next_cursor={self.next_cursor!r})"

    async def next_page(self) -> AsyncPage[T] | None:
        cursor = self.next_cursor
        if not self.has_more or cursor is None:
            return None
        return await self._fetch_next(cursor)

    async def pages(self) -> AsyncIterator[AsyncPage[T]]:
        page: AsyncPage[T] | None = self
        while page is not None:
            yield page
            page = await page.next_page()

    async def auto_paging_iter(self) -> AsyncIterator[T]:
        async for page in self.pages():
            for item in reversed(page.data) if self._backward else page.data:
                yield item

    async def auto_paging_list(self, *, limit: int | None = None) -> list[T]:
        items: list[T] = []
        async for item in self.auto_paging_iter():
            items.append(item)
            if limit is not None and len(items) >= limit:
                break
        return items
