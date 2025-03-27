import neat
import pygame as pg
import os
import random

pg.font.init()
pg.init()

# Définition de la taille de la fenêtre
screenWidth = 500
screenHeight = 800
GEN = 0

# Chargement et redimensionnement des images
BIRD_IMGS = [pg.transform.scale2x(pg.image.load(os.path.join('images', 'bird1.png'))),
             pg.transform.scale2x(pg.image.load(os.path.join('images', 'bird2.png'))),
             pg.transform.scale2x(pg.image.load(os.path.join('images', 'bird3.png')))]
PIPE_IMG = pg.transform.scale2x(pg.image.load(os.path.join('images', 'pipe.png')))
BASE_IMG = pg.transform.scale2x(pg.image.load(os.path.join('images', 'base.png')))
BG_IMG = pg.transform.scale2x(pg.image.load(os.path.join('images', 'bg.png')))

# Définition de la police d'affichage
STAT_FONT = pg.font.SysFont('comicsans', 50)

# Espace entre les tuyaux pour régler la difficulté
spaceBetweenPipe = 100

class Bird:
    """Classe représentant l'oiseau."""
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        """Fait sauter l'oiseau en ajustant sa vitesse."""
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        """Met à jour la position de l'oiseau en fonction de la gravité."""
        self.tick_count += 1
        d = self.vel * self.tick_count + 1.5 * self.tick_count**2

        if d >= 10:  # Limite la vitesse de chute
            d = 10
        if d < 0:
            d -= 2  # Donne un léger boost au saut

        self.y = self.y + d

        # Ajuste l'angle d'inclinaison de l'oiseau
        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        """Affiche l'oiseau en fonction de son état d'animation."""
        self.img_count += 1

        # Animation du battement d'ailes
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # Évite que l'oiseau reste à l'envers quand il tombe
        if self.tilt <= -80:
            self.img = self.IMGS[0]
            self.img_count = self.ANIMATION_TIME*2

        rotated_img = pg.transform.rotate(self.img, self.tilt)
        new_rect = rotated_img.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_img, new_rect.topleft)

    def get_mask(self):
        """Retourne le masque de collision de l'oiseau."""
        return pg.mask.from_surface(self.img)


class Pipe:
    """Classe représentant les tuyaux."""
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0

        # Chargement des images des tuyaux
        self.PIPE_TOP = pg.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.set_height()
        self.passed = False

    def set_height(self):
        """Définit une hauteur aléatoire pour les tuyaux."""
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        """Déplace les tuyaux vers la gauche."""
        self.x -= self.VEL

    def draw(self, win):
        """Affiche les tuyaux."""
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        """Vérifie la collision entre un tuyau et l'oiseau."""
        bird_mask = bird.get_mask()
        top_mask = pg.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pg.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        t_point = bird_mask.overlap(top_mask, top_offset)
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)

        return bool(t_point or b_point)


class Base:
    """Classe représentant le sol du jeu."""
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        """Fait défiler le sol pour donner l'effet de mouvement."""
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        """Affiche le sol."""
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, birds, pipes, base, score, gen):
    """Affiche tous les éléments du jeu."""
    win.blit(BG_IMG, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("Score : " + str(score), 1, (255, 255, 255))
    win.blit(text, (screenWidth - 10 - text.get_width(), 10))

    text = STAT_FONT.render("Gen : " + str(gen), 1, (255, 255, 255))
    win.blit(text, (10, 10))

    base.draw(win)

    for bird in birds:
        bird.draw(win)
    pg.display.update()


def main(genomes, config):
    """Boucle principale du jeu."""
    global GEN
    GEN += 1
    nets = []
    ge = []
    birds = []

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        ge.append(g)

    base = Base(730)
    pipes = [Pipe(screenWidth + spaceBetweenPipe)]
    win = pg.display.set_mode((screenWidth, screenHeight))
    clock = pg.time.Clock()

    score = 0
    run = True
    while run:
        clock.tick(30)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                run = False
                pg.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1

            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.jump()

        rem = []
        add_pipe = False
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            pipe.move()

        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(screenWidth + spaceBetweenPipe))

        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                ge[x].fitness -= 1 # pas sur
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.move()
        draw_window(win, birds, pipes, base, score, GEN)

def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    p.add_reporter(neat.StatisticsReporter())

    winner = p.run(main, 50)


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)