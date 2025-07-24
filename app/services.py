from sqlalchemy.orm import Session
from . import models, schemas, queries
from typing import List
from decimal import Decimal


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


def get_available_account_codes(db: Session) -> List[str]:
    """Get all available account codes from the holdings data"""
    from sqlalchemy import text

    # Query to get distinct account codes only
    rows = db.query(models.FactHoldingsAll.AccountCode).distinct().all()
    return [row[0] for row in rows]


def get_holdings_by_account(db: Session, account_code: str):
    query = queries.get_holdings_query()
    return db.execute(query, {"account_code": account_code}).fetchall()


def get_aggregated_holdings(
    db: Session, request: schemas.HoldingsAggregationRequest
) -> List[schemas.AggregatedHolding]:
    account_group_by = request.account_group_by_clause if request.account_group_by_clause is not None else []
    security_group_by = request.security_group_by_clause if request.security_group_by_clause is not None else []
    query = queries.get_aggregated_holdings_query(
        account_group_by_clause=account_group_by,
        security_group_by_clause=security_group_by,
    )
    results = db.execute(
        query, {"as_of_date": request.as_of_date, "account_codes": tuple(request.account_codes)}
    ).fetchall()

    aggregated_holdings = []
    for row in results:
        group = {}
        for col in account_group_by:
            group[col] = getattr(row, col)
        for col in security_group_by:
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
            # Use the snake_case column name that was aliased in the SQL query
            row_dict[clean_level] = getattr(row, clean_level)
        # Round market value to 2 decimal places
        row_dict["value"] = round(float(row.total_market_value), 2)
        data.append(row_dict)
        total_value += row_dict["value"]

    # Build Sankey nodes and links
    nodes = [schemas.SankeyNode(label="Grand Total")]  # Root node
    node_map = {"Grand Total": 0}
    node_counter = 1
    
    # Collect all unique node labels first
    all_node_labels = set(["Grand Total"])
    for item in data:
        for level in request.sankey_levels:
            clean_level = level.replace("account.", "").replace("security.", "")
            all_node_labels.add(str(item[clean_level]))
    
    # Create all nodes
    for label in sorted(all_node_labels):
        if label not in node_map:
            nodes.append(schemas.SankeyNode(label=label))
            node_map[label] = node_counter
            node_counter += 1

    # Now create links level by level
    links = []
    
    # Process each level of the hierarchy
    for level_idx, level in enumerate(request.sankey_levels):
        clean_level = level.replace("account.", "").replace("security.", "")

        if level_idx == 0:
            # First level: links from Grand Total
            level_aggregation = {}
            for item in data:
                key = str(item[clean_level])
                if key not in level_aggregation:
                    level_aggregation[key] = 0
                level_aggregation[key] += item["value"]
            
            # Create links from Grand Total to first level
            for group_name, group_value in level_aggregation.items():
                rounded_value = round(float(group_value), 2)
                if group_name in node_map:
                    links.append(
                        schemas.SankeyLink(source=0, target=node_map[group_name], value=rounded_value)
                    )
        else:
            # Subsequent levels: links from previous level
            prev_level = request.sankey_levels[level_idx - 1]
            prev_clean_level = prev_level.replace("account.", "").replace("security.", "")
            
            # Create a mapping from (prev_level_value, curr_level_value) -> aggregated_value
            link_aggregation = {}
            for item in data:
                prev_key = str(item[prev_clean_level])
                curr_key = str(item[clean_level])
                link_key = (prev_key, curr_key)
                
                if link_key not in link_aggregation:
                    link_aggregation[link_key] = 0
                link_aggregation[link_key] += item["value"]
            
            # Create links from previous level to current level
            for (prev_name, curr_name), link_value in link_aggregation.items():
                if prev_name in node_map and curr_name in node_map:
                    rounded_link_value = round(float(link_value), 2)
                    links.append(
                        schemas.SankeyLink(
                            source=node_map[prev_name], 
                            target=node_map[curr_name], 
                            value=rounded_link_value
                        )
                    )

    return schemas.SankeyData(nodes=nodes, links=links)


def get_available_dates_for_accounts(
    db: Session, request: schemas.AvailableDatesRequest
) -> schemas.AvailableDatesResponse:
    """
    Get available as_of_date values for given account codes from holdings data.
    """
    query = queries.get_available_dates_query()
    results = db.execute(query, {"account_codes": tuple(request.account_codes)}).fetchall()

    # Extract dates from results
    available_dates = [row.as_of_date for row in results]

    # Calculate summary statistics
    date_count = len(available_dates)
    earliest_date = min(available_dates) if available_dates else None
    latest_date = max(available_dates) if available_dates else None

    return schemas.AvailableDatesResponse(
        account_codes=request.account_codes,
        available_dates=available_dates,
        date_count=date_count,
        earliest_date=earliest_date,
        latest_date=latest_date,
    )


class PerformanceSankeyService:
    def __init__(self, db: Session):
        self.db = db

    def generate_sankey_data(self, start_date, end_date, account_codes):
        # Fixed attribution levels with account breakdown
        attribution_levels = ["fx", "dividends", "appreciation", "fees", "other", "account"]

        # 1. Get raw data using simplified queries
        params = {"start_date": start_date, "end_date": end_date, "account_codes": tuple(account_codes)}

        print(f"🔍 Starting performance attribution calculation for {start_date} to {end_date}")
        print(f"📊 Account codes: {account_codes}")

        # Print SQL queries for manual testing
        print("\n📋 SQL QUERIES FOR MANUAL TESTING:")
        print("=" * 50)
        account_codes_str = "', '".join(account_codes)
        print(f"🏦 Market Value at Start/End Dates:")
        print(f"""SELECT "AsofDate", "AccountCode", SUM("MarketValueAccrued") AS market_value
FROM phw_dev_gold.fact_holdings_all
WHERE "AsofDate" IN ('{start_date.strftime('%Y-%m-%d')}', '{end_date.strftime('%Y-%m-%d')}') 
AND "AccountCode" IN ('{account_codes_str}')
AND "CurrencyCode" = 'CAD'
GROUP BY "AsofDate", "AccountCode"
ORDER BY "AsofDate", "AccountCode";""")

        print(f"\n💱 All Transactions in Period:")
        print(f"""SELECT "TradeDate", "AccountCode", "SecuritySymbol", "TransactionTypeCode", 
       "SettlementAmount", "SettlementCurrency"
FROM phw_dev_gold.fact_transactions
WHERE "TradeDate" BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'
AND "AccountCode" IN ('{account_codes_str}')
ORDER BY "TradeDate", "AccountCode", "TransactionTypeCode";""")

        print(f"\n🌍 FX Rates for Period:")
        print(f"""SELECT "AsofDate", "CurrencyCode", "ExchangeRate"
FROM phw_dev_gold.fx_rate
WHERE "AsofDate" IN ('{start_date.strftime('%Y-%m-%d')}', '{end_date.strftime('%Y-%m-%d')}')
ORDER BY "AsofDate", "CurrencyCode";""")

        print(f"\n📊 Daily Aggregate Net Cash Flow:")
        print(f"""SELECT "AsofDate", "AccountCode", "NetCashflow"
FROM phw_dev_gold.fact_daily_aggregate_values
WHERE "AsofDate" BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'
AND "AccountCode" IN ('{account_codes_str}')
ORDER BY "AsofDate", "AccountCode";""")
        print("=" * 50)

        # Get holdings data
        holdings_data = self.db.execute(queries.GET_HOLDINGS_FOR_ATTRIBUTION, params).fetchall()
        print(f"\n📈 Retrieved {len(holdings_data)} holdings records")

        # Get transaction data
        transactions_data = self.db.execute(queries.GET_TRANSACTIONS_FOR_ATTRIBUTION, params).fetchall()
        print(f"💱 Retrieved {len(transactions_data)} transaction records")

        # Get FX rates
        fx_rates_data = self.db.execute(queries.GET_FX_RATES_FOR_ATTRIBUTION, params).fetchall()
        print(f"💵 Retrieved {len(fx_rates_data)} FX rate records")

        # Get daily aggregate data for net contributions
        daily_agg_data = self.db.execute(queries.GET_DAILY_AGGREGATE_FOR_ATTRIBUTION, params).fetchall()
        print(f"📊 Retrieved {len(daily_agg_data)} daily aggregate records")

        # 2. Process the data in Python for better debugging
        attribution_results = self._calculate_performance_attribution(
            holdings_data, transactions_data, fx_rates_data, daily_agg_data, start_date, end_date, account_codes
        )

        # 3. Build Sankey structure from calculated results
        sankey_data = self._build_sankey_from_attribution(attribution_results, attribution_levels)

        # 4. Build performance summary
        performance_summary = self._build_performance_summary(attribution_results, start_date, end_date, account_codes)

        # 5. Return combined response
        return schemas.PerformanceAttributionResponse(
            perf_summary=performance_summary,
            perf_sankey=schemas.PerformanceSankeyData(nodes=sankey_data.nodes, links=sankey_data.links),
        )

    def _calculate_performance_attribution(
        self, holdings_data, transactions_data, fx_rates_data, daily_agg_data, start_date, end_date, account_codes
    ):
        """Calculate performance attribution with detailed logging for debugging"""

        print("\n" + "=" * 100)
        print("🧮 PERFORMANCE ATTRIBUTION CALCULATION")
        print("=" * 100)

        # Create lookup dictionaries for efficient data access
        fx_rates = {}
        for rate in fx_rates_data:
            date_key = rate.as_of_date.strftime("%Y-%m-%d")
            currency = rate.currency_code
            fx_rates[(date_key, currency)] = float(rate.exchange_rate)

        # Separate holdings by date
        start_holdings = {}
        end_holdings = {}

        for holding in holdings_data:
            security_code = holding.security_code
            date_str = holding.as_of_date.strftime("%Y-%m-%d")

            if date_str == start_date.strftime("%Y-%m-%d"):
                start_holdings[security_code] = holding
            elif date_str == end_date.strftime("%Y-%m-%d"):
                end_holdings[security_code] = holding

        print(f"📊 Start date holdings: {len(start_holdings)} securities")
        print(f"📊 End date holdings: {len(end_holdings)} securities")

        # Show holdings breakdown by account
        print(f"\n📊 HOLDINGS BREAKDOWN BY ACCOUNT:")
        print("-" * 40)
        account_start_mva = {}
        account_end_mva = {}
        
        for security_code, holding in start_holdings.items():
            account = holding.account_code
            if account not in account_start_mva:
                account_start_mva[account] = Decimal("0")
            account_start_mva[account] += Decimal(str(holding.market_value_accrued or 0))
            
        for security_code, holding in end_holdings.items():
            account = holding.account_code
            if account not in account_end_mva:
                account_end_mva[account] = Decimal("0")
            account_end_mva[account] += Decimal(str(holding.market_value_accrued or 0))

        for account in sorted(set(list(account_start_mva.keys()) + list(account_end_mva.keys()))):
            start_val = account_start_mva.get(account, Decimal("0"))
            end_val = account_end_mva.get(account, Decimal("0"))
            print(f"  🏦 {account}: Start ${start_val:,.2f} → End ${end_val:,.2f}")

        # Calculate market values
        start_mva = sum(Decimal(str(h.market_value_accrued or 0)) for h in start_holdings.values())
        end_mva = sum(Decimal(str(h.market_value_accrued or 0)) for h in end_holdings.values())

        print(f"\n💰 TOTAL Start MVA: ${start_mva:,.2f} CAD")
        print(f"💰 TOTAL End MVA: ${end_mva:,.2f} CAD")

        # Calculate net contributions from daily aggregate data
        net_contribution = sum(Decimal(str(daily.net_cashflow or 0)) for daily in daily_agg_data)
        print(f"\n💱 NET CONTRIBUTION CALCULATION:")
        print("-" * 35)
        print(f"   Net Contribution = Sum of daily net cash flows")
        print(f"   This includes cash transfers in/out of accounts")
        print(f"   (TSI, TSO, TCI, TCO, etc. - multiplier transactions)")
        account_contributions = {}
        for daily in daily_agg_data:
            account = daily.account_code
            if account not in account_contributions:
                account_contributions[account] = Decimal("0")
            account_contributions[account] += Decimal(str(daily.net_cashflow or 0))
            
        for account, contrib in account_contributions.items():
            print(f"   🏦 {account}: ${contrib:,.2f}")
        print(f"💱 TOTAL Net Contribution: ${net_contribution:,.2f} CAD")

        # Calculate total gain/loss
        total_gain_loss = end_mva - start_mva - net_contribution
        print(f"📈 Total Gain/Loss: ${total_gain_loss:,.2f} CAD")

        # Process transactions and categorize them
        income_total, fees_total, security_contributions = self._process_transactions(
            transactions_data, fx_rates, start_date, end_date
        )

        print(f"💵 Total Income: ${income_total:,.2f} CAD")
        print(f"💸 Total Fees: ${fees_total:,.2f} CAD")

        # Calculate FX gains for each security
        fx_gains = self._calculate_fx_gains(start_holdings, end_holdings, fx_rates, start_date, end_date)

        fx_total = sum(fx_gains.values())
        print(f"🌍 Total FX Gain/Loss: ${fx_total:,.2f} CAD")

        # Calculate appreciation (residual)
        appreciation_total = total_gain_loss - income_total - fees_total - fx_total
        print(f"📊 Market Appreciation: ${appreciation_total:,.2f} CAD")

        print("\n📊 MARKET APPRECIATION CALCULATION:")
        print("-" * 40)
        print(f"📈 Market Appreciation is calculated as the residual:")
        print(f"   Market Appreciation = Total Gain/Loss - Income - Fees - FX Gains")
        print(f"   ${appreciation_total:,.2f} = ${total_gain_loss:,.2f} - ${income_total:,.2f} - ${fees_total:,.2f} - ${fx_total:,.2f}")
        print(f"   This represents the change in security prices (in local currency)")
        print(f"   after removing the effects of:")
        print(f"   • Income/dividends received (${income_total:,.2f})")
        print(f"   • Fees paid (${fees_total:,.2f})")
        print(f"   • Currency fluctuation impact (${fx_total:,.2f})")

        # Calculate "other" (should be close to zero with good attribution)
        other_total = Decimal("0")  # This would capture any unexplained differences
        print(f"❓ Other/Unexplained: ${other_total:,.2f} CAD")

        print("=" * 60)

        return {
            "start_mva": start_mva,
            "end_mva": end_mva,
            "net_contribution": net_contribution,
            "total_gain_loss": total_gain_loss,
            "income_total": income_total,
            "fees_total": fees_total,
            "fx_total": fx_total,
            "appreciation_total": appreciation_total,
            "other_total": other_total,
            "fx_gains_by_security": fx_gains,
            "security_contributions": security_contributions,
            "account_attributions": self._calculate_account_attributions(
                holdings_data, transactions_data, fx_rates_data, daily_agg_data, start_date, end_date, account_codes, appreciation_total
            ),
        }

    def _process_transactions(self, transactions_data, fx_rates, start_date, end_date):
        """Process transactions and categorize them into income, fees, and contributions"""

        print("\n💱 PROCESSING TRANSACTIONS BY ACCOUNT")
        print("-" * 40)

        # Define transaction type categories based on transaction_types.csv
        # Only transactions with a multiplier value (1 or -1) affect net contribution/cash flow

        # Income types (part of investment gains, not cash flow)
        income_types = [
            "CDV",  # Cash Dividend/ Dividend Income
            "DVI",  # Dividend Income
            "SDV",  # Stock Dividend (Tax-Free)
            "INT",  # Interest Income
            "FNI",  # Foreign Income
            "IPS",  # Interest from Cash
            "DRI",  # Dividend Distribution Reinvestment
            "SDT",  # Stock Dividend (Taxable)
            "GRI",  # Capital Gain Distribution Reinvestment
            "FRI",  # Foreign Income Distribution Reinvestment
            "IRI",  # Interest Distribution Reinvestment
            "CGR",  # Capital Gain Reinvestment
            "DVR",  # Dividend Reinvestment
            "FIR",  # Foreign Income Reinvestment
            "FID",  # Foreign Income Distribution
            "IIR",  # Interest Reinvestment
            "IID",  # Interest Distribution
            "INR",  # Income Reinvestment
            "IND",  # Income Distribution
            "MAT",  # Maturity
        ]

        # Fees (typically have no multiplier, so don't affect net contribution)
        fee_types = ["MFE", "FEE", "ADM", "EXP", "AFE", "TFE", "VFE", "LFE", "PFE", "RDF", "RFE", "CDT", "CFE", "CMF"]

        # Cash flow transactions with explicit multipliers from transaction_types.csv
        # These affect Net Contribution, NOT income
        cash_in_types = ["CCR", "CRD", "SRD", "TCI", "TSI"]  # Multiplier = 1 (cash/security in)
        cash_out_types = [
            "CDR",
            "CWD",
            "SWD",
            "TCO",
            "TSO",
        ]  # Multiplier = -1 (cash/security out)

        # Buy/Sell transactions (JSL, JBY) - these don't affect net contribution as they're just conversions
        trading_types = ["JSL", "JBY"]  # These convert between cash and securities, net effect = 0

        income_total = Decimal("0")
        fees_total = Decimal("0")
        security_contributions = {}

        print(f"📋 Transaction Categories:")
        print(f"  💰 Income (part of gains): {income_types}")
        print(f"  💸 Fees: {fee_types}")
        print(f"  📈 Cash In (Net Contribution +): {cash_in_types}")
        print(f"  📉 Cash Out (Net Contribution -): {cash_out_types}")
        print(f"  🔄 Trading (No net contribution): {trading_types}")
        print()

        for txn in transactions_data:
            # Convert transaction amount to CAD
            amount_cad = self._convert_to_cad(txn.settlement_amount, txn.settlement_currency, txn.trade_date, fx_rates)

            # Categorize transaction based on transaction_types.csv multiplier values
            if txn.transaction_type_code in income_types:
                income_total += Decimal(str(abs(amount_cad)))
                print(f"  � Income: [{txn.account_code}] {txn.security_symbol} {txn.transaction_type_code} ${amount_cad:,.2f}")

            elif txn.transaction_type_code in fee_types and amount_cad < 0:
                fees_total += Decimal(str(abs(amount_cad)))
                print(f"  💸 Fee: [{txn.account_code}] {txn.security_symbol} {txn.transaction_type_code} ${abs(amount_cad):,.2f}")

            elif txn.transaction_type_code in cash_in_types:
                # Transactions with multiplier = 1 (positive cash flow) - affects Net Contribution
                security_code = txn.security_code
                if security_code not in security_contributions:
                    security_contributions[security_code] = Decimal("0")
                security_contributions[security_code] += Decimal(str(abs(amount_cad)))
                print(f"  � Cash In (Net Contrib): [{txn.account_code}] {txn.security_symbol} {txn.transaction_type_code} ${abs(amount_cad):,.2f}")

            elif txn.transaction_type_code in cash_out_types:
                # Transactions with multiplier = -1 (negative cash flow) - affects Net Contribution
                security_code = txn.security_code
                if security_code not in security_contributions:
                    security_contributions[security_code] = Decimal("0")
                security_contributions[security_code] -= Decimal(str(abs(amount_cad)))
                print(f"  � Cash Out (Net Contrib): [{txn.account_code}] {txn.security_symbol} {txn.transaction_type_code} ${-abs(amount_cad):,.2f}")

            elif txn.transaction_type_code in trading_types:
                # Buy/Sell transactions - no net contribution impact
                print(f"  🔄 Trading (No Net Impact): [{txn.account_code}] {txn.security_symbol} {txn.transaction_type_code} ${amount_cad:,.2f}")

            else:
                # Unclassified transaction - log for investigation
                print(f"  ❓ Unclassified: [{txn.account_code}] {txn.security_symbol} {txn.transaction_type_code} ${amount_cad:,.2f}")

        return income_total, fees_total, security_contributions

    def _convert_to_cad(self, amount, currency, date, fx_rates):
        """Convert amount to CAD using FX rates"""
        if currency == "CAD" or amount is None:
            return float(amount or 0)

        date_key = date.strftime("%Y-%m-%d")
        rate_key = (date_key, currency)

        if rate_key in fx_rates:
            return float(amount) * fx_rates[rate_key]
        else:
            print(f"⚠️  No FX rate found for {currency} on {date_key}, using amount as-is")
            return float(amount or 0)

    def _calculate_fx_gains(self, start_holdings, end_holdings, fx_rates, start_date, end_date):
        """Calculate FX gains for each security"""

        print("\n🌍 CALCULATING FX GAINS")
        print("-" * 30)
        print("📋 FX Calculation Method:")
        print("   1. For each non-CAD security, get start and end positions")
        print("   2. Convert market values to local currency using FX rates")
        print("   3. Calculate average local position = (start_local + end_local) / 2")
        print("   4. FX Gain = avg_local_position × (end_fx_rate - start_fx_rate)")
        print("   5. This captures currency impact on existing positions")
        print()

        fx_gains = {}

        # Get all securities that had holdings
        all_securities = set(start_holdings.keys()) | set(end_holdings.keys())

        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        for security_code in all_securities:
            start_holding = start_holdings.get(security_code)
            end_holding = end_holdings.get(security_code)

            # Skip CAD securities (no FX impact)
            currency = None
            account_code = None
            if start_holding:
                currency = start_holding.security_currency_code
                account_code = start_holding.account_code
            elif end_holding:
                currency = end_holding.security_currency_code
                account_code = end_holding.account_code

            if currency == "CAD" or currency is None:
                fx_gains[security_code] = Decimal("0")
                continue

            # Get FX rates for start and end dates
            start_fx_key = (start_date_str, currency)
            end_fx_key = (end_date_str, currency)

            start_fx_rate = fx_rates.get(start_fx_key)
            end_fx_rate = fx_rates.get(end_fx_key)

            if start_fx_rate is None or end_fx_rate is None:
                print(f"⚠️  Missing FX rates for {security_code} ({currency}) in account {account_code}")
                fx_gains[security_code] = Decimal("0")
                continue

            # Calculate FX gain: (end_value_local / end_fx - start_value_local / start_fx) * (end_fx - start_fx)
            start_value = Decimal(str(start_holding.market_value_accrued if start_holding else 0))
            end_value = Decimal(str(end_holding.market_value_accrued if end_holding else 0))
            start_shares = Decimal(str(start_holding.quantity if start_holding else 0))
            end_shares = Decimal(str(end_holding.quantity if end_holding else 0))

            if start_fx_rate != 0 and end_fx_rate != 0:
                start_local = start_value / Decimal(str(start_fx_rate))
                end_local = end_value / Decimal(str(end_fx_rate))
                fx_change = Decimal(str(end_fx_rate - start_fx_rate))

                # This is a simplified FX calculation - may need refinement
                avg_local_position = (start_local + end_local) / 2
                fx_gain = avg_local_position * fx_change

                fx_gains[security_code] = fx_gain

                if abs(fx_gain) > Decimal("0.01"):  # Only log meaningful amounts
                    symbol = (
                        start_holding.security_symbol
                        if start_holding
                        else end_holding.security_symbol if end_holding else security_code
                    )
                    print(f"  💱 [{account_code}] {symbol} ({currency}): ${fx_gain:,.2f}")
                    print(f"      Start: {start_shares:,.0f} shares @ ${start_value:,.2f} CAD (FX: {start_fx_rate:.4f})")
                    print(f"      End:   {end_shares:,.0f} shares @ ${end_value:,.2f} CAD (FX: {end_fx_rate:.4f})")
                    print(f"      Local Start: ${start_local:,.2f} {currency}")
                    print(f"      Local End:   ${end_local:,.2f} {currency}")
                    print(f"      Avg Local:   ${avg_local_position:,.2f} {currency}")
                    print(f"      FX Change: {start_fx_rate:.4f} → {end_fx_rate:.4f} = {fx_change:+.4f}")
                    print(f"      Calculation: ${avg_local_position:,.2f} × {fx_change:+.4f} = ${fx_gain:,.2f}")
                    print()
            else:
                fx_gains[security_code] = Decimal("0")

        return fx_gains

    def _calculate_account_attributions(
        self, holdings_data, transactions_data, fx_rates_data, daily_agg_data, start_date, end_date, account_codes, global_appreciation_total
    ):
        """Calculate attribution breakdown by account for more detailed analysis"""

        print("\n🏦 CALCULATING ACCOUNT-LEVEL ATTRIBUTIONS")
        print("-" * 40)

        account_attributions = {}

        # Initialize account attribution structure
        for account_code in account_codes:
            account_attributions[account_code] = {
                "start_mva": Decimal("0"),
                "end_mva": Decimal("0"),
                "net_contribution": Decimal("0"),
                "total_gain_loss": Decimal("0"),
                "fx_gain": Decimal("0"),
                "income": Decimal("0"),
                "fees": Decimal("0"),
                "appreciation": Decimal("0"),
                "other": Decimal("0"),
            }

        # Create FX rates lookup
        fx_rates = {}
        for rate in fx_rates_data:
            date_key = rate.as_of_date.strftime("%Y-%m-%d")
            currency = rate.currency_code
            fx_rates[(date_key, currency)] = float(rate.exchange_rate)

        # Process holdings by account
        for holding in holdings_data:
            account_code = holding.account_code
            if account_code not in account_attributions:
                continue

            date_str = holding.as_of_date.strftime("%Y-%m-%d")
            market_value = Decimal(str(holding.market_value_accrued or 0))

            if date_str == start_date.strftime("%Y-%m-%d"):
                account_attributions[account_code]["start_mva"] += market_value
            elif date_str == end_date.strftime("%Y-%m-%d"):
                account_attributions[account_code]["end_mva"] += market_value

        # Process daily aggregate data by account
        for daily in daily_agg_data:
            account_code = daily.account_code
            if account_code in account_attributions:
                account_attributions[account_code]["net_contribution"] += Decimal(str(daily.net_cashflow or 0))

        # Calculate total gain/loss by account
        for account_code in account_attributions:
            attr = account_attributions[account_code]
            attr["total_gain_loss"] = attr["end_mva"] - attr["start_mva"] - attr["net_contribution"]

        # Process transactions by account using the same classification as main calculation
        income_types = [
            "CDV",
            "DVI",
            "SDV",
            "INT",
            "FNI",
            "IPS",
            "DRI",
            "SDT",
            "GRI",
            "FRI",
            "IRI",
            "CGR",
            "DVR",
            "FIR",
            "FID",
            "IIR",
            "IID",
            "INR",
            "IND",
            "MAT",
        ]
        fee_types = ["MFE", "FEE", "ADM", "EXP", "AFE", "TFE", "VFE", "LFE", "PFE", "RDF", "RFE", "CDT", "CFE", "CMF"]

        for transaction in transactions_data:
            account_code = transaction.account_code
            if account_code not in account_attributions:
                continue

            amount = Decimal(str(transaction.settlement_amount or 0))
            trans_type = transaction.transaction_type_code

            # Convert to CAD if needed (using the same method as global calculation)
            amount_cad = self._convert_to_cad(transaction.settlement_amount, transaction.settlement_currency, transaction.trade_date, fx_rates)
            amount = Decimal(str(amount_cad))

            # Categorize transaction (using the same logic as global calculation)
            if trans_type in income_types:
                account_attributions[account_code]["income"] += Decimal(str(abs(amount_cad)))
                print(f"    📊 Account Income: [{account_code}] {trans_type} ${abs(amount_cad):,.2f}")
            elif trans_type in fee_types and amount_cad < 0:
                account_attributions[account_code]["fees"] -= Decimal(str(abs(amount_cad)))  # Keep as negative like global calc
                print(f"    📊 Account Fee: [{account_code}] {trans_type} ${-abs(amount_cad):,.2f}")

        # Calculate FX gains by account - track security-by-security for each account
        print("\n🌍 CALCULATING FX GAINS BY ACCOUNT")
        print("-" * 40)

        # Group holdings by account and security for FX calculation
        account_security_holdings = {}
        for holding in holdings_data:
            account_code = holding.account_code
            security_code = holding.security_code
            date_str = holding.as_of_date.strftime("%Y-%m-%d")

            if account_code not in account_security_holdings:
                account_security_holdings[account_code] = {}

            if security_code not in account_security_holdings[account_code]:
                account_security_holdings[account_code][security_code] = {}

            account_security_holdings[account_code][security_code][date_str] = holding

        # Calculate FX gains for each account's holdings
        for account_code in account_codes:
            if account_code not in account_attributions:
                continue

            account_fx_gain = Decimal("0")

            if account_code in account_security_holdings:
                for security_code, security_holdings in account_security_holdings[account_code].items():
                    start_date_str = start_date.strftime("%Y-%m-%d")
                    end_date_str = end_date.strftime("%Y-%m-%d")

                    start_holding = security_holdings.get(start_date_str)
                    end_holding = security_holdings.get(end_date_str)

                    # Skip if we don't have both start and end holdings
                    if not start_holding or not end_holding:
                        continue

                    # Skip CAD securities (no FX impact)
                    security_currency = start_holding.security_currency_code
                    if security_currency == "CAD":
                        continue

                    # Get FX rates for start and end dates
                    start_fx_key = (start_date_str, security_currency)
                    end_fx_key = (end_date_str, security_currency)

                    if start_fx_key not in fx_rates or end_fx_key not in fx_rates:
                        print(f"  ⚠️  Missing FX rates for {security_currency} in {account_code}")
                        continue

                    start_fx_rate = fx_rates[start_fx_key]
                    end_fx_rate = fx_rates[end_fx_key]

                    # Calculate FX gain for this security in this account
                    start_value = Decimal(str(start_holding.market_value_accrued or 0))
                    end_value = Decimal(str(end_holding.market_value_accrued or 0))

                    if start_value > 0 and end_value > 0:
                        # Convert to local currency amounts
                        start_local = start_value / Decimal(str(start_fx_rate))
                        end_local = end_value / Decimal(str(end_fx_rate))
                        fx_change = Decimal(str(end_fx_rate - start_fx_rate))

                        # Calculate FX impact (simplified - using average position)
                        avg_local_position = (start_local + end_local) / 2
                        security_fx_gain = avg_local_position * fx_change

                        account_fx_gain += security_fx_gain

                        if abs(security_fx_gain) > Decimal("1.00"):  # Only log meaningful amounts
                            symbol = start_holding.security_symbol or security_code
                            print(
                                f"  💱 {account_code} - {symbol}: ${security_fx_gain:,.2f} (FX: {start_fx_rate:.4f} → {end_fx_rate:.4f})"
                            )

            account_attributions[account_code]["fx_gain"] = account_fx_gain
            print(f"🏦 {account_code} Total FX Gain: ${account_fx_gain:,.2f}")

        # Calculate market appreciation as residual for each account
        # IMPORTANT: Account appreciations should be proportional shares of the global appreciation,
        # not independent residuals for each account
        global_appreciation = global_appreciation_total  # This is the correct global appreciation
        total_account_gain_loss = sum(attr["total_gain_loss"] for attr in account_attributions.values())
        
        for account_code in account_attributions:
            attr = account_attributions[account_code]

            # Calculate account's proportional share of global appreciation
            # based on its share of total gain/loss
            if total_account_gain_loss != 0:
                account_proportion = attr["total_gain_loss"] / total_account_gain_loss
                attr["appreciation"] = global_appreciation * account_proportion
            else:
                attr["appreciation"] = Decimal("0")

            print(
                f"🏦 {account_code}: Total G/L ${attr['total_gain_loss']:,.2f} "
                f"(Income: ${attr['income']:,.2f}, Fees: ${attr['fees']:,.2f}, "
                f"FX: ${attr['fx_gain']:,.2f}, Appreciation: ${attr['appreciation']:,.2f})"
            )

        print(f"\n📊 FINAL ACCOUNT TOTALS FOR SANKEY:")
        total_account_income_check = sum(attr["income"] for attr in account_attributions.values())
        total_account_fees_check = sum(attr["fees"] for attr in account_attributions.values())
        total_account_fx_check = sum(attr["fx_gain"] for attr in account_attributions.values())
        total_account_appreciation_check = sum(attr["appreciation"] for attr in account_attributions.values())
        
        print(f"  💰 Sum of Account Income: ${total_account_income_check:,.2f}")
        print(f"  💸 Sum of Account Fees: ${total_account_fees_check:,.2f}")
        print(f"  🌍 Sum of Account FX: ${total_account_fx_check:,.2f}")
        print(f"  📊 Sum of Account Appreciation: ${total_account_appreciation_check:,.2f}")
        print(f"  ⚠️  These totals will be compared with global totals in Sankey validation")

        return account_attributions

    def _build_performance_summary(self, results, start_date, end_date, account_codes):
        """Build performance summary from attribution results"""

        # Extract results
        start_mva = float(results["start_mva"])
        end_mva = float(results["end_mva"])
        net_contribution = float(results["net_contribution"])
        total_gain_loss = float(results["total_gain_loss"])
        income_total = float(results["income_total"])
        fees_total = float(results["fees_total"])
        fx_total = float(results["fx_total"])
        appreciation_total = float(results["appreciation_total"])
        other_total = float(results["other_total"])

        # Calculate total gains and losses
        total_gains = 0.0
        total_losses = 0.0

        if fx_total > 0:
            total_gains += fx_total
        else:
            total_losses += abs(fx_total)

        if income_total > 0:
            total_gains += income_total
        else:
            total_losses += abs(income_total)

        if fees_total < 0:  # fees are typically negative
            total_losses += abs(fees_total)
        else:
            total_gains += fees_total

        if appreciation_total > 0:
            total_gains += appreciation_total
        else:
            total_losses += abs(appreciation_total)

        if other_total > 0:
            total_gains += other_total
        else:
            total_losses += abs(other_total)

        return schemas.PerformanceSummary(
            start_mva=start_mva,
            end_mva=end_mva,
            net_contribution=net_contribution,
            total_gain_loss=total_gain_loss,
            total_gains=total_gains,
            total_losses=total_losses,
            income_total=income_total,
            fees_total=fees_total,
            fx_total=fx_total,
            appreciation_total=appreciation_total,
            other_total=other_total,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            account_codes=account_codes,
        )

    def _build_sankey_from_attribution(self, results, attribution_levels):
        """
        Build Sankey diagram focused on gain/loss attribution with account breakdown.
        Structure: Total Gain/Loss → Gains/Losses → Attribution Categories → Accounts
        """

        print("\n🏗️  BUILDING FOCUSED SANKEY DIAGRAM")
        print("-" * 40)

        # Extract results
        total_gain_loss = results["total_gain_loss"]
        income_total = results["income_total"]
        fees_total = results["fees_total"]
        fx_total = results["fx_total"]
        appreciation_total = results["appreciation_total"]
        other_total = results["other_total"]
        account_attributions = results.get("account_attributions", {})

        nodes = []
        links = []

        # Level 1: Total Gain/Loss as the root
        print(f"📊 Level 1: Root - Total Gain/Loss")
        nodes.append(
            schemas.PerformanceNode(label=f"Total Gain/Loss (${total_gain_loss:,.0f})", category="gain_loss")
        )  # 0

        # Level 2: Separate Gains and Losses
        print(f"📊 Level 2: Gains vs Losses Breakdown")
        gains_total = Decimal("0")
        losses_total = Decimal("0")

        # Categorize each component as gain or loss
        if fx_total > 0:
            gains_total += fx_total
        elif fx_total < 0:
            losses_total += abs(fx_total)

        if income_total > 0:
            gains_total += income_total
        elif income_total < 0:
            losses_total += abs(income_total)

        if fees_total < 0:  # fees are typically negative
            losses_total += abs(fees_total)
        elif fees_total > 0:
            gains_total += fees_total

        if appreciation_total > 0:
            gains_total += appreciation_total
        elif appreciation_total < 0:
            losses_total += abs(appreciation_total)

        if other_total > 0:
            gains_total += other_total
        elif other_total < 0:
            losses_total += abs(other_total)

        current_node_idx = 1

        gains_node_idx = None
        losses_node_idx = None

        if gains_total > 0:
            gains_node_idx = current_node_idx
            nodes.append(schemas.PerformanceNode(label=f"Total Gains (+${gains_total:,.0f})", category="gains"))
            links.append(
                schemas.PerformanceLink(
                    source=0, target=gains_node_idx, value=float(gains_total), attribution_type="gains"
                )
            )
            current_node_idx += 1
            print(f"✅ Added Gains node: ${gains_total:,.2f}")

        if losses_total > 0:
            losses_node_idx = current_node_idx
            nodes.append(schemas.PerformanceNode(label=f"Total Losses (-${losses_total:,.0f})", category="losses"))
            links.append(
                schemas.PerformanceLink(
                    source=0, target=losses_node_idx, value=float(losses_total), attribution_type="losses"
                )
            )
            current_node_idx += 1
            print(f"❌ Added Losses node: ${losses_total:,.2f}")

        # Level 3: Attribution Categories
        print(f"📊 Level 3: Attribution Categories")
        attribution_node_map = {}

        # GAINS breakdown
        if gains_total > 0 and gains_node_idx is not None:
            print("✅ Breaking down GAINS:")

            # Market Appreciation (positive)
            if appreciation_total > 0:
                node_idx = current_node_idx
                attribution_node_map["appreciation_gain"] = node_idx
                nodes.append(
                    schemas.PerformanceNode(
                        label=f"Market Appreciation (+${appreciation_total:,.0f})", category="attribution_gain"
                    )
                )
                links.append(
                    schemas.PerformanceLink(
                        source=gains_node_idx,
                        target=node_idx,
                        value=float(appreciation_total),
                        attribution_type="appreciation_gain",
                    )
                )
                print(f"  📈 Market Appreciation: +${appreciation_total:,.2f}")
                current_node_idx += 1

            # FX Gains (positive)
            if fx_total > 0:
                node_idx = current_node_idx
                attribution_node_map["fx_gain"] = node_idx
                nodes.append(schemas.PerformanceNode(label=f"FX Gain (+${fx_total:,.0f})", category="attribution_gain"))
                links.append(
                    schemas.PerformanceLink(
                        source=gains_node_idx, target=node_idx, value=float(fx_total), attribution_type="fx_gain"
                    )
                )
                print(f"  🌍 FX Gain: +${fx_total:,.2f}")
                current_node_idx += 1

            # Income/Dividends (positive)
            if income_total > 0:
                node_idx = current_node_idx
                attribution_node_map["income_gain"] = node_idx
                nodes.append(
                    schemas.PerformanceNode(
                        label=f"Income/Dividends (+${income_total:,.0f})", category="attribution_gain"
                    )
                )
                links.append(
                    schemas.PerformanceLink(
                        source=gains_node_idx,
                        target=node_idx,
                        value=float(income_total),
                        attribution_type="dividend_gain",
                    )
                )
                print(f"  💵 Income/Dividends: +${income_total:,.2f}")
                current_node_idx += 1

            # Other Gains (positive)
            if other_total > 0:
                node_idx = current_node_idx
                attribution_node_map["other_gain"] = node_idx
                nodes.append(
                    schemas.PerformanceNode(label=f"Other Gains (+${other_total:,.0f})", category="attribution_gain")
                )
                links.append(
                    schemas.PerformanceLink(
                        source=gains_node_idx, target=node_idx, value=float(other_total), attribution_type="other_gain"
                    )
                )
                print(f"  ❓ Other Gains: +${other_total:,.2f}")
                current_node_idx += 1

        # LOSSES breakdown
        if losses_total > 0 and losses_node_idx is not None:
            print("❌ Breaking down LOSSES:")

            # Market Depreciation (negative appreciation)
            if appreciation_total < 0:
                node_idx = current_node_idx
                attribution_node_map["appreciation_loss"] = node_idx
                nodes.append(
                    schemas.PerformanceNode(
                        label=f"Market Depreciation (-${abs(appreciation_total):,.0f})", category="attribution_loss"
                    )
                )
                links.append(
                    schemas.PerformanceLink(
                        source=losses_node_idx,
                        target=node_idx,
                        value=float(abs(appreciation_total)),
                        attribution_type="appreciation_loss",
                    )
                )
                print(f"  📉 Market Depreciation: -${abs(appreciation_total):,.2f}")
                current_node_idx += 1

            # FX Losses (negative fx)
            if fx_total < 0:
                node_idx = current_node_idx
                attribution_node_map["fx_loss"] = node_idx
                nodes.append(
                    schemas.PerformanceNode(label=f"FX Loss (-${abs(fx_total):,.0f})", category="attribution_loss")
                )
                links.append(
                    schemas.PerformanceLink(
                        source=losses_node_idx, target=node_idx, value=float(abs(fx_total)), attribution_type="fx_loss"
                    )
                )
                print(f"  🌍 FX Loss: -${abs(fx_total):,.2f}")
                current_node_idx += 1

            # Fees/Expenses (negative)
            if fees_total < 0:
                node_idx = current_node_idx
                attribution_node_map["fees_loss"] = node_idx
                nodes.append(
                    schemas.PerformanceNode(
                        label=f"Fees/Expenses (-${abs(fees_total):,.0f})", category="attribution_loss"
                    )
                )
                links.append(
                    schemas.PerformanceLink(
                        source=losses_node_idx,
                        target=node_idx,
                        value=float(abs(fees_total)),
                        attribution_type="fee_loss",
                    )
                )
                print(f"  💸 Fees/Expenses: -${abs(fees_total):,.2f}")
                current_node_idx += 1

            # Other Losses (negative)
            if other_total < 0:
                node_idx = current_node_idx
                attribution_node_map["other_loss"] = node_idx
                nodes.append(
                    schemas.PerformanceNode(
                        label=f"Other Losses (-${abs(other_total):,.0f})", category="attribution_loss"
                    )
                )
                links.append(
                    schemas.PerformanceLink(
                        source=losses_node_idx,
                        target=node_idx,
                        value=float(abs(other_total)),
                        attribution_type="other_loss",
                    )
                )
                print(f"  ❓ Other Losses: -${abs(other_total):,.2f}")
                current_node_idx += 1

        # Level 4: Account Breakdown
        if account_attributions and "account" in attribution_levels:
            print(f"📊 Level 4: Account Breakdown")
            
            # First, calculate totals for validation
            total_account_income = sum(max(Decimal("0"), attr["income"]) for attr in account_attributions.values())
            total_account_fees = sum(min(Decimal("0"), attr["fees"]) for attr in account_attributions.values())
            total_account_fx_gains = sum(attr["fx_gain"] for attr in account_attributions.values() if attr["fx_gain"] > 0)
            total_account_fx_losses = sum(attr["fx_gain"] for attr in account_attributions.values() if attr["fx_gain"] < 0)
            total_account_appreciation_gains = sum(attr["appreciation"] for attr in account_attributions.values() if attr["appreciation"] > 0)
            total_account_appreciation_losses = sum(attr["appreciation"] for attr in account_attributions.values() if attr["appreciation"] < 0)
            
            print(f"🔍 Account Validation:")
            print(f"   Total Account Income: ${total_account_income:,.2f} vs Global Income: ${income_total:,.2f}")
            print(f"   Total Account Fees: ${total_account_fees:,.2f} vs Global Fees: ${fees_total:,.2f}")
            print(f"   Total Account FX Gains: ${total_account_fx_gains:,.2f}")
            print(f"   Total Account FX Losses: ${total_account_fx_losses:,.2f}")
            print(f"   Global FX Total: ${fx_total:,.2f}")

            for account_code, attr in account_attributions.items():
                account_node_idx = current_node_idx
                account_gain_loss = attr["total_gain_loss"]
                nodes.append(
                    schemas.PerformanceNode(label=f"{account_code} (${account_gain_loss:,.0f})", category="account")
                )

                # Link this account to appropriate attribution categories based on its composition
                # IMPORTANT: Only create links if the account actually contributes to that category
                # and scale the values to ensure proper flow conservation

                # Link to appreciation if this account has market appreciation
                if attr["appreciation"] > 0 and "appreciation_gain" in attribution_node_map and appreciation_total > 0:
                    # Scale the account's appreciation to ensure total flows balance
                    scaled_value = float(attr["appreciation"])
                    links.append(
                        schemas.PerformanceLink(
                            source=attribution_node_map["appreciation_gain"],
                            target=account_node_idx,
                            value=scaled_value,
                            attribution_type="account_appreciation",
                        )
                    )
                    print(f"  📈 {account_code} Appreciation: ${scaled_value:,.2f}")
                elif attr["appreciation"] < 0 and "appreciation_loss" in attribution_node_map and appreciation_total < 0:
                    scaled_value = float(abs(attr["appreciation"]))
                    links.append(
                        schemas.PerformanceLink(
                            source=attribution_node_map["appreciation_loss"],
                            target=account_node_idx,
                            value=scaled_value,
                            attribution_type="account_appreciation",
                        )
                    )
                    print(f"  📉 {account_code} Depreciation: ${scaled_value:,.2f}")

                # Link to income if this account has income
                if attr["income"] > 0 and "income_gain" in attribution_node_map and income_total > 0:
                    # Use actual account income value
                    scaled_value = float(attr["income"])
                    links.append(
                        schemas.PerformanceLink(
                            source=attribution_node_map["income_gain"],
                            target=account_node_idx,
                            value=scaled_value,
                            attribution_type="account_income",
                        )
                    )
                    print(f"  💰 {account_code} Income: ${scaled_value:,.2f}")

                # Link to fees if this account has fees
                if attr["fees"] < 0 and "fees_loss" in attribution_node_map and fees_total < 0:
                    scaled_value = float(abs(attr["fees"]))
                    links.append(
                        schemas.PerformanceLink(
                            source=attribution_node_map["fees_loss"],
                            target=account_node_idx,
                            value=scaled_value,
                            attribution_type="account_fees",
                        )
                    )
                    print(f"  💸 {account_code} Fees: ${scaled_value:,.2f}")

                # Link to FX gains/losses if this account has FX impact
                if attr["fx_gain"] > 0 and "fx_gain" in attribution_node_map:
                    scaled_value = float(attr["fx_gain"])
                    links.append(
                        schemas.PerformanceLink(
                            source=attribution_node_map["fx_gain"],
                            target=account_node_idx,
                            value=scaled_value,
                            attribution_type="account_fx",
                        )
                    )
                    print(f"  🌍 {account_code} FX Gain: ${scaled_value:,.2f}")
                elif attr["fx_gain"] < 0 and "fx_loss" in attribution_node_map:
                    scaled_value = float(abs(attr["fx_gain"]))
                    links.append(
                        schemas.PerformanceLink(
                            source=attribution_node_map["fx_loss"],
                            target=account_node_idx,
                            value=scaled_value,
                            attribution_type="account_fx",
                        )
                    )
                    print(f"  🌍 {account_code} FX Loss: ${scaled_value:,.2f}")

                print(f"🏦 Added account {account_code}: ${account_gain_loss:,.2f}")
                current_node_idx += 1

        print(f"📊 Created {len(nodes)} nodes and {len(links)} links")
        print(f"💰 Summary - Gains: ${gains_total:,.2f}, Losses: ${losses_total:,.2f}")
        return schemas.PerformanceSankeyResponse(nodes=nodes, links=links)
