from sqlalchemy.orm import Session
from . import models, schemas, queries
from typing import List


# dim_accounts
def get_dim_account(db: Session, account_code: str):
    return db.query(models.DimAccount).filter(models.DimAccount.AccountCode == account_code).first()


# dim_securitymaster
def get_dim_securitymaster(db: Session, secid: str):
    return db.query(models.DimSecurityMaster).filter(models.DimSecurityMaster.secid == secid).first()


# dim_transaction_types
def get_dim_transaction_type(db: Session, transaction_type: str):
    return (
        db.query(models.DimTransactionType)
        .filter(models.DimTransactionType.TransactionType == transaction_type)
        .first()
    )


# fact_account_ror
def get_fact_account_ror(db: Session, account_code: str):
    return db.query(models.FactAccountRor).filter(models.FactAccountRor.account_code == account_code).first()


# fact_daily_aggregate_values
def get_fact_daily_aggregate_value(db: Session, account_code: str):
    return (
        db.query(models.FactDailyAggregateValue)
        .filter(models.FactDailyAggregateValue.account_code == account_code)
        .first()
    )


# fact_daily_aggregate_values_slp
def get_fact_daily_aggregate_value_slp(db: Session, account_code: str):
    return (
        db.query(models.FactDailyAggregateValueSlp)
        .filter(models.FactDailyAggregateValueSlp.account_code == account_code)
        .first()
    )


# fact_holdings_all
def get_fact_holdings_all(db: Session, as_of_date: str, account_code: str):
    return (
        db.query(models.FactHoldingsAll)
        .filter(models.FactHoldingsAll.AsofDate == as_of_date, models.FactHoldingsAll.AccountCode == account_code)
        .first()
    )


# fact_holdings_all_rollup
def get_fact_holdings_all_rollup(db: Session, as_of_date: str, account_code: str):
    return (
        db.query(models.FactHoldingsAllRollup)
        .filter(
            models.FactHoldingsAllRollup.AsOfDate == as_of_date,
            models.FactHoldingsAllRollup.AccountCode == account_code,
        )
        .first()
    )


# fact_transactions
def get_fact_transaction(db: Session, account_code: str):
    return db.query(models.FactTransaction).filter(models.FactTransaction.AccountCode == account_code).first()


# fx_rate
def get_fx_rate(db: Session, as_of_date: str):
    return db.query(models.FxRate).filter(models.FxRate.AsofDate == as_of_date).first()


def get_holdings_by_account(db: Session, account_code: str):
    query = queries.get_holdings_query()
    return db.execute(query, {"account_code": account_code}).fetchall()


def get_aggregated_holdings(
    db: Session, request: schemas.HoldingsAggregationRequest
) -> List[schemas.AggregatedHolding]:
    query = queries.get_aggregated_holdings_query(
        account_group_by_clause=request.account_group_by_clause,
        security_group_by_clause=request.security_group_by_clause,
    )
    results = db.execute(
        query, {"as_of_date": request.as_of_date, "account_codes": tuple(request.account_codes)}
    ).fetchall()

    aggregated_holdings = []
    for row in results:
        group = {}
        for col in request.account_group_by_clause:
            group[col] = getattr(row, col)
        for col in request.security_group_by_clause:
            group[col] = getattr(row, col)

        aggregated_holdings.append(schemas.AggregatedHolding(group=group, total_market_value=row.total_market_value))

    return aggregated_holdings


def get_available_sankey_columns(db: Session) -> schemas.AvailableSankeyColumns:
    """
    Get available columns for Sankey diagram grouping from both account and security tables.
    Returns snake_case column names for API consistency while ensuring database compatibility.
    """
    from .queries import get_database_column_mapping, camel_to_snake

    query = queries.get_available_sankey_columns_query()
    results = db.execute(query).fetchall()

    # Get our column mapping for name conversion
    column_mapping = get_database_column_mapping()
    reverse_mapping = {v: k for k, v in column_mapping.items()}

    account_columns = []
    security_columns = []

    for row in results:
        # Convert database column name to snake_case if we have a mapping for it
        db_column_name = row.column_name
        snake_case_name = reverse_mapping.get(db_column_name, camel_to_snake(db_column_name))

        # Create prefixed name using snake_case
        if row.table_type == "account":
            prefixed_name = f"account.{snake_case_name}"
        else:
            prefixed_name = f"security.{snake_case_name}"

        column = schemas.AvailableColumn(
            table_type=row.table_type,
            column_name=snake_case_name,  # Use snake_case for API consistency
            prefixed_name=prefixed_name,
        )

        if row.table_type == "account":
            account_columns.append(column)
        else:
            security_columns.append(column)

    return schemas.AvailableSankeyColumns(account_columns=account_columns, security_columns=security_columns)


def get_holdings_for_sankey(db: Session, request: schemas.SankeyRequest) -> schemas.SankeyData:
    """
    Get holdings data formatted for Sankey diagram visualization.
    Creates a hierarchical structure with Grand Total as the root node.
    """
    query = queries.get_sankey_holdings_query(sankey_levels=request.sankey_levels)
    results = db.execute(
        query, {"as_of_date": request.as_of_date, "account_codes": tuple(request.account_codes)}
    ).fetchall()

    # Convert results to dictionaries for easier processing
    data = []
    total_value = 0

    for row in results:
        row_dict = {}
        for i, level in enumerate(request.sankey_levels):
            # Remove prefixes for column access
            clean_level = level.replace("account.", "").replace("security.", "")
            if clean_level == "asset_class_level_1_name":
                row_dict[clean_level] = getattr(row, "asset_class_level_1_name")
            else:
                row_dict[clean_level] = getattr(row, clean_level)
        row_dict["value"] = row.total_market_value
        data.append(row_dict)
        total_value += row.total_market_value

    # Build Sankey nodes and links
    nodes = [schemas.SankeyNode(label="Grand Total")]  # Root node
    links = []
    node_map = {"Grand Total": 0}
    node_counter = 1

    # Process each level of the hierarchy
    for level_idx, level in enumerate(request.sankey_levels):
        clean_level = level.replace("account.", "").replace("security.", "")

        # Group data by current level
        level_groups = {}
        for item in data:
            key = item[clean_level]
            if key not in level_groups:
                level_groups[key] = 0
            level_groups[key] += item["value"]

        # Create nodes and links for this level
        for group_name, group_value in level_groups.items():
            node_label = f"{group_name}"

            if node_label not in node_map:
                nodes.append(schemas.SankeyNode(label=node_label))
                node_map[node_label] = node_counter
                node_counter += 1

            # Create link from previous level
            if level_idx == 0:
                # Link from Grand Total
                links.append(
                    schemas.SankeyLink(source=0, target=node_map[node_label], value=group_value)  # Grand Total
                )
            else:
                # Link from previous level groups
                prev_level = request.sankey_levels[level_idx - 1]
                prev_clean_level = prev_level.replace("account.", "").replace("security.", "")

                # Group by previous level to create proper links
                prev_to_curr = {}
                for item in data:
                    prev_key = item[prev_clean_level]
                    curr_key = item[clean_level]
                    link_key = f"{prev_key} -> {curr_key}"

                    if link_key not in prev_to_curr:
                        prev_to_curr[link_key] = 0
                    prev_to_curr[link_key] += item["value"]

                # Create links
                for link_key, link_value in prev_to_curr.items():
                    prev_name, curr_name = link_key.split(" -> ")
                    if prev_name in node_map and curr_name in node_map:
                        links.append(
                            schemas.SankeyLink(source=node_map[prev_name], target=node_map[curr_name], value=link_value)
                        )

    return schemas.SankeyData(nodes=nodes, links=links)
