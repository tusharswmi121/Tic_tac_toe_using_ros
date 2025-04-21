#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import pygame
import sys
import math
import random
import time
from enum import Enum, auto

# Constants
BOARD_SIZE = 3
CELL_SIZE = 150
WINDOW_WIDTH = CELL_SIZE * BOARD_SIZE + 100
WINDOW_HEIGHT = CELL_SIZE * BOARD_SIZE + 300
PLAYER_X = 'X'
PLAYER_O = 'O'
EMPTY = None
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Default Colors (Pygame RGB format)
DEFAULT_COLORS = {
    'bg': (240, 240, 240),
    'line': (70, 70, 70),
    'text': (30, 30, 30),
    'menu': (200, 230, 255),
    'button': (100, 150, 255),
    'button_hover': (70, 120, 220),
    'x_default': (255, 50, 50),    # Red
    'o_default': (50, 50, 255),    # Blue
    'highlight': (200, 200, 255)
}

# Game states enumeration
class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    GAME_OVER = auto()
    SETTINGS = auto()
    COLOR_PICKER = auto()
    NAME_INPUT = auto()
    HINT_SCREEN = auto()
    DIFFICULTY_SELECT = auto()
    FIRST_TURN_SELECT = auto()

# Difficulty levels enumeration
class Difficulty(Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    IMPOSSIBLE = "Impossible"

class Button:
    def __init__(self, x, y, width, height, text, color=None, hover_color=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color if color else DEFAULT_COLORS['button']
        self.hover_color = hover_color if hover_color else DEFAULT_COLORS['button_hover']
        self.is_hovered = False
        self.font = pygame.font.SysFont('Arial', 24)
        
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2, border_radius=5)
        
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
        
    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

class ColorPicker:
    def __init__(self, x, y, size=150):
        self.rect = pygame.Rect(x, y, size, size)
        self.color = (255, 0, 0)
        self.surface = pygame.Surface((size, size))
        self.update_surface()
        
    def update_surface(self):
        for y in range(self.rect.height):
            for x in range(self.rect.width):
                hue = x / self.rect.width
                saturation = 1.0 - (y / self.rect.height)
                r, g, b = self.hsv_to_rgb(hue, saturation, 1.0)
                self.surface.set_at((x, y), (r, g, b))
                
    def hsv_to_rgb(self, h, s, v):
        if s == 0.0:
            return (int(v*255), int(v*255), int(v*255))
        i = int(h*6.0)
        f = (h*6.0) - i
        p = v*(1.0 - s)
        q = v*(1.0 - s*f)
        t = v*(1.0 - s*(1.0-f))
        i = i%6
        
        if i == 0: return (int(v*255), int(t*255), int(p*255))
        if i == 1: return (int(q*255), int(v*255), int(p*255))
        if i == 2: return (int(p*255), int(v*255), int(t*255))
        if i == 3: return (int(p*255), int(q*255), int(v*255))
        if i == 4: return (int(t*255), int(p*255), int(v*255))
        if i == 5: return (int(v*255), int(p*255), int(q*255))
        
    def get_color_at_pos(self, pos):
        if self.rect.collidepoint(pos):
            rel_x = pos[0] - self.rect.x
            rel_y = pos[1] - self.rect.y
            hue = rel_x / self.rect.width
            saturation = 1.0 - (rel_y / self.rect.height)
            return self.hsv_to_rgb(hue, saturation, 1.0)
        return None
        
    def draw(self, surface):
        surface.blit(self.surface, self.rect)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2)
        
        # Draw current color preview
        preview_rect = pygame.Rect(self.rect.x + self.rect.width + 20, self.rect.y, 50, 50)
        pygame.draw.rect(surface, self.color, preview_rect)
        pygame.draw.rect(surface, (0, 0, 0), preview_rect, 2)

class InputBox:
    def __init__(self, x, y, width, height, text=''):
        self.rect = pygame.Rect(x, y, width, height)
        self.color_inactive = (200, 200, 200)
        self.color_active = (240, 240, 255)
        self.color = self.color_inactive
        self.text = text
        self.font = pygame.font.SysFont('Arial', 24)
        self.txt_surface = self.font.render(text, True, (0, 0, 0))
        self.active = False
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input box
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive
            
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                # Add character if it's printable and we have space
                if len(self.text) < 12 and event.unicode.isprintable():
                    self.text += event.unicode
                    
            # Re-render the text
            self.txt_surface = self.font.render(self.text, True, (0, 0, 0))
        return False
        
    def draw(self, surface):
        # Blit the rect
        pygame.draw.rect(surface, self.color, self.rect, 0)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2)
        # Blit the text
        surface.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))

class TicTacToe(Node):
    def __init__(self):
        super().__init__('tic_tac_toe_node')
        
        # Initialize Pygame
        pygame.init()
        pygame.font.init()
        self.font_large = pygame.font.SysFont('Arial', 48)
        self.font_medium = pygame.font.SysFont('Arial', 36)
        self.font_small = pygame.font.SysFont('Arial', 24)
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("ROS 2 Tic-Tac-Toe")
        self.clock = pygame.time.Clock()
        
        # Game state variables
        self.board = [EMPTY for _ in range(BOARD_SIZE * BOARD_SIZE)]
        self.current_player = PLAYER_X
        self.game_state = GameState.MENU
        self.game_mode = None
        self.ai_difficulty = None
        self.winner = None
        
        # Player settings
        self.player_x_name = "Player X"
        self.player_o_name = "Player O"
        self.player_x_color = DEFAULT_COLORS['x_default']
        self.player_o_color = DEFAULT_COLORS['o_default']
        self.original_player_o_name = "Player O"
        self.score = {PLAYER_X: 0, PLAYER_O: 0}
        
        # Game settings
        self.animations_enabled = True
        self.sound_effects = False

        # Hint screen scroll variables
        self.hint_scroll_pos = 0
        self.hint_scroll_dragging = False
        self.drag_start_y = 0
        self.drag_start_scroll = 0

        # AI turn visualization
        self.ai_thinking = False
        self.ai_move_position = None
        self.ai_move_start_time = 0
        self.ai_move_duration = 1000  # milliseconds for AI move animation

        # UI elements
        self.setup_ui_elements()
        
        # ROS logging
        self.get_logger().info("Tic-Tac-Toe with ROS 2 and Pygame initialized!")

    def setup_ui_elements(self):
        """Initialize all UI buttons and elements"""
        center_x = WINDOW_WIDTH // 2

        # Main menu buttons
        self.menu_buttons = [
            Button(center_x - 100, 200, 200, 40, "Player vs AI"),
            Button(center_x - 100, 250, 200, 40, "Player vs Player"),
            Button(center_x - 100, 300, 200, 40, "Settings"),
            Button(center_x - 100, 350, 200, 40, "Hint"),
            Button(center_x - 100, 400, 200, 40, "Exit")
        ]

        # Settings buttons
        self.settings_buttons = [
            Button(350, 90, 120, 30, "Change"),  # X Name
            Button(350, 130, 120, 30, "Change"), # O Name
            Button(350, 170, 120, 30, "Change"), # X Color
            Button(350, 210, 120, 30, "Change"), # O Color
            Button(WINDOW_WIDTH//2 - 100, 400, 200, 40, "Back to Menu")
        ]

        # Game over buttons
        self.game_over_buttons = [
            Button(center_x - 100, 300, 200, 40, "Play Again"),
            Button(center_x - 100, 350, 200, 40, "Main Menu")
        ]

        # Color picker
        self.color_picker = ColorPicker(50, 150)
        self.color_picker_buttons = [
            Button(center_x - 100, 350, 200, 40, "Confirm"),
            Button(center_x - 100, 400, 200, 40, "Cancel")
        ]

        # Name input
        self.name_input_box = InputBox(center_x - 100, 200, 200, 40)
        self.name_input_buttons = [
            Button(center_x - 100, 250, 200, 40, "Confirm"),
            Button(center_x - 100, 300, 200, 40, "Cancel")
        ]

        # Current setting being modified
        self.current_setting = None

        # Hint screen back button
        self.hint_back_button = Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT - 100, 200, 40, "Back to Menu")

        # Difficulty selection buttons
        self.difficulty_buttons = [
            Button(WINDOW_WIDTH//2 - 100, 200, 200, 40, "Easy"),
            Button(WINDOW_WIDTH//2 - 100, 250, 200, 40, "Medium"),
            Button(WINDOW_WIDTH//2 - 100, 300, 200, 40, "Hard"),
            Button(WINDOW_WIDTH//2 - 100, 350, 200, 40, "Impossible"),
            Button(WINDOW_WIDTH//2 - 100, 400, 200, 40, "Back")
        ]

        # First turn selection buttons
        self.first_turn_buttons = [
            Button(WINDOW_WIDTH//2 - 100, 200, 200, 40, "Player Goes First"),
            Button(WINDOW_WIDTH//2 - 100, 250, 200, 40, "AI Goes First"),
            Button(WINDOW_WIDTH//2 - 100, 300, 200, 40, "Back")
        ]

    def reset_game(self):
        """Reset the game board"""
        self.board = [EMPTY for _ in range(BOARD_SIZE * BOARD_SIZE)]
        self.winner = None
        self.ai_thinking = False
        self.ai_move_position = None

    def reset_score(self):
        """Reset the game scores"""
        self.score = {PLAYER_X: 0, PLAYER_O: 0}

    def draw_board(self):
        """Draw the game board with Pygame"""
        self.screen.fill(DEFAULT_COLORS['bg'])
        
        # Draw screen based on current game state
        if self.game_state == GameState.MENU:
            self.draw_menu()
        elif self.game_state == GameState.SETTINGS:
            self.draw_settings()
        elif self.game_state == GameState.COLOR_PICKER:
            self.draw_color_picker()
        elif self.game_state == GameState.NAME_INPUT:
            self.draw_name_input()
        elif self.game_state == GameState.HINT_SCREEN:
            self.draw_hint_screen()
        elif self.game_state == GameState.DIFFICULTY_SELECT:
            self.draw_difficulty_select()
        elif self.game_state == GameState.FIRST_TURN_SELECT:
            self.draw_first_turn_select()
        elif self.game_state in [GameState.PLAYING, GameState.GAME_OVER]:
            self.draw_game()
            
        pygame.display.flip()

    def draw_menu(self):
        """Draw the main menu"""
        title = self.font_large.render("Tic-Tac-Toe", True, (0, 0, 100))
        subtitle = self.font_small.render("ROS 2 Enhanced Edition", True, (50, 50, 150))
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 50))
        self.screen.blit(subtitle, (WINDOW_WIDTH//2 - subtitle.get_width()//2, 110))
        
        for button in self.menu_buttons:
            button.draw(self.screen)

    def draw_settings(self):
        """Draw the settings menu"""
        title = self.font_large.render("Settings", True, (0, 0, 100))
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 50))
        
        # Draw current settings
        settings = [
            f"Player X: {self.player_x_name}",
            f"Player O: {self.player_o_name}",
            f"X Color: RGB{self.player_x_color}",
            f"O Color: RGB{self.player_o_color}",
        ]
        
        for i, text in enumerate(settings):
            text_surface = self.font_small.render(text, True, DEFAULT_COLORS['text'])
            self.screen.blit(text_surface, (50, 100 + i * 40))
        
        # Make sure the buttons are visible and properly positioned
        button_labels = [
            "Change", "Change", "Change", "Change", "Back to Menu"
        ]
        
        for i, button in enumerate(self.settings_buttons):
            button.text = button_labels[i]
            # Position buttons to the right of the settings text
            if i < 4:  # All except "Back to Menu"
                button.rect.x = 350
                button.rect.y = 90 + i * 40
            button.draw(self.screen)

    def draw_difficulty_select(self):
        """Draw the difficulty selection menu"""
        title = self.font_large.render("Select AI Difficulty", True, (0, 0, 100))
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 100))
        
        for button in self.difficulty_buttons:
            button.draw(self.screen)

    def draw_first_turn_select(self):
        """Draw the first turn selection menu"""
        title = self.font_large.render("Who Goes First?", True, (0, 0, 100))
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 100))
        
        for button in self.first_turn_buttons:
            button.draw(self.screen)

    def handle_name_input(self, event):
        """Handle text input for name changes"""
        if self.name_input_box.handle_event(event):  # Return is pressed
            if self.current_setting == "Player X":
                self.player_x_name = self.name_input_box.text or "Player X"
            else:
                self.player_o_name = self.name_input_box.text or "Player O"
                self.original_player_o_name = self.player_o_name
            self.game_state = GameState.SETTINGS
            return
                
        # Check buttons
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            for i, button in enumerate(self.name_input_buttons):
                if button.is_clicked(pos, event):
                    if i == 0:  # Confirm
                        if self.current_setting == "Player X":
                            self.player_x_name = self.name_input_box.text or "Player X"
                        else:
                            self.player_o_name = self.name_input_box.text or "Player O"
                            self.original_player_o_name = self.player_o_name
                    self.game_state = GameState.SETTINGS

    def draw_color_picker(self):
        """Draw the color picker interface"""
        title_text = f"Select {self.current_setting} Color"
        title = self.font_large.render(title_text, True, (0, 0, 100))
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 50))
        
        self.color_picker.draw(self.screen)
        
        for button in self.color_picker_buttons:
            button.draw(self.screen)

    def draw_name_input(self):
        """Draw the name input interface"""
        self.screen.fill(DEFAULT_COLORS['bg'])
        
        title_text = f"Enter {self.current_setting} Name"
        title = self.font_large.render(title_text, True, (0, 0, 100))
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 100))
        
        # Draw the input box
        self.name_input_box.draw(self.screen)
        
        # Draw blinking cursor if active
        if self.name_input_box.active and pygame.time.get_ticks() % 1000 < 500:  # Blink every 500ms
            cursor_pos = self.name_input_box.rect.x + 5 + self.name_input_box.font.size(self.name_input_box.text)[0]
            pygame.draw.line(self.screen, (0, 0, 0),
                            (cursor_pos, self.name_input_box.rect.y + 5),
                            (cursor_pos, self.name_input_box.rect.y + 35), 2)
        
        # Draw buttons
        for button in self.name_input_buttons:
            button.draw(self.screen)

    def draw_game(self):
        """Draw the game board and interface"""
        # Draw grid lines
        for i in range(1, BOARD_SIZE):
            # Vertical lines
            pygame.draw.line(self.screen, DEFAULT_COLORS['line'], 
                           (i * CELL_SIZE + 50, 50), 
                           (i * CELL_SIZE + 50, CELL_SIZE * BOARD_SIZE + 50), 3)
            # Horizontal lines
            pygame.draw.line(self.screen, DEFAULT_COLORS['line'], 
                           (50, i * CELL_SIZE + 50), 
                           (CELL_SIZE * BOARD_SIZE + 50, i * CELL_SIZE + 50), 3)
        
        # Draw X's and O's
        for i in range(BOARD_SIZE * BOARD_SIZE):
            row = i // BOARD_SIZE
            col = i % BOARD_SIZE
            if self.board[i] == PLAYER_X:
                # Draw X
                x_pos = col * CELL_SIZE + 50 + CELL_SIZE // 2
                y_pos = row * CELL_SIZE + 50 + CELL_SIZE // 2
                pygame.draw.line(self.screen, self.player_x_color, 
                               (x_pos - 40, y_pos - 40), 
                               (x_pos + 40, y_pos + 40), 5)
                pygame.draw.line(self.screen, self.player_x_color, 
                               (x_pos + 40, y_pos - 40), 
                               (x_pos - 40, y_pos + 40), 5)
            elif self.board[i] == PLAYER_O:
                # Draw O
                x_pos = col * CELL_SIZE + 50 + CELL_SIZE // 2
                y_pos = row * CELL_SIZE + 50 + CELL_SIZE // 2
                pygame.draw.circle(self.screen, self.player_o_color, (x_pos, y_pos), 40, 5)
        
        # Draw AI hand if it's AI's turn and we're in AI mode
        if self.game_mode == 'AI' and self.current_player == PLAYER_O and not self.winner:
            self.draw_ai_hand()
        
        # Draw game info
        mode_text = "VS AI" if self.game_mode == 'AI' else "VS Player"
        turn_text = f"Turn: {self.player_x_name if self.current_player == PLAYER_X else self.player_o_name}"
        score_text = f"{self.player_x_name}: {self.score[PLAYER_X]}  {self.player_o_name}: {self.score[PLAYER_O]}"
        
        self.screen.blit(self.font_small.render(mode_text, True, DEFAULT_COLORS['text']), 
                        (50, CELL_SIZE * BOARD_SIZE + 60))
        self.screen.blit(self.font_small.render(turn_text, True, DEFAULT_COLORS['text']), 
                        (50, CELL_SIZE * BOARD_SIZE + 90))
        self.screen.blit(self.font_small.render(score_text, True, DEFAULT_COLORS['text']), 
                        (50, CELL_SIZE * BOARD_SIZE + 120))
        
        # Draw menu button
        menu_button = Button(WINDOW_WIDTH - 120, 10, 100, 30, "Menu")
        menu_button.draw(self.screen)
        
        # Draw game over message if needed
        if self.game_state == GameState.GAME_OVER:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))
            
            if self.winner == "DRAW":
                result_text = self.font_large.render("It's a DRAW!", True, (255, 255, 255))
            else:
                winner_name = self.player_x_name if self.winner == PLAYER_X else self.player_o_name
                result_text = self.font_large.render(f"{winner_name} wins!", True, (255, 255, 255))
            
            self.screen.blit(result_text, (WINDOW_WIDTH//2 - result_text.get_width()//2, 200))
            
            for button in self.game_over_buttons:
                button.draw(self.screen)

    def draw_ai_hand(self):
        """Draw a robotic pick-and-place arm indicating AI is making a move"""
        current_time = pygame.time.get_ticks()
        
        # Calculate animation progress (0-1)
        if self.ai_thinking and self.ai_move_position is None:
            # Thinking phase - show searching animation
            progress = (current_time % 1000) / 1000  # Continuous pulsing
            
            # Draw scanning laser effect
            scan_y = 50 + (CELL_SIZE * BOARD_SIZE) * progress
            pygame.draw.line(self.screen, (255, 0, 0, 150), (50, scan_y), 
                            (50 + CELL_SIZE * BOARD_SIZE, scan_y), 2)
            
            # Draw grid highlight effect
            for i in range(BOARD_SIZE):
                for j in range(BOARD_SIZE):
                    if self.board[i * BOARD_SIZE + j] == EMPTY:
                        cell_x = 50 + j * CELL_SIZE
                        cell_y = 50 + i * CELL_SIZE
                        highlight_alpha = int(127 + 127 * math.sin(progress * 2 * math.pi + (i+j)/2))
                        s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                        s.fill((255, 0, 0, highlight_alpha//8))
                        self.screen.blit(s, (cell_x, cell_y))
            
            # Draw "AI processing" text with scanning effect
            thinking_text = self.font_small.render("AI processing move...", True, (50, 50, 50))
            self.screen.blit(thinking_text, (WINDOW_WIDTH//2 - thinking_text.get_width()//2, 
                                        CELL_SIZE * BOARD_SIZE + 150))
                                        
        elif self.ai_move_position is not None:
            # Moving phase - show robot arm moving to position
            elapsed = current_time - self.ai_move_start_time
            progress = min(1.0, elapsed / self.ai_move_duration)
            
            # Target position (center of the cell)
            row = self.ai_move_position // BOARD_SIZE
            col = self.ai_move_position % BOARD_SIZE
            target_x = col * CELL_SIZE + 50 + CELL_SIZE // 2
            target_y = row * CELL_SIZE + 50 + CELL_SIZE // 2
            
            # Calculate robot arm position
            # Base of robot arm is fixed at the right side of the board
            base_x = 50 + CELL_SIZE * BOARD_SIZE + 60
            base_y = 50 + CELL_SIZE * BOARD_SIZE // 2
            
            # Determine robot arm movement phases
            if progress < 0.4:  # Moving arm to position above target
                phase_progress = progress / 0.4
                arm_end_x = target_x
                arm_end_y = 20  # Hover above the board first
                gripper_closed = False
            elif progress < 0.6:  # Lowering arm to target
                phase_progress = (progress - 0.4) / 0.2
                arm_end_x = target_x
                arm_end_y = 20 + (target_y - 20) * phase_progress
                gripper_closed = False
            elif progress < 0.8:  # Gripping and placing the O
                phase_progress = (progress - 0.6) / 0.2
                arm_end_x = target_x
                arm_end_y = target_y
                gripper_closed = True
            else:  # Raising arm after placement
                phase_progress = (progress - 0.8) / 0.2
                arm_end_x = target_x
                arm_end_y = target_y - (target_y - 20) * phase_progress
                gripper_closed = False
            
            # Draw robot arm segments (assuming two-segment robotic arm)
            arm_length1 = 140  # Length of first arm segment
            arm_length2 = 160  # Length of second arm segment
            
            # Calculate arm joint position using inverse kinematics (simplified)
            dx = arm_end_x - base_x
            dy = arm_end_y - base_y
            dist = math.sqrt(dx*dx + dy*dy)
            
            # Constrain distance to possible range
            dist = max(abs(arm_length1 - arm_length2) + 10, min(arm_length1 + arm_length2 - 10, dist))
            
            # Law of cosines to find angles
            angle1 = math.atan2(dy, dx) + math.acos((arm_length1*arm_length1 + dist*dist - arm_length2*arm_length2) / (2 * arm_length1 * dist))
            angle2 = math.pi - math.acos((arm_length1*arm_length1 + arm_length2*arm_length2 - dist*dist) / (2 * arm_length1 * arm_length2))
            
            # Calculate joint positions
            joint_x = base_x + arm_length1 * math.cos(angle1)
            joint_y = base_y + arm_length1 * math.sin(angle1)
            
            # Draw base of robot arm (fixed mount)
            base_width = 30
            base_height = 80
            pygame.draw.rect(self.screen, (50, 50, 60), 
                        (base_x - 10, base_y - base_height//2, base_width, base_height))
            # Add metallic details to base
            pygame.draw.rect(self.screen, (80, 80, 90), 
                        (base_x - 5, base_y - base_height//2 + 5, base_width - 10, base_height - 10))
            pygame.draw.rect(self.screen, (30, 30, 35), 
                        (base_x - 15, base_y - base_height//2 - 5, base_width + 10, 10))
            pygame.draw.rect(self.screen, (30, 30, 35), 
                        (base_x - 15, base_y + base_height//2 - 5, base_width + 10, 10))
                        
            # Draw mounting bolts
            bolt_positions = [(base_x - 5, base_y - base_height//2 + 10),
                            (base_x - 5, base_y + base_height//2 - 10),
                            (base_x + base_width - 15, base_y - base_height//2 + 10),
                            (base_x + base_width - 15, base_y + base_height//2 - 10)]
            for bx, by in bolt_positions:
                pygame.draw.circle(self.screen, (120, 120, 130), (int(bx), int(by)), 4)
                pygame.draw.circle(self.screen, (180, 180, 190), (int(bx), int(by)), 2)
            
            # Draw first arm segment (thicker, with hydraulic look)
            pygame.draw.line(self.screen, (60, 60, 70), (base_x, base_y), (joint_x, joint_y), 12)
            # Add mechanical details to first segment
            pygame.draw.line(self.screen, (100, 100, 110), (base_x, base_y), (joint_x, joint_y), 8)
            # Draw hydraulic cylinder alongside the arm
            hydraulic_offset = 5
            hyd1_x = base_x + hydraulic_offset * math.cos(angle1 + math.pi/2)
            hyd1_y = base_y + hydraulic_offset * math.sin(angle1 + math.pi/2)
            hyd2_x = joint_x + hydraulic_offset * math.cos(angle1 + math.pi/2)
            hyd2_y = joint_y + hydraulic_offset * math.sin(angle1 + math.pi/2)
            pygame.draw.line(self.screen, (40, 40, 45), (hyd1_x, hyd1_y), (hyd2_x, hyd2_y), 4)
            
            # Draw second arm segment
            elbow_angle = angle1 + angle2
            pygame.draw.line(self.screen, (80, 80, 90), (joint_x, joint_y), (arm_end_x, arm_end_y), 8)
            pygame.draw.line(self.screen, (120, 120, 130), (joint_x, joint_y), (arm_end_x, arm_end_y), 5)
            
            # Draw joint between segments
            pygame.draw.circle(self.screen, (50, 50, 60), (int(joint_x), int(joint_y)), 8)
            pygame.draw.circle(self.screen, (100, 100, 110), (int(joint_x), int(joint_y)), 5)
            
            # Draw end effector (gripper)
            gripper_width = 24 if not gripper_closed else 14
            gripper_height = 30
            
            # Draw end effector base (connecting to arm)
            pygame.draw.rect(self.screen, (70, 70, 80), 
                        (int(arm_end_x - 6), int(arm_end_y), 12, 10))
            
            # Draw gripper arms
            grip_left_x = arm_end_x - gripper_width//2
            grip_right_x = arm_end_x + gripper_width//2
            
            # Left gripper jaw
            pygame.draw.polygon(self.screen, (100, 100, 110), [
                (int(arm_end_x - 6), int(arm_end_y + 10)),
                (int(grip_left_x), int(arm_end_y + 10)),
                (int(grip_left_x), int(arm_end_y + gripper_height)),
                (int(grip_left_x + 8), int(arm_end_y + gripper_height)),
                (int(arm_end_x - 6), int(arm_end_y + 15))
            ])
            
            # Right gripper jaw
            pygame.draw.polygon(self.screen, (100, 100, 110), [
                (int(arm_end_x + 6), int(arm_end_y + 10)),
                (int(grip_right_x), int(arm_end_y + 10)),
                (int(grip_right_x), int(arm_end_y + gripper_height)),
                (int(grip_right_x - 8), int(arm_end_y + gripper_height)),
                (int(arm_end_x + 6), int(arm_end_y + 15))
            ])
            
            # Draw 'O' marker being placed
            if gripper_closed:
                o_color = self.player_o_color
                pygame.draw.circle(self.screen, o_color, 
                                (int(arm_end_x), int(arm_end_y + gripper_height//2)), 10, 3)
            
            # Add small lights to indicate activity
            light_color = (0, 255, 0) if progress < 0.8 else (255, 255, 0)
            pygame.draw.circle(self.screen, light_color, (int(base_x + 10), int(base_y - base_height//2 + 15)), 3)
            
            # If animation complete, place the mark
            if progress >= 1.0:
                self.board[self.ai_move_position] = PLAYER_O
                self.ai_move_position = None
                self.ai_thinking = False
                self.winner = self.check_winner()
                if not self.winner:
                    self.current_player = PLAYER_X
                # Add this code to handle the game over state when AI wins
                else:
                    if self.winner != "DRAW":
                        self.score[self.winner] += 1
                    self.game_state = GameState.GAME_OVER


    def draw_hint_screen(self):
        """Draw the hint/rules screen with all content fitting without scrolling"""
        self.screen.fill(WHITE)
        
        # Create smaller font objects
        title_font = pygame.font.SysFont('Arial', 32, bold=True)
        section_font = pygame.font.SysFont('Arial', 20, bold=True)
        text_font = pygame.font.SysFont('Arial', 18)
        
        # Draw title
        title = title_font.render("Game Rules and Hints", True, BLACK)
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 20))
        
        # Organized rules and hints with section markers
        rules = [
            ("Tic-Tac-Toe Rules:", True),
            ("1. Game is played on a 3x3 grid", False),
            ("2. Players alternate placing X or O", False),
            ("3. First to get 3 in a row wins", False),
            ("4. Lines can be horizontal, vertical or diagonal", False),
            ("5. Full board with no winner is a draw", False),
            ("", False),
            ("Game Modes:", True),
            ("• Player vs AI: Play against computer", False),
            ("• Player vs Player: Two players alternate", False),
            ("", False),
            ("Winning Strategies:", True),
            ("• Take center spot first (best advantage)", False),
            ("• Create two winning opportunities at once", False),
            ("• Block opponent when they have two in a row", False),
            ("", False),
            ("Settings Options:", True),
            ("• Change player names and colors", False),
            ("• Player O shows as 'AI' in vs AI mode", False),
            ("", False),
            ("Controls:", True),
            ("• Click squares to place your mark", False),
            ("• Menu buttons for navigation", False),
            ("• ESC key returns to main menu", False)
        ]
        
        # Drawing parameters
        start_y = 70  # Below title
        line_spacing = 22  # Reduced spacing
        section_indent = 20
        text_indent = 40
        max_width = WINDOW_WIDTH - 40  # Account for margins
        
        # Draw all content
        y_pos = start_y
        for text, is_section in rules:
            if not text:  # Empty line (spacing)
                y_pos += line_spacing // 2
                continue
                
            if is_section:
                # Draw section header
                text_surface = section_font.render(text, True, (50, 50, 200))
                self.screen.blit(text_surface, (section_indent, y_pos))
            else:
                # Draw regular text (wrap if needed)
                words = text.split(' ')
                line = ''
                for word in words:
                    test_line = line + word + ' '
                    if text_font.size(test_line)[0] < max_width - text_indent:
                        line = test_line
                    else:
                        if line:
                            text_surface = text_font.render(line, True, BLACK)
                            self.screen.blit(text_surface, (text_indent, y_pos))
                            y_pos += line_spacing
                        line = word + ' '
                if line:
                    text_surface = text_font.render(line, True, BLACK)
                    self.screen.blit(text_surface, (text_indent, y_pos))
            
            y_pos += line_spacing
        
        # Position and draw back button
        self.hint_back_button.rect.y = WINDOW_HEIGHT - 70
        self.hint_back_button.draw(self.screen)

    def check_winner(self):
        """Check if there's a winner"""
        win_conditions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
            (0, 4, 8), (2, 4, 6)              # diagonals
        ]
        
        for x, y, z in win_conditions:
            if self.board[x] == self.board[y] == self.board[z] != EMPTY:
                return self.board[x]
        
        if EMPTY not in self.board:
            return "DRAW"
        
        return None

    def best_move(self):
        """Find the best move using minimax algorithm"""
        best_score = -math.inf
        move = None
        
        for i in range(9):
            if self.board[i] == EMPTY:
                self.board[i] = PLAYER_O
                score = self.minimax(0, False)
                self.board[i] = EMPTY
                
                if score > best_score:
                    best_score = score
                    move = i
                    
                if self.ai_difficulty == Difficulty.IMPOSSIBLE and best_score == 10:
                    break
        
        return move

    def minimax(self, depth, is_maximizing):
        """Minimax algorithm implementation"""
        winner = self.check_winner()
        
        if winner == PLAYER_X:
            return -10 + depth
        if winner == PLAYER_O:
            return 10 - depth
        if winner == "DRAW":
            return 0
            
        if is_maximizing:
            best_score = -math.inf
            for i in range(9):
                if self.board[i] == EMPTY:
                    self.board[i] = PLAYER_O
                    score = self.minimax(depth + 1, False)
                    self.board[i] = EMPTY
                    best_score = max(score, best_score)
            return best_score
        else:
            best_score = math.inf
            for i in range(9):
                if self.board[i] == EMPTY:
                    self.board[i] = PLAYER_X
                    score = self.minimax(depth + 1, True)
                    self.board[i] = EMPTY
                    best_score = min(score, best_score)
            return best_score

    def ai_move(self):
        """Make AI move based on difficulty level"""
        self.ai_thinking = True
        self.ai_move_position = None
        
        if self.animations_enabled:
            # Show thinking animation for a moment
            self.draw_board()
            pygame.display.flip()
            pygame.time.delay(500)
        
        if self.ai_difficulty == Difficulty.EASY:
            move = random.choice([i for i, cell in enumerate(self.board) if cell == EMPTY])
        elif self.ai_difficulty == Difficulty.MEDIUM:
            if random.random() < 0.7:
                move = self.medium_ai_move()
            else:
                move = random.choice([i for i, cell in enumerate(self.board) if cell == EMPTY])
        elif self.ai_difficulty in [Difficulty.HARD, Difficulty.IMPOSSIBLE]:
            move = self.best_move()
        
        if self.animations_enabled:
            # Start the move animation
            self.ai_move_position = move
            self.ai_move_start_time = pygame.time.get_ticks()
        else:
            # No animation, just place the mark
            self.board[move] = PLAYER_O
            self.ai_thinking = False
            self.winner = self.check_winner()
            if not self.winner:
                self.current_player = PLAYER_X

    def medium_ai_move(self):
        """AI with some basic strategy"""
        # Check for winning move
        for i in range(9):
            if self.board[i] == EMPTY:
                self.board[i] = PLAYER_O
                if self.check_winner() == PLAYER_O:
                    self.board[i] = EMPTY
                    return i
                self.board[i] = EMPTY
        
        # Check to block player
        for i in range(9):
            if self.board[i] == EMPTY:
                self.board[i] = PLAYER_X
                if self.check_winner() == PLAYER_X:
                    self.board[i] = EMPTY
                    return i
                self.board[i] = EMPTY
        
        # Take center if available
        if self.board[4] == EMPTY:
            return 4
        
        # Take a corner
        corners = [0, 2, 6, 8]
        available_corners = [c for c in corners if self.board[c] == EMPTY]
        if available_corners:
            return random.choice(available_corners)
        
        # Take any available edge
        edges = [1, 3, 5, 7]
        available_edges = [e for e in edges if self.board[e] == EMPTY]
        if available_edges:
            return random.choice(available_edges)
        
        return random.choice([i for i, cell in enumerate(self.board) if cell == EMPTY])

    def handle_click(self, pos, event):
        """Handle mouse click events"""
        if self.game_state == GameState.MENU:
            for i, button in enumerate(self.menu_buttons):
                if button.is_clicked(pos, event):
                    if i == 0:  # Player vs AI
                        self.game_state = GameState.DIFFICULTY_SELECT
                    elif i == 1:  # Player vs Player
                        self.start_pvp_game()
                    elif i == 2:  # Settings
                        self.game_state = GameState.SETTINGS
                    elif i == 3:  # Hint
                        self.game_state = GameState.HINT_SCREEN
                    elif i == 4:  # Exit
                        self.exit_game()
                        
        elif self.game_state == GameState.SETTINGS:
            for i, button in enumerate(self.settings_buttons):
                if button.is_clicked(pos, event):
                    if i == 0:
                        self.current_setting = "Player X"
                        self.name_input_box.text = self.player_x_name
                        self.game_state = GameState.NAME_INPUT
                    elif i == 1:
                        self.current_setting = "Player O"
                        self.name_input_box.text = self.player_o_name
                        self.game_state = GameState.NAME_INPUT
                    elif i == 2:
                        self.current_setting = "X"
                        self.game_state = GameState.COLOR_PICKER
                    elif i == 3:
                        self.current_setting = "O"
                        self.game_state = GameState.COLOR_PICKER
                    elif i == 4:
                        self.game_state = GameState.MENU

        elif self.game_state == GameState.DIFFICULTY_SELECT:
            for i, button in enumerate(self.difficulty_buttons):
                if button.is_clicked(pos, event):
                    if i == 4:  # Back
                        self.game_state = GameState.MENU
                    else:
                        difficulties = [Difficulty.EASY, Difficulty.MEDIUM, 
                                    Difficulty.HARD, Difficulty.IMPOSSIBLE]
                        self.ai_difficulty = difficulties[i]
                        self.game_state = GameState.FIRST_TURN_SELECT

        elif self.game_state == GameState.FIRST_TURN_SELECT:
            for i, button in enumerate(self.first_turn_buttons):
                if button.is_clicked(pos, event):
                    if i == 2:  # Back
                        self.game_state = GameState.DIFFICULTY_SELECT
                    else:
                        self.start_ai_game('PLAYER' if i == 0 else 'AI')

        elif self.game_state == GameState.PLAYING:
            # Don't allow player to click when AI is making a move
            if self.game_mode == 'AI' and (self.ai_thinking or self.current_player == PLAYER_O):
                return
                
            if 50 <= pos[0] <= CELL_SIZE * BOARD_SIZE + 50 and 50 <= pos[1] <= CELL_SIZE * BOARD_SIZE + 50:
                col = (pos[0] - 50) // CELL_SIZE
                row = (pos[1] - 50) // CELL_SIZE
                index = row * BOARD_SIZE + col

                if self.board[index] == EMPTY:
                    if self.game_mode == 'AI' and self.current_player == PLAYER_O:
                        # In AI mode, player should not be able to play as O
                        pass
                    else:
                        # Place the current player's mark
                        self.board[index] = self.current_player
                        self.winner = self.check_winner()

                        if not self.winner:
                            # Switch players
                            self.current_player = PLAYER_O if self.current_player == PLAYER_X else PLAYER_X
                            
                            # If AI mode and it's AI's turn, make AI move
                            if self.game_mode == 'AI' and self.current_player == PLAYER_O:
                                self.ai_move()

                        if self.winner:
                            if self.winner != "DRAW":
                                self.score[self.winner] += 1
                            self.game_state = GameState.GAME_OVER

            menu_button = Button(WINDOW_WIDTH - 120, 10, 100, 30, "Menu")
            if menu_button.is_clicked(pos, event):
                self.reset_score()  # Reset score when returning to main menu
                self.game_state = GameState.MENU

        # In the handle_click method, find the section for GameState.GAME_OVER
        elif self.game_state == GameState.GAME_OVER:
            for i, button in enumerate(self.game_over_buttons):
                if button.is_clicked(pos, event):
                    if i == 0:  # Play Again button
                        self.reset_game()
                        self.game_state = GameState.PLAYING
                        
                        # Fix: Reset AI thinking state and make sure the correct player starts
                        self.ai_thinking = False
                        
                        # If AI mode and AI should go first (when player was O last), make AI move
                        if self.game_mode == 'AI' and self.current_player == PLAYER_O:
                            self.ai_move()
                            
                    elif i == 1:  # Main Menu button
                        self.reset_score()
                        self.game_state = GameState.MENU

        elif self.game_state == GameState.HINT_SCREEN:
            if self.hint_back_button.is_clicked(pos, event):
                self.game_state = GameState.MENU
            
            # Handle scroll bar dragging
            if event.type == pygame.MOUSEBUTTONDOWN:
                if hasattr(self, 'scroll_thumb_rect') and self.scroll_thumb_rect.collidepoint(pos):
                    self.hint_scroll_dragging = True
                    self.drag_start_y = pos[1]
                    self.drag_start_scroll = self.hint_scroll_pos
            
            elif event.type == pygame.MOUSEBUTTONUP:
                self.hint_scroll_dragging = False
            
            elif event.type == pygame.MOUSEMOTION and self.hint_scroll_dragging:
                if hasattr(self, 'scroll_thumb_rect'):
                    content_height = 600
                    viewport_height = WINDOW_HEIGHT - 180 - 80
                    max_scroll = max(0, content_height - viewport_height)
                    
                    delta_y = pos[1] - self.drag_start_y
                    scroll_ratio = delta_y / viewport_height
                    self.hint_scroll_pos = max(0, min(max_scroll, self.drag_start_scroll + scroll_ratio * content_height))

        elif self.game_state == GameState.COLOR_PICKER and event.type == pygame.MOUSEBUTTONDOWN:
            new_color = self.color_picker.get_color_at_pos(pos)
            if new_color:
                self.color_picker.color = new_color

            for i, button in enumerate(self.color_picker_buttons):
                if button.is_clicked(pos, event):
                    if i == 0:
                        if self.current_setting == "X":
                            self.player_x_color = self.color_picker.color
                        else:
                            self.player_o_color = self.color_picker.color
                        self.game_state = GameState.SETTINGS
                    elif i == 1:
                        self.game_state = GameState.SETTINGS

    def start_ai_game(self, first_turn):
        """Start a game against AI"""
        self.game_mode = 'AI'
        self.player_o_name = "AI"  # Always show as AI in this mode
        self.current_player = PLAYER_O if first_turn == 'AI' else PLAYER_X
        self.reset_game()
        self.game_state = GameState.PLAYING
        
        if first_turn == 'AI':
            self.ai_move()

    def start_pvp_game(self):
        """Start a player vs player game"""
        self.game_mode = 'PVP'
        self.player_o_name = self.original_player_o_name  # Use the original name in PvP mode
        self.current_player = PLAYER_X
        self.reset_game()
        self.game_state = GameState.PLAYING

    def exit_game(self):
        """Exit the game gracefully"""
        pygame.quit()
        sys.exit()

    def run(self):
        """Main game loop"""
        while True:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit_game()

                # Handle scroll wheel in hint screen
                if self.game_state == GameState.HINT_SCREEN and event.type == pygame.MOUSEWHEEL:
                    content_height = 600
                    viewport_height = WINDOW_HEIGHT - 180 - 80
                    max_scroll = max(0, content_height - viewport_height)
                    self.hint_scroll_pos = max(0, min(max_scroll, self.hint_scroll_pos - event.y * 20))

                if self.game_state == GameState.NAME_INPUT:
                    self.handle_name_input(event)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(mouse_pos, event)

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.game_state in [
                            GameState.PLAYING,
                            GameState.COLOR_PICKER,
                            GameState.NAME_INPUT,
                            GameState.HINT_SCREEN,
                            GameState.DIFFICULTY_SELECT,
                            GameState.FIRST_TURN_SELECT
                        ]:
                            if self.game_state == GameState.PLAYING:
                                self.reset_score()  # Reset score when returning to main menu
                            self.game_state = GameState.MENU
                    elif event.key == pygame.K_r and self.game_state == GameState.PLAYING:
                        self.reset_game()

            # Hover state updates
            if self.game_state == GameState.MENU:
                for button in self.menu_buttons:
                    button.check_hover(mouse_pos)
            elif self.game_state == GameState.SETTINGS:
                for button in self.settings_buttons:
                    button.check_hover(mouse_pos)
            elif self.game_state == GameState.COLOR_PICKER:
                for button in self.color_picker_buttons:
                    button.check_hover(mouse_pos)
            elif self.game_state == GameState.NAME_INPUT:
                for button in self.name_input_buttons:
                    button.check_hover(mouse_pos)
            elif self.game_state == GameState.GAME_OVER:
                for button in self.game_over_buttons:
                    button.check_hover(mouse_pos)
            elif self.game_state == GameState.HINT_SCREEN:
                self.hint_back_button.check_hover(mouse_pos)
            elif self.game_state == GameState.DIFFICULTY_SELECT:
                for button in self.difficulty_buttons:
                    button.check_hover(mouse_pos)
            elif self.game_state == GameState.FIRST_TURN_SELECT:
                for button in self.first_turn_buttons:
                    button.check_hover(mouse_pos)

            self.draw_board()
            self.clock.tick(60)

def main():
    rclpy.init()
    game = TicTacToe()
    game.run()
    game.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
