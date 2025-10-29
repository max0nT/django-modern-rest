from http import HTTPStatus
from typing import final

import pydantic_xml
from django.http import HttpResponse
from faker import Faker

from django_modern_rest import (
    Body,
    Controller,
)
from django_modern_rest.test import DMRRequestFactory
from tests.test_unit.test_plugins.test_pydantic_xml.serializer import (
    PydanticXmlSerializer,
)


@final
class _InputModel(pydantic_xml.BaseXmlModel, tag='input'):
    first_name: str = pydantic_xml.attr()
    last_name: str = pydantic_xml.attr()


@final
class _ReturnModel(pydantic_xml.BaseXmlModel, tag='output'):
    full_name: str


@final
class _ModelController(
    Controller[PydanticXmlSerializer],
    Body[_InputModel],
):
    def post(self) -> _ReturnModel:
        first_name = self.parsed_body.first_name
        last_name = self.parsed_body.last_name
        return _ReturnModel(full_name=f'{first_name} {last_name}')


def test_pydantic_xml_model_controller(
    dmr_rf: DMRRequestFactory,
    faker: Faker,
) -> None:
    """Ensures that regular parsing works."""
    request_data = {'first_name': faker.name(), 'last_name': faker.last_name()}
    request = dmr_rf.post(
        '/whatever/',
        data=(
            f'<input first_name="{request_data["first_name"]}"'
            f' last_name="{request_data["last_name"]}" />'
        ),
        content_type='application/xml',
    )

    response = _ModelController.as_view()(request)

    assert isinstance(response, HttpResponse)
    assert response.status_code == HTTPStatus.CREATED, response.content
    assert response.headers == {'Content-Type': 'application/xml'}

    expected_full_name = (
        f'{request_data["first_name"]} {request_data["last_name"]}'
    )
    assert (
        _ReturnModel.from_xml(response.content).full_name == expected_full_name
    )
