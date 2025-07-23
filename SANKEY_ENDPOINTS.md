# Sankey Diagram Endpoints Documentation

This document describes the new endpoints added to support Sankey diagram visualization for portfolio holdings.

## Overview

Two new endpoints have been added to enable Sankey diagram functionality:

1. **`GET /available_sankey_columns/`** - Returns available columns for grouping
2. **`POST /holdings_agg_for_sankey/`** - Returns holdings data formatted for Sankey diagrams

## Endpoints

### 1. GET /available_sankey_columns/

Returns a list of available columns that can be used for grouping in Sankey diagrams.

**Response Model: `AvailableSankeyColumns`**

```json
{
  "account_columns": [
    {
      "table_type": "account",
      "column_name": "AccountType", 
      "prefixed_name": "account.AccountType"
    },
    {
      "table_type": "account",
      "column_name": "AccountName",
      "prefixed_name": "account.AccountName"
    }
  ],
  "security_columns": [
    {
      "table_type": "security",
      "column_name": "security_currency_code",
      "prefixed_name": "security.security_currency_code"
    },
    {
      "table_type": "security", 
      "column_name": "asset_class_level_1_name",
      "prefixed_name": "security.asset_class_level_1_name"
    }
  ]
}
```

### 2. POST /holdings_agg_for_sankey/

Returns holdings data formatted for Plotly.js Sankey diagram visualization.

**Request Model: `SankeyRequest`**

```json
{
  "as_of_date": "2024-12-31",
  "account_codes": ["ACC001", "ACC002"],
  "sankey_levels": [
    "account.AccountType",
    "security.security_currency_code", 
    "security.asset_class_level_1_name"
  ]
}
```

**Response Model: `SankeyData`**

```json
{
  "nodes": [
    {"label": "Grand Total"},
    {"label": "Registered"},
    {"label": "Non-Registered"},
    {"label": "CAD"},
    {"label": "USD"},
    {"label": "Equity"},
    {"label": "Fixed Income"}
  ],
  "links": [
    {"source": 0, "target": 1, "value": 500000.0},
    {"source": 0, "target": 2, "value": 300000.0},
    {"source": 1, "target": 3, "value": 400000.0},
    {"source": 1, "target": 4, "value": 100000.0}
  ]
}
```

## Key Features

### 1. Prefixed Column Names

To distinguish between columns from different tables, use prefixes:

- **`account.ColumnName`** - For columns from `dim_accounts` table
- **`security.ColumnName`** - For columns from `dim_securitymaster` table

Example:
```json
{
  "sankey_levels": [
    "account.AccountType",           // From dim_accounts
    "security.security_currency_code", // From dim_securitymaster
    "security.asset_class_level_1_name" // From dim_securitymaster (renamed)
  ]
}
```

### 2. Asset Class Level 1 Name Conversion

The `AssetClassLevel1Name` column is automatically converted to `asset_class_level_1_name` to follow consistent naming conventions:

- **Database column**: `AssetClassLevel1Name`
- **API column**: `asset_class_level_1_name`
- **Prefixed name**: `security.asset_class_level_1_name`

### 3. Hierarchical Structure

The Sankey diagram starts with a "Grand Total" node that represents the sum of all holdings, then flows through the specified levels in order.

### 4. Plotly.js Integration

The returned data format is directly compatible with Plotly.js Sankey diagrams:

```javascript
const data = {
  type: "sankey",
  node: {
    label: sankeyData.nodes.map(n => n.label),
    // ... other node properties
  },
  link: {
    source: sankeyData.links.map(l => l.source),
    target: sankeyData.links.map(l => l.target), 
    value: sankeyData.links.map(l => l.value)
  }
};

Plotly.newPlot('sankeyDiv', [data], layout);
```

## Example Usage

### 1. Get Available Columns

```bash
curl -X GET "http://localhost:8000/available_sankey_columns/"
```

### 2. Get Sankey Data

```bash
curl -X POST "http://localhost:8000/holdings_agg_for_sankey/" \
     -H "Content-Type: application/json" \
     -d '{
       "as_of_date": "2024-12-31",
       "account_codes": ["ACC001", "ACC002"],
       "sankey_levels": [
         "account.AccountType",
         "security.security_currency_code",
         "security.asset_class_level_1_name"
       ]
     }'
```

## Default Sankey Levels

If no `sankey_levels` are provided, the following defaults are used:

```json
[
  "account.AccountType",
  "security.security_currency_code", 
  "security.asset_class_level_1_name"
]
```

This creates a flow from:
1. Grand Total → Account Types (Registered, Non-Registered, etc.)
2. Account Types → Currency Codes (CAD, USD, etc.)
3. Currency Codes → Asset Classes (Equity, Fixed Income, etc.)

## Error Handling

- **404**: No holdings found for the given criteria
- **422**: Validation error (invalid date format, missing required fields)
- **500**: Database connection or query execution errors

## Notes

- All market values are aggregated in CAD currency
- Results are ordered by total market value in descending order
- The endpoint filters for `CurrencyCode = 'CAD'` in the holdings data
- Column names are case-sensitive and must match the database schema
