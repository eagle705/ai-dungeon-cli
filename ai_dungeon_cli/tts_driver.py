import subprocess
import urllib

def install_tts(target):
    def say(text):
        if target.conf.tts == 'say':
            opts = ['-v',target.conf.voice] if target.conf.voice else []
            subprocess.run(['say',*opts,text])
        elif target.conf.tts.startswith('nes'):
            url = target.conf.tts.split(',')[1]
            synthesize = f'curl "{url}/synthesize?speaker={target.conf.voice}&text={urllib.parse.quote(text)}&emotion=0&speed=0&pitch=0&volume=0&format=mp3&use_cache=false"'
            f = subprocess.check_output(synthesize, shell=True, stderr=subprocess.DEVNULL)
            subprocess.Popen(f"curl {url}{f.decode()} --output - | play -t mp3 -", shell=True, stderr=subprocess.DEVNULL)

    target.say = say
