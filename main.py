import base64
import io
import json
import pygame, math, random, threading, os, time, copy, perlin
from pygame.locals import *

from numba import njit

from PIL import Image, ImageFilter


pygame.init()
pygame.mixer.init()
pygame.mixer.set_num_channels(32)

from stuff import *


scr = pygame.display.set_mode((1300,731)) # 640 x 360?
screen = pygame.Surface((1300,731), pygame.SRCALPHA).convert()
monitor_size = [pygame.display.Info().current_w, pygame.display.Info().current_h] 


import userInterface, lizard


logo = pygame.image.load("gamefiles/CvsT logo.png")
pygame.display.set_icon(logo)
pygame.display.set_caption("Zero pi")

ScrWidth = screen.get_width()
ScrHeight = screen.get_height()
screenRect = pygame.Rect(0,0,ScrWidth,ScrHeight)
dt = 0
currentTime:int = 0

def initSurfaces():
    global surfaces
    surfaces = {
    "bullet":{"surface":pygame.Surface((8,8), pygame.SRCALPHA).convert_alpha(),
              "rect":pygame.Rect(0,0,8,8)},
    "enemies":{"surface":pygame.Surface((ScrWidth, ScrHeight), pygame.SRCALPHA).convert_alpha(),
               "rect":pygame.Rect(0,0,ScrWidth, ScrHeight)},
    "particles":{"surface":pygame.Surface((ScrWidth, ScrHeight), pygame.SRCALPHA).convert_alpha(),
                "rect":pygame.Rect(0,0,ScrWidth, ScrHeight)},
    "particleBuffer": {"surface": pygame.Surface((ScrWidth,ScrHeight), pygame.SRCALPHA).convert_alpha(),
                "rect": pygame.Rect(0,0,ScrWidth, ScrHeight)},
    "ulti":{"surface":pygame.Surface((1800,200)).convert_alpha(),
            "rect":pygame.Rect(0,0,1800,200)},
    "darkSurf":{"surface":pygame.Surface((ScrWidth, ScrHeight), pygame.SRCALPHA).convert_alpha(),
                "rect":pygame.Rect(0,0,ScrWidth, ScrHeight)},
    "guiSurf":{"surface":pygame.Surface((ScrWidth, ScrHeight), pygame.SRCALPHA).convert_alpha(),
                "rect":pygame.Rect(0,0,ScrWidth, ScrHeight)},
    "pauseSurf":{"surface":pygame.Surface((ScrWidth, ScrHeight), pygame.SRCALPHA).convert_alpha(),
                "rect":pygame.Rect(0,0,ScrWidth, ScrHeight)},
    }
    # BULLET
    pygame.draw.circle(surfaces["bullet"]["surface"],colors["blanco"],(4,4),4) # draw default bullet

    # DARK OVERLAY
    surfaces["darkSurf"]["surface"].fill((0,0,0,150))

    # ULT
    surfaces["ulti"]["surface"].fill((0,0,0,0))
    for intensity, width, radius in [(5, 150, 100), (10, 85, 75), (20, 75, 65), (50, 50, 50)]:
        pygame.draw.line(surfaces["ulti"]["surface"], (intensity, intensity, intensity), (100,surfaces["ulti"]["surface"].get_height()/2), (1800,surfaces["ulti"]["surface"].get_height()/2), width)
        pygame.draw.circle(surfaces["ulti"]["surface"], (intensity, intensity, intensity), (100,surfaces["ulti"]["surface"].get_height()/2), radius)
    pygame.draw.line(surfaces["ulti"]["surface"], (255,255,255), (100,surfaces["ulti"]["surface"].get_height()/2), (1800,surfaces["ulti"]["surface"].get_height()/2), 10)
initSurfaces()




class Particle():
    # Pre computed glow
    glowCache = {}

    def __init__(self,type:str,pos:pygame.Vector2|tuple[int,int],color:pygame.Color|tuple[int,int,int],radius:int=1,maxRadius:int=0,speed:int=1,width:int=0, glow:int=0, text:str="", font:pygame.font.Font=SMALLESTFONT,duration:float=0.0, direction = pygame.Vector2(0,-1), trailColor = colors["blanco"]):
        self.type = type
        self.pos = pygame.Vector2(pos)
        self.color = color
        self.width:int = width
        self.glow:int = glow
        
        if self.type == "dot":
            self.radius = random.randint(5,15)
            self.decrease = random.uniform(0.1,0.5)
            angle = random.randint(0,360)
            self.direction = pygame.Vector2(math.cos(angle),math.sin(angle)) if direction.x == 0 and direction.y == -1 else direction
            self.speed = speed
            if len(particles) > 200:
                self.radius = 0
            self.gravity = 2
        
        elif self.type == "ring":
            self.radius = radius
            self.maxRadius = maxRadius
            self.speed = speed
        
        elif self.type == "text":
            self.speed = speed
            self.radius = radius
            self.maxRadius = maxRadius
            self.duration = duration
            txt = font.render(text, True, self.color)
            self.text = pygame.Surface(txt.get_size(), pygame.SRCALPHA)
            self.text.blit(txt, (0,0))
            self.direction = direction
            self.glow = glow
            self.textStr = text
        
        elif self.type == "explosion":
            self.speed = 0
            self.radius = radius
            self.maxRadius = maxRadius
            self.duration = duration
            self.glow = 0
            self.color = list(color)
            self.color += [min(5*self.duration, 255)]
            
            vec = pygame.Vector2(self.radius,0)
            self.polygon = []
            for i in range(20):
                point = pygame.Vector2(self.pos+(vec.rotate(18*i)*(random.uniform(0.2, 0.5) if i%2==0 else random.uniform(1,1.2))))
                self.polygon.append([point.x,point.y])
        
        elif self.type == "firework":
            self.speed = speed 
            self.radius = radius
            self.maxRadius = maxRadius if maxRadius != 0 else 100
            self.duration = duration if duration != 0.0 else random.uniform(0.05,0.5)
            self.glow = glow
            self.color = list(color)
            self.trailColor = trailColor
            self.direction = direction
            self.launched = False
            
        

            

        if self.glow > 0:
            self.precompGlow:pygame.Surface
            self.computeGlow()

    def computeGlow(self):
        for j in range(int(self.radius)+1):
            radius = self.maxRadius - j if self.type == "ring" else abs(int(self.radius) - j)
            width = self.width
            cacheKey = (tuple(self.color),radius,int(width),self.glow)

            if cacheKey not in Particle.glowCache:
                
                surfaceSize = int((radius + self.glow*10) *2)
                glowSurf = pygame.Surface((surfaceSize,surfaceSize), pygame.SRCALPHA).convert_alpha()
                
                #for i in range(self.glow):

                glowColor = list(self.color)

                glowColor[0] = min(255,self.color[0]+50)
                glowColor[1] = min(255,self.color[1]+50)
                glowColor[2] = min(255,self.color[2]+50)
                if len(glowColor) == 3:
                    glowColor.append(min(255,self.glow))
                elif len(glowColor) == 4:
                    glowColor[3] = min(255,self.glow)

                
                pygame.draw.circle(glowSurf,glowColor,(surfaceSize//2,surfaceSize//2),radius+self.glow*2,width+self.glow*2 if width != 0 else 0)
                pygame.draw.circle(glowSurf,(glowColor[0],glowColor[1],glowColor[2],min(glowColor[3]+50,255)),(surfaceSize//2,surfaceSize//2),radius,width+self.glow*2 if width != 0 else 0)

                # Blurr 
                data = pygame.image.tostring(glowSurf, 'RGBA')
                image = Image.frombytes('RGBA', glowSurf.get_size(),data)
                blurrdImage = image.filter(ImageFilter.GaussianBlur(radius=10))
                blurrdSurf = pygame.image.fromstring(blurrdImage.tobytes(), image.size, 'RGBA')

                    
                Particle.glowCache[cacheKey] = blurrdSurf

            self.precompGlow = Particle.glowCache[cacheKey]

    def update(self):

        if self.type == "dot":
            self.direction.y += self.gravity*dt
            self.pos += self.direction * self.speed * dt * 100
            self.radius -= self.decrease * dt * 100

        elif self.type == "ring":
            self.radius += self.speed * dt * 100
            sign = (self.speed > 0) - (self.speed < 0) # -1 if neg, 1 if pos, 0 if 0
            if self.radius*sign > self.maxRadius*sign:
                self.radius = 0

        elif self.type == "text":
            self.pos += self.direction * self.speed*100 * self.duration * dt
            self.duration -= dt
            if self.duration <= 0:
                self.radius = 0

        elif self.type == "explosion":
            self.color[3] = max(min(self.duration, 255),1)
            for i, c in enumerate(self.color[:3]):
                if c-self.duration > 0:
                    self.color[i] = c-self.duration/2
            
            self.duration -= dt
            if self.duration <= 0:
                self.radius = 0

        elif self.type == "firework":
            if not self.launched:
                randomizeSound(sounds["fireworklaunch"], volume=0.5)
                self.launched = True

            self.pos += self.direction * self.speed * dt * 2000
            self.duration -= dt
            # trail 
            particles.append(Particle("dot", self.pos, self.trailColor, speed = 2, direction=pygame.Vector2(-self.direction.rotate(random.randint(-25,25)))))
            # explosion
            if self.duration <= 0 or self.pos.y <= 50:
                for i in range(random.randint(3,10)):
                    particles.append(Particle("ring", self.pos, self.color, self.radius, self.maxRadius+random.randint(-25,25), random.randint(2,10), random.randint(1,5)))
                
                particles.append(Particle("ring", self.pos, self.color, self.radius, self.maxRadius+random.randint(-25,25), random.randint(2,10), random.randint(1,5), glow=self.glow))
                randomizeSound(sounds["fireworkexplosion"], volume=0.5)
                self.radius = 0

    def draw(self,dest:pygame.Surface):
        
        if self.type == "text":
            dest.blit(self.text, self.text.get_rect(center=self.pos))
        
        elif self.type == "explosion":
            pygame.draw.polygon(dest, self.color, self.polygon)

        else:
            pygame.draw.circle(dest,self.color,self.pos,self.radius,self.width)

        if self.glow > 0:
            cacheKey = (tuple(self.color),int(abs(self.radius)),int(self.width),self.glow)

            surf = Particle.glowCache.get(cacheKey, None)
            if surf != None:
                blitpos = (surf.get_rect(center=self.pos))
                dest.blit(surf, blitpos, special_flags=pygame.BLEND_RGBA_ADD)

    def toDict(self) -> dict:
        data = {
            "type": self.type,
            "pos": [self.pos.x, self.pos.y],
            "color": self.color[:3] if isinstance(self.color, pygame.Color) else self.color,
            "width": self.width,
            "glow": self.glow,
            }
        if self.type == "dot":
            data.update({
                "radius": self.radius,
                "decrease": self.decrease,
                "direction": [self.direction.x, self.direction.y],
                "speed": self.speed,
                "gravity": self.gravity
            })
        elif self.type == "ring":
            data.update({
                "radius": self.radius,
                "maxRadius": self.maxRadius,
                "speed": self.speed,
            })
        elif self.type == "text":
            data.update({
                "radius": self.radius,
                "maxRadius": self.maxRadius,
                "speed": self.speed,
                "duration": self.duration,
                "text_str": self.textStr,  # store original string
                "fontsize": self.text.get_height()
            })
        
        elif self.type == "explosion":
            data.update({
                "speed":self.speed,
                "radius":self.radius,
                "maxRadius":self.maxRadius,
                "duration":self.duration,
                "color":self.color,
                "polygon":self.polygon,
            })
        
        elif self.type == "firework":
            data.update({
                "speed":self.speed,
                "radius":self.radius,
                "maxRadius":self.maxRadius,
                "duration":self.duration,
                "trailColor":self.trailColor,
                "direction":[self.direction.x,self.direction.y],
                "launched":self.launched,
            })

        return data
        
    @classmethod
    def fromDict(cls, d:dict):
        type = d["type"]
        pos = tuple(d["pos"])
        color = tuple(d["color"])
        radius = d.get("radius", 1)
        maxRadius = d.get("maxRadius", 0)
        speed = d.get("speed", 1)
        width = d.get("width", 0)
        glow = d.get("glow", 0)
        duration = d.get("duration", 0.0)
        # Retrieve text string if available
        text = d.get("text_str", "")
        font = d.get("fontsize", 25)

        p = cls(type, pos, color, radius, maxRadius, speed, width, glow, text, pygame.font.Font(fontpath, font), duration=duration)

        if type == "dot":
            p.direction = pygame.Vector2(d["direction"])
            p.gravity = d.get("gravity", 2)

        elif type == "text":
            p.textStr = text  # restore text string for serialization
            p.direction = pygame.Vector2(0, -1)
        elif type == "explosion":
            p.color = d["color"]
        elif type == "firework":
            p.launched = d["launched"]

        return p





class LoadBar():
    def __init__(self,pos:pygame.Vector2|tuple[int,int],progress:int|float=0.0,end:int|float=100,fillColor=colors["celeste"],borderColor=colors["blanco"],vertical=False, pixelLength:int=100, pixelWidth:int=15):
        self.pos = pos
        self.progress = progress
        self.end = end
        self.fillColor = fillColor
        self.borderColor = borderColor
        self.vertical = vertical
        self.pixelLength = pixelLength
        self.pixelWidth = pixelWidth

        self.rect:pygame.Rect = pygame.Rect(self.pos[0]-self.pixelLength/2,self.pos[1]-self.pixelWidth/2,self.pixelLength,self.pixelWidth)
    
    def draw(self,dest:pygame.Surface):
        drawpos = self.pos[0]-self.pixelLength//2, self.pos[1]-self.pixelWidth//2
        fill = self.progress/self.end # 0 to 1
        if not self.vertical:
            pygame.draw.rect(dest,self.fillColor,(drawpos[0],drawpos[1],fill*self.pixelLength,self.pixelWidth), border_radius=3)
            pygame.draw.rect(dest,self.borderColor,(drawpos[0],drawpos[1],self.pixelLength,self.pixelWidth), width=3, border_radius=3)
        else:
            pygame.draw.rect(dest,self.fillColor,(drawpos[0],drawpos[1]-fill*self.pixelWidth+self.pixelWidth,self.pixelLength,fill*self.pixelWidth), border_radius=3)
            pygame.draw.rect(dest,self.borderColor,(drawpos[0],drawpos[1],self.pixelLength,self.pixelWidth), width=3, border_radius=3)
        

def loadBar(dest:pygame.Surface, pos:pygame.Vector2|tuple[int,int],progress:int|float=0.0,end:int|float=100,fillColor=colors["celeste"],borderColor=colors["gris"],vertical=False, pixelLength:int=100, pixelWidth:int=15):
    width = pixelLength
    height = pixelWidth
    fill = (progress/end) # from 0 to 1
    if not vertical:
        drawpos = pos[0]-width//2, pos[1]-height//2
        pygame.draw.rect(dest,fillColor,(drawpos[0],drawpos[1],fill*width,height),border_radius=3)
        pygame.draw.rect(dest,borderColor,(drawpos[0],drawpos[1],width,height),width=3,border_radius=3)
        return (drawpos[0],drawpos[1],width,height)

    else:
        drawpos = pos[0]-width//2, pos[1]-height//2
        pygame.draw.rect(dest,fillColor,(drawpos[0],drawpos[1]-fill*pixelWidth+pixelWidth,pixelLength,fill*pixelWidth), border_radius=3)
        pygame.draw.rect(dest,borderColor,(drawpos[0],drawpos[1],pixelLength,pixelWidth), width=3, border_radius=3)
        return (drawpos[0],drawpos[1],width,height)



    


class Bullet():
    def __init__(self, pos:pygame.Vector2 |tuple[int,int], direction:pygame.Vector2):
        global particles
        
        # define attributes
        self.pos:pygame.Vector2 = pygame.Vector2(pos)
        self.direction:pygame.Vector2 = direction * 1500
        self.radius = 4

    def updatePos(self):
        self.pos += self.direction * dt

    def draw(self, dest:pygame.Surface):
        dest.blit(surfaces["bullet"]["surface"], (self.pos[0]-4,self.pos[1]-4))

    def toDict(self) -> dict:
        return {
            "pos":[self.pos.x, self.pos.y],
            "direction":[self.direction.x, self.direction.y],
            "radius":self.radius,
        }
    
    @classmethod
    def fromDict(cls, d):
        b = cls(pygame.Vector2(d["pos"]), pygame.Vector2(d["direction"]))
        b.radius = d["radius"]

        return b


def shoot(pos:pygame.Vector2, direction:pygame.Vector2, gun:str, lastBulletTime:int):
    # pos,direction,lastbullettime
    global bullets
    match gun:
        case "default":
            if lastBulletTime > 0.3:
                bullets.append(Bullet(pos,direction))
                return 0

        case "burst":
            if lastBulletTime > 0.35:
                bullets.append(Bullet(pos,direction))
                bullets.append(Bullet(pos+direction*100, direction))
                return 0

        case "auto":
            if lastBulletTime > 0.1:
                bullets.append(Bullet(pos,direction))
                return 0

        case "double":
            if lastBulletTime > 0.15:
                bullets.append(Bullet(pos+direction.rotate(90)*10,direction))
                bullets.append(Bullet(pos+direction.rotate(-90)*10,direction))
                return 0

        case "fan":
            if lastBulletTime > 0.2:
                bullets.append(Bullet(pos,direction.rotate(5)))
                bullets.append(Bullet(pos,direction))
                bullets.append(Bullet(pos,direction.rotate(-5)))
                return 0

        case "shotgun":
            if lastBulletTime > 0.75:
                for _ in range(6):
                    bullets.append(Bullet(pos+direction*random.randint(-50,100), direction.rotate(random.randint(-15,15))))
                return 0
    
        case "sniper":
            if lastBulletTime > 1:
                for _ in range(15):
                    bullets.append(Bullet(pos, direction))
                return 0
    return lastBulletTime




class Player():
    def __init__(self, color:tuple[int,int,int] | pygame.Color=colors["celeste"], pos:tuple[int,int] = (ScrWidth/2, ScrHeight/2)):
        
        #define attributes

        # grafic
        self.defColor:tuple[int,int,int] | pygame.Color = color
        self.color = self.defColor
        self.damageColor = (self.defColor[0]//5,self.defColor[1]//5,self.defColor[2]//5)
        self.scale:int = 1
        self.drawingPoints:list[pygame.Vector2,pygame.Vector2,pygame.Vector2] = (pygame.Vector2(0,0),pygame.Vector2(1,0),pygame.Vector2(1,1))

        # positional
        self.crosshairPos:tuple[int,int] = (ScrWidth/2, 0)
        self.direction:pygame.Vector2 = pygame.Vector2(self.crosshairPos).normalize()
        
        self.pos:pygame.Vector2 = pygame.Vector2(pos)
        self.velocity:pygame.Vector2 = pygame.Vector2(0,0)
        self.acceleration:pygame.Vector2 = pygame.Vector2(0,0)
        self.friction = 0.85

        self.baseSpeed = 50
        self.speedMultiplier = 1.0
        self.maxSpeed = 150

        # gameplay related
        self.invulnerability:bool = False
        self.invulnerabilityTimer:int = 0
        self.gun:str = "default"
        self.stamina:float = 100
        self.sprinting:bool = False
        self.lastBulletTime:int = 0

        self.fairyEffects:list[FairyEffect] = []

        # skill related
        self.skill:int = 0 # index of skill selected
        self.skillSet:list[Skill] = []
        self.shielded = False

        # key input
        self.keys = {
            pygame.K_e: False,
            pygame.K_ESCAPE: False,
            pygame.K_q: False,
            pygame.K_LSHIFT: False
        }
        self.mouseClick = [False,False,False]
        

        # stats
        self.kills = 0
        self.health = 50

        # ults
        self.ultPoints = 0
        self.ultFiring = False
        self.ultDuration = 0
        self.ultPrimeTime = 0

    def updateColor(self, color):
        self.defColor:tuple[int,int,int] | pygame.Color = color
        self.color = self.defColor
        self.damageColor = (self.defColor[0]//5,self.defColor[1]//5,self.defColor[2]//5)

        for skill in self.skillSet:
            skill.updateColor(self.defColor)

    def getInputs(self, case:str, event = None, mousePos=(0,0), mouseClick = [False,False,False]):
        """
        Handle the inputs of the player: Movent keys, pause, sk switch, mouse pos and clicks
        Use case "push" for pause and switch
        Use case "const" for movement and others    
        """
        if case == "push":
            if event.type == pygame.KEYDOWN: 
                if event.key in self.keys: 
                    self.keys[event.key] = True
                    
            


        elif case == "const":
            self.pressed = pygame.key.get_pressed()
        
            self.crosshairPos = mousePos
            aim = pygame.Vector2(pygame.Vector2(self.crosshairPos)-self.pos)
            if aim != pygame.Vector2(0,0): 
                self.direction = aim.normalize() 

            self.mouseClick = mouseClick

    def move(self): 
        global updateParticles

        if self.keys[pygame.K_e]:
            self.keys[pygame.K_e] = False
            sounds["liveup"].play()
            if self.skill < len(self.skillSet) - 1:
                self.skill += 1
            else:
                self.skill = 0

        if self.keys[pygame.K_q]:
            self.keys[pygame.K_q] = False
            sounds["liveup"].play()
            if self.skill > 0:
                self.skill -= 1
            else:
                self.skill = len(self.skillSet) - 1

        if self.keys[pygame.K_ESCAPE]:
            ...

        # RESET ACC Y VEL IF SHIFT
        if self.keys[pygame.K_LSHIFT]:
            self.keys[pygame.K_LSHIFT] = False       
            self.acceleration = pygame.Vector2(0,0)
            self.velocity = pygame.Vector2(0,0)
   

        # vel changes pos, acc changes vel

        # update acc

        self.acceleration = pygame.Vector2(0,0)

    
        if self.pressed[pygame.K_w]:
            self.acceleration.y = -self.baseSpeed
        if self.pressed[pygame.K_s]:
            self.acceleration.y = self.baseSpeed
        if self.pressed[pygame.K_a]:
            self.acceleration.x = -self.baseSpeed
        if self.pressed[pygame.K_d]:
            self.acceleration.x = self.baseSpeed
    

        # update velocity


        if self.acceleration.length() < self.maxSpeed:
            self.velocity += self.acceleration

        self.velocity *= self.friction

        # update position


        self.pos.x += self.velocity.x * self.speedMultiplier * dt
        self.pos.y += self.velocity.y * self.speedMultiplier * dt


        # RESTRAIN TO SCR
        if self.pos.x > ScrWidth-40:
            self.pos.x = ScrWidth-40
        elif self.pos.x < 40:
            self.pos.x = 40
        if self.pos.y > ScrHeight-40:
            self.pos.y = ScrHeight-40
        elif self.pos.y < 40:
            self.pos.y = 40    

        # sprint ---

        if self.pressed[pygame.K_SPACE]:
            if self.stamina > 0.5:      # it needs more than 0.5 stamina
                if not self.sprinting:
                    randomizeSound(sounds["boost"], maxtime=1000, volume=0.5)
                    self.sprinting = True
                
                self.stamina -= 20 * dt
                self.speedMultiplier = 2
                particles.append(Particle("dot",self.pos,self.color,glow=3))

            else:
                self.speedMultiplier = 1
                self.sprinting = False

        else: # si no se apreta espacio, la stamina sube linearmente por .25
            if self.stamina < 100:
                self.stamina += 0.25 *dt*40
            self.speedMultiplier = 1
            self.sprinting = False

        # shoot ---
        self.lastBulletTime += dt
        if self.mouseClick[0] and not self.ultFiring and (self.ultPrimeTime <= 0 or not self.pressed[pygame.K_x]):
            self. lastBulletTime = shoot(self.pos, self.direction, self.gun, self.lastBulletTime)

        # ult
        if not self.ultFiring and self.ultPoints >= 50:
            if self.pressed[pygame.K_x]:
                if self.ultPrimeTime <= 0:
                    sounds["ulticharge"].set_volume(0.05)
                    sounds["ulticharge"].play(0,1000)
                particle = Particle("dot", self.pos+pygame.Vector2(50,0).rotate(random.randint(0,360)), colors["blanco"], glow=3)
                particle.direction = pygame.Vector2(self.pos-particle.pos).normalize()
                particles.append(particle)
                
                self.speedMultiplier = 0.5
                
                self.ultPrimeTime += 2 * dt
                
                game.generateScreenShake(0.5)

                if self.ultPrimeTime >= 1.5:
                    sounds["ulti"].play()
                    for _ in range(100):
                        p = Particle("dot",self.pos,colors["blanco"],speed=random.randint(3,7))
                        particles.append(p)
                    game.generateScreenShake(5)
                    self.ultFiring = True
                    self.ultPrimeTime = 0
            else:
                if self.ultPrimeTime > 0:
                    self.ultPrimeTime -= dt

        if self.ultFiring:
            # DURATION - 5 seconds
            self.ultDuration += dt
            if self.ultDuration > 5: 
                self.ultFiring = False
                self.ultPoints = 0
                self.ultDuration = 0

        # skill
        if self.skillSet:

            for skill in self.skillSet:
                skill.updateTimer()

            if self.mouseClick[2] and not self.skillSet[self.skill].active and self.skillSet[self.skill].charged:
                self.skillSet[self.skill].active = True
                sounds["skActivation"].play()


            # show icon
            if self.pressed[pygame.K_e] or self.pressed[pygame.K_q]:
                skillShow = pygame.transform.scale(self.skillSet[self.skill].icon, (200,200))
                screen.blit(skillShow,skillShow.get_rect(center=(ScrWidth//2,ScrHeight//2)))

        # fairyeffects
        if self.fairyEffects:
            for effect in self.fairyEffects:
                effect.update(self)
        
        self.fairyEffects = [e for e in self.fairyEffects if not e.delete] 

    def draw(self, dest:pygame.Surface):
        mainPoint:pygame.Vector2 = self.direction*(45*self.scale)
        self.drawingPoints = [self.pos + mainPoint, self.pos + mainPoint.rotate(130) - self.velocity*0.05, self.pos + mainPoint.rotate(-130) - self.velocity*0.05]

        pygame.draw.polygon(dest,self.color,self.drawingPoints)

        # draw ult prime
        if self.ultPrimeTime > 0:
            if self.pressed[pygame.K_x]:
                pygame.draw.circle(dest,colors["blanco"],self.pos,35+5/self.ultPrimeTime,3)
            else: 
                pygame.draw.circle(dest,colors["blanco"],self.pos,35+(1.5-self.ultPrimeTime)*20,3)

        if 1 < self.stamina < 100:
            loadBar(dest,self.pos+(0,55),self.stamina,100,fillColor=self.defColor)

        if self.ultFiring:
            loadBar(dest, self.pos-(0,55),5-self.ultDuration,5,fillColor=colors["blanco"])

        
        
        if self.skillSet:    
            for skill in self.skillSet:
                skill.use(self)
        
        # fairyefects
        if self.fairyEffects:
            for effect in self.fairyEffects:
                effect.draw(self)

    def collisions(self, damage:int=0):
       
        if not self.invulnerability:
            if damage > 0:
                if not self.shielded:
                    self.health -= damage

                    randomizeSound(sounds["damage"],volume=0.3)
                    game.generateScreenShake(0.1*damage)

                    self.color = self.damageColor
                    particles.append(Particle("text",self.pos, self.damageColor,text=f"-{damage}",duration=1, speed=1))
                    for _ in range(10):
                        particles.append(Particle("dot", self.pos,self.color, speed=3))
                self.shielded = False
                self.invulnerability = True
                self.invulnerabilityTimer = 1.5
        
        else:
            if damage == 0:
                self.invulnerabilityTimer -= dt
            
            if self.invulnerabilityTimer <= 0:
                self.color = self.defColor
                self.invulnerability = False

    def ult(self,dest:pygame.Surface):
        
        if self.ultFiring:
            # UPDATE AND DRAW
            angleDegrees = math.degrees(math.atan2(self.direction.y,self.direction.x))
            rotatedUltiSurf = pygame.transform.rotate(surfaces["ulti"]["surface"],-angleDegrees)
            offset = pygame.math.Vector2(800,0)
            rotatedOffset = offset.rotate(angleDegrees) #rotate offset vector (pivot pos)
            rect = rotatedUltiSurf.get_rect(center=(int(self.pos.x+rotatedOffset[0]),int(self.pos.y+rotatedOffset[1])))


            dest.blit(surfaces["darkSurf"]["surface"],(0,0))
            dest.blit(rotatedUltiSurf,rect, special_flags=BLEND_RGB_ADD)

            particles.append(Particle("dot",self.pos,colors["blanco"],speed=random.randint(2,4),glow=3))
            if random.randint(1,10) == 1:
                particles.append(Particle("dot",self.pos+self.direction*random.randint(10,1000),colors["blanco"],glow=3))

            # CALCULATE AND DEAL DAMAGE
            ultVector = self.direction*1800
            ultStart = self.pos
            ultEnd = self.pos + ultVector


            ab = ultEnd - ultStart
            abLength = ab.length()

            for enemy in enemies:
                # vector from ult to en
                ap = enemy.pos - ultStart

                # perp distance using cross
                cross = ap.cross(ab) # proyecting formula ! ö
                distance = abs(cross) / abLength # perp distance

                # check if is in the segment
                projection = ap.dot(ab) / ab.length_squared()
                thresh = 50 + enemy.radius

                if 0<= projection <= 1 and distance < thresh or (enemy.pos-self.pos).length() < thresh:
                    if enemy.type != "fairy":
                        enemy.hit(4, player)
                        for _ in range(10):
                            particles.append(Particle("dot",enemy.pos,colors["blanco"],speed=random.randint(1,2),glow=3))

    def toDict(self) -> dict:
        return {
            "defColor": (
                self.defColor.r, 
                self.defColor.g, 
                self.defColor.b
            ) if isinstance(self.defColor, pygame.Color)
              else tuple(self.defColor),
            "pos": (self.pos.x, self.pos.y),
            "velocity": (self.velocity.x, self.velocity.y),
            "acceleration": (self.acceleration.x, self.acceleration.y),
            "drawingPoints": [
                (dp.x, dp.y) for dp in self.drawingPoints
            ],
            "crosshairPos": tuple(self.crosshairPos),
            "direction": (self.direction.x, self.direction.y),

            "friction": self.friction,
            "baseSpeed": self.baseSpeed,
            "speedMultiplier": self.speedMultiplier,
            "maxSpeed": self.maxSpeed,

            "invulnerability": self.invulnerability,
            "invulnerabilityTimer": self.invulnerabilityTimer,
            "gun": self.gun,
            "stamina": self.stamina,
            "sprinting": self.sprinting,
            "lastBulletTime": self.lastBulletTime,

            "kills": self.kills,
            "health": self.health,

            "ultPoints": self.ultPoints,
            "ultFiring": self.ultFiring,
            "ultDuration": self.ultDuration,
            "ultPrimeTime": self.ultPrimeTime,

            "skill": self.skill,
            "shielded": self.shielded,

            # nested lists via their own to_dict()
            "skillSet": [sk.toDict() for sk in self.skillSet],
            "fairyEffects": [fe.toDict() for fe in self.fairyEffects],
        }
    
    @classmethod
    def fromDict(cls, data: dict) -> "Player":
        # recreate color
        color = tuple(data["defColor"])
        # pos and crosshair are base args
        p = cls(color, tuple(data["pos"]))

        # override everything else:
        p.velocity = pygame.Vector2(data["velocity"])
        p.acceleration = pygame.Vector2(data["acceleration"])
        p.drawingPoints = [
            pygame.Vector2(x, y) for x, y in data["drawingPoints"]
        ]
        p.crosshairPos = tuple(data["crosshairPos"])
        p.direction = pygame.Vector2(data["direction"])

        p.friction = data["friction"]
        p.baseSpeed = data["baseSpeed"]
        p.speedMultiplier = data["speedMultiplier"]
        p.maxSpeed = data["maxSpeed"]

        p.invulnerability = data["invulnerability"]
        p.invulnerabilityTimer = data["invulnerabilityTimer"]
        p.gun = data["gun"]
        p.stamina = data["stamina"]
        p.sprinting = data["sprinting"]
        p.lastBulletTime = data["lastBulletTime"]

        p.kills = data["kills"]
        p.health = data["health"]

        p.ultPoints = data["ultPoints"]
        p.ultFiring = data["ultFiring"]
        p.ultDuration = data["ultDuration"]
        p.ultPrimeTime = data["ultPrimeTime"]

        p.skill = data["skill"]
        p.shielded = data["shielded"]

        # nested objects
        p.skillSet = [Skill.fromDict(sk, p) for sk in data["skillSet"]]
        p.fairyEffects = [
            FairyEffect.fromDict(fe, p) for fe in data["fairyEffects"]
        ]

        return p



class Skill():
    def __init__(self, type:str, player:Player):

        self.icon = pygame.Surface((50,50), pygame.SRCALPHA).convert_alpha()
        pygame.draw.rect(self.icon,colors["gris"],(0,0,50,50),width=3,border_radius=3)
        self.display:pygame.Surface
        
        self.duration:int # how much
        self.progress:float = 0.0# currently
        
        self.chargeTime:int # how much
        self.cooldown:float = 0.0# currently

        self.active:bool = False
        self.charged:bool = True
        
        self.pos = pygame.Vector2(0,0)
        self.direction = pygame.Vector2(0,0)

        self.type = type
        match self.type:
            case "shield":
                self.duration = 20
                self.chargeTime = 10
                self.display = pygame.Surface((100,100),pygame.SRCALPHA)
                pygame.draw.circle(self.display, (player.defColor[0],player.defColor[1], player.defColor[2], 100), (50,50),50,10) # draw shield circle, using a transparent player defColor

                # draw icon
                pygame.draw.circle(self.icon, player.defColor, (25,25), 20, 5)

            case "dash":
                self.duration = 0.5
                self.chargeTime = 5
                self.display = pygame.Surface((100,100),pygame.SRCALPHA)

                # draw icon
                pygame.draw.polygon(self.icon,player.defColor,((40,10), (10,35), (15,40)))

            case "decoy":
                self.duration = 5
                self.chargeTime = 10

                self.drawPoints = []

                # draw icon
                pygame.draw.polygon(self.icon, player.defColor, ((25,10), (10,40), (40,40)))

            case "swap":
                self.duration = 0
                self.chargeTime = 12

                # draw icon
                pygame.draw.circle(self.icon, player.defColor, (25,25), 10)
                pygame.draw.circle(self.icon, player.defColor, (35,10), 5)
                pygame.draw.circle(self.icon, player.defColor, (30,40), 3)
                pygame.draw.circle(self.icon, player.defColor, (15,35), 7)

            case "implosion":
                
                self.duration = 3
                self.chargeTime = 15
                self.display = pygame.Surface((100,100),pygame.SRCALPHA)
                transWhite = (colors["blanco"][0],colors["blanco"][1], colors["blanco"][2], 100)
                pygame.draw.circle(self.display, transWhite, (50,50),25,3) # draw croshair
                pygame.draw.line(self.display, transWhite, (50,10), (50,90), 3)
                pygame.draw.line(self.display, transWhite, (10,50), (90, 50), 3)

                # draw icon
                pygame.draw.circle(self.icon, player.defColor, (25,25), 10, 3)
                pygame.draw.line(self.icon, player.defColor, (25,10), (25, 40), 3)
                pygame.draw.line(self.icon, player.defColor, (10, 25), (40, 25), 3)

            case "grenade":
                self.duration = 3
                self.chargeTime = 3

                # draw icon
                pygame.draw.circle(self.icon, player.defColor, (25,25), 6)
                pygame.draw.circle(self.icon, player.defColor, (25,25), 10, 2)
                pygame.draw.line(self.icon, player.defColor, (10,40), (25, 25), 3)

    def updateColor(self, color):
        
        match self.type:
            case "shield":
                self.display = pygame.Surface((100,100),pygame.SRCALPHA)
                pygame.draw.circle(self.display, (color[0],color[1], color[2], 100), (50,50),50,10) # draw shield circle, using a transparent player defColor

                # draw icon
                pygame.draw.circle(self.icon, color, (25,25), 20, 5)

            case "dash":
                self.display = pygame.Surface((100,100),pygame.SRCALPHA)

                # draw icon
                pygame.draw.polygon(self.icon,color,((40,10), (10,35), (15,40)))

            case "decoy":

                # draw icon
                pygame.draw.polygon(self.icon, color, ((25,10), (10,40), (40,40)))

            case "swap":
                # draw icon
                pygame.draw.circle(self.icon, color, (25,25), 10)
                pygame.draw.circle(self.icon, color, (35,10), 5)
                pygame.draw.circle(self.icon, color, (30,40), 3)
                pygame.draw.circle(self.icon, color, (15,35), 7)

            case "implosion":
                
                self.display = pygame.Surface((100,100),pygame.SRCALPHA)
                transWhite = (colors["blanco"][0],colors["blanco"][1], colors["blanco"][2], 100)
                pygame.draw.circle(self.display, transWhite, (50,50),25,3) # draw croshair
                pygame.draw.line(self.display, transWhite, (50,10), (50,90), 3)
                pygame.draw.line(self.display, transWhite, (10,50), (90, 50), 3)

                # draw icon
                pygame.draw.circle(self.icon, color, (25,25), 10, 3)
                pygame.draw.line(self.icon, color, (25,10), (25, 40), 3)
                pygame.draw.line(self.icon, color, (10, 25), (40, 25), 3)

            case "grenade":
                # draw icon
                pygame.draw.circle(self.icon, color, (25,25), 6)
                pygame.draw.circle(self.icon, color, (25,25), 10, 2)
                pygame.draw.line(self.icon, color, (10,40), (25, 25), 3)

    def updateTimer(self):

        if self.active:
            self.charged = False
            if self.progress < self.duration:
                # if active countdouwn
                self.progress += dt

                if self.type == "grenade":
                    self.pos += self.direction * 2 * 1/self.progress
                    
                    particles.append(Particle("dot", self.pos, player.defColor, speed=0.5, glow=3))
                elif self.type == "dash":
                    for _ in range(5):
                        particles.append(Particle("dot", player.pos,player.defColor, glow=3))
                elif self.type == "implosion":
                    if random.randint(1,5) == 1:
                        particle = Particle("dot", self.pos+pygame.Vector2(200,0).rotate(random.randint(0,360)), player.defColor, speed=3)
                        particle.direction = pygame.Vector2(self.pos-particle.pos).normalize()
                        particle.gravity = 0
                        particles.append(particle)

            else:
                # deactivate     
                sounds["skDeactivation"].set_volume(0.2)
                sounds["skDeactivation"].play()
                self.active = False
                self.progress = 0
        else:
            if not self.charged:
                if self.cooldown <= self.chargeTime:
                    # charge sk
                    self.cooldown += dt
                else:
                    # done charging
                    self.cooldown = 0
                    self.charged = True
    
    def use(self, player:Player):
        global enemies, particles

        if self.active:
            match self.type:
                case "shield":

                    if self.progress == 0:
                        # utility
                        player.shielded = True
                    
                    # vfx
                    screen.blit(self.display, (player.pos - (50,50)))

                    
                    if not player.shielded: # if player is hit (not if it was hit)
                        # sfx
                        sounds["shieldBreak"].play()
                        # vfx
                        particles.append(Particle("ring", player.pos, player.defColor,50, 100, 2, 3))
                        # reset
                        self.active = False
                        self.charged = False
                        self.progress = 0
                    
                    if self.progress >= self.duration:
                        player.shielded = False

                case "dash":

                    if self.progress == 0:
                        # only once
                        player.velocity = player.direction*5000

                    for e in enemies:
                        if (e.pos-player.pos).length() < e.radius*1.5 and e.type not in ["fairy", "swap"]:
                            explosion(player.pos,50,False,5,player.defColor)
                    
                    player.invulnerability = True
                    player.invulnerabilityTimer = 0.5

                case "decoy":
                    if self.progress == 0:
                        self.drawPoints = player.drawingPoints
                        self.pos = pygame.Vector2(player.pos.x,player.pos.y)
                    
                    pygame.draw.polygon(screen,player.defColor, self.drawPoints)

                    player.stamina = 0
                    player.color = player.damageColor
                    player.invulnerability = True
                    player.invulnerabilityTimer = 1.5

                    for e in enemies:
                        if e.type not in ["fairy","swap", "guardian"]:
                            e.target = self.pos
                    
                    if self.progress >= self.duration:
                        particles.append(Particle("ring", self.pos, player.defColor, 10, 75, 2, 3))

                        player.stamina = 100
                        player.invulnerability = False
                        player.color = player.defColor

                case "swap":


                    if self.progress == 0:

                        particles.append(Particle("ring", player.pos, player.defColor, 50, 150, 2, 3))
                        
                        activeSwaps = []
                        enemiesToRemove = []
                        enemiesCopy = enemies.copy()
                        for e in enemiesCopy:
                            if (e.pos-player.pos).length_squared() <= (150 + e.radius)**2 and e.type not in ["fairy","swap"]:
                                
                                swap = Enemy("swap", (e.pos.x, e.pos.y))

                                swap.radius = e.radius
                                swap.health = e.health
                                swap.speed = e.speed*1.2
                                swap.collisionRadius = e.collisionRadius
                                swap.drawPriority = e.drawPriority

                                
                                swap.color = randomizeColorHue(player.defColor)

                                activeSwaps.append(swap)
                                e.hit(e.health, player)
                                enemiesToRemove.append(e)
                                
                        for e in enemiesToRemove:
                            if e in enemies:
                                enemies.remove(e)
                            if e in Enemy.hiveEnemies:
                                Enemy.hiveEnemies.remove(e)
                        
                        availableTargets = [e for e in enemies if e.type not in ["fairy","swap"]]

                        for swap in activeSwaps:
                            if availableTargets:
                                # randomly choose from list
                                swap.target = random.choice(availableTargets).pos
                            else:
                                # if none, assing itself
                                swap.target = swap.pos
                        
                        enemies += activeSwaps

                case "implosion":
                    
                    if self.progress == 0:
                        self.pos = pygame.Vector2(player.crosshairPos)
                        p = Particle("ring",self.pos,player.defColor, 100,1,speed=-1,width=3,glow=10)
                        particles.append(p)
                    
                    screen.blit(self.display, self.display.get_rect(center=self.pos))

                    if not game.paused:
                        for e in enemies:
                            if e.type not in ["fairy", "swap"]:
                                vectToPoint = (self.pos-e.pos).normalize()
                                e.pos += vectToPoint*25
                    
                    if self.progress >= self.duration:
                        explosion(self.pos, 100, False, 10, player.defColor)
                        self.active = False
                        self.progress = 0

                case "grenade":
                    if self.progress == 0:
                        self.pos = pygame.Vector2(player.pos)
                        self.direction = pygame.Vector2(player.direction)


                    for e in enemies:
                        if e.type not in ["fairy", "swap"]:
                            if (e.pos-self.pos).length_squared() < (e.radius)**2:
                                self.progress = self.duration

                    for b in bullets:
                        if (b.pos-self.pos).length_squared() < 25**2:
                            sounds["pop"].play()
                            self.progress = self.duration
                            bullets.remove(b)
                        

                    if self.progress >= self.duration:
                        explosion(self.pos, 70, False, 7, player.defColor)

    def toDict(self) -> dict:
        data = {
            "type": self.type,
            "progress": self.progress,
            "cooldown": self.cooldown,
            "active": self.active,
            "charged": self.charged,
            "pos": (self.pos.x, self.pos.y),
            "direction": (self.direction.x, self.direction.y),
            # duration and chargeTime are constants per type,
            # but we store them in case you tweak them at runtime:
            "duration": self.duration,
            "chargeTime": self.chargeTime,
        }
        # only decoy has drawPoints
        if hasattr(self, "drawPoints"):
            data["drawPoints"] = [(p.x, p.y) for p in self.drawPoints]
        return data

    @classmethod
    def fromDict(cls, d: dict, player: Player) -> "Skill":
        # create fresh skill (this regenerates icon & display Surfaces)
        skill = cls(d["type"], player)

        # overwrite dynamic state
        skill.progress   = d["progress"]
        skill.cooldown   = d["cooldown"]
        skill.active     = d["active"]
        skill.charged    = d["charged"]
        skill.pos        = pygame.Vector2(d["pos"])
        skill.direction  = pygame.Vector2(d["direction"])
        skill.duration   = d.get("duration", skill.duration)
        skill.chargeTime = d.get("chargeTime", skill.chargeTime)

        # restore drawPoints if present
        if "drawPoints" in d:
            skill.drawPoints = [pygame.Vector2(x, y) for x, y in d["drawPoints"]]

        return skill


def drawSkillIcons(skillsList, menu=False):
    # gracias gpt
    ICON_SIZE = 50
    ROW_GAP   = 12    # so total row-height is 62
    BASE_Y    = ScrHeight - 125

    # how many rows we'll need in total?
    total_rows = math.ceil(len(skillsList) / 20) or 1

    for index, skill in enumerate(skillsList):
        row = index // 20
        col = index % 20

        # figure out how many icons are in this row (for centering)
        if row == (len(skillsList) - 1) // 20:
            icons_in_row = len(skillsList) % 20 or 20
        else:
            icons_in_row = 20

        total_row_width = icons_in_row * ICON_SIZE
        start_x = (ScrWidth - total_row_width) // 2

        blitx = start_x + col * ICON_SIZE

        # now place row 0 at the highest y, and the last row at BASE_Y
        pos_from_bottom = total_rows - 1 - row
        blity = BASE_Y - pos_from_bottom * (ICON_SIZE + ROW_GAP)

        # draw
        target = surfaces["guiSurf"]["surface"]
        if not menu:
            target.blit(skill.icon, (blitx, blity))
            # cooldown bar
            if 0 < skill.cooldown:
                loadBar(screen, (blitx+25,blity+25),
                        skill.cooldown, skill.chargeTime,
                        fillColor=player.damageColor,
                        pixelLength=ICON_SIZE,
                        pixelWidth=ICON_SIZE,
                        vertical=True)
            # charged skill
            if skill.charged == True:
                loadBar(screen, (blitx+25,blity+25),
                        100, 100,
                        fillColor=player.damageColor,
                        pixelLength=ICON_SIZE,
                        pixelWidth=ICON_SIZE,
                        vertical=True)
            # selected-skill indicator
            if player.skill == index:
                loadBar(screen, (blitx + ICON_SIZE//2, blity + ICON_SIZE),
                        100, 100,
                        fillColor=(100,100,100),
                        pixelLength=ICON_SIZE,
                        pixelWidth=10)
        else:
            target.blit(Skill(skill, player).icon, (blitx, blity))




# entities
class Turret():
    def __init__(self, color, pos):
        self.color = color
        self.pos = pygame.Vector2(pos)
        self.direction = (pygame.Vector2(ScrWidth//2,ScrHeight//2)-self.pos).normalize()
        self.time = 15 + random.uniform(0.0, 0.5)
        self.timer = self.time
        self.lastBulletTime = 0
    
    def update(self, player:Player):

        # calculate distance to closest enemy
        closestEnemy = None
        dist = float('inf')
        
        for e in enemies:
            # dist from turr to e
            distsqrd = (e.pos-self.pos).length_squared()
            if  distsqrd < dist: # keep smallest distance
                dist = distsqrd
                closestEnemy = e
        
        # aim
        self.direction = (closestEnemy.pos-self.pos).normalize() if closestEnemy != None else self.direction

        # shoot
        self.lastBulletTime += dt
        if closestEnemy != None:
            self.lastBulletTime = shoot(self.pos, self.direction, player.gun, self.lastBulletTime)
                        
        self.timer -= dt

        if self.timer <= 0:
            randomizeSound(sounds["skDeactivation"],volume=0.1)
            particles.append(Particle("ring", self.pos, self.color, 50, 100, 2, 3))
            
    def draw(self, dest:pygame.Surface):
        mainPoint = self.direction*40
        drawpoints = [self.pos+mainPoint,self.pos+mainPoint.rotate(130),self.pos+mainPoint.rotate(-130)]
        pygame.draw.polygon(dest, self.color, drawpoints)
        pygame.draw.circle(dest, self.color, self.pos, 40, 3)
        loadBar(dest, self.pos+(0,50),self.timer, self.time, self.color, pixelWidth=10)

class Missile():
    def __init__(self, pos, color, seeking=False):
        
        self.color = color
        self.pos:pygame.Vector2 = pos
        self.seeking = seeking
        self.target = None
        self.direction = pygame.Vector2(0,1)
        self.timer = random.uniform(0.2,3)
        self.exploded = False
        
    def update(self):
        # move
        # chase
        particles.append(Particle("dot", self.pos, self.color, glow=3))
        self.pos += self.direction * 300 * dt
        if self.seeking:
            # calculate distance to closest enemy

            if self.target == None or self.target not in enemies:
                targets = [e for e in enemies if e.type not in ["fairy","swap"]]
                if targets:
                    self.target = random.choice(targets)
                else:
                    self.target = None

            else:
                if (self.target.pos-self.pos).length_squared() <= self.target.radius**2:
                    explosion(self.pos, 50, False, 15, self.color)
                    self.exploded = True
            
                # aim
                self.direction = (self.target.pos-self.pos).normalize() if self.target != None else self.direction


            if self.target == None:
                sounds["skDeactivation"].set_volume(0.2)
                sounds["skDeactivation"].play()
                particles.append(Particle("ring", self.pos, 20, 100))
                self.exploded = True
        
        else:
            self.timer -= dt
            if self.timer <= 0:
                explosion(self.pos, 100, False, 10, self.color)
                self.exploded = True

    def draw(self, dest:pygame.Surface):
        mainPoint = self.direction*40
        drawpoints = [self.pos+mainPoint,self.pos+mainPoint.rotate(130),self.pos+mainPoint.rotate(-130)]
        pygame.draw.polygon(dest, self.color, drawpoints)

class Mirror():
    def __init__(self, color):
        self.color = color
        self.pos = pygame.Vector2(0,0)
        self.direction = pygame.Vector2(1,1).normalize()
        self.timer = 10 + random.uniform(0.0, 0.8)
        self.lastBulletTime = 0
        
    def update(self, index:int, count:int, player:Player):

        self.timer -= dt
        self.direction = (player.pos-self.pos).normalize()
        # aim and shoot
        if index == 0:
            self.pos = pygame.Vector2(player.crosshairPos)
        else: 
            v = pygame.Vector2(player.crosshairPos-player.pos)

            sin = math.sin(math.radians(index*360/count))
            cos = math.cos(math.radians(index*360/count))

            self.pos = pygame.Vector2(v.x*cos-v.y*sin+player.pos.x, v.x*sin+v.y*cos+player.pos.y)
        self.lastBulletTime += dt
        if player.mouseClick[0] and not player.pressed[pygame.K_x] and not player.ultFiring:
            self.lastBulletTime = shoot(self.pos,self.direction,player.gun,self.lastBulletTime) # shoot with same gun as player
        
        if self.timer <= 0:
            randomizeSound(sounds["skDeactivation"], volume=0.2)
            particles.append(Particle("ring", self.pos, self.color, 20, 50, width=3))
        
    def draw(self, dest):
        mainPoint = self.direction*40
        drawpoints = [self.pos+mainPoint,self.pos+mainPoint.rotate(130),self.pos+mainPoint.rotate(-130)]
        pygame.draw.polygon(dest, self.color, drawpoints)


vectors360 = [pygame.Vector2(0,1).rotate(angle*2) for angle in range(180)]
class FairyEffect():

    def __init__(self, type:str, player:Player=None):

        self.type:str = type

        self.duration:int = 0
        self.progress:float = 0

        self.entityList = []
        self.entityEffect = False
        self.lastBulletTime = 0

        self.delete:bool = False
        
        match self.type:
            case "bulletrain":
                self.duration = 5
                
            case "turrets":
                self.entityEffect = True
                self.entityList = [Turret(colors["blanco"], pygame.Vector2(random.randint(100, ScrWidth-100), random.randint(100, ScrHeight-100))) for _ in range(random.randint(3,10))]
            
            case "airattack":
                self.entityEffect = True
                self.entityList = [Missile(pygame.Vector2(random.randint(50,ScrWidth-50), -50),colors["blanco"], False) for _ in range(random.randint(5,20))]
            
            case "missiles":
                self.entityEffect = True
                self.entityList = [Missile(pygame.Vector2(player.pos),colors["blanco"], True) for _ in range(random.randint(5,10))]
            
            case "mirrors":
                self.entityEffect = True
                applied = False

                for e in player.fairyEffects:
                    # look for mirror effects already applied
                    if e.type == "mirrors":
                        # if found, append to that entitylist
                        e.entityList += [Mirror(colors["blanco"]) for _ in range(random.randint(1,20))]
                        # and delete this effect
                        self.delete = True
                        applied = True
                        break # stop looking
                # if no effect found, append to self
                if not applied:
                    self.entityList += [Mirror(colors["blanco"]) for _ in range(random.randint(1,20))]
                
            case "enemyslow":
                self.duration = 6

            case "healthsteal":
                for e in enemies:
                    if player.health < 50:
                        player.health += 1
                        sounds["liveup"].play()
                        e.hit(1, player)
                        p = Particle("dot", e.pos, player.defColor, speed=1.5, glow=3)
                        for _ in range(5):
                            particles.append(p)
            
            case "healthrestore":
                player.health = 50
                sounds["liveup"].play()

            case "skrestore":
                for s in player.skillSet:
                    if not s.active and not s.charged:
                        s.cooldown = s.chargeTime
                        sounds["liveup"].play()
            
            case "ultrestore":
                player.ultPoints = 50
                sounds["liveup"].play()
                
            case "rapidfire":
                self.duration = 4
            
    def update(self, player:Player):

        if self.entityEffect and self.entityList == []:
            self.delete = True

        elif not self.entityEffect: 
            self.progress += dt
            if self.progress >= self.duration:
                self.delete = True


        match self.type:
            case "bulletrain":
                self.lastBulletTime += dt
                self.lastBulletTime = shoot(player.pos, vectors360[0], "default", self.lastBulletTime)
                if self.lastBulletTime == 0:
                    for v in vectors360:
                        shoot(player.pos, v, "default", 100)

            case "turrets":
                for turret in self.entityList:
                    turret.update(player)
                self.entityList = [t for t in self.entityList if t.timer > 0]
            
            case "airattack":
                for missile in self.entityList:
                    missile.update()
                self.entityList = [m for m in self.entityList if not m.exploded]
            
            case "missiles":
                for missile in self.entityList:
                    missile.update()
                self.entityList = [m for m in self.entityList if not m.exploded]

            case "mirrors":
                self.entityList = [m for m in self.entityList if m.timer > 0]
                count = sum(1 for m in self.entityList)
                for index, m in enumerate(self.entityList):
                    m.update(index, count, player)
            
            case "enemyslow":
                Enemy.avgSpeed = 0.15
                for e in enemies:
                    if random.randint(1,5) == 1:
                        p = Particle("dot", e.pos, colors["blanco"])
                        particles.append(p)

                if self.progress >= self.duration:
                    Enemy.avgSpeed = 1


            case "rapidfire":
                player.lastBulletTime = 1000000

    def draw(self, player:Player):
        match self.type:
            case "turrets":
                for turret in self.entityList:
                    turret.draw(screen)

            case "airattack":
                for missile in self.entityList:
                    missile.draw(screen)

            case "missiles":
                for missile in self.entityList:
                    missile.draw(screen)
            
            case "mirrors":
                for mirror in self.entityList:
                    mirror.draw(screen)
            
            case "enemyfreeze":
                loadBar(screen, player.pos+(50,0),self.progress,self.duration,colors["blanco"], vertical=True, pixelLength=15, pixelWidth=100)
            
            case "bulletrain":
                loadBar(screen, player.pos+(50,0),self.progress,self.duration,colors["blanco"], vertical=True, pixelLength=15, pixelWidth=100)

            case "rapidfire":
                loadBar(screen, player.pos+(50,0),self.progress,self.duration,colors["blanco"], vertical=True, pixelLength=15, pixelWidth=100)

    def toDict(self) -> dict:
        data = {
            "type":         self.type,
            "duration":     self.duration,
            "progress":     self.progress,
            "delete":       self.delete,
            "entityEffect": self.entityEffect,
            "lastBulletTime": self.lastBulletTime
        }

        if self.entityEffect:
            lst = []
            for e in self.entityList:
                clsname = e.__class__.__name__
                st = {"class": clsname}

                # all entities share color, pos, direction
                st["color"]     = tuple(e.color)
                st["pos"]       = [e.pos.x, e.pos.y]
                st["direction"] = [e.direction.x, e.direction.y]

                if clsname == "Turret":
                    st.update({
                        "time":           e.time,
                        "timer":          e.timer,
                        "lastBulletTime": e.lastBulletTime,
                    })

                elif clsname == "Missile":
                    st.update({
                        "seeking":        e.seeking,
                        "timer":          e.timer,
                        "exploded":       e.exploded,
                        "lastBulletTime": getattr(e, "lastBulletTime", 0),
                    })

                elif clsname == "Mirror":
                    st.update({
                        "timer":          e.timer,
                        "lastBulletTime": e.lastBulletTime,
                    })

                else:
                    # unknown entity: skip
                    continue

                lst.append(st)

            data["entityList"] = lst

        return data

    @classmethod
    def fromDict(cls, d: dict, player: Player) -> "FairyEffect":
        # 1. Allocate without running __init__, to avoid spawning new entities.
        fe = cls.__new__(cls)

        # 2. Restore scalar attributes
        fe.type         = d["type"]
        fe.duration     = d["duration"]
        fe.progress     = d["progress"]
        fe.delete       = d["delete"]
        fe.entityEffect = d["entityEffect"]
        fe.lastBulletTime= d.get("lastBulletTime", 0)

        # 3. Prepare a fresh list
        fe.entityList = []

        # 4. Reconstruct each serialized entity
        for st in d.get("entityList", []):
            kind = st["class"]

            if kind == "Turret":
                t = Turret(
                    color=st["color"],
                    pos=pygame.Vector2(st["pos"])
                )
                t.direction      = pygame.Vector2(st["direction"])
                t.time, t.timer  = st["time"], st["timer"]
                t.lastBulletTime = st["lastBulletTime"]
                fe.entityList.append(t)

            elif kind == "Missile":
                m = Missile(
                    pos=pygame.Vector2(st["pos"]),
                    color=st["color"],
                    seeking=st["seeking"]
                )
                m.timer    = st["timer"]
                m.exploded = st["exploded"]
                fe.entityList.append(m)

            elif kind == "Mirror":
                m = Mirror(color=st["color"])
                m.pos            = pygame.Vector2(st["pos"])
                m.direction      = pygame.Vector2(st["direction"])
                m.timer          = st["timer"]
                m.lastBulletTime = st.get("lastBulletTime", 0)
                fe.entityList.append(m)

            # ignore any unknown classes

        return fe




def giveFairyEffect(player:Player, effect:str):
        player.fairyEffects.append(FairyEffect(effect, player))





class Enemy():

    hiveHealth = 0 # class variable
    hiveEnemies = []

    avgSpeed = 1

    def __init__(self,type:str, pos:tuple[int,int]):
        # GENERIC
        self.type:str = type
        self.pos:pygame.Vector2 = pygame.Vector2(pos)
        self.direction:pygame.Vector2 = pygame.Vector2(1,0) # unit vector 
        self.target:pygame.vector2 | tuple[int,int] = player.pos
        self.drawPriority = 7
        self.damage = 1

        self.coinReward = 0
        if random.randint(1,20) == 1:
            if random.randint(1,1000) == 1:
                self.coinReward = 100
            else:
                self.coinReward = random.randint(1,2)
        # SPECIFIC
        match type:
            case "normie":
                # size 5, 7 or 9 - matches health 
                self.radius = random.choice([30,42,54])
                self.color = colors["rojo"]
                self.collisionRadius = self.radius
                self.health = self.radius/6
                self.speed = random.choice([100,200,300])
                self.drawPriority = 3
            
            case "trickster":
                self.radius = 36
                self.color = colors["purpura"]
                self.collisionRadius = self.radius
                self.health = random.choice([3,10])
                self.speed = 150
                self.drawPriority = 3

            case "speedster":
                self.radius = 30
                self.color = colors["verdeOsc"]
                self.collisionRadius = self.radius
                self.health = 5
                self.speed = 450
                self.drawPriority = 6

            case "jugg":
                game.generateScreenShake(4)
                self.damage = 5
                sounds["jugg"].set_volume(0.2)
                sounds["jugg"].play()
                self.radius = 600
                self.color = colors["bordo"]
                self.collisionRadius = self.radius
                self.health = 100
                self.speed = 75
                self.drawPriority = 1
                self.pos = pygame.Vector2(random.choice([-1000,ScrWidth+1000]),ScrHeight/2)
                self.coinReward = 10

            case "hive":
                self.damage = 2
                self.radius = 30
                self.color = colors["amarillo"]
                self.collisionRadius = 30
                self.health = 10
                self.speed = 200

                Enemy.hiveHealth += self.health # add hp to hive
                Enemy.hiveEnemies.append(self) # add to hive list
                self.drawPriority = 4

            case "kami":
                self.damage = 3
                self.radius = 60
                self.color = colors["negro"]
                self.collisionRadius = self.radius
                self.health = 10
                self.speed = 300
                self.drawPriority = 5
                self.exploded = False

            case "quantum":
                self.damage = 5
                self.radius = 120
                self.color = (0,0,125,100)
                self.collisionRadius = self.radius
                self.health = 20
                self.speed = 90
                self.drawPriority = 0

            case "fairy":
                self.radius = 5
                self.color = colors["blanco"]
                self.collisionRadius = 35
                self.health = 5
                self.speed = 150
                self.drawPriority = 7
                self.target= pygame.Vector2(random.randint(100,1500), random.randint(100,800))

            case "swap":
                # size 5, 7 or 9 - matches health 
                self.radius = random.choice([30,42,54])
                self.color = colors["celeste"]
                self.collisionRadius = self.radius
                self.health = self.radius/6
                self.speed = random.choice([100,200,300])
                self.drawPriority = 3

            case "spike":
                self.damage = 10
                self.radius = 75
                self.color = colors["violeta"]
                self.collisionRadius = self.radius
                self.health = 15
                self.speed = 150
                self.drawPriority = 2

            case "slime":
                self.damage = 6
                self.radius = random.randint(50,100)
                self.color = list(colors["lima"])+[200]
                self.collisionRadius = self.radius
                self.health = 20
                self.speed = 80
                self.drawPriority = 2
            case "slimy":
                self.damage = 3
                self.radius = 50
                self.color = list(colors["lima"])+[200]
                self.collisionRadius = self.radius
                self.health = 10
                self.speed = 160
                self.drawPriority = 6

            case "guardian":
                self.damage = 5
                self.radius = 60
                self.color = colors["oroviejo"]
                self.collisionRadius = self.radius
                self.health = 5
                self.speed = 200
                self.drawPriority = 2
                # MOVE
                self.target = pygame.Vector2(random.choice([(random.randint(100,ScrWidth-100), 100), 
                                                            ((random.randint(100,ScrWidth-100), ScrHeight-100)),
                                                            ((100, random.randint(100,ScrHeight-100))),
                                                            ((ScrWidth-100, random.randint(100,ScrHeight-100))),
                                                            ]))

                self.attackCharge = 0
                self.coinReward = random.choice([0,3,3])


        # WOBBLE
        self.wobbleOffset:list[int,int] = [random.uniform(0,1000), random.uniform(0,1000)]
        self.wobbleSpeed = random.uniform(0.01, 0.05)
        self.wobbleAmplitude = self.speed/100

        self.color = list(self.color) 
        if self.type != "fairy":

            # randomize color hue
            self.color = randomizeColorHue(self.color)
            
            # set outside
            if self.pos.x < 0:
                self.pos.x = -self.radius*1.5
            if self.pos.x > ScrWidth:
                self.pos.x = ScrWidth+self.radius*1.5
            if self.pos.y < 0:
                self.pos.y = -self.radius*1.5
            if self.pos.y > ScrHeight:
                self.pos.y = ScrHeight+self.radius*1.5

    def draw(self, dest):
                
        if self.type == "trickster":
            pygame.draw.circle(dest, self.color,self.pos,self.radius+5,2)
        elif self.type == "kami":
            pygame.draw.circle(dest, colors["amarillo"],self.pos,18,2)
        elif self.type == "quantum":
            self.color = (0,0,125,max(0,math.sin(self.wobbleOffset[0])*125))
        elif self.type == "hive":
            if self in Enemy.hiveEnemies:
                index = Enemy.hiveEnemies.index(self)
                # draw lines
                if len(Enemy.hiveEnemies) > index + 1:
                    pygame.draw.line(dest,self.color+[128],self.pos,Enemy.hiveEnemies[index+1].pos, 4) 
                if index == 0:
                    loadBar(dest,self.pos+(0,30),Enemy.hiveHealth,sum(10 for e in Enemy.hiveEnemies),fillColor=self.color)
        elif self.type == "spike":
            basePt = self.direction * self.radius
            points = []
            for i in range(20):
                if i%2 == 0:
                    points.append(self.pos + basePt.rotate(18*i)*0.7)
                else:
                    points.append(self.pos + basePt.rotate(18*i)*1.3)
            pygame.draw.polygon(dest, self.color, points)
        elif self.type == "slime" or self.type == "slimy":
            pygame.draw.circle(dest,(self.color[0],self.color[1],self.color[2],75),self.pos, self.radius*1.25)
        elif self.type == "guardian":
            if self.attackCharge > 1:
                pygame.draw.line(dest, self.color+[100],self.pos,player.pos,int(self.attackCharge*5))
                pygame.draw.circle(dest, self.color+[100],self.pos,self.radius*self.attackCharge/4)
                pygame.draw.circle(dest, self.color+[100],player.pos,50*self.attackCharge/5)
        pygame.draw.circle(dest,self.color,self.pos, self.radius)

    def move(self):

        # FAIRY WANDER
        if self.type == "fairy":
            if (self.pos-self.target).length() < 10:
                self.target = pygame.Vector2(random.randint(100,ScrWidth-100), random.randint(100,ScrHeight-100))

            particles.append(Particle("dot",self.pos,self.color, speed=0.5, glow=3))
            if random.randint(1,100) == 1:
                randomizeSound(random.choice([sounds["fairysound"], sounds["fairysound1"]]), volume=0.01)

        # GUARDIAN WANDER
        elif self.type == "guardian" and screenRect.collidepoint(self.pos.x, self.pos.y):
            # charge
            self.attackCharge += dt

            if self.attackCharge > 5:
                # ATTACK
                if not player.invulnerability:
                    player.collisions(self.damage)
                    for _ in range(40):
                        particles.append(Particle("dot", player.pos, self.color, speed=2))
                    # MOVE
                    self.target = pygame.Vector2(random.choice([(random.randint(100,ScrWidth-100), 100), 
                                                                ((random.randint(100,ScrWidth-100), ScrHeight-100)),
                                                                ((100, random.randint(100,ScrHeight-100))),
                                                                ((ScrWidth-100, random.randint(100,ScrHeight-100))),
                                                                ]))
                    # REPEAT
                    self.attackCharge = 0
                else:
                    if self.attackCharge > 5.5:
                        self.attackCharge = 0
            else:
                # AIM SFX
                if 0.9 < self.attackCharge < 1:
                    self.attackCharge = 1
                if self.attackCharge == 1:
                    randomizeSound(sounds["ulticharge"],maxtime=800,volume=0.02)
                if self.attackCharge > 1:
                    if random.randint(1,5) == 1: 
                        particle = Particle("dot", player.pos+pygame.Vector2(50,0).rotate(random.randint(0,360)), self.color)
                        particle.direction = pygame.Vector2(player.pos-particle.pos).normalize()
                        particles.append(particle)
                


        # SWAP CHASE
        elif self.type == "swap":
            availableTargets = [e.pos for e in enemies if e.type not in ["fairy", "swap"]]
            if self.target not in availableTargets:
                if availableTargets:
                    # randomly choose from list
                    self.target = random.choice(availableTargets)
                else:
                    # if none, assing itself
                    self.target = self.pos

            if self.target in availableTargets and (self.pos-self.target).length() < self.radius:
                explosion(self.pos, self.radius*2, False, self.health, self.color)
                self.health = 0

        elif self.type == "slime" or self.type == "slimy":
            if random.randint(1,100) == 1:
                particles.append(Particle("dot", self.pos+self.direction.rotate(random.randint(1,360))*self.radius*1.25, self.color,speed=0.2))

        elif self.type == "speedster":
            if random.randint(1,10) == 1:
                particles.append(Particle("dot",self.pos,self.color))

        

        # CHASE
        self.direction = pygame.Vector2(self.target - self.pos).normalize() if self.target != self.pos else self.direction

        # WOBBLE
        if (self.pos-self.target).length() > 10:
            self.wobbleOffset[0] += self.wobbleSpeed
            self.wobbleOffset[1] += self.wobbleSpeed
            self.pos += pygame.Vector2(math.sin(self.wobbleOffset[0])*self.wobbleAmplitude, math.sin(self.wobbleOffset[1])*self.wobbleAmplitude) * Enemy.avgSpeed

            self.pos += self.direction * self.speed * Enemy.avgSpeed * dt

    def hit(self, amplifier, player:Player):
        global particles
        # DAMAGE
        if self.health > 0:

            damage = 1*amplifier
            self.health -= damage # take that

            if self.type == "hive": # update hivehealth
                #Enemy.hiveHealth -= damage
                Enemy.hiveHealth = sum(hive.health for hive in Enemy.hiveEnemies)
                if int(Enemy.hiveHealth) <= 0:
                    Enemy.hiveHealth = 0
                for hive in Enemy.hiveEnemies:
                    hive.health = Enemy.hiveHealth/len(Enemy.hiveEnemies)

                if Enemy.hiveHealth == 0:
                    hivesToRemove = []
                    for hive in Enemy.hiveEnemies: # update for every hiver
                        hive.health = 0
                        player.kills += 1
                        if player.ultPoints < 50:
                            player.ultPoints += 1
                        if player.stamina < 100:
                            player.stamina += 5
                        randomizeSound(sounds["kill"],volume=0.5)
                        particles.append(Particle("ring",hive.pos,self.color,10,30,2,3,5))
                        hivesToRemove.append(hive)
                    for hive in hivesToRemove:
                        Enemy.hiveEnemies.remove(hive)
                

            # HIT SFX
            random.choice([sounds["pop"], sounds["pop1"], sounds["pop2"]]).play()

            # RADIUS
            if self.type in ["normie","speedster","jugg", "kami"]:
                self.radius = self.health * 6
                self.collisionRadius = self.radius

            # KILL
            if self.health <= 0:
                if random.randint(1,10) == 1:
                    particles.append(Particle("text", self.pos, self.color, text=random.choice(["*-*", "OOF", "Bro...", "RIP", "Ok.", "Umm", "WOW", "CLIP", "EZ", ":(", ".-.", "._.", ":o"]), duration=1))
                
                # KILLS
                if self.type not in ["fairy", "hive", "swap", "slimy"]:
                    player.kills += 1
                # ULT POINTS
                if player.ultPoints < 50:
                    player.ultPoints += 1

                    if player.ultPoints == 50:
                        particles.append(Particle("text", player.pos+(0,-50), player.defColor, text="- ULT READY! -", duration=2))
                # HP
                if player.health < 50:
                    if random.randint(1,100) <= 25:
                        player.health += 1
                        sounds["upgrade"].set_volume(0.2)
                        sounds["upgrade"].play()  
                        particles.append(Particle("text",self.pos, player.defColor,text="+1",duration=1))
                        
                        p = [Particle("dot", self.pos, player.defColor, speed=0.2) for _ in range(20)]
                        particles.extend(p)
                # STAMINA
                if player.stamina < 100:
                    player.stamina += 5
                    
                # COINS
                if self.coinReward > 0:
                    randomizeSound(sounds["coin"])
                    game.coins += self.coinReward
                    particles.append(Particle("text", self.pos, colors["amarillo"], text=f"+{self.coinReward} ■", duration=1.5))
                
                    p = [Particle("dot", self.pos, colors["amarillo"], speed=2) for _ in range(20)]
                    particles.extend(p)
                    
                
                # KILL SFX
                randomizeSound(sounds["kill"],volume=0.5)
                
                # KILL VFX
                if not player.ultFiring:
                    p = [Particle("ring",self.pos,self.color,10,30,0.5,3,5)]
                    p.extend([Particle("dot",self.pos,self.color,speed=2,glow=3) for _ in range(10)])
                    particles.extend(p)
                    
                else:
                    p = Particle("ring",self.pos,colors["blanco"],10,30,0.5,3,5)
                    particles.append(p)
                # BOOM BOOM
                if self.type == "kami":
                    if not self.exploded:
                        explosion(self.pos,200,True,5,self.color)
                        self.exploded = True
                # SLIMESS
                if self.type == "slime" or self.type == "slimy" and self.radius >= 40:

                    particles += [Particle("dot",self.pos,self.color, speed=2) for _ in range(30)]
                    
                    slimy = Enemy("slimy", self.pos+self.direction.rotate(90)*self.radius)
                    slimy.radius = self.radius*0.5
                    slimy.collisionRadius = slimy.radius
                    slimy.health = slimy.radius//5
                    slimy.speed = self.speed * 1.25

                    particles += [Particle("dot",slimy.pos,slimy.color) for _ in range(10)]
                    enemies.append(slimy)
                    
                    if random.randint(1,100) <= 75:
                        slimy2 = Enemy("slimy", self.pos+self.direction.rotate(-90)*self.radius)
                        slimy2.radius = self.radius*0.5
                        slimy2.collisionRadius = slimy.radius
                        slimy2.health = slimy.radius//5
                        slimy2.speed = self.speed * 1.25

                        particles += [Particle("dot",slimy2.pos,slimy.color) for _ in range(10)]
                        enemies.append(slimy2)
                        
                # FAIRYEFFECT
                elif self.type == "fairy":
                    effect = random.choice(list(fairyEffects.keys())) 
                    giveFairyEffect(player, effect)

                    particles.append(Particle("text",self.pos, self.color,text=f"- {fairyEffects[effect][game.language]} -",duration=2, font=SMALLFONT))
                    for _ in range(20):
                        particles.append(Particle("dot",self.pos,self.color,speed=2,glow=3))
                # SPAWN FAIRY
                if random.randint(1,100) <= 5:
                    sounds["fairysound"].play()
                    enemies.append(Enemy("fairy", self.pos))

    def toDict(self) -> dict:
        return {
            "type": self.type,
            "color":list(self.color),
            # vectors → simple lists
            "pos":      [self.pos.x, self.pos.y],
            "direction":[self.direction.x, self.direction.y],
            "target":   [self.target.x, self.target.y]
                        if hasattr(self.target, "x")
                        else list(self.target),
            # core stats
            "damage":         self.damage,
            "radius":         self.radius,
            "collisionRadius":self.collisionRadius,
            "health":         self.health,
            "speed":          self.speed,
            "drawPriority":   self.drawPriority,
            # guardian-only
            **({"attackCharge": self.attackCharge} 
               if hasattr(self, "attackCharge") else {}),
            # Kami-only
            **({"exploded": self.exploded} 
               if hasattr(self, "exploded") else {}),
            # wobble
            "wobbleOffset":   [self.wobbleOffset[0], self.wobbleOffset[1]],
            "wobbleSpeed":    self.wobbleSpeed,
            "wobbleAmplitude":self.wobbleAmplitude,
            # hive membership
            "inHive":         self in Enemy.hiveEnemies,
        }

    @classmethod
    def fromDict(cls, d: dict) -> "Enemy":
        # bypass __init__ (which does random & side‐effects)
        e = object.__new__(cls)

        # restore everything
        e.type           = d["type"]
        e.color          = d["color"]
        e.pos            = pygame.Vector2(d["pos"])
        e.direction      = pygame.Vector2(d["direction"])
        targ = d["target"]
        e.target         = pygame.Vector2(targ)  # always Vector2 on load
        e.damage         = d["damage"]
        e.radius         = d["radius"]
        e.collisionRadius= d["collisionRadius"]
        e.health         = d["health"]
        e.speed          = d["speed"]
        e.drawPriority   = d["drawPriority"]

        if "attackCharge" in d:
            e.attackCharge = d["attackCharge"]
        if "exploded" in d:
            e.exploded = d["exploded"]

        e.wobbleOffset   = [d["wobbleOffset"][0], d["wobbleOffset"][1]]
        e.wobbleSpeed    = d["wobbleSpeed"]
        e.wobbleAmplitude= d["wobbleAmplitude"]

        # restore hive lists & health total
        if d.get("inHive", False):
            # avoid duplicates
            if e not in cls.hiveEnemies:
                cls.hiveEnemies.append(e)
                cls.hiveHealth += e.health

        return e




class Spawner():
    def __init__(self, pos, radius):
        self.pos = pygame.Vector2(pos)
        enemyChoice = random.choice(["normie", "trickster","speedster", "hive", "kami", "quantum","spike", "slime", "guardian"])
        self.spawns:list[Enemy] = [Enemy(enemyChoice, self.pos) for _ in range(random.randint(10,25)+round(radius//10))]
        self.timer = 5
        self.radius = radius

    def update(self):
        global enemies
        self.timer -= dt
        if random.randint(1,50) == 1:
            particles.append(Particle("dot",self.pos, colors["blanco"], speed=4))
        if self.timer <= 0:
            explosion(self.pos, 0,True, 5, colors["blanco"])
            enemies.extend(self.spawns)
            enemies.sort(key=lambda e: e.drawPriority)

    def draw(self,dest):
        pygame.draw.circle(dest, colors["blanco"], self.pos, self.radius)
        loadBar(dest, self.pos+(0,+10+self.radius),self.timer, 5, colors["blanco"], pixelWidth=15)

    def toDict(self) -> dict:
        return {
            "pos":       [self.pos.x, self.pos.y],
            "spawns":    list(self.spawns),   # list of type‐strings
            "timer":     self.timer,
            "radius":    self.radius,
        }

    @classmethod
    def fromDict(cls, d: dict) -> "Spawner":
        s = cls((0,0), d["radius"])     # dummy pos/radius
        s.pos     = pygame.Vector2(d["pos"])
        s.spawns  = list(d["spawns"])
        s.timer   = d["timer"]
        s.radius  = d["radius"]
        return s




class SnakeBoss():

    def __init__(self):
               
        self.snake = lizard.Lizard(numberOfPoints=40,
                                   pointDistance=2, 
                                   walkingSpeed= 300,
                                   bodyScale=5,
                                   flexibility=130,
                                   head=0,
                                   bodyColor=colors["bordo"],
                                   borderColor=colors["negro"],
                                   eyeColor=colors["rojo"])
        self.snake.headSize = 50
        
        for i in range(len(self.snake.points)):
            self.snake.bodyRadiuses[i] = 55/(i/50+1)
        
        
        self.health = 3000
        self.attackCharge = 0
        self.chasingTime = 0
        self.patience = 10 # seconds in changing pathpoint

        self.spawners:list[Spawner] = []

    def move(self):
        def chooseTarget():
            
            randomizeSound(sounds[random.choice(["bossgrowl_1", "bossgrowl_2"])], volume=0.15)

            if random.randint(1,5) == 1:
                self.snake.walkingSpeed = 500 * min(5, 3000/(self.health*2 if self.health != 0 else 1))
                self.snake.pathPoint = player.pos
                    
            else:
                self.snake.walkingSpeed = 300 * min(5, 3000/(self.health*2 if self.health != 0 else 1))
                if len(self.snake.points) <= 2:
                    self.snake.walkingSpeed = 150
                point = [
                    (random.randint(-400, ScrWidth+400), -400),
                    (random.randint(-400, ScrWidth+400), ScrHeight+400),
                    (-400, random.randint(-200, ScrHeight+400)),
                    (ScrWidth+400, random.randint(-400, ScrHeight+400))
                    ]
                
                self.snake.pathPoint = random.choice(point)
        
        if not self.snake.walking:
            chooseTarget()


        self.chasingTime += dt
        if self.chasingTime > self.patience:
            self.chasingTime = 0
            chooseTarget()

        if self.health > 0:
            for spawner in self.spawners:
                spawner.update()
            self.spawners = [s for s in self.spawners if s.timer > 0]

            self.snake.walk(dt)

            # SPAWNERS
            if len(self.snake.points) > 2:
                if screenRect.collidepoint(self.snake.points[-1]):
                    if random.randint(1,100) == 1:
                        if self.patience > 1:
                            self.patience -= 0.2
                        self.snake.walkingSpeed += 10
                        self.spawners.append(Spawner(self.snake.points.pop(), self.snake.bodyRadiuses.pop()))
    
    def colissions(self, player:Player):
        
        for index, point in enumerate(self.snake.points):
            for b in bullets:
                if (point-b.pos).length() < self.snake.bodyRadiuses[index]:
                            
                    random.choice([sounds["pop"], sounds["pop1"], sounds["pop2"]]).play()
                    bullets.remove(b)
                    particles.append(Particle("ring",b.pos,colors["blanco"],4,7,0.5,3))
                    self.health -= 1
            
            playerdist = pygame.Vector2(player.pos-point)
            playerdistlenght = playerdist.length()
            if playerdistlenght < self.snake.bodyRadiuses[index]:
                if not player.invulnerability:
                    player.velocity = playerdist.normalize()*3000
                player.collisions(10)

    def draw(self, dest:pygame.Surface):
        self.snake.draw(dest)
        loadBar(dest, (ScrWidth//2, ScrHeight-50), self.health, 3000, colors["bordo"], pixelLength=8*ScrWidth//10)

        for spawner in self.spawners:
            spawner.draw(dest)

    def toDict(self) -> dict:
        return {
            "snake":        self.snake.to_dict(),
            "health":       self.health,
            "attackCharge": self.attackCharge,
            "chasingTime":  self.chasingTime,
            "patience":     self.patience,
            "spawners":     [sp.toDict() for sp in self.spawners],
        }

    @classmethod
    def fromDict(cls, d: dict) -> "SnakeBoss":
        sb = cls()  # calls __init__, creating a fresh snake & empty spawners
        # overwrite with saved data:
        sb.snake         = lizard.Lizard.from_dict(d["snake"])
        sb.health        = d["health"]
        sb.attackCharge  = d["attackCharge"]
        sb.chasingTime   = d["chasingTime"]
        sb.patience      = d["patience"]
        sb.spawners      = [Spawner.from_dict(spd) for spd in d["spawners"]]
        return sb


class SnakePet():
    def __init__(self, player:Player):
        self.snake = lizard.Lizard(
            numberOfPoints=3,
            pointDistance=0,
            walkingSpeed=300,
            bodyScale=2,
            flexibility=60,
            head=0,
            bodyColor=randomizeColorHue(player.defColor),
            borderColor=player.damageColor,
            borderRadius=2,
            eyeColor=colors["gris"],
            )
        
        for i in range(len(self.snake.points)):
            self.snake.bodyRadiuses[i] = 22/(i/8+1)

        self.snake.headSize = 20
        self.snake.pathPoint = pygame.Vector2(100,100)
        self.snake.eyelidColor = self.snake.eyeColor
        self.age = 0
        self.agingSpeed = 5*60 # in seconds, adds a circle

        self.tiredness = 1
        self.asleep = False
        self.sleepTimer = 0
        

        self.healing = False
        self.healcd = 0
        self.healAura = pygame.Surface((250,250), pygame.SRCALPHA)
        pygame.draw.circle(self.healAura, self.snake.bodyColor+[50], self.healAura.get_rect().center, 100)
        # blurr aura 
        data = pygame.image.tostring(self.healAura, 'RGBA')
        image = Image.frombytes('RGBA', self.healAura.get_size(),data)
        blurrdImage = image.filter(ImageFilter.GaussianBlur(radius=10))
        self.healAura = pygame.image.fromstring(blurrdImage.tobytes(), image.size, 'RGBA')

    def move(self):
        def wander(rect = pygame.Rect(100,100,ScrWidth-200,ScrHeight-200)):
            """Choose a Random location of the screen"""
            point = pygame.Vector2(self.snake.points[0])
            while (point-self.snake.points[0]).length_squared() < 50**2:
                point = pygame.Vector2(rect.left+random.randint(0,rect.width), rect.top+random.randint(0,rect.height))
            self.snake.pathPoint = point
            self.snake.eyeColor = colors["gris"] # wake up

        def follow(target:pygame.Vector2):
            """Follow a target and wander around it"""
            if not self.snake.walking:
                if (self.snake.points[0]-target).length_squared() <= 300**2:
                    wander(pygame.Rect(target.x-150,target.y-150,300,300))
                else:
                    self.snake.pathPoint = target
                    self.snake.eyeColor = colors["gris"] # wakey wakey
        
        def sleep():
            if self.asleep:
                self.snake.eyeColor = self.snake.bodyColor
                self.sleepTimer -= dt

                if random.randint(1,75) == 1:
                    p = Particle("text", (self.snake.points[0].x + random.randint(0,50), self.snake.points[0].y+random.randint(-50, 0)), self.snake.bodyColor,  font=SMALLESTESTFONT, text=random.choice(["Zz", "z", "Zzz", "zZz", "z z z"]), duration=1.5)
                    particles.append(p)

                if self.sleepTimer <= 0:
                    self.tiredness = 1
                    self.sleepTimer = 0
                    self.asleep = False
        def blink():
            if not self.asleep:
                if random.randint(1,50) == 1:
                    self.snake.eyeColor = self.snake.bodyColor
                elif random.randint(1,int(self.tiredness)) == 1:
                    self.snake.eyeColor = colors["gris"]
        def age():
            self.age += dt
            if int(self.age)%self.agingSpeed == 0 and int(self.age)/self.agingSpeed>len(self.snake.points):
                self.snake.points.append(pygame.Vector2(self.snake.points[0].x,self.snake.points[0].y))
                self.snake.bodyRadiuses.append(22/(len(self.snake.points)/8+1))
            if not self.asleep:
                self.tiredness += dt
                
        age()
        blink()

        # SFX
        if random.randint(1,300) == 1 and not self.asleep:
            randomizeSound(sounds["pet"], pitch_factor=random.uniform(3,5), volume=0.2, maxtime=700)

        
        # AI
        if not self.snake.walking:
            # when it reaches a target 
            # if theres a fairy itll get curious and follow, if theres a juggernaught, itll get scared and go to player, else wander
            if  not self.asleep:
                if random.randint(1,int(self.tiredness)) == 1:
                    wander()
            if self.tiredness >= 100 and not self.asleep:
                self.snake.pathPoint = self.snake.points[-1]
                self.asleep = True
                self.sleepTimer = random.randint(20, 90)
            for e in enemies:
                if e.type == "jugg":
                    follow(player.pos)
                    self.asleep = False
                    break
                elif e.type == "fairy" and not self.asleep:
                    follow(e.pos)
                    break
            if 0 < player.health <= 25: 
                self.asleep = False
                follow(player.pos)
                
            sleep()
            
        # MOVE
        self.snake.walkStretch(dt)

    def heal(self,player:Player):
        self.healing = False
        if (self.snake.points[0]-player.pos).length_squared() < 125**2:
            if player.health < 50:

                self.healing = True
                self.healcd += dt
                
                if self.healcd > max(0.5, 5 / len(self.snake.points)):
                    self.healcd = 0
                    player.health += 1
                    p = Particle("text",player.pos+(0,-25), player.defColor,text="+1",duration=0.7)
                    particles.append(p)
                # particles
                if random.randint(1, max(3, min(10, 10 - len(self.snake.points)//2))) == 1:
                    particles.append(Particle("dot",self.snake.points[0],self.snake.bodyColor,glow=3, speed=3))

    def draw(self, dest:pygame.Surface):
        if self.healing:
            dest.blit(self.healAura, self.healAura.get_rect(center=self.snake.points[0]))
        self.snake.draw(dest)

    def toDict(self) -> dict:
        return {
            # serialize the underlying Lizard
            "snake": {**self.snake.to_dict()},
            # pet state
            "age":         self.age,
            "agingSpeed":  self.agingSpeed,
            "tiredness":   self.tiredness,
            "asleep":      self.asleep,
            "sleepTimer":  self.sleepTimer,
            "healing":     self.healing,
            "healcd":      self.healcd,
        }
    
    @classmethod
    def fromDict(cls, d: dict, player: Player) -> "SnakePet":
        # call __init__ to rebuild snake Lizard, healAura, etc.
        pet = cls(player)

        # restore Lizard state
        lizard_data = d["snake"]
        pet.snake = lizard.Lizard.from_dict(lizard_data)

        # restore dynamic fields
        pet.age         = d["age"]
        pet.agingSpeed  = d["agingSpeed"]
        pet.tiredness   = d["tiredness"]
        pet.asleep      = d["asleep"]
        pet.sleepTimer  = d["sleepTimer"]
        pet.healing     = d["healing"]
        pet.healcd      = d["healcd"]

        # healAura was built in __init__, and will be drawn correctly
        return pet



bullets:list[Bullet] = []
enemies:list[Enemy] = []
particles:list[Particle] = []
player:Player=Player()
snake:SnakeBoss = SnakeBoss()

store = userInterface.Store(ScrWidth)

scrollingBackground = None

mainMenuFairy:Enemy = Enemy("fairy",(ScrWidth - 100, ScrHeight//2))

class GameplayManager():
    def __init__(self, loadSettings = False):

        self.paused = False
        self.gameplayStage:str = "mainMenu"
        self.waveNumber:int = 1
        self.waveProgress:int = 0
        self.waveEnd:int = 5
        self.difficulty:int = 0
        self.enemySpawnRate:int = 0
        self.waveWaitTimer = 0
        self.nextWaveStart = False
        self.totalProgress = 0 # kills
        self.playTime = 0
        self.enemiesToSpawn:list[str] = [random.choice(spawnableEnemyTypes) for _ in range(random.randint(3,10))] # list of enemy types for the round

        self.endlessChoiceAmmount = 10
        self.maxEndlessKills = 0

        self.musicToggle = True
        self.fullscreen = False
        self.shakeToggle = True
        self.shakePos = []
        for i in range(360):
            self.shakePos.append(pygame.Vector2(2,0).rotate(i))
        self.fogToggle = True

        
        self.shakeTime = 0
        self.scrBlitPos = (0,0)

        self.inStore = False
        self.coins = 0

        self.playerSelectedColor = colors["celeste"]
        self.playerSelectedGun = "default"
        self.playerSelectedSkillSet = []
        self.backgroundColor = list(colors["grisoscuro"])

        self.language = "EN"
        self.bigScale = False

        self.menuButtons:dict[str,userInterface.Button] = {
            "start": userInterface.Button(200, ScrHeight//2 - 110, (0,255,255,10), colors["celesteOpaco"], "Start", BIGFONT, colors["blanco"], clickable=True, spacing=200),
            "load": userInterface.Button(175, ScrHeight//2 + 25, (0,255,255,10), colors["celesteOpaco"], "Load Game", SMALLFONT, colors["blanco"],size=(250,75), clickable=True, spacing=50),
            "endlessMode": userInterface.Button(425, ScrHeight//2 + 25, (0,255,255,10), colors["celesteOpaco"], "Endless", SMALLFONT, colors["blanco"],size=(250,75), clickable=True, spacing=50),
            "store": userInterface.Button(150, ScrHeight//2 + 120, (0,255,255,10), colors["celesteOpaco"], "Store", SMALLFONT, colors["blanco"],size=(200,75), clickable=True, spacing=100),
            "langToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 50, (0,255,255,10), colors["celesteOpaco"], f"Language: {'EN' if self.language == 'EN' else 'ES'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "musicToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 120, (0,255,255,10), colors["celesteOpaco"], f"Music: {'on' if self.musicToggle else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "fullscrToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 190, (0,255,255,10), colors["celesteOpaco"], f"Full Screen: {'on' if self.fullscreen else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "scale": userInterface.Button(ScrWidth - 150, ScrHeight - 260, (0,255,255,10), colors["celesteOpaco"], f"Scale: {'BIG' if self.bigScale else 'MID'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "shakeToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 330, (0,255,255,10), colors["celesteOpaco"], f"Scr Shake: {'on' if self.shakeToggle else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "fogToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 400, (0,255,255,10), colors["celesteOpaco"], f"Fog: {'on' if self.fogToggle else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "quit": userInterface.Button(150, ScrHeight - 50, (0,255,255,10), colors["celesteOpaco"], "Quit", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
        }

        self.pauseButtons:dict[str,userInterface.Button] = {
            "continue" : userInterface.Button(ScrWidth//2, ScrHeight//2+100+50*0, (0,0,0,50), colors["gris"], "Continue", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "back" : userInterface.Button(ScrWidth//2, ScrHeight//2+100+50*1, (0,0,0,50), colors["gris"], "Back to Menu", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "save" : userInterface.Button(ScrWidth//2, ScrHeight//2+100+50*2, (0,0,0,50), colors["gris"], "Save Run", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "musicToggle" : userInterface.Button(ScrWidth//2, ScrHeight//2+100+50*3, (0,0,0,50), colors["gris"], f"Music: {'on' if self.musicToggle else 'off'}", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "fullscrToggle" : userInterface.Button(ScrWidth//2, ScrHeight//2+100+50*4, (0,0,0,50), colors["gris"], f"Full Screen: {'on' if self.fullscreen else 'off'}", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
        }
        
        self.pauseButtonsEN:dict[str,userInterface.Button] = {
            "continue" : userInterface.Button(ScrWidth//2, ScrHeight//2+100+50*0, (0,0,0,50), colors["gris"], "Continue", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "back" : userInterface.Button(ScrWidth//2, ScrHeight//2+100+50*1, (0,0,0,50), colors["gris"], "Back to Menu", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "save" : userInterface.Button(ScrWidth//2, ScrHeight//2+100+50*2, (0,0,0,50), colors["gris"], "Save Run", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "musicToggle" : userInterface.Button(ScrWidth//2, ScrHeight//2+100+50*3, (0,0,0,50), colors["gris"], f"Music: {'on' if self.musicToggle else 'off'}", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "fullscrToggle" : userInterface.Button(ScrWidth//2, ScrHeight//2+100+50*4, (0,0,0,50), colors["gris"], f"Full Screen: {'on' if self.fullscreen else 'off'}", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
        }       
        self.pauseButtonsES:dict[str,userInterface.Button] = {
            "continue" : userInterface.Button(ScrWidth//2, ScrHeight//2+100+50*0, (0,0,0,50), colors["gris"], "Continuar", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "back" : userInterface.Button(ScrWidth//2, ScrHeight//2+100+50*1, (0,0,0,50), colors["gris"], "Volver al Menu", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "save" : userInterface.Button(ScrWidth//2, ScrHeight//2+100+50*2, (0,0,0,50), colors["gris"], "Guardar Partida", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "musicToggle" : userInterface.Button(ScrWidth//2, ScrHeight//2+100+50*3, (0,0,0,50), colors["gris"], f"Musica: {'on' if self.musicToggle else 'off'}", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "fullscrToggle" : userInterface.Button(ScrWidth//2, ScrHeight//2+100+50*4, (0,0,0,50), colors["gris"], f"Pant. Completa: {'on' if self.fullscreen else 'off'}", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
        }

        self.menuButtonsEN:dict[str,userInterface.Button] = {
            "start": userInterface.Button(200, ScrHeight//2 - 110, (0,255,255,10), colors["celesteOpaco"], "Start", BIGFONT, colors["blanco"], clickable=True, spacing=200),
            "load": userInterface.Button(175, ScrHeight//2 + 25, (0,255,255,10), colors["celesteOpaco"], "Load Game", SMALLFONT, colors["blanco"],size=(250,75), clickable=True, spacing=50),
            "endlessMode": userInterface.Button(425, ScrHeight//2 + 25, (0,255,255,10), colors["celesteOpaco"], "Endless", SMALLFONT, colors["blanco"],size=(250,75), clickable=True, spacing=50),
            "store": userInterface.Button(150, ScrHeight//2 + 120, (0,255,255,10), colors["celesteOpaco"], "Store", SMALLFONT, colors["blanco"],size=(200,75), clickable=True, spacing=100),
            "langToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 50, (0,255,255,10), colors["celesteOpaco"], f"Language: {'EN' if self.language == 'EN' else 'ES'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "musicToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 120, (0,255,255,10), colors["celesteOpaco"], f"Music: {'on' if self.musicToggle else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "fullscrToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 190, (0,255,255,10), colors["celesteOpaco"], f"Full Screen: {'on' if self.fullscreen else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "scale": userInterface.Button(ScrWidth - 150, ScrHeight - 260, (0,255,255,10), colors["celesteOpaco"], f"Scale: {'BIG' if self.bigScale else 'MID'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "shakeToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 330, (0,255,255,10), colors["celesteOpaco"], f"Scr Shake: {'on' if self.shakeToggle else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "fogToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 400, (0,255,255,10), colors["celesteOpaco"], f"Fog: {'on' if self.fogToggle else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "quit": userInterface.Button(150, ScrHeight - 50, (0,255,255,10), colors["celesteOpaco"], "Quit", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
        }
        self.menuButtonsES:dict[str,userInterface.Button] = {
            "start": userInterface.Button(210, ScrHeight//2 - 110, (0,255,255,10), colors["celesteOpaco"], "Jugar", BIGFONT, colors["blanco"], clickable=True, spacing=200),
            "load": userInterface.Button(175, ScrHeight//2 + 25, (0,255,255,10), colors["celesteOpaco"], "Cargar", SMALLFONT, colors["blanco"],size=(250,75), clickable=True, spacing=50),
            "endlessMode": userInterface.Button(425, ScrHeight//2 + 25, (0,255,255,10), colors["celesteOpaco"], "Sin Fin", SMALLFONT, colors["blanco"],size=(250,75), clickable=True, spacing=50),
            "store": userInterface.Button(150, ScrHeight//2 + 120, (0,255,255,10), colors["celesteOpaco"], "Tienda", SMALLFONT, colors["blanco"],size=(200,75), clickable=True, spacing=100),
            "langToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 50, (0,255,255,10), colors["celesteOpaco"], f"Idioma: ES", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "musicToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 120, (0,255,255,10), colors["celesteOpaco"], f"Musica: {'on' if self.musicToggle else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "fullscrToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 190, (0,255,255,10), colors["celesteOpaco"], f"Pant. Completa: {'on' if self.fullscreen else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "scale": userInterface.Button(ScrWidth - 150, ScrHeight - 260, (0,255,255,10), colors["celesteOpaco"], f"Escala: {'BIG' if self.bigScale else 'MID'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "shakeToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 330, (0,255,255,10), colors["celesteOpaco"], f"Sacudir Pant.: {'on' if self.shakeToggle else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "fogToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 400, (0,255,255,10), colors["celesteOpaco"], f"Niebla: {'on' if self.fogToggle else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "quit": userInterface.Button(150, ScrHeight - 50, (0,255,255,10), colors["celesteOpaco"], "Salir", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),

        }


        self.titleDisplay:pygame.Surface = pygame.Surface((ScrWidth, ScrHeight//2), pygame.SRCALPHA)

        # PETS
        self.pets = []

        if loadSettings:
            self.loadSettings()

        self.updateMenu()

        self.rndmSplashTxt:str = f'{random.choice(splashtextsEN) if self.language == "EN" else random.choice(splashtextsES)}'
        self.pauseFact:str = f'"{random.choice(datosEn) if self.language == "EN" else random.choice(datosEs)}"'
        # EXPLOSIONS
        self.explosions = []

    def updateMenu(self, updateScr=True):
        global ScrWidth, ScrHeight, screenRect, scr, monitor_size, screen, scrollingBackground
        if updateScr:
            if not self.bigScale:
                scr = pygame.display.set_mode((1300,731)) # 640 x 360?
                screen = pygame.Surface((1300,731), pygame.SRCALPHA).convert()
                monitor_size = [pygame.display.Info().current_w, pygame.display.Info().current_h] 

            else:
                scr = pygame.display.set_mode((1600,900)) # 640 x 360?
                screen = pygame.Surface((1600,900), pygame.SRCALPHA).convert()
                monitor_size = [pygame.display.Info().current_w, pygame.display.Info().current_h] 

            ScrWidth = screen.get_width()
            ScrHeight = screen.get_height()
            screenRect = pygame.Rect(0,0,ScrWidth,ScrHeight)

            if self.fullscreen:
                scr = pygame.display.set_mode(monitor_size, pygame.FULLSCREEN)
            
            else:
                scr = pygame.display.set_mode((ScrWidth,ScrHeight))

        initSurfaces()
        self.titleDisplay = pygame.Surface((ScrWidth, ScrHeight//2), pygame.SRCALPHA)
        self.titleDisplay.fill((0,0,0,0))

        title = BIGGESTESTESTESTFONT.render("Zero π", True, colors["celeste"]) if self.bigScale else BIGGESTESTESTFONT.render("Zero π", True, colors["celeste"])
        titleShadow = title.copy()
        titleShadow.fill((255,255,255,255), special_flags=pygame.BLEND_RGBA_MULT)
        titleShadow.fill(colors["celesteOpaco"], special_flags=pygame.BLEND_RGBA_MULT)
        #pygame.draw.line(pauseMenuSurface,colors["celeste"],(200,210),(ScrWidth-200,210),25)
        pygame.draw.rect(self.titleDisplay,colors["celesteTrans"],(ScrWidth//10,220,8*ScrWidth//10,25),border_radius=20) #botline
        pygame.draw.rect(self.titleDisplay,colors["celesteTrans"],(ScrWidth//15,232,13*ScrWidth//15,5),border_radius=20)

        pygame.draw.rect(self.titleDisplay,colors["celesteTrans"],(ScrWidth//10,55,8*ScrWidth//10,25),border_radius=20) #topline
        pygame.draw.rect(self.titleDisplay,colors["celesteTrans"],(ScrWidth//15,65,13*ScrWidth//15,5),border_radius=20)

        pygame.draw.rect(self.titleDisplay,colors["celesteTrans"],(0,125,ScrWidth,50),border_radius=20) #medline

        pygame.draw.circle(self.titleDisplay,colors["celesteTrans"],(ScrWidth//4,150),95)
        polycenter = (3*ScrWidth//4, 150)
        polyvect = pygame.Vector2(-120, 0)
        polypoints = [
            pygame.Vector2(polycenter + polyvect),
            pygame.Vector2(polycenter + polyvect.rotate(130)),
            pygame.Vector2(polycenter + polyvect.rotate(-130)),
        ]
        pygame.draw.polygon(self.titleDisplay,colors["celesteTrans"],polypoints)

        self.titleDisplay.blit(titleShadow, (titleShadow.get_rect(center=(ScrWidth//2-10, 160))))
        self.titleDisplay.blit(title, (title.get_rect(center=(ScrWidth//2,150))))
        #pygame.image.save(self.titleDisplay, 'title.png')

        self.pauseFact = f'"{random.choice(datosEn) if self.language == "EN" else random.choice(datosEs)}"'


        self.pauseButtonsEN:dict[str,userInterface.Button] = {
            "continue" : userInterface.Button(ScrWidth//2, ScrHeight//2+100+50*0, (0,0,0,50), colors["gris"], "Continue", SMALLESTFONT, colors["blanco"], size=(525,40),clickable=True),
            "shakeToggle" : userInterface.Button(ScrWidth//2-137, ScrHeight//2+100+50*1, (0,0,0,50), colors["gris"], f"Scr Shake: {'on' if self.shakeToggle else 'off'}", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "musicToggle" : userInterface.Button(ScrWidth//2-137, ScrHeight//2+100+50*2, (0,0,0,50), colors["gris"], f"Music: {'on' if self.musicToggle else 'off'}", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "save" : userInterface.Button(ScrWidth//2-137, ScrHeight//2+100+50*3, (0,0,0,50), colors["gris"], "Save Run", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "fogToggle" : userInterface.Button(ScrWidth//2+137, ScrHeight//2+100+50*1, (0,0,0,50), colors["gris"], f"Fog: {'on' if self.fogToggle else 'off'}", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "fullscrToggle" : userInterface.Button(ScrWidth//2+137, ScrHeight//2+100+50*2, (0,0,0,50), colors["gris"], f"Full Screen: {'on' if self.fullscreen else 'off'}", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "back" : userInterface.Button(ScrWidth//2+137, ScrHeight//2+100+50*3, (0,0,0,50), colors["gris"], "Back to Menu", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            }       
        self.pauseButtonsES:dict[str,userInterface.Button] = {
            "continue" : userInterface.Button(ScrWidth//2, ScrHeight//2+100+50*0, (0,0,0,50), colors["gris"], "Continuar", SMALLESTFONT, colors["blanco"], size=(525,40),clickable=True),
            "shakeToggle" : userInterface.Button(ScrWidth//2-137, ScrHeight//2+100+50*1, (0,0,0,50), colors["gris"], f"Sacudir Pant: {'on' if self.shakeToggle else 'off'}", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "musicToggle" : userInterface.Button(ScrWidth//2-137, ScrHeight//2+100+50*2, (0,0,0,50), colors["gris"], f"Musica: {'on' if self.musicToggle else 'off'}", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "save" : userInterface.Button(ScrWidth//2-137, ScrHeight//2+100+50*3, (0,0,0,50), colors["gris"], "Guardar Partida", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "fogToggle" : userInterface.Button(ScrWidth//2+137, ScrHeight//2+100+50*1, (0,0,0,50), colors["gris"], f"Niebla: {'on' if self.fogToggle else 'off'}", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "fullscrToggle" : userInterface.Button(ScrWidth//2+137, ScrHeight//2+100+50*2, (0,0,0,50), colors["gris"], f"Pant Completa: {'on' if self.fullscreen else 'off'}", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            "back" : userInterface.Button(ScrWidth//2+137, ScrHeight//2+100+50*3, (0,0,0,50), colors["gris"], "Volver al Menu", SMALLESTFONT, colors["blanco"], size=(250,40),clickable=True),
            }

        self.menuButtonsEN:dict[str,userInterface.Button] = {
            "start": userInterface.Button(200, ScrHeight//2, (0,255,255,10), colors["celesteOpaco"], "Start", BIGFONT, colors["blanco"], clickable=True, size=(300,150)),
            "endlessMode": userInterface.Button(200, ScrHeight//2 - 105, (0,255,255,10), colors["celesteOpaco"], f'Endless (record: {self.maxEndlessKills})', SMALLFONT, colors["blanco"],size=(300,50), clickable=True, spacing=50),
            "load": userInterface.Button(175, ScrHeight//2 + 121, (0,255,255,10), colors["celesteOpaco"], "Load Game", SMALLFONT, colors["blanco"],size=(250,75), clickable=True, spacing=50),
            "store": userInterface.Button(150, ScrHeight//2 + 204, (0,255,255,10), colors["celesteOpaco"], "Store", SMALLFONT, colors["blanco"],size=(200,75), clickable=True, spacing=100),
            "langToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 50, (0,255,255,10), colors["celesteOpaco"], f"Language: EN", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "musicToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 120, (0,255,255,10), colors["celesteOpaco"], f"Music: {'on' if self.musicToggle else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "fullscrToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 190, (0,255,255,10), colors["celesteOpaco"], f"Full Screen: {'on' if self.fullscreen else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "scale": userInterface.Button(ScrWidth - 150, ScrHeight - 260, (0,255,255,10), colors["celesteOpaco"], f"Scale: {'BIG' if self.bigScale else 'MID'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "shakeToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 330, (0,255,255,10), colors["celesteOpaco"], f"Scr Shake: {'on' if self.shakeToggle else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "fogToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 400, (0,255,255,10), colors["celesteOpaco"], f"Fog: {'on' if self.fogToggle else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "quit": userInterface.Button(150, ScrHeight - 50, (0,255,255,10), colors["celesteOpaco"], "Quit", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
        }
        self.menuButtonsES:dict[str,userInterface.Button] = {
            "start": userInterface.Button(200, ScrHeight//2, (0,255,255,10), colors["celesteOpaco"], "Jugar", BIGFONT, colors["blanco"], clickable=True, size=(300,150)),
            "endlessMode": userInterface.Button(200, ScrHeight//2 - 105, (0,255,255,10), colors["celesteOpaco"], f'Sin Fin (record: {self.maxEndlessKills})', SMALLFONT, colors["blanco"],size=(300,50), clickable=True, spacing=50),
            "load": userInterface.Button(175, ScrHeight//2 + 121, (0,255,255,10), colors["celesteOpaco"], "Cargar", SMALLFONT, colors["blanco"],size=(250,75), clickable=True, spacing=50),
            "store": userInterface.Button(150, ScrHeight//2 + 204, (0,255,255,10), colors["celesteOpaco"], "Tienda", SMALLFONT, colors["blanco"],size=(200,75), clickable=True, spacing=100),
            "langToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 50, (0,255,255,10), colors["celesteOpaco"], f"Idioma: ES", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "musicToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 120, (0,255,255,10), colors["celesteOpaco"], f"Musica: {'on' if self.musicToggle else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "fullscrToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 190, (0,255,255,10), colors["celesteOpaco"], f"Pant. Comp.: {'on' if self.fullscreen else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "scale": userInterface.Button(ScrWidth - 150, ScrHeight - 260, (0,255,255,10), colors["celesteOpaco"], f"Escala: {'BIG' if self.bigScale else 'MID'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "shakeToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 330, (0,255,255,10), colors["celesteOpaco"], f"Sacudir Pant.: {'on' if self.shakeToggle else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "fogToggle": userInterface.Button(ScrWidth - 150, ScrHeight - 400, (0,255,255,10), colors["celesteOpaco"], f"Niebla: {'on' if self.fogToggle else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),
            "quit": userInterface.Button(150, ScrHeight - 50, (0,255,255,10), colors["celesteOpaco"], "Salir", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50),

        }

        # update buttons
        if self.language == 'EN':
            self.menuButtons = self.menuButtonsEN.copy()
            self.pauseButtons = self.pauseButtonsEN.copy()
        else:
            self.menuButtons = self.menuButtonsES.copy()
            self.pauseButtons = self.pauseButtonsES.copy()

        # update store
        store.updateStoreGui(ScrWidth, self.language)

    def generateScreenShake(self, seconds:float):
        if self.shakeToggle:
            self.shakeTime = seconds if seconds > self.shakeTime else self.shakeTime

    def handleExplosions(self):
        if self.explosions:
            pos,radius,damagePlayer,damage,color = self.explosions.pop(0)
            pos = pygame.Vector2(pos)      
            # 1) play sound & shake screen
            randomizeSound(sounds["explosion"], volume=min(damage/50, 1.0))
            game.generateScreenShake(min(5, damage * radius / 1000))
            
            # 2) spawn particles (all in pure Python)
            epi = 0
            for p in particles:
                if p.type != "explosion":
                    break
                else:
                    epi += 1
            particles.insert(epi, Particle("explosion", pos, color, radius, radius, duration=5))
            ring = Particle("ring", pos, color, 1, radius, damage, width=3)
            dots = [Particle("dot", pos, color, speed=damage) for _ in range(int(damage*2))]
            particles.extend([ring] + dots)
            
            # 3) call the JIT-compiled damage pass
            enemy_count   = len(enemies)
            positions_x   = np.empty(enemy_count, dtype=np.float32)
            positions_y   = np.empty(enemy_count, dtype=np.float32)
            health_array  = np.empty(enemy_count, dtype=np.float32)
            for i, e in enumerate(enemies):
                positions_x[i]  = e.pos.x
                positions_y[i]  = e.pos.y
                health_array[i] = e.health

            apply_explosion_damage(positions_x, positions_y, health_array,
                                pos.x, pos.y, damage, radius)
            
            # 4) write back updated health to Enemy objects
            for e,h in zip(enemies,health_array):
                if e.type != "fairy":
                    e.hit(e.health-int(h),player)
            
            # 5) player damage (pure Python)
            if damagePlayer:
                if (pos - player.pos).length_squared() < radius*radius:
                    knock = (player.pos - pos).normalize() * damage * 10
                    player.velocity += knock
                    player.collisions(damage)
            
            # 6) boss-fight snake damage (pure Python)
            if game.gameplayStage == "bossFight":
                for idx, point in enumerate(snake.snake.points):
                    if (pos - point).length_squared() < (radius + snake.snake.bodyRadiuses[idx])**2:
                        snake.health -= damage
                        break

    def updateScreenPos(self):
        if not self.shakeToggle or self.shakeTime <= 0:
            self.scrBlitPos = (0,0)
        else:
            if self.shakeTime > 0:
                dir = random.choice(self.shakePos)*min(10**(self.shakeTime), 5)
                self.scrBlitPos = (dir.x,dir.y)
                self.shakeTime -= dt

    def mainMenu(self):
        global bullets, enemies, particles, player, running, screen, scr, ScrWidth, ScrHeight, screenRect, monitor_size, save
        mouse = pygame.mouse.get_pressed()
        mousePos = pygame.mouse.get_pos()

        # TITLE
        surfaces["guiSurf"]["surface"].fill((0,25,25,50))
        surfaces["guiSurf"]["surface"].blit(self.titleDisplay, (0,0))

        # SPLASHTEXT
        splashtext = jumpingFont(20, currentTime).render(f'"{self.rndmSplashTxt}"',True,colors["amarillo"])
        splashtextrect = splashtext.get_rect()
        trurect = SMALLESTFONT.size(self.rndmSplashTxt)
        center = int(ScrWidth - 150 - trurect[0]/2), int(225 - trurect[1]/2 - 10)
        blitpos = (center[0] - splashtextrect.width/2, center[1] - splashtextrect.height/2)

        splashtextsurf = pygame.Surface((splashtextrect.width,splashtextrect.height), pygame.SRCALPHA)
        splashtextsurf.blit(splashtext, (0,0))
        splashtextsurfrot = pygame.transform.rotozoom(splashtextsurf, 5,1)
        surfaces["guiSurf"]["surface"].blit(splashtextsurfrot, blitpos)

        # draw skills purchased
        if self.playerSelectedSkillSet != []:
            drawSkillIcons(self.playerSelectedSkillSet, True)

        # BUTTONS
        
        # START BUTTON
        self.menuButtons["start"].draw(surfaces["guiSurf"]["surface"],screen)
        if self.menuButtons["start"].clicked(mousePos[0],mousePos[1],mouse[0],surfaces["guiSurf"]["surface"],True):
            self.gameplayStage = "wavesGameLoop"
            pygame.mixer.music.stop()


            surfaces["guiSurf"]["surface"].fill((0,0,0,0))
                        
            bullets = []
            enemies = []
            particles = []
            player=Player(color=self.playerSelectedColor)
            player.pos = pygame.Vector2(ScrWidth//2,ScrHeight//2)
            # set purchases
            player.gun = self.playerSelectedGun
            player.skillSet = [Skill(s, player) for s in self.playerSelectedSkillSet if self.playerSelectedSkillSet != []]
            # reset purchases
            self.playerSelectedSkillSet = []
            self.playerSelectedGun = "default"

            self.resetWavesLoop()

        # ENDLESS MODE BUTTON
        self.menuButtons["endlessMode"].draw(surfaces["guiSurf"]["surface"],screen)
        if self.pets == []:
            surf = pygame.Surface(self.menuButtons["endlessMode"].buttonRect.size, pygame.SRCALPHA)
            surf.fill((100,100,100,100))
            surfaces["guiSurf"]["surface"].blit(surf, surf.get_rect(center=((self.menuButtons["endlessMode"].x,self.menuButtons["endlessMode"].y))),special_flags=pygame.BLEND_RGB_SUB)
        else:
            if self.menuButtons["endlessMode"].clicked(mousePos[0],mousePos[1],mouse[0],surfaces["guiSurf"]["surface"],True):
                self.gameplayStage = "endlessMode"
                pygame.mixer.music.stop()
                # reset
                bullets = []
                enemies = []
                player=Player(color=self.playerSelectedColor)
                player.pos = pygame.Vector2(ScrWidth//2,ScrHeight//2)

                self.endlessChoiceAmmount = 10

                self.resetWavesLoop()
                particles = []
                resetUI()
                alignChoices()


        # QUIT BUTTON
        self.menuButtons["quit"].draw(surfaces["guiSurf"]["surface"],screen)
        if self.menuButtons["quit"].clicked(mousePos[0],mousePos[1],mouse[0],surfaces["guiSurf"]["surface"],True):
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        
        # MUSIC BUTTON
        self.menuButtons["musicToggle"].draw(surfaces["guiSurf"]["surface"],screen)
        if self.menuButtons["musicToggle"].clicked(mousePos[0],mousePos[1],mouse[0],surfaces["guiSurf"]["surface"],True):
            self.musicToggle = not self.musicToggle
            playMusic("")

            if not self.musicToggle:
                pygame.mixer.music.stop()
            else:
                pygame.mixer.music.play()
            
            self.menuButtons["musicToggle"].move(self.menuButtons["musicToggle"].x,self.menuButtons["musicToggle"].y,textdisplay=f"{'Music: ' if self.language == 'EN' else 'Musica: '}{'on' if self.musicToggle else 'off'}")
            self.pauseButtons["musicToggle"].move(self.pauseButtons["musicToggle"].x,self.pauseButtons["musicToggle"].y,textdisplay=f"{'Music: ' if self.language == 'EN' else 'Musica: '}{'on' if self.musicToggle else 'off'}")

            

        # STORE BUTTON
        self.menuButtons["store"].draw(surfaces["guiSurf"]["surface"],screen)
        if self.menuButtons["store"].clicked(mousePos[0],mousePos[1],mouse[0],surfaces["guiSurf"]["surface"],True):
            self.inStore = True
        
        # LANGUAGE BUTTON
        self.menuButtons["langToggle"].draw(surfaces["guiSurf"]["surface"],screen)
        if self.menuButtons["langToggle"].clicked(mousePos[0],mousePos[1],mouse[0],surfaces["guiSurf"]["surface"],True):
            
            if self.language == 'EN':
                # A ESPAÑOL
                self.language = 'ES'
                self.rndmSplashTxt = f'{random.choice(splashtextsES)}'
                self.menuButtons = self.menuButtonsES.copy()
                self.pauseButtons = self.pauseButtonsES.copy()
            else:
                # TO ENGLISH
                self.language = 'EN'
                self.rndmSplashTxt = f'{random.choice(splashtextsEN)}'
                self.menuButtons = self.menuButtonsEN.copy()
                self.pauseButtons = self.pauseButtonsEN.copy()

            store.updateStoreGui(ScrWidth, self.language)
        
        # SCALE BUTTON
        self.menuButtons["scale"].draw(surfaces["guiSurf"]["surface"],screen)
        if self.menuButtons["scale"].clicked(mousePos[0],mousePos[1],mouse[0],surfaces["guiSurf"]["surface"],True):
            self.bigScale = not self.bigScale
            self.updateMenu()
            resetUI()
            alignChoices()
            store.updateStoreGui(ScrWidth, self.language)

        # FULLSCR BUTTON
        self.menuButtons["fullscrToggle"].draw(surfaces["guiSurf"]["surface"],screen)
        if self.menuButtons["fullscrToggle"].clicked(mousePos[0],mousePos[1],mouse[0],surfaces["guiSurf"]["surface"],True):
        
            self.fullscreen = not self.fullscreen
            self.updateMenu()
            if self.fullscreen:
                scr = pygame.display.set_mode(monitor_size, pygame.FULLSCREEN)
            
            else:
                scr = pygame.display.set_mode((ScrWidth,ScrHeight))

        # SCR SHAKE TOGGLE
        self.menuButtons["shakeToggle"].draw(surfaces["guiSurf"]["surface"],screen)
        if self.menuButtons["shakeToggle"].clicked(mousePos[0],mousePos[1],mouse[0],surfaces["guiSurf"]["surface"],True):
            self.shakeToggle = not self.shakeToggle
            
            self.menuButtons["shakeToggle"].move(self.menuButtons["shakeToggle"].x,self.menuButtons["shakeToggle"].y,textdisplay=f"{'Scr Shake: ' if self.language == 'EN' else 'Sacudir Pant.: '}{'on' if self.shakeToggle else 'off'}")
            self.pauseButtons["shakeToggle"].move(self.pauseButtons["shakeToggle"].x,self.pauseButtons["shakeToggle"].y,textdisplay=f"{'Scr Shake: ' if self.language == 'EN' else 'Sacudir Pant.: '}{'on' if self.shakeToggle else 'off'}")

        # FOG TOGGLE
        self.menuButtons["fogToggle"].draw(surfaces["guiSurf"]["surface"],screen)
        if self.menuButtons["fogToggle"].clicked(mousePos[0],mousePos[1],mouse[0],surfaces["guiSurf"]["surface"],True):
            self.fogToggle = not self.fogToggle
            
            self.menuButtons["fogToggle"].move(self.menuButtons["fogToggle"].x,self.menuButtons["fogToggle"].y,textdisplay=f"{'Fog: ' if self.language == 'EN' else 'Niebla: '}{'on' if self.fogToggle else 'off'}")
            self.pauseButtons["fogToggle"].move(self.pauseButtons["fogToggle"].x,self.pauseButtons["fogToggle"].y,textdisplay=f"{'Fog: ' if self.language == 'EN' else 'Niebla: '}{'on' if self.fogToggle else 'off'}")




        # LOAD BUTTON
        self.menuButtons["load"].draw(surfaces["guiSurf"]["surface"],screen)
        if self.menuButtons["load"].clicked(mousePos[0],mousePos[1],mouse[0],surfaces["guiSurf"]["surface"],True):
            for p in particles:
                p.radius = 0
            
            loadSave(save)
            resetUI()

        screen.blit(save.icon, save.icon.get_rect(center=(self.menuButtons["load"].x,self.menuButtons["load"].y)))

        # fairy and pets ! :3
        for pet in self.pets:
            pet.move()
            pet.draw(screen)

        mainMenuFairy.move()
        mainMenuFairy.draw(screen)
        screen.blit(surfaces["particles"]["surface"], (0,0))

        screen.blit(surfaces["guiSurf"]["surface"], (0,0))
        surfaces["guiSurf"]["surface"].fill((0,0,0,0))

    def store(self):
        global scrollingBackground

        mouse = pygame.mouse.get_pressed()
        mousePos = pygame.mouse.get_pos()

        surfaces["guiSurf"]["surface"].fill((0,25,25,50))
        
        # draw store
        store.draw(self.coins, surfaces["guiSurf"]["surface"], screen)
        # purchase
        purchase, price = store.getPurchases(self.coins, mousePos[0], mousePos[1], mouse[0],screen)

        if purchase != "":
            print(purchase + " purchased!")
            
            if purchase in guns.keys():
                self.playerSelectedGun = purchase
                self.coins -= price
                sounds["coin"].play()

            elif purchase in skills.keys():
                self.playerSelectedSkillSet.append(purchase)
                self.coins -= price
                sounds["coin"].play()

            elif purchase in bgPurchasableColors.keys():
                self.backgroundColor = [c//8 for c in bgPurchasableColors[purchase]["color"]]
                scrollingBackground.change_base_color(self.backgroundColor)
                self.coins -= price
                sounds["coin"].play()

            elif purchase in pPurchasableColors.keys():
                self.playerSelectedColor = pPurchasableColors[purchase]["color"]
                self.coins -= price
                sounds["coin"].play()


        # draw skills purchased
        if self.playerSelectedSkillSet:
            drawSkillIcons(self.playerSelectedSkillSet, True)


        # QUIT BUTTON
        self.menuButtons["quit"].draw(surfaces["guiSurf"]["surface"],screen)
        if self.menuButtons["quit"].clicked(mousePos[0],mousePos[1],mouse[0],surfaces["guiSurf"]["surface"],True):
            self.inStore = False

        # STORE SIGN
        storesign = BIGGESTFONT.render(f"- {'TIENDA' if self.language == 'ES' else 'STORE'} -", True, colors["celeste"])
        surfaces["guiSurf"]["surface"].blit(storesign, storesign.get_rect(center=(ScrWidth//2, 30)))

        # COIN DISPLAY
        pygame.draw.rect(surfaces["guiSurf"]["surface"], colors["amarillo"], (25,25,25,25), border_radius=5)
        surfaces["guiSurf"]["surface"].blit(SMALLFONT.render(str(self.coins), True, colors["blanco"]), (60,15))

        screen.blit(surfaces["guiSurf"]["surface"], (0,0))

    def deathMenu(self):
        global updateParticles, particles
        self.scrBlitPos = (0,0)
        def format_timer(seconds):
            # Extract hours, minutes, and seconds
            hours = math.floor(seconds // 3600)
            minutes = math.floor((seconds % 3600) // 60)
            secs = math.floor(seconds % 60)
            milliseconds = int((seconds - math.floor(seconds)) * 100)  # Get the fractional part as milliseconds

            # Format the string
            return f"{hours:02}:{minutes:02}:{secs:02}:{milliseconds:02}" # zero padded and two dig long

        mousepos = pygame.mouse.get_pos()
        mouseclick = pygame.mouse.get_pressed()

        updateParticles = False
        # player
        player.ult(screen)
        player.draw(screen)

        for e in enemies:
            e.draw(screen)
        
        for b in bullets:
            b.draw(screen)

        screen.blit(surfaces["guiSurf"]["surface"], (0,0))
        screen.blit(surfaces["particles"]["surface"], (0,0))

        # DEATH UI
        surfaces["pauseSurf"]["surface"].fill((50,10,10,150))
        title = BIGGESTFONT.render("Zero π", True, colors["gris"])
        pause = SMALLFONT.render("- MORISTE -", True,colors["blanco"]) if self.language == 'ES' else SMALLFONT.render("- YOU DIED -", True,colors["negro"])
        timeShow = SMALLESTFONT.render(f"{'Run Time' if self.language == 'EN' else 'Tiempo en Partida'}: {format_timer(self.playTime)}", True, colors["blanco"])
        
        surfaces["pauseSurf"]["surface"].blit(title, (ScrWidth//2 - title.get_width()//2, ScrHeight//2 - 200))
        surfaces["pauseSurf"]["surface"].blit(pause, (ScrWidth//2 - pause.get_width()//2, ScrHeight//2 - 100))
        surfaces["pauseSurf"]["surface"].blit(timeShow, (ScrWidth//2 - timeShow.get_width()//2, ScrHeight//2 - 130))

        # BUTTONS
        self.pauseButtons["back"].draw(surfaces["pauseSurf"]["surface"], screen)
        
        if self.pauseButtons["back"].clicked(mousepos[0], mousepos[1], mouseclick[0], screen, True):
            updateParticles = True
            for particle in particles:
                particle.radius = 0
            self.gameplayStage = "mainMenu"

        screen.blit(surfaces["pauseSurf"]["surface"], (0,0))

    def pauseMenu(self):
        global updateParticles, particles, scr, save, enemies, bullets, player
        self.scrBlitPos = (0,0)

        def format_timer(seconds):
            # Extract hours, minutes, and seconds
            hours = math.floor(seconds // 3600)
            minutes = math.floor((seconds % 3600) // 60)
            secs = math.floor(seconds % 60)
            milliseconds = int((seconds - math.floor(seconds)) * 100)  # Get the fractional part as milliseconds

            # Format the string
            return f"{hours:02}:{minutes:02}:{secs:02}:{milliseconds:02}" # zero padded and two dig long


        mousepos = pygame.mouse.get_pos()
        mouseclick = pygame.mouse.get_pressed()

        updateParticles = False
        if self.gameplayStage == "bossFight":
            snake.draw(screen)
        # player
        player.ult(screen)
        player.draw(screen)
        for p in self.pets:
            p.draw(screen)

        for e in enemies:
            e.draw(screen)
        
        for b in bullets:
            b.draw(screen)
        
        

        screen.blit(surfaces["guiSurf"]["surface"], (0,0))
        screen.blit(surfaces["particles"]["surface"], (0,0))

        # PAUSE UI
        surfaces["pauseSurf"]["surface"].fill((10,10,10,150))
        title = BIGGESTFONT.render("Zero π", True, colors["celeste"])
        pause = SMALLFONT.render("- PAUSA -", True,colors["blanco"]) if self.language == 'ES' else SMALLFONT.render("- PAUSE -", True,colors["blanco"])

        factWord = SMALLFONT.render("Dato:", True, colors["blanco"]) if self.language == 'ES' else SMALLFONT.render("Fact:", True, colors["blanco"])

        factShow = userInterface.textWrap(f"{self.pauseFact}", SMALLESTFONT, ScrWidth//2, 100, pygame.Rect(100,100,ScrWidth-300,50), colors["blanco"])
        timeShow = SMALLESTFONT.render(f"{'Run Time' if self.language == 'EN' else 'Tiempo en Partida'}: {format_timer(self.playTime)}", True, colors["blanco"])

        surfaces["pauseSurf"]["surface"].blit(factWord, (ScrWidth//2 - factWord.get_width()//2, 50))

        for line in factShow:
            surfaces["pauseSurf"]["surface"].blit(line[0], line[1])

        surfaces["pauseSurf"]["surface"].blit(timeShow, (ScrWidth//2 - timeShow.get_width()//2, ScrHeight//2 - 130))
        
        surfaces["pauseSurf"]["surface"].blit(title, (ScrWidth//2 - title.get_width()//2, ScrHeight//2 - 200))
        surfaces["pauseSurf"]["surface"].blit(pause, (ScrWidth//2 - pause.get_width()//2, ScrHeight//2 - 100))

        # BUTTONS
        for button in self.pauseButtons:
            self.pauseButtons[button].draw(surfaces["pauseSurf"]["surface"], screen)
        
        if self.pauseButtons["continue"].clicked(mousepos[0], mousepos[1], mouseclick[0], screen, True) or player.keys[pygame.K_ESCAPE]:
            player.keys[pygame.K_ESCAPE] = False
            sounds["liveup"].play()

            pygame.mixer.music.unpause()
            pygame.mixer.unpause()


            updateParticles = True
            self.paused = False
        # BACK BUTTON
        if self.pauseButtons["back"].clicked(mousepos[0], mousepos[1], mouseclick[0], screen, True):
            if self.gameplayStage == "bossFight":
                global scrollingFog
                scrollingFog.change_base_color(colors["gris"])
            updateParticles = True
            for particle in particles:
                particle.radius = 0            
            
            enemies = []
            bullets = []

            pygame.mixer.music.unpause()

            self.paused = False
            self.gameplayStage = "mainMenu"
            self.updateMenu(updateScr=False)
        
        # FULLSCR BUTTON
        if self.pauseButtons["fullscrToggle"].clicked(mousepos[0],mousepos[1],mouseclick[0],screen,True):
        
            self.fullscreen = not self.fullscreen
            self.updateMenu()
            if self.fullscreen:
                scr = pygame.display.set_mode(monitor_size, pygame.FULLSCREEN)
            
            else:
                scr = pygame.display.set_mode((ScrWidth,ScrHeight))

        
        # MUSIC BUTTON
        if self.pauseButtons["musicToggle"].clicked(mousepos[0],mousepos[1],mouseclick[0],screen,True):
            self.musicToggle = not self.musicToggle
            playMusic("")

            if not self.musicToggle:
                pygame.mixer.music.stop()
            else:
                pygame.mixer.music.play()
                pygame.mixer.music.pause()

            self.pauseButtons["musicToggle"].move(self.pauseButtons["musicToggle"].x,self.pauseButtons["musicToggle"].y,textdisplay=f"{'Music: ' if self.language == 'EN' else 'Musica: '}{'on' if self.musicToggle else 'off'}")
            self.menuButtons["musicToggle"].move(self.menuButtons["musicToggle"].x,self.menuButtons["musicToggle"].y,textdisplay=f"{'Music: ' if self.language == 'EN' else 'Musica: '}{'on' if self.musicToggle else 'off'}")
        
        # SCR SHAKE TOGGLE
        if self.pauseButtons["shakeToggle"].clicked(mousepos[0],mousepos[1],mouseclick[0],screen,True):
            self.shakeToggle = not self.shakeToggle
            
            self.pauseButtons["shakeToggle"].move(self.pauseButtons["shakeToggle"].x,self.pauseButtons["shakeToggle"].y,textdisplay=f"{'Scr Shake: ' if self.language == 'EN' else 'Sacudir Pant.: '}{'on' if self.shakeToggle else 'off'}")
        
        # FOG TOGGLE
        if self.pauseButtons["fogToggle"].clicked(mousepos[0],mousepos[1],mouseclick[0],screen,True):
            self.fogToggle = not self.fogToggle
            
            self.pauseButtons["fogToggle"].move(self.pauseButtons["fogToggle"].x,self.pauseButtons["fogToggle"].y,textdisplay=f"{'Fog: ' if self.language == 'EN' else 'Niebla: '}{'on' if self.fogToggle else 'off'}")



        # SAVE BUTTON
        if self.pauseButtons["save"].clicked(mousepos[0],mousepos[1],mouseclick[0],screen,True):
            p = Particle("firework", pygame.Vector2(random.randint(100,ScrWidth-100), ScrHeight), random.choice(list(colors.values())), glow=3)
            particles.append(p)
            save = Save(bullets, enemies, particles, player, snake, game)
            save.save("gamefiles/save.json")
        

        screen.blit(surfaces["pauseSurf"]["surface"], (0,0))
             
    def resetWavesLoop(self):
        self.waveNumber:int = 0
        waveRewards(self, player)
        self.waveNumber = 1
        self.waveProgress:int = 0
        self.waveEnd:int = 5
        self.difficulty:int = 0
        self.enemySpawnRate:int = 0
        self.waveWaitTimer = 0
        self.nextWaveStart = True
        self.totalProgress = 0 # kills
        self.playTime = 0
        text1 = Particle("text", (ScrWidth//2, ScrHeight//2-100), colors["gris"], text="W, A, S, D para MOVERTE", font=BIGFONT, duration=5, speed=0)
        text2 = Particle("text", (ScrWidth//2, ScrHeight//2+100), colors["gris"], text="ESPACIO para CORRER", font=BIGFONT, duration=5, speed=0)
        text3 = Particle("text", (ScrWidth//2, ScrHeight//2+200), colors["gris"], text="CLK IZQ para DISPARAR", font=BIGFONT, duration=5, speed=0)
        if self.language == 'EN':
            text1 = Particle("text", (ScrWidth//2, ScrHeight//2-100), colors["gris"], text="W, A, S, D to MOVE", font=BIGFONT, duration=5, speed=0)
            text2 = Particle("text", (ScrWidth//2, ScrHeight//2+100), colors["gris"], text="SPACE to RUN", font=BIGFONT, duration=5, speed=0)
            text3 = Particle("text", (ScrWidth//2, ScrHeight//2+200), colors["gris"], text="LFT CLK to SHOOT", font=BIGFONT, duration=5, speed=0)

        particles.append(text1)
        particles.append(text2)
        particles.append(text3)

        resetUI()

    def wavesGameLoop(self):
        global enemies, bullets, player, particles, snake

        self.playTime += dt

        self.updateScreenPos()

        # PLAYER INPUT AND UPDATES
        mousePos = pygame.mouse.get_pos() 
        mouseClick = pygame.mouse.get_pressed()

        player.getInputs("const", mousePos=mousePos, mouseClick=mouseClick)

        player.ult(screen)
        player.draw(screen)

        for pet in self.pets:
            pet.move()
            pet.heal(player)
            pet.draw(screen)

        player.move()
        player.collisions()

        # ENEMIES SPAWN
        # wait for wave to start
        if self.waveWaitTimer < 5:
            
            if not self.nextWaveStart:
                waveRewards(self, player)
            else:
                self.waveWaitTimer += dt
                loadBar(screen,(ScrWidth//2,ScrHeight-50),self.waveWaitTimer,5,colors["gris"],pixelLength=8*ScrWidth//10)
        
        else:
            
            # spawn enemies
            if self.waveProgress < self.waveEnd:
                if len([e for e in enemies if e.type not in ["fairy","swap"]]) < max(20,self.waveNumber//2):
                    if spawnEnemies(difficulty=max(1, self.waveNumber//2),rate=max(1, self.waveNumber//2)):
                        self.waveProgress += 1
            
            # start wave timer, inc wave numb, calc wave end
            elif self.waveProgress == self.waveEnd and not player.mouseClick[0]:
                if sum(1 for e in enemies if e.type not in ["fairy", "swap"]) == 0:

                    self.totalProgress += self.waveEnd # to set kills to 0% of bar
                    player.kills = int(self.totalProgress)
                    self.nextWaveStart = False # begin next wave
                    self.waveProgress = 0 # no enemies spawned
                    self.waveWaitTimer = 0 # for when the wave ends
                    self.waveNumber += 1 # next wave
                    self.waveEnd = 5 * self.waveNumber  # how many to spawn
                    self.enemiesToSpawn = [random.choice(spawnableEnemyTypes) for _ in range(random.randint(3,10))] # which ones to spawn
                
                    if self.waveNumber % 25 == 0:
                        global scrollingFog
                        scrollingFog.change_base_color(colors["rojo"])
                        snake = SnakeBoss()
                        self.gameplayStage = "bossFight"
                        self.waveWaitTimer = 0


        # explosions
        self.handleExplosions()
        # enemies
        for enemy in enemies:
            # bullet colision
            for bullet in bullets:
                if (enemy.pos - bullet.pos).length() <= max(25,enemy.collisionRadius + bullet.radius):
                    enemy.hit(1,player)
                    bullets.remove(bullet)
                    particles.append(Particle("ring",bullet.pos,colors["blanco"],4,7,0.5,3))
            
            # enemy colision
            if enemy.type not in ["fairy", "swap"]:

                if not player.invulnerability and enemy.type != "guardian":
                    enemy.target = player.pos 

                if (enemy.pos - player.pos).length() < enemy.radius:
                    player.collisions(damage = enemy.damage)

            enemy.move()

            enemy.draw(surfaces["enemies"]["surface"])
            
        # delete enemies if killd
        enemies = [enemie for enemie in enemies if enemie.health > 0] 
        
        # DEATH
        if player.health <= 0:
            player.health = 0
            self.gameplayStage = "deathMenu" 

        # DRAW
        
        screen.blit(surfaces["enemies"]["surface"], (0,0))
        surfaces["enemies"]["surface"].fill((0,0,0,0))
        
        screen.blit(surfaces["particles"]["surface"], (0,0))
        
        # BULLETS 
        for bullet in bullets:
            bullet.updatePos()
            bullet.draw(screen)
        # delete bullets off screen
        bullets = [bullet for bullet in bullets if screenRect.collidepoint(bullet.pos.x,bullet.pos.y)]  

        drawUI(screen,player,self)

        # PAUSE
        
        if player.keys[pygame.K_ESCAPE]:
            
            player.keys[pygame.K_ESCAPE] = False
            sounds["liveup"].play()
            
            pygame.mixer.music.pause()
            pygame.mixer.pause()

            self.pauseFact = f'"{random.choice(datosEn) if self.language == "EN" else random.choice(datosEs)}"'
            self.paused = True

    def bossFight(self):
        global enemies, bullets, player, particles, snake
        self.updateScreenPos()

        snake.move()
        snake.draw(screen)

        self.playTime += dt

        # PLAYER INPUT AND UPDATES
        mousePos = pygame.mouse.get_pos() 
        mouseClick = pygame.mouse.get_pressed()

        player.getInputs("const", mousePos=mousePos, mouseClick=mouseClick)

        player.ult(screen)
        player.draw(screen)

        if snake.health > 0:
            player.move()
            player.collisions()
            snake.colissions(player)

        # explosions
        self.handleExplosions()
        # enemies
        for enemy in enemies:
            # bullet colision
            for bullet in bullets:
                if (enemy.pos - bullet.pos).length() <= max(25,enemy.collisionRadius + bullet.radius):
                    enemy.hit(1,player)
                    bullets.remove(bullet)
                    particles.append(Particle("ring",bullet.pos,colors["blanco"],4,7,0.5,3))
            
            # enemy colision
            if enemy.type not in ["fairy", "swap"]:

                if not player.invulnerability and enemy.type != "guardian":
                    enemy.target = player.pos 

                if (enemy.pos - player.pos).length() < enemy.radius:
                    player.collisions(damage = enemy.damage)

            enemy.move()

            enemy.draw(surfaces["enemies"]["surface"])
            
        # delete enemies if killd
        enemies = [enemie for enemie in enemies if enemie.health > 0] 
        
        # DEATH
        if player.health <= 0:
            player.health = 0
            self.gameplayStage = "deathMenu" 

        # DRAW
        
        screen.blit(surfaces["enemies"]["surface"], (0,0))
        surfaces["enemies"]["surface"].fill((0,0,0,0))
        
        screen.blit(surfaces["particles"]["surface"], (0,0))
        
        # BULLETS 
        for bullet in bullets:
            bullet.updatePos()
            bullet.draw(screen)
        bullets = [bullet for bullet in bullets if screenRect.collidepoint(bullet.pos.x,bullet.pos.y)]

        player.kills = int(self.totalProgress)

        
        # BOSSFIGHT END
        if snake.health <= 0:
            screen.blit(surfaces["guiSurf"]["surface"],(0,0))
            screen.blit(surfaces["particles"]["surface"], (0,0))
            if self.waveWaitTimer < 10:
                for e in enemies:
                    e.hit(e.health, player)
                self.waveWaitTimer += dt
                white = list(colors["blanco"]) + [0]
                white[3] = self.waveWaitTimer * 25
                surfaces["guiSurf"]["surface"].fill(white)
                
                 # when dead, explode
                if random.randint(1,50):
                    explosion(random.choice(snake.snake.points) + pygame.Vector2(0,25).rotate(random.randint(1,360)), 100, False, 10, snake.snake.bodyColor)
            
            elif self.waveWaitTimer < 20:
                self.waveWaitTimer += dt
                surfaces["guiSurf"]["surface"].fill(colors["blanco"])
                congrats = SMALLFONT.render(f"{'Congratulations.' if self.language == 'EN' else 'Felicitaciones.'}", True, colors["gris"])
                surfaces["guiSurf"]["surface"].blit(congrats, congrats.get_rect(center=(ScrWidth//2,ScrHeight//2)))
                if random.randint(1,100) <= 7:
                    p = Particle("firework", pygame.Vector2(random.randint(100,ScrWidth-100), ScrHeight), random.choice(list(colors.values())), glow=3,trailColor=colors["grisclaro"])
                    particles.append(p)
            
            
            elif self.waveWaitTimer >= 20:
                global scrollingFog
                scrollingFog.change_base_color(colors["gris"])
                # REWARD
                self.pets.append(SnakePet(player))
                # RESET
                surfaces["guiSurf"]["surface"].fill((0,0,0,0))
                resetUI()
                particles.append(Particle("text", (ScrWidth//2, ScrHeight//2), colors["gris"], speed=0.2, duration=5, text=f"{'Wanna keep going?' if self.language == 'EN' else 'Quieres seguir?'}"))
                self.gameplayStage = "wavesGameLoop"
                
                self.totalProgress += self.waveEnd # to set kills to 0% of bar
                player.kills = int(self.totalProgress)
                self.nextWaveStart = False # begin next wave
                self.waveProgress = 0 # no enemies spawned
                self.waveWaitTimer = 0 # for when the wave ends
                self.waveNumber += 1 # next wave
                self.waveEnd = 5 * self.waveNumber  # how many to spawn

        else:
            drawUI(screen,player,self)



            # PAUSE
            
            if player.keys[pygame.K_ESCAPE]:
                
                player.keys[pygame.K_ESCAPE] = False
                sounds["liveup"].play()

                self.pauseFact = f'"{random.choice(datosEn) if self.language == "EN" else random.choice(datosEs)}"'
                self.paused = True

    def endlessMode(self):
        global enemies, bullets, player, particles, snake

        self.playTime += dt

        self.updateScreenPos()

        # PLAYER INPUT AND UPDATES
        mousePos = pygame.mouse.get_pos() 
        mouseClick = pygame.mouse.get_pressed()

        player.getInputs("const", mousePos=mousePos, mouseClick=mouseClick)

        player.ult(screen)
        player.draw(screen)

        for pet in self.pets:
            pet.move()
            pet.heal(player)
            pet.draw(screen)

        player.move()
        player.collisions()


        # ENEMIES SPAWN
        if self.waveWaitTimer < 5:
            
            if self.endlessChoiceAmmount > 0:
                self.endlessChoiceAmmount = endlessChoices(mousePos, mouseClick, choices=self.endlessChoiceAmmount)
            else:
                surfaces["guiSurf"]["surface"].fill((0,0,0,0))
                self.waveWaitTimer += dt
                loadBar(screen,(ScrWidth//2,ScrHeight-50),self.waveWaitTimer,5,colors["gris"],pixelLength=8*ScrWidth//10)
        
        else:
            # Spawn non stop
            spawnEnemies(max(1,round(math.log2(max(1,player.kills)))), max(1,round(math.log2(max(1,player.kills)))))

        # record
        if player.kills > self.maxEndlessKills:
            self.maxEndlessKills = player.kills

        # explosions
        self.handleExplosions()
        # enemies
        for enemy in enemies:
            # bullet colision
            for bullet in bullets:
                if (enemy.pos - bullet.pos).length() <= max(25,enemy.collisionRadius + bullet.radius):
                    enemy.hit(1,player)
                    bullets.remove(bullet)
                    particles.append(Particle("ring",bullet.pos,colors["blanco"],4,7,0.5,3))
            
            # enemy colision
            if enemy.type not in ["fairy", "swap"]:

                if not player.invulnerability and enemy.type != "guardian":
                    enemy.target = player.pos 

                if (enemy.pos - player.pos).length() < enemy.radius:
                    player.collisions(damage = enemy.damage)

            enemy.move()

            enemy.draw(surfaces["enemies"]["surface"])
            
        # delete enemies if killd
        enemies = [enemie for enemie in enemies if enemie.health > 0] 
        
        # DEATH
        if player.health <= 0:
            player.health = 0
            self.gameplayStage = "deathMenu" 

        # DRAW
        
        screen.blit(surfaces["enemies"]["surface"], (0,0))
        surfaces["enemies"]["surface"].fill((0,0,0,0))
        
        screen.blit(surfaces["particles"]["surface"], (0,0))
        
        drawUI(screen,player,self)
        
        # BULLETS 
        for bullet in bullets:
            bullet.updatePos()
            bullet.draw(screen)
        bullets = [bullet for bullet in bullets if screenRect.collidepoint(bullet.pos.x,bullet.pos.y)]  #! delete bullets off screen, add to main loop


        # PAUSE
        
        if player.keys[pygame.K_ESCAPE]:
            
            player.keys[pygame.K_ESCAPE] = False
            sounds["liveup"].play()
            
            pygame.mixer.music.pause()
            pygame.mixer.pause()

            self.pauseFact = f'"{random.choice(datosEn) if self.language == "EN" else random.choice(datosEs)}"'
            self.paused = True

    def run(self):
        if self.paused:
                self.pauseMenu()
        else:
            match self.gameplayStage:
                case "mainMenu":
                    if self.inStore:
                        self.store()
                    else:
                        self.mainMenu()

                case "deathMenu":
                    self.deathMenu()

                case "wavesGameLoop":
                    self.wavesGameLoop()

                case "bossFight":
                    self.bossFight()
                
                case "endlessMode":
                    self.endlessMode()

    def toDict(self) -> dict:
        return {
            # game flow
            "paused":                   self.paused,
            "gameplayStage":            self.gameplayStage,
            "waveNumber":               self.waveNumber,
            "waveProgress":             self.waveProgress,
            "waveEnd":                  self.waveEnd,
            "difficulty":               self.difficulty,
            "enemySpawnRate":           self.enemySpawnRate,
            "waveWaitTimer":            self.waveWaitTimer,
            "nextWaveStart":            self.nextWaveStart,
            "totalProgress":            self.totalProgress,
            "playTime":                 self.playTime,
            "shakeTime":                self.shakeTime,
            "endlessChoiceAmmount":     self.endlessChoiceAmmount,
            # player customization
        }

    def saveSettings(self):
        print("Saving settings...")
        data = {
            "musicToggle": self.musicToggle,
            "shakeToggle": self.shakeToggle,
            "fullscreen": self.fullscreen,
            "language": self.language,
            "bigScale": self.bigScale,
            "fogToggle": self.fogToggle,
            "maxEndlessKills": self.maxEndlessKills,
            "coins": self.coins,
            "playerSelectedColor": self.playerSelectedColor,
            "playerSelectedSkillSet": self.playerSelectedSkillSet,
            "playerSelectedGun": self.playerSelectedGun,
            "backgroundColor": self.backgroundColor,
            "pets": [p.toDict() for p in self.pets]
        }
        with open("gamefiles/settings.json", "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def fromDict(cls, d: dict) -> "GameplayManager":
        gm = cls()  # builds default Buttons + menu

        # restore pure‐data fields
        gm.paused                   = d["paused"]
        gm.gameplayStage            = d["gameplayStage"]
        gm.waveNumber               = d["waveNumber"]
        gm.waveProgress             = d["waveProgress"]
        gm.waveEnd                  = d["waveEnd"]
        gm.difficulty               = d["difficulty"]
        gm.enemySpawnRate           = d["enemySpawnRate"]
        gm.waveWaitTimer            = d["waveWaitTimer"]
        gm.nextWaveStart            = d["nextWaveStart"]
        gm.totalProgress            = d["totalProgress"]
        gm.playTime                 = d["playTime"]
        gm.shakeTime                = d["shakeTime"]
        gm.endlessChoiceAmmount     = d["endlessChoiceAmmount"]


        # rebuild buttons/text to reflect restored toggles
        gm.updateMenu()

        return gm

    def loadSettings(self):
        print("Loading settings...")
        with open("gamefiles/settings.json", "r") as f:
            d:dict = json.load(f)
        
        self.musicToggle = d.get("musicToggle", True)
        self.shakeToggle = d.get("shakeToggle", True)
        self.fullscreen = d.get("fullscreen", False)
        self.language = d.get("language", "EN")
        self.bigScale = d.get("bigScale", False)
        self.fogToggle = d.get("fogToggle", True)
        self.maxEndlessKills = d.get("maxEndlessKills", 0)
        self.coins = d.get("coins", 0)
        self.playerSelectedColor = d.get("playerSelectedColor", colors["celeste"])
        self.playerSelectedGun   = d.get("playerSelectedGun", "default")
        self.playerSelectedSkillSet = d.get("playerSelectedSkillSet", [])
        self.backgroundColor = d.get("backgroundColor", list(colors["grisoscuro"]))
        self.pets = [SnakePet.fromDict(p, player) for p in d.get("pets", [])]



class Save():
    SAVEPATH = "gamefiles/save.json"
    def __init__(self, bullets, enemies, particles, player, snake, game):
        self.bullets = bullets
        self.enemies = enemies
        self.particles = particles
        self.player = player
        self.snake = snake
        self.gameplayManager = game
        self.icon = pygame.Surface((250,75))
        # Default icon
        # self.icon.fill((0,0,0,128))
        
        try:
            with open(Save.SAVEPATH, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            # archivo no existe: creo un surface de ejemplo
            self.icon = pygame.Surface((250,75), pygame.SRCALPHA)
            self.icon.fill((255,0,0,128))  # semitransparente
            return

        # paso inverso: Base64 → bytes PNG → PIL → raw → pygame.Surface
        img_bytes = base64.b64decode(data["icon"])
        buffer = io.BytesIO(img_bytes)
        pil_img = Image.open(buffer).convert("RGBA")
        raw_str = pil_img.tobytes()
        size = pil_img.size  # (width, height)
        # reconvierto a Surface:
        self.icon = pygame.image.fromstring(raw_str, size, "RGBA")

    def toDict(self):
        # primero vuelco el Surface a raw RGBA bytes
        raw_str = pygame.image.tostring(self.icon, "RGBA")
        size = self.icon.get_size()
        # genero un objeto PIL Image desde esos bytes
        pil_img = Image.frombytes("RGBA", size, raw_str)
        # guardo como PNG en un buffer
        buffer = io.BytesIO()
        pil_img.save(buffer, format="PNG")
        png_bytes = buffer.getvalue()
        # codifico a Base64 para JSON
        img_str = base64.b64encode(png_bytes).decode("utf-8")

        return {
            "bullets":[b.toDict() for b in self.bullets],
            "enemies":[e.toDict() for e in self.enemies],
            "particles":[p.toDict() for p in self.particles],
            "player":self.player.toDict(),
            "snake":self.snake.toDict(),
            "game":self.gameplayManager.toDict(),
            "icon":img_str,
            "version":1, # for future migrations
        }
    
    def save(self, path:str = None):
        self.icon = pygame.transform.scale(screen, (250,75))

        path = path or Save.SAVEPATH
        with open(path, "w") as f:
            json.dump(self.toDict(), f, indent=2)
            
    @classmethod
    def load(cls, path:str=None):
        path = path or cls.SAVEPATH
        data, fail = load_json(path, "save copy.json")

        bullets = [Bullet.fromDict(bd) for bd in data["bullets"]]
        enemies = [Enemy.fromDict(ed) for ed in data["enemies"]]
        particles = [Particle.fromDict(pd) for pd in data["particles"]]
        player = Player.fromDict(data["player"])
        player.updateColor(game.playerSelectedColor)
        snake = SnakeBoss.fromDict(data["snake"])
        gm = GameplayManager.fromDict(data["game"])
        # copy settings
        gm.language = game.language
        gm.bigScale = game.bigScale
        gm.fullscreen = game.fullscreen
        gm.musicToggle = game.musicToggle
        gm.shakeToggle = game.shakeToggle
        gm.playerSelectedColor = game.playerSelectedColor
        gm.playerSelectedSkillSet = game.playerSelectedSkillSet
        gm.playerSelectedGun = game.playerSelectedGun
        gm.backgroundColor = game.backgroundColor
        gm.coins = game.coins
        gm.pets = game.pets
        gm.updateMenu()

        if fail:
            p = Particle("text", (ScrWidth//2,ScrHeight//2),colors["gris"], text=f'{"Failed to load save :(" if game.language == "EN" else "No se pudo cargar la partida :("}')
            particles.append(p)


        return cls(bullets,enemies,particles,player,snake,gm)



game:GameplayManager = GameplayManager(loadSettings=True)
load_json("gamefiles/save.json", "save copy.json") # Check for file corruption
save = Save(bullets, enemies, particles, player, snake, game)
#save.save()

def loadSave(save:Save):
    """Load game state from save file"""
    global bullets, enemies, particles, player, snake, game
    save = Save.load("gamefiles/save.json")
    bullets, enemies, particles, player, snake, game = (
        save.bullets, save.enemies, save.particles, 
        save.player, save.snake, save.gameplayManager
    )

def explosion(pos: pygame.Vector2, radius: int, damagePlayer: bool, damage: int, color: tuple):
    game.explosions.append([pos,radius,damagePlayer,damage,color])

@njit
def apply_explosion_damage(positions_x, positions_y, health_array,
                           center_x, center_y,
                           base_damage, explosion_radius):
    count       = positions_x.shape[0]
    radius_sq   = explosion_radius * explosion_radius
    for i in range(count):
        dx = positions_x[i] - center_x
        dy = positions_y[i] - center_y
        dist_sq = dx*dx + dy*dy
        if dist_sq <= radius_sq:
            # dist     = dist_sq ** 0.5
            # linear falloff
            # dmg      = base_damage * (1.0 - dist/explosion_radius)
            new_h    = health_array[i] - base_damage
            # clamp to zero
            health_array[i] = new_h if new_h > 0.0 else 0.0


def spawnEnemies(rate=1, difficulty=1):
    """:param rate: chance un % to spawn enemy per tick
        :param difficulty: int 1 to 6 to add an enemy type"""
    if random.randint(1,100) <= rate:
        enemySpawnright = [-50, random.randint(0,ScrHeight)]
        enemySpawnleft = [ScrWidth+50, random.randint(0,ScrHeight)]
        enemySpawntop = [random.randint(0,ScrWidth),-50]
        enemySpawnbott = [random.randint(0,ScrWidth), ScrHeight+50]

        choice = random.choice([enemySpawnright,enemySpawnleft,enemySpawntop,enemySpawnbott])
        match difficulty:
            case 1:
                enemies.append(Enemy(random.choice(["normie"]),choice)) # choose to spawn a random enemie up to the diff
            
            case 2: 
                enemies.append(Enemy(random.choice(["normie","trickster"]),choice))
            
            case 3:
                enemies.append(Enemy(random.choice(["normie", "trickster", "speedster"]),choice))
            
            case 4:
                if random.randint(1,100) == 1:
                    enemies.append(Enemy("jugg",choice))
                else:
                    enemies.append(Enemy(random.choice(["normie", "trickster", "speedster"]),choice))
            
            case 5:
                if random.randint(1,100) == 1:
                    enemies.append(Enemy("jugg",choice))
                else:
                    enemies.append(Enemy(random.choice(["trickster", "speedster","hive","hive", "hive"]),choice))
            
            case 6:
                if random.randint(1,100) == 1:
                    enemies.append(Enemy("jugg",choice))
                else:
                    enemies.append(Enemy(random.choice(["normie", "trickster", "speedster", "hive","kami", "kami"]),choice))
            
            case 7:
                if random.randint(1,100) == 1:
                    enemies.append(Enemy("jugg",choice))
                else: 
                    enemies.append(Enemy(random.choice(["trickster", "hive", "kami","quantum", "quantum"]),choice))

            case 8:
                if random.randint(1,100) == 1:
                    enemies.append(Enemy("jugg",choice))
                else: 
                    enemies.append(Enemy(random.choice(["speedster","speedster", "hive", "kami", "kami", "quantum"]),choice))
            case 9:
                if random.randint(1,100) == 1:
                    enemies.append(Enemy("jugg",choice))
                else: 
                    enemies.append(Enemy(random.choice(["speedster", "hive", "kami", "quantum", "slime" ,"slime"]),choice))
            case 10:
                if random.randint(1,100) == 1:
                    enemies.append(Enemy("jugg",choice))
                else: 
                    enemies.append(Enemy(random.choice(["trickster", "speedster", "hive", "kami","spike", "spike"]),choice))
            case 11:
                if random.randint(1,100) == 1:
                    enemies.append(Enemy("jugg",choice))
                else: 
                    enemies.append(Enemy(random.choice(["trickster", "hive", "kami","spike", "guardian", "guardian"]),choice))


            case _:
                enemy = None
                if random.randint(1,100) <= 1:
                    enemy = Enemy("jugg", choice)
                    enemy.health = max(enemy.health, difficulty*10)
                else:
                    enemy = Enemy(random.choice(game.enemiesToSpawn),choice)
                    enemy.health = max(enemy.health, enemy.health*difficulty//12)
                    enemy.damage = max(enemy.damage, enemy.damage*difficulty//12) # difficulty goes up every two rounds
                    if enemy.type in ["normie","speedster","jugg", "kami"]: # update raduis for custom hp
                        enemy.radius = enemy.health * 6
                        enemy.collisionRadius = enemy.radius
                enemy.speed = max(enemy.speed, enemy.speed*difficulty/12)
                enemies.append(enemy)

        # sort enemies by draw priority
        enemies.sort(key=lambda e: e.drawPriority)
        return True
    return False


waveProgressBar:LoadBar = LoadBar((ScrWidth//2,50),0,1,colors["bordo"],colors["gris"],pixelLength=1000)
playerHealthbar:LoadBar = LoadBar((ScrWidth//2,75),0,50,player.color,colors["gris"],pixelLength=250)
playerUltBar:LoadBar = LoadBar((ScrWidth//2,100),0,50,fillColor=colors["blanco"],borderColor=colors["gris"],pixelLength=250)

waveNumDisplay = SMALLESTFONT.render("Wave 0",True,colors["blanco"])
waveNumDisplayRect = waveNumDisplay.get_rect()

ultReadyDisplay = SMALLESTFONT.render(f"{'ULT ready!' if game.language == 'EN' else 'Ulti lista!'}",True,colors["blanco"])
ultReadyDisplayRect = ultReadyDisplay.get_rect()

skillsDrawn = 0

def resetUI():
    global waveProgressBar, playerHealthbar, playerUltBar, waveNumDisplay, waveNumDisplayRect, ultReadyDisplay, ultReadyDisplayRect, skillsDrawn

    waveProgressBar = LoadBar((ScrWidth//2,50),0,1,colors["bordo"],colors["gris"],pixelLength=8*ScrWidth//10)
    playerHealthbar = LoadBar((ScrWidth//2,75),0,50,player.color,colors["gris"],pixelLength=2*ScrWidth//10)
    playerUltBar = LoadBar((ScrWidth//2,100),0,50,fillColor=colors["blanco"],borderColor=colors["gris"],pixelLength=2*ScrWidth//10)

    waveNumDisplay = SMALLESTFONT.render("Wave 0",True,colors["blanco"])
    waveNumDisplayRect = waveNumDisplay.get_rect()

    ultReadyDisplay = SMALLESTFONT.render(f"{'ULT ready!' if game.language == 'EN' else 'Ulti lista!'}",True,colors["blanco"])
    ultReadyDisplayRect = ultReadyDisplay.get_rect()

    skillsDrawn = 0

def drawUI(dest:pygame.Surface,player:Player,gpman:GameplayManager):
    global waveNumDisplay, waveNumDisplayRect, skillsDrawn
    # PLAYER STATS
    # wave number
    if gpman.waveWaitTimer > 0:
        if gpman.language == "EN":
            waveNumDisplay = SMALLESTFONT.render(f"Wave {gpman.waveNumber}",True,colors["blanco"])
        else:
            waveNumDisplay = SMALLESTFONT.render(f"Oleada {gpman.waveNumber}",True,colors["blanco"])

        waveNumDisplayRect = waveNumDisplay.get_rect()


    # COIN DISPLAY
    coins = SMALLFONT.render(str(gpman.coins), True, colors["blanco"])
    surfaces["guiSurf"]["surface"].fill((0,0,0,0), coins.get_rect(topleft=(60,15)))

    pygame.draw.rect(surfaces["guiSurf"]["surface"], colors["amarillo"], (25,25,25,25), border_radius=5)
    surfaces["guiSurf"]["surface"].blit(coins, (60,15))

    # wave
    newProgress = player.kills - gpman.totalProgress
    if gpman.gameplayStage != "endlessMode":
        if waveProgressBar.progress != newProgress or waveProgressBar.end != gpman.waveEnd:
            surfaces["guiSurf"]["surface"].fill((0,0,0,0),(waveProgressBar.rect))
            waveProgressBar.progress = newProgress
            waveProgressBar.end = gpman.waveEnd
            waveProgressBar.draw(surfaces["guiSurf"]["surface"])
    # kills
    if gpman.gameplayStage == "endlessMode" and gpman.endlessChoiceAmmount == 0:
        killsDisp = SMALLESTFONT.render(f'Kills: {player.kills}', True, colors["blanco"])
        surfaces["guiSurf"]["surface"].fill((0,0,0,0), killsDisp.get_rect(center=(ScrWidth//2, 50)))
        surfaces["guiSurf"]["surface"].blit(killsDisp, killsDisp.get_rect(center=(ScrWidth//2, 50)))



    # hp
    if playerHealthbar.progress != player.health or playerHealthbar.fillColor != player.color:
        surfaces["guiSurf"]["surface"].fill((0,0,0,0),(playerHealthbar.rect))
        playerHealthbar.progress = player.health
        playerHealthbar.fillColor = player.color

        playerHealthbar.draw(surfaces["guiSurf"]["surface"])

    # ult
    if playerUltBar.progress != player.ultPoints:
        surfaces["guiSurf"]["surface"].fill((0,0,0,0),(playerUltBar.rect))
        playerUltBar.progress = player.ultPoints  
        playerUltBar.draw(surfaces["guiSurf"]["surface"])

        # ult ready
        if player.ultPoints == 50:
            surfaces["guiSurf"]["surface"].blit(ultReadyDisplay, ((ScrWidth//2 - ultReadyDisplayRect.width//2, 120)))
        elif player.ultPoints == 0:
            surfaces["guiSurf"]["surface"].fill((0,0,0,0),(ScrWidth//2 - ultReadyDisplayRect.width//2, 120, ultReadyDisplayRect.width, ultReadyDisplayRect.height))

    # skil icons
    if len(player.skillSet) != skillsDrawn:
        surfaces["guiSurf"]["surface"].fill((0,0,0,0),(0,ScrHeight-125,ScrWidth,50))
        skillsDrawn = len(player.skillSet)

    drawSkillIcons(player.skillSet)

    if gpman.gameplayStage != "endlessMode":
        dest.blit(waveNumDisplay, (ScrWidth//2 - waveNumDisplayRect.width//2, 10))
    dest.blit(surfaces["guiSurf"]["surface"],(0,0))


gunUpgradeButton = userInterface.Button(ScrWidth//2 - 200,ScrHeight//2,(10,10,10,100),colors["gris"],"Gun Upgrade: BurstShot",SMALLESTESTFONT,size=(110,100),clickable=True,square=True,wrap=True)
skillUpgradeButton = userInterface.Button(ScrWidth//2 + 200,ScrHeight//2,(10,10,10,100),colors["gris"],"Skill Upgrade: Shield",SMALLESTESTFONT,size=(110,100),clickable=True,square=True,wrap=True)
rndmGun = random.choice(list(guns.keys()))
rndmSk = random.choice(list(skills.keys()))
def waveRewards(gm:GameplayManager,player:Player):
    global gunUpgradeButton, skillUpgradeButton, rndmGun, rndmSk
    def dispReward(gReward:str,sReward:str):
        global gunUpgradeButton, skillUpgradeButton
        
        # draw rewards
        if gm.waveNumber != 0:

            gunUpgradeButton.move(ScrWidth//2 - 200,ScrHeight//2, textdisplay=f'{ "Gun Upgrade: " if gm.language == "EN" else "Mejora de Arma: " }{ guns[gReward][gm.language] }', resize=False)
            skillUpgradeButton.move(ScrWidth//2 + 200,ScrHeight//2, textdisplay=f'{"Skill Upgrade: " if gm.language == "EN" else "Mejora de Habilidad: "}{skills[sReward][gm.language]}', resize=False)
            
            skillUpgradeButton.draw(surfaces["guiSurf"]["surface"],screen)
            gunUpgradeButton.draw(surfaces["guiSurf"]["surface"],screen)

        # choose pibe
        if gunUpgradeButton.clicked(player.crosshairPos[0],player.crosshairPos[1],player.mouseClick[0],screen,multiclick=True):
            surfaces["guiSurf"]["surface"].fill((0,0,0,0), skillUpgradeButton.buttonRect)
            surfaces["guiSurf"]["surface"].fill((0,0,0,0), gunUpgradeButton.buttonRect)

            player.gun = gReward # set reward 
            gm.nextWaveStart = True # start next wave

        if skillUpgradeButton.clicked(player.crosshairPos[0],player.crosshairPos[1],player.mouseClick[0],screen,multiclick=True):
            surfaces["guiSurf"]["surface"].fill((0,0,0,0), skillUpgradeButton.buttonRect)
            surfaces["guiSurf"]["surface"].fill((0,0,0,0), gunUpgradeButton.buttonRect)

            player.skillSet.append(Skill(sReward, player)) #set reward 
            gm.nextWaveStart = True # start next wave
    

    match gm.waveNumber:
        case 0:
            if gm.language == "EN":
                gunUpgradeButton = userInterface.Button(ScrWidth//2 - 200,ScrHeight//2,(10,10,10,100),colors["gris"],"Gun Upgrade: BurstShot",SMALLESTESTFONT,size=(110,100),clickable=True,square=True,wrap=True)
                skillUpgradeButton = userInterface.Button(ScrWidth//2 + 200,ScrHeight//2,(10,10,10,100),colors["gris"],"Skill Upgrade: Shield",SMALLESTESTFONT,size=(110,100),clickable=True,square=True,wrap=True)
            else: 
                gunUpgradeButton = userInterface.Button(ScrWidth//2 - 200,ScrHeight//2,(10,10,10,100),colors["gris"],"Mejora Arma: BurstShot",SMALLESTESTFONT,size=(110,100),clickable=True,square=True,wrap=True)
                skillUpgradeButton = userInterface.Button(ScrWidth//2 + 200,ScrHeight//2,(10,10,10,100),colors["gris"],"Mejora Habilidad: Escudo",SMALLESTESTFONT,size=(110,100),clickable=True,square=True,wrap=True)

        case 2:
                dispReward("burst","shield")
        
        case 5:
                dispReward("shotgun", "dash")

        case 8:
                dispReward("sniper", "grenade")
        
        case 11:
                dispReward("auto", "decoy")

        case 14:
                dispReward("double", "swap")
        
        case 17:
            dispReward("fan", "implosion")

        case _:
            if gm.waveNumber > 18 and gm.waveNumber%3 == 0:
                dispReward(rndmGun, rndmSk)
            else:
                if gm.waveNumber > 18:
                    rndmGun = random.choice(list(guns.keys()))
                    rndmSk = random.choice(list(skills.keys()))
                
                particles.append(Particle("text", (ScrWidth//2,ScrHeight//2-100), colors["gris"], text=f"'{random.choice(messagesEn) if gm.language == 'EN' else random.choice(messagesEs)}'", font=SMALLFONT,speed=0.01, duration=5))

                gm.nextWaveStart = True


# endless mode buttons
choicesSk:list[list[userInterface.Button, str]] = []
for s in list(skills.keys()):
    choicesSk.append([userInterface.Button(ScrWidth//2 - 100,ScrHeight//2,(10,10,10,100),colors["gris"],f'{"Skill" if game.language == "EN" else "Habilidad"}: {skills[s][game.language]}',SMALLESTESTFONT,size=(110,110),clickable=True,square=True,wrap=True), s])
choicesGn:list[list[userInterface.Button, str]] = []
for g in list(guns.keys()):
    choicesGn.append([userInterface.Button(ScrWidth//2 + 100,ScrHeight//2,(10,10,10,100),colors["gris"],f'{"Gun" if game.language == "EN" else "Arma"}: {guns[g][game.language]}',SMALLESTESTFONT,size=(110,110),clickable=True,square=True,wrap=True), g])

readyButton = userInterface.Button(ScrWidth//2,ScrHeight-100,(10,10,10,100),colors["gris"],f'{"Im Ready" if game.language == "EN" else "Estoy Listo"}',BIGFONT,size=(110,220),clickable=True,wrap=True)
choicesDisp = userInterface.Button(ScrWidth//2,100,(10,10,10,100),colors["gris"],f'{"Skills Remaining: " if game.language == "EN" else "Habilidades Restantes: "} {game.endlessChoiceAmmount}',SMALLFONT,size=(110,220),wrap=True)

def alignChoices():
    global choicesGn, choicesSk, readyButton, choicesDisp
    for i,b in enumerate(choicesSk):
        b[0].move(ScrWidth//2-110*(i-(len(choicesSk)-1)/2),ScrHeight//2-100,f'{"Skill" if game.language == "EN" else "Habilidad"}: {skills[b[1]][game.language]}',resize=False,place=True)
    
    for j,b in enumerate(choicesGn):
        b[0].move(ScrWidth//2-110*(j-(len(choicesGn)-1)/2),ScrHeight//2+100, f'{"Gun" if game.language == "EN" else "Arma"}: {guns[b[1]][game.language]}',resize=False,place=True)
    
    readyButton = userInterface.Button(ScrWidth//2,ScrHeight-100,(10,10,10,100),colors["gris"],f'{"Im Ready" if game.language == "EN" else "Estoy Listo"}',SMALLFONT,size=(220,110),clickable=True,wrap=True)
    choicesDisp = userInterface.Button(ScrWidth//2,100,(10,10,10,100),colors["gris"],f'{"Skills Remaining: " if game.language == "EN" else "Habilidades Restantes: "} {game.endlessChoiceAmmount}',SMALLFONT,size=(220,110),wrap=True)
alignChoices()

def endlessChoices(mousepos, mouseclk, gm = game, choices = 10):

    surfaces["guiSurf"]["surface"].fill((0,0,0,0))
    choicesDisp.move(choicesDisp.x, choicesDisp.y,textdisplay=f'{"Skills Remaining: " if game.language == "EN" else "Habilidades Restantes: "} {game.endlessChoiceAmmount}', resize=False)
    # DRAW
    for b in choicesSk:
        b[0].draw(surfaces["guiSurf"]["surface"],screen)
        if b[0].clicked(mousepos[0],mousepos[1], mouseclk[0], screen,True):
            player.skillSet.append(Skill(b[1], player))
            choices -= 1
    
    for b in choicesGn:
        b[0].draw(surfaces["guiSurf"]["surface"],screen)
        if b[0].clicked(mousepos[0],mousepos[1], mouseclk[0], screen,True):
            player.gun = b[1]

    choicesDisp.draw(surfaces["guiSurf"]["surface"],screen)
    readyButton.draw(surfaces["guiSurf"]["surface"],screen)
    if readyButton.clicked(mousepos[0],mousepos[1], mouseclk[0], screen,True):
        choices = 0

    #screen.blit(surfaces["guiSurf"]["surface"],(0,0))

    return choices



fps = SMALLFONT.render("FPS: ", True, colors["blanco"]) 

scrollingFog = None
bossFog = None

scrollingBackground = perlin.PerlinScroller(356,200,1600,900,list(game.backgroundColor), False)

particlesLock = threading.Lock()
def partFunc():
    global particles, updateParticles, scrollingBackground, scrollingFog
    clock = pygame.time.Clock()
    scrollingFog = perlin.PerlinScroller(int(250*0.7),int(100*0.7),1600,900,list(colors["gris"]),True, 1, 200)
    fogType = game.gameplayStage
    while True:
        with particlesLock:
            dt = clock.tick(60) / 1000.0 # 60 desired fps
            surfaces["particleBuffer"]["surface"].fill((0,0,0,1))
            
            if fogType != game.gameplayStage:
                scrollingFog.change_base_color(colors["rojo"] if game.gameplayStage == "bossFight" else colors["gris"])
                fogType = game.gameplayStage

            # particles
            for particle in particles:
                if updateParticles:
                    particle.update()
                if particle.type != "text":
                    particle.draw(surfaces["particleBuffer"]["surface"])

            #fog
            if game.fogToggle:
                scrollingFog.scroll(surfaces["particleBuffer"]["surface"], game.paused, 2, dt)
                
            # texts
            for p in particles:
                if p.type == "text":
                    p.draw(surfaces["particleBuffer"]["surface"])
            
            surfaces["particles"]["surface"] = surfaces["particleBuffer"]["surface"].copy()
            
            particles = [particle for particle in particles if particle.radius > 0]
        time.sleep(0.02)

# Create and start the particle thread
updateParticles = True
particleThread = threading.Thread(target=partFunc)
particleThread.daemon = True  # This allows the particle thread to exit when the main program exits
particleThread.start()



# MUSIC

# Music end event
MUSIC_END = pygame.USEREVENT + 1
pygame.mixer.music.set_endevent(MUSIC_END)
defaultMusicVolume = 0.05
pygame.mixer.music.set_volume(defaultMusicVolume)

playlistCopy = random.sample(playlist, len(playlist))
def playMusic(nextTrack = ""):
    global playlistCopy
    if game.musicToggle:
        if playlistCopy:
            nextTrack = playlistCopy.pop()
            pygame.mixer.music.load(nextTrack)
            pygame.mixer.music.play(fade_ms=3000)
        else:
            # reshufle
            playlistCopy = random.sample(playlist, len(playlist))
            playMusic()

playMusic()


# MAIN LOOP
clock = pygame.time.Clock()
running = True
while running:
    dt = clock.tick(60) / 1000.0 # 60 desired fps, same movement while low fps
    currentTime = pygame.time.get_ticks()

    #scrollingbg.scrollingbg(screen,game.paused,dt)
    if scrollingBackground != None:
        scrollingBackground.scroll(screen,game.paused,0.5,dt=dt)
    else:
        screen.fill((0,0,0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game.saveSettings()
            running = False

        if event.type == MUSIC_END:
            playMusic()

        if event.type == KEYDOWN:
            if event.key == K_F11:
                game.fullscreen = not game.fullscreen
                game.menuButtons["fullscrtoggle"] = userInterface.Button(ScrWidth - 150, ScrHeight - 190, (0,255,255,10), colors["celesteOpaco"], f"{'Full Screen' if game.language == 'EN' else 'Pant. Completa'}: {'on' if game.fullscreen else 'off'}", SMALLESTFONT, colors["blanco"],size=(250,50), clickable=True, spacing=50)
                if game.fullscreen:
                    scr = pygame.display.set_mode(monitor_size, pygame.FULLSCREEN)
            
                else:
                    scr = pygame.display.set_mode((ScrWidth,ScrHeight))
                

        player.getInputs("push", event)

    game.run()


    
    # display fps
    
    #fps = SMALLESTFONT.render(f"FPS: {round(1/dt)} | Particles: {len(particles)}",True, colors["blanco"])
    #screen.blit(fps,(0,0))

    #size = scr.get_size()
    #scaledscr = pygame.transform.smoothscale(screen,size)
    scr.blit(screen,game.scrBlitPos)

    pygame.display.update()