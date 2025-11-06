from __future__ import annotations

import logging

from ..core.config import settings

log = logging.getLogger("telemetry")


def _init_sentry() -> bool:
    """
    Инициализирует Sentry, если задан DSN и доступен пакет sentry_sdk.
    Возвращает True, если Sentry включён.
    """
    dsn = settings.SENTRY_DSN
    if not dsn:
        log.info("Sentry DSN is not set — Sentry disabled")
        return False

    try:
        import sentry_sdk  # type: ignore
        from sentry_sdk.integrations.logging import LoggingIntegration  # type: ignore
        from sentry_sdk.integrations.fastapi import FastApiIntegration  # type: ignore

        sentry_logging = LoggingIntegration(
            level=logging.INFO,  # breadcrumbs
            event_level=logging.ERROR,  # отправлять события с ERROR и выше
        )

        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=0.2,  # APM, подстрой при необходимости
            profiles_sample_rate=0.0,  # профайлинг выключен по умолчанию
            integrations=[
                sentry_logging,
                FastApiIntegration(),  # корректная интеграция с FastAPI
            ],
            environment=settings.ENV,
            release=f"{settings.APP_NAME}@{settings.APP_VERSION}",
            send_default_pii=False,
        )
        log.info("Sentry initialized")
        return True
    except ImportError:
        log.warning("sentry_sdk not installed — Sentry disabled")
        return False
    except Exception as e:  # на всякий случай не валим сервис
        log.exception("Sentry init failed: %s", e)
        return False


def _init_opentelemetry() -> bool:
    """
    Инициализирует OpenTelemetry, если соответствующие пакеты установлены.
    Экспорт — OTLP, endpoint берётся из переменной окружения OTEL_EXPORTER_OTLP_ENDPOINT (если выставлена).
    Возвращает True, если OTel включён.
    """
    try:
        # Опциональные импорты (если нет — просто пропускаем)
        from opentelemetry import trace  # type: ignore
        from opentelemetry.sdk.resources import Resource  # type: ignore
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter  # type: ignore

        resource = Resource.create(
            {
                "service.name": settings.APP_NAME,
                "service.version": settings.APP_VERSION,
                "deployment.environment": settings.ENV,
            }
        )

        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

        exporter = (
            OTLPSpanExporter()
        )  # читает конфиг из env, например OTEL_EXPORTER_OTLP_ENDPOINT
        processor = BatchSpanProcessor(exporter, max_export_batch_size=512)
        provider.add_span_processor(processor)

        log.info("OpenTelemetry initialized (OTLP exporter)")
        return True
    except ImportError:
        log.info("OpenTelemetry packages not installed — OTel disabled")
        return False
    except Exception as e:
        log.exception("OpenTelemetry init failed: %s", e)
        return False


def init_telemetry() -> None:
    """
    Единая точка входа для телеметрии.
    Безусловно вызывается приложением; внутри сам решает, что инициализировать.
    Всегда безопасен (не кидает исключений наружу).
    """
    try:
        sentry_on = _init_sentry()
        otel_on = _init_opentelemetry()
        if not (sentry_on or otel_on):
            log.info("Telemetry: all optional backends are disabled (ok for local/dev)")
    except Exception as e:
        # Никогда не ломаем приложение из-за телеметрии
        log.exception("Telemetry initialization failed: %s", e)
