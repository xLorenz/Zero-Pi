from pygame import mixer, font, sndarray, Surface, Rect
import numpy as np
from math import sin
from random import uniform
import json, shutil
import os

font.init()

# pyinstaller --onefile --noconsole --icon="CvsT logoicon.ico" main.py
#fontpath = os.path.join(os.path.dirname(__file__), 'freesansbold.ttf')
fontpath = 'SpectralSC-SemiBold.ttf'

BIGGESTESTESTESTFONT = font.Font(fontpath,200)
BIGGESTESTESTFONT = font.Font(fontpath,150)
BIGGESTESTFONT = font.Font(fontpath,100)
BIGGESTFONT = font.Font(fontpath,60)
BIGFONT = font.Font(fontpath, 45)
SMALLFONT = font.Font(fontpath, 30)
SMALLESTFONT = font.Font(fontpath, 25)
SMALLESTESTFONT = font.Font(fontpath, 15)



def load_json(file_path, backup_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f), False
    except (json.JSONDecodeError, FileNotFoundError, IOError):
        print(f"Error reading {file_path}. Replacing with backup.")
        shutil.copy(backup_path, file_path)
        with open(file_path, 'r') as f:
            return json.load(f), True


def save_json(data, file_path):
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"Error writing to {file_path}: {e}")


def randomizeColorHue(color,m=0.75):
    m = min(1,m)
    color = list(color)

    for index, c in enumerate(color):
        rand = uniform(m,1)
        color[index] = int(c * rand)
    
    return color

def jumpingFont(size, currentime):
    size += int((sin(currentime/125) +2) * 2.5)
    
    bouncyfont = font.Font(fontpath, size)
    return(bouncyfont)

splashtextsES = [
    "Full HD 4k 1 link Mediafire",
    "By xLorenz",
    "Mas circulos que triangulos",
    "Simple, pero complejo",
    "Pithagora's wet dream",
    "A^2 = B^2 + C^2",
    "La suma de los cuadrados de los catetos",
    "3.141592653589793238462643383279502884197...",
    "Pi = 3",
    "Completamente circular",
    "Nah, id win",
    "Re de virgo",
    "Sali a laburar",
    "Loco deja de jugar a los jueguitos",
    "Ahora libre de gluten!",
    "Ahora sin TACC!",
    "Ahora sin azucar!",
    "Cual es el sentido de la vida?",
    "El verdadero sentido de la vida",
    "No saben que mas inventar",
    "#GraciasChatGPT",
    "Vamos redondeando",
    "*chiste malo",
    "Pi por radio cuadrado",
    "La mas larga es de la hipotenusa",
    "La geometria nunca fue tan tryhardeable",
    "Pipi es un gato y vale 9.8696",
    "Triangulo amoroso?",
    "MIRA ESAS CURVAS!",
    "Top gameplay",
    "Torneos competitivos coming soon",
    "Ahora con brillitos!",
    "Ahora con niebla!",
    "Ahora con efectos especiales!",
    "La geometria es tanto una materia de m** como un arte",
    "De que trata?",
    "Uepa!",
    "Opa!",
    "AAA",
    "Como?",
    "Cuando?",
    "Donde?",
    "Por que?",
    "x^2 + y^2 = r^2",
    "sen(x)^2 + cos(x)^2",
    "Dos por Pi por radio",
    "Ni un solo cuadrado?",
    "Como para variar",
    "Juegazo",
    "0 x Pi = 0 ...",
    ":)",
    ":]",
    ":o",
    ":D",
    ":P",
    ">:)",
    "Circulos vs Triangulo",
]
splashtextsEN = [
    "Full HD 4k 1 link Mediafire",
    "By xLorenz",
    "More circles than triangles",
    "Simple, yet complex",
    "Pithagora's wet dream",
    "A^2 = B^2 + C^2",
    "The sum of the squares of the cathetos",
    "3.141592653589793238462643383279502884197...",
    "Pi = 3",
    "Completely round",
    "Nah, id win",
    "Skull emoji",
    "Go get a job",
    "Bro stop playing videogames",
    "Now gluten free!",
    "Now lactose free!",
    "Now sugar free!",
    "Whats the meaning of life?",
    "The true meaning of life",
    "Who comes up with this?",
    "#ThanksChatGPT",
    "Round about",
    "*Dad joke",
    "Pi times radius squared",
    "You make my world go round",
    "Geometry was never so tryhardable",
    "Pipi is a cat and equals 9.8696",
    "Love triangle?",
    "LOOK AT THOSE CURVES!",
    "Top gameplay",
    "Competitive tournaments coming soon",
    "Now with glitter!",
    "Now with fog!",
    "Now with SFXs!",
    "Geometry is both a sh** subject and an art",
    "Whats all this about?",
    "Uepa!",
    "Opa!",
    "AAA",
    "How?",
    "When?",
    "Where?",
    "Why?",
    "x^2 + y^2 = r^2",
    "sen(x)^2 + cos(x)^2",
    "Two Pi radius",
    "Not a single sqare?",
    "Just to mess around",
    "The game",
    "0 x Pi = 0 ...",
    ":)",
    ":]",
    ":o",
    ":D",
    ":P",
    ">:)",
    "Circulos vs Triangulo",
]


datosEs = [
        "El Trickster tiene un halo que nos impide saber cuanta vida tiene",
         "El Speedster es el mas rapido, pero tambien lo son los Kamikazes",
         "Los Kamikazes advertiran cuando esten a punto de explotar con un halo amarillo",
         "El Juggernaught solo se hara mas grande mientras pasen las rondas",
         "Presiona 'ESC' para pausar el juego... pero eso ya lo sabes",
         "Tu Stamina se regenera poco a poco, pero tambien cuando matas enemigos",
         "Son datos, no tips, no es tan dificil el jueguito",
         "El Jefe te esta esperando...",
         "Activa tu habilidad con 'Click Derecho'",
         "Cambia de habilidad usando 'E' y 'Q'"
         "La Ulti es un rayo extremadamente poderoso, dicen que puede matar varios Juggernaughts",
         "La Ulti es muy fuerte... pero no puede contra una simple Hada",
         "Las Hadas pueden aparecer cada vez que mates un enemigo, te traen un regalo!",
         "Existe una precuela de este juego, solo que tiene menos circulos, y menos descargas",
         "Dos y dos son cuatro, cuatro y dos son seis... como era?",
         "La Colmena combina la vida de todos sus miembros a traves de lineas de energia",
         "Dicen la Colmena, a demas de compartir vida, comparten cuenta de Netflix",
         "Cada que veas un Hada matala asi te da una recompensa, o coleccionalas, lo que quieras",
         "Los Normies pueden venir en 3 tamaños: chiqui, gande y gor",
         "La Ulti fue muy dificil de programar, hubiese dicho sin ChatGPT",
         "Aunque no lo creas, ChatGPT no programo este juego... por lo menos la mayoria",
         "No te asustes si escuchas al Juggernaught acercandose, es un amigo! no tengas miedo",
         "De cariño al Juggernaught le dicen Juggo!",
         "Nadie sabe donde de verdad pueden estar los Quantums",
         "Los Quantum podrian estar en cualquier lado, pero son respetuosos y siguen una linea recta",
         "Hay 9 enemigos: Normie, Trickster, Speedster, Hive, Kamikaze, Quantum, Spike, Slime y Guardian",
         "Alguien va a leer esto?",
         "Que le dijo un circulo rojo a uno verde?... Nada, no hablan, pero ellos se entienden",
         "Escribiendo estos datos me doy cuenta que es un juego bastante simple...",
         "Aqui puedes presionar el boton de continuar, o puedes presionar 'ESC'",
         "Presiona 'LSHIFT' para cancelar la aceleracion",
         "No recibiras daño durante el DASH",
         "Puedes detener el DASH donde quieras, solo presiona 'LSHIFT'",
         "Lo estas haciendo enojar...",
         "Si quieres guarda la partida y descansa un rato, pero no cierres el juego",
         "Cada ronda apareceran mas y mas enemigos, hasta que te maten, o exploten tu PC",
         "No quiero desilucionarte, pero no le vas a ganar al jefe",
         "Luego de a batalla con el jefe puedes seguir jugando!",
         "Los Slimes se partiran en enemigos mas pequeños: Slimies",
         "Los Spikes hacen mucha pupa, no te les acerques",
         "Los Guardianes no te van a ir a buscar, pero te molestaran igual",
         "Los Slimes tienen un 75 por ciento de probabilidades de partirse en 2",
         "Los Slimies tambien se partiran cuando los mates si son lo suficientemente grandes"
         "Los Guardianes te atacaran cada 5 segundos... Insoportables",
         "Las Granadas explotaran contra enemigos si van lo suficientemente rapido, o les puedes disparar",
]
datosEn = [
    "The Trickster has a halo that keeps us from knowing how much health it has",
    "The Speedster is the fastest, but so are the Kamikazes",
    "The Kamikazes will flash a yellow halo when they're about to explode",
    "The Juggernaught will only get bigger as the rounds go on",
    "Press 'ESC' to pause the game... but you already knew that",
    "Your Stamina regenerates slowly, but also when you kill enemies",
    "These are facts, not tips, the game isn't *that* hard",
    "The Boss is waiting for you...",
    "Activate your ability with 'Right Click'",
    "Switch abilities using 'E' and 'Q'",
    "The ult is an extremely powerful beam, they say it can kill multiple Juggernaughts",
    "The ult is really strong... but it can't beat a simple Fairy",
    "Fairies might appear every time you kill an enemy, they bring gifts!",
    "There's a prequel to this game, just with fewer circles... and fewer downloads",
    "The Hive shares the health of all its members through energy lines",
    "They say the Hive not only shares health, but also a Netflix account",
    "Every time you see a Fairy, kill it to get a reward — or collect them, your call",
    "Normies can come in 3 sizes: small, big, and fatto",
    "The ult was really hard to code, or so I would've said without ChatGPT",
    "Believe it or not, ChatGPT didn’t code this game... at least not most of it",
    "Don't be scared if you hear the Juggernaught getting closer, he's a friend! Don’t be afraid",
    "As a nickname, they call the Juggernaught 'Juggo'!",
    "Nobody really knows where the Quantums might be",
    "Quantums could be anywhere, but they're polite and follow a straight line",
    "There are 9 enemies: Normie, Trickster, Speedster, Hive, Kamikaze, Quantum, Spike, Slime, and Guardian",
    "Is anyone going to read this?",
    "What did the red circle say to the green one?... Nothing, they don’t talk, but they get each other",
    "Writing these facts made me realize this is a pretty simple game...",
    "Here you can press the continue button, or press 'ESC'",
    "Press 'LSHIFT' to cancel acceleration",
    "You won’t take damage during the DASH",
    "You can stop the DASH wherever you want, just press 'LSHIFT'",
    "You're making it angry...",
    "If you want, save your game and take a break — just don’t close it",
    "Each round will spawn more and more enemies, until they kill you... or your PC explodes",
    "I don’t want to disappoint you, but you’re not going to beat the boss",
    "After the boss fight you can keep playing!",
    "Slimes will split into smaller enemies: Slimies",
    "Spikes hurt a lot, stay away from them",
    "Guardians won’t come looking for you, but they’ll still bother you",
    "Slimes have a 75 percent chance of splitting into 2",
    "Slimies will also split when you kill them, if they’re big enough",
    "Guardians will attack every 5 seconds... Annoying ahh",
    "Grenades will explode against enemies if they are going fast enough, but you can always shoot them",
]


messagesEn = [
    "Everything is going to be OK",
    "Nice job!",
    "Alright, keep going",
    "You are a natural!",
    "Pff, too easy!",
    "Keep going",
    "That's it?",
    "It keeps going?",
    "Easy Peasy",
    "Finally some rest...",
    "What now?",
    "More circles!?",
    "Nice and easy",
    "Not even a sweat",
    "Stupid kids game...",
    "Alright lets go",
    "Take a deep breath",
    "What a wave!",
    "Niiiiiiice",
    "Hurry up!",
    "Are you sure you want to keep going?",
    "So fun!",
    "I am a triangle",
    "They are... circles?",
    "Done.",
]
messagesEs = [
    "Todo va a estar bien",
    "Bien ahi!",
    "Bien, sigue asi",
    "Talento nato!",
    "Uhh facilongo!",
    "Segui",
    "Ya esta?",
    "Sigue stodavia?",
    "Facilito",
    "Alfin un descanso...",
    "Ahora que?",
    "Mas circulos!?",
    "Tranqui",
    "Con los ojos cerrados",
    "Jueguito de nenes...",
    "Bueno vamos",
    "Respira profundo",
    "Que oleada!",
    "Buenaaaaaa",
    "Apurate!",
    "Seguro que quieres seguir?",
    "Divertidisimo!",
    "Soy un triangulo",
    "Son... circulos?",
    "Listo.",
]



enemyTypes = [
    "normie", "trickster", "speedster", "jugg", "hive", "kami", "quantum", "swap", "spike", "slime", "slimy", "guardian",
]

spawnableEnemyTypes = [
    "normie", "trickster", "speedster", "hive", "kami", "quantum", "spike", "slime", "guardian",
]

guns = {
    "default": {"EN": "Default",   "ES": "Por defecto",     "price": 0},
    "burst":   {"EN": "Burst",     "ES": "Ráfaga",          "price": 40},
    "shotgun": {"EN": "Shotgun",   "ES": "Escopeta",        "price": 50},
    "sniper":  {"EN": "Sniper",    "ES": "Franco",          "price": 70},
    "auto":    {"EN": "Auto",      "ES": "Automático",      "price": 130},
    "double":  {"EN": "Double",    "ES": "Doble",           "price": 200},
    "fan":     {"EN": "Fan",       "ES": "Abanico",         "price": 250},
}

skills = {
    "shield":    {"EN": "Shield",     "ES": "Escudo",       "price": 15},
    "dash":      {"EN": "Dash",       "ES": "Impulso",      "price": 25},
    "grenade":   {"EN": "Grenade",    "ES": "Granada",      "price": 50},
    "decoy":     {"EN": "Decoy",      "ES": "Señuelo",      "price": 140},
    "swap":      {"EN": "Swap",       "ES": "Intercambio",  "price": 150},
    "implosion": {"EN": "Implosion",  "ES": "Implosion",    "price": 200},
}

fairyEffects = {
    "bulletrain":    {"EN": "Bullet Rain",       "ES": "LLuvia de Balas"},
    "turrets":       {"EN": "Turrets",           "ES": "Torretas"},
    "airattack":     {"EN": "Air Attack",        "ES": "Ataque Aereo"},
    "missiles":      {"EN": "Missiles",          "ES": "Misiles"},
    "healthrestore": {"EN": "Health Restored",   "ES": "Vida Restaurada"},
    "skrestore":     {"EN": "Skill Restored",    "ES": "Habilidad Restaurada"},
    "ultrestore":    {"EN": "Ultimate Restored", "ES": "Ultimate Restaurada"},
    "enemyslow":     {"EN": "Enemies Slowed",    "ES": "Enemigos Relentizados"},
    "mirrors":       {"EN": "Mirrors",           "ES": "Espejos"},
    "healthsteal":   {"EN": "Health Steal",      "ES": "Roba vidas"},
    "rapidfire":     {"EN": "Rapid Fire",        "ES": "Fuego Rapido"}
}


colors = {
    "negro" : (1,1,1), #kami
    "blanco" : (255,255,255), #bala
    "rojo" : (255, 0, 0), #normie
    "violeta" : (75, 0, 75), #boss
    "purpura" : (255, 0, 255), #trick
    "gris" : (30,30,32), #fondo
    "amarillo" : (255, 255, 0), #hive
    "bordo" : (75, 0, 0), #jugg
    "verdeOsc" : (85, 107, 47), #sped
    "amarilloOsc" : (50, 50, 0), #quantum
    "azul" : (0, 0, 255), 
    "verde" : (0, 255, 0), 
    "celesteTrans" : (0, 255, 255, 70), 
    
    "celeste" : (0, 255, 255), #player
    "celesteOpaco" : (0, 50, 50), #decoy/daño

    "naranja": (255, 165, 0),
    "morado": (128, 0, 128),
    "rosa": (255, 192, 203),
    "marron": (139, 69, 19),
    "grisclaro": (150,150,150),
    "grisoscuro": (5,5,5),
    "lima": (50, 205, 50),
    "dorado": (255, 215, 0),
    "azulmarino": (0, 0, 128),
    "granate": (128, 0, 0),
    "oliva": (128, 128, 0),
    "verdeazulado": (0, 128, 128),
    "índigo": (75, 0, 130),
    "turquesa": (64, 224, 208),
    "melocoton": (255, 218, 185),
    "lavanda": (230, 230, 250),
    "oroviejo": (218, 165, 32),
    "verdefluor": (127, 255, 0),
}


bgPurchasableColors = {
    "bg_black":   {"EN": "Black",     "ES": "Negro",      "color": (0, 0, 0),         "price": 50},
    "bg_white":   {"EN": "White",     "ES": "Blanco",     "color": (255, 255, 255),   "price": 50},
    "bg_red":     {"EN": "Red",       "ES": "Rojo",       "color": (255, 0, 0),       "price": 50},
    "bg_green":   {"EN": "Green",     "ES": "Verde",      "color": (0, 255, 0),       "price": 50},
    "bg_blue":    {"EN": "Blue",      "ES": "Azul",       "color": (0, 0, 255),       "price": 50},
    "bg_yellow":  {"EN": "Yellow",    "ES": "Amarillo",   "color": (255, 255, 0),     "price": 50},
    "bg_orange":  {"EN": "Orange",    "ES": "Naranja",    "color": (255, 140, 0),     "price": 50},
    "bg_purple":  {"EN": "Purple",    "ES": "Púrpura",    "color": (128, 0, 128),     "price": 50},
    "bg_brown":   {"EN": "Brown",     "ES": "Marrón",     "color": (210, 105, 42),    "price": 50},
    "bg_pink":    {"EN": "Pink",      "ES": "Rosa",       "color": (255, 105, 180),   "price": 50}
}

pPurchasableColors = {
    "p_black":   {"EN": "Black",     "ES": "Negro",      "color": (0, 0, 0),         "price": 50},
    "p_white":   {"EN": "White",     "ES": "Blanco",     "color": (255, 255, 255),   "price": 50},
    "p_red":     {"EN": "Red",       "ES": "Rojo",       "color": (255, 0, 0),       "price": 50},
    "p_green":   {"EN": "Green",     "ES": "Verde",      "color": (0, 255, 0),       "price": 50},
    "p_blue":    {"EN": "Blue",      "ES": "Azul",       "color": (0, 0, 255),       "price": 50},
    "p_yellow":  {"EN": "Yellow",    "ES": "Amarillo",   "color": (255, 255, 0),     "price": 50},
    "p_orange":  {"EN": "Orange",    "ES": "Naranja",    "color": (255, 140, 0),     "price": 50},
    "p_purple":  {"EN": "Purple",    "ES": "Púrpura",    "color": (128, 0, 128),     "price": 50},
    "p_brown":   {"EN": "Brown",     "ES": "Marrón",     "color": (210, 105, 42),     "price":50},
    "p_pink":    {"EN": "Pink",      "ES": "Rosa",       "color": (255, 105, 180),   "price": 50}
}



sounds = {
    "pop" : mixer.Sound("audio/pop.wav"),
    "pop1" : mixer.Sound("audio/pop1.mp3"),
    "pop2" : mixer.Sound("audio/pop2.mp3"),
    "damage" : mixer.Sound("audio/damage.wav"),
    "jugg" : mixer.Sound("audio/jugg.mp3"),
    "kill" : mixer.Sound("audio/kill.wav"),
    "liveup" : mixer.Sound("audio/up.wav"),
    "upgrade" : mixer.Sound("audio/upgrade.wav"),
    "ulti" : mixer.Sound("audio/ulti.wav"),
    "boost" : mixer.Sound("audio/boost.wav"),
    "skActivation" : mixer.Sound("audio/SkActivation.mp3"),
    "shieldBreak" : mixer.Sound("audio/shieldBroken.mp3"),
    "skDeactivation" : mixer.Sound("audio/skilldeact.wav"),
    "explosion" : mixer.Sound("audio/explosion.wav"),
    "fireworklaunch" : mixer.Sound("audio/fireworklaunch.wav"),
    "fireworkexplosion" : mixer.Sound("audio/fireworkexplosion.wav"),
    "victorysound" : mixer.Sound("audio/victorysound.wav"),
    "ultimactivation" : mixer.Sound("audio/ultimactivation.wav"),
    "bossgrowl_1" : mixer.Sound("audio/bossgrowl_1.wav"),
    "bossgrowl_2" : mixer.Sound("audio/bossgrowl_2.wav"),
    "fairysound" : mixer.Sound("audio/fairysound.wav"),
    "fairysound1" : mixer.Sound("audio/fairysound1.wav"),
    "easteregg" : mixer.Sound("audio/vine-boom.mp3"),
    "easteregg1" : mixer.Sound("audio/omgbro.mp3"),
    "easteregg2" : mixer.Sound("audio/raah.mp3"),
    "easteregg2" : mixer.Sound("audio/enginerev.mp3"),
    "easteregg3" : mixer.Sound("audio/navi-hey-listen.mp3"),
    "easteregg4" : mixer.Sound("audio/gunshot.wav"),
    "ulticharge" : mixer.Sound("audio/ulticharge.wav"),
    "pet" : mixer.Sound("audio/pet.mp3"),
    "coin": mixer.Sound("audio/coin.wav")
    
}


playlist = [
            "audio/music/Another Day.mp3",
            "audio/music/Holy Moly.mp3", 
            "audio/music/Honey Pie.mp3", 
            "audio/music/How to Tell.mp3", 
            "audio/music/I Love U.mp3", 
            "audio/music/Ocean Blue.mp3",
            "audio/music/Outside.mp3", 
            "audio/music/You're Never Alone.mp3",
            ]

surfaces:dict[str, dict[str,Surface | Rect]] = {}





def randomizeSound(sound, pitch_factor=None, maxtime=0, volume=1):
    """
    Modify the pitch/speed of a sound and play it.
    
    :param sound: pygame.mixer.Sound object
    :param pitch_factor: float, if None a random factor between 0.5 and 1.5 will be used
    :return: float, the pitch factor used
    """

    #Gracias Claude
    if pitch_factor is None:
        pitch_factor = np.random.uniform(0.5, 1.5)
    
    sound_array = sndarray.array(sound)
    
    # Resample the audio data
    indices = np.round(np.arange(0, len(sound_array), pitch_factor)).astype(int)
    indices = indices[indices < len(sound_array)]
    modified_array = sound_array[indices]
    
    # Convert the modified array back to a Pygame Sound object and play
    modified_sound = sndarray.make_sound(modified_array)
    modified_sound.set_volume(volume)
    modified_sound.play(0,maxtime)
    
    return pitch_factor
