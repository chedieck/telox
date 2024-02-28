from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
from config import LOG_LEVEL
import subprocess
import json
import asyncio
import hashlib
import logging
from pathlib import Path
import json



CURL_ARGS = str("""--compressed"""
                """ -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0'"""
                """ -H 'Accept: */*'"""
                """ -H 'Accept-Language: en-US,en;q=0.5'"""
                """ -H 'Accept-Encoding: gzip, deflate, br'"""
                """ -H 'x-nextjs-data: 1'"""
                """ -H 'Connection: keep-alive'"""
                """ -H 'Sec-Fetch-Dest: empty'"""
                """ -H 'Sec-Fetch-Mode: cors'"""
                """ -H 'Sec-Fetch-Site: same-origin'""")


MAX_DESCIPTION_SIZE = 600
NEW_ADS_LIMIT = 10


Path("logs/").mkdir(exist_ok=True)
log_format_string = '[%(name)-4s][%(levelname)8s](%(asctime)s): %(message)s'
log_formatter = logging.Formatter(log_format_string)
logging.basicConfig(
    level=logging.ERROR,
    format=log_format_string,
)

scan_logger = logging.getLogger('scan')
scan_logger.setLevel(LOG_LEVEL)
scan_file_handler = logging.FileHandler('logs/scan.log')
scan_file_handler.setFormatter(log_formatter)
scan_logger.addHandler(scan_file_handler)


def curl_request(url):
    curl_command = f'curl \'{url}\' {CURL_ARGS}'
    process = subprocess.Popen(curl_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    return out


async def async_curl_request(url):
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        curl_command = f'curl \'{url}\' {CURL_ARGS}'
        # Use run_in_executor to run the blocking function in a separate thread
        result = await loop.run_in_executor(pool, lambda: subprocess.run(curl_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
        return result.stdout



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
        self.imovelData = {}
        self.phone = None
        self.zipcode = None
        self.condominio = None
        self.garage_spaces = None
        self.bathrooms = None
        self.rooms = None
        self.size = None
        self.iptu = None
        self.full_price = None
        self.full_label = None

    async def update_detailed_data(self):
        """Update the Ad's location & description data, which is not present in the `raw_ad_list`
        constructor parameter.
        Available properties 27-02-2024:
            'adId',
            'listId',
            'body',
            'subject',
            'priceLabel',
            'priceValue',
            'oldPrice',
            'professionalAd',
            'category',
            'parentCategoryName',
            'categoryName',
            'searchCategoryLevelZero',
            'searchCategoryLevelOne',
            'searchCategoryLevelTwo',
            'origListTime',
            'adReply',
            'planBundleZap',
            'friendlyUrl',
            'hasRealEstateHighlight',
            'loanSpecificData',
            'user',
            'phone',
            'images',
            'videos',
            'location',
            'vehicleSpecificData',
            'properties',
            'pubSpecificData',
            'trackingSpecificData',
            'searchboxes',
            'breadcrumbUrls',
            'featured',
            'carSpecificData',
            'abuyFipePrice',
            'abuyPriceRef',
            'realEstateSpecificData',
            'olxPay',
            'olxDelivery',
            'vehicleReport',
            'vehicleTags',
            'sellerHistory',
            'description',
            'price',
            'listTime',
            'locationProperties',
            'securityTips',
            'denounceLink',
            'nativeVas',
            'isFeatured',
            'chatEnabled',
            'isCompetitionLock',
            'signedPostalCode',
            'slotsId'
        """
        if not self.url:
            return
        page_content = await async_curl_request(self.url)
        soup = BeautifulSoup(page_content, 'html.parser')
        scripts = soup.findAll('script')

        try:
            next_data = next((s for s in scripts if s.has_attr('data-json')), None)
            if next_data == None:
                scan_logger.error("No data-json.")
                return
            data_json = json.loads(next_data['data-json'])
        except TypeError:
            scan_logger.error(f'Type error for ad of URL {self.url}')
            return

        ad_data = data_json.get('ad')
        location_properties = ad_data.get('locationProperties')

        phone_data = ad_data.get('phone')
        phone = phone_data.get("phone") if phone_data else None
        self.phone = phone

        location = ad_data.get('location')
        zipcode = location.get('zipcode') if location else None
        self.zipcode = zipcode

        properties = ad_data.get('properties')
        if properties:
            for prop in properties:
                name = prop.get('name')
                value = prop.get('value')
                if name == 'condominio':
                    self.condominio = value
                if name == 'garage_spaces':
                    self.garage_spaces = value
                if name == 'bathrooms':
                    self.bathrooms = value
                if name == 'rooms':
                    self.rooms = value
                if name == 'size':
                    self.size = value
                if name == 'iptu':
                    self.iptu = value
                if name == 're_rent_full_price':
                    label = prop.get('label')
                    self.full_price = value
                    self.full_label = label
        if location_properties:
            for prop in location_properties:
                if prop['label'] == 'CEP':
                    self.cep = prop['value']
                if prop['label'] == 'Município':
                    self.municipio = prop['value']
                if prop['label'] == 'Bairro':
                    self.bairro = prop['value']

        scan_logger.info(f'——— Got detailed data for {self.title}')
        self.description = ad_data['description']

    def __eq__(self, other):
        """Two ads are equal if their hash property is the same.
        """
        return self.hash == other.hash if other is not None else False

    def __repr__(self):
        if self.full_label and self.full_price:
            price_segment = f"{self.full_label}: <b>R$ {self.full_price}</b>\n"
        else: 
            price_segment = f"Preço: <b>R$ {self.price}</b>\n"
        if self.old_price:
            price_segment = price_segment.rstrip('\n') + f" (de {self.old_price})\n"

        description = self.description
        if len(description) > MAX_DESCIPTION_SIZE:
            description = self.description[:MAX_DESCIPTION_SIZE - 3] + '...'

        zip_code_text = f' <b>{self.zipcode}</b\n>'if self.zipcode else ''
        phone_info = f'Telefone: <b>{self.phone}</b\n>'if self.phone else ''
        price_info = f'(Aluguel: <b>{self.price}</b> Condomínio: <b>{self.condominio}</b> IPTU: <b>{self.iptu}</b>)\n' if self.condominio or self.iptu else ''
        imovel_info = (
            '<i>-------I M Ó V E L {--------\n</i>'
            + price_info +
            f'- Vagas pra garagem: {self.garage_spaces}\n'
            f'- Banheiros: {self.bathrooms}\n'
            f'- Quartos: {self.rooms}\n'
            f'- Área útil: {self.size}\n'
            '<i>-----} I M Ó V E L----------\n</i>'
        ) if self.rooms else ''
        return (
            f"<b>{self.title:^45}</b>\n\n"
            + f"Lugar: <i>{self.municipio} - {self.bairro}</i>{zip_code_text}\n"
            + phone_info
            + imovel_info
            + price_segment
            + "Descrição:\n"
            + f"- {description}\n\n"
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

    def __repr__(self):
        """
        Parameters
        ----------

        url
            URL to be watched.
        """
        return self.url.split('.com.br')[1]


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

    @classmethod
    def get_ad_list(cls, soup: BeautifulSoup) -> List:
        data = soup.find('script', {'id': '__NEXT_DATA__'})
        if data:
            data_string: str
            if type(data) == Tag:
                data_string = data.string or ''
            elif type(data) == NavigableString:
                data_string = str(data)
            else:
                scan_logger.error(f'Data is actually {type(data)}')
                return []
            data_json = json.loads(data_string)
            scan_logger.debug(f'Data JSON on get_ad_list: {data_json}')
            return data_json['props']['pageProps']['ads']
        return []


    async def _update_ad_detailed_data(self, ad: Ad) -> Optional[Ad]:
        await ad.update_detailed_data()  # Ensure this is an async method
        if ad.hash not in self.seen:
            self.seen.add(ad.hash)
            return ad
        return None

    async def update(self) -> List[Ad] | None:
        """Updates `self.ad_list` and `self.last_ad`.

        Returns
        -------

        `None` if nothing changed, the list of new Ads if there are some.
        """
        page_content = curl_request(self.url)
        soup = BeautifulSoup(page_content, 'html.parser')
        scan_logger.debug('Sopa da lista:', soup.get_text())
        ad_list = Watcher.get_ad_list(soup)
        new_ad_list = [Ad(raw_ad) for raw_ad in ad_list if 'subject' in raw_ad.keys()]
        new_ad_list = new_ad_list[:NEW_ADS_LIMIT]
        if Watcher.get_ad_list_hash(new_ad_list) != self.hash:
            tasks = []
            scan_logger.info(f'—— Preparing {len(new_ad_list)} requests for detailed data...')
            for idx, new_ad in enumerate(new_ad_list):
                if new_ad.hash not in self.seen:
                    scan_logger.info(f'——— Will create request for unseen add #{idx:<2} — {new_ad.title}')
                    task = self._update_ad_detailed_data(new_ad)
                    tasks.append(task)

            scan_logger.info(f'—— Gathering detailed data...')
            updated_ads = await asyncio.gather(*tasks)
            ret = [ad for ad in updated_ads if ad]
            scan_logger.info(f'Finished sending requests, updated {len(ret)} ads.')

            self.ad_list = new_ad_list
            return ret
