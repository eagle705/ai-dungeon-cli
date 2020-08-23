import requests
import json
import subprocess
import speech_recognition as sr

def install_asr(target):
    def nest(audio,url):
        files = {'audio':audio.get_wav_data()}
        resp = requests.post(url, files=files)
        return json.loads(resp.text)['text']

    def beep(type=0):
        urls = [
            'https://raw.githubusercontent.com/nakosung/ai-dungeon-cli/master/res/PremiumBeat_0013_cursor_selection_02.wav',
            'https://raw.githubusercontent.com/nakosung/ai-dungeon-cli/master/res/PremiumBeat_0046_sci_fi_beep_electric_2.wav'
        ]
        url = urls[type]
        command = f'''curl "{url}" --output - | play -t wav -'''
        subprocess.Popen(command, shell=True, stderr=subprocess.DEVNULL)

    def listen():
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        
        print('Calibrating Mic...')
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            print('Recording...')
            beep(1)
            audio = recognizer.listen(source,phrase_time_limit=5)

        while True:
            try:
                if target.conf.asr == 'google':
                    result = recognizer.recognize_google(audio,language=target.conf.locale)
                elif target.conf.asr.startswith('nest'):
                    result = nest(audio,url=target.conf.asr.split(',')[1])
                break
            except sr.UnknownValueError:
                print('Got a ASR error / retry')
                continue
        print('Listened: ',result)
        beep(0)
        return result

    target.listen = listen    