import imgui

class GameUI:
    def __init__(self, lives, ammo, score):
        self.lives = lives
        self.ammo = ammo
        self.score = score

    def set_lives(self, lives):
        self.lives = lives
    
    def set_ammo(self, ammo):
        self.ammo = ammo

    def set_score(self, score):
        self.score = score
    
    def render_ui(self):
        imgui.begin("Game UI", False, imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE)

        imgui.text(f"Lives: {self.lives}")
        imgui.text(f"Ammo: {self.ammo}")
        imgui.text(f"Score: {self.score}")

        imgui.end()
        