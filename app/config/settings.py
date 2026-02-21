"""
Master application settings.

Pure Python dataclasses — zero external dependencies.
All values configurable via environment variables.
Env var naming: INSTRUMENT__NPS_ANNUAL_RATE, PERFORMANCE__WORKER_THREADS, etc.

Design decisions:
- No pydantic dependency — runs in any Python 3.10+ environment
- Dataclasses are immutable (frozen=True) — thread-safe reads
- All monetary values as Decimal — never float
- Single module-level singleton loaded once at startup
- get_config() returns same singleton — safe for DI frameworks
"""

import os
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache


# ─────────────────────────────────────────────────────────────────
# Helpers — read from environment with typed defaults
# ─────────────────────────────────────────────────────────────────

def _env_str(key: str, default: str) -> str:
    return os.environ.get(key, default)

def _env_int(key: str, default: int) -> int:
    return int(os.environ.get(key, str(default)))

def _env_float(key: str, default: float) -> float:
    return float(os.environ.get(key, str(default)))

def _env_bool(key: str, default: bool) -> bool:
    val = os.environ.get(key, str(default)).lower()
    return val in ("1", "true", "yes")

def _env_decimal(key: str, default: str) -> Decimal:
    return Decimal(os.environ.get(key, default))


# ─────────────────────────────────────────────────────────────────
# Sub-configs
# ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class InstrumentConfig:
    """
    Investment instrument rates and constraints.
    All configurable — change rates without touching business logic.
    """

    # NPS — National Pension Scheme
    nps_annual_rate:      Decimal = _env_decimal("INSTRUMENT__NPS_ANNUAL_RATE",    "0.0711")
    nps_max_deduction:    Decimal = _env_decimal("INSTRUMENT__NPS_MAX_DEDUCTION",  "200000")
    nps_income_pct_cap:   Decimal = _env_decimal("INSTRUMENT__NPS_INCOME_PCT_CAP", "0.10")

    # Index Fund (Nifty 50)
    index_annual_rate:    Decimal = _env_decimal("INSTRUMENT__INDEX_ANNUAL_RATE",  "0.1449")

    # Compounding — annually per challenge spec (n=1)
    compounding_frequency: int    = _env_int("INSTRUMENT__COMPOUNDING_FREQUENCY",  1)

    # Retirement thresholds
    retirement_age:        int    = _env_int("INSTRUMENT__RETIREMENT_AGE",         60)
    min_investment_years:  int    = _env_int("INSTRUMENT__MIN_INVESTMENT_YEARS",   5)

    # Rounding
    rounding_multiple:     int    = _env_int("INSTRUMENT__ROUNDING_MULTIPLE",      100)


@dataclass(frozen=True)
class PerformanceConfig:
    """
    Runtime performance tuning.
    Adjust per deployment environment without code changes.
    """

    max_payload_size_mb:     int  = _env_int("PERFORMANCE__MAX_PAYLOAD_SIZE_MB",     50)
    request_timeout_ms:      int  = _env_int("PERFORMANCE__REQUEST_TIMEOUT_MS",      1000)
    streaming_threshold:     int  = _env_int("PERFORMANCE__STREAMING_THRESHOLD",     10_000)
    worker_threads:          int  = _env_int("PERFORMANCE__WORKER_THREADS",          16)
    max_concurrent_requests: int  = _env_int("PERFORMANCE__MAX_CONCURRENT_REQUESTS", 1000)
    cache_ttl_seconds:       int  = _env_int("PERFORMANCE__CACHE_TTL_SECONDS",       300)
    enable_response_cache:   bool = _env_bool("PERFORMANCE__ENABLE_RESPONSE_CACHE",  True)


@dataclass(frozen=True)
class ScalingConfig:
    """
    Rate limiting and circuit breaker configuration.
    """

    rate_limit_per_ip:              int   = _env_int("SCALING__RATE_LIMIT_PER_IP",               1000)
    rate_limit_per_user:            int   = _env_int("SCALING__RATE_LIMIT_PER_USER",             5000)
    rate_limit_window_seconds:      int   = _env_int("SCALING__RATE_LIMIT_WINDOW_SECONDS",       60)
    circuit_breaker_threshold:      float = _env_float("SCALING__CIRCUIT_BREAKER_THRESHOLD",     0.50)
    circuit_breaker_window_seconds: int   = _env_int("SCALING__CIRCUIT_BREAKER_WINDOW_SECONDS",  10)
    circuit_breaker_recovery_s:     int   = _env_int("SCALING__CIRCUIT_BREAKER_RECOVERY_S",      30)


@dataclass(frozen=True)
class ObservabilityConfig:
    """
    Logging, metrics, and tracing configuration.
    """

    log_level:       str  = _env_str("OBSERVABILITY__LOG_LEVEL",       "INFO")
    log_format:      str  = _env_str("OBSERVABILITY__LOG_FORMAT",       "json")
    enable_metrics:  bool = _env_bool("OBSERVABILITY__ENABLE_METRICS",  True)
    enable_tracing:  bool = _env_bool("OBSERVABILITY__ENABLE_TRACING",  True)
    metrics_port:    int  = _env_int("OBSERVABILITY__METRICS_PORT",     9090)
    service_name:    str  = _env_str("OBSERVABILITY__SERVICE_NAME",     "blk-retirement-api")
    service_version: str  = _env_str("OBSERVABILITY__SERVICE_VERSION",  "1.0.0")


@dataclass(frozen=True)
class ServerConfig:
    """
    HTTP server configuration.
    Port 5477 is MANDATORY per challenge spec.
    """

    host:       str  = _env_str("SERVER__HOST",      "0.0.0.0")
    port:       int  = _env_int("SERVER__PORT",       5477)          # MANDATORY
    workers:    int  = _env_int("SERVER__WORKERS",    4)
    reload:     bool = _env_bool("SERVER__RELOAD",    False)
    api_prefix: str  = _env_str("SERVER__API_PREFIX", "/blackrock/challenge/v1")


# ─────────────────────────────────────────────────────────────────
# Root config
# ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class AppConfig:
    """
    Root configuration — composes all sub-configs.
    Single source of truth for the entire application.

    Loading order (later overrides earlier):
    1. Defaults defined in dataclass fields
    2. Environment variables (SECTION__KEY=value)

    Thread-safe: frozen dataclass + module-level singleton.
    """

    instrument:    InstrumentConfig    = None   # type: ignore
    performance:   PerformanceConfig   = None   # type: ignore
    scaling:       ScalingConfig       = None   # type: ignore
    observability: ObservabilityConfig = None   # type: ignore
    server:        ServerConfig        = None   # type: ignore
    environment:   str                 = _env_str("ENVIRONMENT", "development")

    def __post_init__(self):
        # Populate nested configs if not provided
        # frozen=True requires object.__setattr__ for mutation
        if self.instrument is None:
            object.__setattr__(self, "instrument", InstrumentConfig())
        if self.performance is None:
            object.__setattr__(self, "performance", PerformanceConfig())
        if self.scaling is None:
            object.__setattr__(self, "scaling", ScalingConfig())
        if self.observability is None:
            object.__setattr__(self, "observability", ObservabilityConfig())
        if self.server is None:
            object.__setattr__(self, "server", ServerConfig())

        allowed = {"development", "staging", "production", "test"}
        if self.environment not in allowed:
            raise ValueError(
                f"ENVIRONMENT must be one of {allowed}, "
                f"got '{self.environment}'"
            )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


# ─────────────────────────────────────────────────────────────────
# Singleton accessor
# ─────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """
    Singleton config accessor.
    Loaded once at first call, cached forever.
    Zero overhead on subsequent calls.

    Usage in FastAPI:  Depends(get_config)
    Usage in core:     from app.config.settings import config
    """
    return AppConfig()


# Module-level singleton — imported directly by core layer
config: AppConfig = get_config()