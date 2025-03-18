import httpx
import logging
import psycopg2
from datetime import datetime
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def fetch_btc_price(request):
    """Fetch Bitcoin price and store in TimescaleDB."""
    try:
        # Fetch BTC price from CoinGecko API
        response = httpx.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        )
        response.raise_for_status()

        data = response.json()
        btc_price = data.get("bitcoin", {}).get("usd")

        if not btc_price:
            return JsonResponse({"error": "Failed to get BTC price data"}, status=400)

        # Store in TimescaleDB (monitoring database)
        timestamp = datetime.now()

        # Connect directly to monitoring database
        conn = psycopg2.connect(
            dbname="monitoring", user="adam", password="adam", host="localhost"
        )

        with conn.cursor() as cursor:
            # Insert the price data
            cursor.execute(
                "INSERT INTO bitcoin_price (time, price) VALUES (%s, %s)",
                [timestamp, btc_price],
            )
            conn.commit()

        conn.close()

        return JsonResponse(
            {
                "success": True,
                "timestamp": timestamp.isoformat(),
                "btc_price_usd": btc_price,
            }
        )

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching BTC price: {e}")
        return JsonResponse({"error": f"API error: {str(e)}"}, status=500)
    except psycopg2.Error as e:
        logger.error(f"Database error storing BTC price: {e}")
        return JsonResponse({"error": f"Database error: {str(e)}"}, status=500)
    except Exception as e:
        logger.error(f"Error processing BTC price: {e}")
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)
