from sqlalchemy import text
import re


def camel_to_snake(name):
    """Convert CamelCase to snake_case"""
    # Insert an underscore before any uppercase letter that follows a lowercase letter
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    # Insert an underscore before any uppercase letter that follows a lowercase letter or digit
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def get_database_column_mapping():
    """
    Map user-friendly snake_case column names to actual database column names.
    This ensures we use the correct database columns while maintaining consistent API naming.
    """
    return {
        # Account table mappings
        "account_type": "AccountType",
        "account_visualization_id": "AccountVisualizationID",
        "account_name": "AccountName",
        "custodian_account_code": "CustodianAccountCode",
        "custodian_code": "CustodianCode",
        "custodian_name": "CustodianName",
        "open_date": "OpenDate",
        "country": "Country",
        "contact_address_line1": "ContactAddressLine1",
        "status": "Status",
        "account_currency_code": "AccountCurrencyCode",
        "is_registered_account": "IsRegisteredAccount",
        "processed_date": "ProcessedDate",
        "processed_timestamp_est": "ProcessedTimestampEST",
        "raw_file": "rawFile",
        # Security table mappings
        "security_name": "security_name",  # already snake_case
        "security_symbol": "security_symbol",  # already snake_case
        "security_description": "security_description",  # already snake_case
        "security_type_code": "security_type_code",  # already snake_case
        "security_type_description": "security_type_description",  # already snake_case
        "sec_status": "sec_status",  # already snake_case
        "security_country": "security_country",  # already snake_case
        "security_currency_code": "security_currency_code",  # already snake_case
        "asset_class": "asset_class",  # already snake_case
        "asset_class_code": "asset_class_code",  # already snake_case
        "industry_group": "industry_group",  # already snake_case
        "industry_group_code": "industry_group_code",  # already snake_case
        "issuer_code": "issuer_code",  # already snake_case
        "issuer": "issuer",  # already snake_case
        "asset_class_level_1_name": "AssetClassLevel1Name",  # CamelCase in DB
        "asset_class_level_2_name": "AssetClassLevel2Name",  # CamelCase in DB
        "asset_class_level_3_name": "AssetClassLevel3Name",  # CamelCase in DB
    }


def get_holdings_query():
    return text(
        """
        SELECT
            h."AsofDate" AS as_of_date,
            a."AccountName" AS account_name,
            s.security_name AS security_name,
            s.security_type_description AS security_type,
            h."MarketValue" AS market_value,
            h."Quantity" AS quantity,
            h."MarketValue" * h."Quantity" AS total_value
        FROM phw_dev_gold.fact_holdings_all h
        JOIN phw_dev_gold.dim_accounts a ON h."AccountCode" = a."AccountCode"
        JOIN phw_dev_gold.dim_securitymaster s ON h."SecurityCode" = s.security_code
        WHERE h."AccountCode" = :account_code
    """
    )


def get_aggregated_holdings_query(account_group_by_clause: list[str], security_group_by_clause: list[str]):
    account_cols = ", ".join([f'a."{col}"' for col in account_group_by_clause])
    security_cols = ", ".join([f's."{col}"' for col in security_group_by_clause])

    group_by_cols = []
    if account_cols:
        group_by_cols.append(account_cols)
    if security_cols:
        group_by_cols.append(security_cols)

    select_clause = ", ".join(group_by_cols)
    group_by_clause = ", ".join(group_by_cols)

    return text(
        f"""
        SELECT
            {select_clause},
            SUM(h."MarketValue") as total_market_value
        FROM phw_dev_gold.fact_holdings_all h
        JOIN phw_dev_gold.dim_accounts a ON h."AccountCode" = a."AccountCode"
        JOIN phw_dev_gold.dim_securitymaster s ON h."SecurityCode" = s.security_code
        WHERE h."CurrencyCode" = 'CAD'
        AND h."AsofDate" = :as_of_date
        AND h."AccountCode" IN :account_codes
        GROUP BY {group_by_clause}
    """
    )


def get_sankey_holdings_query(sankey_levels: list[str]):
    """
    Generate a query for Sankey diagram data with dynamic column selection.
    Supports prefixed columns: 'account.ColumnName' or 'security.ColumnName'
    """
    column_mapping = get_database_column_mapping()
    select_cols = []
    group_by_cols = []

    for level in sankey_levels:
        if level.startswith("account."):
            snake_case_col = level[8:]  # Remove 'account.' prefix
            # Get actual database column name
            db_col_name = column_mapping.get(snake_case_col, snake_case_col)
            select_cols.append(f'a."{db_col_name}" AS {snake_case_col}')
            group_by_cols.append(f'a."{db_col_name}"')
        elif level.startswith("security."):
            snake_case_col = level[9:]  # Remove 'security.' prefix
            # Get actual database column name
            db_col_name = column_mapping.get(snake_case_col, snake_case_col)
            select_cols.append(f's."{db_col_name}" AS {snake_case_col}')
            group_by_cols.append(f's."{db_col_name}"')
        else:
            # Default behavior for backward compatibility - assume it's from security table
            snake_case_col = camel_to_snake(level)
            db_col_name = column_mapping.get(snake_case_col, level)
            select_cols.append(f's."{db_col_name}" AS {snake_case_col}')
            group_by_cols.append(f's."{db_col_name}"')

    # Combine clauses
    select_clause = ", ".join(select_cols)
    group_by_clause = ", ".join(group_by_cols)

    return text(
        f"""
        SELECT
            {select_clause},
            SUM(h."MarketValue") as total_market_value
        FROM phw_dev_gold.fact_holdings_all h
        JOIN phw_dev_gold.dim_accounts a ON h."AccountCode" = a."AccountCode"
        JOIN phw_dev_gold.dim_securitymaster s ON h."SecurityCode" = s.security_code
        WHERE h."CurrencyCode" = 'CAD'
        AND h."AsofDate" = :as_of_date
        AND h."AccountCode" IN :account_codes
        GROUP BY {group_by_clause}
        ORDER BY total_market_value DESC
    """
    )


def get_available_sankey_columns_query():
    """
    Get available columns for Sankey diagram grouping from both account and security tables.
    Returns snake_case column names for API consistency while mapping to correct database columns.
    """
    column_mapping = get_database_column_mapping()
    # Create reverse mapping to get snake_case names for display
    reverse_mapping = {v: k for k, v in column_mapping.items()}

    return text(
        """
        SELECT 
            'account' as table_type,
            column_name,
            'account.' || column_name as prefixed_name
        FROM information_schema.columns 
        WHERE table_schema = 'phw_dev_gold' 
        AND table_name = 'dim_accounts'
        AND column_name NOT IN ('AccountCode', 'ProcessedDate', 'ProcessedTimestampEST', 'rawFile')
        
        UNION ALL
        
        SELECT 
            'security' as table_type,
            column_name,
            'security.' || column_name as prefixed_name
        FROM information_schema.columns 
        WHERE table_schema = 'phw_dev_gold' 
        AND table_name = 'dim_securitymaster'
        AND column_name NOT IN ('secid', 'security_code', 'ProcessedDate')
        
        ORDER BY table_type, column_name
    """
    )
