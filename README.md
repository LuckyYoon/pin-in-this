# Yoontown Rhavenge

Yoontown Rhavenge is a top-down shoot'em up game. Our game takes inspiration from [Bullet Hell](https://en.wikipedia.org/wiki/Bullet_hell), a subgenre of shoot'em up games also known as **manic shooter**. The game is written in Python 3.14 and utilizes the popular [pygame-ce](https://github.com/pygame-community/pygame-ce) library. All classes for the game are located in [zclasses.py](zclasses.py) and the configs are located in [zconfig.py](zconfig.py). All sprites and sound tracks were made from scratch specifically for the game.

![The Rhavenger of Yoontown in Phase 1](images/phase-1.png)

The player "Gilbert" is required to dodge a large amount of attacks and projectiles from "The Rhavenger of Yoontown". The user can use **WASD** inputs to move around in 2D space and fire Gilbert's slingshot by using the **Spacebar** or **Mouse 1**.

![The Rhavenger of Yoontown in Phase 2](images/phase-2.png)

After a certain amount of damage The Rhavenger of Yoontown enters into phase 2, where it unlocks new attacks and the patterns become harder for the player to dodge.

The game involves certain audio cues which may effect the gameplay experience. The use of audio devices such as headphones is recommended.

**WARNING: THIS GAME CONTAINS FLASHING LIGHTS WHICH MAY NOT BE SUITABLE FOR PHOTOSENSITIVE EPILEPSY.**

# Installation

Running the game on Python 3.14 is recommended. However, the game should run fine on previous versions of Python. If the game fails to run or if you run into any issues, switch to Python 3.14.

[Python 3.14 Download](https://www.python.org/downloads/release/python-3144/)

To install Yoontown Rhavenge, first clone this repository.

```bash
git clone https://github.com/LuckyYoon/yoontown-rhavenge.git
```

Next, pip install the community edition of pygame.

```bash
pip install pygame-ce
```

On Windows systems you may need to use the prefix:

```bash
py -m pip install pygame-ce
```

Use the following command to run Yoontown Rhavenge:

```bash
cd yoontown-rhavenge
python ztestgame2.py
```