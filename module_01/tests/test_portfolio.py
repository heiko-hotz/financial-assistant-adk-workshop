import json
import unittest

from module_01.financial_agent_app.portfolio import (
    calculate_shock,
    get_holdings,
    get_position_values,
    get_stock_price,
)


class SimulatedFixtureTests(unittest.TestCase):
    def test_known_quotes_preserve_prices_and_supply_provenance(self):
        for symbol, price in {"LUMR": 245.50, "AAPL": 180, "GOOG": 140}.items():
            with self.subTest(symbol=symbol):
                self.assertEqual(
                    get_stock_price(f" {symbol.lower()} "),
                    {
                        "symbol": symbol,
                        "price": price,
                        "currency": "USD",
                        "source": "simulated",
                    },
                )

    def test_unknown_or_invalid_ticker_has_no_price(self):
        for ticker in ("UNKNOWN", "", " \t", None, 123):
            with self.subTest(ticker=ticker):
                quote = get_stock_price(ticker)
                self.assertIn("error", quote)
                self.assertNotIn("price", quote)

    def test_holdings_include_cash_and_each_call_gets_a_fresh_mapping(self):
        first_snapshot = get_holdings()
        self.assertEqual(
            first_snapshot,
            {
                "holdings": {"LUMR": 20, "AAPL": 100},
                "cash": 77_090,
                "currency": "USD",
                "source": "simulated",
            },
        )
        first_snapshot["holdings"]["LUMR"] = 0
        self.assertEqual(get_holdings()["holdings"]["LUMR"], 20)

    def test_position_values_exclude_target_holding_from_other_value(self):
        for ticker, symbol, current, other in (
            (" lumr ", "LUMR", 4_910, 95_090),
            ("AAPL", "AAPL", 18_000, 82_000),
        ):
            with self.subTest(ticker=ticker):
                self.assertEqual(
                    get_position_values(ticker),
                    {
                        "symbol": symbol,
                        "current_position_value": current,
                        "other_portfolio_value": other,
                        "currency": "USD",
                        "source": "simulated",
                    },
                )

    def test_position_values_error_for_unknown_and_unheld_tickers(self):
        for ticker, message in (("ZZZZ", "No simulated quote"), ("goog", "not in the simulated portfolio")):
            with self.subTest(ticker=ticker):
                result = get_position_values(ticker)
                self.assertEqual(set(result), {"symbol", "error"})
                self.assertIn(message, result["error"])


class ShockTests(unittest.TestCase):
    def setUp(self):
        snapshot = get_holdings()
        self.holdings = snapshot["holdings"]
        self.cash = snapshot["cash"]
        self.quotes = {
            ticker: get_stock_price(ticker)["price"] for ticker in self.holdings
        }

    def assert_invalid(self, result, message):
        self.assertIn(message, result["error"])
        self.assertNotIn("starting_value", result)
        self.assertNotIn("ending_value", result)

    def test_lumr_drop_leaves_other_holdings_and_cash_at_original_values(self):
        result = calculate_shock(self.holdings, self.quotes, self.cash, {"LUMR": -10})
        self.assertEqual(
            result,
            {
                "starting_value": 100_000,
                "ending_value": 99_509,
                "change_dollars": -491,
                "change_pct": -0.491,
            },
        )
        json.dumps(result, allow_nan=False)

    def test_mixed_shocks_apply_each_change_to_its_own_position(self):
        result = calculate_shock(
            self.holdings, self.quotes, self.cash, {"LUMR": -10, "AAPL": 5}
        )
        self.assertEqual(result["ending_value"], 100_409)
        self.assertEqual(result["change_dollars"], 409)
        self.assertEqual(result["change_pct"], 0.409)

    def test_total_price_loss_can_leave_an_empty_portfolio(self):
        result = calculate_shock({"LUMR": 20}, {"LUMR": 245.5}, 0, {"LUMR": -100})
        self.assertEqual(result["ending_value"], 0)
        self.assertEqual(result["change_pct"], -100)

    def test_total_price_loss_preserves_cash(self):
        result = calculate_shock({"LUMR": 1}, {"LUMR": 1e29}, 1, {"LUMR": -100})
        self.assertEqual(result["ending_value"], 1)

    def test_empty_shock_keeps_a_cash_only_portfolio_unchanged(self):
        result = calculate_shock({}, {}, 1_000, {})
        self.assertEqual(result["starting_value"], 1_000)
        self.assertEqual(result["ending_value"], 1_000)
        self.assertEqual(result["change_pct"], 0)

    def test_missing_quote_for_unchanged_position_fails(self):
        result = calculate_shock(
            self.holdings, {"LUMR": 245.5}, self.cash, {"LUMR": -10}
        )
        self.assert_invalid(result, "Missing quote for AAPL")

    def test_shock_for_unheld_name_fails_even_if_quote_exists(self):
        quotes = dict(self.quotes, GOOG=140)
        result = calculate_shock(self.holdings, quotes, self.cash, {"GOOG": 10})
        self.assert_invalid(result, "not in the portfolio")

    def test_invalid_quote_values_fail(self):
        for quote in (0, -1, "245.5", True, None, float("nan"), float("inf")):
            with self.subTest(quote=quote):
                quotes = dict(self.quotes, LUMR=quote)
                result = calculate_shock(self.holdings, quotes, self.cash, {})
                self.assert_invalid(result, "Quote for LUMR")

    def test_invalid_share_values_fail(self):
        for shares in (-1, 1.5, "20", True, None):
            with self.subTest(shares=shares):
                holdings = dict(self.holdings, LUMR=shares)
                result = calculate_shock(holdings, self.quotes, self.cash, {})
                self.assert_invalid(result, "Shares for LUMR")

    def test_invalid_cash_values_fail(self):
        for cash in (-1, "77090", False, None, float("nan"), float("inf")):
            with self.subTest(cash=cash):
                result = calculate_shock(self.holdings, self.quotes, cash, {})
                self.assert_invalid(result, "Cash must be")

    def test_invalid_shock_values_fail(self):
        for change in (-100.1, "-10", False, None, float("nan"), float("-inf")):
            with self.subTest(change=change):
                result = calculate_shock(
                    self.holdings, self.quotes, self.cash, {"LUMR": change}
                )
                self.assert_invalid(result, "Shock for LUMR")

    def test_invalid_mapping_inputs_fail(self):
        for args in (
            (None, self.quotes, self.cash, {}),
            (self.holdings, [], self.cash, {}),
            (self.holdings, self.quotes, self.cash, [-10]),
        ):
            with self.subTest(args=args):
                self.assert_invalid(calculate_shock(*args), "ticker mapping")

    def test_noncanonical_ticker_keys_fail(self):
        for key in ("lumr", " LUMR", "", 5):
            with self.subTest(key=key):
                result = calculate_shock(self.holdings, self.quotes, self.cash, {key: 5})
                self.assert_invalid(result, "uppercase ticker")

    def test_zero_starting_value_fails_instead_of_dividing_by_zero(self):
        self.assert_invalid(calculate_shock({}, {}, 0, {}), "must be positive")

    def test_numeric_overflow_fails_without_returning_nonfinite_values(self):
        result = calculate_shock({"LUMR": 2}, {"LUMR": 1e308}, 0, {})
        self.assert_invalid(result, "numeric range")


if __name__ == "__main__":
    unittest.main()
