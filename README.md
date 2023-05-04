# OVPNBlockUserFromTelegram
This is the code for blocking OVPN certificates via Telegram bot, based on python-telegram-bot, do not judge strictly))

Blocking occurs instantly, via telnet, the user immediately finds a connection to the server. Connected users access, a list of all certificates, a list of blocked users can also be obtained, and a user certificate unlock is also available.
1. Change the paths where blocked certificates and working certificates are located.
2. Pleased with public constructive comments, this is my first major python code)

config.ini

#id users(use IdBOt)
[USERS]
XXXXX = true 
XXXXX = true
XXXXX = true

[TelegramBot]
token = XXXXXXX-XXX

[group]
group_id = -XXXXXXX

