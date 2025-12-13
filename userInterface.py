import pygame
import random
import stuff

from pygame.locals import *


def textWrap(text: str, font, x: int, y: int, rect, color):
    """
    Wraps the text to fit within a given rectangle and centers each line.

    Args:
        text (str): The text to wrap.
        font: A pygame Font object.
        x (int): Horizontal center position for text.
        y (int): Vertical center position for text block.
        rect: A pygame.Rect object specifying width constraint.
        color: Text color.

    Returns:
        List of tuples: (rendered_text_surface, (x, y)) for each line.
    """
    words = text.split()
    font_height = font.size("Tg")[1]  # consistent height, regardless of content
    space_width = font.size(" ")[0]

    lines = []
    current_line = []
    current_width = 0

    for word in words:
        word_width = font.size(word)[0]
        if current_width + word_width <= rect.width:
            current_line.append(word)
            current_width += word_width + space_width
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_width = word_width + space_width

    if current_line:
        lines.append(" ".join(current_line))

    # Prepare rendered lines centered at (x, y)
    line_blits = []
    total_height = font_height * len(lines)
    start_y = y - total_height // 2

    for i, line in enumerate(lines):
        line_surface = font.render(line, True, color)
        line_width = font.size(line)[0]
        line_y = start_y + i * font_height
        line_blits.append((line_surface, (x - line_width // 2, line_y)))

    return line_blits



buttonshovering = []
class Button():
    def __init__(self, x, y, bgColor, bdrColor, text, font, textcolor=(255,255,255), size=(0,0), clickable = False, square=False, spacing=20,hovercolor=(50,50,50),disabledcolor=(0,0,0,128), placed=1, wrap=False, wasClicked = 0):
        self.x = x
        self.y = y
        self.bgColor = bgColor
        self.borderColor = bdrColor
        self.size = size # x, y | tuple
        self.text = text
        self.textColor = textcolor
        self.clickable = clickable
        self.square = square
        self.spacing = spacing
        self.textColor = textcolor
        if isinstance(font, int):
            # If font is an integer, create a Font object using the specified font size
            self.font = pygame.font.Font(stuff.fontpath, font)
            self.fontSize = font
        elif isinstance(font, pygame.font.Font):
            self.font = font
            self.fontSize = font.get_height()

        self.wasClicked = wasClicked # 0 not click | 1 being click | 2 clicked
        
        self.placed = placed #false

        self.disabledcolor = disabledcolor
        self.hovercolor = hovercolor
        
        self.buttonRect = pygame.rect.Rect(0,0,size[0],size[1])
        self.buttonRect.center = x,y

        self.textDisplay = self.font.render(text, True, textcolor)
        self.textDisplayRect = self.textDisplay.get_rect()
        self.wrap = wrap
        if self.wrap:
            self.textlines = textWrap(text,self.font,x,y,self.buttonRect, self.textColor)
        else:
            self.textlines = textWrap(text,self.font,x,y,self.textDisplayRect, self.textColor)

        
        
        if self.size == (0,0):
            self.dinamic = True
            if square:
                self.buttonRect = pygame.rect.Rect(0,0,self.textDisplayRect.width + spacing, self.textDisplayRect.width + spacing)
                self.buttonRect.center = x,y

            else: 
                self.buttonRect = pygame.rect.Rect(0,0,self.textDisplayRect.width + spacing, self.textDisplayRect.height + spacing/2)
                self.buttonRect.center = x,y
        else: 
            self.dinamic = False
            if square:  #if square with dimentions
                self.buttonRect = pygame.rect.Rect(0,0,size[0], size[0])
                self.buttonRect.center = x,y
            else:
                self.buttonRect = pygame.rect.Rect(0,0,size[0], size[1])
                self.buttonRect.center = x,y

        self.size = (self.buttonRect.width,self.buttonRect.height)

        
        self.hoverSurface = pygame.Surface((0,0))       #if CLICKALE, hoversurface
        
        self.hoverSurface = pygame.Surface((self.buttonRect.width,self.buttonRect.height), pygame.SRCALPHA)
        

    def draw(self, surface, screen):

        pygame.draw.rect(surface, self.bgColor, (self.buttonRect), border_radius=3)
        pygame.draw.rect(surface, self.borderColor, (self.buttonRect), 3, 3) # FOKIN ROUND BUTTONS?!?!?!???!?!????!??!

        for line in self.textlines:
            surface.blit(line[0], line[1])

        if self.wasClicked == 2:
            
            pygame.draw.rect(self.hoverSurface, self.disabledcolor, (0,0,self.buttonRect.width,self.buttonRect.height),border_radius=3)
            screen.blit(self.hoverSurface, (self.buttonRect.x, self.buttonRect.y))


    def clicked(self, mx, my, click, screen, multiclick=False):
        global buttonshovering
        
        #set cursor to hand
        for button in buttonshovering:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            #print(f"hay {len(buttonshovering)} botone en hoverin: {buttonshovering}")

        if self.clickable:

            #hover
            if not self.buttonRect.collidepoint(mx,my):  
                if (self.x,self.y) in buttonshovering:
                    buttonshovering.remove((self.x,self.y))
                    #set cursor to normal
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                self.wasClicked=0

            elif self.wasClicked < 2: # if hovering
                # blit hoversurface
                if self.wasClicked == 0:
                    pygame.draw.rect(self.hoverSurface, self.hovercolor, (0,0,self.buttonRect.width,self.buttonRect.height),border_radius=3) 
                    screen.blit(self.hoverSurface, (self.buttonRect.x,self.buttonRect.y), special_flags=BLEND_RGB_ADD)

                if (self.x,self.y) not in buttonshovering:
                    buttonshovering.append((self.x,self.y))


                #click logic (why tf mousebuttonup don work)
                if click:
                    self.wasClicked = 1
                    if (self.x,self.y) in buttonshovering:
                        buttonshovering.remove((self.x,self.y))
                else: 
                    if self.wasClicked == 1:
                        stuff.sounds[random.choice(["pop", "pop1", "pop2"])].play()
                        
                        self.wasClicked = 2
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)  # this for if not hoverin, set cursor to normal


        if self.wasClicked == 0:
            self.clickable = True
            return(False)
        
        elif self.wasClicked == 2: 
    
            if (self.x,self.y) in buttonshovering:
                buttonshovering.remove((self.x,self.y))

            self.clickable = False

            if multiclick:
                self.wasClicked = 0

            #else: 
            #    Button.draw(self,screen)

            return(True)


    def move(self, x, y, textdisplay="", place=False, resize=True):
            global buttonshovering

            if place:
                self.placed = 1 - self.placed

            if self.y != y or self.x != x or self.text != textdisplay:
                if (self.x,self.y) in buttonshovering:
                    buttonshovering.remove((self.x,self.y))
                
                if self.placed == 0:
                    self.x = x      #update pos
                    self.y = y
                    

                self.buttonRect.center = self.x,self.y

                self.text = textdisplay
                self.textDisplay = self.font.render(textdisplay, True, self.textColor)
                self.textDisplayRect = self.textDisplay.get_rect()

                
                if self.wrap:
                    self.textlines = textWrap(self.text,self.font,self.x,self.y,self.buttonRect, self.textColor)
                else:
                    self.textlines = textWrap(self.text,self.font,self.x,self.y,self.textDisplayRect, self.textColor)
                
                if resize:
                    if self.dinamic:       #if SQUARE
                        if self.square:
                            self.buttonRect = pygame.rect.Rect(0,0,self.textDisplayRect.width + self.spacing, self.textDisplayRect.width + self.spacing)
                            self.buttonRect.center = self.x,self.y

                        else: 
                            self.buttonRect = pygame.rect.Rect(0,0,self.textDisplayRect.width + self.spacing, self.textDisplayRect.height + self.spacing/2)
                            self.buttonRect.center = self.x,self.y
                    else: 
                        if self.square:  #if square with dimentions
                            self.buttonRect = pygame.rect.Rect(0,0,self.size[0] + self.spacing, self.size[0] + self.spacing)
                            self.buttonRect.center = self.x,self.y
                        

                self.size = (self.buttonRect.width,self.buttonRect.height)

                self.hoverSurface = pygame.Surface((0,0))       #if CLICKALE, hoversurface
                self.hoverSurface = pygame.Surface((self.buttonRect.width,self.buttonRect.height), pygame.SRCALPHA)
                    #pygame.draw.rect(self.hoverSurface, self.hovercolor, (0,0,self.buttonRect.width,self.buttonRect.height),border_radius=3)
            

    def dupe(self):
        #gracias chat ge pe te
        return {
            'x': self.x,
            'y': self.y,
            'bgColor': self.bgColor,
            'bdrColor': self.borderColor,
            'text': self.text,
            'font': self.font,
            'textcolor': self.textColor,
            'size': self.size,
            'clickable': self.clickable,
            'square': self.square,
            'spacing': self.spacing,
            'hovercolor': self.hovercolor,
            'disabledcolor': self.disabledcolor,
            'placed': self.placed,
            'wrap' : self.wrap,
            'wasClicked' : self.wasClicked,
        }





def createBuyButton(itemName, x, y, color=stuff.colors["blanco"], font=stuff.SMALLESTFONT) -> Button:
    
    return Button(
        x =x,
        y = y,
        text=itemName,
        font=font,
        textcolor=color,
        size= (200,50),
        clickable=True,
        bgColor=(0,255,255,10),
        bdrColor=stuff.colors["gris"]
    )


class StoreItem():
    def __init__(self, button:Button, itemKey:str, price:int):
        self.button = button
        self.key = itemKey
        self.price = price

coinIcon = pygame.Rect(0,0,15,15)
class Store():
    def __init__(self, scrWidth):

        self.gunsButtons = {
            "EN": {g:  createBuyButton(stuff.guns[g]["EN"], (scrWidth//5)*1, 100+80*i) for i, g in enumerate(list(stuff.guns.keys()))},
            "ES": {g:  createBuyButton(stuff.guns[g]["ES"], (scrWidth//5)*1, 100+80*i) for i, g in enumerate(list(stuff.guns.keys()))},
        }
        
        self.skillsButtons = {
            "EN": {s:  createBuyButton(stuff.skills[s]["EN"], (scrWidth//5)*2, 100+80*i) for i, s in enumerate(list(stuff.skills.keys()))},
            "ES": {s:  createBuyButton(stuff.skills[s]["ES"], (scrWidth//5)*2, 100+80*i) for i, s in enumerate(list(stuff.skills.keys()))},
        }
        
        self.playerColorButtons = {
            "EN": {pc:  createBuyButton(stuff.pPurchasableColors[pc]["EN"], (scrWidth//5)*3, 100+80*i, color=stuff.pPurchasableColors[pc]["color"], font=stuff.BIGFONT) for i, pc in enumerate(list(stuff.pPurchasableColors.keys()))},
            "ES": {pc:  createBuyButton(stuff.pPurchasableColors[pc]["ES"], (scrWidth//5)*3, 100+80*i, color=stuff.pPurchasableColors[pc]["color"], font=stuff.BIGFONT) for i, pc in enumerate(list(stuff.pPurchasableColors.keys()))},
        }
        
        self.backgroundColorButtons = {
            "EN": {bc:  createBuyButton(stuff.bgPurchasableColors[bc]["EN"], (scrWidth//5)*4, 100+80*i, color=stuff.bgPurchasableColors[bc]["color"], font=stuff.BIGFONT) for i, bc in enumerate(list(stuff.bgPurchasableColors.keys()))},
            "ES": {bc:  createBuyButton(stuff.bgPurchasableColors[bc]["ES"], (scrWidth//5)*4, 100+80*i, color=stuff.bgPurchasableColors[bc]["color"], font=stuff.BIGFONT) for i, bc in enumerate(list(stuff.bgPurchasableColors.keys()))},
        }

        self.storeSigns = {
            "EN": 
                {"guns": [stuff.BIGFONT.render("Guns", True, stuff.colors["celeste"]), (scrWidth//5)*1],
                 "skills": [stuff.BIGFONT.render("Skills", True, stuff.colors["celeste"]),(scrWidth//5)*2],
                 "pcolors": [stuff.BIGFONT.render("Player", True, stuff.colors["celeste"]), (scrWidth//5)*3],
                 "bgcolors": [stuff.BIGFONT.render("BackGround", True, stuff.colors["celeste"]), (scrWidth//5)*4],
                },
            "ES": 
                {"guns": [stuff.BIGFONT.render("Armas", True, stuff.colors["celeste"]), (scrWidth//5)*1],
                 "skills": [stuff.BIGFONT.render("Habilidades", True, stuff.colors["celeste"]), (scrWidth//5)*2],
                 "pcolors": [stuff.BIGFONT.render("Personaje", True, stuff.colors["celeste"]), (scrWidth//5)*3],
                 "bgcolors": [stuff.BIGFONT.render("Fondo", True, stuff.colors["celeste"]), (scrWidth//5)*4],
                },
        }
        
        self.storeItems = {
            "EN": 
                [StoreItem(b, k, stuff.guns[k]["price"]) for b, k in zip(self.gunsButtons["EN"].values(), self.gunsButtons["EN"].keys())] +
                [StoreItem(b, k, stuff.skills[k]["price"]) for b, k in zip(self.skillsButtons["EN"].values(), self.skillsButtons["EN"].keys())] +
                [StoreItem(b, k, stuff.pPurchasableColors[k]["price"]) for b, k in zip(self.playerColorButtons["EN"].values(), self.playerColorButtons["EN"].keys())] +
                [StoreItem(b, k, stuff.bgPurchasableColors[k]["price"]) for b, k in zip(self.backgroundColorButtons["EN"].values(), self.backgroundColorButtons["EN"].keys())],
            "ES": 
                [StoreItem(b, k, stuff.guns[k]["price"]) for b, k in zip(self.gunsButtons["ES"].values(), self.gunsButtons["ES"].keys())] +
                [StoreItem(b, k, stuff.skills[k]["price"]) for b, k in zip(self.skillsButtons["ES"].values(), self.skillsButtons["ES"].keys())] +
                [StoreItem(b, k, stuff.pPurchasableColors[k]["price"]) for b, k in zip(self.playerColorButtons["ES"].values(), self.playerColorButtons["ES"].keys())] +
                [StoreItem(b, k, stuff.bgPurchasableColors[k]["price"]) for b, k in zip(self.backgroundColorButtons["ES"].values(), self.backgroundColorButtons["ES"].keys())]    
        }
        self.language = "EN"

    def updateStoreGui(self,scrWidth, language):
        h0 = 120
        dh = 60 # 50 + gap
        self.gunsButtons = {
            "EN": {g:  createBuyButton(stuff.guns[g]["EN"], (scrWidth//5)*1, h0+dh*i) for i, g in enumerate(list(stuff.guns.keys()))},
            "ES": {g:  createBuyButton(stuff.guns[g]["ES"], (scrWidth//5)*1, h0+dh*i) for i, g in enumerate(list(stuff.guns.keys()))},
        }
        
        self.skillsButtons = {
            "EN": {s:  createBuyButton(stuff.skills[s]["EN"], (scrWidth//5)*2, h0+dh*i) for i, s in enumerate(list(stuff.skills.keys()))},
            "ES": {s:  createBuyButton(stuff.skills[s]["ES"], (scrWidth//5)*2, h0+dh*i) for i, s in enumerate(list(stuff.skills.keys()))},
        }
        
        self.playerColorButtons = {
            "EN": {pc:  createBuyButton(stuff.pPurchasableColors[pc]["EN"], (scrWidth//5)*3, h0+dh*i, color=stuff.pPurchasableColors[pc]["color"]) for i, pc in enumerate(list(stuff.pPurchasableColors.keys()))},
            "ES": {pc:  createBuyButton(stuff.pPurchasableColors[pc]["ES"], (scrWidth//5)*3, h0+dh*i, color=stuff.pPurchasableColors[pc]["color"]) for i, pc in enumerate(list(stuff.pPurchasableColors.keys()))},
        }
        
        self.backgroundColorButtons = {
            "EN": {bc:  createBuyButton(stuff.bgPurchasableColors[bc]["EN"], (scrWidth//5)*4, h0+dh*i, color=stuff.bgPurchasableColors[bc]["color"]) for i, bc in enumerate(list(stuff.bgPurchasableColors.keys()))},
            "ES": {bc:  createBuyButton(stuff.bgPurchasableColors[bc]["ES"], (scrWidth//5)*4, h0+dh*i, color=stuff.bgPurchasableColors[bc]["color"]) for i, bc in enumerate(list(stuff.bgPurchasableColors.keys()))},
        }
        
        
        self.storeSigns = {
            "EN": 
                {"guns": [stuff.BIGFONT.render("Guns", True, stuff.colors["celeste"]), (scrWidth//5)*1],
                 "skills": [stuff.BIGFONT.render("Skills", True, stuff.colors["celeste"]),(scrWidth//5)*2],
                 "pcolors": [stuff.BIGFONT.render("Player", True, stuff.colors["celeste"]), (scrWidth//5)*3],
                 "bgcolors": [stuff.BIGFONT.render("BackGround", True, stuff.colors["celeste"]), (scrWidth//5)*4],
                },
            "ES": 
                {"guns": [stuff.BIGFONT.render("Armas", True, stuff.colors["celeste"]), (scrWidth//5)*1],
                 "skills": [stuff.BIGFONT.render("Habilidades", True, stuff.colors["celeste"]), (scrWidth//5)*2],
                 "pcolors": [stuff.BIGFONT.render("Personaje", True, stuff.colors["celeste"]), (scrWidth//5)*3],
                 "bgcolors": [stuff.BIGFONT.render("Fondo", True, stuff.colors["celeste"]), (scrWidth//5)*4],
                },
        }
        


        self.storeItems = {
            "EN": 
                [StoreItem(b, k, stuff.guns[k]["price"]) for b, k in zip(self.gunsButtons["EN"].values(), self.gunsButtons["EN"].keys())] +
                [StoreItem(b, k, stuff.skills[k]["price"]) for b, k in zip(self.skillsButtons["EN"].values(), self.skillsButtons["EN"].keys())] +
                [StoreItem(b, k, stuff.pPurchasableColors[k]["price"]) for b, k in zip(self.playerColorButtons["EN"].values(), self.playerColorButtons["EN"].keys())] +
                [StoreItem(b, k, stuff.bgPurchasableColors[k]["price"]) for b, k in zip(self.backgroundColorButtons["EN"].values(), self.backgroundColorButtons["EN"].keys())],
            "ES": 
                [StoreItem(b, k, stuff.guns[k]["price"]) for b, k in zip(self.gunsButtons["ES"].values(), self.gunsButtons["ES"].keys())] +
                [StoreItem(b, k, stuff.skills[k]["price"]) for b, k in zip(self.skillsButtons["ES"].values(), self.skillsButtons["ES"].keys())] +
                [StoreItem(b, k, stuff.pPurchasableColors[k]["price"]) for b, k in zip(self.playerColorButtons["ES"].values(), self.playerColorButtons["ES"].keys())] +
                [StoreItem(b, k, stuff.bgPurchasableColors[k]["price"]) for b, k in zip(self.backgroundColorButtons["ES"].values(), self.backgroundColorButtons["ES"].keys())]    
        }

        self.language = language


    def draw(self, coins:int, dest:pygame.Surface, screen:pygame.surface):
        
        for sign in self.storeSigns[self.language].values():
            dest.blit(sign[0], sign[0].get_rect(center=(sign[1], 70)))

        for item in self.storeItems[self.language]:
            # draw button
            item.button.draw(dest, screen)
            if coins < item.price:
                disabledSurf = pygame.Surface(item.button.buttonRect.size, pygame.SRCALPHA)
                disabledSurf.fill((100,100,100))
                dest.blit(disabledSurf, disabledSurf.get_rect(center=(item.button.x,item.button.y)), special_flags=pygame.BLEND_RGB_SUB)

        for item in self.storeItems[self.language]:
            # draw price tag
            priceTag = stuff.SMALLESTESTFONT.render(f'{item.price}', True, stuff.colors["blanco"] if coins >= item.price else stuff.colors["grisclaro"])
            blitpos = priceTag.get_rect(center=(item.button.x, item.button.y+25))
            dest.blit(priceTag, (blitpos[0], blitpos[1]-5))
            # draw coin
            pygame.draw.rect(dest, stuff.colors["amarillo"], coinIcon.move(blitpos.x-20,blitpos.y-2), border_radius=2)


    def getPurchases(self, coins:int, mx,my,clk,screen:pygame.Surface) -> str:
        """Returns the key of the purchased item. Use 'if key in x.values()' for purchase acreditation. If no purchase is done, itll return an empty str"""
        for item in self.storeItems[self.language]:
            if coins >= item.price:
                if item.button.clicked(mx,my,clk,screen,True):
                    return item.key, item.price
        return "", 0
