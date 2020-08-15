#!/usr/bin/env python3

import os
import sys
import asyncio
from gql import gql, Client, WebsocketsTransport
import requests

from abc import ABC, abstractmethod

from typing import Dict

from pprint import pprint

# NB: this is hackish but seems necessary when downloaded from pypi
main_path = os.path.dirname(os.path.realpath(__file__))
module_path = os.path.abspath(main_path)
if module_path not in sys.path:
    sys.path.append(module_path)

from impl.utils.debug_print import activate_debug, debug_print, debug_pprint
from impl.conf import Config
from impl.user_interaction import UserIo, TermIo


# -------------------------------------------------------------------------
# EXCEPTIONS

# Quit Session exception for easier error and exiting handling
class QuitSession(Exception):
    """raise this when the user typed /quit in order to leave the session"""


# -------------------------------------------------------------------------
# GAME LOGIC

class AbstractAiDungeonGame(ABC):
    def __init__(self, conf: Config, user_io: UserIo):
        self.stop_session: bool = False
        self.session: requests.Session = requests.Session()

        self.conf = conf
        self.user_io = user_io

    def update_session_auth(self):
        self.session.headers.update({"X-Access-Token": self.conf.auth_token})

    def get_auth_token(self) -> str:
        return self.conf.auth_token

## --------------------------------


class MyAiDungeonGame(AbstractAiDungeonGame):
    def __init__(self, conf: Config, user_io: UserIo):
        super().__init__(conf, user_io)

        self.url: str = 'wss://api.aidungeon.io/subscriptions'
        self.custom_scenario_id: str = 'scenario:458625' # custom

    def _execute_query(self, query, params=None):
        return self.gql_client.execute(gql(query), variable_values=params)

    def boot(self, access_token, prompt):
        def init():
            self.websocket = WebsocketsTransport(
                url=self.url,
                init_payload={'token': access_token})
            self.gql_client = Client(transport=self.websocket)

        def create(prompt_x):
            result = self._execute_query('''
            mutation ($id: String, $prompt: String) {  createAdventureFromScenarioId(id: $id, prompt: $prompt) {    id    contentType    contentId    title    description    musicTheme    tags    nsfw    published    createdAt    updatedAt    deletedAt    publicId    historyList    __typename  }}
            ''',
                                     {
                                         "id": self.custom_scenario_id,
                                         "prompt": prompt_x
                                     }
            )
        
            self.adventure_id = result['createAdventureFromScenarioId']['id']
            self.history = None
            if 'historyList' in result['createAdventureFromScenarioId']:
                # NB: not present when self.story_pitch is None, as is the case for a custom scenario
                self.history = result['createAdventureFromScenarioId']['historyList']
                self.history = [{'id':x['id'],'text':x['text']} for x in self.history]

        def alter(id,text):
            result = self._execute_query('''
            mutation ($input: ContentActionInput) {  doAlterAction(input: $input) {    id    actions {      id      text      }    __typename }}
            ''',                        {
                                            "input":
                                            {
                                                "text": text,
                                                "type": "alter",
                                                "id": self.adventure_id,
                                                "actionId": id
                                            }
            })
            self.history = result['doAlterAction']['actions']
        
        def cont(text):
            result = self._execute_query('''
            mutation ($input: ContentActionInput) {  sendAction(input: $input) {    id    actionLoading    memory    died    gameState    __typename  }}
            ''',
                {
                    "input": {
                        "type": "story",
                        "text": text,
                        "id": self.adventure_id
                    }
                })

            result = self._execute_query('''
            query ($id: String, $playPublicId: String) {
                content(id: $id, playPublicId: $playPublicId) {
                    id
                    actions {
                        id
                        text
                    }
                }
            }
            ''',
                {
                    "id": self.adventure_id
                })
            self.history = result['content']['actions']

        from googletrans import Translator
        translator = Translator()

        def en_ko(text):
            return translator.translate(text, dest="ko").text

        self.en_ko = en_ko
            
        def show():
            text = ''.join([x['text'] for x in self.history])
            print(text)
            
            result = en_ko(text)
            self.en_text = text
            self.ko_text = result
            print(self.ko_text)

        init()

        # skip gpt-2
        prompt_x = prompt[:4]
        prompt_y = prompt[4:]
        create(prompt_x)
        show()
        
        # spinning for result
        while len(self.history) == 1:
            cont('')
            show()

        alter(self.history[-1]['id'],prompt_y)
        show()

        def go(text=''):
            result = translator.translate(text, dest="en")
            text = result.text

            cont(text)
            show()

        def rollback(nlines=1):
            for h in self.history[::-1]:
                if nlines <= 0:
                    break

                lines = h['text'].split('\n')
                
                if len(lines) <= nlines:
                    alter(h['id'],'')
                    nlines -= len(lines)
                else:
                    alter(h['id'],'\n'.join(lines[:len(lines)-nlines]))
                    nlines = 0
            show()
                
        self.go = go
        self.rollback = rollback

    def main(self):
        auth_token = self.get_auth_token()

        assert auth_token

        with open(self.conf.scene) as f:
            self.boot(auth_token, f.read())

        from collections import Counter
        cands = [l.split(':')[0].strip() for l in self.en_text.split('\n')]
        c = Counter(cands)
        del c['']

        actors = [x[0] for x in c.most_common(2)]
        
        if len(actors) == 2:
            if cands.index(actors[0]) > cands.index(actors[1]) or \
                actors[0].lower().startswith('agent') or \
                actors[1].lower().startswith('user') or \
                actors[1].lower().startswith('you'):
                actors = actors[::-1]

            print('Actors detected',actors)

        def say(text):
            import subprocess
            subprocess.run(['say',text])

        def listen():
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            mic = sr.Microphone()
            
            print('Recording...')
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source)

            result = recognizer.recognize_google(audio,language='ko-KR')
            print('Listened: ',result)
            return result

        while True:
            user_input = self.user_io.handle_user_input()
            if user_input.startswith('/r'):
                self.rollback(len(user_input)-1)
            elif user_input.startswith('/s'):
                nlines = len(user_input)-1
                text = '\n'.join(self.ko_text.split('\n')[-nlines:])
                say(text)
            elif user_input.startswith('/qa'):
                prev_lines = len(self.en_text.split('\n'))
                actor_u, actor_a = actors
                self.go(f'{actor_u}: ' + listen())

                # wait for answer to be fully-generated.
                while True:
                    found = False
                    t = self.en_text.split('\n')[prev_lines:]
                    for i,l in enumerate(t):
                        if l.startswith(actor_a):
                            found = i < (len(t) - 1)
                            break
                    if found:
                        break

                    self.go('')
                            
                t_en = self.en_text.split('\n')[prev_lines:]
                
                for i,l in enumerate(t_en):
                    if l.startswith(actor_a):
                        l_ko = self.en_ko(':'.join(l.split(':')[1:]))
                        say(l_ko)
                        self.rollback(max(0,len(t) - i - 1))
                        break
            else:
                MIC = '<mic>'
                if MIC in user_input:
                    result = listen()
                    user_input = user_input.replace(MIC,result)
                    
                self.go(user_input.replace('\\n','\n'))

# -------------------------------------------------------------------------
# MAIN

def main():
    try:
        # Initialize the configuration from config file
        file_conf = Config.loaded_from_file()
        cli_args_conf = Config.loaded_from_cli_args()
        conf = Config.merged([file_conf, cli_args_conf])

        if conf.debug:
            activate_debug()

        # Initialize the terminal I/O class
        term_io = TermIo(conf.prompt)

        # Initialize the game logic class with the given auth_token and prompt
        ai_dungeon = MyAiDungeonGame(conf, term_io)

        # Clears the console
        term_io.clear()

        # Login
        ai_dungeon.main()

    except QuitSession:
        term_io.handle_basic_output("Bye Bye!")

    except EOFError:
        term_io.handle_basic_output("Received Keyboard Interrupt. Bye Bye...")

    except KeyboardInterrupt:
        term_io.handle_basic_output("Received Keyboard Interrupt. Bye Bye...")

    except requests.exceptions.TooManyRedirects:
        term_io.handle_basic_output("Exceded max allowed number of HTTP redirects, API backend has probably changed")
        exit(1)

    except requests.exceptions.HTTPError as err:
        term_io.handle_basic_output("Unexpected response from API backend:")
        term_io.handle_basic_output(err)
        exit(1)

    except ConnectionError:
        term_io.handle_basic_output("Lost connection to the Ai Dungeon servers")
        exit(1)

    except requests.exceptions.RequestException as err:
        term_io.handle_basic_output("Totally unexpected exception:")
        term_io.handle_basic_output(err)
        exit(1)


if __name__ == "__main__":
    main()
