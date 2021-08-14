# SubclassCommands
Executes user-specified commands based on their currently equipped Destiny 2 subclass.

For those who don't have Python installed, a .exe can be found in `/dist`. If you don't trust that, but still want an .exe, use PyInstaller like I did.


Config file options:
- Int: "subclassCheckInterval": defaults to 10, how often (in seconds) the program checks the user's subclass in the API.
- Bool: "perElementNotSubclass": defaults to false, run specified commands for each element OR each subclass (e.g. Revenant/Behemoth/Shadebinder would have separate entries).
- Bool: "defaultBatAndSh": defaults to false, runs Arc.bat AND Arc.sh (and other elements, or per subclass) in relative root, as an alternative to config-specified commands.
- Bool: "onlyWhileDestinyRunning": defaults to false, only does API calls and runs specified commands while destiny2.exe is running.

If no config file is found, the script will clone from the [default config file on GitHub](https://github.com/mennockramer/SubclassCommands/blob/main/SubclassCommandsConfig-DEFAULT.json).


Example use cases:
- Changing system RGB to match the subclass ([OpenRGB](https://openrgb.org/) has a CLI and wide compatability).
- Changing music? I don't know, I made it for the above.


