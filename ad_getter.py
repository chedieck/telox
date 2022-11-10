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
        raw_ad_list = data_json['listingProps']['adList']
        self.ad_list = [Ad(raw_ad) for raw_ad in raw_ad_list if 'subject' in raw_ad.keys()]

        # see if changed:
        prev_ad = self.last_ad
        last_ad = self.ad_list[0]
        if last_ad != prev_ad:
            self.last_ad = last_ad
            if last_ad.hash not in self.seen:
                last_ad.update_detailed_data()
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
        self.cep = None
        self.municipio = None
        self.bairro = None
        self.description = None

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
            data_json = json.loads(next((s for s in scripts if s.has_attr('data-json')), None)['data-json'])
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

        return (
            f"<b>{self.title:^45}</b>\n\n"
            + f"Lugar: <i>{self.municipio} - {self.bairro}</i>\n"
            + price_segment
            + f"Descrição: <i>{self.description}</i>\n\n"
            + f'<a href="{self.url}">URL</a>'
        )

    @property
    def hash(self):
        """Hash of the Ad's URL + the Ad's price.
        """
        concatenated_info = f'{self.url}{self.price}'
        return hashlib.md5(concatenated_info.encode('utf-8')).hexdigest()
