# Blackjack Game Plan

## Overview
A simple blackjack game built with Pygame and pygame_cards modules.

## Game Features

### Core Gameplay
- **Deck**: 6 decks combined for gameplay
- **Objective**: Beat the dealer's hand without exceeding 21
- **Starting Coins**: 1000 coins
- **Hourly Bonus**: Earn 20 coins every hour

### Betting Options
Available bet amounts: 1000, 500, 250, 100, 50, 25, 10, 5, 2.5, 1, 0.1 coins

### Player Actions
Buttons with color coding:
- **Hit** (Green): Draw another card
- **Stand** (Red): End turn and evaluate hand
- **Double** (Orange): Double your bet and receive one more card (only available after first two cards)
- **Split** (Yellow): Split identical value cards into two hands (only when holding two cards of the same number)

### Game Rules

#### Action Constraints
- **Hitting**: User cannot hit after reaching exactly 21
- **Doubling**: Only available after receiving the first two cards; disappears after the third card
- **Splitting**: Button only visible when holding two cards of the same numerical value

#### Hand Values
- **Blackjack**: Ace + 10-value card (10, J, Q, K) = 21 on first two cards
- **Ace Value**: Counts as 11 or 1, whichever is most favorable
- **Face Cards**: Jack, Queen, King = 10 points
- **Number Cards**: Face value

#### Dealer Rules
- Dealer shows one card face up and hides one card face down
- Dealer must reveal hidden card at end of player's turn
- Dealer plays according to standard rules (hits on 16 or less, stands on 17+)

## UI Elements
- Player hand display
- Dealer hand display (one visible, one hidden)
- Current bet display
- Coin balance display
- Action buttons (Hit, Stand, Double, Split)
- Betting interface with preset amounts

## Game States
1. **Betting Phase**: Player selects bet amount
2. **Deal Phase**: Cards dealt to player and dealer
3. **Player Turn**: Player chooses actions (Hit, Stand, Double, Split)
4. **Dealer Turn**: Dealer reveals hidden card and plays
5. **Outcome Phase**: Winner determined and coins adjusted
