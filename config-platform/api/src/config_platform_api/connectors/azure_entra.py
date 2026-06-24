"""Azure Entra token acquisition for database connectors."""

from __future__ import annotations

from config_platform_api.connectors.base import ConnectorValidationError

AZURE_SQL_SCOPE = "https://database.windows.net/.default"
AZURE_OSS_RDBMS_SCOPE = "https://ossrdbms-aad.database.windows.net/.default"


def _import_azure_identity():
    try:
        from azure.identity import ClientSecretCredential, DefaultAzureCredential, UsernamePasswordCredential
    except ImportError as exc:
        raise ConnectorValidationError(
            "Azure identity library is not installed on the config API host."
        ) from exc
    return ClientSecretCredential, DefaultAzureCredential, UsernamePasswordCredential


def acquire_token_client_secret(
    tenant_id: str,
    client_id: str,
    client_secret: str,
    *,
    scope: str,
) -> str:
    ClientSecretCredential, _, _ = _import_azure_identity()
    credential = ClientSecretCredential(tenant_id, client_id, client_secret)
    return credential.get_token(scope).token


def acquire_token_username_password(
    tenant_id: str,
    client_id: str,
    username: str,
    password: str,
    *,
    scope: str,
) -> str:
    _, _, UsernamePasswordCredential = _import_azure_identity()
    credential = UsernamePasswordCredential(
        client_id=client_id,
        username=username,
        password=password,
        tenant_id=tenant_id,
    )
    return credential.get_token(scope).token


def acquire_token_managed_identity(
  managed_identity_client_id: str = "",
  *,
  scope: str,
) -> str:
    _, DefaultAzureCredential, _ = _import_azure_identity()
    credential = DefaultAzureCredential(
        managed_identity_client_id=managed_identity_client_id or None,
    )
    try:
        return credential.get_token(scope).token
    except Exception as exc:
        raise ConnectorValidationError(
            "Managed identity authentication failed. Run the config API on an Azure host "
            "with managed identity enabled, or configure local Azure credentials for development."
        ) from exc


def acquire_azure_sql_token_service_principal(tenant_id: str, client_id: str, client_secret: str) -> str:
    return acquire_token_client_secret(
        tenant_id,
        client_id,
        client_secret,
        scope=AZURE_SQL_SCOPE,
    )


def acquire_azure_sql_token_password(
    tenant_id: str,
    client_id: str,
    entra_user: str,
    entra_password: str,
) -> str:
    return acquire_token_username_password(
        tenant_id,
        client_id,
        entra_user,
        entra_password,
        scope=AZURE_SQL_SCOPE,
    )


def acquire_azure_sql_token_managed_identity(managed_identity_client_id: str = "") -> str:
    return acquire_token_managed_identity(managed_identity_client_id, scope=AZURE_SQL_SCOPE)


def acquire_azure_oss_rdbms_token_service_principal(
    tenant_id: str,
    client_id: str,
    client_secret: str,
) -> str:
    return acquire_token_client_secret(
        tenant_id,
        client_id,
        client_secret,
        scope=AZURE_OSS_RDBMS_SCOPE,
    )


def acquire_azure_oss_rdbms_token_password(
    tenant_id: str,
    client_id: str,
    entra_user: str,
    entra_password: str,
) -> str:
    return acquire_token_username_password(
        tenant_id,
        client_id,
        entra_user,
        entra_password,
        scope=AZURE_OSS_RDBMS_SCOPE,
    )


def acquire_azure_oss_rdbms_token_managed_identity(managed_identity_client_id: str = "") -> str:
    return acquire_token_managed_identity(managed_identity_client_id, scope=AZURE_OSS_RDBMS_SCOPE)


def build_entra_export_block(validated: dict[str, object]) -> dict[str, object]:
    entra: dict[str, object] = {}
    for key in ("tenant_id", "client_id", "entra_user", "managed_identity_client_id"):
        value = validated.get(key)
        if value:
            entra[key] = value
    return entra
