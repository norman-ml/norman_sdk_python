import pytest

@pytest.mark.usefixtures("authentication_manager")
class TestModelInvoke:
    @pytest.mark.invocations
    def test_create_invocation(self):
        pass

    @pytest.mark.invocations
    def test_upload_invocation_configuration(self):
        pass
