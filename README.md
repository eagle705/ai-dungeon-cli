# GPT-3 Interactive

This work is based on [AI Dungeon CLI](https://github.com/Eigenbahn/ai-dungeon-cli).

Speech-enabled Interactive GPT-3 CLI is integrated with Google Speech Recognition, Google Translation and Apple Text-To-Speech.

#### Examples

The system records spoken Korean language and translates into English using Google Translation. GPT-3 generates responses and the system is translating the conversation back into Korean language and speaking in verbal Korean language using OS/X "Say". You can find out how smooth the conversation flows.

```
[English]
Q: I had presbyopia in my early 40s. What should I do?
A: In the old days, you would simply have got reading glasses for slightly closer work such as reading the newspaper.
Q: Since I'm in my early 40s, I think people will think it's strange to use a magnifying glass. Is there any other alternative?
A: If you can affort to, then you should see an eye doctor to see if anything can be done for your presbyopia.
Q: What methods do ophthalmologists have to treat presbyopia?
A: You may be able to benefit from new technologies such as monovision lens implants or small incision lenticule extraction (LASE) and no surgery is required.
Q: Wouldn't such a procedure be expensive?
A: That's all about how much money you have, if you can't affort that, you might want to consider wearing reading glasses or bifocals.
```

``` 
[Korean]
Q : 40 대 초반에 노안이있었습니다. 어떻게해야합니까?
A : 예전에는 신문을 읽는 것과 같이 좀 더 가까운 작업을 위해 돋보기를 가지고 있었을 것입니다.
Q : 40 대 초반이라 사람들이 돋보기를 사용하는 것이 이상하다고 생각할 것 같아요. 다른 대안이 있습니까?
A : 노력할 수 있다면 안과 의사를 만나 노안을 치료할 수 있는지 확인해야합니다.
Q : 안과 의사는 노안을 치료하기 위해 어떤 방법을 사용해야합니까?
A : Monovision 렌즈 임플란트 또는 LASE (small incision lenticule extract)와 같은 새로운 기술의 혜택을받을 수 있으며 수술이 필요하지 않습니다.
Q : 그러한 절차는 비싸지 않습니까?
A : 그것이 얼마나 많은 돈이 있는지에 관한 것입니다. 그렇게 노력할 수 없다면 독서 용 안경이나 이중 초점을 고려하는 것이 좋습니다.
```

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
 

