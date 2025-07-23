from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, Float, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class DimAccount(Base):
    __tablename__ = "dim_accounts"
    __table_args__ = {'schema': 'phw_dev_gold'}
    AccountCode = Column(String, primary_key=True, index=True)
    AccountType = Column(String)
    AccountVisualizationID = Column(String)
    AccountName = Column(String)
    CustodianAccountCode = Column(String)
    CustodianCode = Column(String)
    CustodianName = Column(String)
    OpenDate = Column(Date)
    Country = Column(String)
    ContactAddressLine1 = Column(String)
    Status = Column(String)
    AccountCurrencyCode = Column(String)
    IsRegisteredAccount = Column(String)
    ProcessedDate = Column(Date)
    ProcessedTimestampEST = Column(DateTime)
    rawFile = Column(String)

    holdings = relationship("FactHoldingsAll", back_populates="account")

class DimSecurityMaster(Base):
    __tablename__ = "dim_securitymaster"
    __table_args__ = {'schema': 'phw_dev_gold'}
    secid = Column(String, primary_key=True, index=True)
    security_code = Column(String, unique=True, index=True)
    security_name = Column(String)
    security_symbol = Column(String)
    security_description = Column(String)
    security_type_code = Column(String)
    security_type_description = Column(String)
    sec_status = Column(String)
    security_country = Column(String)
    security_currency_code = Column(String)
    cusip = Column(String)
    sedol = Column(String)
    isin = Column(String)
    bbgid = Column(String)
    asset_class = Column(String)
    asset_class_code = Column(String)
    industry_group = Column(String)
    industry_group_code = Column(String)
    issuer_code = Column(String)
    issuer = Column(String)
    ProcessedDate = Column(Date)
    AssetClassLevel1Name = Column(String)
    AssetClassLevel2Name = Column(String)
    AssetClassLevel3Name = Column(String)
    AssetClassLevel1 = Column(String)
    AssetClassLevel2 = Column(String)
    AssetClassLevel3 = Column(String)
    ProcessedTimestampEST = Column(DateTime)
    rawFile = Column(String)

    holdings = relationship("FactHoldingsAll", back_populates="security")

class DimTransactionType(Base):
    __tablename__ = "dim_transaction_types"
    __table_args__ = {'schema': 'phw_dev_gold'}
    TransactionType = Column(String, primary_key=True, index=True)
    Description = Column(String)
    Taxable = Column(Boolean)
    ProcessedDate = Column(Date)
    ProcessedTimestampEST = Column(DateTime)
    rawFile = Column(String, nullable=False)

class FactAccountRor(Base):
    __tablename__ = "fact_account_ror"
    __table_args__ = {'schema': 'phw_dev_gold'}
    account_code = Column(String, ForeignKey("phw_dev_gold.dim_accounts.AccountCode"), primary_key=True, index=True)
    as_of_date = Column(String)
    mtd = Column(Float)
    lcm = Column(Float)
    qtd = Column(Float)
    lcq = Column(Float)
    ytd = Column(Float)
    l3y = Column(Float)
    l5y = Column(Float)
    l10y = Column(Float)
    itd = Column(Float)

class FactDailyAggregateValue(Base):
    __tablename__ = "fact_daily_aggregate_values"
    __table_args__ = {'schema': 'phw_dev_gold'}
    account_code = Column(String, ForeignKey("phw_dev_gold.dim_accounts.AccountCode"), primary_key=True, index=True)
    as_of_date = Column(Date)
    deposit_local = Column(Numeric)
    withdrawal_local = Column(Numeric)
    net_cashflow_local = Column(Numeric)
    deposit_converted = Column(Numeric)
    withdrawal_converted = Column(Numeric)
    net_cashflow_converted = Column(Numeric)
    market_value_accrued_local = Column(Numeric)
    market_value_accrued_converted = Column(Numeric)
    market_value_accrued_previous_local = Column(Numeric)
    market_value_accrued_previous_converted = Column(Numeric)
    cumulative_cashflow_local = Column(Numeric)
    cumulative_cashflow_converted = Column(Numeric)
    rawFile = Column(String)

class FactDailyAggregateValueSlp(Base):
    __tablename__ = "fact_daily_aggregate_values_slp"
    __table_args__ = {'schema': 'phw_dev_gold'}
    account_code = Column(String, ForeignKey("phw_dev_gold.dim_accounts.AccountCode"), primary_key=True, index=True)
    security_code = Column(String, ForeignKey("phw_dev_gold.dim_securitymaster.security_code"), primary_key=True, index=True)
    as_of_date = Column(Date)
    deposit = Column(Numeric)
    deposit_local = Column(Numeric)
    withdrawal = Column(Numeric)
    withdrawal_local = Column(Numeric)
    net_cashflow_converted = Column(Numeric)
    net_cashflow_local = Column(Numeric)
    cumulative_cashflow_converted = Column(Numeric)
    cumulative_cashflow_local = Column(Numeric)
    mva = Column(Numeric)
    mva_local = Column(Numeric)
    mva_previous = Column(Numeric)
    mva_local_previous = Column(Numeric)
    rawFile = Column(String)

class FactHoldingsAll(Base):
    __tablename__ = "fact_holdings_all"
    __table_args__ = {'schema': 'phw_dev_gold'}
    AsofDate = Column(Date, primary_key=True, index=True)
    AccountCode = Column(String, ForeignKey("phw_dev_gold.dim_accounts.AccountCode"), primary_key=True, index=True)
    SecurityCode = Column(String, ForeignKey("phw_dev_gold.dim_securitymaster.security_code"), index=True)
    SecurityType = Column(String)
    CurrencyCode = Column(String)
    MarketValueAccrued = Column(Float)
    MarketValue = Column(Float)
    AverageCost = Column(Float)
    BookValue = Column(Float)
    LocalMarketAccrued = Column(Float)
    LocalMarketValue = Column(Float)
    LocalAverageCost = Column(Numeric)
    LocalBookValue = Column(Numeric)
    SecurityFXRate = Column(Numeric)
    InvertedSecurityFXRate = Column(Numeric)
    Quantity = Column(Numeric)
    MarketPrice = Column(Numeric)
    CurrentYield = Column(Numeric)
    TotalUnrealizedGL = Column(Float)
    AnnualIncome = Column(Numeric)
    ValueIsInSecurityCurrency = Column(Boolean)
    ProcessedDate = Column(Date)
    ProcessedTimestampEST = Column(DateTime)
    rawFile = Column(String)
    AccountName = Column(String(255))
    PriceUnrealizedGL = Column(Float)
    FXUnrealizedGL = Column(Float)

    account = relationship("DimAccount", back_populates="holdings")
    security = relationship("DimSecurityMaster", back_populates="holdings")

class FactHoldingsAllRollup(Base):
    __tablename__ = "fact_holdings_all_rollup"
    __table_args__ = {'schema': 'phw_dev_gold'}
    AsOfDate = Column(Date, primary_key=True, index=True)
    AccountCurrencyCode = Column(String)
    LocalMarketAccrued = Column(Numeric)
    MarketValueAccrued = Column(Numeric)

class FactTransaction(Base):
    __tablename__ = "fact_transactions"
    __table_args__ = {'schema': 'phw_dev_gold'}
    AccountCode = Column(String, ForeignKey("phw_dev_gold.dim_accounts.AccountCode"), primary_key=True, index=True)
    SecurityCode = Column(String, ForeignKey("phw_dev_gold.dim_securitymaster.security_code"), primary_key=True, index=True)
    ExternalTransactionCode = Column(Integer, primary_key=True, index=True)
    TransactionTypeCode = Column(String)
    TradeDate = Column(Date)
    SettleDate = Column(Date)
    Quantity = Column(Numeric)
    UnitPrice = Column(Numeric)
    BookValue = Column(Numeric)
    SettlementAmount = Column(Numeric)
    SettlementCurrency = Column(String)
    ExchangeCurrency = Column(String)
    EffectiveDate = Column(Date)
    Cancel = Column(String)
    ProcessedDate = Column(Date)
    ProcessedTimestampEST = Column(DateTime)
    rawFile = Column(String)

class FxRate(Base):
    __tablename__ = "fx_rate"
    __table_args__ = {'schema': 'phw_dev_gold'}
    AsofDate = Column(Date, primary_key=True, index=True)
    BaseCAD = Column(Numeric)
    Local = Column(Numeric)
    LocalCurrencyCode = Column(String)
    ProcessedDate = Column(Date)
    ProcessedTimestampEST = Column(DateTime)
    rawFile = Column(String)