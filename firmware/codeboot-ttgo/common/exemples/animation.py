import ttgo as dev

fg = "#ff0"  # jaune
bg = "#aaa"  # gris

taille = 40  # taille, position et vitesse en y de la balle
x = 0
y = 0
vy = 5

def balle(x, y, couleur):
    dev.fill_rect(x, y, taille, taille, couleur)

def animer():
    global x, y, vy
    if y+vy<0 or y+vy+taille>dev.screen_height:  # rebondir sur les bords
        vy = -vy
    balle(x, y, bg)  # effacer la balle
    if dev.button(0) and x>0: x -= 1
    if dev.button(1) and x+taille<dev.screen_width: x += 1
    y += vy          # avancer la balle
    balle(x, y, fg)  # tracer la balle à sa nouvelle position
    if repeter:
        dev.after(0.01, animer)  # dans 0.01 seconde appeler animer()

repeter = True

def stop():  # arrêter l'animation
    global repeter
    repeter = False

dev.clear_screen(bg)  # effacer l'écran
animer()              # débuter l'animation

dev.after(300, stop)   # après 10 secondes arrêter l'animation
