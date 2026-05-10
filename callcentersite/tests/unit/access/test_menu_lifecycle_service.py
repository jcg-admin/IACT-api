"""
Tests para MenuLifecycleService (T-104).

Cobertura:
- VALID_TRANSITIONS: estructura correcta
- transition(): transiciones permitidas y bloqueadas
- transition(): setea timestamps correctos
- can_transition() / get_allowed_transitions()
- auto_archive_menu_items(): archiva los candidatos correctos
- auto_archive_menu_items(): respeta block_auto_archive
"""
import pytest
from datetime import timedelta
from unittest.mock import MagicMock, patch, PropertyMock, call
from django.utils import timezone

from apps.access.services.menu_lifecycle_service import (
    MenuLifecycleService,
    InvalidTransitionError,
)
from apps.access.models import MenuItem


# ---------------------------------------------------------------------------
# Fixture: MenuItem mock sin BD
# ---------------------------------------------------------------------------

def _make_item(status='DRAFT', pk=1):
    item = MagicMock(spec=MenuItem)
    item.pk = pk
    item.status = status
    item.deprecated_at = None
    item.archived_at = None
    item.block_auto_archive = False
    item.save = MagicMock()
    return item


# ---------------------------------------------------------------------------
# VALID_TRANSITIONS
# ---------------------------------------------------------------------------

class TestValidTransitions:

    def test_estructura_completa(self):
        vt = MenuLifecycleService.VALID_TRANSITIONS
        assert set(vt.keys()) == {'DRAFT', 'ACTIVE', 'DEPRECATED', 'ARCHIVED'}

    def test_draft_solo_puede_ir_a_active(self):
        assert MenuLifecycleService.VALID_TRANSITIONS['DRAFT'] == ['ACTIVE']

    def test_active_solo_puede_ir_a_deprecated(self):
        assert MenuLifecycleService.VALID_TRANSITIONS['ACTIVE'] == ['DEPRECATED']

    def test_deprecated_solo_puede_ir_a_archived(self):
        assert MenuLifecycleService.VALID_TRANSITIONS['DEPRECATED'] == ['ARCHIVED']

    def test_archived_es_terminal(self):
        assert MenuLifecycleService.VALID_TRANSITIONS['ARCHIVED'] == []

    def test_archived_no_puede_volver_a_active(self):
        """Invariante: ARCHIVED → ACTIVE no está permitida."""
        assert 'ACTIVE' not in MenuLifecycleService.VALID_TRANSITIONS['ARCHIVED']


# ---------------------------------------------------------------------------
# transition()
# ---------------------------------------------------------------------------

class TestTransition:

    def test_draft_a_active_permitido(self):
        item = _make_item('DRAFT')
        with patch('django.db.transaction.atomic'):
            MenuLifecycleService.transition(item, 'ACTIVE')
        assert item.status == 'ACTIVE'

    def test_active_a_deprecated_permitido(self):
        item = _make_item('ACTIVE')
        with patch('django.db.transaction.atomic'):
            MenuLifecycleService.transition(item, 'DEPRECATED')
        assert item.status == 'DEPRECATED'

    def test_deprecated_a_archived_permitido(self):
        item = _make_item('DEPRECATED')
        with patch('django.db.transaction.atomic'):
            MenuLifecycleService.transition(item, 'ARCHIVED')
        assert item.status == 'ARCHIVED'

    def test_draft_a_deprecated_prohibido(self):
        item = _make_item('DRAFT')
        with pytest.raises(InvalidTransitionError):
            MenuLifecycleService.transition(item, 'DEPRECATED')

    def test_archived_a_active_prohibido(self):
        item = _make_item('ARCHIVED')
        with pytest.raises(InvalidTransitionError):
            MenuLifecycleService.transition(item, 'ACTIVE')

    def test_active_a_draft_prohibido(self):
        item = _make_item('ACTIVE')
        with pytest.raises(InvalidTransitionError):
            MenuLifecycleService.transition(item, 'DRAFT')

    def test_estado_invalido_lanza_value_error(self):
        item = _make_item('DRAFT')
        with pytest.raises(ValueError, match="Estado inválido"):
            MenuLifecycleService.transition(item, 'INEXISTENTE')

    def test_deprecated_setea_deprecated_at(self):
        item = _make_item('ACTIVE')
        before = timezone.now()
        with patch('django.db.transaction.atomic'):
            MenuLifecycleService.transition(item, 'DEPRECATED')
        assert item.deprecated_at is not None
        assert item.deprecated_at >= before

    def test_archived_setea_archived_at(self):
        item = _make_item('DEPRECATED')
        before = timezone.now()
        with patch('django.db.transaction.atomic'):
            MenuLifecycleService.transition(item, 'ARCHIVED')
        assert item.archived_at is not None
        assert item.archived_at >= before

    def test_active_no_setea_timestamps(self):
        item = _make_item('DRAFT')
        item.deprecated_at = None
        item.archived_at = None
        with patch('django.db.transaction.atomic'):
            MenuLifecycleService.transition(item, 'ACTIVE')
        assert item.deprecated_at is None
        assert item.archived_at is None

    def test_llama_save(self):
        item = _make_item('DRAFT')
        with patch('django.db.transaction.atomic'):
            MenuLifecycleService.transition(item, 'ACTIVE')
        item.save.assert_called_once()

    def test_save_incluye_status_en_update_fields(self):
        item = _make_item('DRAFT')
        with patch('django.db.transaction.atomic'):
            MenuLifecycleService.transition(item, 'ACTIVE')
        kwargs = item.save.call_args[1]
        assert 'status' in kwargs['update_fields']


# ---------------------------------------------------------------------------
# can_transition / get_allowed_transitions
# ---------------------------------------------------------------------------

class TestCanTransition:

    def test_draft_puede_ir_a_active(self):
        item = _make_item('DRAFT')
        assert MenuLifecycleService.can_transition(item, 'ACTIVE') is True

    def test_draft_no_puede_ir_a_deprecated(self):
        item = _make_item('DRAFT')
        assert MenuLifecycleService.can_transition(item, 'DEPRECATED') is False

    def test_archived_no_puede_transicionar(self):
        item = _make_item('ARCHIVED')
        assert MenuLifecycleService.can_transition(item, 'ACTIVE') is False
        assert MenuLifecycleService.can_transition(item, 'DEPRECATED') is False

    def test_get_allowed_transitions_draft(self):
        item = _make_item('DRAFT')
        assert MenuLifecycleService.get_allowed_transitions(item) == ['ACTIVE']

    def test_get_allowed_transitions_archived(self):
        item = _make_item('ARCHIVED')
        assert MenuLifecycleService.get_allowed_transitions(item) == []


# ---------------------------------------------------------------------------
# auto_archive_menu_items()
# ---------------------------------------------------------------------------

class TestAutoArchive:

    def test_archiva_deprecated_mayor_90_dias(self):
        item = _make_item('DEPRECATED')
        item.deprecated_at = timezone.now() - timedelta(days=91)
        item.block_auto_archive = False

        with patch.object(MenuLifecycleService, 'transition') as mock_t, \
             patch('apps.access.models.MenuItem.objects') as mock_qs:
            mock_qs.filter.return_value = [item]
            count = MenuLifecycleService.auto_archive_menu_items()

        mock_t.assert_called_once_with(item, 'ARCHIVED')
        assert count == 1

    def test_no_archiva_si_block_auto_archive(self):
        item = _make_item('DEPRECATED')
        item.deprecated_at = timezone.now() - timedelta(days=91)
        item.block_auto_archive = True

        with patch.object(MenuLifecycleService, 'transition') as mock_t, \
             patch('apps.access.models.MenuItem.objects') as mock_qs:
            mock_qs.filter.return_value = [item]
            count = MenuLifecycleService.auto_archive_menu_items()

        mock_t.assert_not_called()
        assert count == 0

    def test_retorna_numero_de_archivados(self):
        items = [_make_item('DEPRECATED', pk=i) for i in range(3)]
        for it in items:
            it.deprecated_at = timezone.now() - timedelta(days=91)
            it.block_auto_archive = False

        with patch.object(MenuLifecycleService, 'transition'), \
             patch('apps.access.models.MenuItem.objects') as mock_qs:
            mock_qs.filter.return_value = items
            count = MenuLifecycleService.auto_archive_menu_items()

        assert count == 3
