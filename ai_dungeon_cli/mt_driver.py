from googletrans import Translator
import requests
import urllib
import json

def install_mt(target):
    loc = target.conf.locale.split('-')[0]

    if loc == 'en':
        def nop(x):
            return x

        target.translate_to_local = nop
        target.translate_from_local = nop
            
    elif target.conf.mt == 'google':
        translator = Translator()

        def translate_to_local(text):
            return translator.translate(text, dest=loc).text

        def translate_from_local(text):
            return translator.translate(text, dest='en').text

        target.translate_to_local = translate_to_local
        target.translate_from_local = translate_from_local
    elif target.conf.mt.startswith('papago'):
        _, papago_id, papago_secret = target.conf.mt.split(',')

        def translate_papago(source,target,srcText):
            if srcText.strip() == '':
                return ''
                
            encText = urllib.parse.quote(srcText)
            data = f"source={source}&target={target}&text=" + encText
            url = "https://openapi.naver.com/v1/papago/n2mt"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Naver-Client-Id":papago_id,
                "X-Naver-Client-Secret":papago_secret,
            }
            resp = requests.post(url,headers=headers,data=data)
            try:
                return json.loads(resp.content)['message']['result']['translatedText']
            except KeyError:
                print('ERROR: ', resp.content)
                return srcText

        def translate_to_local(text):
            return translate_papago('en',loc,text)

        def translate_from_local(text):
            return translate_papago(loc,'en',text)

        target.translate_to_local = translate_to_local
        target.translate_from_local = translate_from_local
