#!/usr/bin/env python3
"""
Quick test to verify the SQL query generation for Sankey endpoints.
Run this to check if the SQL syntax is correct before testing with the full API.
"""

import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from queries import get_sankey_holdings_query, get_available_sankey_columns_query


def test_sankey_query_generation():
    """Test the Sankey SQL query generation"""
    print("🧪 Testing Sankey Query Generation")
    print("=" * 50)

    # Test case 1: Default levels
    test_levels_1 = ["account.AccountType", "security.security_currency_code", "security.asset_class_level_1_name"]

    print("Test 1: Default levels")
    print(f"Levels: {test_levels_1}")
    query1 = get_sankey_holdings_query(test_levels_1)
    print("Generated SQL:")
    print(str(query1))
    print("\n" + "-" * 50 + "\n")

    # Test case 2: Account-only levels
    test_levels_2 = ["account.AccountType", "account.AccountName"]

    print("Test 2: Account-only levels")
    print(f"Levels: {test_levels_2}")
    query2 = get_sankey_holdings_query(test_levels_2)
    print("Generated SQL:")
    print(str(query2))
    print("\n" + "-" * 50 + "\n")

    # Test case 3: Security-only levels
    test_levels_3 = [
        "security.security_currency_code",
        "security.asset_class_level_1_name",
        "security.security_type_description",
    ]

    print("Test 3: Security-only levels")
    print(f"Levels: {test_levels_3}")
    query3 = get_sankey_holdings_query(test_levels_3)
    print("Generated SQL:")
    print(str(query3))
    print("\n" + "-" * 50 + "\n")

    # Test case 4: Mixed with IsRegisteredAccount
    test_levels_4 = [
        "account.IsRegisteredAccount",
        "security.security_currency_code",
        "security.asset_class_level_1_name",
    ]

    print("Test 4: IsRegisteredAccount flow")
    print(f"Levels: {test_levels_4}")
    query4 = get_sankey_holdings_query(test_levels_4)
    print("Generated SQL:")
    print(str(query4))
    print("\n" + "-" * 50 + "\n")

    # Test available columns query
    print("Test 5: Available columns query")
    columns_query = get_available_sankey_columns_query()
    print("Generated SQL:")
    print(str(columns_query))

    print("\n" + "=" * 50)
    print("✅ All queries generated successfully!")
    print("\n💡 Key fixes applied:")
    print("   - Separated SELECT columns (with aliases) from GROUP BY columns (without aliases)")
    print("   - Fixed AssetClassLevel1Name → asset_class_level_1_name handling")
    print("   - Added proper column prefixing for account vs security tables")


if __name__ == "__main__":
    test_sankey_query_generation()
