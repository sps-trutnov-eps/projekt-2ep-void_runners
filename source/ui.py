import imgui

class GameUI:
    def __init__(self, lives, ammo, score):
        self.lives = lives
        self.ammo = ammo
        self.score = score

    def render_ui(self):
        window_width, window_height = 1280, 720  
        
        # Nastavení pozice okna na levý dolní roh
        imgui.set_next_window_position(10, window_height - 150)  
        imgui.set_next_window_size(300, 130)  

       
        imgui.begin("Game UI", False, imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE)
       
        imgui.text(f"Lives: {self.lives}")
        imgui.same_line(120)
        imgui.text("[icon]")

        imgui.text(f"Ammo: {self.ammo}")
        imgui.same_line(120)
        imgui.text("[icon]")

        imgui.text(f"Score: {self.score}")
        imgui.same_line(120)
        imgui.text("[icon]")

        imgui.end()





