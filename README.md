# telox
<p align="center" >
<img width="200" height="200" src="https://user-images.githubusercontent.com/21281174/201219494-2f6ab07c-8f7b-407b-87a8-a871a63a6263.png"> 
<p>
<p align="center" >
Scraper para a OLX que envia novos anúncios para usuários pré-definidos, através do Telegram.
</p>

Uso
---
1. Baixe as dependências com `pip install -r requirements.txt`
2. Configure seu bot através do [@BotFather](https://t.me/botfather) no telegram;
3. Coloque o token e as URLs da OLX de interesse no arquivo `config.py` (ver `config.example.py`)
4. `python bot.py`
5. Mande a mensagem `/start` para o bot. 
6. No console deverá aparecer `User of id <SEU_ID> tried starting the bot.`
7. Coloque `<SEU_ID>` no arquivo `config.py`, na variável `CHAT_ID_LIST`.
8. Execute novamente os passos 4 & 5.


**Dica: A informação sobre a ordem na qual devem aparecer os anúncios (mais relevantes, mais novos, etc) vai inclusa na URL.**
