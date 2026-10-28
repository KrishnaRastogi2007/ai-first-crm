from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.modules.hcp.service import HCPService


@pytest.fixture
def repository():
    return SimpleNamespace(
        get_by_id=AsyncMock(),
        delete=AsyncMock(),
        delete_if_assigned_to=AsyncMock(),
    )


@pytest.fixture
def user_repository():
    return SimpleNamespace(
        get_by_id=AsyncMock(),
    )


@pytest.fixture
def service(repository, user_repository):
    return HCPService(
        repository=repository,
        user_repository=user_repository,
    )


@pytest.mark.asyncio
async def test_field_rep_can_delete_own_hcp(service, repository):
    user = SimpleNamespace(id=10, role="field_representative")
    repository.delete_if_assigned_to.return_value = True

    result = await service.delete_hcp(1, user)

    assert result is True
    repository.delete_if_assigned_to.assert_awaited_once_with(
        hcp_id=1,
        user_id=10,
    )
    repository.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_field_rep_cannot_delete_unassigned_hcp(service, repository):
    user = SimpleNamespace(id=10, role="field_representative")
    repository.delete_if_assigned_to.return_value = False
    repository.get_by_id.return_value = SimpleNamespace(
        id=1,
        assigned_to=None,
    )

    with pytest.raises(Exception) as exc_info:
        await service.delete_hcp(1, user)

    assert getattr(exc_info.value, "status_code", None) == 403
    repository.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_field_rep_cannot_delete_another_users_hcp(
    service,
    repository,
):
    user = SimpleNamespace(id=10, role="field_representative")
    repository.delete_if_assigned_to.return_value = False
    repository.get_by_id.return_value = SimpleNamespace(
        id=1,
        assigned_to=20,
    )

    with pytest.raises(Exception) as exc_info:
        await service.delete_hcp(1, user)

    assert getattr(exc_info.value, "status_code", None) == 403
    repository.delete.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["admin", "sales_manager"])
async def test_admin_and_sales_manager_can_delete_unassigned_hcp(
    service,
    repository,
    role,
):
    user = SimpleNamespace(id=10, role=role)
    hcp = SimpleNamespace(id=1, assigned_to=None)
    repository.get_by_id.return_value = hcp

    result = await service.delete_hcp(1, user)

    assert result is True
    repository.delete.assert_awaited_once_with(hcp)
    repository.delete_if_assigned_to.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_missing_hcp_returns_none(service, repository):
    user = SimpleNamespace(id=10, role="admin")
    repository.get_by_id.return_value = None

    result = await service.delete_hcp(999, user)

    assert result is None
    repository.delete.assert_not_awaited()
