import pygame, math
import pygame.gfxdraw


pygame.init()

def drawPoints(index:int, vector:pygame.Vector2,point:tuple[int,int]|pygame.Vector2,lenPoints:int, radiuses:list[int],list:list[tuple[int,int],tuple[int,int]]):
    
    drawPointLeft:tuple[int,int] = point+vector.rotate(90)*radiuses[index]
    drawPointRight:tuple[int,int] = point+vector.rotate(-90)*radiuses[index]

    list[index] = ((drawPointRight.x,drawPointRight.y),(drawPointLeft.x,drawPointLeft.y))
    if index == lenPoints-1:
        
        drawPointLeft:tuple[int,int] = point+vector.rotate(30)*radiuses[index]
        drawPointRight:tuple[int,int] = point+vector.rotate(-30)*radiuses[index]

        list[index+1] = ((drawPointRight.x,drawPointRight.y),(drawPointLeft.x,drawPointLeft.y))
    if index == 0:
        
        drawPointLeft:tuple[int,int] = point+vector.rotate(50)*radiuses[index]
        drawPointRight:tuple[int,int] = point+vector.rotate(-50)*radiuses[index]

        list[index] = ((drawPointRight.x,drawPointRight.y),(drawPointLeft.x,drawPointLeft.y))


class Lizard():
    def __init__(self, numberOfPoints:int = 10, pointDistance:int = 1, retractionSpeed:int = -1, walkingSpeed:float = 100,bodyScale:float=4,eyeSize:int=5, flexibility:int=160, eyeColor = (255,255,255), borderColor = (255,255,255), borderRadius = 1, bodyColor = (255,0,0), head:int = -1, fish:bool = False, finList:list[int]=[], finColor:tuple[int,int,int]|pygame.Color=()):

        self.points:list[pygame.Vector2] = [pygame.Vector2(50*i,-400) for i in range(1, numberOfPoints)]

        self.drawingPoints:list[tuple[tuple[int,int],tuple[int,int]],] = [((0,0),(0,0))]*(numberOfPoints+1)

        self.eyePoints:tuple[int,int] = [(0,0),(0,0)] 

        self.pointDistance = pointDistance

        self.retractionSpeed = retractionSpeed
        if retractionSpeed == -1:
            self.retractionSpeed = 10
        
        self.flexibility = abs(flexibility)

        self.walkingSpeed = walkingSpeed
        self.walking = False

        self.pathPoint:tuple[int,int] = (0,0)
        self.direction:pygame.Vector2 = pygame.Vector2(1,0)

        self.bodyRadiuses:int = []

        self.headSize:int = 0
        self.head:int = 0

        for i in range(numberOfPoints-1):
            self.bodyRadiuses.append((((1/numberOfPoints)*(i+0.2)*math.exp(-((i+0.2)*4/(numberOfPoints)))))*bodyScale*100)

            if head == -1:
                if i > 0 and self.bodyRadiuses[i] > self.bodyRadiuses[i-1]:
                    self.headSize = self.bodyRadiuses[i]
                    self.head = i
            
        if head != -1:
            self.head = head
            self.headSize = self.bodyRadiuses[head]
        
        self.eyeSize = eyeSize

        self.eyeColor = eyeColor
        self.borderColor = borderColor
        self.borderRadius = borderRadius
        self.bodyColor = bodyColor
        self.eyelidColor = self.eyeColor

        if fish:
            if finColor == ():
                finColor = bodyColor
        self.fish = fish

    def walkStretch(self, dt):

        # Anchor points
        for index,point in enumerate(self.points):
            if index > 0:

                vectorToPrev:pygame.Vector2 = pygame.Vector2(self.points[index-1]) - pygame.Vector2(point)
                distanceToPreviousPoint:float = vectorToPrev.length()

                maxdistance = self.bodyRadiuses[index]+self.bodyRadiuses[index-1]+self.pointDistance
                mindistance = self.bodyRadiuses[index-1]+self.pointDistance


                normalVector:pygame.Vector2 = (vectorToPrev/distanceToPreviousPoint) if distanceToPreviousPoint != 0 else vectorToPrev
                
                #drawPoints(index,-normalVector,point,len(self.points),self.bodyRadiuses,self.drawingPoints)
                
                if index != len(self.points)-1:
                    nextv =  pygame.Vector2(self.points[index+1]) - pygame.Vector2(point)
                    nextDistance = nextv.length()
                    nextv = nextv/nextDistance if nextDistance != 0 else nextv
                    angle = nextv.angle_to(vectorToPrev)

                    angle = angle % 360
                    
                    if angle < self.flexibility:
                        self.points[index+1] = point + nextv.rotate(angle-self.flexibility)*nextDistance
                    elif angle > 360-self.flexibility:
                        self.points[index+1] = point + nextv.rotate(angle+self.flexibility)*nextDistance
                
                # current position as a Vector2
                cur = pygame.Vector2(point)

                if distanceToPreviousPoint > maxdistance*1.1:
                    #snap if past maxdistance
                    self.points[index] = self.points[index-1] - normalVector*maxdistance 
                else:
                    # anywhere at or below max: gently pull back toward mindistance
                    target = self.points[index-1] - normalVector * mindistance
                    self.points[index] += (target - cur) * self.retractionSpeed * dt
                
                
                
                if index == self.head:
                    eyePointRight:tuple[int,int] = point+normalVector.rotate(90)*self.headSize/2
                    eyePointLeft:tuple[int,int] = point+normalVector.rotate(-90)*self.headSize/2

                    self.eyePoints = [(eyePointRight.x,eyePointRight.y),(eyePointLeft.x,eyePointLeft.y)]


            else: 
                self.walking = False
                # Move head
                toPathPoint:pygame.Vector2 = pygame.Vector2(self.pathPoint) - point

                vectToNext = pygame.Vector2(self.points[index+1]) - pygame.Vector2(point)
                angle = toPathPoint.angle_to(vectToNext) % 360 

                if angle < self.flexibility:
                    toPathPoint = toPathPoint.rotate(angle-self.flexibility)
                elif angle > 360-self.flexibility:
                    toPathPoint = toPathPoint.rotate(angle+self.flexibility)

                self.direction = toPathPoint.normalize() if self.direction.length_squared() != 0 else self.direction

                if toPathPoint.length() > 50:
                    self.walking = True
                    self.points[index] += self.direction * self.walkingSpeed * math.sqrt(toPathPoint.length())/20 * dt

                if index == self.head:
                    eyePointRight:tuple[int,int] = point+self.direction.rotate(45)*self.headSize/2
                    eyePointLeft:tuple[int,int] = point+self.direction.rotate(-45)*self.headSize/2

                    self.eyePoints = [(eyePointRight.x,eyePointRight.y),(eyePointLeft.x,eyePointLeft.y)]



                #drawPoints(index,vectToNext.normalize(),point,len(self.points),self.bodyRadiuses,self.drawingPoints)

            if index == self.head and index != 0:
                # Load eyepos
                vectToPrev = (pygame.Vector2(self.points[index-1]) - pygame.Vector2(point))
                normalVector:pygame.Vector2 = vectToPrev.normalize()
                eyePointRight:tuple[int,int] = point+normalVector.rotate(45)*self.headSize/2
                eyePointLeft:tuple[int,int] = point+normalVector.rotate(-45)*self.headSize/2

                self.eyePoints = [(eyePointRight.x,eyePointRight.y),(eyePointLeft.x,eyePointLeft.y)]

    def walk(self, dt:float):
        for index, point in enumerate(self.points):
            if index > 0:

                # Move body
                direction = pygame.Vector2(point) - pygame.Vector2(self.points[index-1])
                normalVector = direction.normalize()
                self.points[index] = pygame.Vector2(self.points[index-1]) + normalVector * (self.pointDistance*self.bodyRadiuses[index])

                #drawPoints(index,normalVector,point,len(self.points),self.bodyRadiuses,self.drawingPoints)

                if index != len(self.points)-1:
                    prev = pygame.Vector2(point) - pygame.Vector2(self.points[index+1])
                    angle = prev.angle_to(direction)

                    angle = angle % 360

                    if self.fish:
                        for i, fin in enumerate(self.fins):
                            if index == fin.bodyPart:
                                self.fins[i].rotateFins(self.bodyRadiuses[index],point,self.points[index-1],angle)


                    if angle < self.flexibility:
                        self.points[index+1] = point + (-prev.rotate(angle-self.flexibility)).normalize()*(self.bodyRadiuses[index+1]+self.pointDistance) #bi tonto
                    elif angle > 360-self.flexibility:
                        self.points[index+1] = point + (-prev.rotate(angle+self.flexibility)).normalize()*(self.bodyRadiuses[index+1]+self.pointDistance)
            
           
            else: 
                self.walking = False
                # Move head
                toPathPoint:pygame.Vector2 = pygame.Vector2(self.pathPoint) - point

                vectToNext = pygame.Vector2(self.points[index+1]) - pygame.Vector2(point)
                angle = toPathPoint.angle_to(vectToNext) % 360 
                if angle < self.flexibility:
                    toPathPoint = toPathPoint.rotate(angle-self.flexibility)
                elif angle > 360-self.flexibility:
                    toPathPoint = toPathPoint.rotate(angle+self.flexibility)

                self.direction = toPathPoint.normalize()

                if toPathPoint.length() > 50:
                    self.walking = True
                    self.points[index] += self.direction * self.walkingSpeed * dt

                if index == self.head:
                    eyePointRight:tuple[int,int] = point+self.direction.rotate(45)*self.headSize/2
                    eyePointLeft:tuple[int,int] = point+self.direction.rotate(-45)*self.headSize/2

                    self.eyePoints = [(eyePointRight.x,eyePointRight.y),(eyePointLeft.x,eyePointLeft.y)]



                #drawPoints(index,vectToNext.normalize(),point,len(self.points),self.bodyRadiuses,self.drawingPoints)

            if index == self.head and index != 0:
                # Load eyepos
                vectToPrev = (pygame.Vector2(self.points[index-1]) - pygame.Vector2(point))
                normalVector:pygame.Vector2 = vectToPrev.normalize()
                eyePointRight:tuple[int,int] = point+normalVector.rotate(45)*self.headSize/2
                eyePointLeft:tuple[int,int] = point+normalVector.rotate(-45)*self.headSize/2

                self.eyePoints = [(eyePointRight.x,eyePointRight.y),(eyePointLeft.x,eyePointLeft.y)]

    def drawSkeleton(self,dest):
        if self.fish:
            for fin in self.fins:
                lp, rp = fin.leftFin.pos, fin.rightFin.pos

                pygame.draw.circle(dest, (255,255,255), lp, 10, 3)
                pygame.draw.circle(dest, (255,255,255), rp, 10, 3)


        for index, point in enumerate(self.points):
            if index > 0:
                pygame.draw.line(dest,(255,255,255),(point),(self.points[index-1]),5)

            pygame.draw.circle(dest,(255,255,255),point,10,3)

            pygame.draw.circle(dest,(255,255,255), self.drawingPoints[index][0], 5, 3)
            pygame.draw.circle(dest,(255,255,255), self.drawingPoints[index][1], 5, 3)

            pygame.draw.line(dest, (255,255,255), point, self.drawingPoints[index][0], 3)
            pygame.draw.line(dest, (255,255,255), point, self.drawingPoints[index][1], 3)
        

    def draw(self, dest:pygame.surface):
        if self.fish:
            for fin in self.fins:
                fin.drawFinPair(dest)

        for index,point in enumerate(self.points):
            pygame.draw.circle(dest,self.borderColor,point,self.bodyRadiuses[index]+self.borderRadius,3)
        for index,point in enumerate(self.points):
            pygame.draw.circle(dest,self.bodyColor, point,self.bodyRadiuses[index]) # REPLACE WITH PYGAME MASK (pls)


        for eye in self.eyePoints:
            pygame.draw.circle(dest,self.eyelidColor,eye+self.direction*2,self.eyeSize)
            pygame.draw.circle(dest,self.eyeColor,eye,self.eyeSize)

    def drawPoly(self, dest:pygame.surface):
        
        if self.fish:
            for fin in self.fins:
                fin.drawFinPair(dest)

        # Extract the first set of coordinates from each pair
        first_coords = [pair[0] for pair in self.drawingPoints]

        # Extract the second set of coordinates from each pair
        second_coords = [pair[1] for pair in reversed(self.drawingPoints)]

        points = first_coords + second_coords

        pygame.gfxdraw.filled_polygon(dest, points, self.bodyColor)
        pygame.gfxdraw.polygon(dest, points,self.borderColor)

        
        for eye in self.eyePoints:
            pygame.draw.circle(dest,self.eyeColor,eye,self.eyeSize)


    def to_dict(self) -> dict:
        return {
            "points":          [[x,y] for x,y in self.points],
            "eyePoints":       [[x,y] for x,y in self.eyePoints],
            "pointDistance":   self.pointDistance,
            "retractionSpeed": self.retractionSpeed,
            "flexibility":     self.flexibility,
            "walkingSpeed":    self.walkingSpeed,
            "walking":         self.walking,
            "pathPoint":       [self.pathPoint[0], self.pathPoint[1]],
            "direction":       [self.direction.x, self.direction.y],
            "bodyRadiuses":    list(self.bodyRadiuses),
            "headSize":        self.headSize,
            "head":            self.head,
            "eyeSize":         self.eyeSize,
            "eyeColor":        list(self.eyeColor),
            "eyelidColor":     list(self.eyelidColor),
            "borderColor":     list(self.borderColor),
            "borderRadius":    self.borderRadius,
            "bodyColor":       list(self.bodyColor),
            "fish":            self.fish,
            "finList":         list(getattr(self, "finList", [])),
            "finColor":        list(getattr(self, "finColor", self.bodyColor)),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Lizard":
        # build a fresh instance with minimal params
        num_pts = len(d["points"])
        liz = cls(
            numberOfPoints=num_pts,
            pointDistance=d["pointDistance"],
            retractionSpeed=d["retractionSpeed"],
            walkingSpeed=d["walkingSpeed"],
            flexibility=d["flexibility"],
            bodyScale=1,       # will be overwritten
            head=d["head"],
            eyeSize=d["eyeSize"],
            eyeColor=tuple(d["eyeColor"]),
            borderColor=tuple(d["borderColor"]),
            borderRadius=d["borderRadius"],
            bodyColor=tuple(d["bodyColor"]),
            fish=d["fish"],
            finList=d.get("finList", []),
            finColor=tuple(d.get("finColor", d["bodyColor"]))
        )

        # overwrite all dynamic fields
        liz.points           = [pygame.Vector2(pt) for pt in d["points"]]
        liz.eyePoints        = [tuple(ep) for ep in d["eyePoints"]]
        liz.walking          = d["walking"]
        liz.pathPoint        = pygame.Vector2(d["pathPoint"])
        liz.direction        = pygame.Vector2(d["direction"])
        liz.bodyRadiuses     = list(d["bodyRadiuses"])
        liz.eyelidColor      = d["eyelidColor"]
        liz.headSize         = d["headSize"]
        liz.head             = d["head"]
        return liz


lizard:Lizard = Lizard()

direction = pygame.Vector2(100,0)
clock = pygame.time.Clock()
running = True
if __name__ == "__main__":
    scr = pygame.display.set_mode((1000,700))

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        scr.fill((30,30,40))
        dt = clock.tick(60)/1000

        pressed = pygame.key.get_pressed()

        if pressed[pygame.K_1]:
            pointlist = lizard.points

            lizard = Lizard(numberOfPoints=10, 
                            pointDistance=1, 
                            retractionSpeed=20, 
                            walkingSpeed=20, 
                            bodyScale=5, 
                            eyeSize=5,
                            eyeColor=(255,255,255), 
                            flexibility=160,
                            fish=True,
                            finList=[3,6,9],
                            finColor=(125,0,0))
            

            lizard.points[:len(pointlist)] = pointlist[:len(lizard.points)]
        elif pressed[pygame.K_2]:
            pointlist = lizard.points

            lizard = Lizard(numberOfPoints=100,
                            pointDistance=1,  
                            walkingSpeed=200, 
                            bodyScale=2, 
                            eyeSize=5, 
                            flexibility=160, 
                            bodyColor=(0,0,128),
                            head=10)

            lizard.points[:len(pointlist)] = pointlist[:len(lizard.points)]


        elif pressed[pygame.K_3]:

            pointlist = lizard.points

            lizard = Lizard(numberOfPoints=100,
                            pointDistance=0.1,
                            flexibility=160)

            lizard.points[:len(pointlist)] = pointlist[:len(lizard.points)]

        if pressed[pygame.K_a]:
            direction = direction.rotate(-lizard.walkingSpeed)
        elif pressed[pygame.K_d]:
            direction = direction.rotate(lizard.walkingSpeed)

        #lizard.pathPoint = lizard.points[0] + direction
        lizard.pathPoint = pygame.mouse.get_pos()
        lizard.walkStretch(dt)
        lizard.draw(scr)
        

        if pressed[pygame.K_SPACE]:
            lizard.drawSkeleton(scr)


        pygame.display.flip()
    pygame.quit()
