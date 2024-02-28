from logging import INFO

TOKEN = '1234567890:s3crET7El3Gr4mBoT0k3Nd0N@tsh4r3zzzz'
SHOW_NEW_ON_START = False
SCAN_DELAY=45
LOG_LEVEL = INFO

SURF_SKATE_URL = 'https://pr.olx.com.br/regiao-de-curitiba-e-paranagua/esportes-e-ginastica?q=surf%20skate'
AMPLIFICADOR_URL = 'https://www.olx.com.br/instrumentos-musicais/amplificadores-e-microfones/estado-am/regiao-de-manaus'

MY_TELEGRAM_ID = 123456789
MY_GRAMMAS_TELEGRAM_ID = 123456780

URL_TO_CHAT_DICT = {
    SURF_SKATE_URL: [MY_TELEGRAM_ID, MY_GRAMMAS_TELEGRAM_ID],
    AMPLIFICADOR_URL:[MY_GRAMMAS_TELEGRAM_ID]
}
