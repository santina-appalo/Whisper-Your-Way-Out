import pygame
import speech_recognition as sr
from enum import Enum
import threading
import time
import random
import os

# Game settings
WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)

class GameState(Enum):
    INTRO = 0
    STAGE_1 = 1  # Library puzzle
    STAGE_2 = 2  # Laboratory puzzle
    STAGE_3 = 3  # Secret office puzzle
    STAGE_4 = 4  # Ancient vault puzzle
    STAGE_5 = 5  # Final escape
    WIN = 6
    FAIL = 7

class VoiceControlledEscapeRoom:
    def __init__(self):
        # Initialize pygame
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Whisper Your Way Out")
        self.clock = pygame.time.Clock()
        
        # Game state
        self.current_state = GameState.INTRO
        self.game_running = True
        self.time_limit = 1200  # 20 minutes in seconds
        self.start_time = None
        self.remaining_time = self.time_limit
        
        # Voice recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.voice_thread = None
        self.last_command = ""
        self.recognized_text = ""
        self.is_listening = False
        
        # Game assets
        self.load_assets()
        
        # Puzzle states
        self.puzzles_solved = {
            GameState.STAGE_1: False,
            GameState.STAGE_2: False,
            GameState.STAGE_3: False,
            GameState.STAGE_4: False,
            GameState.STAGE_5: False
        }
        
        # Game-specific variables
        self.inventory = []
        self.current_clues = []
        self.messages = []
        self.max_messages = 5
        
        # Stage-specific variables
        self.stage1_bookcase_open = False
        self.stage2_cabinet_opened = False
        self.stage2_chemicals_mixed = False
        self.stage3_computer_unlocked = False
        self.stage3_computer_on = False
        self.stage3_portrait_flip = False
        self.stage4_symbols_solved = False
        self.stage5_door_unlocked = False
        self.stage5_riddle = False
        
        # Setup voice recognition
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        
    def load_assets(self):
        # Create backgrounds dictionary
        self.backgrounds = {}
        
        # Try to load images from assets folder
        try:
            # Create image file paths
            image_files = {
                GameState.INTRO: os.path.join("assets", "intro.jpg"),
                GameState.STAGE_1: os.path.join("assets", "library.jpg"),
                GameState.STAGE_2: os.path.join("assets", "lab.jpg"),
                GameState.STAGE_3: os.path.join("assets", "office.jpg"),
                GameState.STAGE_4: os.path.join("assets", "vault.jpg"),
                GameState.STAGE_5: os.path.join("assets", "final_room.jpg"),
            }
            
            # Load each image if it exists
            for state, file_path in image_files.items():
                if os.path.exists(file_path):
                    self.backgrounds[state] = pygame.image.load(file_path)
                    self.backgrounds[state] = pygame.transform.scale(self.backgrounds[state], (WIDTH, HEIGHT))
                    print(f"Loaded image: {file_path}")
                    door_path = os.path.join("assets", "open_passage.png") #stage1
                    chemicals_img = os.path.join("assets", "chemicals.jpg") #stage2
                    mixed_img = os.path.join("assets", "mixed_chemicals.jpg") #stage3
                    phoenix_img = os.path.join("assets", "phoenix.png") #stage4
                    connected_img = os.path.join("assets", "connected.jpg") #stage4
                    sequence_img = os.path.join("assets", "sequence.png") #stage4
                    solved_img = os.path.join("assets", "stage4_open.png") #stage5
                    riddle_img = os.path.join("assets", "stage5_riddle.png") #stage5
                    solved_img5 = os.path.join("assets", "stage5_open.png") #stage5

                    if os.path.exists(door_path):
                       self.door_overlay = pygame.image.load(door_path)
                       self.chemical_overlay = pygame.image.load(chemicals_img)
                       self.mix_overlay = pygame.image.load(mixed_img)
                       self.phoenix_overlay = pygame.image.load(phoenix_img)
                       self.connected_overlay = pygame.image.load(connected_img)
                       self.sequence_overlay = pygame.image.load(sequence_img)
                       self.ssolved_overlay = pygame.image.load(solved_img)
                       self.riddle_overlay = pygame.image.load(riddle_img)
                       self.ssolved5_overlay = pygame.image.load(solved_img5)


                       self.door_overlay = pygame.transform.scale(self.door_overlay, (120, 170))
                       self.chemical_overlay = pygame.transform.scale(self.chemical_overlay, (100, 85))
                       self.mix_overlay = pygame.transform.scale(self.mix_overlay, (100, 85))  # You can change size here
                       self.phoenix_overlay = pygame.transform.scale(self.phoenix_overlay, (163, 295))
                       self.connected_overlay = pygame.transform.scale(self.connected_overlay, (76, 118))
                       self.sequence_overlay = pygame.transform.scale(self.sequence_overlay, (76, 118))
                       self.ssolved_overlay = pygame.transform.scale(self.ssolved_overlay, (WIDTH, HEIGHT))
                       self.riddle_overlay = pygame.transform.scale(self.riddle_overlay, (384, 256))
                       self.ssolved5_overlay = pygame.transform.scale(self.ssolved5_overlay, (WIDTH, HEIGHT))

                       print("Door overlay image loaded.")
                    else:
                       print("Warning: Door overlay image not found.")
                       self.door_overlay = None
                else:
                    # Create a placeholder if the image doesn't exist
                    print(f"Warning: Image not found: {file_path}")
                    self.backgrounds[state] = pygame.Surface((WIDTH, HEIGHT))
                    
                    # Give each missing image a different color
                    if state == GameState.INTRO:
                        self.backgrounds[state].fill((50, 50, 80))
                    elif state == GameState.STAGE_1:
                        self.backgrounds[state].fill((70, 40, 40))  # Library - dark red
                    elif state == GameState.STAGE_2:
                        self.backgrounds[state].fill((40, 70, 70))  # Laboratory - teal
                    elif state == GameState.STAGE_3:
                        self.backgrounds[state].fill((70, 70, 40))  # Office - olive
                    elif state == GameState.STAGE_4:
                        self.backgrounds[state].fill((50, 40, 70))  # Vault - purple
                    elif state == GameState.STAGE_5:
                        self.backgrounds[state].fill((30, 60, 30))  # Final room - green
            
            # Create placeholders for WIN and FAIL states (usually no image files for these)
            self.backgrounds[GameState.WIN] = pygame.Surface((WIDTH, HEIGHT))
            self.backgrounds[GameState.WIN].fill((40, 100, 40))  # Win - bright green
            
            self.backgrounds[GameState.FAIL] = pygame.Surface((WIDTH, HEIGHT))
            self.backgrounds[GameState.FAIL].fill((100, 40, 40))  # Fail - bright red
            
        except Exception as e:
            print(f"Error loading images: {e}")
            # Create fallback placeholders if there's an error
            for state in GameState:
                self.backgrounds[state] = pygame.Surface((WIDTH, HEIGHT))
            
            # Set colors for placeholder backgrounds
            self.backgrounds[GameState.INTRO].fill((50, 50, 80))
            self.backgrounds[GameState.STAGE_1].fill((70, 40, 40))  # Library - dark red
            self.backgrounds[GameState.STAGE_2].fill((40, 70, 70))  # Laboratory - teal
            self.backgrounds[GameState.STAGE_3].fill((70, 70, 40))  # Office - olive
            self.backgrounds[GameState.STAGE_4].fill((50, 40, 70))  # Vault - purple
            self.backgrounds[GameState.STAGE_5].fill((30, 60, 30))  # Final room - green
            self.backgrounds[GameState.WIN].fill((40, 100, 40))     # Win - bright green
            self.backgrounds[GameState.FAIL].fill((100, 40, 40))    # Fail - bright red
        
        # Load fonts
        self.font_small = pygame.font.SysFont('Arial', 18)
        self.font_medium = pygame.font.SysFont('Arial', 24)
        self.font_large = pygame.font.SysFont('Arial', 32)
        
        # Sound effects - would be loaded from files in a real implementation
        # self.sounds = {
        #    "success": pygame.mixer.Sound("success.wav"),
        #    "fail": pygame.mixer.Sound("fail.wav"),
        #    ...
        # }
        
    def start_listening(self):
        """Start the voice recognition thread"""
        if not self.is_listening:
            self.is_listening = True
            self.add_message("Listening for commands...")
            self.voice_thread = threading.Thread(target=self.voice_recognition_loop)
            self.voice_thread.daemon = True
            self.voice_thread.start()
            
    def stop_listening(self):
        """Stop the voice recognition thread"""
        self.is_listening = False
        if self.voice_thread:
            self.voice_thread.join(timeout=1)
            self.voice_thread = None
        self.add_message("Voice recognition stopped.")
    
    def voice_recognition_loop(self):
        """Voice recognition thread function"""
        while self.is_listening:
            try:
                with self.microphone as source:
                    self.add_message("Listening...")
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    
                try:
                    self.recognized_text = self.recognizer.recognize_google(audio).lower()
                    self.last_command = self.recognized_text
                    self.add_message(f"You said: {self.recognized_text}")
                    self.process_voice_command(self.recognized_text)
                    
                except sr.UnknownValueError:
                    self.add_message("Sorry, I didn't understand that.")
                except sr.RequestError:
                    self.add_message("Could not request results. Check your network connection.")
                    
            except Exception as e:
                self.add_message(f"Error: {str(e)}")
                time.sleep(1)
                
    def process_voice_command(self, command):
        """Process voice commands based on current game state"""
        # General commands that work in any stage
        if "help" in command or "hint" in command:
            self.provide_hint()
            return
            
        if "inventory" in command or "what do i have" in command:
            self.show_inventory()
            return
            
        if "look around" in command or "examine room" in command:
            self.describe_current_room()
            return
            
        # Process stage-specific commands
        if self.current_state == GameState.INTRO:
            if "start" in command or "begin" in command or "enter" in command or "start game" in command or "game start" in command:
                self.start_game()
                
        elif self.current_state == GameState.STAGE_1:
            self.process_stage1_command(command)
            
        elif self.current_state == GameState.STAGE_2:
            self.process_stage2_command(command)
            
        elif self.current_state == GameState.STAGE_3:
            self.process_stage3_command(command)
            
        elif self.current_state == GameState.STAGE_4:
            self.process_stage4_command(command)
            
        elif self.current_state == GameState.STAGE_5:
            self.process_stage5_command(command)

        elif self.current_state in [GameState.WIN, GameState.FAIL]:
            if "start" in command or "begin" in command:
                self.reset_game()
            return
    
    def process_stage1_command(self, command):
        """Process commands for the library stage"""
        if "examine bookshelf" in command or "look at books" in command or "examine" in command or "look" in command:
            self.add_message("You see many old books. One red book seems out of place.")
            
        elif "pull red book" in command or "take red book" in command or "take book" in command or "pull" in command or "take" in command or "take red" in command:
            if not self.stage1_bookcase_open:
                self.stage1_bookcase_open = True
                self.add_message("You pulled the red book. The bookcase slides open revealing a hidden passage!")
                self.add_message("You found a key card.")
                self.inventory.append("key card")
            else:
                self.add_message("You've already opened the bookcase.")
                
        elif "enter passage" in command or "go through passage" in command or "enter" in command or "go in" in command or "go" in command :
            if self.stage1_bookcase_open:
                self.current_state = GameState.STAGE_2
                self.add_message("You enter the passage and find yourself in a laboratory.")
                self.describe_current_room()
            else:
                self.add_message("What passage? You need to find a way out first.")
    
    def process_stage2_command(self, command):
        """Process commands for the laboratory stage"""
        if "examine lab" in command or "look around" in command:
            self.add_message("You see various chemical apparatus, a locked cabinet, and strange symbols on a whiteboard.")
            
        elif "use key card" in command or "use key" in command and "key card" in self.inventory:
            self.stage2_cabinet_opened = True
            self.add_message("You used the key card to unlock the cabinet.")
            self.add_message("Inside you find chemicals and a note about mixing blue and green liquids.")
            
        elif "mix chemicals" in command or "mix blue and green" in command or "mix" in command :
            if "key card" in self.inventory and not self.stage2_chemicals_mixed:
                self.stage2_chemicals_mixed = True
                self.add_message("The chemicals react and create a purple smoke that reveals hidden writing on the wall!")
                self.add_message("The writing shows a code: 4827")
                self.inventory.append("lab code")
            elif self.stage2_chemicals_mixed:
                self.add_message("You've already mixed the chemicals.")
            else:
                self.add_message("You need to access the chemicals first.")
                
        elif "enter code" in command or "use code" in command:
            if "lab code" in self.inventory:
                self.add_message("You enter the code 4827 into the door panel. The door unlocks!")
                self.current_state = GameState.STAGE_3
                self.describe_current_room()
            else:
                self.add_message("What code? You need to find a code first.")
    
    def process_stage3_command(self, command):
        """Process commands for the office stage"""
        if "examine office" in command or "look around" in command:
            self.add_message("You're in a secret office with a computer, filing cabinet, and a portrait on the wall.")
            
        elif "check computer" in command or "use computer" in command or "look at computer" in command:
            self.stage3_computer_on = True
            self.add_message("The computer needs a password.")
            
        elif "look behind portrait" in command or "look behind" in command or "check portrait" in command or "check painting" in command or "look behind painting" in command:
            self.stage3_portrait_flip = True
            self.add_message("You find a sticky note with 'password: PHOENIX' written on it.")
            self.inventory.append("computer password")
            
        elif "enter password" in command and "computer password" in self.inventory:
            if not self.stage3_computer_unlocked:
                self.stage3_computer_unlocked = True
                self.add_message("You logged into the computer. There's a map to an ancient vault and a sequence of symbols.")
                self.inventory.append("vault map")
                self.inventory.append("symbol sequence")
                self.add_message("You can now exit the office.")
            else:
                self.add_message("You're already logged into the computer.")
                self.add_message("You can now exit the office.")
                
        elif "exit office" in command or "go to vault" in command or "exit" in command:
            if "vault map" in self.inventory:
                self.current_state = GameState.STAGE_4
                self.add_message("Using the map, you navigate to the ancient vault.")
                self.describe_current_room()
            else:
                self.add_message("You don't know where to go yet.")
    
    def process_stage4_command(self, command):
        """Process commands for the ancient vault stage"""
        if "examine vault" in command or "look around" in command:
            self.add_message("The vault has a stone door with 5 symbol slots. Ancient symbols are carved all around.")
            
        elif ("use symbol sequence" in command or "use sequence" in command or "use pattern" in command) and "symbol sequence" in self.inventory:
            self.add_message("You enter the sequence of symbols. The stone door creaks open.")
            if not self.stage4_symbols_solved:
                self.stage4_symbols_solved = True
                self.add_message("You arrange the symbols in the correct order: Sun, Moon, Star, Mountain, Ocean.")
                self.add_message("The stone door rumbles and slowly slides open!")
            else:
                self.add_message("You've already solved the symbol puzzle.")
                
        elif "enter vault" in command or "go through door" in command or "enter" in command:
            if self.stage4_symbols_solved:
                self.current_state = GameState.STAGE_5
                self.add_message("You enter the vault and find a final chamber with an exit door.")
                self.describe_current_room()
            else:
                self.add_message("The stone door is still closed.")
    
    def process_stage5_command(self, command):
        """Process commands for the final escape stage"""
        if "examine room" in command or "look around" in command:
            self.add_message("There's a modern door with a complex lock and a plaque with a riddle.")
            
        elif "read riddle" in command or "examine plaque" in command or "riddle" in command:
            self.add_message("The plaque holds a riddle that challenges your wit.")
            self.stage5_riddle = True
            self.add_message("The riddle says: 'I guard the secrets of those who dare,")
            self.add_message("Through whispered words and heavy air.'")
            self.add_message("My face is cold, my grip is tight,")
            self.add_message("I open only when the phrase is right.")
            self.add_message("No key I need, no lock you see,")
            self.add_message("Yet silent speech will set you free.")
            self.add_message("What am I?' written on it.")

            
        elif "answer riddle" in command :
            self.add_message("What is your answer to the riddle?")
            
        elif "a password" in command or "password" in command:
            if not self.stage5_door_unlocked:
                self.stage5_door_unlocked = True
                self.add_message("Correct! The lock mechanism whirs and the exit door opens!")
            else:
                self.add_message("You've already solved the riddle.")
                
        elif "exit" in command or "escape" in command or "leave" in command or "enter" in command:
            if self.stage5_door_unlocked:
                self.win_game()
            else:
                self.add_message("You need to unlock the door first.")
    
    def provide_hint(self):
        """Give a hint based on current game state"""
        if self.current_state == GameState.STAGE_1:
            self.add_message("Hint: Look carefully at the bookshelf. Something might be out of place.")
        elif self.current_state == GameState.STAGE_2:
            self.add_message("Hint: You need to access the cabinet to find important chemicals.")
        elif self.current_state == GameState.STAGE_3:
            self.add_message("Hint: Important information is often hidden in plain sight.")
        elif self.current_state == GameState.STAGE_4:
            self.add_message("Hint: The symbol sequence you found earlier might be useful here.")
        elif self.current_state == GameState.STAGE_5:
            self.add_message("Hint: Think about the riddle. What shape has no end? What letter ends the word 'all'?")
    
    def show_inventory(self):
        """Display current inventory items"""
        if not self.inventory:
            self.add_message("Your inventory is empty.")
        else:
            self.add_message(f"Inventory: {', '.join(self.inventory)}")
    
    def describe_current_room(self):
        """Describe the current room based on game state"""
        if self.current_state == GameState.STAGE_1:
            self.add_message("You're in an old library with tall bookshelves and dusty tomes.")
        elif self.current_state == GameState.STAGE_2:
            self.add_message("This appears to be a high-tech laboratory with various equipment and chemicals.")
            self.add_message("You see various chemical apparatus, a locked cabinet, and strange symbols on a whiteboard.")
            self.add_message("The objective is to find the code to open the door.")
        elif self.current_state == GameState.STAGE_3:
            self.add_message("You're in a secret office with modern technology that contrasts with the old building.")
            self.add_message("You see a computer, filing cabinet, and a portrait on the wall.")
        elif self.current_state == GameState.STAGE_4:
            self.add_message("An ancient vault with stone walls covered in mysterious symbols.")
            self.add_message("The vault has a stone door with 5 symbol slots. Ancient symbols are carved all around.")
        elif self.current_state == GameState.STAGE_5:
            self.add_message("The final chamber has a modern security door - your path to freedom.")
            self.add_message("There's a modern door with a complex lock and a plaque with a riddle.")
    
    def add_message(self, message):
        """Add a message to the message log"""
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
        print(message)  # Print to console for debugging
    
    def start_game(self):
        """Start the actual game"""
        self.current_state = GameState.STAGE_1
        self.start_time = time.time()
        self.add_message("The game has begun! You find yourself trapped in an old library.")
        self.add_message("Use your voice to explore and solve puzzles to escape.")
        self.describe_current_room()
    
    def update_time(self):
        """Update the remaining time"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            self.remaining_time = max(0, self.time_limit - elapsed)
            
            if self.remaining_time <= 0 and self.current_state not in [GameState.WIN, GameState.FAIL]:
                self.game_over()
    
    def win_game(self):
        """Player has won the game"""
        self.current_state = GameState.WIN
        self.add_message("Congratulations! You've escaped!")
    
    def game_over(self):
        """Player has lost the game"""
        self.current_state = GameState.FAIL
        self.add_message("Time's up! You failed to escape in time.")
    
    def draw(self):
        """Draw the game screen"""
        # Draw background for current stage
        self.screen.blit(self.backgrounds[self.current_state], (0, 0))
        
        # Draw stage-specific elements
        if self.current_state == GameState.INTRO:
            self.draw_intro()
        elif self.current_state == GameState.WIN:
            self.draw_win_screen()
        elif self.current_state == GameState.FAIL:
            self.draw_fail_screen()
        else:
            self.draw_game_screen()
        
        #draw ui
        self.draw_ui()
        pygame.display.flip()
    
    def draw_intro(self):
        """Draw the intro screen"""
        title = self.font_large.render("Whisper Your Way Out", True, WHITE)
        instr1 = self.font_medium.render("Say 'Start or begin' to begin the game", True, WHITE)
        instr2 = self.font_medium.render("Solve puzzles and escape within 20 minutes", True, WHITE)
        
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
        self.screen.blit(instr1, (WIDTH//2 - instr1.get_width()//2, 200))
        self.screen.blit(instr2, (WIDTH//2 - instr2.get_width()//2, 250))
    
    def draw_win_screen(self):
        """Draw the win screen"""
        title = self.font_large.render("You Escaped!", True, WHITE)
        if self.start_time:
            elapsed = time.time() - self.start_time
            mins, secs = divmod(int(elapsed), 60)
            time_text = f"Time taken: {mins:02d}:{secs:02d}"
            time_surf = self.font_medium.render(time_text, True, WHITE)
            
            self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
            self.screen.blit(time_surf, (WIDTH//2 - time_surf.get_width()//2, 200))
    
    def draw_fail_screen(self):
        """Draw the failure screen"""
        title = self.font_large.render("Time's Up! You Failed to Escape", True, WHITE)
        instr = self.font_medium.render("Say 'Start' to try again", True, WHITE)
        
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
        self.screen.blit(instr, (WIDTH//2 - instr.get_width()//2, 200))
    
    def reset_game(self):
        """Reset game state and start over"""
        self.__init__()  # reinitialize everything
        self.run()

    def draw_game_screen(self):
        """Draw the game screen for the current stage"""
        
        
        # Draw stage-specific elements (would use actual images in a real implementation)
        if self.current_state == GameState.STAGE_1:
            # Draw bookshelf
            # Draw passage if open
            if self.stage1_bookcase_open:
                self.screen.blit(self.door_overlay, (420, 170))
        
        elif self.current_state == GameState.STAGE_2:
            # Draw lab equipment
            if self.stage2_cabinet_opened:
                self.screen.blit(self.chemical_overlay, (82, 205))
            
            if self.stage2_chemicals_mixed:
                self.screen.blit(self.mix_overlay, (82, 205))  # Purple mixture
        
        elif self.current_state == GameState.STAGE_3:
            if self.stage3_computer_on:
                # Draw portrait
                self.screen.blit(self.connected_overlay, (610,333))

            if self.stage3_portrait_flip:
                # Draw flipped portrait
                self.screen.blit(self.phoenix_overlay, (330,80))
      
            if self.stage3_computer_unlocked:  
                self.screen.blit(self.sequence_overlay, (610, 333))
        
        elif self.current_state == GameState.STAGE_4:
            # Draw vault door
            # Door frame
            if self.stage4_symbols_solved:
                self.screen.blit(self.ssolved_overlay, (0, 0))

        elif self.current_state == GameState.STAGE_5:
            #riddle
            if self.stage5_riddle:
                
                center_x = (WIDTH - 384) // 2
                center_y = (HEIGHT - 256) // 2
                self.screen.blit(self.riddle_overlay,(center_x, center_y))

            # Draw open door if unlocked
            if self.stage5_door_unlocked:

                self.screen.blit(self.ssolved5_overlay, (0,0))

        # Draw stage title
        stage_titles = {
            GameState.STAGE_1: "Stage 1: The Ancient Library",
            GameState.STAGE_2: "Stage 2: The Secret Laboratory",
            GameState.STAGE_3: "Stage 3: The Hidden Office",
            GameState.STAGE_4: "Stage 4: The Ancient Vault",
            GameState.STAGE_5: "Stage 5: The Final Escape"
        }
        
        title = self.font_medium.render(stage_titles[self.current_state], True, WHITE)
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 60))        

    def draw_ui(self):
        """Draw common UI elements"""
        # Draw message log
        msg_box = pygame.Rect(10, HEIGHT - 150, WIDTH - 20, 140)
        pygame.draw.rect(self.screen, (20, 20, 20), msg_box)
        pygame.draw.rect(self.screen, GRAY, msg_box, 2)
        
        # Draw messages
        for i, msg in enumerate(self.messages):
            msg_surf = self.font_small.render(msg, True, WHITE)
            self.screen.blit(msg_surf, (20, HEIGHT - 140 + (i * 25)))
        
        # Draw time remaining if game has started
        if self.current_state not in [GameState.INTRO, GameState.WIN, GameState.FAIL]:
            mins, secs = divmod(int(self.remaining_time), 60)
            time_text = f"Time: {mins:02d}:{secs:02d}"
            time_surf = self.font_medium.render(time_text, True, WHITE)
            self.screen.blit(time_surf, (WIDTH - 120, 20))
            
            # Draw listening indicator
            if self.is_listening:
                status = "Listening..."
            else:
                status = "Voice Off"
            status_surf = self.font_small.render(status, True, WHITE)
            self.screen.blit(status_surf, (20, 20))
    

    def run(self):
        """Main game loop"""
        try:
            self.start_listening()
            
            while self.game_running:
                self.clock.tick(FPS)
                
                # Process events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.game_running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.game_running = False
                        elif event.key == pygame.K_l:
                            # Toggle listening with L key (for testing)
                            if self.is_listening:
                                self.stop_listening()
                            else:
                                self.start_listening()
                
                # Update game state
                self.update_time()
                
                # Draw everything
                self.draw()
                
        except Exception as e:
            print(f"Game crashed: {str(e)}")
        finally:
            # Clean up
            self.stop_listening()
            pygame.quit()

if __name__ == "__main__":
    game = VoiceControlledEscapeRoom()
    game.run()