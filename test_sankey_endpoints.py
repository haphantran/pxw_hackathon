#!/usr/bin/env python3
"""
Test script to demonstrate the new Sankey diagram endpoints.

This script shows how to use the new endpoints:
1. /available_sankey_columns/ - Get available columns for grouping
2. /holdings_agg_for_sankey/ - Get holdings data formatted for Sankey diagrams

Usage:
    python test_sankey_endpoints.py
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"  # Adjust this to your FastAPI server URL


def test_available_columns():
    """Test the available_sankey_columns endpoint."""
    print("Testing /available_sankey_columns/ endpoint...")

    try:
        response = requests.get(f"{BASE_URL}/available_sankey_columns/")
        response.raise_for_status()

        data = response.json()
        print("✅ Available columns retrieved successfully!")
        print("\nAccount columns:")
        for col in data["account_columns"]:
            print(f"  - {col['prefixed_name']} ({col['column_name']})")

        print("\nSecurity columns:")
        for col in data["security_columns"]:
            print(f"  - {col['prefixed_name']} ({col['column_name']})")

        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ Error testing available columns: {e}")
        return None


def test_sankey_holdings():
    """Test the holdings_agg_for_sankey endpoint."""
    print("\nTesting /holdings_agg_for_sankey/ endpoint...")

    # Example request payload
    payload = {
        "as_of_date": "2024-12-31",  # Adjust this date as needed
        "account_codes": ["ACC001", "ACC002"],  # Adjust account codes as needed
        "sankey_levels": [
            "account.AccountType",
            "security.security_currency_code",
            "security.asset_class_level_1_name",
        ],
    }

    try:
        response = requests.post(
            f"{BASE_URL}/holdings_agg_for_sankey/", json=payload, headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()

        data = response.json()
        print("✅ Sankey holdings data retrieved successfully!")
        print(f"\nNodes ({len(data['nodes'])}):")
        for i, node in enumerate(data["nodes"]):
            print(f"  {i}: {node['label']}")

        print(f"\nLinks ({len(data['links'])}):")
        for i, link in enumerate(data["links"][:10]):  # Show first 10 links
            source_label = data["nodes"][link["source"]]["label"]
            target_label = data["nodes"][link["target"]]["label"]
            print(f"  {source_label} → {target_label}: ${link['value']:,.2f}")

        if len(data["links"]) > 10:
            print(f"  ... and {len(data['links']) - 10} more links")

        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ Error testing sankey holdings: {e}")
        return None


def generate_plotly_example(sankey_data):
    """Generate example Plotly.js code for the Sankey diagram."""
    if not sankey_data:
        return

    print("\n" + "=" * 60)
    print("PLOTLY.JS EXAMPLE CODE")
    print("=" * 60)

    plotly_code = f"""
// Example Plotly.js code for rendering the Sankey diagram
const data = {{
  type: "sankey",
  node: {{
    pad: 15,
    thickness: 30,
    line: {{
      color: "black",
      width: 0.5
    }},
    label: {json.dumps([node['label'] for node in sankey_data['nodes']])},
    color: "blue"
  }},
  link: {{
    source: {json.dumps([link['source'] for link in sankey_data['links']])},
    target: {json.dumps([link['target'] for link in sankey_data['links']])},
    value: {json.dumps([link['value'] for link in sankey_data['links']])}
  }}
}};

const layout = {{
  title: "Portfolio Holdings Sankey Diagram",
  width: 1200,
  height: 800,
  font: {{
    size: 12
  }}
}};

Plotly.newPlot('sankeyDiv', [data], layout);
"""

    print(plotly_code)


def main():
    """Main test function."""
    print("🚀 Testing Sankey Diagram Endpoints")
    print("=" * 50)

    # Test available columns endpoint
    columns_data = test_available_columns()

    # Test sankey holdings endpoint
    sankey_data = test_sankey_holdings()

    # Generate Plotly example
    generate_plotly_example(sankey_data)

    print("\n" + "=" * 50)
    print("📋 ENDPOINT SUMMARY")
    print("=" * 50)
    print("1. GET /available_sankey_columns/")
    print("   - Returns available columns for Sankey grouping")
    print("   - No parameters required")
    print()
    print("2. POST /holdings_agg_for_sankey/")
    print("   - Returns Sankey diagram data")
    print("   - Requires: as_of_date, account_codes, sankey_levels")
    print("   - Use prefixes: 'account.' or 'security.'")
    print()
    print("💡 The data returned is ready for Plotly.js Sankey diagrams!")


if __name__ == "__main__":
    main()
