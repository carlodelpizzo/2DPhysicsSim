import pygame
from pygame.locals import *

pygame.init()
clock = pygame.time.Clock()
frame_rate = 240

# Screen default
screen_width = 1100
screen_height = 700
screen = pygame.display.set_mode((screen_width, screen_height), RESIZABLE)

# Title
pygame.display.set_caption('Physics Sim')

# Colors
black = [0, 0, 0]
white = [255, 255, 255]
red = [255, 0, 0]
green = [0, 255, 0]
blue = [0, 0, 255]
cyan = [0, 255, 255]
orange = [255, 165, 0]
yellow = [255, 255, 0]
purple = [128, 0, 128]
pink = [255, 192, 203]

# Fonts
default_font = 'Helvetica'


class Object:
    def __init__(self, x: int, y: int, obj_type: str, obj_color=None, radius=10, width=20, height=20):
        if obj_color is None:
            obj_color = red
        self.x = x
        self.y = y
        self.type = obj_type
        self.color = obj_color
        self.vel = [0.0, 0.0]
        self.pos = [float(self.x), float(self.y)]
        self.acc = [0.0, 0.0]
        if self.type == 'Ball':
            self.radius = radius
        elif self.type == 'Block':
            self.width = width
            self.height = height

    def draw(self):
        if self.type == 'Ball':
            pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)
        elif self.type == 'Block':
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

    def update_pos(self, new_x: float, new_y: float):
        self.pos = (new_x, new_y)

        if new_x % 1 >= 0.5:
            self.x = int(self.pos[0] + 1)
        else:
            self.x = int(self.pos[0])

        if new_y % 1 >= 0.5:
            self.y = int(self.pos[1] + 1)
        else:
            self.y = int(self.pos[1])


class Main:
    def __init__(self):
        top_menu_width = 20
        top_tool_width = 40
        scroll_bar_width = 15
        tool_bar_width = 80

        self.gravity = 9.8 / frame_rate

        self.top_menu = TopMenu(0, 0, screen_width, top_menu_width, bg_color=red)
        self.top_toolbar = TopToolbar(0, self.top_menu.y + self.top_menu.height, screen_width, top_tool_width,
                                      bg_color=purple)
        top_tool_bottom = self.top_toolbar.y + self.top_toolbar.height
        self.toolbar = SideToolbar(0, self.top_toolbar.y + self.top_toolbar.height, tool_bar_width,
                                   screen_height - top_tool_bottom, bg_color=pink)
        self.scroll_h = ScrollBarH(self.toolbar.width, screen_height - scroll_bar_width,
                                   screen_width - self.toolbar.width, scroll_bar_width, bg_color=yellow)
        self.scroll_v = ScrollBarV(screen_width - scroll_bar_width, top_tool_bottom, scroll_bar_width,
                                   screen_height - top_tool_bottom - scroll_bar_width, bg_color=orange)
        self.viewer = ViewScreen(self.toolbar.x + self.toolbar.width, top_tool_bottom,
                                 screen_width - self.toolbar.width - scroll_bar_width,
                                 screen_height - top_tool_bottom - scroll_bar_width)
        self.elements = [self.viewer, self.scroll_v, self.scroll_h, self.toolbar, self.top_toolbar, self.top_menu]

        self.held_object = None
        self.objects = [Object(0, 0, '')]

    def draw(self):
        pygame.draw.rect(screen, black, (self.viewer.x, self.viewer.y, self.viewer.width, self.viewer.height))

        if self.held_object is not None:
            self.held_object.draw()

        for obj in self.objects:
            obj.draw()

        for element in self.elements:
            element.draw()

        pygame.display.flip()

    def mouse_handler(self, pos: tuple, pressed: tuple, press_type=''):
        for element in self.elements:
            element.mouse_handler(pos, pressed, press_type)

        if self.held_object is not None:
            if self.held_object.type == 'Ball':
                self.held_object.update_pos(pos[0], pos[1])
            elif self.held_object.type == 'Block':
                self.held_object.update_pos(pos[0] - self.held_object.width / 2, pos[1] - self.held_object.height / 2)

        if press_type == 'DOWN' and pressed[0]:
            if self.held_object is not None and self.on_view_screen(pos):
                self.objects.append(self.held_object)
                for button in self.toolbar.buttons:
                    if button.action == self.held_object.type:
                        button.running = False
                        self.toolbar.active_button = -1
                self.held_object = None

    def run(self, pos: tuple, pressed: tuple, press_type=''):
        self.mouse_handler(pos, pressed, press_type)

        actions = []
        undo_actions = []

        for button in self.toolbar.buttons:
            if button.need_to_run:
                actions.append(button.action)
                button.need_to_run = False
                button.running = True
            if button.undo:
                undo_actions.append(button.action)
                button.undo = False
                button.running = False
                button.need_to_run = False
                button.pressed_draw = False

        # Button actions undo
        if 'Ball' in undo_actions and self.held_object is not None:
            self.held_object = None
        elif 'Block' in undo_actions and self.held_object is not None:
            self.held_object = None

        # Button actions
        if 'Ball' in actions and self.held_object is None:
            self.held_object = Object(pos[0], pos[1], 'Ball')
        elif 'Block' in actions and self.held_object is None:
            self.held_object = Object(pos[0], pos[1], 'Block')

        # Object updates
        for obj in self.objects:
            if obj.type == '':
                continue
            self.move_object(obj)

        self.draw()
        clock.tick(frame_rate)

    def on_view_screen(self, pos: tuple):
        if self.viewer.x <= pos[0] <= self.viewer.x + self.viewer.width:
            if self.viewer.y <= pos[1] <= self.viewer.y + self.viewer.height:
                return True
            return False

    def resize(self):
        self.top_menu.width = screen_width
        self.top_toolbar.width = screen_width
        top_tool_bottom = self.top_toolbar.y + self.top_toolbar.height
        self.toolbar.height = screen_height - top_tool_bottom
        self.scroll_h.y = screen_height - self.scroll_h.height
        self.scroll_h.width = screen_width - self.toolbar.width
        self.scroll_v.x = screen_width - self.scroll_v.width
        self.scroll_v.height = screen_height - top_tool_bottom - self.scroll_h.height
        self.viewer.width = screen_width - self.toolbar.width - self.scroll_v.width
        self.viewer.height = screen_height - top_tool_bottom - self.scroll_h.height

    def move_object(self, obj: Object):
        # Boundary
        if abs(obj.pos[0]) >= 50000 or abs(obj.pos[1]) >= 50000:
            return

        obj.vel[0] += obj.acc[0]
        obj.vel[1] += obj.acc[1] + self.gravity
        obj.update_pos(obj.pos[0] + obj.vel[0], obj.pos[1] + obj.vel[1])


class Element:
    def __init__(self, x: int, y: int, width: int, height: int, bg_color=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.bg_color = bg_color

    def draw(self):
        if self.bg_color is not None:
            pygame.draw.rect(screen, self.bg_color, (self.x, self.y, self.width, self.height))

    def mouse_handler(self, pos: tuple, pressed: tuple, press_type: str):
        pass


class Button:
    def __init__(self, x: int, y: int, label: str, action='', padding=5, border_width=3, border_color=None,
                 button_color=None, font=default_font, font_size=20, font_color=None, toggle=False):
        if border_color is None:
            border_color = black
        if font_color is None:
            font_color = black
        self.x = x
        self.y = y
        self.padding = padding
        self.color = button_color
        self.font = pygame.font.SysFont(font, font_size)
        self.font_color = font_color
        self.label = label
        self.label_width = int(self.font.render(self.label, True, self.font_color).get_rect().width)
        self.label_height = int(self.font.render(self.label, True, self.font_color).get_rect().height)
        self.width = self.label_width + self.padding * 2
        self.height = self.label_height + self.padding * 2
        self.border = border_width
        self.border_color = border_color
        self.border_color_pressed = [255 - border_color[0], 255 - border_color[1], 255 - border_color[2]]
        self.need_to_run = False
        self.running = False
        self.held = False
        self.pressed_draw = False
        self.undo = False
        self.toggle = toggle
        if action == '':
            self.action = self.label
        else:
            self.action = action

    def draw(self):
        if self.pressed_draw or self.running:
            if self.color is not None:
                pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
            self.draw_border()
            screen.blit(self.font.render(self.label, True,
                                         [255 - self.font_color[0],
                                          255 - self.font_color[1],
                                          255 - self.font_color[2]]),
                        (self.x + self.padding, self.y + self.padding))
        else:
            if self.color is not None:
                pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
            self.draw_border()
            screen.blit(self.font.render(self.label, True, self.font_color),
                        (self.x + self.padding, self.y + self.padding))

    def draw_border(self):
        if self.pressed_draw or self.running:
            pygame.draw.rect(screen, self.border_color_pressed, (self.x, self.y, self.border, self.height))
            pygame.draw.rect(screen, self.border_color_pressed, (self.x, self.y, self.width, self.border))
            pygame.draw.rect(screen, self.border_color_pressed, (self.x, self.y + self.height - self.border,
                                                                 self.width, self.border))
            pygame.draw.rect(screen, self.border_color_pressed, (self.x + self.width - self.border,
                                                                 self.y, self.border, self.height))
        else:
            pygame.draw.rect(screen, self.border_color, (self.x, self.y, self.border, self.height))
            pygame.draw.rect(screen, self.border_color, (self.x, self.y, self.width, self.border))
            pygame.draw.rect(screen, self.border_color, (self.x, self.y + self.height - self.border, self.width,
                                                         self.border))
            pygame.draw.rect(screen, self.border_color, (self.x + self.width - self.border,
                                                         self.y, self.border, self.height))

    def check_collide(self, pos: tuple):
        if self.x <= pos[0] <= self.x + self.width:
            if self.y <= pos[1] <= self.y + self.height:
                return True
        return False

    def mouse_input(self, pos: tuple, pressed: tuple, press_type: str):
        if self.check_collide(pos):
            if press_type == 'DOWN' and pressed[0] and self.running:
                self.undo = True
            elif press_type == 'DOWN' and pressed[0]:
                self.held = True
                self.pressed_draw = True
            elif press_type == 'UP' and not pressed[0] and self.pressed_draw:
                self.held = False
                if self.toggle:
                    self.need_to_run = True
                else:
                    self.pressed_draw = False
                    self.need_to_run = True
        elif press_type == 'UP' and not pressed[0]:
            self.held = False
            self.pressed_draw = False

        if press_type == '' and self.held:
            if self.check_collide(pos):
                self.pressed_draw = True
            else:
                self.pressed_draw = False

    def change_label(self, new_label: str):
        self.label = new_label
        self.label_width = int(self.font.render(self.label, True, self.font_color).get_rect().width)
        self.label_height = int(self.font.render(self.label, True, self.font_color).get_rect().height)
        self.width = self.label_width + self.padding * 2
        self.height = self.label_height + self.padding * 2


class TopMenu(Element):
    def __init__(self, x: int, y: int, width: int, height: int, bg_color=None):
        super().__init__(x, y, width, height, bg_color)


class TopToolbar(Element):
    def __init__(self, x: int, y: int, width: int, height: int, bg_color=None):
        super().__init__(x, y, width, height, bg_color)


class SideToolbar(Element):
    def __init__(self, x: int, y: int, width: int, height: int, bg_color=None):
        button_spacing = 10

        self.circle_button = Button(0, 0, 'Circle', toggle=True, action='Ball')
        self.block_button = Button(0, 0, 'Block', toggle=True)
        self.buttons = [self.circle_button, self.block_button]
        self.active_button = -1
        for button in self.buttons:
            if button.width > width:
                width = button.width
        for button in self.buttons:
            button.y = y + (self.buttons.index(button) * (button_spacing + button.height)) + button_spacing
            button.x = int(x + (width - button.width) / 2)

        super().__init__(x, y, width, height, bg_color)

    def draw(self):
        super().draw()
        for button in self.buttons:
            button.draw()

    def mouse_handler(self, pos: tuple, pressed: tuple, press_type: str):
        if self.active_button == -1:
            for button in self.buttons:
                button.mouse_input(pos, pressed, press_type)
                if button.need_to_run:
                    self.active_button = self.buttons.index(button)
                    break
        else:
            for button in self.buttons:
                button.mouse_input(pos, pressed, press_type)
                if button.need_to_run and self.buttons.index(button) != self.active_button:
                    self.buttons[self.active_button].undo = True
                    self.active_button = self.buttons.index(button)


class ScrollBarH(Element):
    def __init__(self, x: int, y: int, width: int, height: int, bg_color=None):
        super().__init__(x, y, width, height, bg_color)


class ScrollBarV(Element):
    def __init__(self, x: int, y: int, width: int, height: int, bg_color=None):
        super().__init__(x, y, width, height, bg_color)


class ViewScreen(Element):
    def __init__(self, x: int, y: int, width: int, height: int, bg_color=None):
        super().__init__(x, y, width, height, bg_color)


main = Main()
running = True
while running:
    # Event loop
    for event in pygame.event.get():
        # Press close button
        if event.type == pygame.QUIT:
            running = False
            break

        # Key down events
        if event.type == pygame.KEYDOWN:
            keys_list = pygame.key.get_pressed()

            # Close window shortcut
            if (keys_list[K_LCTRL] or keys_list[K_RCTRL]) and keys_list[K_w]:
                running = False
                break

        # Key up events
        if event.type == pygame.KEYUP:
            keys_list = pygame.key.get_pressed()

        # Mouse down event
        if event.type == pygame.MOUSEBUTTONDOWN:
            main.mouse_handler(pygame.mouse.get_pos(), pygame.mouse.get_pressed(), 'DOWN')

        # Mouse up event
        if event.type == pygame.MOUSEBUTTONUP:
            main.mouse_handler(pygame.mouse.get_pos(), pygame.mouse.get_pressed(), 'UP')

        # Window resize event
        if event.type == pygame.VIDEORESIZE:
            screen_width = event.w
            screen_height = event.h
            screen = pygame.display.set_mode((screen_width, screen_height), RESIZABLE)
            main.resize()

    main.run(pygame.mouse.get_pos(), pygame.mouse.get_pressed())

pygame.display.quit()
pygame.quit()
