from bs4 import BeautifulSoup
import requests
import json
import hashlib


HEADERS = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'}


def parse_price(price: str | None) -> str | None:
    if price is None:
        return price
    return price.split(' ')[-1]


class Watcher():
    """
    Attributes
    ----------
    url: str
            URL to be watched.
    ad_list: List[Ad] | None
            List of ads present in the URL.
    last_ad: Ad | None
            Last ad posted on the URL (first ad you would see on the list, when entering the URL)
    seen: List[str] | None
            Ads that were already seen.
    """
    def __init__(self, url: str):
        """
        Parameters
        ----------

        url
            URL to be watched.
        """
        self.url = url
        self.ad_list = None
        self.last_ad = None

        self.seen = []

    def update(self) -> bool:
        """Updates `self.ad_list` and `self.last_ad`.

        Returns
        -------
        True if `self.last_ad` changed, False if not.
        """
        page = requests.get(self.url, headers=HEADERS)
        soup = BeautifulSoup(page.content, 'html.parser')
        scripts = soup.findAll('script')

        data_json = json.loads(next((s for s in scripts if s.has_attr('data-json')), None)['data-json'])
        ad_list = data_json['listingProps']['adList']
        self.ad_list = [Ad(ad) for ad in ad_list if 'subject' in ad.keys()]

        # see if changed:
        prev_ad = self.last_ad
        last_ad = self.ad_list[0]
        if last_ad != prev_ad:
            self.last_ad = last_ad
            if last_ad.hash not in self.seen:
                last_ad.update_specific_info()
                return True
        return False

    def get_last_ad(self, commit=True):
        """Get last ad.

        Parameters
        ----------

        commit
            If this ad should now be added to `seen` list.
        """

        if commit:
            self.seen.append(self.last_ad.hash)
        return self.last_ad


class Ad():
    def __init__(self, adList):
        self.name = adList['subject']
        self.price = parse_price(adList['price'])
        self.old_price = parse_price(adList['oldPrice'])
        self.images = adList['images']
        self.location = adList['location']
        self.url = adList['url']

        # to be set later
        self.cep = None
        self.municipio = None
        self.bairro = None
        self.description = None

    def update_specific_info(self):
        if not self.url:
            return
        page = requests.get(self.url, headers=HEADERS)
        soup = BeautifulSoup(page.content, 'html.parser')
        scripts = soup.findAll('script')

        data_json = json.loads(next((s for s in scripts if s.has_attr('data-json')), None)['data-json'])
        location_properties = data_json['ad']['locationProperties']

        for prop in location_properties:
            if prop['label'] == 'CEP':
                self.cep = prop['value']
            if prop['label'] == 'Município':
                self.municipio = prop['value']
            if prop['label'] == 'Bairro':
                self.bairro = prop['value']

        self.description = data_json['ad']['description']

    def __eq__(self, other):
        return self.hash == other.hash if other is not None else False

    def __repr__(self):
        price_segment = f"Preço: <b>R$ {self.price}</b>\n"
        if self.old_price:
            price_segment = price_segment.rstrip('\n') + f" (de {self.old_price})\n"

        return (
            f"<b>{self.name:^45}</b>\n\n"
            + f"Lugar: <i>{self.municipio} - {self.bairro}</i>\n"
            + price_segment
            + f"Descrição: <i>{self.description}</i>\n\n"
            + f'<a href="{self.url}">URL</a>'
        )

    @property
    def hash(self):
        concatenated_info = f'{self.url}{self.price}'
        return hashlib.md5(concatenated_info.encode('utf-8')).hexdigest()
