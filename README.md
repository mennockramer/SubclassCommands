# SubclassCommands
Changes RGB lighting or executes user-specified commands based on their currently equipped Destiny 2 subclass.

Note: if you are using this program with SteelSeries Engine, this must be started **after** SteelSeries Engine, as Engine generates a new API port on boot.

# Config file options
## General:
- Int: "subclassCheckInterval": defaults to 10, how often (in seconds) the program checks the user's subclass in the API.
- Bool: "perElementNotSubclass": defaults to false, run specified commands for each element OR each subclass (e.g. Revenant/Behemoth/Shadebinder would have separate entries).
- Bool: "onlyWhileDestinyRunning": defaults to false, only does API calls and runs specified commands while destiny2.exe is running.

## RGB Programs:
- Bool: "useRGBPrograms": defaults to true, whether to change device RGB lights via manufacturer programs
- Several bools under "RGBPrograms": all default to true, whether to change device RGB lights via particular manufacturer program (e.g. Razer Chroma/Synapse)
- Several strings under "colourHexes": defaults to colours sampled from element icons in the API, the colours to set RGB lighting to. Organised into element-specific and subclass-specific.

## Commands:
- Bool: "useCommands": defaults to true, whether to actually run any commands
- Bool: "defaultBatAndSh": defaults to false, runs Arc.bat AND Arc.sh (and other elements, or per subclass) in relative root, as an alternative to config-specified commands.
- Several strings under "commands": defaults to just echoing the element/subclass name, specifies the commands to run. Organised into element-specific and subclass-specific. Use .bat/.sh files if you want to run multiple commands.

If no config file is found, the script will clone from the [default config file on GitHub](https://github.com/mennockramer/SubclassCommands/blob/main/SubclassCommandsConfig-DEFAULT.json).

If you are using this to control devices via Razer or SteelSeries software, `subclassCheckInterval` must be less than 15 for Razer, 60 for SteelSeries, as the Chroma API and the SteelSeries API both require a heartbeat from this application. The default value is 10, so if you haven't changed the config file, you're fine.


# Example use cases of command output
- ~~Changing system RGB to match the subclass ([OpenRGB](https://openrgb.org/) has a CLI and wide compatability).~~ Now supported natively! *only via OpenRGB ~~and SteelSeries Engine~~ right now, see FAQ
- Changing music? I don't know, I made it for the above.


# FAQ
## Why don't you support:

- SteelSeries Engine: Well, as far as I can tell, it *should* work, but the game events don't execute despite returning Code 200

- Corsair/iCue devices: Corsair's way of integrating other programs is more of a closed ecosystem, designed for the developers of the program (in this case Bungie), not for third parties (in this case me).

- MSI: Mystic Light doesn't have a way to interact with it via Python AFAIK. SteelSeries Engine, however, has integration with Mystic Light, and this has integration with SteelSeries Engine, so you'll need that as a middleman.

- ASUS/RoG: With Armoury Crate installed, the code in the Python tutorial changed the lighting, but it reverted after a second. The RESTful API, well it seems like the port wasn't opened by AURA. If someone knows how to make this work, please tell me.

- Razer: Outdated documentation means I can't send the correct initialisation packet. Waiting on info from Razer Support.

- EVGA devices: They have RGB? News to me. 

- SignalRGB: It has it's own Destiny 2 integration.

- Others:

  Do they have a third-party usable SDK/API? If no, then that's why. If yes, I've overlooked them, please create an Issue here, with a link to their documentation on it <3.

  If they don't have a third-party usable SDK/API (eg Corsair), but you do want them to change colours to match your subclass, see if they're supported by [OpenRGB](https://openrgb.org/).

  If so you can use this program's native OpenRGB support (note that OpenRGB works best as a *replacement* for manufacturer RGB software (eg iCue), not in parallel).

## Where'd you get those default colours from?
From elemental icon images in the Bungie API, as used in DIM.

[Arc 7AECF3](https://www.bungie.net/common/destiny2_content/icons/DestinyDamageTypeDefinition_092d066688b879c807c3b460afdd61e6.png)

[Solar F0631E](https://www.bungie.net/common/destiny2_content/icons/DestinyDamageTypeDefinition_2a1773e10968f2d088b97c22b22bba9e.png)

[Void B185DF](https://www.bungie.net/common/destiny2_content/icons/DestinyDamageTypeDefinition_ceb2f6197dccf3958bb31cc783eb97a0.png)

[Stasis 4D88FF](https://www.bungie.net/common/destiny2_content/icons/DestinyDamageTypeDefinition_530c4c3e7981dc2aefd24fd3293482bf.png)

And pure red FF0000 just made sense as an error colour to me.






