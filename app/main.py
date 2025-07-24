from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from . import services, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Add CORS middleware to allow web requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/performance_benchmark/", response_model=schemas.BenchmarkPerformanceResponse)
def get_performance_benchmark(
    request: schemas.BenchmarkPerformanceRequest,
    db: Session = Depends(get_db),
):
    """
    Get performance benchmark data for a given set of accounts and benchmarks.

    Example payload:
    {
        "account_codes": ["5PXABH"],
        "benchmark_list": ["VFV.TO", "XEQT.TO"],
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
    """
    from .benchmark_service import BenchmarkService

    service = BenchmarkService(db)
    data = service.get_benchmark_performance(
        account_codes=request.account_codes,
        benchmark_symbols=request.benchmark_list,
        start_date=request.start_date,
        end_date=request.end_date,
    )
    return data


# Removed multiple endpoints as requested - keeping only FX rate and Sankey-related endpoints


@app.post("/available_account_codes/", response_model=List[str])
def get_available_account_codes(request: schemas.AccountCodesRequest, db: Session = Depends(get_db)):
    """
    Get all available account codes in the system.

    Returns a simple list of account code strings.

    Example payload:
    {}
    """
    return services.get_available_account_codes(db)


@app.post("/fx_rate/", response_model=schemas.FxRate)
def read_fx_rate(request: schemas.FxRateRequest, db: Session = Depends(get_db)):
    """
    Get FX rate for a specific date.

    Example payload:
    {
        "as_of_date": "2024-12-31"
    }
    """
    db_fx_rate = services.get_fx_rate(db, as_of_date=request.as_of_date)
    if db_fx_rate is None:
        raise HTTPException(status_code=404, detail="FxRate not found")
    return db_fx_rate


# Removed holdings endpoints as requested


@app.post("/holdings_available_sankey_columns/", response_model=schemas.AvailableSankeyColumns)
def read_available_sankey_columns(request: schemas.AvailableSankeyColumnsRequest, db: Session = Depends(get_db)):
    """
    Get available columns for Sankey diagram grouping.
    Returns columns from both account and security tables with proper prefixes.

    Example payload:
    {}

    Returns columns that can be used in the sankey_levels parameter for holdings_agg_for_sankey endpoint.
    """
    return services.get_available_sankey_columns(db)


@app.post("/holdings_agg_for_sankey/", response_model=schemas.SankeyData)
def read_holdings_for_sankey(request: schemas.SankeyRequest, db: Session = Depends(get_db)):
    """
    Get holdings data formatted for Sankey diagram visualization.

    The sankey_levels should use prefixes:
    - 'account.ColumnName' for columns from dim_accounts table
    - 'security.ColumnName' for columns from dim_securitymaster table

    Example payload:
    {
        "as_of_date": "2024-12-31",
        "account_codes": ["5PXABH", "5PXAZZ"],
        "sankey_levels": [
            "account.account_type",
            "security.security_currency_code",
            "security.asset_class_level_1_name"
        ]
    }

    Use holdings_available_sankey_columns endpoint to get available column options.
    """
    results = services.get_holdings_for_sankey(db, request=request)
    if not results.nodes:
        raise HTTPException(status_code=404, detail="No holdings found for the given criteria")
    return results


@app.post("/holdings_available_dates/", response_model=schemas.AvailableDatesResponse)
def get_available_dates(request: schemas.AvailableDatesRequest, db: Session = Depends(get_db)):
    """
    Get available as_of_date values for given account codes.

    Returns a list of all available dates from the holdings data for the specified accounts,
    along with summary statistics like earliest/latest dates and total count.

    Example payload:
    {
        "account_codes": ["5PXABH", "5PXAZZ"]
    }
    """
    results = services.get_available_dates_for_accounts(db, request=request)
    if not results.available_dates:
        raise HTTPException(status_code=404, detail="No data found for the given account codes")
    return results


@app.post("/performance_attribution_sankey/", response_model=schemas.PerformanceAttributionResponse)
async def get_performance_attribution_sankey(
    request: schemas.PerformanceAttributionRequest, db: Session = Depends(get_db)
):
    """
    Generate performance attribution data with both summary and Sankey diagram.

    Returns:
    - perf_summary: MVA values, net contributions, and attribution totals
    - perf_sankey: Sankey diagram focused on gain/loss breakdown with account details

    The Sankey diagram excludes Start/End MVA for better visualization of attribution flows:
    Total Gain/Loss → Gains/Losses → Attribution Categories → Account Breakdown

    Attribution categories include:
    - FX Gain/Loss: Currency impact on foreign securities
    - Portfolio Income: Dividends and interest (reinvested)
    - Market Appreciation/Depreciation: Price movement in local currency
    - Portfolio Fees/Expenses: Management fees and trading costs
    - Other Gain/Loss: Unexplained attribution differences

    Example payload:
    {
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "account_codes": ["5PXABH", "5PXAZZ"]
    }
    """
    service = services.PerformanceSankeyService(db)
    data = service.generate_sankey_data(
        start_date=request.start_date,
        end_date=request.end_date,
        account_codes=request.account_codes,
    )
    return data


@app.post("/available_performance_sankey_levels/", response_model=List[str])
async def get_available_performance_sankey_levels(
    request: schemas.AvailablePerformanceSankeyLevelsRequest, db: Session = Depends(get_db)
):
    """
    Returns the fixed attribution levels used in performance attribution Sankey diagrams.

    The performance attribution follows a predefined flow structure and always includes these levels:
    - "fx": Foreign exchange gain/loss from currency movements
    - "dividends": Portfolio income from dividends and interest (reinvested)
    - "appreciation": Market price appreciation/depreciation in local currency
    - "fees": Portfolio fees and expenses (management fees, trading costs)
    - "other": Other/unexplained gains and losses that cannot be attributed to the above categories

    Note: Attribution levels are now fixed and cannot be customized to ensure consistent calculations.

    Example payload:
    {}
    """
    return ["fx", "dividends", "appreciation", "fees", "other"]
