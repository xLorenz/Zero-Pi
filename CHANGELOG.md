30/4
    Added new explosion particle type

    Fixed particleSurface rendering bug using particleBuffer surface 

9/5
    Implemented playMusic(nextTrack:str="") function
    Through playlistCopy, a shuffled stuff.playlist[] list it chooses the next track. Music volume can be controlled by global defaultMusicVolume:float = 0.05
    Implemented Music Toggle to main menu and pause menu, controlled by GameplayManager.musicToggle:bool
    Music is controlled through pygame.mixer.music.stop() and play() respectively 
    Sounds and music are now paused on "pausemenu" through pygame.mixer.music.pause()/.unpause() and pygame.mixer.pause()/.unpause()

    Added music: 
        Another Day
        Holy Moly
        Honey Pie
        How to Tell
        I Love U
        Ocean Blue
        Outside
        You're Never Alone
    
    Added translations

12/5
    Updated Save() to a serialization method to work with json (default save file stored in "save copy.json")
    Added .toDict() and .fromDict() to almost every objet

    Updated "dot" particles to respond to gravity

    Added screen shake, from GameplayManager.generateScreenShake(self, seconds:float)
    Screen shake is updated every frame in GameplayManager.updateScreenPos(self) 
    Every frame as long as GameplayManager.shakeTime > 0 and GameplayManager.shakeToggle, 
    GameplayManager.scrBlitPos is swapped by a random uniform vector stored in GameplayManager.shakePos[] 
    screen is blitted onto scr using game.scrBlitPos 
    If conditions dont meet then GameplayManager.scrBlitPos = (0,0)
    This last is forced when in "pausemenu" or "deathmenu"

    Nerfed grenade by reducing damage 10 -> 7 
    Nerfed grenade by reducing radius 100 -> 70

    Grenade now explodes on impact regardless of velocity

    Optimized explosion() to use squared lengths

    Explosion now generates screen shake relative to the damage and size

    Juggernaught now generates screen shake when spawned

    Ultimate now generates screen shake when charged and during use

    Damage taken to the player generates screen shake

    Added translations
14/5
    Created new SnakePet() ( w.i.p. )
    It will wander around the screen randomly until it gets too tired and goes to sleep, curling up
    This will take 100s and will sleep between 20s and 1.5m
    The more tired the pet is the less it'll walk
    If a juggernaught is in screen, it will wake up and follow the player
    If a fairy is in screen, it will follow it

    The pet will slowly "age", growing longer by one point every 5m. 

    The pet will also blink cutely

    Changed Lizard.walkStrech() to be more reliable and optimized
    Added eyelidColor to Lizard() 
    Added borderRadius to Lizard()

    p2

    Nerfed fairyeffect "enemyfreeze" to "enemyslow" slowing them by 50% instead of 100%
    Now "healthsteal" affects 100% of enemies on screen

    Added the posibility for "ring" particles to shrink

    Explosions can now generate a max of 5s of screenshake

    Enemies now give 5 stamina when killed

    fairyeffects[], skills[] and guns[] converted to dictionares of the format:
        dict = {id : {"EN": name, "ES": translation}}
    for easier translation
    These along with enemytypes[] were moved to stuff.py

    Pet will now heal the player when near them with SnakePet.heal(self, player:Player)
    It will heal when in a 100px radius from the player, displaying self.healAura

    When the player is less than 25hp pet will start following 

15/5
    BIG EXPLOSION REWORK
    Now explosions get added to a queue in GamePlaymanager.explosions[] throug explosion()
    Then theyll get processed one per frame every frame trhoug GameplayManager.handleExplosions(self)
    They way explosions are proccessed has been overhauled:
        handleExplosions() process vfx, sfx, collisions with player and snakeBoss the same way as old explosions(), but for enemies does the following:
        Make numpy arrays with enemies x pos, y pos and health respectively
        Use an NJIT function ( C under the hood ) to process trigonometry and assign new health from the numpy arrays
        Go back to handleExplosions() and hit every enemy by the difference between their health and the processed health 
    Explosions now adds an explosion to the queue instead of processing them
    

    Fixed a bug where "grenade" would explode and not reset when exploded on progress == 0

    Now "settings" are saved on game exit on settings.json, this includes any pets aquired

    Pets are now given to the player when killed a boss

    Boss Spawners now spawn only one type of enemy, between 10 and 25 + radius//10 and explode when opened

    The game window is no longer rezisable

    p2 

    Reworked scrollingbg.py into perlin.py ( thnks Claude! ) 
    Now scrollingBackground is an object

    Added fog using a transparent scrollingBackground
    ScrollingBackground and fog are initialized in particlethread and the fog scrolls inside the thread in particleSurface

    Reworked glow computation for particles
    Now it computes glow for each radii the particle could get to

    RandomizeColorHue() now returns int values, this was to minimize glowcache key generation ( plans to reduce it further by computing every r//2 or 5 )

    ParticleSurface now renders behind the gui in the main menu

    Buffed "enemyslow" now slows for 85% ( *0.15)

16/5
    Retouched Fog
    Changed Particles render order in partFunc and when called in processExplosions 
    Rendering of "text" particles from plain text to surfaces

17/5
    Tweaked explosion particles fadeout
    Tweaked pet AI

    Nerfed "rapidfire" to last 4 seconds
    Buffed "bulletrain" to spawn 22 bullets in a 360 for 5 seconds in a "default" interval

    Fog now changes to red in bossfight

18/5
    Now enemies spawn up to 10 random types from spawnableEnemyTypes per round past round 25
    Fixed a bug where "implosion" would move enemies when game paused
    
    Pet now does a little cute skeak bc its so cute

19/5 
    Added ENDLESS MODE 
        When started player has the option to choose weapons and up to ten skills. After that the game continues without pause. The difficulty increases logarithmically from the player kills.

    Fixed a bug where entities in fairyEffect woudnt save correctly
    Entities from fairyEffects are now independent classes ( possible turrer skill? )

    pt

    CHANGED GAME NAME: "Zero π"

    Redesigned Pause menu

    Moved Endless Mode button
    Endless Mode Button now displays endlessmode kill record

20/5
    Implemented a fail system when a save fails to load, itll load "save copy.json"

22/5
    Remade whole store system. 
    Eliminated the need for an inventory

    Store is now fully dependant on the dictionaries in stuff.py:
        guns
        skills
        pPurchasableColors
        bgPurchasableColors
    
    Items purchased are kept in gameplaymanager's playerSelectedGun:str, playerSelectedSkillSet:list[str], which are kept and set to the player on game start, skills will be wiped after the first game with them, player cant keep purchased skills or guns for endlessmode.

    todo: add coins and make items dependant on them, delete inventory and reorganize main menu

    This game is so close to completion...

    p2

    Made a drawSkillIcons() function, used in store, main menu ( to draw purchased skills ) and in drawUI().
    Skills no display in rows up to 20 skills per row.
    Chargetime for skills now displays inside the icon using player.damageColor.

    Added coins ( gameplayManager.coins:int ), they display in the store and are saved in setting

    Now item purchases and availability are dependant on coin ammount, a purchase will decrease coins by the items price
    Now player gets to take playerselectedcolor and background to saves and different playthroughs

    CHANGED FONT to SPECTRALSC-SEMIBOLD