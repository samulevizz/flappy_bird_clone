import pygame as pg

import random as rand

pg.init()  # inizializza motore di gioco

# COSTANTI
LARGHEZZA_SCHERMO, ALTEZZA_SCHERMO = 288, 512
GRAVITA, POT_VOLO, LARGHEZZA_TUBO, SPAZIO_TUBI = 0.25, -4.91, 90, 120
# potenza_volo = -g/2 = -9.81/2 = -4.91

VEL_TUBO, ALTEZZA_SUOLO = -8, 110
ANGOLO_ROTAZIONE_SU, ANGOLO_ROTAZIONE_GIU, NERO, ARANCIO = 20, -80, (0, 0, 0), (255, 165, 0)  # rgb
FLAPPY_FONT = pg.font.Font('assets/flappy-font.ttf', 24)


def carica_img(percorso, dim=None):
    img = pg.image.load(percorso).convert_alpha()
    return pg.transform.scale(img, dim) if dim else img


def carica_suono(percorso):
    return pg.mixer.Sound(percorso)


# imposta icona
def logo():
    icona = carica_img('assets/favicon.ico')
    pg.display.set_icon(icona)


# punteggio
def disegna_punteggio(punteggio, schermo):
    punteggio_str = str(punteggio)
    for indice, cifra in enumerate(punteggio_str):
        pos_x = (LARGHEZZA_SCHERMO // 1.95) - (len(punteggio_str) * 15) + (
                indice * 30)  # centra il punteggio sullo schermo
        schermo.blit(sprites_num[int(cifra)], (pos_x, 50))


def disegna_testo(testo, font, colore, schermo, x, y):
    # bordo bianco dei testi
    BORDO_BIANCO = (255, 255, 255)  # rgb
    SPESSORE_BORDO = 2

    for dx in range(-SPESSORE_BORDO, SPESSORE_BORDO + 1):  # ciclo per creare il bordo
        for dy in range(-SPESSORE_BORDO, SPESSORE_BORDO + 1):
            superficie_testo = font.render(testo, True, BORDO_BIANCO)
            schermo.blit(superficie_testo, superficie_testo.get_rect(center=(x + dx, y + dy)))

            superficie_testo = font.render(testo, True, colore)
            schermo.blit(superficie_testo, superficie_testo.get_rect(center=(x, y)))


# classe principale del Giocatore
class Giocatore(pg.sprite.Sprite):
    def __init__(self):  # constructor del giocatore
        super().__init__()
        self.sprites = sprites_giocatore
        self.frame_corrente = 0
        self.vel = 0
        self.angolo = 0
        self.image = self.sprites[self.frame_corrente]
        self.rect = self.image.get_rect(center=(60, ALTEZZA_SCHERMO // 2))
        self.timer_volo = 0

    def update(self):
        # applica forza di gravità
        self.vel = min(self.vel + GRAVITA, 10)
        self.rect.y += int(self.vel)

        # rotazione giocatore
        if self.vel < 0:
            self.angolo = ANGOLO_ROTAZIONE_SU
        else:
            self.angolo = max(self.angolo - 3, ANGOLO_ROTAZIONE_GIU)

        # animazioni varie
        self.timer_volo += 1  # incrementa il timer
        if self.timer_volo > 5:
            self.frame_corrente = (self.frame_corrente + 1) % len(self.sprites)
            self.timer_volo = 0
        self.image = pg.transform.rotate(self.sprites[self.frame_corrente], self.angolo)

        if self.rect.bottom >= ALTEZZA_SCHERMO - ALTEZZA_SUOLO:
            self.rect.bottom = ALTEZZA_SCHERMO - ALTEZZA_SUOLO
            return True  # quindi ritorna vero

        # fix: non uscire dallo schermo
        self.rect.clamp_ip(pg.Rect(0, 0, LARGHEZZA_SCHERMO, ALTEZZA_SCHERMO - ALTEZZA_SUOLO))
        return False

    def vola(self):  # gestisci il volo
        self.vel = POT_VOLO
        self.angolo = ANGOLO_ROTAZIONE_SU
        suono_volo.play()


# classe del tubo
class Tubo(pg.sprite.Sprite):
    def __init__(self, x, altezza, superiore):  # constructor del tubo
        super().__init__()
        self.image = pg.transform.scale(sprites_tubo, (LARGHEZZA_TUBO, ALTEZZA_SCHERMO))
        if superiore:
            self.image = pg.transform.flip(self.image, False, True)
        self.rect = self.image.get_rect(topleft=(x, altezza))
        self.punteggio = False

    def update(self):
        self.rect.x += VEL_TUBO
        if self.rect.right < 0:
            self.kill()

    def controlla_collisione(self, giocatore):
        return self.rect.colliderect(giocatore.rect)


# classe della coppia di tubi
class CoppiaTubi:
    def __init__(self, x):  # constructor della coppia di tubi
        gap_minimo = 130
        gap_massimo = ALTEZZA_SCHERMO - ALTEZZA_SUOLO - SPAZIO_TUBI - 30

        self.gap_y = rand.randint(gap_minimo, gap_massimo)
        self.gap_y = max(gap_minimo, min(self.gap_y, gap_massimo))

        self.tubo_superiore = Tubo(x, self.gap_y - SPAZIO_TUBI - ALTEZZA_SCHERMO, True)
        self.tubo_inferiore = Tubo(x, self.gap_y, False)

    def aggiungi_a_gruppo(self, gruppo):
        gruppo.add(self.tubo_superiore, self.tubo_inferiore)

    def passa(self, giocatore):
        if not self.tubo_superiore.punteggio and self.tubo_inferiore.rect.right < giocatore.rect.left:
            self.tubo_superiore.punteggio = True
            return True
        return False


# classe del terreno
class Suolo(pg.sprite.Sprite):
    def __init__(self):  # constructor del terreno
        super().__init__()
        self.image = sprites_suolo
        self.rect = self.image.get_rect(topleft=(0, ALTEZZA_SCHERMO - ALTEZZA_SUOLO))

    def update(self):
        self.rect.x += VEL_TUBO
        if self.rect.right <= LARGHEZZA_SCHERMO:
            self.rect.left = 0

    def disegna(self, schermo):
        schermo.blit(self.image, self.rect)


# funzione principale
def gioco():
    schermo = pg.display.set_mode((LARGHEZZA_SCHERMO, ALTEZZA_SCHERMO))
    pg.display.set_caption("Clone di Flappy Bird")
    logo()

    # carica assets globali (sprites, suoni ecc...) e crea variabili o oggetti vari
    global sprites_giocatore, sprites_tubo, sfondi, sprites_suolo, sprites_num, suono_volo, suono_colpito, suono_punto, logo_titolo
    sprites_giocatore = [carica_img(f'assets/giocatore/bird{i + 1}.png', (55, 40)) for i in range(3)]
    sprites_tubo = carica_img('assets/tubo.png')
    sfondi = [carica_img(f'assets/sfondi/bg_{tempo}.png') for tempo in reversed(['giorno', 'notte'])]
    sprites_suolo = carica_img('assets/suolo.png', (LARGHEZZA_SCHERMO * 2, ALTEZZA_SUOLO))
    sprites_num = [carica_img(f'assets/numeri/{i}.png') for i in range(10)]
    suono_volo = carica_suono(f'assets/suoni/volo.wav')
    suono_colpito = carica_suono(f'assets/suoni/morte.wav')
    suono_punto = carica_suono(f'assets/suoni/punto.wav')
    logo_titolo = carica_img('assets/logo.png', (200, 50))
    framerate = pg.time.Clock()  # fps
    giocatore = Giocatore()
    gruppo_giocatore = pg.sprite.Group(giocatore)
    suolo = Suolo()
    gruppo_tubi = pg.sprite.Group()
    coppie_tubi = []  # array delle coppie di tubi

    # variabili
    timer_tubi = 0
    punteggio = 0
    game_over = False
    stato_gioco = 'INIZIO'
    indice_sfondo = 1
    mostra_pos_morte = False

    # ciclo principale del gioco
    while True:
        if not game_over:
            schermo.blit(sfondi[indice_sfondo], (0, 0))

        for evento in pg.event.get():
            # gestione degli input da tastiera
            if evento.type == pg.QUIT:
                pg.quit()
                exit()
            if evento.type == pg.KEYDOWN:  # Cambia K_SPACE in KEYDOWN
                if evento.key == pg.K_SPACE:
                    if stato_gioco == 'INIZIO':
                        stato_gioco = 'GIOCO'
                    elif stato_gioco == 'GIOCO' and not game_over:
                        giocatore.vola()
                    elif stato_gioco == 'GAME_OVER' and mostra_pos_morte:
                        gioco()
                if evento.key == pg.K_c:
                    # cambia sfondo giorno/notte cliccando 'c'
                    indice_sfondo = 1 - indice_sfondo

        if stato_gioco == 'GIOCO':
            timer_tubi += 1
            if timer_tubi >= 60:
                coppia_tubi = CoppiaTubi(LARGHEZZA_SCHERMO)
                coppia_tubi.aggiungi_a_gruppo(gruppo_tubi)
                coppie_tubi.append(coppia_tubi)
                timer_tubi = 0

            # aggiornamenti
            gruppo_giocatore.update()
            gruppo_tubi.update()
            suolo.update()

            for coppia_tubi in coppie_tubi[:]:
                if coppia_tubi.tubo_superiore.controlla_collisione(
                        giocatore) or coppia_tubi.tubo_inferiore.controlla_collisione(giocatore):
                    suono_colpito.play()
                    game_over = True
                    stato_gioco = 'GAME_OVER'
                if coppia_tubi.passa(giocatore):
                    punteggio += 1  # incrementa punteggio
                    suono_punto.play()
                if coppia_tubi.tubo_superiore.rect.right < 0:
                    coppie_tubi.remove(coppia_tubi)

            # allora controlla se collide con il terreno
            if giocatore.update():
                suono_colpito.play()
                game_over = True
                stato_gioco = 'GAME_OVER'

            gruppo_giocatore.draw(schermo)
            gruppo_tubi.draw(schermo)
            suolo.disegna(schermo)
            disegna_punteggio(punteggio, schermo)

        # schermata iniziale
        elif stato_gioco == 'INIZIO':
            pos_logo_x = LARGHEZZA_SCHERMO // 1.9
            pos_logo_y = ALTEZZA_SCHERMO // 2.5
            schermo.blit(logo_titolo, logo_titolo.get_rect(center=(pos_logo_x, pos_logo_y)))

            disegna_testo("premi spazio", FLAPPY_FONT, NERO, schermo, LARGHEZZA_SCHERMO // 2, ALTEZZA_SCHERMO // 2)
            disegna_testo("per iniziare", FLAPPY_FONT, NERO, schermo, LARGHEZZA_SCHERMO // 2,
                          ALTEZZA_SCHERMO // 1.78)

            # schermata di game over
        elif stato_gioco == 'GAME_OVER':
            if not mostra_pos_morte:
                gruppo_giocatore.draw(schermo)
                gruppo_giocatore.draw(schermo)
                suolo.disegna(schermo)
                pg.display.flip()
                mostra_pos_morte = True
            else:
                disegna_punteggio(punteggio, schermo)
                GAMEOVER_FONT = pg.font.Font('assets/flappy-font.ttf', 36)
                disegna_testo("HAI PERSO!", GAMEOVER_FONT, ARANCIO, schermo, LARGHEZZA_SCHERMO // 2,
                              ALTEZZA_SCHERMO // 2.1)
        pg.display.flip()
        framerate.tick(60)  # 60 fps


# esegui
if __name__ == "__main__":
    gioco()
