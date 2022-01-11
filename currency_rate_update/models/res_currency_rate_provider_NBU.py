# Copyright 2009 Camptocamp
# Copyright 2009 Grzegorz Grzelak
# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from collections import defaultdict
import requests
from datetime import datetime
from dateutil import rrule
from lxml import etree as ET

from odoo import fields, models


class ResCurrencyRateProviderNBU(models.Model):
    _inherit = "res.currency.rate.provider"

    service = fields.Selection(selection_add=[("UA_NBU", "National Bank of Ukraine")])

    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service != "UA_NBU":
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
        root = ET.fromstring(response.content)
        if 'date' in url:
            for child in root.iter('ROW'):
                rate = 1 / float(child.find('Amount').text)
                rate_date = str(datetime.strptime(child.find('StartDate').text, '%d.%m.%Y').date())
                cc = child.find('CurrencyCodeL').text
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
            url = "https://bank.gov.ua/NBU_Exchange/exchange?date={}"
            # url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?date={}"
            # content = self.response(url.format(datetime.strftime(date_to, '%Y%m%d')), currencies, content)
            content = self.response(url.format(datetime.strftime(date_to, '%d-%m-%Y')), currencies, content)
        else:
            urls_date = []
            for dt in rrule.rrule(rrule.DAILY,
                                  dtstart=date_from,
                                  until=date_to):
                urls_date.append((dt.strftime('%d-%m-%Y')))
                url = "https://bank.gov.ua/NBU_Exchange/exchange?date={}"
                for i in range(len(urls_date)):
                    content = self.response(url.format(urls_date[i]), currencies, content)
        if invert_calculation:
            for k in content.keys():
                base_rate = float(content[k][base_currency])
                for rate in content[k].keys():
                    content[k][rate] = str(float(content[k][rate]) / base_rate)
                content[k]["UAH"] = str(1.0 / base_rate)
        return content
