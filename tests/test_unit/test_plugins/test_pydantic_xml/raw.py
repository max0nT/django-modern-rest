import xml.etree.ElementTree as ET  # noqa: S405
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from django_modern_rest.exceptions import DataParsingError

if TYPE_CHECKING:
    from . import FromXml


def serialize(
    to_serialize: Any,
    serializer: Callable[[Any], Any] | None = None,
) -> bytes:
    """Convert data to raw xml format."""
    try:
        if serializer:
            to_serialize = serializer(to_serialize)
        return ET.tostring(to_serialize)
    except (TypeError, ValueError, ET.ParseError) as exc:
        raise DataParsingError(str(exc)) from exc


def deserialize(
    to_deserialize: 'FromXml',
    deserializer: Callable[[Any], Any] | None = None,
) -> Any:
    """Convert raw data to xml format."""
    try:
        return ET.fromstring(to_deserialize)  # noqa: S314
    except (TypeError, ValueError, ET.ParseError) as exc:
        raise DataParsingError(str(exc)) from exc
