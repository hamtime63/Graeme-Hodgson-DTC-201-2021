"""
Digging Game

This is my really fun game about shooting your way to the bottom,
once you reach the bottom you get as much gold and coal as you want,
that's the point of the game
"""

import math
import os

import arcade
import pyglet

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500
SCREEN_TITLE = "Digging Game - Graeme Hodgson"

# Constants used to scale our sprites from their original size
TILE_SCALING = 1
CHARACTER_SCALING = TILE_SCALING / 1.6
GOLD_SCALING = TILE_SCALING
Coal_SCALING = TILE_SCALING
SPRITE_PIXEL_SIZE = 128
GRID_PIXEL_SIZE = (SPRITE_PIXEL_SIZE * TILE_SCALING)
SPRITE_SCALING_LASER = 0.8
BULLET_SCALING = TILE_SCALING

# Movement speed of player, in pixels per frame
PLAYER_MOVEMENT_SPEED = 7
GRAVITY = 1.5

# Bullet speed
BULLET_SPEED = 10

# How many pixels to keep as a minimum margin between the character
# and the edge of the screen.
LEFT_VIEWPORT_MARGIN = 200
RIGHT_VIEWPORT_MARGIN = 200
BOTTOM_VIEWPORT_MARGIN = 150
TOP_VIEWPORT_MARGIN = 100

PLAYER_START_X = SPRITE_PIXEL_SIZE * TILE_SCALING * 4.5
PLAYER_START_Y = SPRITE_PIXEL_SIZE * TILE_SCALING * 50

# Constants used to track if the player is facing left or right
RIGHT_FACING = 0
LEFT_FACING = 1


def load_texture_pair(filename):
    """
    Load a texture pair, with the second being a mirror image.
    """
    return [
        arcade.load_texture(filename),
        arcade.load_texture(filename, flipped_horizontally=True)
    ]


class PlayerCharacter(arcade.Sprite):
    """ Player Sprite"""

    def __init__(self):
        # Set up parent class
        super().__init__()

        # Default to face-right
        self.character_face_direction = RIGHT_FACING

        # Variables that will hold sprite lists
        self.player_list = None
        self.platforms_list = None
        self.bullet_list = None

        # Used for flipping between image sequences
        self.cur_texture = 0
        self.scale = CHARACTER_SCALING

        # main_path variable
        main_path = f"images/digger"
        # main_path2 = "Sounds"

        # Load textures for idle standing
        self.idle_texture_pair = load_texture_pair(f"{main_path}_idle.png")
        self.fall_texture_pair = load_texture_pair(f"{main_path}_fall.png")

        # Load textures for walking
        self.walk_textures = []
        for i in range(8):
            texture = load_texture_pair(f"{main_path}_walk{i}.png")
            self.walk_textures.append(texture)

        # Set the initial texture
        self.texture = self.idle_texture_pair[0]

        # Hit box will be set based on the first image used. If you want to specify
        # a different hit box, you can do it like the code below.
        # self.set_hit_box([[-22, -64], [22, -64], [22, 28], [-22, 28]])
        # self.set_hit_box(self.texture.hit_box_points)

    def update_animation(self, delta_time: float = 1 / 60):

        # Figure out if we need to flip face left or right
        if self.change_x < 0 and self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0 and self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING

        # Idle animation

        if self.change_x == 0:
            self.texture = self.idle_texture_pair[self.character_face_direction]
            return

        # Walking animation
        self.cur_texture += 1
        if self.cur_texture > 7:
            self.cur_texture = 0
        self.texture = self.walk_textures[self.cur_texture][self.character_face_direction]


class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self):
        """
        Initializer for the game
        """

        # Call the parent class and set up the window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Set the path to start with this program
        self.draw_time = 0
        self.processing_time = 0
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        # Track the current state of what key is pressed
        self.left_pressed = False
        self.right_pressed = False

        # Background sound
        pyglet.media.Player()  # Might need to figure this one out.

        # These are 'lists' that keep track of our sprites. Each sprite should
        # go into a list.
        self.gold_list = None
        self.coal_list = None
        # self.background_list = None
        self.player_list = None
        self.bullet_list = None
        self.platforms_list = None

        # Separate variable that holds the player sprite
        self.player_sprite = None

        # Our 'physics' engine
        self.physics_engine = None

        # Used to keep track of our scrolling
        self.view_bottom = 0
        self.view_left = 0

        self.end_of_map = 0

        # Keep track of the score
        self.score = 0

        # Load sounds
        self.collect_gold_sound = arcade.load_sound("Sounds/gold1.wav")
        self.collect_coal_sound = arcade.load_sound("Sounds/coal.wav")
        # self.game_over = arcade.load_sound("f"{main_path}sounds/gameover1.wav")

    def setup(self):
        """ Set up the game here. Call this function to restart the game. """

        # Used to keep track of our scrolling
        self.view_bottom = 0
        self.view_left = 0

        # Keep track of the score
        self.score = 0

        # Create the Sprite lists
        self.player_list = arcade.SpriteList()
        # self.background_list = arcade.SpriteList()
        self.gold_list = arcade.SpriteList()
        self.coal_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()
        self.platforms_list = arcade.SpriteList()

        # Set up the player, specifically placing it at these coordinates.
        self.player_sprite = PlayerCharacter()
        self.player_sprite.center_x = PLAYER_START_X
        self.player_sprite.center_y = PLAYER_START_Y
        self.player_list.append(self.player_sprite)

        # --- Load in a map from the tiled editor ---

        # Name of the layer in the file that has our platforms this contains dirt block
        platforms_layer_name = 'Platforms'

        # Names of the layers that has items for picking up
        gold_layer_name = 'Gold'
        coal_layer_name = 'Coal'

        # Map name
        map_name = f"Tiled_Maps/Map2.tmx"

        # Read in the tiled map
        my_map = arcade.tilemap.read_tmx(map_name)

        # Calculate the right edge of the my_map in pixels
        self.end_of_map = my_map.map_size.width * GRID_PIXEL_SIZE

        # -- Platforms
        self.platforms_list = arcade.tilemap.process_layer(my_map,
                                                           platforms_layer_name,
                                                           TILE_SCALING,
                                                           use_spatial_hash=True)

        # -- Background objects
        # self.background_list = arcade.tilemap.process_layer(my_map, "Background", TILE_SCALING)

        # Gold
        self.gold_list = arcade.tilemap.process_layer(my_map, gold_layer_name,
                                                      TILE_SCALING,
                                                      use_spatial_hash=True)

        # Coal
        self.coal_list = arcade.tilemap.process_layer(my_map, coal_layer_name,
                                                      TILE_SCALING,
                                                      use_spatial_hash=True)

        # --- Other stuff ie the physics engine which
        # Set the background color
        # if my_map.background_color:
        #     arcade.set_background_color(my_map.background_color)

        # Create the 'physics engine'
        self.physics_engine = arcade.PhysicsEnginePlatformer(self.player_sprite,
                                                             self.platforms_list,
                                                             gravity_constant=GRAVITY,)

    def on_draw(self):
        """ Render the screen. """

        # Clear the screen to the background color
        arcade.start_render()

        # Draw our sprites
        # self.background_list.draw()
        self.platforms_list.draw()
        self.gold_list.draw()
        self.coal_list.draw()
        self.player_list.draw()
        self.bullet_list.draw()

        # Draw our score on the screen, scrolling it with the viewport
        score_text = f"Score: {self.score}"
        arcade.draw_text(score_text, 10 + self.view_left, 10 + self.view_bottom,
                         arcade.csscolor.BLACK, 18)

    def on_mouse_press(self, x, y, button, modifiers):

        """
        Called whenever the mouse button is clicked.
        """

        # Create a bullet
        bullet = arcade.Sprite("Images/laserBlue01.png", SPRITE_SCALING_LASER)

        # Position the bullet at the player's current location
        start_x = self.player_sprite.center_x  # position where the character at any point on the screen
        start_y = self.player_sprite.center_y  # We want the bullet in the top of the player
        bullet.center_x = start_x
        bullet.center_y = start_y

        # Makes bullet move
        bullet.change_y = BULLET_SPEED
        bullet.change_x = BULLET_SPEED

        # Get from the mouse the destination location for the bullet
        # IMPORTANT! If you have a scrolling screen, you will also need
        # to add in self.view_bottom and self.view_left.
        dest_x = self.view_left + x
        dest_y = self.view_bottom + y

        # Do math to calculate how to get the bullet to the destination.
        # Calculation the angle in radians between the start points
        # and end points. This is the angle the bullet will travel.
        x_diff = dest_x - start_x
        y_diff = dest_y - start_y
        angle = math.atan2(y_diff, x_diff)

        # Angle the bullet sprite so it doesn't look like it is flying
        # sideways.
        bullet.angle = math.degrees(angle)
        print(f"Bullet angle: {bullet.angle:.2f}")

        # Taking into account the angle, calculate our change_x
        # and change_y. Velocity is how fast the bullet travels.
        bullet.change_x = math.cos(angle) * BULLET_SPEED
        bullet.change_y = math.sin(angle) * BULLET_SPEED

        # Add the bullet to the appropriate lists
        self.bullet_list.append(bullet)

    """ Movement and game logic """
    def update(self, delta_time):

        # Call update on all sprites
        self.platforms_list.update()
        self.bullet_list.update()
        self.player_list.update()

        # Loop through each bullet
        for bullet in self.bullet_list:

            # Check this bullet to see if it hit a block
            hit_list = arcade.check_for_collision_with_list(bullet, self.platforms_list)

            # If it did, get rid of the bullet
            if len(hit_list) > 0:
                bullet.remove_from_sprite_lists()

            # For every block we hit, add to the score and remove the block
            for platforms in hit_list:
                platforms.remove_from_sprite_lists()

    def process_keychange(self):
        """
        Called when we change a key up/down.
        """

        # Process left/right
        if self.right_pressed and not self.left_pressed:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED
        elif self.left_pressed and not self.right_pressed:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        else:
            self.player_sprite.change_x = 0

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """

        if key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = True
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = True

        self.process_keychange()

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = False

        self.process_keychange()

    def on_update(self, delta_time):
        """ Movement and game logic """

        # Move the player with the physics engine
        self.physics_engine.update()
        self.gold_list.update_animation(delta_time)
        self.coal_list.update_animation(delta_time)
        # self.background_list.update_animation(delta_time)
        self.player_list.update_animation(delta_time)
        self.bullet_list.update_animation(delta_time)

        # See if we hit any Gold
        gold_hit_list = arcade.check_for_collision_with_list(self.player_sprite,
                                                             self.gold_list)

        # See if we hit any Coal
        coal_hit_list = arcade.check_for_collision_with_list(self.player_sprite,
                                                             self.coal_list)

        # Loop through each gold we hit (if any) and remove it
        for gold in gold_hit_list:

            # Figure out how many points this gold is worth
            if 'Points' not in gold.properties:
                print("Warning, collected a gold without a Points property.")
            else:
                points = int(gold.properties['Points'])
                self.score += points

            # Remove the gold
            gold.remove_from_sprite_lists()
            arcade.play_sound(self.collect_gold_sound)

            # Loop through each coal we hit (if any) and remove it
            for coal in coal_hit_list:

                # Figure out how many points this coal is worth
                if 'Points' not in coal.properties:
                    print("Warning, collected a coal without a Points property.")
                else:
                    points = int(coal.properties['Points'])
                    self.score += points

                # Remove the coal
                coal.remove_from_sprite_lists()
                arcade.play_sound(self.collect_coal_sound)

        # Track if we need to change the viewport
        changed_viewport = False

        # --- Manage Scrolling ---

        # Scroll left
        left_boundary = self.view_left + LEFT_VIEWPORT_MARGIN
        if self.player_sprite.left < left_boundary:
            self.view_left -= left_boundary - self.player_sprite.left
            changed_viewport = True

        # Scroll right
        right_boundary = self.view_left + SCREEN_WIDTH - RIGHT_VIEWPORT_MARGIN
        if self.player_sprite.right > right_boundary:
            self.view_left += self.player_sprite.right - right_boundary
            changed_viewport = True

        # Scroll up
        top_boundary = self.view_bottom + SCREEN_HEIGHT - TOP_VIEWPORT_MARGIN
        if self.player_sprite.top > top_boundary:
            self.view_bottom += self.player_sprite.top - top_boundary
            changed_viewport = True

        # Scroll down
        bottom_boundary = self.view_bottom + BOTTOM_VIEWPORT_MARGIN
        if self.player_sprite.bottom < bottom_boundary:
            self.view_bottom -= bottom_boundary - self.player_sprite.bottom
            changed_viewport = True

        if changed_viewport:
            # Only scroll to integers. Otherwise we end up with pixels that
            # don't line up on the screen
            self.view_bottom = int(self.view_bottom)
            self.view_left = int(self.view_left)

            # Do the scrolling
            arcade.set_viewport(self.view_left,
                                SCREEN_WIDTH + self.view_left,
                                self.view_bottom,
                                SCREEN_HEIGHT + self.view_bottom)


def main():
    """ Main method """
    window = MyGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
