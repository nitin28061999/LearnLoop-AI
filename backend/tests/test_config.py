from app.core.config import Settings


def test_settings_have_expected_defaults():
    settings = Settings(_env_file=None)

    assert settings.app_name == "LearnLoop AI"
    assert settings.app_version == "0.1.0"
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.environment == "development"
    assert settings.debug is True


def test_settings_can_read_environment_variables(monkeypatch):
    monkeypatch.setenv("APP_NAME", "LearnLoop Test")

    settings = Settings(_env_file=None)

    assert settings.app_name == "LearnLoop Test"


def test_supabase_settings_are_optional_by_default():
    settings = Settings(_env_file=None)

    assert settings.supabase_url is None
    assert settings.supabase_publishable_key is None
    assert settings.supabase_secret_key is None


def test_settings_can_read_supabase_environment_variables(monkeypatch):
    monkeypatch.setenv(
        "SUPABASE_URL",
        "https://example.supabase.co",
    )
    monkeypatch.setenv(
        "SUPABASE_PUBLISHABLE_KEY",
        "test-publishable-key",
    )
    monkeypatch.setenv(
        "SUPABASE_SECRET_KEY",
        "test-secret-key",
    )

    settings = Settings(_env_file=None)

    assert settings.supabase_url == "https://example.supabase.co"
    assert (
        settings.supabase_publishable_key.get_secret_value()  # pyright: ignore[reportOptionalMemberAccess]
        == "test-publishable-key"
    )
    assert (
        settings.supabase_secret_key.get_secret_value()  # pyright: ignore[reportOptionalMemberAccess]
        == "test-secret-key"
    )
