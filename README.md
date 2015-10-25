# err-holidaybot

An errbot plugin for querying whether colleagues are on holiday using the BambooHR API.

Also contains a standalone python3 script for querying who's out directly from command line, without the need for a bot.

## Usage

Ask it "who's out?" to get a list of who is currently on leave, or "is X in?" to find out if somebody is away and if so when they will be back. (It accepts a few variants on these phrases, try and see).

If connecting to HipChat, the plugin can optionally be configured to look up colleagues from their HipChat handles and pipe up if someone is @mentioned who is currently on leave.

The standalone script is at `whosout.py` - run `./whosout.py --help` for info. Note, you will need a `holidaybot_credentials.cfg` file as per the 'Configuring from file' section below.

### Installation

The following instructions assume your err bot is set up as per the instructions at http://errbot.net/user_guide/setup/ 

Requirements: Python3 and python module `unidecode` on the machine running your bot.

To install, paste the following command in a private chat with the bot from a bot admin account:

  `!repos install https://github.com/anitawoodruff/err-holidaybot` 
  
(If you have a custom bot prefix, you will need to replace '!' in the line above with your custom prefix)

### Configuration

To be of any  use, HolidayBot needs to be configured with BambooHR credentials with access to view who's out.
Optionally, you can also provide it with HipChat credentials so it can pick up on @mentions and pipe up if someone is mentioned who is away.

#### Configuring from file

If you have access to the machine your errbot is running on, you can simply provide a `holidaybot_credentials.cfg` in the same directory where you start up the bot, containing the following: (the HipChat section is optional)

    [BambooHR]
    ApiKey=BAMBOO_API_KEY
    Host=https://api.bamboohr.com
    Company=COMPANY_NAME
    [HipChat]
    Token=HIPCHAT_API_TOKEN
    Host=https://api.hipchat.com
    
Replace the words in all caps as follows:

- `BAMBOO_API_KEY` - a Bamboo API key with read-access to who's out and the directory of all employees. See the Authentication section at http://www.bamboohr.com/api/documentation/ for how to generate a key (_nb. it implies any user should be able to generate a key but that was not my experience, I had to ask someone with admin rights_)
- `COMPANY_NAME` - should match the first part of the BambooHR site for your company (i.e. xxx for xxx.bamboohr.com).
- `HIPCHAT_API_TOKEN` (optional) - a HipChat API token for looking up user handles (you can use the same token your bot uses to connect to HipChat)
    
#### Configuring manually

Paste the following command in a private chat with the bot from a bot admin account:

    !config HolidayBot {
      'BAMBOOHR_APIKEY': 'changeme',
      'BAMBOOHR_COMPANY': 'changeme',
      'BAMBOOHR_HOST': 'https://api.bamboohr.com'}

Again, remember to replace `!` in the above if you have a custom bot prefix.

(Manual HipChat API token configurability coming soon!)
