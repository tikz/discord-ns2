discord-ns2
====
A Discord bot for NS2 that interacts with your game server via the ServerQuery to get current map, slots and player list. If you run Wonitor and NS2Plus, it can also get the ns2plus.sqlite3 file from your Wonitor URL to fetch some per player statistics not originally available in Wonitor.

For translation or customization, templates.py contains all the messages that are sent to Discord.

Originally made for the NS2 Sudamerica 8v8 server.

Requires Python >= 3.6

### Deploy
```
$ pip install virtualenv
$ cd discord-ns2/
$ virtualenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ mv config_default.py config.py
$ python3 main.py
```