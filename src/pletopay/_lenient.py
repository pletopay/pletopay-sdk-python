"""Lenient model construction for responses that do not match this SDK's schema.

When the API adds or changes something this version does not describe, parsing must not break a
merchant's process. ``construct_lenient`` builds the model without validation, still turning nested
objects into their model classes where the annotation says so, so attribute access keeps working.
"""

from __future__ import annotations

import types
import typing
from typing import Any, TypeVar, cast

from pletopay.types._base import PletopayModel

M = TypeVar("M", bound=PletopayModel)


def _model_in(annotation: Any) -> type[PletopayModel] | None:
    """The PletopayModel class named by an annotation such as ``Payment``, ``Payment | None`` or ``Annotated[Payment, …]``."""
    origin = typing.get_origin(annotation)
    if origin is typing.Annotated:
        return _model_in(typing.get_args(annotation)[0])
    if origin in (typing.Union, types.UnionType):
        for arg in typing.get_args(annotation):
            found = _model_in(arg)
            if found is not None:
                return found
        return None
    if isinstance(annotation, type) and issubclass(annotation, PletopayModel):
        return annotation
    return None


def _list_model_in(annotation: Any) -> type[PletopayModel] | None:
    origin = typing.get_origin(annotation)
    if origin is typing.Annotated:
        return _list_model_in(typing.get_args(annotation)[0])
    if origin in (typing.Union, types.UnionType):
        for arg in typing.get_args(annotation):
            found = _list_model_in(arg)
            if found is not None:
                return found
        return None
    if origin is list:
        return _model_in(typing.get_args(annotation)[0])
    return None


def construct_lenient(model: type[M], data: dict[str, Any]) -> M:
    values: dict[str, Any] = {}
    for name, value in data.items():
        field = model.model_fields.get(name)
        if field is not None and isinstance(value, dict):
            nested = _model_in(field.annotation)
            if nested is not None:
                value = construct_lenient(nested, value)
        elif field is not None and isinstance(value, list):
            item_model = _list_model_in(field.annotation)
            if item_model is not None:
                value = [construct_lenient(item_model, v) if isinstance(v, dict) else v for v in value]
        values[name] = value
    return cast(M, model.model_construct(**values))
