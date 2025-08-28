"""
A Wee Bit Miffed Ducks (2024 Elementary Programming Course Project)

Author: Anh Le

Used library: 
    - sweeperlib (author: Mika Oja, University of Oulu).
    - pyglet

Game Overview:
---------------
In A Wee Bit Miffed Ducks, the player launches ducks at targets and obstacles 
to collect coins. The game offers two modes: normal levels and randomly 
generated levels.

1. Normal Levels:
   - 2 pre-defined levels with specific challenges.
   - The player is given a limited number of ducks to destroy all obstacles and targets.
   - Player can restart a level at any time.
   - Player wins after completing each level.

2. Randomized Levels:
   - 3 levels are randomly created.
   - Each level contains 3 targets and 3 obstacles created at random positions.
   - Only the first random level can be reset.
   - The game ends if the player fails to destroy all targets in a level.

Game Modes:
-----------
- **Normal Levels**: Progress through 2 fixed levels with a set number of ducks.
- **Randomized Levels**: 3 randomly created levels

Controls:
---------
    General Controls:
        Q: Quit the game
        M: Menu

    In Menu:
        P: Play normal levels
        R: Play random levels

    In Game:
        R: Restart current level (only available in normal levels and first random level)
        C: Continue to next level (only works for level 1 of normal stage)

By following the gameplay rules and overcoming obstacles, players will advance through 
levels and ultimately win or lose the game.
"""

import sweeperlib
import pyglet
import math
import json
import random 
from sweeperlib import KEYS

WIN_WIDTH = 626
WIN_HEIGHT = 376
START_X = 50
START_Y = 110
GROUND_LEVEL = 85
FORCE_FACTOR = 0.6
GRAVITATIONAL_ACC = 1.5
MAX_DUCKS = 10
TOTAL_ROUNDS = 3
CURRENT_ROUND = 1

game = {
    "x": START_X,
    "y": START_Y,
    "w": 0,
    "h": 0,
    "angle": 0,
    "force": 0,
    "x_velocity": 0,
    "y_velocity": 0,
    "flight": False,
    "dragging": False
}

game_state = {
    "targets": [],
    "obstacles": [],
    "breakable_obstacles": [],
    "boxes": [],
    "used_ducks": [],
    "remaining_ducks": MAX_DUCKS,
    "level": "menu",
    "next_level": None,
    "is_random": False
}

state = []

#---------------------------------Launch ducks------------------------------------------
def launch():
    """
    Initializes the launch process by setting the x and y velocities 
    of the duck based on the current angle and force. Marks the 
    duck as being in flight.
    """
    angle_rad = game["angle"]
        
    x_velocity = -game["force"] * math.cos(angle_rad)
    y_velocity = -game["force"] * math.sin(angle_rad)
        
    game["x_velocity"] = x_velocity
    game["y_velocity"] = y_velocity
    
    game["flight"] = True

def drag_handler(x, y, dx, dy, button, modifiers):
    """
    Handles the dragging of the duck by updating its position 
    and ensuring it stays within the defined circle boundary.

    Parameters:
        x (float): Current x-coordinate of the mouse.
        y (float): Current y-coordinate of the mouse.
        dx (float): Change in x-coordinate of the mouse.
        dy (float): Change in y-coordinate of the mouse.
        button (int): The mouse button being used for the drag.
        modifiers: Additional modifiers for the mouse input.
    """
    if not game["flight"]:
        game["dragging"] = True
        game["x"] += dx
        game["y"] += dy
        game["x"], game["y"] = clamp_inside_circle(game["x"], game["y"], START_X, START_Y, 35)
        
def release_handler(x, y, button, modifiers):
    """
    Handles the release of duck, calculating the launch angle 
    and force, and initiating the launch process.

    Parameters:
        x (float): Current x-coordinate of the mouse.
        y (float): Current y-coordinate of the mouse.
        button (int): The mouse button being used for the release.
        modifiers: Additional modifiers for the mouse input.
    """
    if not game["flight"]: 
        game["angle"] = calculate_angle(START_X, START_Y, game["x"], game["y"])
        game["force"] = calculate_distance(game["x"], game["y"], START_X, START_Y)
        launch()
    game["dragging"] = False

def clamp_inside_circle(x, y, x_center, y_center, rad):
    """
    Ensures a point remains inside a specified circle. If the point is 
    outside the circle, it is clamped to the circle's boundary.

    Parameters:
        x (float): x-coordinate of the point.
        y (float): y-coordinate of the point.
        x_center (float): x-coordinate of the circle's center.
        y_center (float): y-coordinate of the circle's center.
        rad (float): Radius of the circle.

    Returns:
        tuple: The adjusted (x, y) coordinates, ensuring the point lies 
               within or on the circle's boundary.
    """
    center_distance = calculate_distance(x, y, x_center, y_center)
    
    if center_distance > rad: 
        ratio = rad / center_distance
        new_x = ratio * (x - x_center) + x_center
        new_y = ratio * (y - y_center) + y_center
        return new_x, new_y
    return x, y

def calculate_angle(x1, y1, x2, y2):
    """
    Calculates the angle (in radians) between two points relative to the 
    horizontal axis.

    Parameters:
        x1 (float): x-coordinate of the first point.
        y1 (float): y-coordinate of the first point.
        x2 (float): x-coordinate of the second point.
        y2 (float): y-coordinate of the second point.

    Returns:
        float: The angle in radians.
    """
    return math.atan2(y2 - y1, x2 - x1)
    
#---------------------------------Collisions------------------------------------------
def initial_state():
    """
    Puts the game back into its initial state: the duck is put back into the
    launch position, its speed to zero, and its flight state to False.
    """
    if game_state["remaining_ducks"] > 0:
        game_state["remaining_ducks"] -= 1
        game["x"] = START_X
        game["y"] = START_Y
        game["angle"] = 0
        game["force"] = 0
        game["x_velocity"] = 0
        game["y_velocity"] = 0
        game["flight"] = False
   
def stop_duck():
    """
    Stops the duck's movement by setting its velocity to zero and ensuring 
    it rests on the ground if below the ground level.
    """
    game["x_velocity"] = 0
    game["y_velocity"] = 0
    
    if game["y"] < GROUND_LEVEL:
        game["y"] = GROUND_LEVEL

def target_collision():
    """
    Checks if the duck has collided with any target. If a collision is 
    detected, the target is removed, the duck is stopped, and a message 
    is printed.
    """
    for coin in game_state["targets"]:
        coin["radius"] = coin["w"] / 2
        if calculate_distance(game["x"], game["y"], coin["x"], coin["y"]) <= coin["radius"]:
            game_state["targets"].remove(coin)
            print("Hit targets!")
            stop_duck()
            return

def obstacle_collision():
    """
    Checks if the duck has collided with any obstacle. If a collision is 
    detected, the duck is stopped and a message is printed.
    """
    for obstacle in game_state["obstacles"]:
        if (
            obstacle["x"] <= game["x"] <= obstacle["x"] + obstacle["w"] 
            and obstacle["y"] <= game["y"] <= obstacle["y"] + obstacle["h"]
        ):
               print("Hit obstacle!")
               stop_duck()
               return

def check_breakable_collision():
    """
    Checks if the duck has collided with any breakable obstacle. If a collision 
    is detected, the obstacle is marked as falling, the duck is stopped, and a 
    message is printed. It also propagates the falling state to anything above
    falling obstacles.
    """
    for plank in game_state["breakable_obstacles"]:
        if (
            plank["x"] <= game["x"] <= plank["x"] + plank["w"] 
            and plank["y"] <= game["y"] <= plank["y"] + plank["h"]
        ):
            plank["falling"] = True
            print("Hit obstacle!")
            stop_duck()
            return
    
    for plank in game_state["breakable_obstacles"]:
        if plank["falling"]:
            for other_plank in game_state["breakable_obstacles"]:
                if not other_plank["falling"]:
                    if (
                        plank["x"] == other_plank["x"]  # Same vertical column
                        or other_plank["type"] == "horizontal"  # Horizontal obstacles
                        and plank["block"] == other_plank["block"]
                    ):
                        other_plank["falling"] = True

def falling_obstacle():
    """
    Handles the behavior of falling breakable obstacles. Updates their vertical 
    velocity and position. Checks for collisions with targets and removes any 
    hit targets.
    """
    for plank in game_state["breakable_obstacles"]: 
        if plank["falling"]:
            plank["vy"] -= GRAVITATIONAL_ACC
            plank["y"] += plank["vy"]
              
            for coin in game_state["targets"]:
                coin["radius"] = coin["w"] / 2
                if calculate_distance(plank["x"], plank["y"], coin["x"], coin["y"]) <= coin["radius"]:
                    game_state["targets"].remove(coin)
                    print("Hit targets!")

def calculate_distance(x1, y1, x2, y2):
    """
    Calculates the Euclidean distance between two points.

    Parameters:
    x1 (float): x-coordinate of the first point.
    y1 (float): y-coordinate of the first point.
    x2 (float): x-coordinate of the second point.
    y2 (float): y-coordinate of the second point.

    Returns:
    float: The distance between the two points.
    """
    distance = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
    return distance

#---------------------------------Random Stage------------------------------------------
def create_items(obs_num, tar_num, min_height):
    """
    Generates a list of random obstacles and targets and adds them to the 
    game state.

    Parameters:
        obs_num (int): The number of obstacles to generate.
        tar_num (int): The number of targets to generate.
        min_height (int): The minimum y-coordinate for items to spawn.

    Returns:
        list: A combined list of all generated obstacles and targets.
    """
    items = []
    
    for _ in range(obs_num):
        each_obs = {
            "x": random.randint(340, WIN_WIDTH - 25),
            "y": random.randint(min_height, WIN_HEIGHT - 26),
            "w": 25,
            "h": 26,
            "vy": 0
        }
        items.append(each_obs)
        game_state["obstacles"].append(each_obs)
    
    for _ in range(tar_num):
        each_tar = {
            "x": random.randint(340, WIN_WIDTH - 46),
            "y": random.randint(min_height, WIN_HEIGHT - 46),
            "w": 46,
            "h": 46,
            "vy": 0
        }
        items.append(each_tar)
        game_state["targets"].append(each_tar)
    return items

def height_order(items_list):
    """
    Determines the height order of an item based on its top edge position.

    Parameters:
        items_list (dict): An item with properties including `y` and `h`.

    Returns:
        int: The sum of the `y` position and height of the item, indicating its 
            top edge.
    """
    return items_list["y"] + items_list["h"]

def drop(items):
    """
    Simulates the dropping of items under gravity, ensuring items rest on 
    the ground or on top of each other.

    Parameters:
        items (list): A list of items to be updated based on gravitational force.
    """
    items.sort(key=height_order)
    
    for i, block in enumerate(items):
        #Apply gravity to y-velocity
        block["vy"] += GRAVITATIONAL_ACC
        
        #Update new position
        new_y = block["y"] - block["vy"]
       
        if new_y <= GROUND_LEVEL:
            block["y"] = GROUND_LEVEL
            block["vy"] = 0
        else:
            for j in range(i - 1, -1, -1):
                other_block = items[j]
                #Check if blocks fall on top of previous blocks
                if (
                    block["x"] < other_block["x"] + other_block["w"] 
                    and other_block["x"] < block["x"] + block["w"] 
                    and new_y <= other_block["y"] + other_block["h"]
                ):
                    block["y"] = other_block["y"] + other_block["h"]
                    block["vy"] = 0
                    break
                block["y"] = new_y

def create_new_round():
    """
    Sets up a new round in the game. Clears previous targets and obstacles, 
    generates new ones, resets the duck count, and updates the game state 
    to indicate a random level.
    """
    game_state["targets"].clear()
    game_state["obstacles"].clear()
    game_state["remaining_ducks"] = MAX_DUCKS
    game_state["boxes"] = create_items(3, 3, WIN_HEIGHT // 2)

#---------------------------------------------------------------------------------
def draw():
    """
    Draws the current game state to the window, including backgrounds, sprites,
    UI elements, and the appropriate game status.

    This function handles:
    - Drawing the background and the main game window.
    - Rendering the menu screen when the game is in the "menu" state.
    - Drawing the game elements like the sling, targets, obstacles, ducks, and 
      flight paths for levels.
    - Displaying win and lose messages after completing a level or random rounds.
    - Rendering the random levels, including obstacles and targets, based on 
      the game state.
    - Handling the rendering of remaining ducks, their positions, and other 
      gameplay elements.
    """
    sweeperlib.clear_window()
    sweeperlib.draw_background()
    
    if game_state["level"] == "menu":
        menu_items = [
            {"text": "Choose mode...", "font_size": 16, "x": WIN_WIDTH // 2, "y": 230},
            {"text": "P: Play levels", "font_size": 9, "x": WIN_WIDTH // 2, "y": 180 },
            {"text": "R: Play random levels", "font_size": 9, "x": WIN_WIDTH // 2, "y": 150 },
            {"text": "Q: Quit", "font_size": 9, "x": WIN_WIDTH // 2, "y": 120 }
        ]
        
        #Draw box text
        box = pyglet.shapes.Rectangle(
                x=WIN_WIDTH / 2,
                y=WIN_HEIGHT / 2 - 10,
                width=300,
                height=180,
                color=(31, 169, 248)
            )
        box.anchor_x = 150
        box.anchor_y = 90
        box.opacity = 250
        box.draw()
        
        #Add texts for command lines
        for items in menu_items:
            label = pyglet.text.Label(
                items["text"],
                font_name='Minecraft Standard',
                font_size=items["font_size"],
                x=items["x"],
                y=items["y"],
                anchor_x='center',
                anchor_y='center',
                color=(255, 255, 255, 255)
            )
            label.draw()
    
    elif game_state["level"].startswith("level"): 
        
        #Load sling
        sling = sweeperlib.load_background_image("sprites", "sling.png")
        sling_sprites = pyglet.sprite.Sprite(sling, x=50, y=GROUND_LEVEL)
        sling_sprites.scale = 1/2
        sling_sprites.draw()
       
        #Load targets
        for coin in game_state["targets"]:
            target_img = sweeperlib.load_background_image("sprites", "target.png")
            target_sprites = pyglet.sprite.Sprite(target_img, coin["x"], coin["y"])
            target_sprites.scale = 1/10
            target_sprites.draw()
        
        #Load obstacles for level 1
        for box in game_state["obstacles"]:
            obstacle_img = sweeperlib.load_background_image("sprites", "obstacle.jpg")
            obstacle_sprites = pyglet.sprite.Sprite(obstacle_img, box["x"], box["y"])
            obstacle_sprites.scale = 1/20
            obstacle_sprites.draw() 
        
        #Load obstacles for level 2
        for box in game_state["breakable_obstacles"]:
            obstacle_img = sweeperlib.load_background_image("sprites", "plank.png")
            obstacle_sprites = pyglet.sprite.Sprite(obstacle_img, box["x"], box["y"])
            obstacle_sprites.scale = 1/3
            if box["type"] == "horizontal":
                obstacle_sprites.rotation = 90
            obstacle_sprites.draw()
        
        #Load duck
        duck_img = sweeperlib.load_background_image("sprites", "duck.png")
        duck_sprites = pyglet.sprite.Sprite(duck_img, game["x"], game["y"])
        duck_sprites.scale = 1/12
        duck_sprites.draw()
        
        #Load remaining ducks 
        for i in range(game_state["remaining_ducks"] - 1):
            duck_img = sweeperlib.load_background_image("sprites", "duck.png")
            remaining_duck = pyglet.sprite.Sprite(duck_img, x= i*30, y=WIN_HEIGHT-40)
            remaining_duck.scale = 1/12
            remaining_duck.draw()
        
    #Load win message for normal levels  
    elif game_state["level"] == "win": 
        win_strings = [
            {"text": "You win!", "font_size": 18, "x": WIN_WIDTH // 2, "y": WIN_HEIGHT // 2 + 40},
            {"text": "R: Restart", "font_size": 9, "x": WIN_WIDTH // 2, "y": WIN_HEIGHT // 2 - 30},
            {"text": "M: Menu", "font_size": 9, "x": WIN_WIDTH // 2, "y": WIN_HEIGHT // 2 - 50},
            {"text": "Q: Quit", "font_size": 9, "x": WIN_WIDTH // 2, "y": WIN_HEIGHT // 2 - 70}
        ]
        
        #Only load "C: Continue" option if there are next levels 
        if game_state["next_level"]:
            win_strings.insert(
                1, 
                {"text": "C: Continue", "font_size": 9, "x": WIN_WIDTH // 2, "y": WIN_HEIGHT // 2 - 10}
            )
        
        #Draw box text
        box = pyglet.shapes.Rectangle(
            x=WIN_WIDTH / 2,
            y=WIN_HEIGHT / 2 - 10,
            width=300,
            height=180,
            color=(31, 169, 248)
        )
        box.anchor_x = 150
        box.anchor_y = 90
        box.opacity = 250
        box.draw()
        
        #Add texts for command lines
        for string in win_strings:
            label_win = pyglet.text.Label(
                string["text"],
                font_name='Minecraft Standard',
                font_size=string["font_size"],
                x=string["x"],
                y=string["y"],
                anchor_x='center',
                anchor_y='center',
                color=(255, 255, 255, 255)
            )
            label_win.draw()
        
    #Load lose message for normal levels           
    elif game_state["level"] == "lose":
        lose_strings = [
            {"text": "You lose!", "font_size": 20, "x": WIN_WIDTH // 2, "y": WIN_HEIGHT // 2 + 40},
            {"text": "R: Restart", "font_size": 11, "x": WIN_WIDTH // 2, "y": WIN_HEIGHT // 2 + - 10},
            {"text": "M: Menu", "font_size": 11, "x": WIN_WIDTH // 2, "y": WIN_HEIGHT // 2 - 40},
            {"text": "Q: Quit", "font_size": 11, "x": WIN_WIDTH // 2, "y": WIN_HEIGHT // 2 - 70}
        ]
        
        #Draw box text
        box = pyglet.shapes.Rectangle(
            x=WIN_WIDTH / 2,
            y=WIN_HEIGHT / 2 - 10,
            width=300,
            height=180,
            color=(31, 169, 248)
        )
        box.anchor_x = 150
        box.anchor_y = 90
        box.opacity = 250
        box.draw()
        
        #Add texts for command lines
        for string in lose_strings:
            label_lose = pyglet.text.Label(
                string["text"],
                font_name='Minecraft Standard',
                font_size=string["font_size"],
                x=string["x"],
                y=string["y"],
                anchor_x='center',
                anchor_y='center',
                color=(255, 255, 255, 255)
            )
            label_lose.draw()
        
    elif game_state["level"] == "random":
        #Load sling
        sling = sweeperlib.load_background_image("sprites", "sling.png")
        sling_sprites = pyglet.sprite.Sprite(sling, x=50, y=GROUND_LEVEL)
        sling_sprites.scale = 1/2
        sling_sprites.draw()
       
        #Load targets
        for coin in game_state["targets"]:
            target_img = sweeperlib.load_background_image("sprites", "target.png")
            target_sprites = pyglet.sprite.Sprite(target_img, coin["x"], coin["y"])
            target_sprites.scale = 1/10
            target_sprites.draw()
        
        #Load obstacles for each level 
        for box in game_state["obstacles"]:
            obstacle_img = sweeperlib.load_background_image("sprites", "obstacle.jpg")
            obstacle_sprites = pyglet.sprite.Sprite(obstacle_img, box["x"], box["y"])
            obstacle_sprites.scale = 1/20
            obstacle_sprites.draw() 
        
        #Load duck
        duck_img = sweeperlib.load_background_image("sprites", "duck.png")
        duck_sprites = pyglet.sprite.Sprite(duck_img, game["x"], game["y"])
        duck_sprites.scale = 1/12
        duck_sprites.draw()
        
        #Load remaining ducks 
        for i in range(game_state["remaining_ducks"]):
            duck_img = sweeperlib.load_background_image("sprites", "duck.png")
            remaining_duck = pyglet.sprite.Sprite(duck_img, x= i*30, y=WIN_HEIGHT-40)
            remaining_duck.scale = 1/12
            remaining_duck.draw()
        
def load_level(level):
    """
    Loads a new level or state based on the provided level identifier.

    This function:
    - Loads a normal level by reading the level data from a JSON file and 
      updating the game state (obstacles, targets, duck count, etc.).
    - Handles transitions to win or lose states for both normal and random levels.
    - Resets game elements (like ducks, obstacles, and targets) before loading 
      a new level or state.
    - In case of a win, it updates the game state with the next level to load.
    
    It handles three types of levels:
    - Normal levels (e.g., "level1.json").
    - Random levels (e.g., "random").
    - Special states for win/lose conditions.

    Parameters:
        level (str): A string representing the level to load. This can be a normal level 
                    file (e.g., "level1.json"), a random level ("random"), or a special 
                    game state ("win", "lose").
    """
    game_state["used_ducks"].clear()
    game_state["obstacles"].clear()
    game_state["targets"].clear()
    game_state["breakable_obstacles"].clear()
    
    try:
        if level == "win":
            game_state["level"] = level
            game_state["next_level"] = None
        
        # Normal levels
        elif level.endswith(".json"):
                try:
                    with open(level) as file:
                        data = json.load(file)
                        game_state["level"] = level
                        if level == "level1.json":
                            game_state["obstacles"] = data["obstacles"].copy()
                        else:
                            game_state["breakable_obstacles"] = data["obstacles"].copy()
                        game_state["targets"] = data["targets"].copy()
                        game_state["remaining_ducks"] = data["ducks"]
                        game_state["next_level"] = data["next_level"]
                except IOError:
                    print("Failed to load level.")
    except AttributeError:
        print("There are no more levels left!") #Catch errors for pressing C option

def keyboard_handler(symbol, modifiers):
    """
    Handles keyboard input events and updates the game state accordingly.

    This function processes keypresses based on the current game state and 
    takes actions such as navigating through menus, starting new levels, and 
    restarting or quitting the game.

    Key actions include:
    - Pressing 'Q' to quit the game.
    - Pressing 'M' to return to the main menu.
    - Pressing 'P' to start playing a normal level.
    - Pressing 'R' (in menu) to start a random level.
    - Pressing 'C' to continue after winning a level.
    - Pressing 'R' (in game command) to restart the current level 
      or random round after losing.
    - Pressing 'M' in the win/lose screens to return to the menu.

    Parameters:
        symbol (int): The key symbol (key code) of the pressed key.
        modifiers: Additional modifiers for the mouse input.
    """
    global state
    global CURRENT_ROUND
    
    if symbol == KEYS.Q:
        sweeperlib.close()
    
    if symbol == KEYS.M:
        initial_state()
        game_state["targets"].clear()
        game_state["obstacles"].clear()
        game_state["is_random"] = False
        game_state["level"] = "menu"
        CURRENT_ROUND = 1
        state.clear()
        return
       
    if game_state["level"] == "menu":
        if symbol == KEYS.P:
            #Load level 1
            load_level("level1.json")
            game_state["level"] = "level1"
            game_state["next_level"] = "level2"
            game_state["is_random"] = False
            state.append("level1")
            
        elif symbol == KEYS.R:
            #Load random stage
            CURRENT_ROUND = 1
            create_new_round()      
            game_state["level"] = "random"
            game_state["is_random"] = True
    
    if game_state["level"] == "win":
        try:
            if symbol == KEYS.C:
                #Proceed from level 1 to level 2
                initial_state()
                load_level("level2.json")
                game_state["level"] = "level2"
                state.append(game_state["level"])
            
            elif symbol == KEYS.R:
                if game_state["is_random"] and CURRENT_ROUND == 1:
                    #Reset random stage
                    CURRENT_ROUND = 1
                    create_new_round()
                    game_state["level"] = "random"
                    game_state["is_random"] = False
                else:
                    #Reset normal stage
                    initial_state()
                    game_state["is_random"] = False
                    game_state["level"] = state[-1]
                    load_level(game_state["level"] + ".json") 
        except IndexError: 
                print("Only reset first round!") 
                #Catch error if resetting random stage in rounds other than first one                
           
    elif game_state["level"] == "lose":
        try:
            if symbol == KEYS.R:
                #Reset random stage
                if game_state["is_random"] and CURRENT_ROUND == 1:
                    CURRENT_ROUND = 1
                    create_new_round()
                    game_state["level"] = "random"
                    game_state["is_random"] = False
                else:
                    #Reset normal stage
                    initial_state()
                    game_state["level"] = state[-1]
                    load_level(game_state["level"] + ".json")
        except IndexError: 
                print("Only reset first round!")
                #Catch error if resetting random stage in rounds other than first one

def update(elapsed_time):
    if game_state["level"] == "random":
        drop(game_state["boxes"])
    
    if game["flight"]:
        game["y_velocity"] -= GRAVITATIONAL_ACC  
        game["x"] += game["x_velocity"]
        game["y"] += game["y_velocity"]
        
        #Collision for level 1
        obstacle_collision()
        target_collision()
        if not game_state["targets"] and game_state["remaining_ducks"] >= 0:
            if game_state["level"].startswith("level"):
                game_state["is_random"] = False
                game_state["level"] = "win"
            else:
                global CURRENT_ROUND
                if CURRENT_ROUND < TOTAL_ROUNDS:
                    CURRENT_ROUND += 1
                    create_new_round()
                else: 
                    game_state["next_level"] = None
                    game_state["level"] = "win"       
        elif game_state["remaining_ducks"] == 0:
            game_state["level"] = "lose"
         
        #Collision for level 2
        check_breakable_collision()    
        
        if game["y"] <= GROUND_LEVEL:
            game_state["used_ducks"].append({
                "x": game["x"],
                "y": game["y"],
                "w": game["w"],
                "h": game["h"],
                "vy": 0
            })
            initial_state()
    
    #Falling obstacles destroy targets level 2
    falling_obstacle()        

#-------------------Main-----------------------
if __name__ == "__main__":
    if game_state["level"] == "random":
        create_new_round()
    image = sweeperlib.load_background_image("sprites", "background.jpg")
    sweeperlib.create_window(width = WIN_WIDTH, height = WIN_HEIGHT, bg_image=image)
    sweeperlib.load_duck("sprites")
    sweeperlib.set_draw_handler(draw)
    sweeperlib.set_keyboard_handler(keyboard_handler)
    sweeperlib.set_drag_handler(drag_handler)
    sweeperlib.set_release_handler(release_handler)
    sweeperlib.set_interval_handler(update, 1/60)
    sweeperlib.start()
"""
    Updates the game state based on the elapsed time, handling physics, 
    collisions, and transitions between game states.

    This function executes the following logic:
    - Updates the position of objects affected by gravity, such as blocks falling 
      in the "random" level.
    - Handles the flight mechanics of the duck, updating its position based on 
      velocity and applying gravitational acceleration.
    - Checks for collisions:
        - Ducks with obstacles in level 1.
        - Ducks with breakable obstacles in level 2.
        - Ducks with targets across all levels.
    - Manages the win condition:
        - If all targets are cleared and ducks remain, the player wins, and 
          the win message appears prompting users to choose next actions.
        - If playing random levels, transitions to the next random level or 
          ends the game if all rounds are completed.
    - Manages the lose condition:
        - If no ducks remain and targets are not cleared, the player loses and 
          the lose message appears prompting users to choose next actions.
    - Handles the physics for falling objects, including interactions where 
      falling obstacles can destroy targets in level 2.
      
      Parameters:
        elapsed_time (float): The amount of time elapsed since the last update, 
        typically provided by the game loop.
    """