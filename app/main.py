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


@app.get("/dim_accounts/{account_code}", response_model=schemas.DimAccount)
def read_dim_account(account_code: str, db: Session = Depends(get_db)):
    db_dim_account = services.get_dim_account(db, account_code=account_code)
    if db_dim_account is None:
        raise HTTPException(status_code=404, detail="DimAccount not found")
    return db_dim_account


@app.get("/dim_securitymaster/{secid}", response_model=schemas.DimSecurityMaster)
def read_dim_securitymaster(secid: str, db: Session = Depends(get_db)):
    db_dim_securitymaster = services.get_dim_securitymaster(db, secid=secid)
    if db_dim_securitymaster is None:
        raise HTTPException(status_code=404, detail="DimSecurityMaster not found")
    return db_dim_securitymaster


@app.get("/dim_transaction_types/{transaction_type}", response_model=schemas.DimTransactionType)
def read_dim_transaction_type(transaction_type: str, db: Session = Depends(get_db)):
    db_dim_transaction_type = services.get_dim_transaction_type(db, transaction_type=transaction_type)
    if db_dim_transaction_type is None:
        raise HTTPException(status_code=404, detail="DimTransactionType not found")
    return db_dim_transaction_type


@app.get("/fact_account_ror/{account_code}", response_model=schemas.FactAccountRor)
def read_fact_account_ror(account_code: str, db: Session = Depends(get_db)):
    db_fact_account_ror = services.get_fact_account_ror(db, account_code=account_code)
    if db_fact_account_ror is None:
        raise HTTPException(status_code=404, detail="FactAccountRor not found")
    return db_fact_account_ror


@app.get("/fact_daily_aggregate_values/{account_code}", response_model=schemas.FactDailyAggregateValue)
def read_fact_daily_aggregate_value(account_code: str, db: Session = Depends(get_db)):
    db_fact_daily_aggregate_value = services.get_fact_daily_aggregate_value(db, account_code=account_code)
    if db_fact_daily_aggregate_value is None:
        raise HTTPException(status_code=404, detail="FactDailyAggregateValue not found")
    return db_fact_daily_aggregate_value


@app.get("/fact_daily_aggregate_values_slp/{account_code}", response_model=schemas.FactDailyAggregateValueSlp)
def read_fact_daily_aggregate_value_slp(account_code: str, db: Session = Depends(get_db)):
    db_fact_daily_aggregate_value_slp = services.get_fact_daily_aggregate_value_slp(db, account_code=account_code)
    if db_fact_daily_aggregate_value_slp is None:
        raise HTTPException(status_code=404, detail="FactDailyAggregateValueSlp not found")
    return db_fact_daily_aggregate_value_slp


@app.get("/fact_holdings_all/{as_of_date}/{account_code}", response_model=schemas.FactHoldingsAll)
def read_fact_holdings_all(as_of_date: str, account_code: str, db: Session = Depends(get_db)):
    db_fact_holdings_all = services.get_fact_holdings_all(db, as_of_date=as_of_date, account_code=account_code)
    if db_fact_holdings_all is None:
        raise HTTPException(status_code=404, detail="FactHoldingsAll not found")
    return db_fact_holdings_all


@app.get("/fact_holdings_all_rollup/{as_of_date}/{account_code}", response_model=schemas.FactHoldingsAllRollup)
def read_fact_holdings_all_rollup(as_of_date: str, account_code: str, db: Session = Depends(get_db)):
    db_fact_holdings_all_rollup = services.get_fact_holdings_all_rollup(
        db, as_of_date=as_of_date, account_code=account_code
    )
    if db_fact_holdings_all_rollup is None:
        raise HTTPException(status_code=404, detail="FactHoldingsAllRollup not found")
    return db_fact_holdings_all_rollup


@app.get("/fact_transactions/{account_code}", response_model=schemas.FactTransaction)
def read_fact_transaction(account_code: str, db: Session = Depends(get_db)):
    db_fact_transaction = services.get_fact_transaction(db, account_code=account_code)
    if db_fact_transaction is None:
        raise HTTPException(status_code=404, detail="FactTransaction not found")
    return db_fact_transaction


@app.get("/fx_rate/{as_of_date}", response_model=schemas.FxRate)
def read_fx_rate(as_of_date: str, db: Session = Depends(get_db)):
    db_fx_rate = services.get_fx_rate(db, as_of_date=as_of_date)
    if db_fx_rate is None:
        raise HTTPException(status_code=404, detail="FxRate not found")
    return db_fx_rate


@app.get("/holdings/{account_code}", response_model=List[schemas.Holding])
def read_holdings_by_account(account_code: str, db: Session = Depends(get_db)):
    results = services.get_holdings_by_account(db, account_code=account_code)
    if not results:
        raise HTTPException(status_code=404, detail="Holdings not found")
    return results


@app.post("/holdings_aggregated/", response_model=List[schemas.AggregatedHolding])
def read_aggregated_holdings(request: schemas.HoldingsAggregationRequest, db: Session = Depends(get_db)):
    results = services.get_aggregated_holdings(db, request=request)
    if not results:
        raise HTTPException(status_code=404, detail="No holdings found for the given criteria")
    return results


@app.get("/available_sankey_columns/", response_model=schemas.AvailableSankeyColumns)
def read_available_sankey_columns(db: Session = Depends(get_db)):
    """
    Get available columns for Sankey diagram grouping.
    Returns columns from both account and security tables with proper prefixes.
    """
    return services.get_available_sankey_columns(db)


@app.post("/holdings_agg_for_sankey/", response_model=schemas.SankeyData)
def read_holdings_for_sankey(request: schemas.SankeyRequest, db: Session = Depends(get_db)):
    """
    Get holdings data formatted for Sankey diagram visualization.

    The sankey_levels should use prefixes:
    - 'account.ColumnName' for columns from dim_accounts table
    - 'security.ColumnName' for columns from dim_securitymaster table

    Example sankey_levels: ["account.AccountType", "security.security_currency_code", "security.asset_class_level_1_name"]
    """
    results = services.get_holdings_for_sankey(db, request=request)
    if not results.nodes:
        raise HTTPException(status_code=404, detail="No holdings found for the given criteria")
    return results
