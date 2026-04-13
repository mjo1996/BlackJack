# Blackjack

A modern, feature-rich Blackjack game built with Python and Pygame. Play against the dealer with a beautiful casino-style interface.

![Blackjack Game](img.jpg)

## Features

- **Classic Blackjack Gameplay**: Play against the dealer with standard Blackjack rules
- **Modern Casino UI**: Beautiful dark green felt background with gold accents
- **Multiple Betting Options**: Choose from various bet amounts (0.1 to 1000 coins)
- **Split Hands**: Split your hand when dealt two cards of the same rank or value
- **Double Down**: Double your bet and receive exactly one more card
- **Surrender**: Give up half your bet to fold your hand
- **Repeat Bet**: Automatically place the same bet for consecutive hands
- **Quarterly Bonus**: Receive bonus coins every 15 minutes of play
- **6-Deck Shoe**: Play with a realistic 6-deck shoe that reshuffles when low
- **Resizable Window**: Adjust the game window to your preferred size

## Requirements

- Python 3.x
- Pygame 2.6.1
- pygame-cards 0.2.0

## Installation

1. Clone the repository:
```bash
git clone https://github.com/mjo1996/BlackJack.git
cd BlackJack
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## How to Play

1. **Start the Game**:
```bash
python main.py
```

2. **Place Your Bet**:
   - Click on a bet amount button to place your wager
   - Check the "Repeat Bet" checkbox to automatically place the same bet on subsequent hands
   - Your initial coin balance is 1000

3. **Player Actions** (during your turn):
   - **Hit**: Draw another card
   - **Stand**: End your turn and let the dealer play
   - **Double**: Double your bet and receive exactly one more card (only on first two cards)
   - **Split**: Split your hand into two separate hands (requires two cards of same rank/value)
   - **Surrender**: Give up half your bet and end the hand (only on first two cards)

4. **Winning**:
   - **Blackjack** (Ace + 10-value card): Pays 3:2 (2.5x your bet)
   - **Regular Win**: Pays 1:1 (2x your bet)
   - **Push** (Tie): Your bet is returned
   - **Dealer Bust** (dealer exceeds 21): You win

5. **Game Flow**:
   - Dealer must hit on 16 or less and stand on 17 or more
   - Dealer's first card is hidden until the end of your turn
   - Click anywhere after a hand ends to continue to the next hand

## Configuration

The game settings can be customized in `settings.json`:

```json
{
    "window": {
        "size": [1200, 800],
        "title": "Blackjack",
        "background_color": [0, 80, 0]
    },
    "card": {
        "size": [80, 120],
        "front_sprite_path": "img/cards/",
        "back_sprite_file": "img/back-side.png",
        "move_speed": 80
    },
    "game": {
        "initial_coins": 1000,
        "quarterly_bonus": 100,
        "num_decks": 6,
        "bet_amounts": [1000, 500, 250, 100, 50, 25, 10, 5, 2.5, 1, 0.1]
    }
}
```

### Configuration Options:

- **window.size**: Initial window dimensions [width, height]
- **window.title**: Window title bar text
- **window.background_color**: RGB color for the table background
- **card.size**: Dimensions of playing cards [width, height]
- **game.initial_coins**: Starting coin balance
- **game.quarterly_bonus**: Bonus coins awarded every 15 minutes
- **game.num_decks**: Number of decks in the shoe (default: 6)
- **game.bet_amounts**: Available betting amounts

## Game Rules

### Card Values
- Number cards (2-10): Face value
- Face cards (J, Q, K): 10
- Ace: 11 or 1 (automatically adjusted to prevent busting)

### Splitting Rules
- Can split when dealt two cards of the same rank (e.g., two 8s)
- Can also split any two 10-value cards (10, J, Q, K combinations)
- Each split hand receives one additional card
- Play each hand separately against the dealer
- Blackjack on split hands pays 3:2

### Dealer Rules
- Dealer hits on 16 or less
- Dealer stands on 17 or more
- Dealer's hidden card is revealed after player stands

## Project Structure

```
BlackJack/
├── main.py              # Main game logic and UI
├── settings.json        # Game configuration
├── requirements.txt     # Python dependencies
├── img.jpg             # Window icon
├── PLAN.md             # Development plan
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Dependencies

- **pygame**: Core game engine and graphics
- **pygame-cards**: Card rendering and management
- **Pillow**: Image processing
- **CairoSVG**: SVG rendering for card graphics

See `requirements.txt` for complete list.

## License

This project is open source. Feel free to use, modify, and distribute.

## Credits

Built with [Pygame](https://www.pygame.org/) and [pygame-cards](https://pypi.org/project/pygame-cards/).
