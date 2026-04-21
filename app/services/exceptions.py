"""Errores de dominio para mapear a respuestas JSON coherentes."""


class OAuthConnectorError(Exception):
    """Base para errores del conector."""

    def __init__(self, message: str, status_code: int = 400, code: str = "error") -> None:
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


class ConfigurationError(OAuthConnectorError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=500, code="configuration_error")


class UnsupportedProviderError(OAuthConnectorError):
    def __init__(self, provider: str) -> None:
        super().__init__(
            f"Proveedor no soportado: {provider}",
            status_code=400,
            code="unsupported_provider",
        )


class OAuthFlowError(OAuthConnectorError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message, status_code=status_code, code="oauth_flow_error")


class TokenExchangeError(OAuthFlowError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=502)


class InvalidSessionError(OAuthConnectorError):
    def __init__(self) -> None:
        super().__init__(
            "Sesión inválida o expirada. Completa de nuevo el flujo OAuth.",
            status_code=401,
            code="invalid_session",
        )


class ExternalAPIError(OAuthConnectorError):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message, status_code=status_code, code="external_api_error")
