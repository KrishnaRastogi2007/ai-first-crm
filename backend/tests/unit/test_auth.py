from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.modules.auth.service import UserService, get_device_name
from app.modules.auth.schemas import UserRole


# ----------------------------------------
# Device detection tests
# ----------------------------------------

def test_get_device_name_with_unknown_user_agent():
    result = get_device_name("CustomUnknownAgent/1.0")

    assert result == "Unknown Browser on Unknown OS"


def test_get_device_name_without_user_agent():
    result = get_device_name(None)

    assert result is None


def test_get_device_name_with_brave_client_hint():
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/155.0.0.0 Safari/537.36"
    )
    client_hint = (
        '"Brave";v="155", "Chromium";v="155", '
        '"Not(A:Brand";v="24"'
    )

    result = get_device_name(user_agent, client_hint)

    assert result == "Brave on Windows"


# ----------------------------------------
# Login unit tests
# ----------------------------------------

@pytest.mark.asyncio
async def test_login_user_success(monkeypatch):
    user = SimpleNamespace(
        id=1,
        email="test@example.com",
        password_hash="hashed-password",
        is_active=True,
        token_version=0,
    )

    repository = SimpleNamespace(
        get_by_email=AsyncMock(return_value=user),
        create_session=AsyncMock(),
    )

    service = UserService(repository)

    monkeypatch.setattr(
        "app.modules.auth.service.verify_password",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr(
        "app.modules.auth.service.create_access_token",
        lambda *args, **kwargs: "test-access-token",
    )
    monkeypatch.setattr(
        "app.modules.auth.service.create_refresh_token",
        lambda user_id: "test-refresh-token",
    )
    monkeypatch.setattr(
        "app.modules.auth.service.decode_refresh_token",
        lambda token: {
            "exp": int(datetime.now(timezone.utc).timestamp()) + 3600,
            "jti": "test-session-jti",
        },
    )

    result = await service.login_user(
        email="test@example.com",
        password="correct-password",
        ip_address="127.0.0.1",
        user_agent="CustomUnknownAgent/1.0",
    )

    assert result == {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "token_type": "bearer",
    }

    repository.get_by_email.assert_awaited_once_with(
        "test@example.com"
    )
    repository.create_session.assert_awaited_once()

    created_session = repository.create_session.await_args.args[0]

    assert created_session.user_id == 1
    assert created_session.refresh_token_jti == "test-session-jti"
    assert created_session.ip_address == "127.0.0.1"
    assert created_session.device_name == (
        "Unknown Browser on Unknown OS"
    )


@pytest.mark.asyncio
async def test_login_user_wrong_password(monkeypatch):
    user = SimpleNamespace(
        id=1,
        email="test@example.com",
        password_hash="hashed-password",
        is_active=True,
        token_version=0,
    )

    repository = SimpleNamespace(
        get_by_email=AsyncMock(return_value=user),
        create_session=AsyncMock(),
    )

    service = UserService(repository)

    verify_password_mock = AsyncMock(return_value=False)

    monkeypatch.setattr(
        "app.modules.auth.service.verify_password",
        verify_password_mock,
    )

    result = await service.login_user(
        email="test@example.com",
        password="wrong-password",
    )

    assert result is None

    verify_password_mock.assert_awaited_once_with(
        "wrong-password",
        "hashed-password",
    )
    repository.create_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_login_user_when_user_does_not_exist():
    repository = SimpleNamespace(
        get_by_email=AsyncMock(return_value=None),
        create_session=AsyncMock(),
    )

    service = UserService(repository)

    result = await service.login_user(
        email="missing@example.com",
        password="any-password",
    )

    assert result is None

    repository.get_by_email.assert_awaited_once_with(
        "missing@example.com"
    )
    repository.create_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_login_user_when_account_is_inactive(monkeypatch):
    user = SimpleNamespace(
        id=1,
        email="inactive@example.com",
        password_hash="hashed-password",
        is_active=False,
        token_version=0,
    )

    repository = SimpleNamespace(
        get_by_email=AsyncMock(return_value=user),
        create_session=AsyncMock(),
    )

    service = UserService(repository)

    verify_password_mock = AsyncMock(return_value=True)

    monkeypatch.setattr(
        "app.modules.auth.service.verify_password",
        verify_password_mock,
    )

    result = await service.login_user(
        email="inactive@example.com",
        password="correct-password",
    )

    assert result is None

    verify_password_mock.assert_awaited_once()
    repository.create_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_refresh_user_session_success(monkeypatch):
    from datetime import timedelta

    now = datetime.now(timezone.utc)

    old_session = SimpleNamespace(
        user_id=1,
        refresh_token_jti="old-jti",
        ip_address="127.0.0.1",
        user_agent="CustomUnknownAgent/1.0",
        device_name="Test Browser on Test OS",
        expires_at=now + timedelta(hours=1),
        revoked_at=None,
    )

    user = SimpleNamespace(
        id=1,
        is_active=True,
        token_version=0,
    )

    repository = SimpleNamespace(
        get_session_by_jti=AsyncMock(return_value=old_session),
        get_by_id=AsyncMock(return_value=user),
        rotate_session=AsyncMock(return_value=True),
    )

    service = UserService(repository)

    def fake_decode_refresh_token(token):
        if token == "old-refresh-token":
            return {
                "jti": "old-jti",
                "sub": "1",
            }

        if token == "new-refresh-token":
            return {
                "jti": "new-jti",
                "exp": int(
                    (datetime.now(timezone.utc) + timedelta(hours=1))
                    .timestamp()
                ),
            }

        return None

    monkeypatch.setattr(
        "app.modules.auth.service.decode_refresh_token",
        fake_decode_refresh_token,
    )
    monkeypatch.setattr(
        "app.modules.auth.service.create_access_token",
        lambda *args, **kwargs: "new-access-token",
    )
    monkeypatch.setattr(
        "app.modules.auth.service.create_refresh_token",
        lambda user_id: "new-refresh-token",
    )

    result = await service.refresh_user_session(
        "old-refresh-token"
    )

    assert result == {
        "access_token": "new-access-token",
        "refresh_token": "new-refresh-token",
        "token_type": "bearer",
    }

    repository.get_session_by_jti.assert_awaited_once_with(
        "old-jti"
    )
    repository.get_by_id.assert_awaited_once_with(1)
    repository.rotate_session.assert_awaited_once()

    rotation_args = repository.rotate_session.await_args.kwargs

    assert rotation_args["old_jti"] == "old-jti"
    assert rotation_args["user_id"] == 1

    new_session = rotation_args["new_session"]

    assert new_session.refresh_token_jti == "new-jti"
    assert new_session.user_id == 1
    assert new_session.ip_address == "127.0.0.1"
    assert new_session.user_agent == "CustomUnknownAgent/1.0"
    assert new_session.device_name == "Test Browser on Test OS"


@pytest.mark.asyncio
async def test_refresh_user_session_rejects_expired_session(
    monkeypatch,
):
    from datetime import timedelta

    old_session = SimpleNamespace(
        user_id=1,
        refresh_token_jti="expired-jti",
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0",
        device_name="Test Browser on Test OS",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        revoked_at=None,
    )

    repository = SimpleNamespace(
        get_session_by_jti=AsyncMock(return_value=old_session),
        get_by_id=AsyncMock(),
        rotate_session=AsyncMock(),
    )

    service = UserService(repository)

    monkeypatch.setattr(
        "app.modules.auth.service.decode_refresh_token",
        lambda token: {
            "jti": "expired-jti",
            "sub": "1",
        },
    )

    result = await service.refresh_user_session(
        "expired-refresh-token"
    )

    assert result is None

    repository.get_session_by_jti.assert_awaited_once_with(
        "expired-jti"
    )
    repository.get_by_id.assert_not_awaited()
    repository.rotate_session.assert_not_awaited()

@pytest.mark.asyncio
async def test_refresh_user_session_rejects_revoked_session(
    monkeypatch,
):
    from datetime import timedelta

    old_session = SimpleNamespace(
        user_id=1,
        refresh_token_jti="revoked-jti",
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0",
        device_name="Test Browser on Test OS",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        revoked_at=datetime.now(timezone.utc),
    )

    repository = SimpleNamespace(
        get_session_by_jti=AsyncMock(return_value=old_session),
        get_by_id=AsyncMock(),
        rotate_session=AsyncMock(),
    )

    service = UserService(repository)

    monkeypatch.setattr(
        "app.modules.auth.service.decode_refresh_token",
        lambda token: {
            "jti": "revoked-jti",
            "sub": "1",
        },
    )

    result = await service.refresh_user_session(
        "revoked-refresh-token"
    )

    assert result is None

    repository.get_session_by_jti.assert_awaited_once_with(
        "revoked-jti"
    )
    repository.get_by_id.assert_not_awaited()
    repository.rotate_session.assert_not_awaited()

@pytest.mark.asyncio
async def test_refresh_user_session_rejects_invalid_token(
    monkeypatch,
):
    repository = SimpleNamespace(
        get_session_by_jti=AsyncMock(),
        get_by_id=AsyncMock(),
        rotate_session=AsyncMock(),
    )

    service = UserService(repository)

    monkeypatch.setattr(
        "app.modules.auth.service.decode_refresh_token",
        lambda token: None,
    )

    result = await service.refresh_user_session(
        "invalid-refresh-token"
    )

    assert result is None

    repository.get_session_by_jti.assert_not_awaited()
    repository.get_by_id.assert_not_awaited()
    repository.rotate_session.assert_not_awaited()

@pytest.mark.asyncio
async def test_refresh_user_session_when_rotation_fails(
    monkeypatch,
):
    from datetime import timedelta

    old_session = SimpleNamespace(
        user_id=1,
        refresh_token_jti="old-jti",
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0",
        device_name="Test Browser on Test OS",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        revoked_at=None,
    )

    user = SimpleNamespace(
        id=1,
        is_active=True,
        token_version=0,
    )

    repository = SimpleNamespace(
        get_session_by_jti=AsyncMock(return_value=old_session),
        get_by_id=AsyncMock(return_value=user),
        rotate_session=AsyncMock(return_value=False),
    )

    service = UserService(repository)

    def fake_decode_refresh_token(token):
        if token == "old-refresh-token":
            return {"jti": "old-jti", "sub": "1"}

        if token == "new-refresh-token":
            from datetime import timedelta

            return {
                "jti": "new-jti",
                "exp": int(
                    (
                        datetime.now(timezone.utc)
                        + timedelta(hours=1)
                    ).timestamp()
                ),
            }

        return None

    monkeypatch.setattr(
        "app.modules.auth.service.decode_refresh_token",
        fake_decode_refresh_token,
    )
    monkeypatch.setattr(
        "app.modules.auth.service.create_access_token",
        lambda *args, **kwargs: "new-access-token",
    )
    monkeypatch.setattr(
        "app.modules.auth.service.create_refresh_token",
        lambda user_id: "new-refresh-token",
    )

    result = await service.refresh_user_session(
        "old-refresh-token"
    )

    assert result is None
    repository.rotate_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_user_session_rejects_inactive_user(
    monkeypatch,
):
    from datetime import timedelta

    old_session = SimpleNamespace(
        user_id=1,
        refresh_token_jti="old-jti",
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0",
        device_name="Test Browser on Test OS",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        revoked_at=None,
    )

    inactive_user = SimpleNamespace(
        id=1,
        is_active=False,
        token_version=0,
    )

    repository = SimpleNamespace(
        get_session_by_jti=AsyncMock(return_value=old_session),
        get_by_id=AsyncMock(return_value=inactive_user),
        rotate_session=AsyncMock(),
    )

    service = UserService(repository)

    monkeypatch.setattr(
        "app.modules.auth.service.decode_refresh_token",
        lambda token: {
            "jti": "old-jti",
            "sub": "1",
        },
    )

    result = await service.refresh_user_session(
        "old-refresh-token"
    )

    assert result is None

    repository.get_by_id.assert_awaited_once_with(1)
    repository.rotate_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_refresh_user_session_rejects_missing_user(
    monkeypatch,
):
    from datetime import timedelta

    old_session = SimpleNamespace(
        user_id=1,
        refresh_token_jti="old-jti",
        ip_address="127.0.0.1",
        user_agent="TestAgent/1.0",
        device_name="Test Browser on Test OS",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        revoked_at=None,
    )

    repository = SimpleNamespace(
        get_session_by_jti=AsyncMock(return_value=old_session),
        get_by_id=AsyncMock(return_value=None),
        rotate_session=AsyncMock(),
    )

    service = UserService(repository)

    monkeypatch.setattr(
        "app.modules.auth.service.decode_refresh_token",
        lambda token: {
            "jti": "old-jti",
            "sub": "1",
        },
    )

    result = await service.refresh_user_session(
        "old-refresh-token"
    )

    assert result is None

    repository.get_by_id.assert_awaited_once_with(1)
    repository.rotate_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_logout_user_session_success(monkeypatch):
    from datetime import timedelta

    session = SimpleNamespace(
        user_id=1,
        refresh_token_jti="logout-jti",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        revoked_at=None,
    )

    repository = SimpleNamespace(
        get_session_by_jti=AsyncMock(return_value=session),
        revoke_session=AsyncMock(),
    )

    service = UserService(repository)

    monkeypatch.setattr(
        "app.modules.auth.service.decode_refresh_token",
        lambda token: {
            "jti": "logout-jti",
            "sub": "1",
        },
    )

    result = await service.logout_user_session(
        "valid-refresh-token"
    )

    assert result is True

    repository.get_session_by_jti.assert_awaited_once_with(
        "logout-jti"
    )
    repository.revoke_session.assert_awaited_once_with(session)


@pytest.mark.asyncio
async def test_logout_user_session_rejects_invalid_token(monkeypatch):
    repository = SimpleNamespace(
        get_session_by_jti=AsyncMock(),
        revoke_session=AsyncMock(),
    )

    service = UserService(repository)

    monkeypatch.setattr(
        "app.modules.auth.service.decode_refresh_token",
        lambda token: None,
    )

    result = await service.logout_user_session(
        "invalid-refresh-token"
    )

    assert result is False

    repository.get_session_by_jti.assert_not_awaited()
    repository.revoke_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_logout_user_session_rejects_user_id_mismatch(
    monkeypatch,
):
    from datetime import timedelta

    session = SimpleNamespace(
        user_id=2,
        refresh_token_jti="mismatch-jti",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        revoked_at=None,
    )

    repository = SimpleNamespace(
        get_session_by_jti=AsyncMock(return_value=session),
        revoke_session=AsyncMock(),
    )

    service = UserService(repository)

    monkeypatch.setattr(
        "app.modules.auth.service.decode_refresh_token",
        lambda token: {
            "jti": "mismatch-jti",
            "sub": "1",
        },
    )

    result = await service.logout_user_session(
        "valid-refresh-token"
    )

    assert result is False

    repository.get_session_by_jti.assert_awaited_once_with(
        "mismatch-jti"
    )
    repository.revoke_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_logout_user_session_when_already_revoked(
    monkeypatch,
):
    from datetime import timedelta

    session = SimpleNamespace(
        user_id=1,
        refresh_token_jti="already-revoked-jti",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        revoked_at=datetime.now(timezone.utc),
    )

    repository = SimpleNamespace(
        get_session_by_jti=AsyncMock(return_value=session),
        revoke_session=AsyncMock(),
    )

    service = UserService(repository)

    monkeypatch.setattr(
        "app.modules.auth.service.decode_refresh_token",
        lambda token: {
            "jti": "already-revoked-jti",
            "sub": "1",
        },
    )

    result = await service.logout_user_session(
        "previously-used-refresh-token"
    )

    assert result is True

    repository.get_session_by_jti.assert_awaited_once_with(
        "already-revoked-jti"
    )
    repository.revoke_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_all_users_returns_paginated_result():
    users = [
        SimpleNamespace(id=11, name="User 11"),
        SimpleNamespace(id=12, name="User 12"),
    ]

    repository = SimpleNamespace(
        get_all=AsyncMock(return_value=(users, 22)),
    )

    service = UserService(repository)

    result = await service.get_all_users(page=2, limit=10)

    assert result == {
        "items": users,
        "page": 2,
        "limit": 10,
        "total": 22,
        "pages": 3,
    }

    repository.get_all.assert_awaited_once_with(
        limit=10,
        offset=10,
    )


@pytest.mark.asyncio
async def test_get_user_by_id_returns_user():
    user = SimpleNamespace(
        id=5,
        name="Test User",
        email="test@example.com",
    )

    repository = SimpleNamespace(
        get_by_id=AsyncMock(return_value=user),
    )

    service = UserService(repository)

    result = await service.get_user_by_id(user_id=5)

    assert result is user

    repository.get_by_id.assert_awaited_once_with(5)


@pytest.mark.asyncio
async def test_create_user_success(monkeypatch):
    from types import SimpleNamespace

    user_data = SimpleNamespace(
        name="Test User",
        email="test@example.com",
        password="StrongPassword123!",
        phone="9876543210",
    )

    created_user = SimpleNamespace(
        id=1,
        name=user_data.name,
        email=user_data.email,
        role="field_representative",
        phone=user_data.phone,
    )

    repository = SimpleNamespace(
        get_by_email=AsyncMock(return_value=None),
        create=AsyncMock(return_value=created_user),
    )

    service = UserService(repository)

    async def fake_hash_password(password):
        assert password == user_data.password
        return "hashed-password"

    monkeypatch.setattr(
        "app.modules.auth.service.hash_password",
        fake_hash_password,
    )

    result = await service.create_user(user_data)

    assert result is created_user

    repository.get_by_email.assert_awaited_once_with(
        "test@example.com"
    )
    repository.create.assert_awaited_once()

    created_model = repository.create.await_args.args[0]

    assert created_model.name == "Test User"
    assert created_model.email == "test@example.com"
    assert created_model.password_hash == "hashed-password"
    assert created_model.role == "field_representative"
    assert created_model.phone == "9876543210"

@pytest.mark.asyncio
async def test_create_user_rejects_duplicate_email(monkeypatch):
    existing_user = SimpleNamespace(
        id=1,
        email="test@example.com",
    )

    user_data = SimpleNamespace(
        name="Another User",
        email="test@example.com",
        password="StrongPassword123!",
        phone="9876543210",
    )

    repository = SimpleNamespace(
        get_by_email=AsyncMock(return_value=existing_user),
        create=AsyncMock(),
    )

    service = UserService(repository)

    hash_password_mock = AsyncMock(
        return_value="hashed-password",
    )

    monkeypatch.setattr(
        "app.modules.auth.service.hash_password",
        hash_password_mock,
    )

    result = await service.create_user(user_data)

    assert result is None

    repository.get_by_email.assert_awaited_once_with(
        "test@example.com"
    )
    hash_password_mock.assert_not_awaited()
    repository.create.assert_not_awaited()



# ---------------------------------------------------------
# Additional UserService tests
# ---------------------------------------------------------


@pytest.mark.asyncio
async def test_update_user_role_returns_none_when_user_missing():
    repository = SimpleNamespace(
        get_by_id=AsyncMock(return_value=None),
        count_active_admins=AsyncMock(),
        db=SimpleNamespace(
            commit=AsyncMock(),
            refresh=AsyncMock(),
        ),
    )
    service = UserService(repository)

    result = await service.update_user_role(
        user_id=999,
        role=UserRole.FIELD_REPRESENTATIVE,
    )

    assert result is None
    repository.get_by_id.assert_awaited_once_with(999)
    repository.count_active_admins.assert_not_awaited()
    repository.db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_user_role_updates_role_and_commits():
    user = SimpleNamespace(
        id=1,
        role="field_representative",
    )
    repository = SimpleNamespace(
        get_by_id=AsyncMock(return_value=user),
        count_active_admins=AsyncMock(),
        db=SimpleNamespace(
            commit=AsyncMock(),
            refresh=AsyncMock(),
        ),
    )
    service = UserService(repository)

    result = await service.update_user_role(
        user_id=1,
        role=UserRole.SALES_MANAGER,
    )

    assert result is user
    assert user.role == UserRole.SALES_MANAGER.value
    repository.db.commit.assert_awaited_once()
    repository.db.refresh.assert_awaited_once_with(user)
    repository.count_active_admins.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_user_role_protects_last_active_admin():
    admin = SimpleNamespace(
        id=1,
        role="admin",
    )
    repository = SimpleNamespace(
        get_by_id=AsyncMock(return_value=admin),
        count_active_admins=AsyncMock(return_value=1),
        db=SimpleNamespace(
            commit=AsyncMock(),
            refresh=AsyncMock(),
        ),
    )
    service = UserService(repository)

    with pytest.raises(
        ValueError,
        match="Cannot remove the last active admin",
    ):
        await service.update_user_role(
            user_id=1,
            role=UserRole.FIELD_REPRESENTATIVE,
        )

    assert admin.role == "admin"
    repository.db.commit.assert_not_awaited()
    repository.db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_user_role_allows_removing_admin_when_another_exists():
    admin = SimpleNamespace(
        id=1,
        role="admin",
    )
    repository = SimpleNamespace(
        get_by_id=AsyncMock(return_value=admin),
        count_active_admins=AsyncMock(return_value=2),
        db=SimpleNamespace(
            commit=AsyncMock(),
            refresh=AsyncMock(),
        ),
    )
    service = UserService(repository)

    result = await service.update_user_role(
        user_id=1,
        role=UserRole.FIELD_REPRESENTATIVE,
    )

    assert result is admin
    assert admin.role == "field_representative"
    repository.count_active_admins.assert_awaited_once()
    repository.db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_user_data_returns_none_when_user_missing():
    repository = SimpleNamespace(
        get_by_id=AsyncMock(return_value=None),
        update_user=AsyncMock(),
    )
    service = UserService(repository)

    result = await service.update_user_data(
        user_id=999,
        update_data={"name": "Updated Name"},
    )

    assert result is None
    repository.update_user.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_user_data_delegates_to_repository():
    user = SimpleNamespace(id=1, name="Old Name")
    updated_user = SimpleNamespace(id=1, name="Updated Name")
    update_data = {"name": "Updated Name"}

    repository = SimpleNamespace(
        get_by_id=AsyncMock(return_value=user),
        update_user=AsyncMock(return_value=updated_user),
    )
    service = UserService(repository)

    result = await service.update_user_data(
        user_id=1,
        update_data=update_data,
    )

    assert result is updated_user
    repository.update_user.assert_awaited_once_with(
        user,
        update_data,
    )


@pytest.mark.asyncio
async def test_change_password_rejects_wrong_current_password(
    monkeypatch,
):
    user = SimpleNamespace(
        id=1,
        password_hash="existing-hash",
    )
    repository = SimpleNamespace(
        update_password_and_revoke_sessions=AsyncMock(),
    )
    service = UserService(repository)

    verify_mock = AsyncMock(return_value=False)
    hash_mock = AsyncMock(return_value="new-hash")

    monkeypatch.setattr(
        "app.modules.auth.service.verify_password",
        verify_mock,
    )
    monkeypatch.setattr(
        "app.modules.auth.service.hash_password",
        hash_mock,
    )

    result = await service.change_password(
        user=user,
        current_password="wrong-password",
        new_password="NewStrongPassword123!",
    )

    assert result is False
    verify_mock.assert_awaited_once_with(
        "wrong-password",
        "existing-hash",
    )
    hash_mock.assert_not_awaited()
    repository.update_password_and_revoke_sessions.assert_not_awaited()


@pytest.mark.asyncio
async def test_change_password_hashes_new_password_and_revokes_sessions(
    monkeypatch,
):
    user = SimpleNamespace(
        id=1,
        password_hash="old-hash",
    )
    repository = SimpleNamespace(
        update_password_and_revoke_sessions=AsyncMock(),
    )
    service = UserService(repository)

    verify_mock = AsyncMock(return_value=True)
    hash_mock = AsyncMock(return_value="new-hash")

    monkeypatch.setattr(
        "app.modules.auth.service.verify_password",
        verify_mock,
    )
    monkeypatch.setattr(
        "app.modules.auth.service.hash_password",
        hash_mock,
    )

    result = await service.change_password(
        user=user,
        current_password="OldPassword123!",
        new_password="NewStrongPassword123!",
    )

    assert result is True
    hash_mock.assert_awaited_once_with(
        "NewStrongPassword123!",
    )
    repository.update_password_and_revoke_sessions.assert_awaited_once_with(
        user=user,
        password_hash="new-hash",
    )


@pytest.mark.asyncio
async def test_login_user_raises_when_new_refresh_token_cannot_be_decoded(
    monkeypatch,
):
    user = SimpleNamespace(
        id=1,
        password_hash="existing-hash",
        is_active=True,
        token_version=0,
    )
    repository = SimpleNamespace(
        get_by_email=AsyncMock(return_value=user),
        create_session=AsyncMock(),
    )
    service = UserService(repository)

    monkeypatch.setattr(
        "app.modules.auth.service.verify_password",
        AsyncMock(return_value=True),
    )
    monkeypatch.setattr(
        "app.modules.auth.service.create_access_token",
        lambda *args, **kwargs: "access-token",
    )
    monkeypatch.setattr(
        "app.modules.auth.service.create_refresh_token",
        lambda user_id: "refresh-token",
    )
    monkeypatch.setattr(
        "app.modules.auth.service.decode_refresh_token",
        lambda token: None,
    )

    with pytest.raises(
        RuntimeError,
        match="Failed to decode newly created refresh token",
    ):
        await service.login_user(
            email="test@example.com",
            password="CorrectPassword123!",
        )

    repository.create_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_refresh_user_session_raises_when_new_token_cannot_be_decoded(
    monkeypatch,
):
    now = datetime.now(timezone.utc)
    session = SimpleNamespace(
        user_id=1,
        revoked_at=None,
        expires_at=now.replace(year=now.year + 1),
        ip_address="127.0.0.1",
        user_agent="Test Browser",
        device_name="Test Browser on Test OS",
    )
    user = SimpleNamespace(
        id=1,
        is_active=True,
        token_version=0,
    )
    repository = SimpleNamespace(
        get_session_by_jti=AsyncMock(return_value=session),
        get_by_id=AsyncMock(return_value=user),
        rotate_session=AsyncMock(),
    )
    service = UserService(repository)

    def decode_token(token):
        if token == "old-refresh-token":
            return {"jti": "old-jti", "sub": "1"}
        return None

    monkeypatch.setattr(
        "app.modules.auth.service.decode_refresh_token",
        decode_token,
    )
    monkeypatch.setattr(
        "app.modules.auth.service.create_access_token",
        lambda *args, **kwargs: "new-access-token",
    )
    monkeypatch.setattr(
        "app.modules.auth.service.create_refresh_token",
        lambda user_id: "new-refresh-token",
    )

    with pytest.raises(
        RuntimeError,
        match="Failed to decode newly created refresh token",
    ):
        await service.refresh_user_session("old-refresh-token")

    repository.rotate_session.assert_not_awaited()