# OLX-SCRAPER

Avisa, via telegram, novos anúncios de alguma URL qualquer.

Deve-se criar um arquivo `variables.py` com 3 variáveis:
`CHAT_ID_LIST`: List com os `chat_id` dos usuário do telegram a serem informados;
`TOKEN`: O token to bot do telegram;
`URL_SEARCH_LIST`: Lista com as URLS da OLX a serem monitoradas. A ordem qual aparecem os anúncios (mais relevantes, mais novos, etc) é definida na URL.
