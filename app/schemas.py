from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime


class DimAccount(BaseModel):
    AccountCode: str
    AccountType: Optional[str] = None
    AccountVisualizationID: Optional[str] = None
    AccountName: Optional[str] = None
    CustodianAccountCode: Optional[str] = None
    CustodianCode: Optional[str] = None
    CustodianName: Optional[str] = None
    OpenDate: Optional[date] = None
    Country: Optional[str] = None
    ContactAddressLine1: Optional[str] = None
    Status: Optional[str] = None
    AccountCurrencyCode: Optional[str] = None
    IsRegisteredAccount: Optional[str] = None
    ProcessedDate: Optional[date] = None
    ProcessedTimestampEST: Optional[datetime] = None
    rawFile: Optional[str] = None

    class Config:
        orm_mode = True


class DimSecurityMaster(BaseModel):
    secid: str
    security_code: Optional[str] = None
    security_name: Optional[str] = None
    security_symbol: Optional[str] = None
    security_description: Optional[str] = None
    security_type_code: Optional[str] = None
    security_type_description: Optional[str] = None
    sec_status: Optional[str] = None
    security_country: Optional[str] = None
    security_currency_code: Optional[str] = None
    cusip: Optional[str] = None
    sedol: Optional[str] = None
    isin: Optional[str] = None
    bbgid: Optional[str] = None
    asset_class: Optional[str] = None
    asset_class_code: Optional[str] = None
    industry_group: Optional[str] = None
    industry_group_code: Optional[str] = None
    issuer_code: Optional[str] = None
    issuer: Optional[str] = None
    ProcessedDate: Optional[date] = None
    AssetClassLevel1Name: Optional[str] = None
    AssetClassLevel2Name: Optional[str] = None
    AssetClassLevel3Name: Optional[str] = None
    AssetClassLevel1: Optional[str] = None
    AssetClassLevel2: Optional[str] = None
    AssetClassLevel3: Optional[str] = None
    ProcessedTimestampEST: Optional[datetime] = None
    rawFile: Optional[str] = None

    class Config:
        orm_mode = True


class DimTransactionType(BaseModel):
    TransactionType: str
    Description: Optional[str] = None
    Taxable: Optional[bool] = None
    ProcessedDate: Optional[date] = None
    ProcessedTimestampEST: Optional[datetime] = None
    rawFile: str

    class Config:
        orm_mode = True


class FactAccountRor(BaseModel):
    account_code: str
    as_of_date: Optional[str] = None
    mtd: Optional[float] = None
    lcm: Optional[float] = None
    qtd: Optional[float] = None
    lcq: Optional[float] = None
    ytd: Optional[float] = None
    l3y: Optional[float] = None
    l5y: Optional[float] = None
    l10y: Optional[float] = None
    itd: Optional[float] = None

    class Config:
        orm_mode = True


class FactDailyAggregateValue(BaseModel):
    account_code: str
    as_of_date: Optional[date] = None
    deposit_local: Optional[float] = None
    withdrawal_local: Optional[float] = None
    net_cashflow_local: Optional[float] = None
    deposit_converted: Optional[float] = None
    withdrawal_converted: Optional[float] = None
    net_cashflow_converted: Optional[float] = None
    market_value_accrued_local: Optional[float] = None
    market_value_accrued_converted: Optional[float] = None
    market_value_accrued_previous_local: Optional[float] = None
    market_value_accrued_previous_converted: Optional[float] = None
    cumulative_cashflow_local: Optional[float] = None
    cumulative_cashflow_converted: Optional[float] = None
    rawFile: Optional[str] = None

    class Config:
        orm_mode = True


class FactDailyAggregateValueSlp(BaseModel):
    account_code: str
    security_code: Optional[str] = None
    as_of_date: Optional[date] = None
    deposit: Optional[float] = None
    deposit_local: Optional[float] = None
    withdrawal: Optional[float] = None
    withdrawal_local: Optional[float] = None
    net_cashflow_converted: Optional[float] = None
    net_cashflow_local: Optional[float] = None
    cumulative_cashflow_converted: Optional[float] = None
    cumulative_cashflow_local: Optional[float] = None
    mva: Optional[float] = None
    mva_local: Optional[float] = None
    mva_previous: Optional[float] = None
    mva_local_previous: Optional[float] = None
    rawFile: Optional[str] = None

    class Config:
        orm_mode = True


class FactHoldingsAll(BaseModel):
    AsofDate: date
    AccountCode: str
    SecurityCode: Optional[str] = None
    SecurityType: Optional[str] = None
    CurrencyCode: Optional[str] = None
    MarketValueAccrued: Optional[float] = None
    MarketValue: Optional[float] = None
    AverageCost: Optional[float] = None
    BookValue: Optional[float] = None
    LocalMarketAccrued: Optional[float] = None
    LocalMarketValue: Optional[float] = None
    LocalAverageCost: Optional[float] = None
    LocalBookValue: Optional[float] = None
    SecurityFXRate: Optional[float] = None
    InvertedSecurityFXRate: Optional[float] = None
    Quantity: Optional[float] = None
    MarketPrice: Optional[float] = None
    CurrentYield: Optional[float] = None
    TotalUnrealizedGL: Optional[float] = None
    AnnualIncome: Optional[float] = None
    ValueIsInSecurityCurrency: Optional[bool] = None
    ProcessedDate: Optional[date] = None
    ProcessedTimestampEST: Optional[datetime] = None
    rawFile: Optional[str] = None
    AccountName: Optional[str] = None
    PriceUnrealizedGL: Optional[float] = None
    FXUnrealizedGL: Optional[float] = None

    class Config:
        orm_mode = True


class FactHoldingsAllRollup(BaseModel):
    AsOfDate: date
    AccountCode: str
    AccountCurrencyCode: Optional[str] = None
    LocalMarketAccrued: Optional[float] = None
    MarketValueAccrued: Optional[float] = None

    class Config:
        orm_mode = True


class FactTransaction(BaseModel):
    AccountCode: str
    SecurityCode: Optional[str] = None
    ExternalTransactionCode: Optional[int] = None
    TransactionTypeCode: Optional[str] = None
    TradeDate: Optional[date] = None
    SettleDate: Optional[date] = None
    Quantity: Optional[float] = None
    UnitPrice: Optional[float] = None
    BookValue: Optional[float] = None
    SettlementAmount: Optional[float] = None
    SettlementCurrency: Optional[str] = None
    ExchangeCurrency: Optional[str] = None
    EffectiveDate: Optional[date] = None
    Cancel: Optional[str] = None
    ProcessedDate: Optional[date] = None
    ProcessedTimestampEST: Optional[datetime] = None
    rawFile: Optional[str] = None

    class Config:
        orm_mode = True


class FxRate(BaseModel):
    AsofDate: date
    BaseCAD: Optional[float] = None
    Local: Optional[float] = None
    LocalCurrencyCode: Optional[str] = None
    ProcessedDate: Optional[date] = None
    ProcessedTimestampEST: Optional[datetime] = None
    rawFile: Optional[str] = None

    class Config:
        orm_mode = True


class Holding(BaseModel):
    as_of_date: date
    account_name: str
    security_name: str
    security_type: str
    market_value: float
    quantity: float
    total_value: float

    class Config:
        orm_mode = True


class HoldingsAggregationRequest(BaseModel):
    as_of_date: date
    account_codes: List[str]
    account_group_by_clause: Optional[List[str]] = Field(default_factory=lambda: ["AccountType"])
    security_group_by_clause: Optional[List[str]] = Field(
        default_factory=lambda: ["security_currency_code", "AssetClassLevel1Name"]
    )


class AggregatedHolding(BaseModel):
    group: Dict[str, Any]
    total_market_value: float

    class Config:
        orm_mode = True


class SankeyRequest(BaseModel):
    as_of_date: date
    account_codes: List[str]
    sankey_levels: List[str] = Field(
        default_factory=lambda: [
            "account.AccountType",
            "security.security_currency_code",
            "security.asset_class_level_1_name",
        ]
    )


class SankeyNode(BaseModel):
    label: str


class SankeyLink(BaseModel):
    source: int
    target: int
    value: float


class SankeyData(BaseModel):
    nodes: List[SankeyNode]
    links: List[SankeyLink]


class AvailableColumn(BaseModel):
    table_type: str
    column_name: str
    prefixed_name: str


class AvailableSankeyColumns(BaseModel):
    account_columns: List[AvailableColumn]
    security_columns: List[AvailableColumn]
