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
        
        # Repeat bet functionality
        self.repeat_bet_active = False
        self.repeat_bet_amount = 0
        
        # UI elements
        self.bet_buttons = []
        self.hit_button = None
        self.stand_button = None
        self.double_button = None
        self.split_button = None
        self.surrender_button = None
        self.repeat_checkbox = None
        self.repeat_exit_button = None
        
        # Modern color palette
        self.DARK_GREEN = (0, 100, 0)  # Casino felt
        self.GOLD = (255, 215, 0)  # Gold accents
        self.LIGHT_GOLD = (255, 235, 150)
        self.GREEN = (0, 150, 0)  # Success/positive actions
        self.RED = (220, 20, 60)  # Crimson for stand/surrender
        self.ORANGE = (255, 140, 0)  # Dark orange for double
        self.YELLOW = (255, 200, 0)  # Bright yellow for split
        self.PURPLE = (138, 43, 226)  # Violet for surrender
        self.WHITE = (255, 255, 255)
        self.BLACK = (20, 20, 20)
        self.DARK_GRAY = (60, 60, 60)
        self.GRAY = (120, 120, 120)
        self.LIGHT_GRAY = (200, 200, 200)
        self.CARD_BACK_COLOR = (25, 25, 112)  # Midnight blue for card backs
    
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
            # Check repeat checkbox
            if self.repeat_checkbox and self.repeat_checkbox.collidepoint(mouse_pos):
                self.repeat_bet_active = not self.repeat_bet_active
            
            # Check bet buttons
            for button in self.bet_buttons:
                if button['rect'].collidepoint(mouse_pos):
                    self.place_bet(button['amount'])
        
        elif self.game_state == GameState.PLAYING:
            # Check repeat exit button
            if self.repeat_exit_button and self.repeat_exit_button.collidepoint(mouse_pos):
                self.repeat_bet_active = False
                self.repeat_bet_amount = 0
            elif self.hit_button.collidepoint(mouse_pos):
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
            # Check repeat exit button
            if self.repeat_exit_button and self.repeat_exit_button.collidepoint(mouse_pos):
                self.repeat_bet_active = False
                self.repeat_bet_amount = 0
            else:
                # Any other click proceeds to next hand
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
        button_width = 100
        button_height = 50
        start_x = 50
        start_y = self.app.height - 180
        spacing = 15
        
        self.bet_buttons = []
        for i, amount in enumerate(self.bet_amounts):
            x = start_x + (i % 6) * (button_width + spacing)
            y = start_y + (i // 6) * (button_height + spacing)
            
            button_rect = pygame.Rect(x, y, button_width, button_height)
            self.bet_buttons.append({'rect': button_rect, 'amount': amount})
    
    def _create_action_buttons(self):
        """Create action buttons for player turn"""
        button_width = 120
        button_height = 60
        button_y = self.app.height - 100
        
        spacing = 15
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
            
            # If repeat bet is active, remember this amount
            if self.repeat_bet_active:
                self.repeat_bet_amount = amount
            
            self.deal_initial_cards()
        else:
            self.message = "Not enough coins!"
    
    def check_hourly_bonus(self):
        """Check if player can get hourly bonus"""
        now = datetime.now()
        quarterly_bonus = self.settings_json.get("game", {}).get("quarterly_bonus", 100)
        if now - self.last_bonus_time >= timedelta(minutes=15):
            self.coins += quarterly_bonus
            self.last_bonus_time = now
            self.message = f"You got {quarterly_bonus} coins!"
    
    def reset_hand(self):
        """Reset for next hand"""
        self.player_hand = []
        self.dealer_hand = []
        self.current_bet = 0
        
        # If repeat bet is active, automatically place the same bet
        if self.repeat_bet_active and self.repeat_bet_amount > 0:
            if self.coins >= self.repeat_bet_amount:
                self.current_bet = self.repeat_bet_amount
                self.coins -= self.repeat_bet_amount
                self.deal_initial_cards()
            else:
                # Not enough coins for repeat bet, disable repeat mode
                self.repeat_bet_active = False
                self.repeat_bet_amount = 0
                self.game_state = GameState.BETTING
                self.message = "Not enough coins for repeat bet"
        else:
            self.game_state = GameState.BETTING
            self.message = "Place your bet"
    
    def draw(self):
        """Draw game screen"""
        screen = self.app.screen
        
        # Try to load a nicer font, fallback to default
        try:
            font_large = pygame.font.Font(pygame.font.get_default_font(), 56)
            font_medium = pygame.font.Font(pygame.font.get_default_font(), 40)
            font_small = pygame.font.Font(pygame.font.get_default_font(), 28)
            font_tiny = pygame.font.Font(pygame.font.get_default_font(), 20)
        except:
            font_large = pygame.font.Font(None, 56)
            font_medium = pygame.font.Font(None, 40)
            font_small = pygame.font.Font(None, 28)
            font_tiny = pygame.font.Font(None, 20)
        
        if self.game_state == GameState.BETTING:
            # Draw title with shadow effect
            title = font_large.render("Place Your Bet", True, self.GOLD)
            title_shadow = font_large.render("Place Your Bet", True, self.BLACK)
            title_x = self.app.width // 2 - title.get_width() // 2
            screen.blit(title_shadow, (title_x + 3, 53))
            screen.blit(title, (title_x, 50))
            
            # Create repeat bet checkbox if not exists
            if self.repeat_checkbox is None:
                checkbox_size = 30
                checkbox_x = self.app.width - 250
                checkbox_y = 140
                self.repeat_checkbox = pygame.Rect(checkbox_x, checkbox_y, checkbox_size, checkbox_size)
            
            # Draw repeat bet checkbox
            checkbox_bg = pygame.Rect(self.repeat_checkbox.x - 5, self.repeat_checkbox.y - 5, 
                                     self.repeat_checkbox.width + 10, self.repeat_checkbox.height + 10)
            checkbox_surf = pygame.Surface((checkbox_bg.width, checkbox_bg.height))
            checkbox_surf.set_alpha(180)
            checkbox_surf.fill((0, 0, 0))
            screen.blit(checkbox_surf, checkbox_bg)
            pygame.draw.rect(screen, self.GOLD, checkbox_bg, 2)
            
            # Draw checkbox border
            pygame.draw.rect(screen, self.GOLD, self.repeat_checkbox, 3)
            
            # Draw checkmark if active
            if self.repeat_bet_active:
                # Fill checkbox with gold
                pygame.draw.rect(screen, self.GOLD, self.repeat_checkbox)
                # Draw checkmark
                check_padding = 5
                # Draw checkmark lines
                pygame.draw.line(screen, self.BLACK,
                               (self.repeat_checkbox.left + check_padding, self.repeat_checkbox.centery),
                               (self.repeat_checkbox.centerx - 2, self.repeat_checkbox.bottom - check_padding), 3)
                pygame.draw.line(screen, self.BLACK,
                               (self.repeat_checkbox.centerx - 2, self.repeat_checkbox.bottom - check_padding),
                               (self.repeat_checkbox.right - check_padding, self.repeat_checkbox.top + check_padding), 3)
            
            # Draw "Repeat Bet" label
            repeat_label = font_tiny.render("Repeat Bet", True, self.GOLD)
            screen.blit(repeat_label, (self.repeat_checkbox.right + 10, self.repeat_checkbox.centery - repeat_label.get_height() // 2))
            
            # Draw bet buttons with modern styling
            for button in self.bet_buttons:
                amount = button['amount']
                is_enabled = self.coins >= amount
                color = self.DARK_GRAY if not is_enabled else self.GOLD
                self._draw_button_modern(screen, button['rect'], f"{amount}", color, is_enabled)
            
            # Draw coin display with gold styling
            coin_bg = pygame.Rect(40, 140, 300, 60)
            coin_surf = pygame.Surface((coin_bg.width, coin_bg.height))
            coin_surf.set_alpha(180)
            coin_surf.fill((0, 0, 0))
            screen.blit(coin_surf, coin_bg)
            pygame.draw.rect(screen, self.GOLD, coin_bg, 3)
            
            coin_text_str = f"Coins: {self.coins:.2f}"
            coin_text_surf, _ = self._get_fitted_text(coin_text_str, coin_bg.width - 20, coin_bg.height - 10, 40)
            coin_text = font_medium.render(coin_text_str, True, self.GOLD)
            # Scale if needed
            if coin_text.get_width() > coin_bg.width - 20:
                scale = (coin_bg.width - 20) / coin_text.get_width()
                new_size = int(font_medium.get_height() * scale)
                try:
                    font_coin = pygame.font.Font(pygame.font.get_default_font(), new_size)
                except:
                    font_coin = pygame.font.Font(None, new_size)
                coin_text = font_coin.render(coin_text_str, True, self.GOLD)
            coin_text_rect = coin_text.get_rect(center=coin_bg.center)
            screen.blit(coin_text, coin_text_rect)
        
        elif self.game_state == GameState.PLAYING or self.game_state == GameState.OUTCOME:
            # Draw dealer section with background
            dealer_bg = pygame.Rect(30, 30, self.app.width - 60, 280)
            dealer_surf = pygame.Surface((dealer_bg.width, dealer_bg.height))
            dealer_surf.set_alpha(100)
            dealer_surf.fill((0, 0, 0))
            screen.blit(dealer_surf, dealer_bg)
            pygame.draw.rect(screen, self.GOLD, dealer_bg, 2)
            
            dealer_text = font_medium.render("Dealer", True, self.GOLD)
            dealer_shadow = font_medium.render("Dealer", True, self.BLACK)
            screen.blit(dealer_shadow, (53, 53))
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
            screen.blit(dealer_value_text, (50, 270))
            
            # Draw player section with background
            player_bg = pygame.Rect(30, 330, self.app.width - 60, 280)
            player_surf = pygame.Surface((player_bg.width, player_bg.height))
            player_surf.set_alpha(100)
            player_surf.fill((0, 0, 0))
            screen.blit(player_surf, player_bg)
            pygame.draw.rect(screen, self.GOLD, player_bg, 2)
            
            player_text = font_medium.render("You", True, self.GOLD)
            player_shadow = font_medium.render("You", True, self.BLACK)
            screen.blit(player_shadow, (53, 333))
            screen.blit(player_text, (50, 330))

            if self.split_active and self.split_hands:
                # Draw both split hands side by side and highlight current
                self._draw_cards(screen, self.split_hands[0], 50, 400)
                self._draw_cards(screen, self.split_hands[1], 350, 400)

                # Highlight current hand
                current_hand_x = 50 + self.current_split_index * 300
                highlight_rect = pygame.Rect(current_hand_x - 10, 390, 200, 140)
                highlight_surf = pygame.Surface((highlight_rect.width, highlight_rect.height))
                highlight_surf.set_alpha(50)
                highlight_surf.fill((255, 255, 0))
                screen.blit(highlight_surf, highlight_rect)
                pygame.draw.rect(screen, self.GOLD, highlight_rect, 3)

                # show value for current hand
                hand = self.split_hands[self.current_split_index]
                player_value = self._hand_value(hand)
                player_value_text = font_small.render(f"Value: {player_value}", True, self.WHITE)
                screen.blit(player_value_text, (current_hand_x, 570))
            else:
                self._draw_cards(screen, self.player_hand, 50, 400)
                player_value = self._hand_value(self.player_hand)
                player_value_text = font_small.render(f"Value: {player_value}", True, self.WHITE)
                screen.blit(player_value_text, (50, 570))
            
            # Draw info panel on the right
            info_panel = pygame.Rect(self.app.width - 280, 30, 250, 150)
            info_surf = pygame.Surface((info_panel.width, info_panel.height))
            info_surf.set_alpha(180)
            info_surf.fill((0, 0, 0))
            screen.blit(info_surf, info_panel)
            pygame.draw.rect(screen, self.GOLD, info_panel, 3)
            
            # Bet text - fit within panel
            bet_text_str = f"Bet: {self.current_bet:.2f}"
            bet_text = font_small.render(bet_text_str, True, self.GOLD)
            if bet_text.get_width() > info_panel.width - 20:
                scale = (info_panel.width - 20) / bet_text.get_width()
                new_size = int(font_small.get_height() * scale)
                try:
                    font_bet = pygame.font.Font(pygame.font.get_default_font(), new_size)
                except:
                    font_bet = pygame.font.Font(None, new_size)
                bet_text = font_bet.render(bet_text_str, True, self.GOLD)
            bet_text_rect = bet_text.get_rect(left=info_panel.left + 10, top=info_panel.top + 20)
            screen.blit(bet_text, bet_text_rect)

            # Coin text - fit within panel
            coin_text_str = f"Coins: {self.coins:.2f}"
            coin_text = font_small.render(coin_text_str, True, self.GOLD)
            if coin_text.get_width() > info_panel.width - 20:
                scale = (info_panel.width - 20) / coin_text.get_width()
                new_size = int(font_small.get_height() * scale)
                try:
                    font_coin = pygame.font.Font(pygame.font.get_default_font(), new_size)
                except:
                    font_coin = pygame.font.Font(None, new_size)
                coin_text = font_coin.render(coin_text_str, True, self.GOLD)
            coin_text_rect = coin_text.get_rect(left=info_panel.left + 10, top=info_panel.top + 60)
            screen.blit(coin_text, coin_text_rect)
            
            # Draw repeat bet exit button if repeat is active (bottom right of window)
            if self.repeat_bet_active:
                # Create exit button if not exists or update position if window resized
                exit_size = 40
                exit_x = self.app.width - exit_size - 20
                exit_y = self.app.height - exit_size - 20
                self.repeat_exit_button = pygame.Rect(exit_x, exit_y, exit_size, exit_size)
                
                # Draw exit button background
                exit_bg = pygame.Surface((self.repeat_exit_button.width, self.repeat_exit_button.height))
                exit_bg.set_alpha(200)
                exit_bg.fill(self.RED)
                screen.blit(exit_bg, self.repeat_exit_button)
                pygame.draw.rect(screen, self.WHITE, self.repeat_exit_button, 2)
                
                # Draw X mark
                padding = 10
                pygame.draw.line(screen, self.WHITE,
                               (self.repeat_exit_button.left + padding, self.repeat_exit_button.top + padding),
                               (self.repeat_exit_button.right - padding, self.repeat_exit_button.bottom - padding), 3)
                pygame.draw.line(screen, self.WHITE,
                               (self.repeat_exit_button.right - padding, self.repeat_exit_button.top + padding),
                               (self.repeat_exit_button.left + padding, self.repeat_exit_button.bottom - padding), 3)
                
                # Draw "Exit Repeat" label above exit button
                repeat_label = font_tiny.render("Exit", True, self.GOLD)
                label_x = self.repeat_exit_button.centerx - repeat_label.get_width() // 2
                label_y = self.repeat_exit_button.top - 20
                screen.blit(repeat_label, (label_x, label_y))
            
            if self.game_state == GameState.PLAYING:
                # Draw action buttons with modern styling
                self._draw_button_modern(screen, self.hit_button, "Hit", self.GREEN, True)
                self._draw_button_modern(screen, self.stand_button, "Stand", self.RED, True)
                
                # Determine if double button should be shown
                # For split hands: show only if current split hand has exactly 2 cards
                # For regular hand: show only if hand has exactly 2 cards
                can_double = False
                if self.split_active:
                    current_hand = self.split_hands[self.current_split_index]
                    can_double = len(current_hand) == 2 and self.coins >= self.current_bet
                else:
                    can_double = len(self.player_hand) == 2 and self.coins >= self.current_bet
                
                if can_double:
                    self._draw_button_modern(screen, self.double_button, "Double", self.ORANGE, True)
                
                # Only show split if can split (and not already split)
                if not self.split_active and self._can_split(self.player_hand):
                    self._draw_button_modern(screen, self.split_button, "Split", self.YELLOW, True)
                
                # Draw surrender button (only on first draw, 2 cards, and not after split)
                if len(self.player_hand) == 2 and not self.split_active:
                    self._draw_button_modern(screen, self.surrender_button, "Surrender", self.PURPLE, True)
            
            elif self.game_state == GameState.OUTCOME:
                # Draw outcome message with background
                outcome_bg = pygame.Rect(self.app.width // 2 - 400, 650, 800, 120)
                outcome_surf = pygame.Surface((outcome_bg.width, outcome_bg.height))
                outcome_surf.set_alpha(200)
                outcome_surf.fill((0, 0, 0))
                screen.blit(outcome_surf, outcome_bg)
                pygame.draw.rect(screen, self.GOLD, outcome_bg, 4)
                
                # Fit message text within outcome box
                message_text = font_large.render(self.message, True, self.GOLD)
                if message_text.get_width() > outcome_bg.width - 40:
                    scale = (outcome_bg.width - 40) / message_text.get_width()
                    new_size = int(font_large.get_height() * scale)
                    try:
                        font_msg = pygame.font.Font(pygame.font.get_default_font(), new_size)
                    except:
                        font_msg = pygame.font.Font(None, new_size)
                    message_text = font_msg.render(self.message, True, self.GOLD)
                
                message_shadow = message_text.copy()
                message_shadow.fill(self.BLACK)
                message_shadow.set_alpha(200)
                
                msg_rect = message_text.get_rect(center=(outcome_bg.centerx, outcome_bg.centery - 15))
                screen.blit(message_shadow, (msg_rect.x + 3, msg_rect.y + 3))
                screen.blit(message_text, msg_rect)
                
                # Fit "Click to continue" text
                next_text = font_small.render("Click to continue...", True, self.LIGHT_GRAY)
                if next_text.get_width() > outcome_bg.width - 40:
                    scale = (outcome_bg.width - 40) / next_text.get_width()
                    new_size = int(font_small.get_height() * scale)
                    try:
                        font_next = pygame.font.Font(pygame.font.get_default_font(), new_size)
                    except:
                        font_next = pygame.font.Font(None, new_size)
                    next_text = font_next.render("Click to continue...", True, self.LIGHT_GRAY)
                next_rect = next_text.get_rect(center=(outcome_bg.centerx, outcome_bg.bottom - 25))
                screen.blit(next_text, next_rect)
    
    def _draw_cards(self, screen, cards, start_x, start_y, hide_first=False):
        """Draw cards on screen using pygame_cards"""
        spacing = 25
        card_size = tuple(self.settings_json.get("card", {}).get("size", [80, 120]))
        for i, card in enumerate(cards):
            x = start_x + i * (card_size[0] + spacing)
            y = start_y

            if hide_first and i == 0:
                # Draw card back with modern design
                back = pygame.Surface(card_size)
                back.fill(self.CARD_BACK_COLOR)
                # Add border
                pygame.draw.rect(back, self.WHITE, back.get_rect(), 3)
                # Add pattern
                pattern_color = (50, 50, 150)
                for j in range(3):
                    for k in range(4):
                        pygame.draw.circle(back, pattern_color, 
                                         (20 + j * 30, 20 + k * 30), 8)
                # Add shadow effect
                shadow = pygame.Surface((card_size[0] + 4, card_size[1] + 4))
                shadow.set_alpha(100)
                shadow.fill((0, 0, 0))
                screen.blit(shadow, (x - 2, y + 2))
                screen.blit(back, (x, y))
            else:
                # Draw card front using pygame_cards graphics with shadow
                shadow = pygame.Surface((card_size[0] + 4, card_size[1] + 4))
                shadow.set_alpha(100)
                shadow.fill((0, 0, 0))
                screen.blit(shadow, (x - 2, y + 2))
                surf = card.graphics.surface
                screen.blit(surf, (x, y))
    
    def _draw_button(self, screen, button, label, color):
        """Draw a button (legacy method for compatibility)"""
        rect = button['rect'] if isinstance(button, dict) else button
        self._draw_button_modern(screen, rect, label, color, True)
    
    def _get_fitted_text(self, text, max_width, max_height, initial_size=24):
        """Get a text surface that fits within the given dimensions"""
        try:
            font = pygame.font.Font(pygame.font.get_default_font(), initial_size)
        except:
            font = pygame.font.Font(None, initial_size)
        
        text_surface = font.render(str(text), True, (255, 255, 255))
        
        # If text fits, return it
        if text_surface.get_width() <= max_width and text_surface.get_height() <= max_height:
            return text_surface, font
        
        # Otherwise, scale down the font size
        size = initial_size
        while size > 8:
            size -= 1
            try:
                font = pygame.font.Font(pygame.font.get_default_font(), size)
            except:
                font = pygame.font.Font(None, size)
            text_surface = font.render(str(text), True, (255, 255, 255))
            if text_surface.get_width() <= max_width and text_surface.get_height() <= max_height:
                return text_surface, font
        
        # If still too large, return the smallest version
        return text_surface, font
    
    def _draw_button_modern(self, screen, button, label, color, enabled=True):
        """Draw a modern styled button with rounded corners and shadow"""
        # Accept either a pygame.Rect or a dict with 'rect'
        rect = button['rect'] if isinstance(button, dict) else button
        
        if not enabled:
            color = self.DARK_GRAY
        
        # Draw shadow
        shadow_rect = pygame.Rect(rect.x + 3, rect.y + 3, rect.width, rect.height)
        shadow_surf = pygame.Surface((rect.width, rect.height))
        shadow_surf.set_alpha(150)
        shadow_surf.fill((0, 0, 0))
        screen.blit(shadow_surf, (shadow_rect.x, shadow_rect.y))
        
        # Draw button with gradient effect (simulated with lighter top edge)
        pygame.draw.rect(screen, color, rect)
        
        # Add highlight on top edge
        highlight_color = tuple(min(255, c + 40) for c in color)
        pygame.draw.line(screen, highlight_color, (rect.x, rect.y), (rect.x + rect.width, rect.y), 2)
        
        # Add border
        border_color = self.WHITE if enabled else self.GRAY
        pygame.draw.rect(screen, border_color, rect, 3)
        
        # Get text that fits within button (with padding)
        padding = 10
        max_text_width = rect.width - padding
        max_text_height = rect.height - padding
        
        # Choose text color based on button color brightness
        try:
            avg = color[0] + color[1] + color[2]
            avg = avg / 3
        except Exception:
            avg = 0
        text_color = self.BLACK if avg > 180 else self.WHITE
        
        # Get fitted text surface and font
        text_surface, font = self._get_fitted_text(str(label), max_text_width, max_text_height, 24)
        
        # Re-render with correct color
        text_surface = font.render(str(label), True, text_color)
        text_shadow = font.render(str(label), True, self.BLACK)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_shadow, (text_rect.x + 2, text_rect.y + 2))
        screen.blit(text_surface, text_rect)


class GameApp:
    def __init__(self, json_path: str, game_controller: BlackjackController):
        with open(json_path, 'r') as f:
            self.settings_json = json.load(f)

        win = self.settings_json.get('window', {})
        size = tuple(win.get('size', (1200, 800)))
        title = win.get('title', 'Game')
        # Use a darker, richer green for casino feel
        bg = tuple(win.get('background_color', (0, 80, 0)))

        pygame.init()
        self.width, self.height = size
        self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        pygame.display.set_caption(title)
        
        # Set window icon
        try:
            icon = pygame.image.load('img.jpg')
            pygame.display.set_icon(icon)
        except Exception as e:
            # If icon file not found, continue without icon
            print(f"Could not load icon: {e}")
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
