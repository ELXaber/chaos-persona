from AlgorithmImports import *
from QuantConnect.Indicators import StandardDeviation, ExponentialMovingAverage, AverageTrueRange
import time

class CRB67TradingPlugin:
    def __init__(self):
        self.shared_memory = {
            "capital": 100.0,
            "position_value": 0.0,
            "prev_price": 0.0,
            "last_trade_time": 0.0,
            "collective_volatility": 0.1,
            "trade_log": [],
            "total_fees": 0.0,
            "entry_price": 0.0,
            "highest_price": 0.0
        }
        self.max_position = 85.0
        self.trade_cooldown = 0  # Remove cooldown - minute bars already limit frequency
        self.risk_cap = 0.40  # Increased to allow 35% positions
        self.fee_rate = 0.001

    def trading_plugin(self, current_time, price_data, volatility, portfolio_value, actual_cash):
        price = price_data.get("price", 1.0)
        prev_price = self.shared_memory.get("prev_price", price)
        change_ratio = (price - prev_price) / prev_price if prev_price != 0 else 0.0
        time_diff = current_time - self.shared_memory.get("last_trade_time", current_time - 60)

        log = f"[CRB67 @{current_time:.0f} V:{volatility:.1f} CR:{change_ratio:.3f}]"

        if time_diff < self.trade_cooldown:
            return None, 0.0, f"[COOLDOWN {time_diff:.0f}s]"

        capital = actual_cash  # Use real portfolio cash instead of tracked value
        position_size = min(0.20 * capital, 25.0)  # Reduced to 20% to fit risk cap
        current_position = self.shared_memory.get("position_value", 0.0)

        action = None
        amount = 0.0

        ema_cross = price_data.get("ema_cross", False)

        # SELL LOGIC - Check if we should sell existing position
        if current_position > 0:
            # Update highest_price on every tick
            highest = max(self.shared_memory.get("highest_price", price), price)
            self.shared_memory["highest_price"] = highest

            # Check sell conditions
            entry = self.shared_memory.get("entry_price", price)
            trailing_stop = highest * 0.90  # 10% trailing stop from peak
            hard_stop_loss = price < entry * 0.95  # 5% loss from entry
            trailing_triggered = price < trailing_stop  # 10% down from peak
            take_profit = (price - entry) / entry > 0.15  # 15% gain from entry

            if hard_stop_loss or trailing_triggered or take_profit:
                action = "sell"
                amount = current_position
                fee = amount * self.fee_rate
                self.shared_memory["capital"] += amount - fee
                self.shared_memory["total_fees"] += fee
                reason = 'STOP' if hard_stop_loss else 'TRAIL' if trailing_triggered else 'PROFIT'
                log += f" [SELL {amount:.1f} Fee:${fee:.2f} Reason:{reason}]"
                self.shared_memory["position_value"] = 0.0

        # BUY LOGIC - Only if we don't have a sell action
        if action is None:
            buy_condition = (ema_cross or (change_ratio > 0.003 and volatility < 500))
            volatility_ok = volatility < 1000
            position_ok = current_position + position_size <= self.max_position

            # DEBUG: Log why we're not buying (only first 5 times)
            if not hasattr(self, '_debug_buy_count'):
                self._debug_buy_count = 0

            if self._debug_buy_count < 5:
                log += f" [BUY_CHECK: ema={ema_cross}, cr={change_ratio:.4f}, v={volatility:.1f}, v_ok={volatility_ok}, pos_ok={position_ok}]"
                self._debug_buy_count += 1

            if buy_condition and volatility_ok and position_ok:
                # Risk check before buying
                potential_risk = position_size / capital
                if potential_risk <= self.risk_cap:
                    action = "buy"
                    amount = position_size
                    log += f" [BUY {amount:.1f}]"
                else:
                    log += f" [RISK_BLOCKED {potential_risk:.2f}]"

        # Update tracking
        self.shared_memory["prev_price"] = price
        if action and amount > 0:
            self.shared_memory["last_trade_time"] = current_time

        # Execute buy and update tracking
        if action == "buy":
            fee = amount * self.fee_rate
            self.shared_memory["position_value"] += amount
            self.shared_memory["capital"] -= (amount + fee)
            self.shared_memory["total_fees"] += fee
            self.shared_memory["entry_price"] = price
            self.shared_memory["highest_price"] = price

        self.shared_memory["trade_log"].append({
            "action": action, 
            "amount": amount, 
            "time": current_time, 
            "fee": self.shared_memory["total_fees"]
        })

        # Return log even if no action (for debugging)
        return action, amount, log


class EmotionalSkyBlueViper(QCAlgorithm):
    def Initialize(self):
        self.set_start_date(2024, 4, 19)
        self.set_end_date(2025, 10, 20)
        self.set_account_currency("USD", 100.0)
        self.debug(f"[DEBUG] Initial cash set to: {self.portfolio.cash} USD")

        self.symbol_ticker = "BTCUSD"
        self.add_crypto(self.symbol_ticker, Resolution.MINUTE)

        self.volatility_window = 20
        self.btc_volatility = StandardDeviation(f"{self.symbol_ticker}_VOL", self.volatility_window)
        self.ema_short = ExponentialMovingAverage(f"{self.symbol_ticker}_EMA5", 5)
        self.ema_long = ExponentialMovingAverage(f"{self.symbol_ticker}_EMA20", 20)

        # Optional: Try ATR with proper QuantConnect syntax
        try:
            self.atr_indicator = AverageTrueRange(f"{self.symbol_ticker}_ATR", 14, MovingAverageType.SIMPLE)
            self.register_indicator(self.symbol_ticker, self.atr_indicator, Resolution.MINUTE)
            self.use_atr = True
        except Exception as e:
            self.use_atr = False
            self.debug(f"[DEBUG] ATR initialization failed: {e}, using StandardDeviation")

        self.register_indicator(self.symbol_ticker, self.btc_volatility, Resolution.MINUTE)
        self.register_indicator(self.symbol_ticker, self.ema_short, Resolution.MINUTE)
        self.register_indicator(self.symbol_ticker, self.ema_long, Resolution.MINUTE)

        self.crb = CRB67TradingPlugin()
        self.schedule.on(
            self.date_rules.every_day(), 
            self.time_rules.every(TimeSpan.from_minutes(1)), 
            lambda: self.rebalance()
        )
        self.prev_ema_short = None
        self.prev_ema_long = None
        self.holdings_value = 0.0

    def OnData(self, data):
        if not data.contains_key(self.symbol_ticker) or not data.bars.contains_key(self.symbol_ticker):
            return

        price = data.bars[self.symbol_ticker].close

        # Use ATR if available, otherwise StandardDeviation
        if self.use_atr and self.atr_indicator.IsReady:
            volatility = self.atr_indicator.Current.Value  # Raw ATR value, not percentage
        elif self.btc_volatility.IsReady:
            volatility = self.btc_volatility.Current.Value  # Raw SD value
        else:
            volatility = 30.0

        current_time = self.time.timestamp()

        # Detect EMA crossover
        ema_cross = False
        if (self.ema_short.IsReady and self.ema_long.IsReady and 
            self.prev_ema_short is not None and self.prev_ema_long is not None):
            ema_cross = (self.prev_ema_short < self.prev_ema_long and 
                        self.ema_short.Current.Value > self.ema_long.Current.Value)

        price_data = {"price": price, "ema_cross": ema_cross}
        portfolio_value = self.portfolio[self.symbol_ticker].quantity * price
        self.holdings_value = portfolio_value

        # Get trading decision from CRB plugin
        action, amount, log = self.crb.trading_plugin(
            current_time, 
            price_data, 
            volatility, 
            portfolio_value,
            self.portfolio.cash  # Pass actual cash
        )

        # Log first 10 decisions to debug
        if not hasattr(self, '_log_count'):
            self._log_count = 0
        if self._log_count < 10:
            self.debug(log)
            self._log_count += 1

        if action:
            self.debug(log)
            self.debug(f"[DEBUG] Attempting {action} - Cash: ${self.portfolio.cash:.2f}, Amount: ${amount:.2f}")

            if action == "buy" and self.portfolio.cash >= amount:
                quantity = amount / price
                if quantity > 0:
                    order = self.buy(self.symbol_ticker, quantity)
                    if order.status == OrderStatus.FILLED:
                        self.debug(f"[DEBUG] Bought {quantity:.6f} BTC at ${price:.2f}")
                    else:
                        self.debug(f"[DEBUG] Buy failed: {order.status}")

            elif action == "sell" and self.portfolio[self.symbol_ticker].quantity > 0:
                quantity = min(amount / price, self.portfolio[self.symbol_ticker].quantity)
                if quantity > 0:
                    order = self.sell(self.symbol_ticker, quantity)
                    if order.status == OrderStatus.FILLED:
                        self.debug(f"[DEBUG] Sold {quantity:.6f} BTC at ${price:.2f}")
                    else:
                        self.debug(f"[DEBUG] Sell failed: {order.status}")

        # Update EMA tracking for next crossover detection
        self.prev_ema_short = self.ema_short.Current.Value if self.ema_short.IsReady else None
        self.prev_ema_long = self.ema_long.Current.Value if self.ema_long.IsReady else None

    def rebalance(self):
        """Check for trailing stop triggers during scheduled rebalance"""
        if self.portfolio[self.symbol_ticker].quantity > 0:
            current_price = self.securities[self.symbol_ticker].price

            # Use ATR if available, otherwise StandardDeviation
            if self.use_atr and self.atr_indicator.IsReady:
                volatility = self.atr_indicator.Current.Value  # Raw value
            elif self.btc_volatility.IsReady:
                volatility = self.btc_volatility.Current.Value  # Raw value
            else:
                volatility = 30.0

            portfolio_value = self.portfolio[self.symbol_ticker].quantity * current_price

            price_data = {"price": current_price, "ema_cross": False}
            action, amount, log = self.crb.trading_plugin(
                self.time.timestamp(), 
                price_data, 
                volatility, 
                portfolio_value,
                self.portfolio.cash  # Pass actual cash
            )

            if action == "sell":
                quantity = min(amount / current_price, self.portfolio[self.symbol_ticker].quantity)
                if quantity > 0:
                    order = self.sell(self.symbol_ticker, quantity)
                    if order.status == OrderStatus.FILLED:
                        self.debug(f"[REBALANCE] {log}")
                    else:
                        self.debug(f"[REBALANCE] Sell failed: {order.status}")

    def OnEnd(self):
        """Report final portfolio value"""
        final_cash = self.portfolio.cash
        final_holdings = self.holdings_value
        usd_equivalent = final_cash + final_holdings
        total_fees = self.crb.shared_memory.get("total_fees", 0.0)
        total_trades = len([t for t in self.crb.shared_memory["trade_log"] if t["action"] is not None])

        self.debug(f"[CRB67 FINAL REPORT]")
        self.debug(f"  Cash: ${final_cash:.2f} USD")
        self.debug(f"  Holdings: ${final_holdings:.2f} USD")
        self.debug(f"  Total Value: ${usd_equivalent:.2f} USD")
        self.debug(f"  Total Fees: ${total_fees:.2f} USD")
        self.debug(f"  Total Trades: {total_trades}")
        self.debug(f"  Return: {((usd_equivalent - 100) / 100 * 100):.2f}%")
