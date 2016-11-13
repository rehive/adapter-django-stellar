import json
import urllib.parse
from decimal import Decimal


def input_to_json(metadata):
    if metadata:
        if type(metadata) is str:
            return json.loads(metadata)
        else:
            return metadata
    else:
        return json.loads('{}')


def to_cents(amount: Decimal, divisibility: int) -> int:
    return int(amount * Decimal('10')**Decimal(divisibility))


def from_cents(amount: int, divisibility: int) -> Decimal:
    return Decimal(amount) / Decimal('10')**Decimal(divisibility)


def create_qr_code_url(value, size=300):
    url = "https://chart.googleapis.com/chart?%s" % urllib.parse.urlencode({'chs': size,
                                                                            'cht': 'qr',
                                                                            'chl': value,
                                                                            'choe': 'UTF-8'})
    return url
