"""Base class of every generated model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, PrivateAttr

if TYPE_CHECKING:
    from pletopay._response import ResponseInfo


class PletopayModel(BaseModel):
    """A resource returned by the API.

    Unknown fields are kept (``extra='allow'``) so new API fields never break parsing; read them with
    ``model_extra``. ``last_response`` carries the request id and rate-limit headers of the call that
    returned this object.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True, validate_assignment=False)

    _last_response: ResponseInfo | None = PrivateAttr(default=None)

    @property
    def last_response(self) -> ResponseInfo | None:
        """Metadata of the HTTP response this object came from, or ``None`` if it was built locally."""
        return self._last_response

    def __getitem__(self, key: str) -> Any:
        """Dict-style access, including to fields this SDK version does not know."""
        if key in type(self).model_fields:
            return getattr(self, key)
        extra = self.model_extra or {}
        if key in extra:
            return extra[key]
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default
