
import yfinance as yf
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from . import models, schemas

class BenchmarkService:
    def __init__(self, db: Session):
        self.db = db

    def get_benchmark_performance(
        self,
        account_codes: list[str],
        benchmark_symbols: list[str],
        start_date: str,
        end_date: str,
    ):
        # 1. Get portfolio cash flows
        cash_flows = self._get_portfolio_cash_flows(account_codes, start_date, end_date)

        # 2. Get portfolio daily values
        portfolio_values = self._get_portfolio_daily_values(account_codes, start_date, end_date)

        # 3. Calculate benchmark performance for each benchmark
        benchmark_performance_data = {}
        for symbol in benchmark_symbols:
            benchmark_data = self._get_benchmark_data(symbol, start_date, end_date)
            if benchmark_data:
                benchmark_performance_data[symbol] = self._calculate_benchmark_value(
                    cash_flows, benchmark_data, start_date, end_date
                )

        return {
            "portfolio_values": portfolio_values,
            "benchmark_performance": benchmark_performance_data,
        }

    def _get_portfolio_cash_flows(self, account_codes: list[str], start_date: str, end_date: str) -> dict:
        cash_flow_transactions = (
            self.db.query(models.FactTransaction)
            .filter(
                models.FactTransaction.AccountCode.in_(account_codes),
                models.FactTransaction.TradeDate >= start_date,
                models.FactTransaction.TradeDate <= end_date,
                models.FactTransaction.TransactionTypeCode.in_(["CRD", "TCI", "CWD", "TCO"]),
            )
            .all()
        )

        cash_flows = {}
        for tx in cash_flow_transactions:
            date_str = tx.TradeDate.strftime("%Y-%m-%d")
            amount = float(tx.SettlementAmount)
            if tx.TransactionTypeCode in ["CWD", "TCO"]:
                amount *= -1
            
            if date_str not in cash_flows:
                cash_flows[date_str] = 0
            cash_flows[date_str] += amount
            
        return cash_flows

    def _get_portfolio_daily_values(self, account_codes: list[str], start_date: str, end_date: str) -> dict:
        from sqlalchemy import func

        daily_values_query = (
            self.db.query(
                models.FactHoldingsAll.AsofDate,
                func.sum(models.FactHoldingsAll.MarketValueAccrued).label("total_mva"),
            )
            .filter(
                models.FactHoldingsAll.AccountCode.in_(account_codes),
                models.FactHoldingsAll.AsofDate >= start_date,
                models.FactHoldingsAll.AsofDate <= end_date,
            )
            .group_by(models.FactHoldingsAll.AsofDate)
            .order_by(models.FactHoldingsAll.AsofDate)
            .all()
        )

        portfolio_values = {}
        for daily_value in daily_values_query:
            date_str = daily_value.AsofDate.strftime("%Y-%m-%d")
            portfolio_values[date_str] = float(daily_value.total_mva)

        return portfolio_values


    def _get_benchmark_data(self, benchmark_symbol: str, start_date: str, end_date: str) -> dict:
        proxy_map = {
            "XEQT.TO": "VTI"
        }

        end_date_plus_one = (datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        
        try:
            data = yf.download(benchmark_symbol, start=start_date, end=end_date_plus_one)
            if data.empty and benchmark_symbol in proxy_map:
                proxy_symbol = proxy_map[benchmark_symbol]
                data = yf.download(proxy_symbol, start=start_date, end=end_date_plus_one)
        except Exception as e:
            print(f"Error fetching benchmark data for {benchmark_symbol}: {e}")
            return {}
        print(data.columns)
        adj_close_prices = data["Adj Close"].to_dict()
        
        return {date.strftime("%Y-%m-%d"): price for date, price in adj_close_prices.items()}

    def _calculate_benchmark_value(self, cash_flows: dict, benchmark_prices: dict, start_date_str: str, end_date_str: str) -> dict:
        benchmark_value_history = {}
        benchmark_shares = 0.0
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        # Find the first date with a valid price
        first_valid_price_date = None
        for date in (start_date + timedelta(n) for n in range((end_date - start_date).days + 1)):
             if date.strftime("%Y-%m-%d") in benchmark_prices:
                 first_valid_price_date = date
                 break
        
        if not first_valid_price_date:
            return {} # No price data available for the whole period

        # Start calculation from the first day a price is available
        start_date = first_valid_price_date

        for date in (start_date + timedelta(n) for n in range((end_date - start_date).days + 1)):
            current_date_str = date.strftime("%Y-%m-%d")
            
            price_today = benchmark_prices.get(current_date_str)
            
            if price_today is None:
                if benchmark_value_history:
                    last_date = (date - timedelta(days=1)).strftime("%Y-%m-%d")
                    benchmark_value_history[current_date_str] = benchmark_value_history.get(last_date)
                continue

            cash_flow = cash_flows.get(current_date_str, 0)
            if cash_flow != 0:
                shares_to_add = cash_flow / price_today
                benchmark_shares += shares_to_add
            
            current_benchmark_value = benchmark_shares * price_today
            benchmark_value_history[current_date_str] = current_benchmark_value

        return benchmark_value_history
