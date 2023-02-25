import ttgo as dev

dev.clear_screen("#ff0")      # remplir l'ecran en jaune

for x in range(50):           # dessiner un cercle bleu
    for y in range(50):
        if (x-25)**2+(y-25)**2 < 625:
            dev.set_pixel(x, y, "#00f")

vert = "#0f0"
noir = "#000"

dev.fill_rect(10, 50, 120, 80, "#f0f")  # dessiner un rectangle mauve
dev.fill_rect(20, 60, 100, 60, vert)    # et un rectangle vert dedans

dev.draw_text(30, 70, "HACK!", noir, vert)  # texte noir sur fond vert

plus = """
#ff0#ff0#ff0#f00#ff0#ff0#ff0
#ff0#ff0#ff0#f00#ff0#ff0#ff0
#ff0#ff0#ff0#f00#ff0#ff0#ff0
#f00#f00#f00#f00#f00#f00#f00
#ff0#ff0#ff0#f00#ff0#ff0#ff0
#ff0#ff0#ff0#f00#ff0#ff0#ff0
#ff0#ff0#ff0#f00#ff0#ff0#ff0
"""

dev.draw_image(70, 160, plus)  # afficher l'image d'un plus rouge
