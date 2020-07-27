# This file contains the Strings from __main__.py
PM_START_TEXT = """
Hi {}, my name is {}! If you have any questions on how to use me, read /help - and then head to @MarieSupport.

I'm a group manager bot built in python3, using the python-telegram-bot library, and am fully opensource; \
you can find what makes me tick [here](github.com/KaratekHD/tgbot)!

Feel free to submit pull requests on github, or to contact my support group, @MarieSupport, with any bugs, questions \
or feature requests you might have :)
I also have a news channel, @MarieNews for announcements on new features, downtime, etc.

You can find the list of available commands with /help.
You can also read my documentation at [karatek.net](https://karatek.net/Projects/Nemesisdocs/).

By using Nemesis, you agree to the privacy policies of Karatek Software Development, located at [karatek.net](https://karatek.net/Legal/privacy/).
"""

HELP_STRINGS = """
Hey there! My name is *{}*.
I'm a modular group management bot with a few fun extras! Have a look at the following for an idea of some of \
the things I can help you with. You can also read my documentation at [karatek.net](https://karatek.net/Projects/Nemesisdocs/).

*Main* commands available:
 - /start: start the bot
 - /help: PM's you this message.
 - /help <module name>: PM's you info about that module.
 - /settings:
   - in PM: will send you your settings for all supported modules.
   - in a group: will redirect you to pm, with all that chat's settings.

{}
And the following:
"""

HELP_STRINGS_PART_2 = "\nAll commands can either be used with / or !.\n"

NO_TWO_MODULES = "Can't have two modules with the same name! Please change one"

EDITED_MESSAGE = "This person edited a message"

START_IN_GROUP = "Yo, whadup?"

HELP_FOR_MODULE = "Here is the help for the *{}* module:\n"

ERR_MSG_NOT_MODIFIED = "Message is not modified"

ERR_QUERY_ID_INVALID = "Query_id_invalid"

ERR_MSG_CANT_DELETE = "Message can't be deleted"

ERR_EXCP_HELP_BUTTONS = "Exception in help buttons. %s"

PM_FOR_HELP = "Contact me in PM to get the list of possible commands."

PM_FOR_HELP_BUTTON = "Help"

HELP_FOR_MODULE_AVAILABLE = "Here is the available help for the *{}* module:\n"

CURRENT_SETTINGS = "These are your current settings:"

ERR_NO_USER_SETTINGS = "Seems like there aren't any user specific settings available :'("

Q_SETTINGS_WHICH_MODULE = "Seems like there aren't any chat settings available :'(\nSend this in a group chat you're admin in to find its current settings!"

MODULE_SETTINGS = "*{}* has the following settings for the *{}* module:\n\n"

LOT_OF_SETTINGS = "Hi there! There are quite a few settings for {} - go ahead and pick what you're interested in."

ERR_EXCP_SETTINGS_BUTTONS = "Exception in settings buttons. %s"

CLICK_HERE_FOR_SETTINGS = "Click here to get this chat's settings, as well as yours."

SETTINGS = "Settings"

YOUR_SETTINGS = "Click here to check your settings."

MIGRATING = "Migrating from %s, to %s"

MIGRATING_SUCCESS = "Successfully migrated!"

WEBHOOKS = "Using webhooks."

LONG_POLLING = "Using long polling."

ERR_UNKNOWN = "An uncaught error was raised while handling the error"

ERR_DISPATCHERHANDLERSTOP = "Stopping further handlers due to DispatcherHandlerStop"

ERR_TELEGRAM = "A TelegramError was raised while processing the Update"

ERR_ERRHANDLER = "Error handler stopped further handlers"

ERR_UPDATE_UNKNOWN = "An uncaught error was raised while processing the update"

MODULES_LOADED = "Successfully loaded modules: "