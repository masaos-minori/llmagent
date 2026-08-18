#!/usr/bin/env python3
"""scripts/shared/llm_transport_errors.py — LLM transport error handling helpers."""

import httpx

from shared.llm_exceptions import LLMTransportError

# HTTP status codes treated as transient (safe to retry): 429 Too Many Requests,
# 503 Service Unavailable.
_RETRYABLE_HTTP_STATUS_CODES = (429, 503)


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut: MutantDict = {}  # type: ignore
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut: MutantDict = {}  # type: ignore


class LlmTransportErrorHandler:
    """Static methods for translating HTTP/stream errors into LLMTransportError."""

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut)
    def raise_http_status_error(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in _RETRYABLE_HTTP_STATUS_CODES
        raise LLMTransportError(
            kind="HTTP_STATUS_RETRYABLE" if retryable else "HTTP_STATUS_FATAL",
            phase="pre_stream",
            url=url,
            status_code=code,
            retryable=retryable,
        ) from e

    @staticmethod
    def xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_orig(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in _RETRYABLE_HTTP_STATUS_CODES
        raise LLMTransportError(
            kind="HTTP_STATUS_RETRYABLE" if retryable else "HTTP_STATUS_FATAL",
            phase="pre_stream",
            url=url,
            status_code=code,
            retryable=retryable,
        ) from e

    @staticmethod
    def xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_1(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = None
        retryable = code in _RETRYABLE_HTTP_STATUS_CODES
        raise LLMTransportError(
            kind="HTTP_STATUS_RETRYABLE" if retryable else "HTTP_STATUS_FATAL",
            phase="pre_stream",
            url=url,
            status_code=code,
            retryable=retryable,
        ) from e

    @staticmethod
    def xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_2(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = None
        raise LLMTransportError(
            kind="HTTP_STATUS_RETRYABLE" if retryable else "HTTP_STATUS_FATAL",
            phase="pre_stream",
            url=url,
            status_code=code,
            retryable=retryable,
        ) from e

    @staticmethod
    def xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_3(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code not in _RETRYABLE_HTTP_STATUS_CODES
        raise LLMTransportError(
            kind="HTTP_STATUS_RETRYABLE" if retryable else "HTTP_STATUS_FATAL",
            phase="pre_stream",
            url=url,
            status_code=code,
            retryable=retryable,
        ) from e

    @staticmethod
    def xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_4(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in _RETRYABLE_HTTP_STATUS_CODES
        raise LLMTransportError(
            kind=None,
            phase="pre_stream",
            url=url,
            status_code=code,
            retryable=retryable,
        ) from e

    @staticmethod
    def xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_5(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in _RETRYABLE_HTTP_STATUS_CODES
        raise LLMTransportError(
            kind="HTTP_STATUS_RETRYABLE" if retryable else "HTTP_STATUS_FATAL",
            phase=None,
            url=url,
            status_code=code,
            retryable=retryable,
        ) from e

    @staticmethod
    def xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_6(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in _RETRYABLE_HTTP_STATUS_CODES
        raise LLMTransportError(
            kind="HTTP_STATUS_RETRYABLE" if retryable else "HTTP_STATUS_FATAL",
            phase="pre_stream",
            url=None,
            status_code=code,
            retryable=retryable,
        ) from e

    @staticmethod
    def xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_7(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in _RETRYABLE_HTTP_STATUS_CODES
        raise LLMTransportError(
            kind="HTTP_STATUS_RETRYABLE" if retryable else "HTTP_STATUS_FATAL",
            phase="pre_stream",
            url=url,
            status_code=None,
            retryable=retryable,
        ) from e

    @staticmethod
    def xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_8(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in _RETRYABLE_HTTP_STATUS_CODES
        raise LLMTransportError(
            kind="HTTP_STATUS_RETRYABLE" if retryable else "HTTP_STATUS_FATAL",
            phase="pre_stream",
            url=url,
            status_code=code,
            retryable=None,
        ) from e

    @staticmethod
    def xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_9(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in _RETRYABLE_HTTP_STATUS_CODES
        raise LLMTransportError(
            phase="pre_stream",
            url=url,
            status_code=code,
            retryable=retryable,
        ) from e

    @staticmethod
    def xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_10(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in _RETRYABLE_HTTP_STATUS_CODES
        raise LLMTransportError(
            kind="HTTP_STATUS_RETRYABLE" if retryable else "HTTP_STATUS_FATAL",
            url=url,
            status_code=code,
            retryable=retryable,
        ) from e

    @staticmethod
    def xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_11(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in _RETRYABLE_HTTP_STATUS_CODES
        raise LLMTransportError(
            kind="HTTP_STATUS_RETRYABLE" if retryable else "HTTP_STATUS_FATAL",
            phase="pre_stream",
            status_code=code,
            retryable=retryable,
        ) from e

    @staticmethod
    def xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_12(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in _RETRYABLE_HTTP_STATUS_CODES
        raise LLMTransportError(
            kind="HTTP_STATUS_RETRYABLE" if retryable else "HTTP_STATUS_FATAL",
            phase="pre_stream",
            url=url,
            retryable=retryable,
        ) from e

    @staticmethod
    def xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_13(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in _RETRYABLE_HTTP_STATUS_CODES
        raise LLMTransportError(
            kind="HTTP_STATUS_RETRYABLE" if retryable else "HTTP_STATUS_FATAL",
            phase="pre_stream",
            url=url,
            status_code=code,
            ) from e

    @staticmethod
    def xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_14(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in _RETRYABLE_HTTP_STATUS_CODES
        raise LLMTransportError(
            kind="XXHTTP_STATUS_RETRYABLEXX" if retryable else "HTTP_STATUS_FATAL",
            phase="pre_stream",
            url=url,
            status_code=code,
            retryable=retryable,
        ) from e

    @staticmethod
    def xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_15(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in _RETRYABLE_HTTP_STATUS_CODES
        raise LLMTransportError(
            kind="http_status_retryable" if retryable else "HTTP_STATUS_FATAL",
            phase="pre_stream",
            url=url,
            status_code=code,
            retryable=retryable,
        ) from e

    @staticmethod
    def xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_16(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in _RETRYABLE_HTTP_STATUS_CODES
        raise LLMTransportError(
            kind="HTTP_STATUS_RETRYABLE" if retryable else "XXHTTP_STATUS_FATALXX",
            phase="pre_stream",
            url=url,
            status_code=code,
            retryable=retryable,
        ) from e

    @staticmethod
    def xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_17(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in _RETRYABLE_HTTP_STATUS_CODES
        raise LLMTransportError(
            kind="HTTP_STATUS_RETRYABLE" if retryable else "http_status_fatal",
            phase="pre_stream",
            url=url,
            status_code=code,
            retryable=retryable,
        ) from e

    @staticmethod
    def xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_18(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in _RETRYABLE_HTTP_STATUS_CODES
        raise LLMTransportError(
            kind="HTTP_STATUS_RETRYABLE" if retryable else "HTTP_STATUS_FATAL",
            phase="XXpre_streamXX",
            url=url,
            status_code=code,
            retryable=retryable,
        ) from e

    @staticmethod
    def xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_19(e: httpx.HTTPStatusError, url: str) -> None:
        """Convert an httpx HTTP status error into LLMTransportError and raise it."""
        code = e.response.status_code
        retryable = code in _RETRYABLE_HTTP_STATUS_CODES
        raise LLMTransportError(
            kind="HTTP_STATUS_RETRYABLE" if retryable else "HTTP_STATUS_FATAL",
            phase="PRE_STREAM",
            url=url,
            status_code=code,
            retryable=retryable,
        ) from e

    @staticmethod
    @_mutmut_mutated(mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut)
    def translate_stream_error(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_orig(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_1(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind=None,
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_2(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase=None,
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_3(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=None,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_4(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=None,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_5(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=None,
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_6(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_7(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_8(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_9(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_10(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_11(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="XXCONNECT_ERRORXX",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_12(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="connect_error",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_13(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="XXpre_streamXX",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_14(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="PRE_STREAM",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_15(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=False,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_16(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(None),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_17(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind=None,
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_18(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase=None,
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_19(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=None,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_20(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=None,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_21(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=None,
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_22(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_23(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_24(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_25(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_26(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_27(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="XXREAD_TIMEOUTXX",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_28(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="read_timeout",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_29(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="XXin_streamXX",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_30(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="IN_STREAM",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_31(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=False,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_32(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(None),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_33(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind=None,
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_34(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase=None,
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_35(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=None,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_36(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=None,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_37(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=None,
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_38(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_39(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_40(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_41(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_42(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_43(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="XXUNKNOWN_STREAM_ERRORXX",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_44(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="unknown_stream_error",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_45(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="XXin_streamXX",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_46(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="IN_STREAM",
            url=url,
            retryable=False,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_47(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=True,
            detail=str(e),
        )

    @staticmethod
    def xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_48(e: Exception, url: str) -> LLMTransportError:
        """Translate a stream-level exception into LLMTransportError.

        HTTP status errors are handled separately in raise_http_status_error.
        """
        if isinstance(e, httpx.ConnectError):
            return LLMTransportError(
                kind="CONNECT_ERROR",
                phase="pre_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        if isinstance(e, httpx.ReadTimeout):
            return LLMTransportError(
                kind="READ_TIMEOUT",
                phase="in_stream",
                url=url,
                retryable=True,
                detail=str(e),
            )
        return LLMTransportError(
            kind="UNKNOWN_STREAM_ERROR",
            phase="in_stream",
            url=url,
            retryable=False,
            detail=str(None),
        )

mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut['_mutmut_orig'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut['xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_1'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut['xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_2'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut['xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_3'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut['xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_4'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut['xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_5'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut['xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_6'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut['xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_7'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut['xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_8'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut['xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_9'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut['xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_10'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut['xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_11'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut['xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_12'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut['xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_13'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut['xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_14'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut['xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_15'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut['xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_16'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut['xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_17'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut['xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_18'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut['xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_19'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁraise_http_status_error__mutmut_19 # type: ignore # mutmut generated

mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['_mutmut_orig'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_orig # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_1'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_1 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_2'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_2 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_3'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_3 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_4'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_4 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_5'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_5 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_6'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_6 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_7'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_7 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_8'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_8 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_9'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_9 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_10'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_10 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_11'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_11 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_12'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_12 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_13'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_13 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_14'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_14 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_15'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_15 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_16'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_16 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_17'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_17 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_18'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_18 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_19'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_19 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_20'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_20 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_21'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_21 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_22'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_22 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_23'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_23 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_24'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_24 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_25'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_25 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_26'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_26 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_27'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_27 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_28'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_28 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_29'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_29 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_30'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_30 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_31'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_31 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_32'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_32 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_33'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_33 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_34'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_34 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_35'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_35 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_36'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_36 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_37'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_37 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_38'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_38 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_39'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_39 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_40'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_40 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_41'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_41 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_42'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_42 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_43'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_43 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_44'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_44 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_45'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_45 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_46'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_46 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_47'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_47 # type: ignore # mutmut generated
mutants_xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut['xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_48'] = LlmTransportErrorHandler.xǁLlmTransportErrorHandlerǁtranslate_stream_error__mutmut_48 # type: ignore # mutmut generated
