import functools
from typing import TYPE_CHECKING, Any, ClassVar, TypedDict, override

import pydantic
import pydantic_core
import pydantic_xml

from django_modern_rest.exceptions import ResponseSerializationError
from django_modern_rest.plugins.pydantic import PydanticSerializer

from .raw import deserialize, serialize

if TYPE_CHECKING:
    from . import FromXml


class ToXmlTreeKwargs(TypedDict):
    """Kwargs for model xml dump."""

    skip_empty: bool
    exclude_none: bool
    exclude_unset: bool


class ErrorDetail(pydantic_xml.BaseXmlModel):
    """Base schema for pydantic xml error detail."""

    type: str = pydantic_xml.element()
    loc: list[int | str] = pydantic_xml.element()
    msg: str = pydantic_xml.element()


class PydanticXmlErrorModel(pydantic_xml.BaseXmlModel, tag='Errors'):
    """Error response schema for serialization errors."""

    detail: list[ErrorDetail]


class PydanticXmlSerializer(PydanticSerializer):
    """
    Serialize and deserialize objects on xml format using pydantic-xml.

    Pydantic-xml support is optional.
    To install it run:

    .. code:: bash

        pip install 'django-modern-rest[pydantic-xml]'

    """

    __slots__ = ()

    # Required API:
    validation_error: ClassVar[type[Exception]] = pydantic.ValidationError
    response_parsing_error_model: ClassVar[Any] = PydanticXmlErrorModel
    content_type: ClassVar[str] = 'application/xml'

    format_type: str = 'xml'

    to_xml_tree_kwargs: ClassVar[ToXmlTreeKwargs] = {
        'skip_empty': False,
        'exclude_none': False,
        'exclude_unset': False,
    }

    @override
    @classmethod
    def serialize_hook(cls, to_serialize: Any) -> Any:
        """Customize how some objects are serialized into json."""
        if isinstance(to_serialize, pydantic_xml.BaseXmlModel):
            return to_serialize.to_xml_tree(**cls.to_xml_tree_kwargs)
        return super().serialize_hook(to_serialize)

    @override
    @classmethod
    def serialize(cls, structure: Any) -> bytes:
        """Convert any object to json bytestring."""
        try:
            return serialize(
                structure,
                cls.serialize_hook,
            )
        except pydantic_core.PydanticSerializationError as exc:
            raise ResponseSerializationError(str(exc)) from None

    @override
    @classmethod
    def deserialize_hook(
        cls,
        target_type: type[Any],
        to_deserialize: Any,
    ) -> Any:
        """
        Convert raw xml tree to validated model.

        There isn't double validation since `model_validate` in `from_python`
        doesn't allow to make validation again if data type is corresponded by
        model type.

        """
        if isinstance(target_type, type(pydantic_xml.BaseXmlModel)):
            return target_type.from_xml_tree(to_deserialize)
        return super().deserialize_hook(target_type, to_deserialize)

    @override
    @classmethod
    def deserialize(
        cls,
        buffer: 'FromXml',
        target_type: type[Any],
    ) -> Any:
        """Convert string or bytestring to simple xml tree."""
        return deserialize(
            buffer,
            functools.partial(
                cls.deserialize_hook,
                target_type,
            ),
        )
