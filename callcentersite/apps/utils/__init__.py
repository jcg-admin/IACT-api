"""
Utils package para IACT.

CLEAN_CODE v3.0.1: Exports organizados.
SOLID: Interface Segregation - Solo exportar lo necesario.

Exports principales:
- Validators
- Formatters
- Date utils
- String utils
- Number utils
- File utils
- Decorators
- Helpers

NOTA: SoftDeleteMixin, TimeStampedModel, etc están en apps.core.models
"""

# ============================================================================
# VALIDATORS
# ============================================================================

from apps.utils.validators import (
    validate_email,
    validate_phone_number,
    validate_rut,
    validate_service_800,
    validate_codigo_center,
    validate_date_range,
)

# ============================================================================
# FORMATTERS
# ============================================================================

from apps.utils.formatters import (
    format_phone_cl,
    format_rut,
    format_currency,
    format_percentage,
    format_service_800,
    format_file_size,
)

# ============================================================================
# DATE UTILS
# ============================================================================

from apps.utils.date_utils import (
    get_quarter_from_date,
    get_quarter_date_range,
    format_datetime_cl,
    format_date_cl,
    parse_date_flexible,
    get_date_range_days,
    add_business_days,
    is_business_day,
    convert_to_cl_timezone,
    get_current_datetime_cl,
    generate_date_range,
)

# ============================================================================
# STRING UTILS
# ============================================================================

from apps.utils.string_utils import (
    slugify,
    normalize_text,
    remove_special_chars,
    truncate,
    truncate_words,
    to_snake_case,
    to_camel_case,
    to_title_case,
    pad_left,
    pad_right,
)

# ============================================================================
# NUMBER UTILS
# ============================================================================

from apps.utils.number_utils import (
    round_decimal,
    round_to_nearest,
    calculate_percentage,
    percentage_change,
    format_number,
    format_compact_number,
    clamp,
    is_in_range,
    calculate_average,
    calculate_median,
)

# ============================================================================
# FILE UTILS
# ============================================================================

from apps.utils.file_utils import (
    get_file_extension,
    change_file_extension,
    get_file_size_bytes,
    validate_file_type,
    is_image_file,
    is_document_file,
    get_mime_type,
    sanitize_filename,
    ensure_directory_exists,
    get_unique_filename,
)

# ============================================================================
# DECORATORS
# ============================================================================

from apps.utils.decorators import (
    log_execution,
    log_duration,
    retry_on_failure,
    cache_result,
    require_permission,
    measure_time,
    deprecated,
)

# ============================================================================
# HELPERS
# ============================================================================

from apps.utils.helpers import (
    get_client_ip,
    get_user_agent,
    is_ajax_request,
    generate_uuid,
    generate_short_uuid,
    hash_string,
    generate_random_token,
    safe_get,
    merge_dicts,
    chunk_list,
    flatten_list,
    unique_list,
    str_to_bool,
    remove_none_values,
    remove_empty_strings,
    should_exclude_path,
)

# ============================================================================
# ALL EXPORTS
# ============================================================================

__all__ = [
    # Validators
    'validate_email',
    'validate_phone_number',
    'validate_rut',
    'validate_service_800',
    'validate_codigo_center',
    'validate_date_range',
    
    # Formatters
    'format_phone_cl',
    'format_rut',
    'format_currency',
    'format_percentage',
    'format_service_800',
    'format_file_size',
    
    # Date Utils
    'get_quarter_from_date',
    'get_quarter_date_range',
    'format_datetime_cl',
    'format_date_cl',
    'parse_date_flexible',
    'get_date_range_days',
    'add_business_days',
    'is_business_day',
    'convert_to_cl_timezone',
    'get_current_datetime_cl',
    'generate_date_range',
    
    # String Utils
    'slugify',
    'normalize_text',
    'remove_special_chars',
    'truncate',
    'truncate_words',
    'to_snake_case',
    'to_camel_case',
    'to_title_case',
    'pad_left',
    'pad_right',
    
    # Number Utils
    'round_decimal',
    'round_to_nearest',
    'calculate_percentage',
    'percentage_change',
    'format_number',
    'format_compact_number',
    'clamp',
    'is_in_range',
    'calculate_average',
    'calculate_median',
    
    # File Utils
    'get_file_extension',
    'change_file_extension',
    'get_file_size_bytes',
    'validate_file_type',
    'is_image_file',
    'is_document_file',
    'get_mime_type',
    'sanitize_filename',
    'ensure_directory_exists',
    'get_unique_filename',
    
    # Decorators
    'log_execution',
    'log_duration',
    'retry_on_failure',
    'cache_result',
    'require_permission',
    'measure_time',
    'deprecated',
    
    # Helpers
    'get_client_ip',
    'get_user_agent',
    'is_ajax_request',
    'generate_uuid',
    'generate_short_uuid',
    'hash_string',
    'generate_random_token',
    'safe_get',
    'merge_dicts',
    'chunk_list',
    'flatten_list',
    'unique_list',
    'str_to_bool',
    'remove_none_values',
    'remove_empty_strings',
    'should_exclude_path',
]

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
# Validators
from apps.utils import validate_email, validate_rut
if validate_email('user@example.com'):
    ...

# Formatters
from apps.utils import format_rut, format_currency
formatted_rut = format_rut('12345678-9')
formatted_money = format_currency(1234567, currency='CLP')

# Date Utils
from apps.utils import get_quarter_from_date, format_datetime_cl
quarter = get_quarter_from_date(date.today())

# String Utils
from apps.utils import slugify, truncate
slug = slugify('Hola Mundo 2025')
short = truncate('Long text...', 20)

# Number Utils
from apps.utils import calculate_percentage, format_compact_number
percentage = calculate_percentage(25, 100)
compact = format_compact_number(1500000)  # '1.5M'

# File Utils
from apps.utils import get_file_extension, sanitize_filename
ext = get_file_extension('document.pdf')
safe_name = sanitize_filename('My File!.txt')

# Decorators
from apps.utils import log_execution, cache_result

@log_execution
def my_function():
    pass

@cache_result(timeout=300)
def expensive_calc():
    pass

# Helpers
from apps.utils import get_client_ip, generate_uuid
ip = get_client_ip(request)
uuid = generate_uuid()
"""
