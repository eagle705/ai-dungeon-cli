#!/usr/bin/env python3

import os
import sys
import asyncio
from gql import gql, Client, WebsocketsTransport, transport
import requests

from abc import ABC, abstractmethod

from typing import Dict

from pprint import pprint

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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

        def settings(temperature, modelType):
            result = self._execute_query('''
            mutation ($input: GameSettingsInput) {  saveGameSettings(input: $input) {    id    gameSettings { id safeMode modelType proofRead temperature textLength directDialog __typename } __typename }}
            ''',                        {
                                            "input":
                                            {
                                                "modelType": modelType,
                                                "directDialog": True,
                                                "safeMode": False,
                                                "temperature": temperature
                                            }
            })
            
            print(result['saveGameSettings']['gameSettings'])
        
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

        
            
        def show():
            text = ''.join([x['text'] for x in self.history])
            print(f'{bcolors.WARNING}{text}{bcolors.ENDC}')
            
            result = self.translate_to_local(text)
            self.en_text = text
            self.local_text = result

            # this could happen within en locale.
            if text != result:
                print(f'{bcolors.OKGREEN}{self.local_text}{bcolors.ENDC}')

        init()

        settings(self.conf.temperature,'griffin' if self.conf.gpt == 2 else 'dragon')

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
            result = self.translate_from_local(text)
            text = result

            try:
                cont(text)
            except asyncio.exceptions.TimeoutError:
                return
            except transport.exceptions.TransportQueryError:
                return
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
        
    def install_mt(self):
        from mt_driver import install_mt
        install_mt(self)

    def install_sr(self):
        from asr_driver import install_asr
        install_asr(self)

    def install_tts(self):
        from tts_driver import install_tts
        install_tts(self)

    def main(self,callback=False,scene=None):
        self.install_mt()
        self.install_sr()
        self.install_tts()
        
        auth_token = self.get_auth_token()

        assert auth_token

        if scene:
            self.boot(auth_token, self.translate_from_local(scene))
        else:
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
                actors[1].lower().startswith('human') or \
                actors[1].lower().startswith('input') or \
                actors[1].lower().startswith('you'):
                actors = actors[::-1]

            print('Actors detected',actors) 

        def qa(q):
            prev_lines = len(self.en_text.split('\n'))
            
            actor_u, actor_a = actors
            self.go(f'{actor_u}: ' + q)

            # wait for answer to be fully-generated. (MAX TRIALS: 5)
            for _ in range(5):
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
                    l_en = ':'.join(l.split(':')[1:])
                    l_local = self.translate_to_local(l_en)
                    self.rollback(max(0,len(t) - i - 1))
                    return l_local

        if callback:
            return qa

        while True:
            user_input = self.user_io.handle_user_input()
            if user_input.startswith('/r'):
                self.rollback(len(user_input)-1)
            elif user_input.startswith('/s'):
                nlines = len(user_input)-1
                text = '\n'.join(self.local_text.split('\n')[-nlines:])
                self.say(text)
            elif user_input.startswith('/qa'):                
                q = user_input[len('/qa'):].strip()
                q = self.listen() if len(q) == 0 else q

                l_local = qa(q)

                self.say(l_local)

                
            else:
                MIC = '<mic>'
                if MIC in user_input:
                    result = self.listen()
                    user_input = user_input.replace(MIC,result)
                    
                self.go(user_input.replace('\\n','\n'))

# -------------------------------------------------------------------------
# MAIN

def line_bot(conf,q_callback):
    channel,secret = conf.linebot.split(',')
    
    from flask import Flask, request, abort

    from linebot import (
        LineBotApi, WebhookHandler
    )
    from linebot.exceptions import (
        InvalidSignatureError, LineBotApiError
    )
    from linebot.models import (
        MessageEvent, TextMessage, TextSendMessage,
    )

    app = Flask(__name__)

    line_bot_api = LineBotApi(channel)
    handler = WebhookHandler(secret)

    @app.route("/callback", methods=['POST'])
    def callback():
        # get X-Line-Signature header value
        signature = request.headers['X-Line-Signature']

        # get request body as text
        body = request.get_data(as_text=True)
        app.logger.info("Request body: " + body)

        # handle webhook body
        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            print("Invalid signature. Please check your channel access token/channel secret.")
            abort(400)

        return 'OK'

    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        q = event.message.text
        
        print('q:',q)
        a = q_callback(event.source.sender_id,q)

        if a == '':
            a = '<empty>'

        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=a))
                
        except LineBotApiError: # time out might happen
            line_bot_api.push_message(
                event.source.sender_id,
                TextSendMessage(text=a))

    line_bot_api.broadcast(
        TextSendMessage(text='GPT-3 is up again. /reset [scene (multiline)] to reset your conversation. This system might be unstable. GPT-3 takes several seconds to process a request.\nMessages starting with / will be regarded as system commands.')
    )

    app.run(threaded=False)

def main():
    try:
        # Initialize the configuration from config file
        file_conf = Config.loaded_from_file()
        cli_args_conf = Config.loaded_from_cli_args()
        conf = Config.merged([file_conf, cli_args_conf])

        if conf.debug:
            activate_debug()

        if conf.linebot != '':
            channels = {}
            def q_callback(source,q):
                source = f'{source}'
                if not source in channels or q.startswith('/reset'):
                    print('Create a channel',source)
                    channels[source] = lambda x:x

                    scene = None
                    if q.startswith('/reset'):
                        scene = q[len('/reset'):].strip()
                        if scene == '':
                            scene = None
                    
                    ai_dungeon = MyAiDungeonGame(conf, None)
                    channels[source] = ai_dungeon.main(callback=True,scene=scene)
                    return f"<started> Now you can talk to me! (Your message '{q}' isn't processed. Please try again!)"

                if q.startswith('/'):
                    return f"Unsupported command: {q}"
                return channels[source](q)
            line_bot(conf, q_callback)
            return

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
