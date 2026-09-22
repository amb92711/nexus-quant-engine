import urllib.request
import json
import logging

class DataIngestion:
    """Low-Latency REST Fallback for Orderbook & Options Chain"""
    @staticmethod
    def fetch(url):
        req = urllib.request.Request(url, headers={'User-Agent': 'Nexus-Quant-Institution/2.0'})
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            logging.error(f"API Latency/Failure: {e}")
            return None

    @staticmethod
    def get_deribit_chain():
        data = DataIngestion.fetch("https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option")
        return data['result'] if data else []

    @staticmethod
    def get_gateio_orderbook():
        data = DataIngestion.fetch("https://api.gateio.ws/api/v4/futures/usdt/order_book?contract=BTC_USDT&limit=100")
        return data if data else {}
