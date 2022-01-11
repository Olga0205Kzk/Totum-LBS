# Copyright 2009 Camptocamp
# Copyright 2009 Grzegorz Grzelak
# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from collections import defaultdict
import requests
from datetime import datetime
from dateutil import rrule
import json

from odoo import fields, models


class ResCurrencyRateProviderPB(models.Model):
    _inherit = "res.currency.rate.provider"

    service = fields.Selection(selection_add=[("UA_PB", "Privatbank of Ukraine")])

    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service != "UA_PB":
            return super()._get_supported_currencies()  # pragma: no cover

        return [
            "USD",
            "JPY",
            "BGN",
            "CYP",
            "CZK",
            "DKK",
            "EEK",
            "GBP",
            "HUF",
            "LTL",
            "LVL",
            "MTL",
            "PLN",
            "ROL",
            "RON",
            "SEK",
            "SIT",
            "SKK",
            "CHF",
            "ISK",
            "NOK",
            "HRK",
            "RUB",
            "TRL",
            "TRY",
            "AUD",
            "BRL",
            "CAD",
            "CNY",
            "HKD",
            "IDR",
            "ILS",
            "INR",
            "KRW",
            "MXN",
            "MYR",
            "NZD",
            "PHP",
            "SGD",
            "THB",
            "ZAR",
            "EUR",
        ]

    def response(self, url, currencies, content):
        response = requests.get(url)
        resp_json = json.loads(response.text)
        for exchange_rate in resp_json['exchangeRate']:
            if 'saleRate' in exchange_rate:
                rate = 1 / float(exchange_rate['saleRate'])
                date = url[url.find('date='):]
                date = date.replace('date=','')
                rate_date = str(datetime.strptime(date, '%d.%m.%Y').date())
                cc = exchange_rate['currency']
                for i in currencies:
                    if cc == i:
                        content[rate_date][cc] = str(rate)
        return content

    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        invert_calculation = False
        if base_currency != "UAH":
            invert_calculation = True
            if base_currency not in currencies:
                currencies.append(base_currency)

        content = defaultdict(dict)
        if date_to == date_from:
            url = "https://api.privatbank.ua/p24api/exchange_rates?json&date={}"
            content = self.response(url.format(datetime.strftime(date_to, '%d.%m.%Y')), currencies, content)
        else:
            urls_date = []
            for dt in rrule.rrule(rrule.DAILY,
                                  dtstart=date_from,
                                  until=date_to):
                urls_date.append((dt.strftime('%d-%m-%Y')))
                url = "https://api.privatbank.ua/p24api/exchange_rates?json&date={}"
                for i in range(len(urls_date)):
                    content = self.response(url.format(urls_date[i]), currencies, content)
        if invert_calculation:
            for k in content.keys():
                base_rate = float(content[k][base_currency])
                for rate in content[k].keys():
                    content[k][rate] = str(float(content[k][rate]) / base_rate)
                content[k]["UAH"] = str(1.0 / base_rate)
        return content
