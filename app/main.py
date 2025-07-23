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


# Removed multiple endpoints as requested - keeping only FX rate and Sankey-related endpoints


@app.post("/fx_rate/", response_model=schemas.FxRate)
def read_fx_rate(request: schemas.FxRateRequest, db: Session = Depends(get_db)):
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
    """
    return services.get_available_sankey_columns(db)


@app.post("/holdings_agg_for_sankey/", response_model=schemas.SankeyData)
def read_holdings_for_sankey(request: schemas.SankeyRequest, db: Session = Depends(get_db)):
    """
    Get holdings data formatted for Sankey diagram visualization.

    The sankey_levels should use prefixes and snake_case format:
    - 'account.column_name' for columns from dim_accounts table
    - 'security.column_name' for columns from dim_securitymaster table

    Example sankey_levels: ["account.account_type", "security.security_currency_code", "security.asset_class_level_1_name"]
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
    """
    results = services.get_available_dates_for_accounts(db, request=request)
    if not results.available_dates:
        raise HTTPException(status_code=404, detail="No data found for the given account codes")
    return results


@app.post("/performance_attribution_sankey/", response_model=schemas.PerformanceSankeyResponse)
async def get_performance_attribution_sankey(
    request: schemas.PerformanceAttributionRequest, db: Session = Depends(get_db)
):
    """
    Generate performance attribution data for a Sankey diagram.
    """
    service = services.PerformanceSankeyService(db)
    data = service.generate_sankey_data(
        start_date=request.start_date,
        end_date=request.end_date,
        account_codes=request.account_codes,
        attribution_levels=request.attribution_levels,
    )
    return data


@app.get("/available_performance_sankey_levels/", response_model=List[str])
async def get_available_performance_sankey_levels():
    """
    Returns the available levels for performance attribution.
    """
    return ["fx", "dividends", "appreciation", "securities", "fees"]
