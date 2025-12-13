import pygame
from pygame.locals import *
import numpy as np
from perlin_noise import PerlinNoise
import random

class PerlinScroller:
    def __init__(self, width=356, height=200, display_width=1600, display_height=900, 
                 base_color=(15, 15, 15), use_transparency=True, min_alpha=0, max_alpha=230):
        pygame.init()
        
        # Screen dimensions
        self.width = width
        self.height = height
        self.display_width = display_width
        self.display_height = display_height
        
        # Transparency settings
        self.use_transparency = use_transparency
        self.min_alpha = min_alpha
        self.max_alpha = max_alpha
        
        # Scroll positions
        self.scr1pos = 0
        self.scr2pos = display_width
        
        # Create surfaces with or without alpha channel based on transparency setting
        if self.use_transparency:
            self.surf = pygame.Surface((width, height), pygame.SRCALPHA)
            self.display_surf = pygame.Surface((display_width, display_height), pygame.SRCALPHA)
        else:
            self.surf = pygame.Surface((width, height))
            self.display_surf = pygame.Surface((display_width, display_height))
        
        self.scaled_surf = None
        self.flipped_surf = None
        
        # Set color and generate noise
        self.set_base_color(base_color)
        self.noise_map = None
        self.generate_noise()
        self.render_noise()
        self.update_surfaces()
    
    def generate_noise(self):
        """Generate the perlin noise map"""
        noise = PerlinNoise(octaves=6, seed=random.randint(0, 100000))
        self.noise_map = np.array([[noise([i/self.height, j/self.width]) 
                                  for j in range(self.width)] 
                                  for i in range(self.height)])
    
    def set_base_color(self, color):
        """Set the base color and prepare colors with alpha values if needed
        
        Args:
            color: RGB or RGBA tuple. If RGBA is provided, the alpha channel is used
                  as a base alpha value for transparency.
        """
        # Extract RGB and optional alpha
        if len(color) >= 4:
            self.base_color = color[:3]
            base_alpha = color[3]
        else:
            self.base_color = color
            base_alpha = self.max_alpha if self.use_transparency else 255
        
        # Create colors (with or without alpha)
        self.colors = []
        for i in range(9):
            # Increase color intensity slightly with each level
            r = min(255, self.base_color[0] + i )
            g = min(255, self.base_color[1] + i )
            b = min(255, self.base_color[2] + i )
            
            if self.use_transparency:
                # Calculate alpha based on level (0-8)
                # Lowest level has min_alpha, highest level has max_alpha
                alpha_range = self.max_alpha - self.min_alpha
                alpha = int(self.min_alpha + (i / 8.0) * alpha_range)
                # Apply base alpha as a scaling factor (percentage)
                alpha = int(alpha * (base_alpha / 255))
                self.colors.append((r, g, b, alpha))
            else:
                self.colors.append((r, g, b))
    
    def render_noise(self):
        """Render the noise map to the surface"""
        # Clear the surface 
        if self.use_transparency:
            self.surf.fill((0, 0, 0, 0))
        else:
            self.surf.fill((0, 0, 0))
        
        # Threshold values for each density level
        thresholds = [0.6, 0.2, 0.09, 0.009, 0.002, -0.06, -0.02, -0.1, -0.8]
        
        if self.use_transparency:
            # Draw using set_at for transparency support
            for i, row in enumerate(self.noise_map):
                for j, value in enumerate(row):
                    # Skip if value is below lowest threshold AND min_alpha is 0 (optimization)
                    if value < thresholds[-1] and self.min_alpha == 0:
                        continue
                        
                    # Find the appropriate color index
                    color_idx = next((idx for idx, thresh in enumerate(thresholds) if value >= thresh), 8)
                    
                    # Draw a single pixel with the appropriate color and alpha
                    self.surf.set_at((j, i), self.colors[color_idx])
        else:
            # Use faster PixelArray for non-transparent mode
            pixel_array = pygame.PixelArray(self.surf)
            
            for i, row in enumerate(self.noise_map):
                for j, value in enumerate(row):
                    # Find the appropriate color index
                    color_idx = next((idx for idx, thresh in enumerate(thresholds) if value >= thresh), 8)
                    pixel_array[j, i] = self.colors[color_idx]
            
            # Release the pixel array
            pixel_array.close()
    
    def update_surfaces(self):
        """Update scaled and flipped surfaces"""
        if self.use_transparency:
            self.scaled_surf = pygame.transform.scale(self.surf, (self.display_width, self.display_height)).convert_alpha()
            flipped = pygame.transform.flip(self.surf, True, False)
            self.flipped_surf = pygame.transform.scale(flipped, (self.display_width, self.display_height)).convert_alpha()
        else:
            self.scaled_surf = pygame.transform.scale(self.surf, (self.display_width, self.display_height)).convert()
            flipped = pygame.transform.flip(self.surf, True, False)
            self.flipped_surf = pygame.transform.scale(flipped, (self.display_width, self.display_height)).convert()
    
    def change_base_color(self, color):
        """Change the color and redraw"""
        self.set_base_color(color)
        self.render_noise()
        self.update_surfaces()
        
    def set_alpha_range(self, min_alpha, max_alpha):
        """Update the alpha range and redraw (only applies when using transparency)"""
        if not self.use_transparency:
            return
            
        self.min_alpha = min_alpha
        self.max_alpha = max_alpha
        # Re-apply color to update alpha values
        self.set_base_color(self.base_color + (self.max_alpha,))
        self.render_noise()
        self.update_surfaces()
    
    def toggle_transparency(self, use_transparency):
        """Toggle transparency mode and redraw"""
        if self.use_transparency == use_transparency:
            return
            
        self.use_transparency = use_transparency
        
        # Recreate surfaces with/without alpha
        if self.use_transparency:
            self.surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA).convert_alpha()
            self.display_surf = pygame.Surface((self.display_width, self.display_height), pygame.SRCALPHA).convert_alpha()
        else:
            self.surf = pygame.Surface((self.width, self.height)).convert_alpha()
            self.display_surf = pygame.Surface((self.display_width, self.display_height)).convert_alpha()
        
        # Update colors and redraw
        self.set_base_color(self.base_color + (self.max_alpha,) if self.use_transparency else self.base_color)
        self.render_noise()
        self.update_surfaces()
    
    def scroll(self, screen:pygame.Surface, paused=False, rate=2, dt=1/60):
        """Draw scrolling effect to screen"""
        if not paused:
            # Update scroll positions
            speed = int(60 * dt)*rate
            self.scr1pos -= speed
            self.scr2pos -= speed
            
            # Reset positions when offscreen
            #print(f"1. {self.scr1pos}, 2: {self.scr2pos}")
            if -self.display_width < self.scr1pos <= 0:
                self.scr2pos = self.scr1pos+self.display_width
            elif -self.display_width < self.scr2pos <= 0:
                self.scr1pos = self.scr2pos+self.display_width


        # Clear display surface
        if self.use_transparency:
            self.display_surf.fill((0, 0, 0, 0))
        else:
            self.display_surf.fill((0, 0, 0))
        
        # Blit scaled surfaces
        self.display_surf.blit(self.scaled_surf, (self.scr1pos, 0))
        self.display_surf.blit(self.flipped_surf, (self.scr2pos, 0))
        
        # Blit to screen
        screen.blit(self.display_surf, (0, 0), special_flags=pygame.BLEND_RGB_SUB if self.use_transparency else 0)
        if self.use_transparency:
            screen.blit(self.display_surf, (0, 0))
   

# Example usage:
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1600, 900))

    scr = pygame.Surface((3840, 2160))

    pygame.display.set_caption("Perlin Fog Effect")
    clock = pygame.time.Clock()
        
    scrollingBackground = PerlinScroller(356,200,3840,2160,(5,5,5), False)
    scrollingFog = PerlinScroller(int(250*0.7),int(100*0.7),3840,2160,(30,30,32),True, 1, 200)
    
    # Create background surface for demonstration
    background = pygame.Surface((3840, 2160), pygame.SRCALPHA)
    background.fill((0, 0, 0, 0))  # Dark blue background
    
    # Create fog scroller with white fog
    # We can set custom alpha range and enable/disable transparency
    # RGBA format: (red, green, blue, base_alpha_multiplier)
    fog = PerlinScroller(
        base_color=(200, 200, 255, 200),  # White/blue fog with 200/255 alpha multiplier
        use_transparency=True,            # Enable transparency
        min_alpha=30,                     # Minimum alpha value for lowest noise
        max_alpha=180                     # Maximum alpha value for highest noise
    )
    
    running = True
    paused = True
    
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    pygame.image.save(scr, 'output.png')
                    paused = not paused
                elif event.key == K_c:
                    # Random color change example
                    new_color = (
                        random.randint(180, 255),
                        random.randint(180, 255),
                        random.randint(200, 255),
                        random.randint(150, 250)  # Random alpha multiplier
                    )
                    fog.change_base_color(new_color)
                elif event.key == K_t:
                    # Toggle transparency on/off
                    fog.toggle_transparency(not fog.use_transparency)
                    print(f"Transparency: {'ON' if fog.use_transparency else 'OFF'}")
                elif event.key == K_UP:
                    # Increase min alpha
                    fog.set_alpha_range(min(fog.min_alpha + 10, 255), fog.max_alpha)
                    print(f"Min Alpha: {fog.min_alpha}")
                elif event.key == K_DOWN:
                    # Decrease min alpha
                    fog.set_alpha_range(max(fog.min_alpha - 10, 0), fog.max_alpha)
                    print(f"Min Alpha: {fog.min_alpha}")
                elif event.key == K_RIGHT:
                    # Increase max alpha
                    fog.set_alpha_range(fog.min_alpha, min(fog.max_alpha + 10, 255))
                    print(f"Max Alpha: {fog.max_alpha}")
                elif event.key == K_LEFT:
                    # Decrease max alpha
                    fog.set_alpha_range(fog.min_alpha, max(fog.max_alpha - 10, 0))
                    print(f"Max Alpha: {fog.max_alpha}")
        
        
        # Draw fog on top with transparency (if enabled)
        scrollingBackground.scroll(scr, paused, dt=dt, rate=1)
        background.fill((0,0,0,0))
        scrollingFog.scroll(background, paused, dt=dt, rate=2)
        scr.blit(background, (0,0))
        screen.blit(scr,(0,0))
        
        pygame.display.flip()
    
    pygame.quit()