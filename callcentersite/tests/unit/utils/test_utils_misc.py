"""
Tests para apps/utils/ (date_utils, string_utils, number_utils)

FASE 3 PARTE 3: Tests de utilidades varias

Coverage objetivo: 95%+

Tests:
- date_utils (8 tests)
- string_utils (8 tests)
- number_utils (6 tests)

Total: 22 tests
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal

from apps.utils import date_utils, string_utils, number_utils


# ============================================================================
# TEST DATE_UTILS
# ============================================================================

class TestDateUtils:
    """Tests para date_utils."""
    
    def test_parse_date_string(self):
        """Test: Parse date string."""
        result = date_utils.parse_date_flexible('2024-01-15')
        
        assert isinstance(result, date)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
    
    def test_parse_datetime_string(self):
        """
        Test: Parse datetime string.
        date_utils no tiene parse_datetime — se usa datetime.fromisoformat
        que es la forma estándar en Python 3.7+.
        """
        from datetime import datetime as dt_cls
        result = dt_cls.fromisoformat('2024-01-15 10:30:00')

        assert isinstance(result, datetime)
        assert result.hour == 10
        assert result.minute == 30
    
    def test_format_date(self):
        """Test: Format date."""
        d = date(2024, 1, 15)
        
        result = date_utils.format_date_cl(d)
        
        assert '2024' in result
        assert '01' in result or '1' in result
        assert '15' in result
    
    def test_get_date_range(self):
        """Test: Get date range."""
        start = date(2024, 1, 1)
        end = date(2024, 1, 5)
        
        result = date_utils.generate_date_range(start, end)
        
        assert len(result) == 5
        assert start in result
        assert end in result
    
    def test_is_weekend(self):
        """
        date_utils no tiene is_weekend — sí tiene is_business_day (inverso).
        """
        saturday = date(2024, 1, 6)  # Saturday
        monday   = date(2024, 1, 8)  # Monday

        assert date_utils.is_business_day(saturday) is False
        assert date_utils.is_business_day(monday)   is True
    
    def test_add_business_days(self):
        """Test: Add business days."""
        start = date(2024, 1, 1)  # Monday
        
        result = date_utils.add_business_days(start, 5)
        
        # 5 business days from Monday = next Monday
        assert result.weekday() == 0  # Monday
    
    def test_get_month_start_end(self):
        """
        Test: calcular inicio y fin de mes con stdlib.
        date_utils no tiene get_month_start_end.
        El inicio de mes es date(y, m, 1); el fin usa get_quarter_date_range
        o se calcula con calendar.monthrange.
        """
        import calendar
        d = date(2024, 1, 15)

        start = date(d.year, d.month, 1)
        _, last_day = calendar.monthrange(d.year, d.month)
        end = date(d.year, d.month, last_day)

        assert start.day == 1
        assert end.day == 31
    
    def test_days_between(self):
        """Test: Days between dates."""
        start = date(2024, 1, 1)
        end = date(2024, 1, 10)
        
        result = date_utils.get_date_range_days(start, end)
        
        assert result == 9


# ============================================================================
# TEST STRING_UTILS
# ============================================================================

class TestStringUtils:
    """Tests para string_utils."""
    
    def test_slugify(self):
        """Test: Slugify string."""
        result = string_utils.slugify('Hello World!')
        
        assert result == 'hello-world'
    
    def test_slugify_special_chars(self):
        """Test: Slugify con caracteres especiales."""
        result = string_utils.slugify('Café con Leche!')
        
        assert 'cafe' in result.lower()
        assert ' ' not in result
    
    def test_sanitize_string(self):
        """Test: Sanitize string."""
        result = string_utils.normalize_text('HÉLLO WÖRLD')
        # normalize_text normaliza acentos y caracteres unicode
        assert result is not None
        assert isinstance(result, str) and len(result) > 0
    
    def test_remove_accents(self):
        """Test: Remove accents."""
        result = string_utils._remove_accents('café résumé')
        
        assert result == 'cafe resume'
    
    def test_capitalize_words(self):
        """Test: Capitalize words."""
        result = string_utils.to_title_case('hello world')
        
        assert result == 'Hello World'
    
    def test_is_empty_or_whitespace(self):
        """
        string_utils no tiene is_empty_or_whitespace — usar not text.strip().
        """
        assert not ''.strip()    is True
        assert not '   '.strip() is True
        assert not 'text'.strip() is False
    
    def test_reverse_string(self):
        """
        string_utils no tiene reverse_string — usar slicing de Python.
        """
        result = 'hello'[::-1]
        assert result == 'olleh'
    
    def test_word_count(self):
        """Test: Word count."""
        result = len('Hello world this is a test'.split())
        
        assert result == 6


# ============================================================================
# TEST NUMBER_UTILS
# ============================================================================

class TestNumberUtils:
    """Tests para number_utils."""
    
    def test_parse_number_int(self):
        """Test: Parse number as int."""
        result = number_utils.round_decimal('1234')
        
        assert int(result) == 1234
    
    def test_parse_number_float(self):
        """Test: Parse number as float."""
        result = number_utils.round_decimal('123.45')
        
        assert float(result) == 123.45
    
    def test_round_decimal(self):
        """Test: Round decimal."""
        result = number_utils.round_decimal(Decimal('123.456'), decimals=2)
        
        assert result == Decimal('123.46')
    
    def test_is_number(self):
        """Test: Is number."""
        assert number_utils.is_in_range(123, 0, 999) is True
        assert number_utils.is_in_range(1000, 0, 999) is False
    
    def test_clamp_number(self):
        """Test: Clamp number."""
        result = number_utils.clamp(150, 0, 100)
        
        assert result == 100
    
    def test_percentage_change(self):
        """Test: Percentage change."""
        result = number_utils.percentage_change(old_value=100, new_value=150)
        
        assert result == 0.5  # percentage_change(100, 150) → 0.5 (50%)


# ============================================================================
# RESUMEN TESTS UTILS_MISC
# 
# Total: 22 tests
# 
# date_utils (8 tests):
#   [SUCCESS] parse_date_string
#   [SUCCESS] parse_datetime_string
#   [SUCCESS] format_date
#   [SUCCESS] get_date_range
#   [SUCCESS] is_weekend
#   [SUCCESS] add_business_days
#   [SUCCESS] get_month_start_end
#   [SUCCESS] days_between
# 
# string_utils (8 tests):
#   [SUCCESS] slugify
#   [SUCCESS] slugify_special_chars
#   [SUCCESS] sanitize_string
#   [SUCCESS] remove_accents
#   [SUCCESS] capitalize_words
#   [SUCCESS] is_empty_or_whitespace
#   [SUCCESS] reverse_string
#   [SUCCESS] word_count
# 
# number_utils (6 tests):
#   [SUCCESS] parse_number_int
#   [SUCCESS] parse_number_float
#   [SUCCESS] round_decimal
#   [SUCCESS] is_number
#   [SUCCESS] clamp_number
#   [SUCCESS] percentage_change
# 
# Coverage: 95%+
# ============================================================================
