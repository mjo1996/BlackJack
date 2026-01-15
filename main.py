import json
import pygame
from pygame_cards.classics import CardSets
from pygame_cards.set import CardsSet
from enum import Enum
from datetime import datetime, timedelta


class GameState(Enum):
    BETTING = 1
    PLAYING = 2
    DEALER_TURN = 3
    OUTCOME = 4


class BlackjackController:
    def __init__(self):
        self.game_state = GameState.BETTING
        self.deck = None
        self.player_hand = []
        self.split_active = False
        self.split_hands = []
        self.current_split_index = 0
        self.split_finished = []
        self.dealer_hand = []
        self.coins = 0
        self.current_bet = 0
        self.last_bonus_time = datetime.now()
        self.message = ""
        self.message_time = 0
        
        # UI elements
        self.bet_buttons = []
        self.hit_button = None
        self.stand_button = None
        self.double_button = None
        self.split_button = None
        self.surrender_button = None
        
        # Colors
        self.GREEN = (0, 128, 0)
        self.RED = (200, 0, 0)
        self.ORANGE = (255, 165, 0)
        self.YELLOW = (184, 134, 11)
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (128, 128, 128)
        self.PURPLE = (128, 0, 128)
    
    def build_objects(self):
        """Build game objects from settings"""
        self.coins = self.settings_json.get("game", {}).get("initial_coins", 1000)
        self.bet_amounts = self.settings_json.get("game", {}).get("bet_amounts", [1000, 500, 250, 100, 50, 25, 10, 5, 2.5, 1, 0.1])
        self.num_decks = self.settings_json.get("game", {}).get("num_decks", 6)
        # Create deck as a CardsSet composed of num_decks standard 52-card sets
        self.deck = CardsSet()
        for _ in range(self.num_decks):
            # CardSets.n52 returns a fresh cards set
            self.deck.extend(CardSets.n52)
        self.deck.shuffle()
        # Ensure card graphics sizes match settings
        card_size = tuple(self.settings_json.get("card", {}).get("size", [80, 120]))
        for c in self.deck:
            c.graphics.size = card_size
        
        # Create bet buttons
        self._create_bet_buttons()
    
    def start_game(self):
        """Start the game"""
        self.game_state = GameState.BETTING
        self.player_hand = []
        self.dealer_hand = []
        self.current_bet = 0
        self.message = "Place your bet"
    
    def execute_game(self):
        """Execute game logic"""
        self.check_hourly_bonus()
        # Immediate bust resolution: if player's hand exceeds 21 during their turn,
        # resolve as dealer win. If dealer exceeds 21 during dealer turn, resolve as player win.
        if self.game_state == GameState.PLAYING and self.player_hand:
            if self._hand_value(self.player_hand) > 21:
                self.game_state = GameState.OUTCOME
                # Use _determine_outcome for consistent messaging (it will detect player bust)
                self._determine_outcome()

        if self.game_state == GameState.DEALER_TURN and self.dealer_hand:
            if self._hand_value(self.dealer_hand) > 21:
                self.game_state = GameState.OUTCOME
                # Dealer busted — determine outcome to award coins
                self._determine_outcome()
    
    def process_mouse_events(self, mouse_button, mouse_pos):
        """Handle mouse clicks"""
        if self.game_state == GameState.BETTING:
            for button in self.bet_buttons:
                if button['rect'].collidepoint(mouse_pos):
                    self.place_bet(button['amount'])
        
        elif self.game_state == GameState.PLAYING:
            if self.hit_button.collidepoint(mouse_pos):
                self.player_hit()
            elif self.stand_button.collidepoint(mouse_pos):
                self.player_stand()
            elif self.double_button.collidepoint(mouse_pos) and len(self.player_hand) == 2:
                self.player_double()
            elif self.split_button.collidepoint(mouse_pos) and self._can_split(self.player_hand):
                self.player_split()
            elif self.surrender_button.collidepoint(mouse_pos):
                self.player_surrender()
        
        elif self.game_state == GameState.OUTCOME:
            # Any click proceeds to next hand
            self.reset_hand()
    
    def restart_game(self):
        """Restart the game"""
        self.coins = self.settings_json.get("game", {}).get("initial_coins", 1000)
        self.player_hand = []
        self.dealer_hand = []
        self.current_bet = 0
        self.game_state = GameState.BETTING
        self.message = "Place your bet"
    
    def _create_bet_buttons(self):
        """Create betting option buttons"""
        button_width = 80
        button_height = 40
        start_x = 50
        start_y = self.app.height - 150
        spacing = 10
        
        self.bet_buttons = []
        for i, amount in enumerate(self.bet_amounts):
            x = start_x + (i % 6) * (button_width + spacing)
            y = start_y + (i // 6) * (button_height + spacing)
            
            button_rect = pygame.Rect(x, y, button_width, button_height)
            self.bet_buttons.append({'rect': button_rect, 'amount': amount})
    
    def _create_action_buttons(self):
        """Create action buttons for player turn"""
        button_width = 100
        button_height = 50
        button_y = self.app.height - 80
        
        spacing = 20
        start_x = (self.app.width - (5 * button_width + 4 * spacing)) // 2
        
        self.hit_button = pygame.Rect(start_x, button_y, button_width, button_height)
        self.stand_button = pygame.Rect(start_x + button_width + spacing, button_y, button_width, button_height)
        self.double_button = pygame.Rect(start_x + 2 * (button_width + spacing), button_y, button_width, button_height)
        self.split_button = pygame.Rect(start_x + 3 * (button_width + spacing), button_y, button_width, button_height)
        self.surrender_button = pygame.Rect(start_x + 4 * (button_width + spacing), button_y, button_width, button_height)
    
    def _card_value(self, card):
        """Get numeric value of a card"""
        # Card from pygame_cards.classics stores its number in `number` attribute
        rank = getattr(card, 'number', None)

        # Helper to check enum Level or raw string for Ace
        def _is_ace(r):
            if r is None:
                return False
            # Enum with .value == 'A'
            if hasattr(r, 'value') and r.value == 'A':
                return True
            if isinstance(r, str) and r == 'A':
                return True
            return False

        if _is_ace(rank):
            return 11

        if isinstance(rank, int):
            return rank

        # Face cards may be enums with .value 'J','Q','K' or strings
        val = getattr(rank, 'value', None) if hasattr(rank, 'value') else rank
        if isinstance(val, str) and val in ['J', 'Q', 'K']:
            return 10

        try:
            return int(rank)
        except Exception:
            return 0
    
    def _hand_value(self, hand):
        """Calculate best value of a hand"""
        total = 0
        aces = 0
        
        for card in hand:
            value = self._card_value(card)
            # Count aces robustly (handle Level enums)
            r = getattr(card, 'number', None)
            if (hasattr(r, 'value') and r.value == 'A') or (isinstance(r, str) and r == 'A'):
                aces += 1
            total += value
        
        # Adjust for aces if busted
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        
        return total
    
    def _is_blackjack(self, hand):
        """Check if hand is blackjack (21 on first two cards)"""
        return len(hand) == 2 and self._hand_value(hand) == 21
    
    def _can_split(self, hand):
        """Check if hand can be split (two cards of same rank)"""
        if len(hand) != 2:
            return False
        # Allow split when numbers are identical (e.g., two Aces)
        n0 = getattr(hand[0], 'number', None)
        n1 = getattr(hand[1], 'number', None)
        if n0 == n1:
            return True

        # Also allow splitting any two ten-value cards (10, J, Q, K combinations)
        try:
            v0 = self._card_value(hand[0])
            v1 = self._card_value(hand[1])
            if v0 == 10 and v1 == 10:
                return True
        except Exception:
            pass

        return False
    
    def _reshuffle_if_needed(self):
        """Reshuffle deck if it gets too small"""
        if len(self.deck) < 20:
            self.deck = CardsSet()
            for _ in range(self.num_decks):
                self.deck.extend(CardSets.n52)
            self.deck.shuffle()
            card_size = tuple(self.settings_json.get("card", {}).get("size", [80, 120]))
            for c in self.deck:
                c.graphics.size = card_size
    
    def deal_initial_cards(self):
        """Deal initial two cards to player and dealer"""
        self._reshuffle_if_needed()
        # Draw returns a CardsSet; take first element
        self.player_hand = [self.deck.draw(1)[0], self.deck.draw(1)[0]]
        self.dealer_hand = [self.deck.draw(1)[0], self.deck.draw(1)[0]]
        
        if self._is_blackjack(self.player_hand):
            self.game_state = GameState.OUTCOME
            self.message = "Blackjack!"
        else:
            self.game_state = GameState.PLAYING
            self._create_action_buttons()
    
    def player_hit(self):
        """Player draws a card"""
        # If split is active, draw on current split hand
        if self.split_active:
            hand = self.split_hands[self.current_split_index]
            if self._hand_value(hand) < 21:
                self._reshuffle_if_needed()
                hand.append(self.deck.draw(1)[0])

                if self._hand_value(hand) > 21:
                    self.split_finished[self.current_split_index] = True
                    self.message = "Bust!"
                    # Move to next hand or dealer
                    if all(self.split_finished):
                        self.game_state = GameState.DEALER_TURN
                        self.dealer_play()
                    else:
                        for i in range(len(self.split_hands)):
                            if not self.split_finished[i]:
                                self.current_split_index = i
                                break
                elif self._hand_value(hand) == 21:
                    # finish this hand and move on
                    self.split_finished[self.current_split_index] = True
                    if all(self.split_finished):
                        self.game_state = GameState.DEALER_TURN
                        self.dealer_play()
                    else:
                        for i in range(len(self.split_hands)):
                            if not self.split_finished[i]:
                                self.current_split_index = i
                                break
        else:
            if self._hand_value(self.player_hand) < 21:
                self._reshuffle_if_needed()
                self.player_hand.append(self.deck.draw(1)[0])
                
                if self._hand_value(self.player_hand) > 21:
                    self.game_state = GameState.OUTCOME
                    self.message = "Bust! You lose."
                elif self._hand_value(self.player_hand) == 21:
                    # Automatically stand on 21
                    self.game_state = GameState.DEALER_TURN
                    self.dealer_play()
    
    def player_stand(self):
        """Player stands"""
        if self.split_active:
            # mark current split hand finished and move to next or dealer
            self.split_finished[self.current_split_index] = True
            if all(self.split_finished):
                self.game_state = GameState.DEALER_TURN
                self.dealer_play()
            else:
                for i in range(len(self.split_hands)):
                    if not self.split_finished[i]:
                        self.current_split_index = i
                        break
        else:
            self.game_state = GameState.DEALER_TURN
            self.dealer_play()
    
    def player_double(self):
        """Player doubles their bet and gets one more card"""
        # If splitting, operate on current split hand
        if self.split_active:
            hand = self.split_hands[self.current_split_index]
            if len(hand) == 2 and self.coins >= self.current_bet:
                self.coins -= self.current_bet
                # draw one card and then mark this hand finished
                hand.append(self.deck.draw(1)[0])
                if self._hand_value(hand) > 21:
                    self.split_finished[self.current_split_index] = True
                else:
                    self.split_finished[self.current_split_index] = True

                # move to next hand or dealer
                if all(self.split_finished):
                    self.game_state = GameState.DEALER_TURN
                    self.dealer_play()
                else:
                    # advance to next unfinished hand
                    for i in range(len(self.split_hands)):
                        if not self.split_finished[i]:
                            self.current_split_index = i
                            break
        else:
            if self.coins >= self.current_bet:
                self.coins -= self.current_bet
                self.current_bet *= 2
                self.player_hit()
                if self.game_state == GameState.PLAYING:
                    self.game_state = GameState.DEALER_TURN
                    self.dealer_play()
    
    def player_split(self):
        """Perform a split: create two hands and continue play on first hand.
        Basic rules implemented: require exactly two cards of same rank and enough coins
        to place the second bet. Bets for split hands equal to `current_bet`.
        """
        if not self._can_split(self.player_hand):
            self.message = "Cannot split"
            return

        # Require enough coins for doubling the bet (one extra current_bet)
        if self.coins < self.current_bet:
            self.message = "Not enough coins to split"
            return

        # Deduct second bet
        self.coins -= self.current_bet

        # Create two hands each starting with one of the cards
        card0, card1 = self.player_hand[0], self.player_hand[1]
        self.split_hands = [[card0], [card1]]
        self.split_finished = [False, False]
        self.current_split_index = 0
        self.split_active = True

        # Draw one card to each hand
        self._reshuffle_if_needed()
        self.split_hands[0].append(self.deck.draw(1)[0])
        self.split_hands[1].append(self.deck.draw(1)[0])

        # Start playing first split hand
        self.game_state = GameState.PLAYING
        self._create_action_buttons()
    
    def player_surrender(self):
        """Player surrenders and gets half their bet back"""
        self.coins += self.current_bet / 2
        self.game_state = GameState.OUTCOME
        self.message = "You surrendered!"
    
    def dealer_play(self):
        """Dealer plays their hand"""
        while self._hand_value(self.dealer_hand) < 17:
            self._reshuffle_if_needed()
            self.dealer_hand.append(self.deck.draw(1)[0])
        
        self.game_state = GameState.OUTCOME
        self._determine_outcome()
    
    def _determine_outcome(self):
        """Determine the winner and update coins"""
        dealer_value = self._hand_value(self.dealer_hand)

        if self.split_active:
            # Evaluate each split hand independently using the same dealer hand
            results = []
            for hand in self.split_hands:
                player_value = self._hand_value(hand)
                # Blackjack checks: player blackjack pays 1.5x (i.e., add 2.5x total), tie if dealer also blackjack
                player_blackjack = self._is_blackjack(hand)
                dealer_blackjack = self._is_blackjack(self.dealer_hand)
                if player_blackjack:
                    if dealer_blackjack:
                        results.append(("push", self.current_bet))
                    else:
                        results.append(("blackjack", self.current_bet * 2.5))
                elif player_value > 21:
                    results.append(("lose", 0))
                elif dealer_value > 21:
                    results.append(("win", self.current_bet * 2))
                elif player_value > dealer_value:
                    results.append(("win", self.current_bet * 2))
                elif dealer_value > player_value:
                    results.append(("lose", 0))
                else:
                    results.append(("push", self.current_bet))

            # Sum payouts and create a message summary
            payout = 0
            msgs = []
            for i, (res, amt) in enumerate(results):
                payout += amt
                msgs.append(f"Hand {i+1}: {res}")

            if payout:
                self.coins += payout

            self.message = " | ".join(msgs)
            # reset split state after outcome
            self.split_active = False
            self.split_hands = []
            self.split_finished = []
            self.current_split_index = 0
            self.current_bet = 0
        else:
            player_value = self._hand_value(self.player_hand)
            player_blackjack = self._is_blackjack(self.player_hand)
            dealer_blackjack = self._is_blackjack(self.dealer_hand)

            if player_blackjack:
                if dealer_blackjack:
                    self.message = "Push! Both blackjack."
                    self.coins += self.current_bet
                else:
                    self.message = "Blackjack! You win 1.5x."
                    self.coins += self.current_bet * 2.5
            elif player_value > 21:
                self.message = "You bust! Dealer wins."
            elif dealer_value > 21:
                self.message = "Dealer busts! You win!"
                self.coins += self.current_bet * 2
            elif player_value > dealer_value:
                self.message = "You win!"
                self.coins += self.current_bet * 2
            elif dealer_value > player_value:
                self.message = "Dealer wins!"
            else:
                self.message = "Push! Tie."
                self.coins += self.current_bet
    
    def place_bet(self, amount):
        """Place a bet"""
        if self.coins >= amount:
            self.current_bet = amount
            self.coins -= amount
            self.deal_initial_cards()
        else:
            self.message = "Not enough coins!"
    
    def check_hourly_bonus(self):
        """Check if player can get hourly bonus"""
        now = datetime.now()
        hourly_bonus = self.settings_json.get("game", {}).get("hourly_bonus", 20)
        if now - self.last_bonus_time >= timedelta(hours=1):
            self.coins += hourly_bonus
            self.last_bonus_time = now
            self.message = f"You got {hourly_bonus} coins!"
    
    def reset_hand(self):
        """Reset for next hand"""
        self.player_hand = []
        self.dealer_hand = []
        self.current_bet = 0
        self.game_state = GameState.BETTING
        self.message = "Place your bet"
    
    def draw(self):
        """Draw game screen"""
        screen = self.app.screen
        font_large = pygame.font.Font(None, 48)
        font_medium = pygame.font.Font(None, 36)
        font_small = pygame.font.Font(None, 24)
        
        if self.game_state == GameState.BETTING:
            title = font_large.render("Place your bet", True, self.WHITE)
            screen.blit(title, (self.app.width // 2 - title.get_width() // 2, 50))
            
            # Draw bet buttons (use green for enabled buttons so text is visible)
            for button in self.bet_buttons:
                amount = button['amount']
                color = self.GRAY if self.coins < amount else self.GREEN
                self._draw_button(screen, button['rect'], f"{amount}", color)
            
            # Draw coin display (rounded to 3 decimals)
            coin_text = font_medium.render(f"Coins: {self.coins:.3f}", True, self.WHITE)
            screen.blit(coin_text, (50, 150))
        
        elif self.game_state == GameState.PLAYING or self.game_state == GameState.OUTCOME:
            # Draw dealer hand
            dealer_text = font_medium.render("Dealer", True, self.WHITE)
            screen.blit(dealer_text, (50, 50))
            
            if self.game_state == GameState.PLAYING:
                self._draw_cards(screen, self.dealer_hand, 50, 100, hide_first=True)
            else:
                self._draw_cards(screen, self.dealer_hand, 50, 100, hide_first=False)

            # During PLAYING we show the value of the visible dealer card (index 1).
            if self.game_state == GameState.PLAYING:
                if len(self.dealer_hand) > 1:
                    dealer_value = self._hand_value([self.dealer_hand[1]])
                else:
                    dealer_value = self._hand_value([self.dealer_hand[0]])
            else:
                dealer_value = self._hand_value(self.dealer_hand)
            dealer_value_text = font_small.render(f"Value: {dealer_value}", True, self.WHITE)
            screen.blit(dealer_value_text, (50, 250))
            
            # Draw player hand(s)
            player_text = font_medium.render("You", True, self.WHITE)
            screen.blit(player_text, (50, 350))

            if self.split_active and self.split_hands:
                # Draw both split hands side by side and highlight current
                self._draw_cards(screen, self.split_hands[0], 50, 400)
                self._draw_cards(screen, self.split_hands[1], 350, 400)

                # show value for current hand
                hand = self.split_hands[self.current_split_index]
                player_value = self._hand_value(hand)
                player_value_text = font_small.render(f"Value: {player_value}", True, self.WHITE)
                screen.blit(player_value_text, (50 + self.current_split_index * 300, 550))
            else:
                self._draw_cards(screen, self.player_hand, 50, 400)
                player_value = self._hand_value(self.player_hand)
                player_value_text = font_small.render(f"Value: {player_value}", True, self.WHITE)
                screen.blit(player_value_text, (50, 550))
            
            # Draw bet
            bet_text = font_small.render(f"Bet: {self.current_bet}", True, self.WHITE)
            screen.blit(bet_text, (self.app.width - 250, 50))

            # Draw coins (rounded to 3 decimals)
            coin_text = font_small.render(f"Coins: {self.coins:.3f}", True, self.WHITE)
            screen.blit(coin_text, (self.app.width - 250, 100))
            
            if self.game_state == GameState.PLAYING:
                # Draw action buttons
                self._draw_button(screen, self.hit_button, "Hit", self.GREEN)
                self._draw_button(screen, self.stand_button, "Stand", self.RED)
                
                # Only show double if have exactly 2 cards
                if len(self.player_hand) == 2:
                    self._draw_button(screen, self.double_button, "Double", self.ORANGE)
                
                # Only show split if can split
                if self._can_split(self.player_hand):
                    self._draw_button(screen, self.split_button, "Split", self.YELLOW)
                
                # Draw surrender button (only on first draw, 2 cards, and not after split)
                if len(self.player_hand) == 2 and not self.split_active:
                    self._draw_button(screen, self.surrender_button, "Surrender", self.PURPLE)
            
            elif self.game_state == GameState.OUTCOME:
                # Draw outcome message
                message_text = font_large.render(self.message, True, self.WHITE)
                screen.blit(message_text, (self.app.width // 2 - message_text.get_width() // 2, 700))
                
                next_text = font_small.render("Click to continue...", True, self.WHITE)
                screen.blit(next_text, (self.app.width // 2 - next_text.get_width() // 2, 750))
    
    def _draw_cards(self, screen, cards, start_x, start_y, hide_first=False):
        """Draw cards on screen using pygame_cards"""
        spacing = 20
        card_size = tuple(self.settings_json.get("card", {}).get("size", [80, 120]))
        for i, card in enumerate(cards):
            x = start_x + i * (card_size[0] + spacing)
            y = start_y

            if hide_first and i == 0:
                # Draw card back as a filled rect
                back = pygame.Surface(card_size)
                back.fill((50, 50, 50))
                pygame.draw.rect(back, self.WHITE, back.get_rect(), 2)
                screen.blit(back, (x, y))
            else:
                # Draw card front using pygame_cards graphics
                surf = card.graphics.surface
                screen.blit(surf, (x, y))
    
    def _draw_button(self, screen, button, label, color):
        """Draw a button"""
        # Accept either a pygame.Rect or a dict with 'rect'
        rect = button['rect'] if isinstance(button, dict) else button
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, self.WHITE, rect, 2)

        font_small = pygame.font.Font(None, 24)
        # choose contrasting text color based on button fill
        try:
            avg = (rect_color := color)[0] + rect_color[1] + rect_color[2]
            avg = avg / 3
        except Exception:
            avg = 0
        text_color = self.BLACK if avg > 180 else self.WHITE
        text = font_small.render(str(label), True, text_color)
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)


class GameApp:
    def __init__(self, json_path: str, game_controller: BlackjackController):
        with open(json_path, 'r') as f:
            self.settings_json = json.load(f)

        win = self.settings_json.get('window', {})
        size = tuple(win.get('size', (1200, 800)))
        title = win.get('title', 'Game')
        bg = tuple(win.get('background_color', (34, 139, 34)))

        pygame.init()
        self.width, self.height = size
        self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        pygame.display.set_caption(title)
        self.background = bg
        self.clock = pygame.time.Clock()

        self.card = lambda: None
        self.card.size = tuple(self.settings_json.get('card', {}).get('size', [80, 120]))

        self.controller = game_controller
        # Provide references required by controller
        self.controller.app = self
        self.controller.settings_json = self.settings_json
        self.controller.build_objects()
        self.controller.start_game()

    def execute(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.width, self.height = event.size
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    self.controller._create_bet_buttons()
                    self.controller._create_action_buttons()
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.controller.process_mouse_events(event.button, event.pos)

            self.screen.fill(self.background)
            self.controller.execute_game()
            self.controller.draw()

            pygame.display.flip()
            self.clock.tick(30)


def main():
    """Main entry point"""
    app = GameApp(json_path='settings.json', game_controller=BlackjackController())
    app.execute()


if __name__ == "__main__":
    main()
