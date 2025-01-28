import requests
from termcolor import colored
from tabulate import tabulate
import numpy as np
import time

# Функція для отримання поточної ціни
def get_current_price(symbol="XRPUSDT"):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    response = requests.get(url)
    data = response.json()
    return float(data['price'])

# Анімація
def display_animation():
    animation = ["|", "/", "-", "\\"]
    print("Запуск аналізу ринку", end="")
    for i in range(10):
        print(f"\rЗапуск аналізу ринку {animation[i % len(animation)]}", end="")
        time.sleep(0.2)
    print("\rЗапуск аналізу ринку завершено!       ")

# Отримання історичних даних про XRP з Binance API
def get_crypto_data(symbol="XRPUSDT", interval="15m", limit=96):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    prices = [float(candle[4]) for candle in data]  # Отримуємо закриті ціни
    highs = [float(candle[2]) for candle in data]  # Отримуємо максимальні ціни
    lows = [float(candle[3]) for candle in data]  # Отримуємо мінімальні ціни
    return prices, highs, lows

# Розрахунок індикаторів
def calculate_indicators(prices, highs, lows):
    indicators = {}

    # Проста ковзна середня (SMA)
    indicators['SMA'] = sum(prices[-14:]) / 14

    # RSI
    gains = []
    losses = []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        if change > 0:
            gains.append(change)
        else:
            losses.append(abs(change))
    average_gain = sum(gains) / len(gains) if gains else 0
    average_loss = sum(losses) / len(losses) if losses else 0
    rs = average_gain / average_loss if average_loss else 0
    indicators['RSI'] = 100 - (100 / (1 + rs))

    # EMA
    ema = prices[0]
    multiplier = 2 / (len(prices) + 1)
    for price in prices:
        ema = (price - ema) * multiplier + ema
    indicators['EMA'] = ema

    # Bollinger Bands
    sma = indicators['SMA']
    stddev = np.std(prices[-14:])
    indicators['Bollinger Upper'] = sma + (2 * stddev)
    indicators['Bollinger Lower'] = sma - (2 * stddev)

    # ADX (Average Directional Index)
    tr_list = [max(highs[i] - lows[i], abs(highs[i] - prices[i - 1]), abs(lows[i] - prices[i - 1])) for i in range(1, len(prices))]
    tr14 = sum(tr_list[-14:]) / 14
    dx_list = []
    for i in range(1, len(highs)):
        dm_plus = max(highs[i] - highs[i - 1], 0) if highs[i] - highs[i - 1] > lows[i - 1] - lows[i] else 0
        dm_minus = max(lows[i - 1] - lows[i], 0) if lows[i - 1] - lows[i] > highs[i] - highs[i - 1] else 0
        dx = 100 * abs(dm_plus - dm_minus) / (dm_plus + dm_minus) if (dm_plus + dm_minus) != 0 else 0
        dx_list.append(dx)
    indicators['ADX'] = sum(dx_list[-14:]) / 14

    # Stochastic Oscillator
    highest_high = max(highs[-14:])
    lowest_low = min(lows[-14:])
    indicators['Stochastic'] = ((prices[-1] - lowest_low) / (highest_high - lowest_low)) * 100 if highest_high != lowest_low else 0

    # CCI (Commodity Channel Index)
    typical_prices = [(highs[i] + lows[i] + prices[i]) / 3 for i in range(len(prices))]
    sma_tp = sum(typical_prices[-14:]) / 14
    mean_deviation = sum([abs(tp - sma_tp) for tp in typical_prices[-14:]]) / 14
    indicators['CCI'] = (typical_prices[-1] - sma_tp) / (0.015 * mean_deviation) if mean_deviation != 0 else 0

    # Лінії підтримки та опору
    indicators['Support'] = min(lows[-14:])
    indicators['Resistance'] = max(highs[-14:])

    # Рівні Фібоначчі
    max_price = max(highs[-14:])
    min_price = min(lows[-14:])
    diff = max_price - min_price
    fibonacci_levels = [
        {"Level": "0%", "Value": max_price},
        {"Level": "23.6%", "Value": max_price - 0.236 * diff},
        {"Level": "38.2%", "Value": max_price - 0.382 * diff},
        {"Level": "50%", "Value": max_price - 0.5 * diff},
        {"Level": "61.8%", "Value": max_price - 0.618 * diff},
        {"Level": "78.6%", "Value": max_price - 0.786 * diff},
        {"Level": "100%", "Value": min_price},
    ]
    indicators['Fibonacci'] = fibonacci_levels

    # Напрямок ринку
    if indicators['RSI'] < 20 or indicators['EMA'] < prices[-1]:
        indicators['Market Trend'] = "Short"
    elif indicators['RSI'] > 80 or indicators['EMA'] > prices[-1]:
        indicators['Market Trend'] = "Long"
    else:
        indicators['Market Trend'] = "Невизначений тренд"

    return indicators

# Форматування даних для горизонтальної таблиці
def format_horizontal_table(indicators_15m, indicators_1h, indicators_4h, indicators_1d):
    green_bg_white_text = "\033[42m\033[37m"  # Зелений фон, білий текст
    reset_formatting = "\033[0m"  # Скидання форматування

    # Функція для підсвічування тренду
    def highlight_trend(trend):
        if trend == "Short":
            return colored(trend, "red")
        elif trend == "Long":
            return colored(trend, "green")
        return trend

    # Таблиця підтримки, опору і тренду
    table_data = [
        ["Параметр", "15 хвилин", "1 година", "4 години", "1 день"],
        ["Support", f"{indicators_15m['Support']:.2f}", f"{indicators_1h['Support']:.2f}", f"{indicators_4h['Support']:.2f}", f"{indicators_1d['Support']:.2f}"],
        ["Resistance", f"{indicators_15m['Resistance']:.2f}", f"{indicators_1h['Resistance']:.2f}", f"{indicators_4h['Resistance']:.2f}", f"{indicators_1d['Resistance']:.2f}"],
        ["Тренд ринку", highlight_trend(indicators_15m['Market Trend']), highlight_trend(indicators_1h['Market Trend']), highlight_trend(indicators_4h['Market Trend']), highlight_trend(indicators_1d['Market Trend'])]
    ]
    table = tabulate(table_data, headers="firstrow", tablefmt="fancy_grid")

    # Таблиця рівнів Фібоначчі
    fibonacci_table = tabulate(
        [[level['Level'] for level in indicators_1d['Fibonacci']],
         [f"{level['Value']:.2f}" for level in indicators_1d['Fibonacci']]],
        tablefmt="grid"
    )

    return table, fibonacci_table

# Генерація звіту з висновками та таблицею
def generate_report(current_price, indicators_15m, indicators_1h, indicators_4h, indicators_1d):
    print(colored(f"\nПоточна ціна: ${current_price:.2f}", "cyan"))

    # Висновки на основі індикаторів
    print("\nВисновки:")
    if indicators_1h['RSI'] > 80 or indicators_1d['RSI'] > 80:
        print(colored("Ринок перекуплений (RSI > 80). Можливий розворот вниз.", "yellow"))
    if indicators_1h['RSI'] < 20 or indicators_1d['RSI'] < 20:
        print(colored("Ринок перепроданий (RSI < 20). Можливий відскок вгору.", "yellow"))
    if indicators_1h['EMA'] > indicators_1h['SMA'] and indicators_1d['EMA'] > indicators_1d['SMA']:
        print(colored("Ціна у висхідному тренді (EMA > SMA).", "green"))
    if indicators_1h['EMA'] < indicators_1h['SMA'] and indicators_1d['EMA'] < indicators_1d['SMA']:
        print(colored("Ціна у низхідному тренді (EMA < SMA).", "red"))

    # Формування та друк таблиці
    table, fibonacci_table = format_horizontal_table(indicators_15m, indicators_1h, indicators_4h, indicators_1d)
    print(colored("\nТаблиця підтримки, опору та тренду:", "green"))
    print(table)
    print(colored("\nРівні Фібоначчі (1 день):", "green"))
    print(fibonacci_table)

# Основна функція
def main():
    display_animation()  # Анімація перед запуском

    try:
        symbol = input("Введіть торгову пару (наприклад, XRPUSDT або BTCUSDT): ").upper()

        while True:
            # Отримання поточної ціни
            current_price = get_current_price(symbol)

            # Аналіз для таймфрейму 15 хвилин
            prices_15m, highs_15m, lows_15m = get_crypto_data(symbol, "15m", 96)
            indicators_15m = calculate_indicators(prices_15m, highs_15m, lows_15m)

            # Аналіз для таймфрейму 1 година
            prices_1h, highs_1h, lows_1h = get_crypto_data(symbol, "1h", 24)
            indicators_1h = calculate_indicators(prices_1h, highs_1h, lows_1h)

            # Аналіз для таймфрейму 4 години
            prices_4h, highs_4h, lows_4h = get_crypto_data(symbol, "4h", 24)
            indicators_4h = calculate_indicators(prices_4h, highs_4h, lows_4h)

            # Аналіз для таймфрейму 1 день
            prices_1d, highs_1d, lows_1d = get_crypto_data(symbol, "1d", 30)
            indicators_1d = calculate_indicators(prices_1d, highs_1d, lows_1d)

            # Генерація звіту
            generate_report(current_price, indicators_15m, indicators_1h, indicators_4h, indicators_1d)

            time.sleep(900)  # Оновлення кожні 15 хвилин

    except Exception as e:
        print(f"Помилка: {e}")

if __name__ == "__main__":
    main()
