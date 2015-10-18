# err-holidaybot
An errbot plugin for querying whether colleagues are on holiday using the BambooHR API.

## Usage (Errbot plugin)

The following instructions assume your err bot is set up as per the instructions at http://errbot.net/user_guide/setup/ 

I have only tested this using HipChat, no guarantees it will work with other chat servers.

### Installation

Paste the following command in a private chat with the bot from a bot admin account:

  `!repos install https://github.com/anitawoodruff/err-holidaybot` 
  
(If you have a custom bot prefix, you will need to replace '!' in the line above with your custom prefix)

Note, this plugin is written in Python3 and requires the module `unidecode` so make sure these are installed on the machine running your bot.

### Configuration


