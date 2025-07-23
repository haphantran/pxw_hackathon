# Quick Start Guide: Sankey Diagram Endpoints

## 🚀 Getting Started

### 1. Start Your FastAPI Server
```bash
# From your project root directory
uvicorn app.main:app --reload
```

### 2. Test the New Endpoints

#### Option A: Use the Test Script
```bash
# Install required dependencies first
pip install requests

# Run the test script
python test_sankey_endpoints.py
```

#### Option B: Manual API Testing

**Get Available Columns:**
```bash
curl -X GET "http://localhost:8000/available_sankey_columns/"
```

**Get Sankey Data:**
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

#### Option C: Interactive Demo
```bash
# Serve the demo HTML file
python -m http.server 8080

# Open in browser
open http://localhost:8080/sankey_demo.html
```

## 📊 Frontend Integration with Plotly.js

```javascript
// 1. Fetch data from your API
const response = await fetch('/holdings_agg_for_sankey/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    as_of_date: '2024-12-31',
    account_codes: ['ACC001', 'ACC002'],
    sankey_levels: [
      'account.AccountType',
      'security.security_currency_code', 
      'security.asset_class_level_1_name'
    ]
  })
});

const sankeyData = await response.json();

// 2. Create Plotly Sankey diagram
const data = [{
  type: "sankey",
  node: {
    label: sankeyData.nodes.map(node => node.label),
    color: "blue"
  },
  link: {
    source: sankeyData.links.map(link => link.source),
    target: sankeyData.links.map(link => link.target),
    value: sankeyData.links.map(link => link.value)
  }
}];

const layout = {
  title: "Portfolio Holdings Sankey Diagram",
  width: 1200,
  height: 600
};

Plotly.newPlot('sankeyDiv', data, layout);
```

## 🔧 Configuration Options

### Default Sankey Levels
```json
[
  "account.AccountType",
  "security.security_currency_code",
  "security.asset_class_level_1_name"
]
```

### Available Prefixes
- **`account.`** - Columns from `dim_accounts` table
- **`security.`** - Columns from `dim_securitymaster` table

### Common Column Examples
```
Account columns:
- account.AccountType
- account.AccountName
- account.Country

Security columns:  
- security.security_currency_code
- security.asset_class_level_1_name
- security.security_type_description
- security.industry_group
```

## 🐛 Troubleshooting

### Common Issues:

1. **"Import could not be resolved" errors in VS Code**
   - These are expected in this environment
   - Run the server to test actual functionality

2. **404 errors when testing**
   - Ensure your database has data for the specified date and accounts
   - Check that account codes exist in your database

3. **Empty Sankey diagram**
   - Verify the `as_of_date` has holdings data
   - Check that account codes are valid
   - Ensure the currency filter (CAD) matches your data

### Success Indicators:
- ✅ Server starts without errors: `uvicorn app.main:app --reload`
- ✅ GET `/available_sankey_columns/` returns column lists
- ✅ POST `/holdings_agg_for_sankey/` returns nodes and links
- ✅ Demo page displays interactive Sankey diagram

## 📚 Documentation Files

- **`SANKEY_ENDPOINTS.md`** - Complete API documentation
- **`IMPLEMENTATION_SUMMARY.md`** - Technical implementation details
- **`sankey_demo.html`** - Interactive demo and example
- **`test_sankey_endpoints.py`** - Automated testing script

You're all set! The new Sankey diagram endpoints are ready for use. 🎉
