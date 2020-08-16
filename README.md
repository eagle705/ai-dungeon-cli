# GPT-3 Interactive

This work is based on [AI Dungeon CLI](https://github.com/Eigenbahn/ai-dungeon-cli).

Speech-enabled Interactive GPT-3 CLI is integrated with Google Speech Recognition, Google Translation and Apple Text-To-Speech.

#### Installation

```
    $ python3 -m pip install -e .
```

## Running

In any case, you first need to create a configuration file.


```
    $ ai-dungeon-cli  --auth-token [your auth token] --scene scenes/qa --locale ko-KR --voice Yuna
```

Specified voice font should be available with OS/X Say command.

## Configuration (optional)

Several things can be tuned by resorting to a config file.

Create a file `config.yml` either:

 - in the same folder in your home folder: `$HOME/.config/ai-dungeon-cli/config.yml`
 - in the same folder as the sources: `./ai-dungeon-cli/ai_dungeon_cli/config.yml`


#### Authentication

Sniff a _Authentication Token_ and use it directly:

```yaml
auth_token: '<MY-AUTH-TOKEN>'
```

To get this token, you need to first login in a web browser to [play.aidungeon.io](https://play.aidungeon.io/).

Then you can find the token either in your browser [localStorage](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage) or in the content of the `connection_init` message of the websocket communication (first sent message).

Either way, developer tools (`F12`) is your friend.


#### Prompt

The default user prompt is `'> '`.

You can customize it with e.g. :

```yaml
prompt: 'me: '
```


## Dependencies

Please have a look at [requirements.txt](./requirements.txt).


## Limitations and future improvements

Right now, the code is over-optimistic: we don't catch cleanly when the backend is down.

A better user experience could be achieved with the use of the [curses](https://docs.python.org/3/library/curses.html) library.

For now `/revert` and `/alter`special actions are not supported.

It would also be nice to add support for browsing other players' stories (_Explore_ menu).


## Support

As you might have heard, hosting AI Dungeon costs a lot of money.

This cli client relies on the same infrastructure as the online version ([play.aidungeon.io](https://play.aidungeon.io/)).

So don't hesitate to [help support the hosting fees](https://aidungeon.io/) to keep the game up and running.


## Author

Nako Sung [@nakosung](https://github.com/nakosung).


## Contributors & acknowledgements

 - TBU
 

