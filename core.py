from bs4 import BeautifulSoup
from typing import List
import requests
import json
import hashlib


HEADERS = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'}
MAX_DESCIPTION_SIZE = 600


class Ad():
    """
    Attributes
    ----------
    title: str
            Ad's title.
    price: str
            Ad's price.
    old_price: str | None
            Old price (if the seller has reduced the price recently, this info is avaiable).
    image_url_list: Ad | None
            List with all the Ad's images URLs.
    raw_location: List[str] | None
            Ad's raw location info.
    url: str
            Ad's URL.
    cep: str
            Ad's CEP.
    municipio: str
            The name of the Ad's município.
    bairro: str
            The name of the Ad's bairro.
    description: str
            Ad description.
    """
    def __init__(self, raw_ad_list):
        """
        Parameters
        ----------

        raw_ad_list: List
            Raw info of ad list scrapped from OLX.
        """
        self.title = raw_ad_list['subject']
        self.price = parse_price(raw_ad_list['price'])
        self.old_price = parse_price(raw_ad_list['oldPrice'])
        self.image_url_list = [i['original'] for i in raw_ad_list['images']]
        self.raw_location = raw_ad_list['location']
        self.url = raw_ad_list['url']

        # to be set later
        self.cep = ''
        self.municipio = ''
        self.bairro = ''
        self.description = ''

    def update_detailed_data(self):
        """Update the Ad's location & description data, which is not present in the `raw_ad_list`
        constructor parameter.
        """
        if not self.url:
            return
        page = requests.get(self.url, headers=HEADERS)
        soup = BeautifulSoup(page.content, 'html.parser')
        scripts = soup.findAll('script')

        try:
            next_data = next((s for s in scripts if s.has_attr('data-json')), None)
            if next_data == None:
                print("No data-json.")
                return
            data_json = json.loads(next_data['data-json'])
        except TypeError:
            print(f'Type error for ad of URL {self.url}')
            return

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
        """Two ads are equal if their hash property is the same.
        """
        return self.hash == other.hash if other is not None else False

    def __repr__(self):
        price_segment = f"Preço: <b>R$ {self.price}</b>\n"
        if self.old_price:
            price_segment = price_segment.rstrip('\n') + f" (de {self.old_price})\n"

        description = self.description
        if len(description) > MAX_DESCIPTION_SIZE:
            description = self.description[:MAX_DESCIPTION_SIZE - 3] + '...'


        return (
            f"<b>{self.title:^45}</b>\n\n"
            + f"Lugar: <i>{self.municipio} - {self.bairro}</i>\n"
            + price_segment
            + f"Descrição: <i>{description}</i>\n\n"
            + f'<a href="{self.url}">URL</a>'
        )

    @property
    def hash(self):
        """Hash of the Ad's URL + the Ad's price.
        """
        concatenated_info = f'{self.url}{self.price}'
        return hashlib.md5(concatenated_info.encode('utf-8')).hexdigest()


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
    seen: Set[str] | None
            The hash of the Ads that were already seen.
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

        self.seen = set()


    @classmethod
    def get_ad_list_hash(cls, ad_list: List[Ad] | None):
        if ad_list == None:
            return ''
        concatenated_info = ''.join([ad.hash for ad in ad_list])
        return hashlib.md5(concatenated_info.encode('utf-8')).hexdigest()

    @property
    def hash(self) -> str:
        """Hash of all the `ad_list` hashes.
        """
        return Watcher.get_ad_list_hash(self.ad_list)

    def update(self) -> List[Ad] | None:
        """Updates `self.ad_list` and `self.last_ad`.

        Returns
        -------

        `None` if nothing changed, the list of new Ads if there are some.
        """
        page = requests.get(self.url, headers=HEADERS)
        soup = BeautifulSoup(page.content, 'html.parser')
        scripts = soup.findAll('script')
        next_data = next((s for s in scripts if s.has_attr('data-json')), None)
        if next_data == None:
            print("No data-json.")
            return
        data_json = json.loads(next_data['data-json'])
        raw_ad_list = data_json['listingProps']['adList']
        new_ad_list = [Ad(raw_ad) for raw_ad in raw_ad_list if 'subject' in raw_ad.keys()]
        if Watcher.get_ad_list_hash(new_ad_list) != self.hash:
            ret = []
            for new_ad in new_ad_list:
                if new_ad.hash not in self.seen:
                    new_ad.update_detailed_data()
                    self.seen.add(new_ad.hash)
                    ret.append(new_ad)
            self.ad_list = new_ad_list
            return ret
