import bareutils.response_code as response_code


def test_response_code():
    assert response_code.is_information(response_code.CONTINUE)
    assert not response_code.is_information(response_code.OK)

    assert not response_code.is_successful(response_code.CONTINUE)
    assert response_code.is_successful(response_code.OK)
    assert not response_code.is_successful(response_code.MULTIPLE_CHOICE)

    assert not response_code.is_redirection(response_code.OK)
    assert response_code.is_redirection(response_code.MULTIPLE_CHOICE)
    assert not response_code.is_redirection(response_code.BAD_REQUEST)

    assert not response_code.is_client_error(response_code.MULTIPLE_CHOICE)
    assert response_code.is_client_error(response_code.BAD_REQUEST)
    assert not response_code.is_client_error(response_code.INTERNAL_SERVER_ERROR)

    assert not response_code.is_server_error(response_code.BAD_REQUEST)
    assert response_code.is_server_error(response_code.INTERNAL_SERVER_ERROR)
