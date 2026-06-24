"""Microsoft SQL Server ODBC connection helpers."""

from __future__ import annotations

import platform
import re
import struct
from typing import Any

import pyodbc
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL

from config_platform_api.connectors.base import ConnectorValidationError

SQL_COPT_SS_ACCESS_TOKEN = 1256

ODBC_DRIVER_CANDIDATES = (
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 13 for SQL Server",
    "SQL Server",
)


def resolve_odbc_driver() -> str:
    installed = set(pyodbc.drivers())
    for driver_name in ODBC_DRIVER_CANDIDATES:
        if driver_name in installed:
            return driver_name
    raise ConnectorValidationError(
        "SQL Server ODBC driver not found on the config API host. "
        "Install Microsoft ODBC Driver 18 for SQL Server and retry."
    )


def build_mssql_odbc_connect(
    *,
    server: str,
    port: int,
    database: str,
    auth_method: str,
    username: str = "",
    password: str = "",
    domain: str = "",
    client_id: str = "",
    client_secret: str = "",
    encrypt: bool = True,
    trust_server_certificate: bool = False,
    driver_name: str | None = None,
) -> str:
    if auth_method == "windows_integrated" and platform.system() != "Windows":
        raise ConnectorValidationError(
            "Windows integrated security requires the config API to run on a domain-joined Windows host. "
            "Use SQL login or explicit Windows authentication instead."
        )

    driver = driver_name or resolve_odbc_driver()
    encrypt_value = "yes" if encrypt else "no"
    trust_value = "yes" if trust_server_certificate else "no"
    parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={server},{port}",
        f"DATABASE={database}",
        f"Encrypt={encrypt_value}",
        f"TrustServerCertificate={trust_value}",
    ]

    if auth_method == "sql_login":
        parts.extend([f"UID={username}", f"PWD={password}"])
    elif auth_method == "windows_integrated":
        parts.append("Trusted_Connection=yes")
    elif auth_method == "windows_login":
        login = f"{domain}\\{username}" if domain else username
        parts.extend([f"UID={login}", f"PWD={password}"])
    elif auth_method == "entra_service_principal":
        parts.extend(
            [
                f"UID={client_id}",
                f"PWD={client_secret}",
                "Authentication=ActiveDirectoryServicePrincipal",
            ]
        )
    else:
        raise ConnectorValidationError(f"Unsupported MSSQL auth method: {auth_method}")

    return ";".join(parts) + ";"


def create_mssql_engine(
    odbc_connect: str,
    *,
    connect_timeout: int = 10,
    access_token: str | None = None,
) -> Engine:
    url = URL.create("mssql+pyodbc", query={"odbc_connect": odbc_connect})
    connect_args: dict[str, Any] = {"timeout": connect_timeout}
    if access_token:
        token_bytes = access_token.encode("utf-16-le")
        token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
        connect_args["attrs_before"] = {SQL_COPT_SS_ACCESS_TOKEN: token_struct}
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)


def acquire_azure_sql_access_token(tenant_id: str, client_id: str, client_secret: str) -> str:
    try:
        from azure.identity import ClientSecretCredential
    except ImportError as exc:
        raise ConnectorValidationError(
            "Azure identity library is not installed on the config API host."
        ) from exc

    credential = ClientSecretCredential(tenant_id, client_id, client_secret)
    return credential.get_token("https://database.windows.net/.default").token


def strip_sqlalchemy_error_suffix(message: str) -> str:
    return re.split(r"\s*\(Background on this error at:", message, maxsplit=1)[0].strip()
