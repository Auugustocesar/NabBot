# NabBot
Nab Bot is a discord bot that uses [Rapptz's discord.py](https://github.com/Rapptz/discord.py). It features commands related to the MMORPG [Tibia](http://www.tibia.com/news/?subtopic=latestnews).

##Requirements
* Python 3.4.2+
* discord.py
* Tested on Windows and Raspbian

##Installing and running
To install discord.py simply run the following on the command line:

```
pip install git+https://github.com/Rapptz/discord.py@async
```

Create a bot token on Discord

```
https://discordapp.com/developers/applications/me
```

Allow the bot to join your server

```
https://discordapp.com/developers/docs/topics/oauth2#bots
```

Define the bots permissions for your server.  
As of 01/Oct/2016, Nab Bot needs the following permissions: 261120 

```
https://discordapi.com/permissions.html
https://discordapp.com/developers/docs/topics/oauth2#adding-bots-to-guilds
```

To run the bot, execute the following command:

```
python nabbot.py
```

##Current features
* Character database to keep track of the member's characters
* Level up and deaths are announced by the bot
* Events can be created by users and announced by the bot
* Items/Monsters database


### Commands
* **/check** *charname*: Shows information about a character.
* **/guild** *guildname*: Shows a list of the online players of a guild.
* **/share** *level*/*playername*: Returns the level range for party experience share for the specified level or character.
* **/itemprice** *itemname*: Returns a list of NPCs that buy the item
* **/deaths** *charname*: Shows a list of the character's recent deaths
* **/stats** *level*/*vocation* or **/stats** *playername*: Shows the total health, mana and capacity for the character or level and vocation specified
* **/online**: Shows a list of the current server's discord users that are online on tibia. It shows their in-game character and discord user.
* **/whois** *discorduser*: Shows the list of Tibia character registered to that discord user.
* And others, like **/levels**, **/events**, **/roles**, etc

<img align="center" src="https://cloud.githubusercontent.com/assets/12865379/14549417/86905512-0274-11e6-87f0-ccbab911c820.png" alt="An example of the /check command">
