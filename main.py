
# -*- coding: utf-8 -*-

import sys
import math
import os
import json
import datetime
import platform as py_platform

APP_ROTATION = 0
is_windows = py_platform.system() == 'Windows'

try:
    from kivy.config import Config
    if is_windows:
        Config.set('graphics', 'resizable', False)
        if APP_ROTATION in [90, 270]:
            Config.set('graphics', 'width', '450')
            Config.set('graphics', 'height', '800')
        else:
            Config.set('graphics', 'width', '800')
            Config.set('graphics', 'height', '450')
    else:
        Config.set('graphics', 'resizable', True)
        if APP_ROTATION in [90, 270]:
            Config.set('graphics', 'width', '900')
            Config.set('graphics', 'height', '430')
        else:
            Config.set('graphics', 'width', '430')
            Config.set('graphics', 'height', '900')
except Exception:
    pass

try:
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.widget import Widget
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.popup import Popup
    from kivy.core.window import Window
    from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, PushMatrix, PopMatrix, Rotate, Translate
    from kivy.graphics.texture import Texture
    from kivy.properties import NumericProperty, StringProperty, ListProperty, BooleanProperty
    from kivy.metrics import dp, Metrics
    from kivy.clock import Clock
except ModuleNotFoundError:
    print("\n[Error] Kivy library is not installed.")
    sys.exit(1)

if is_windows:
    try:
        dpi = Metrics.dpi if (hasattr(Metrics, 'dpi') and Metrics.dpi > 0) else 96
        win_w = int(6.10 * dpi)
        win_h = int(3.43 * dpi)
        if APP_ROTATION in [90, 270]:
            Window.size = (win_h, win_w)
        else:
            Window.size = (win_w, win_h)
    except Exception:
        if APP_ROTATION in [90, 270]:
            Window.size = (450, 800)
        else:
            Window.size = (800, 450)

try:
    Window.rotation = APP_ROTATION
except Exception:
    pass

try:
    from kivy.core.text import LabelBase
    import kivy.resources as resources
    dejavu_path = resources.resource_find('fonts/DejaVuSans.ttf')
    if dejavu_path:
        LabelBase.register(name='Roboto', fn_regular=dejavu_path, fn_bold=dejavu_path)
except Exception:
    pass

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError:
    arabic_reshaper = None
    get_display = None

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    try:
        RESAMPLE_FILTER = Image.Resampling.BILINEAR
    except AttributeError:
        RESAMPLE_FILTER = Image.BILINEAR
except ImportError:
    Image = None
    ImageDraw = None
    ImageFont = None
    ImageFilter = None
    RESAMPLE_FILTER = None


def create_vertical_gradient(color_top, color_bottom):
    texture = Texture.create(size=(1, 2), colorfmt='rgba')
    buf = bytes([
        int(color_bottom[0]*255), int(color_bottom[1]*255), int(color_bottom[2]*255), int(color_bottom[3]*255),
        int(color_top[0]*255), int(color_top[1]*255), int(color_top[2]*255), int(color_top[3]*255)
    ])
    texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
    return texture


class RotatedLabel(Label):
    angle = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas, angle=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            PushMatrix()
            Translate(self.center_x, self.center_y)
            Rotate(angle=self.angle, axis=(0, 0, 1))
            Translate(-self.center_x, -self.center_y)
        self.canvas.after.clear()
        with self.canvas.after:
            PopMatrix()


class PlasticButton(Button):
    btn_color = ListProperty([0.5, 0.5, 0.5, 1])
    btn_pressed_color = ListProperty([0.4, 0.4, 0.4, 1])
    is_active = BooleanProperty(False)

    def __init__(self, btn_color=None, btn_pressed_color=None, **kwargs):
        if btn_color:
            self.btn_color = btn_color
            self.top_color = [min(c + 0.12, 1.0) for c in btn_color[:3]] + [btn_color[3]]
            self.bottom_color = [max(c - 0.12, 0.0) for c in btn_color[:3]] + [btn_color[3]]
        else:
            self.btn_color = [0.5, 0.5, 0.5, 1]
            self.top_color = [0.62, 0.62, 0.62, 1]
            self.bottom_color = [0.38, 0.38, 0.38, 1]

        self.btn_pressed_color = btn_pressed_color or [max(c - 0.2, 0) for c in self.btn_color[:3]] + [self.btn_color[3]]
        super().__init__(**kwargs)
        self.background_color = [0, 0, 0, 0]
        self.font_size = '10sp'
        self.bold = True
        self.color = [0.1, 0.1, 0.1, 1] if sum(self.btn_color[:3])/3 > 0.7 else [1, 1, 1, 1]
        self.halign = 'center'
        self.valign = 'middle'
        self.bind(size=self._update_text_size)
        self.normal_texture = create_vertical_gradient(self.top_color, self.bottom_color)
        p_top = [max(c - 0.1, 0) for c in self.btn_pressed_color[:3]] + [1]
        p_bottom = [max(c - 0.25, 0) for c in self.btn_pressed_color[:3]] + [1]
        self.pressed_texture = create_vertical_gradient(p_top, p_bottom)
        self.bind(pos=self.draw_button, size=self.draw_button, state=self.draw_button, is_active=self.draw_button)

    def _update_text_size(self, instance, value):
        self.text_size = value

    def draw_button(self, *args):
        self.canvas.before.clear()
        effectively_pressed = (self.state == 'down' or self.is_active)
        with self.canvas.before:
            if not effectively_pressed:
                Color(0.05, 0.05, 0.05, 0.7)
                RoundedRectangle(pos=(self.x + dp(1), self.y - dp(5)), size=(self.width - dp(2), self.height), radius=[dp(8)])
            Color(0, 0, 0, 0.5) if effectively_pressed else Color(1, 1, 1, 0.35)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
            if not effectively_pressed:
                Color(1, 1, 1, 1)
                RoundedRectangle(pos=(self.x + dp(2), self.y + dp(4)), size=(self.width - dp(4), self.height - dp(6)), radius=[dp(7)], texture=self.normal_texture)
            else:
                Color(1, 1, 1, 1)
                RoundedRectangle(pos=(self.x + dp(3), self.y + dp(1)), size=(self.width - dp(6), self.height - dp(6)), radius=[dp(7)], texture=self.pressed_texture)


class RecessedInput(Button):
    value_text = StringProperty("")
    label_text = StringProperty("")

    def __init__(self, label_text="", value_text="", **kwargs):
        self.label_text = label_text
        self.value_text = value_text
        super().__init__(**kwargs)
        self.background_color = [0, 0, 0, 0]
        self.font_size = '11sp'
        self.bold = True
        self.color = [0.95, 0.95, 0.1, 1]
        self.halign = 'center'
        self.valign = 'middle'
        self.bind(pos=self.update_graphics, size=self.update_graphics, value_text=self.update_text)
        self.update_text()

    def update_text(self, *args):
        app = App.get_running_app()
        if app and hasattr(app, 'translate'):
            label = app.translate(self.label_text)
            val = app.convert_digits(self.value_text)
            if app.lang == 'fa' and val.endswith(' M'):
                val = val.replace(' M', ' متر')
        else:
            label = self.label_text
            val = self.value_text
        self.text = f"[size=10sp][color=#8c8c8c]{label}[/color][/size]\n{val}"
        self.markup = True

    def update_graphics(self, *args):
        self.text_size = self.size
        self.canvas.before.clear()
        with self.canvas.before:
            Color(1, 1, 1, 0.25)
            RoundedRectangle(pos=(self.x, self.y - dp(1)), size=self.size, radius=[dp(5)])
            Color(0.1, 0.1, 0.1, 1)
            RoundedRectangle(pos=(self.x + dp(1), self.y + dp(1)), size=(self.width - dp(2), self.height - dp(2)), radius=[dp(5)])
            Color(0, 0, 0, 0.6)
            Line(points=[self.x + dp(2), self.y + self.height - dp(2), self.x + self.width - dp(2), self.y + self.height - dp(2)], width=1.1)


class MonitorView(FloatLayout):
    width_val = NumericProperty(5.0)
    length_val = NumericProperty(5.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lbl_p1 = Label(text="[b]P1[/b]", markup=True, color=[0.05, 0.05, 0.05, 1], font_size='14sp', size_hint=(None, None), size=(dp(30), dp(30)))
        self.lbl_p2 = Label(text="[b]P2[/b]", markup=True, color=[0.05, 0.05, 0.05, 1], font_size='14sp', size_hint=(None, None), size=(dp(30), dp(30)))
        self.lbl_p3 = Label(text="[b]P3[/b]", markup=True, color=[0.05, 0.05, 0.05, 1], font_size='14sp', size_hint=(None, None), size=(dp(30), dp(30)))
        self.lbl_p4 = Label(text="[b]P4[/b]", markup=True, color=[0.05, 0.05, 0.05, 1], font_size='14sp', size_hint=(None, None), size=(dp(30), dp(30)))
        self.lbl_y = Label(text="[b]Y[/b]", markup=True, color=[0.05, 0.05, 0.05, 1], font_size='15sp', size_hint=(None, None), size=(dp(20), dp(20)))
        self.lbl_x = Label(text="[b]X[/b]", markup=True, color=[0.05, 0.05, 0.05, 1], font_size='15sp', size_hint=(None, None), size=(dp(20), dp(20)))
        
        self.lbl_p1p2 = RotatedLabel(text="", color=[0, 0, 0, 1], font_size='13sp', bold=True, size_hint=(None, None), size=(dp(40), dp(20)))
        self.lbl_p2p4 = RotatedLabel(text="", color=[0, 0, 0, 1], font_size='13sp', bold=True, size_hint=(None, None), size=(dp(40), dp(20)))
        self.lbl_p4p3 = RotatedLabel(text="", color=[0, 0, 0, 1], font_size='13sp', bold=True, size_hint=(None, None), size=(dp(40), dp(20)))
        self.lbl_p3p1 = RotatedLabel(text="", color=[0, 0, 0, 1], font_size='13sp', bold=True, size_hint=(None, None), size=(dp(40), dp(20)))
        self.lbl_p1p4 = RotatedLabel(text="", color=[0, 0, 0, 1], font_size='13sp', bold=True, size_hint=(None, None), size=(dp(40), dp(20)))
        self.lbl_p2p3 = RotatedLabel(text="", color=[0, 0, 0, 1], font_size='13sp', bold=True, size_hint=(None, None), size=(dp(40), dp(20)))

        self.lbl_filename = Label(text="", color=[0.1, 0.1, 0.1, 1], font_size='13sp', bold=True, size_hint=(None, None), size=(dp(150), dp(25)), halign='left', valign='middle')
        self.lbl_filename.bind(size=lambda inst, val: setattr(inst, 'text_size', val))

        self.watermark_layout = FloatLayout(size_hint=(1, 1))
        self.watermark_lbl = Label(text="[color=#00000012]Cornix\nWinner[/color]", markup=True, bold=True, halign='center', valign='middle', size_hint=(None, None))
        self.watermark_layout.add_widget(self.watermark_lbl)

        self.btn_help = PlasticButton(text="Help", btn_color=[0.11, 0.51, 0.84, 1], size_hint=(None, None), size=(dp(90), dp(33)))
        self.btn_help.bind(on_release=self.on_help_click)
        self.btn_help.opacity = 0
        self.btn_help.disabled = True
        
        for w in [self.watermark_layout, self.lbl_p1, self.lbl_p2, self.lbl_p3, self.lbl_p4, self.lbl_y, self.lbl_x,
                  self.lbl_p1p2, self.lbl_p2p4, self.lbl_p4p3, self.lbl_p3p1, self.lbl_p1p4, self.lbl_p2p3, self.lbl_filename,
                  self.btn_help]:
            self.add_widget(w)
        self.bind(pos=self.redraw, size=self.redraw, width_val=self.redraw, length_val=self.redraw)

    def on_help_click(self, instance):
        app = App.get_running_app()
        if app:
            app.show_contamination_help()

    def redraw(self, *args):
        self.canvas.before.clear()
        max_w, max_h = self.width * 0.85, self.height * 0.85
        app = App.get_running_app()
        if app:
            self.width_val = app.width_val
            self.length_val = app.length_val
            
        aspect_ratio = self.width_val / max(self.length_val, 0.1)
        if aspect_ratio > (max_w / max_h):
            rect_w = max_w
            rect_h = max_w / aspect_ratio
        else:
            rect_h = max_h
            rect_w = max_h * aspect_ratio
            
        rect_x, rect_y = self.x + (self.width - rect_w) / 2, self.y + (self.height - rect_h) / 2
        
        self.lbl_p1.pos = (rect_x - dp(30), rect_y - dp(32))
        self.lbl_p2.pos = (rect_x + rect_w + dp(2), rect_y - dp(32))
        self.lbl_p3.pos = (rect_x - dp(30), rect_y + rect_h + dp(2))
        self.lbl_p4.pos = (rect_x + rect_w + dp(2), rect_y + rect_h + dp(2))
        
        if app:
            e = app.ui_entry_values
            self.lbl_p1p2.text = app.convert_digits(e.get("p1p2", ""))
            self.lbl_p2p4.text = app.convert_digits(e.get("p2p4", ""))
            self.lbl_p4p3.text = app.convert_digits(e.get("p4p3", ""))
            self.lbl_p3p1.text = app.convert_digits(e.get("p3p1", ""))
            self.lbl_p1p4.text = app.convert_digits(e.get("p1p4", ""))
            self.lbl_p2p3.text = app.convert_digits(e.get("p2p3", ""))
        
        self.lbl_p1p2.pos = (rect_x + rect_w / 2 - self.lbl_p1p2.width / 2, rect_y - self.lbl_p1p2.height - dp(2))
        self.lbl_p2p4.pos = (rect_x + rect_w + dp(2), rect_y + rect_h / 2 - self.lbl_p2p4.height / 2)
        self.lbl_p4p3.pos = (rect_x + rect_w / 2 - self.lbl_p4p3.width / 2, rect_y + rect_h + dp(2))
        self.lbl_p3p1.pos = (rect_x - self.lbl_p3p1.width - dp(2), rect_y + rect_h / 2 - self.lbl_p3p1.height / 2)

        self.lbl_p1p2.angle = 0
        self.lbl_p4p3.angle = 0
        self.lbl_p2p4.angle = 270
        self.lbl_p3p1.angle = 90
        
        theta = math.atan2(rect_h, rect_w)
        self.lbl_p1p4.angle = math.degrees(theta)
        self.lbl_p2p3.angle = -math.degrees(theta)

        self.lbl_p1p2.pos = (rect_x + rect_w / 2 - self.lbl_p1p2.width / 2, rect_y - self.lbl_p1p2.height + dp(4))
        self.lbl_p4p3.pos = (rect_x + rect_w / 2 - self.lbl_p4p3.width / 2, rect_y + rect_h + dp(2))

        if app and app.loaded_scan_name:
            self.lbl_filename.text = app.loaded_scan_name
            p4p3_w = self.lbl_p4p3.width if self.lbl_p4p3.width > 0 else dp(40)
            start_x = rect_x + dp(12)
            end_x = rect_x + rect_w / 2 - p4p3_w / 2 - dp(8)
            available_width = max(dp(50), end_x - start_x)
            name_len = len(app.loaded_scan_name) if len(app.loaded_scan_name) > 0 else 1
            calc_font_size = available_width / (name_len * 0.65)
            font_size_dp = min(dp(13), max(dp(8), calc_font_size))
            self.lbl_filename.font_size = font_size_dp
            self.lbl_filename.size = (available_width, dp(25))
            self.lbl_filename.pos = (start_x, rect_y + rect_h + dp(3))
            self.lbl_filename.opacity = 1
        else:
            self.lbl_filename.text = ""
            self.lbl_filename.opacity = 0
        
        self.lbl_p2p4.center_x = rect_x + rect_w + dp(2) + dp(10)
        self.lbl_p2p4.center_y = rect_y + rect_h / 2
        self.lbl_p3p1.center_x = rect_x - dp(8)
        self.lbl_p3p1.center_y = rect_y + rect_h / 2
        
        shift_chord_dist = dp(10) + dp(3)
        dx = - shift_chord_dist * math.sin(theta)
        dy = shift_chord_dist * math.cos(theta)
        
        self.lbl_p1p4.center_x = rect_x + rect_w * 0.33 + dx
        self.lbl_p1p4.center_y = rect_y + rect_h * 0.33 + dy
        self.lbl_p2p3.center_x = rect_x + rect_w * 0.67 - dx
        self.lbl_p2p3.center_y = rect_y + rect_h * 0.33 + dy

        target_w = rect_w - dp(100)
        target_h = rect_h - dp(100)
        S_w = target_w / 3.9
        S_h = target_h / 2.4
        S = max(dp(12), min(S_w, S_h))
        
        self.watermark_lbl.font_size = f"{int(S)}dp"
        self.watermark_lbl.pos = (rect_x, rect_y + dp(15))
        self.watermark_lbl.size = (rect_w, rect_h)
        self.watermark_lbl.text_size = (rect_w, rect_h)

        self.watermark_layout.canvas.before.clear()
        self.watermark_layout.canvas.after.clear()
            
        with self.canvas.before:
            Color(0.85, 0.85, 0.85, 1)
            Rectangle(pos=self.pos, size=self.size)
            Color(0.78, 0.78, 0.78, 0.4)
            for i in range(0, int(self.height), int(dp(6))):
                Line(points=[self.x, self.y + i, self.x + self.width, self.y + i], width=0.8)
            
            if app:
                text = app.get_render_texture()
                if text:
                    Color(1, 1, 1, 1)
                    Rectangle(pos=(rect_x, rect_y), size=(rect_w, rect_h), texture=text)
                    self.watermark_lbl.opacity = 0
                else:
                    Color(0, 0, 0, 1)
                    Line(rectangle=(rect_x, rect_y, rect_w, rect_h), width=2)
                    self.draw_dashed(rect_x, rect_y, rect_x + rect_w, rect_y + rect_h)
                    self.draw_dashed(rect_x, rect_y + rect_h, rect_x + rect_w, rect_y)
                    self.watermark_lbl.opacity = 1
            else:
                Color(0, 0, 0, 1)
                Line(rectangle=(rect_x, rect_y, rect_w, rect_h), width=2)
                self.watermark_lbl.opacity = 1
                
            Color(0, 0, 0, 1)
            for px, py in [(rect_x, rect_y), (rect_x + rect_w, rect_y), (rect_x, rect_y + rect_h), (rect_x + rect_w, rect_y + rect_h)]:
                Line(circle=(px, py, 4), width=1.8)
            
            ax_y = rect_y - dp(22)
            x_start = rect_x + rect_w * 0.2
            x_end = rect_x + rect_w * 0.8
            Line(points=[x_start, ax_y, x_end, ax_y], width=1.5)
            Line(points=[x_end - dp(6), ax_y - dp(4), x_end, ax_y, x_end - dp(6), ax_y + dp(4)], width=1.5)
            
            ay_x = rect_x - dp(22)
            y_start = rect_y + rect_h * 0.2
            y_end = rect_y + rect_h * 0.8
            Line(points=[ay_x, y_start, ay_x, y_end], width=1.5)
            Line(points=[ay_x - dp(4), y_end - dp(6), ay_x, y_end, ay_x + dp(4), y_end - dp(6)], width=1.5)

        self.lbl_x.pos = (x_end + dp(4), ax_y - dp(10))
        self.lbl_y.pos = (ay_x - dp(10), y_end + dp(2))

        if app and app.soil_contaminated and not app.get_cut_segments():
            self.btn_help.text = app.translate("Help") if hasattr(app, 'translate') else "Help"
            self.btn_help.opacity = 1
            self.btn_help.disabled = False
            face_center_y = rect_y + rect_h / 2
            face_radius_y = rect_h * 0.15
            self.btn_help.center_x = rect_x + rect_w / 2
            self.btn_help.top = face_center_y - face_radius_y - dp(15)
        else:
            self.btn_help.opacity = 0
            self.btn_help.disabled = True

    def draw_dashed(self, x1, y1, x2, y2):
        dist = math.hypot(x2-x1, y2-y1)
        if dist == 0:
            return
        ux, uy = (x2-x1)/dist, (y2-y1)/dist
        for i in range(int(dist // 15)):
            sx, sy = x1 + i*15*ux, y1 + i*15*uy
            Line(points=[sx, sy, sx+9*ux, sy+9*uy], width=1.2)

    def on_touch_down(self, touch):
        return super().on_touch_down(touch)


class LogoPlate(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(4)
        self.bind(pos=self.draw_plate, size=self.draw_plate)
        self.lbl = Label(text="[b][size=12sp][color=#1c1c1c]cornix[/color][/size]\n[size=12sp][color=#2a2a2a]Winner[/color][/size] [size=16sp][color=#0a0a0a]PRO[/color][/size][/b]", markup=True, halign='center', valign='middle')
        self.lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        self.add_widget(self.lbl)

    def draw_plate(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(1, 1, 1, 0.4)
            RoundedRectangle(pos=(self.x, self.y - dp(1)), size=self.size, radius=[dp(6)])
            Color(0.85, 0.85, 0.85, 1)
            RoundedRectangle(pos=(self.x+dp(1), self.y+dp(1)), size=(self.width-dp(2), self.height-dp(2)), radius=[dp(6)])
            Color(0.1, 0.1, 0.2, 0.2)
            Line(rounded_rectangle=(self.x+dp(1), self.y+dp(1), self.width-dp(2), self.height-dp(2), dp(6)), width=1)


class KeypadPopup(Popup):
    def __init__(self, target_widget, callback, **kwargs):
        super().__init__(**kwargs)
        self.target_widget = target_widget
        self.callback = callback
        app = App.get_running_app()
        lang = app.lang if app else 'en'
        title_text = f": {target_widget.label_text}"
        if app and hasattr(app, 'translate'):
            title_text = app.translate(title_text)
        self.title = title_text
        self.size_hint = (0.85, 0.9)
        self.auto_dismiss = False
        self.current_value = ""
        
        layout = BoxLayout(orientation='vertical', spacing=5, padding=10)
        self.display = Label(text="0", font_size='22sp', bold=True, size_hint_y=0.2, color=[0.95, 0.95, 0.1, 1])
        layout.add_widget(self.display)
        
        grid = GridLayout(cols=4, spacing=5)
        del_text = "پاک" if lang == 'fa' else "Delet"
        can_text = "لغو" if lang == 'fa' else "Cancel"
        ok_text = "تایید" if lang == 'fa' else "OK"
        
        btns = [
            ('1','n'),('2','n'),('3','n'),(del_text,'d'),
            ('4','n'),('5','n'),('6','n'),('< C','c'),
            ('7','n'),('8','n'),('9','n'),(can_text,'x'),
            ('.','n'),('0','n'),(ok_text,'o'),('',None)
        ]
        for t, m in btns:
            if not t:
                grid.add_widget(Widget())
                continue
            c, pc = ([0.18,0.65,0.28,1],[0.1,0.4,0.1,1]) if m=='o' else (([0.8,0.2,0.1,1],[0.5,0.1,0.1,1]) if m in ['d','c','x'] else ([0.3,0.3,0.3,1],[0.2,0.2,0.2,1]))
            b = PlasticButton(text=t, btn_color=c)
            b.bind(on_release=getattr(self, 'press_'+m if m else 'dismiss'))
            grid.add_widget(b)
        layout.add_widget(grid)
        self.content = layout

    def press_n(self, i):
        self.current_value += i.text
        self.display.text = self.current_value

    def press_c(self, i):
        self.current_value = self.current_value[:-1]
        self.display.text = self.current_value or "0"

    def press_d(self, i):
        self.current_value = ""
        self.display.text = "0"

    def press_x(self, i):
        self.dismiss()

    def press_o(self, i):
        if self.current_value:
            self.callback(self.target_widget, self.current_value)
        self.dismiss()


class VirtualKeyboardPopup(Popup):
    def __init__(self, title, callback, default_text="", **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.callback = callback
        self.current_value = default_text
        app = App.get_running_app()
        self.current_lang = app.lang if app else 'en'
        self.is_shift = False
        self.size_hint = (0.9, 0.9)
        self.auto_dismiss = False
        
        self.main_layout = BoxLayout(orientation='vertical', spacing=dp(4), padding=dp(6))
        self.display_box = BoxLayout(size_hint_y=0.15, padding=dp(2))
        self.display_lbl = Label(text="", font_size='14sp', bold=True, halign='center', valign='middle')
        self.display_lbl.bind(size=self.display_lbl.setter('text_size'))
        self.display_box.add_widget(self.display_lbl)
        self.main_layout.add_widget(self.display_box)
        
        self.grid_container = BoxLayout(orientation='vertical', spacing=dp(3), size_hint_y=0.7)
        self.main_layout.add_widget(self.grid_container)
        
        ctrl_row = BoxLayout(spacing=dp(3), size_hint_y=0.15)
        self.btn_ok = PlasticButton(text="OK", btn_color=[0.1, 0.6, 0.2, 1])
        self.btn_ok.bind(on_release=self.press_ok)
        self.btn_cancel = PlasticButton(text="Cancel", btn_color=[0.8, 0.2, 0.2, 1])
        self.btn_cancel.bind(on_release=self.dismiss)
        
        ctrl_row.add_widget(self.btn_cancel)
        ctrl_row.add_widget(self.btn_ok)
        self.main_layout.add_widget(ctrl_row)
        
        self.content = self.main_layout
        self.build_keyboard()
        self.update_display()
        self.bind(pos=self.update_display_bg, size=self.update_display_bg)

    def update_display_bg(self, *args):
        self.display_box.canvas.before.clear()
        with self.display_box.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            RoundedRectangle(pos=self.display_box.pos, size=self.display_box.size, radius=[dp(5)])
            Color(0.3, 0.3, 0.3, 1)
            Line(rounded_rectangle=(self.display_box.x, self.display_box.y, self.display_box.width, self.display_box.height, dp(5)), width=1.1)

    def build_keyboard(self):
        self.grid_container.clear_widgets()
        en_rows = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', '-'],
            ['Shift', 'z', 'x', 'c', 'v', 'b', 'n', 'm', 'BACK'],
            ['LANG', '_', 'Space', '.', 'CLR']
        ]
        fa_rows = [
            ['۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹', '۰'],
            ['ض', 'ص', 'ث', 'ق', 'ف', 'غ', 'ع', 'ه', 'خ', 'ح', 'ج', 'چ'],
            ['ش', 'س', 'ی', 'ب', 'ل', 'ا', 'ت', 'ن', 'م', 'ک', 'گ'],
            ['Shift', 'ظ', 'ط', 'ز', 'ر', 'ذ', 'د', 'پ', 'و', 'ژ', 'آ', 'BACK'],
            ['LANG', '_', 'Space', '.', 'CLR']
        ]
        
        layout = en_rows if self.current_lang == 'en' else fa_rows
        for row in layout:
            row_box = BoxLayout(spacing=dp(3))
            for key in row:
                display_text = key
                btn_color = [0.25, 0.25, 0.25, 1]
                size_hint_x = 1.0
                if key == 'LANG':
                    display_text = "FA" if self.current_lang == 'en' else "EN"
                    btn_color = [0.1, 0.45, 0.75, 1]
                    size_hint_x = 1.5
                elif key == 'CLR':
                    display_text = "Clear" if self.current_lang == 'en' else "پاک"
                    btn_color = [0.6, 0.4, 0.1, 1]
                    size_hint_x = 1.5
                elif key == 'BACK':
                    display_text = "< C"
                    btn_color = [0.45, 0.15, 0.15, 1]
                    size_hint_x = 1.5
                elif key == 'Shift':
                    display_text = "Shift"
                    btn_color = [0.15, 0.6, 0.6, 1] if self.is_shift else [0.35, 0.35, 0.35, 1]
                    size_hint_x = 1.5
                elif key == 'Space':
                    display_text = "Space" if self.current_lang == 'en' else "فاصله"
                    btn_color = [0.4, 0.4, 0.4, 1]
                    size_hint_x = 5.0
                
                if self.current_lang == 'en' and len(key) == 1 and key.isalpha():
                    display_text = key.upper() if self.is_shift else key.lower()
                
                btn = PlasticButton(text=display_text, btn_color=btn_color, size_hint_x=size_hint_x)
                btn.bind(on_release=lambda instance, k=key: self.press_key(k))
                row_box.add_widget(btn)
            self.grid_container.add_widget(row_box)
        self.btn_cancel.text = "Cancel" if self.current_lang == 'en' else "انصراف"

    def press_key(self, key):
        if key == 'LANG':
            self.current_lang = 'fa' if self.current_lang == 'en' else 'en'
            self.build_keyboard()
            self.update_display()
        elif key == 'CLR':
            self.current_value = ""
            self.update_display()
        elif key == 'BACK':
            self.current_value = self.current_value[:-1]
            self.update_display()
        elif key == 'Shift':
            self.is_shift = not self.is_shift
            self.build_keyboard()
        elif key == 'Space':
            self.current_value += " "
            self.update_display()
        else:
            char = key
            if self.current_lang == 'en' and char.isalpha():
                char = char.upper() if self.is_shift else char.lower()
            self.current_value += char
            self.update_display()

    def update_display(self):
        if self.current_value:
            self.display_lbl.text = self.current_value
            self.display_lbl.color = [0.95, 0.95, 0.1, 1]
        else:
            self.display_lbl.text = "Enter Name..." if self.current_lang == 'en' else "نام فایل را وارد کنید..."
            self.display_lbl.color = [0.5, 0.5, 0.5, 1]

    def press_ok(self, *args):
        self.callback(self.current_value)
        self.dismiss()


class MainApp(App):
    width_val = NumericProperty(5.0)
    length_val = NumericProperty(5.0)

    def build(self):
        self._cached_render_texture = None
        self.edge_keys = ["p1p2", "p2p4", "p4p3", "p3p1", "p1p4", "p2p3"]
        self.side_keys = ["p1p2", "p2p4", "p4p3", "p3p1"]
        self.diag_keys = ["p1p4", "p2p3"]
        
        self.entry_values = {k: "" for k in self.edge_keys}
        self.ui_entry_values = {k: "" for k in self.edge_keys}
        self.ui_width_val = 5.0
        self.ui_length_val = 5.0
        self.ui_ref_soil_val = 600.0
        
        self.chord_pull = 35.0
        self.void_pull = 50.0
        self.min_diameter = 0.10
        self.max_diameter = 0.50
        self.PURPLE = "#8000FF"
        
        self.heatmap_data = None
        self.min_point = None
        self.max_point = None
        self.detected_circles = []
        self.warning_arrows = []
        
        self.ref_soil_val = 600.0
        self.soil_contaminated = False
        self.center_red_focus_mode = False
        self.show_depth_overlay = True
        self.gpr_active = False
        self.fibo_active = False
        self.compare_active = False
        self.show_geo_var = True
        
        self.scanning = False
        self.scan_cols = 45
        self.scan_rows = 45
        self.scan_grid = None
        self.scan_current_col = 0
        self.scan_current_row = 0
        self.scan_direction_up = True
        self.sampled_points = []
        self.final_min_points = []
        self.transition_step = 0
        self.gpr_fibo_skeleton_visible = False
        
        self.expand_pos_count = 0
        self.expand_neg_count = 0
        self.expansion_level = 0
        self.signal_correction_level = 0
        
        self.history = []
        self.history_index = -1
        self.lang = 'en'
        self.loaded_scan_name = ""

        self.root_layout = BoxLayout(orientation='vertical', padding=dp(6), spacing=dp(6))
        self.root_layout.bind(size=self.on_resize)
        Window.bind(on_size=self.on_resize)
        
        self.monitor = MonitorView()
        self.control_panel = BoxLayout(orientation='vertical', spacing=dp(4))
        
        self.setup_ui()
        self.set_lang('en')
        self.push_state()
        
        self.blink_state = True
        Clock.schedule_interval(self.toggle_blink, 0.5)
        return self.root_layout

    def toggle_blink(self, dt):
        if self.get_cut_segments():
            self.blink_state = not self.blink_state
            self.invalidate_render_cache()
            if hasattr(self, 'monitor') and self.monitor:
                self.monitor.redraw()

    def get_cut_segments(self):
        cuts = []
        for key in self.edge_keys:
            val = self.safe_float(self.ui_entry_values.get(key, ""))
            if val is not None and val > 100000:
                cuts.append(key)
        return cuts

    def check_cuts_and_warn(self):
        if self.get_cut_segments():
            self.show_popup("Error", "Cannot scan. Probe is disconnected." if self.lang=='en' else "امکان اسکن وجود ندارد. پراپ قطع است.")
            return True
        return False

    def convert_digits(self, text):
        if self.lang != 'fa' or not text:
            return text
        farsi_digits = "۰۱۲۳۴۵۶۷۸۹"
        english_digits = "0123456789"
        translation_table = str.maketrans(english_digits, farsi_digits)
        return text.translate(translation_table)

    def translate(self, text):
        if not text:
            return ""
        if self.lang == 'en':
            if text == "copper":
                return "Cooper"
            return text
            
        translations = {
            "Help": "راهنما",
            "Target 1:\nX=                         Y=\nDepth (H) = —": "هدف ۱:\nX=                         Y=\nعمق (H) = —",
            "Target 2:\nX=                         Y=\nDepth (H) = —": "هدف ۲:\nX=                         Y=\nعمق (H) = —",
            "Compare\n 3 Scans": "مقایسه\n۳ اسکن",
            "Press the\nSTART\nFor Scan": "برای اسکن\nشروع را\nفشار دهید",
            "Width": "عرض",
            "Lenght": "طول",
            "Soil Ref": "خاک مرجع",
            "GEO Scan": "اسکن زمین",
            "Fibo Scan": "اسکن فیبو",
            "GPR Scan": "اسکن رادار",
            "Reset": "راه‌اندازی مجدد",
            "Save Memory": "ذخیره حافظه",
            "Recall Memory": "فراخوانی حافظه",
            "< Back Scan": "اسکن قبل >",
            "Forward Scan >": "< اسکن بعد",
            "Save JPG": "ذخیره عکس",
            "Please run scan first.": "لطفاً ابتدا اسکن را اجرا کنید.",
            "Maximum 10 expansion steps.": "حداکثر ۱۰ مرحله گسترش.",
            "Maximum 10 contraction steps.": "حداکثر ۱۰ مرحله انقباض.",
            "No saved scans found": "هیچ اسکن ذخیره شده‌ای یافت نشد",
            "No json files found": "هیچ فایل اسکن json یافت نشد",
            "Scan recalled successfully!": "اسکن با موفقیت فراخوانی شد!",
            "Failed to load scan:": "خطا در بارگذاری اسکن:",
            "Save Memory to:": "ذخیره حافظه در:",
            "Internal Storage": "حافظه داخلی",
            "External Storage": "حافظه خارجی",
            "Cancel": "انصراف",
            "Save Image to:": "ذخیره تصویر در:",
            "Save Image": "ذخیره تصویر",
            "Success": "موفقیت",
            "Success (Fallback)": "ذظیره امن",
            "Error": "خطا",
            "Close": "بستن",
            "Contamination Warning": "هشدار آلودگی خاک",
            "Void": "حفره (Void)",
            "Small Void": "حفره کوچک (Small Void)",
            "Medium Void": "حفره متوسط (Medium Void)",
            "Big Void": "حفره بزرگ (Big Void)",
            "No Target": "بدون هدف (No Target)",
            "water": "آب",
            "gold": "طلا",
            "silver": "نقره",
            "copper": "مس",
            "brass": "برنج",
            "iron": "آهن",
            "natural": "طبیعی",
            "Unknown": "نامشخص",
            "Search: [Click to type]": "جستجو: [کلیک کنید]",
            "Select Scan File": "انتخاب فایل اسکن",
            "No matches found": "موردی یافت نشد",
            "Type query / متن جستجو را وارد کنید": "جستجو را وارد کنید",
            "Enter Filename": "نام فایل را وارد کنید",
            "Enter Name...": "نام را وارد کنید...",
            "Work Report": "گزارش\nکار",
            "Next Target": "تارگت بعدی",
            "Target 1 Report": "گزارش تارگت ۱",
            "Target 2 Report": "گزارش تارگت ۲",
        }
        
        if "Scan saved successfully to:" in text:
            path = text.split(":\n")[-1]
            return self.shape_text(f"اسکن با موفقیت ذخیره شد در:\n{path}")
        if "Screenshot saved successfully to:" in text:
            path = text.split(":\n")[-1]
            return self.shape_text(f"تصویر با موفقیت ذخیره شد در:\n{path}")
        if "Public write failed. Saved to App safe storage:" in text:
            path = text.split(":\n")[-1]
            return self.shape_text(f"خطای مجوز صادر شد. در پوشه امن برنامه ذخیره شد:\n{path}")
        if "Could not save file:" in text:
            err = text.split(":\n")[-1]
            return self.shape_text(f"فایل ذخیره نشد:\n{err}")

        translated = translations.get(text, text)
        return self.shape_text(translated)

    def shape_text(self, text):
        global arabic_reshaper, get_display
        if self.lang != 'fa' or not text:
            return text
        if not any((ord(c) >= 0x0600 and ord(c) <= 0x06FF) for c in text):
            return text
        if arabic_reshaper is None or get_display is None:
            try:
                import arabic_reshaper as ar
                from bidi.algorithm import get_display as gd
                arabic_reshaper = ar
                get_display = gd
            except ImportError:
                pass
        if arabic_reshaper is not None and get_display is not None:
            try:
                reshaped = arabic_reshaper.reshape(text)
                bidi_text = get_display(reshaped)
                return bidi_text
            except Exception:
                pass
        return text[::-1]

    def update_ui_language(self):
        self.btn_compare.text = self.translate("Compare\n 3 Scans")
        self.btn_report.text = self.translate("Work Report")
        self.btn_start.text = self.translate("Press the\nSTART\nFor Scan")
        self.in_w.label_text = self.translate("Width")
        self.in_w.update_text()
        self.in_l.label_text = self.translate("Lenght")
        self.in_l.update_text()
        self.in_ref.label_text = self.translate("Soil Ref")
        self.in_ref.update_text()
        self.btn_geo.text = self.translate("GEO Scan")
        self.btn_fibo.text = self.translate("Fibo Scan")
        self.btn_gpr.text = self.translate("GPR Scan")
        self.btn_reset.text = self.translate("Reset")
        self.btn_save.text = self.translate("Save Memory")
        self.btn_recall.text = self.translate("Recall Memory")
        self.btn_undo.text = self.translate("< Back Scan")
        self.btn_redo.text = self.translate("Forward Scan >")
        self.btn_save_jpg.text = self.translate("Save JPG")
        for seg_btn in self.segs:
            seg_btn.update_text()
        self.update_target_boxes()
        self.monitor.redraw()

    def invalidate_render_cache(self):
        self._cached_render_texture = None

    def on_resize(self, *args):
        if Window.width > Window.height:
            self.root_layout.orientation = 'horizontal'
            self.monitor.size_hint = (0.48, 1)
            self.control_panel.size_hint = (0.52, 1)
        else:
            self.root_layout.orientation = 'vertical'
            self.monitor.size_hint = (1, 0.48)
            self.control_panel.size_hint = (1, 0.52)
        self._update_bg()
        self.monitor.redraw()

    def setup_ui(self):
        mid = GridLayout(cols=2, spacing=dp(4), size_hint_y=0.4)
        l_sub = BoxLayout(orientation='vertical', spacing=dp(3))
        self.t1 = Label(text="Target 1:\nX=                         Y=\nDepth (H) = —", font_size='10sp', bold=True, color=[0.1, 0.1, 0.1, 1], markup=True, halign='left', valign='middle', padding=[dp(15), 0])
        self.t2 = Label(text="Target 2:\nX=                         Y=\nDepth (H) = —", font_size='10sp', bold=True, color=[0.1, 0.1, 0.1, 1], markup=True, halign='left', valign='middle', padding=[dp(15), 0])
        for t in [self.t1, self.t2]:
            t.bind(pos=self._update_target_bg, size=self._update_target_bg)
            t.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            l_sub.add_widget(t)
        l_sub.add_widget(LogoPlate(size_hint_y=0.4))
        
        r_sub = BoxLayout(orientation='vertical', spacing=dp(3))
        deep_compare_layout = BoxLayout(spacing=dp(3))
        self.btn_compare = PlasticButton(text="Compare\n 3 Scans", btn_color=[0.5, 0.4, 0.6, 1], size_hint_x=0.5)
        self.btn_compare.bind(on_release=self.compare_click)
        self.btn_report = PlasticButton(text="Work\nReport", btn_color=[0.31, 0.45, 0.58, 1], size_hint_x=0.5)
        self.btn_report.bind(on_release=self.show_report_popup)
        deep_compare_layout.add_widget(self.btn_compare)
        deep_compare_layout.add_widget(self.btn_report)
        r_sub.add_widget(deep_compare_layout)
        
        s_row = BoxLayout(spacing=dp(3))
        pm = BoxLayout(orientation='vertical', spacing=dp(3))
        self.btn_minus = PlasticButton(text="—", btn_color=[0.11, 0.51, 0.84, 1])
        self.btn_minus.bind(on_release=self.minus_click)
        self.btn_plus = PlasticButton(text="+", btn_color=[0.84, 0.17, 0.12, 1])
        self.btn_plus.bind(on_release=self.plus_click)
        pm.add_widget(self.btn_plus)
        pm.add_widget(self.btn_minus)
        
        self.btn_start = PlasticButton(text="Press the\nSTART\nFor Scan", btn_color=[0.84, 0.17, 0.12, 1])
        self.btn_start.bind(on_release=self.refresh_scan)
        s_row.add_widget(pm)
        s_row.add_widget(self.btn_start)
        r_sub.add_widget(s_row)
        mid.add_widget(l_sub)
        mid.add_widget(r_sub)
        self.control_panel.add_widget(mid)

        r3 = BoxLayout(spacing=dp(3), size_hint_y=0.18)
        self.in_w = RecessedInput(label_text="Width", value_text="5.0 M", size_hint_x=0.13)
        self.in_l = RecessedInput(label_text="Lenght", value_text="5.0 M", size_hint_x=0.13)
        self.in_ref = RecessedInput(label_text="Soil Ref", value_text="600", size_hint_x=0.15)
        for i in [self.in_w, self.in_l, self.in_ref]:
            i.bind(on_release=self.open_keypad)
        r3.add_widget(self.in_w)
        r3.add_widget(self.in_l)
        r3.add_widget(self.in_ref)
        
        self.btn_geo = PlasticButton(text="GEO Scan", btn_color=[0.2, 0.4, 0.4, 1], size_hint_x=0.196)
        self.btn_geo.bind(on_release=self.geo_click)
        self.btn_geo.is_active = True
        self.btn_fibo = PlasticButton(text="Fibo Scan", btn_color=[0.4, 0.2, 0.4, 1], size_hint_x=0.196)
        self.btn_fibo.bind(on_release=self.fibo_click)
        self.btn_gpr = PlasticButton(text="GPR Scan", btn_color=[0.4, 0.4, 0.2, 1], size_hint_x=0.196)
        self.btn_gpr.bind(on_release=self.gpr_click)
        r3.add_widget(self.btn_geo)
        r3.add_widget(self.btn_fibo)
        r3.add_widget(self.btn_gpr)
        self.control_panel.add_widget(r3)

        r4 = BoxLayout(spacing=dp(2), size_hint_y=0.13)
        self.segs = []
        for s in ["P1P2", "P2P4", "P4P3", "P3P1", "P1P4", "P2P3"]:
            b = RecessedInput(label_text=s)
            b.bind(on_release=self.open_keypad)
            self.segs.append(b)
            r4.add_widget(b)
        self.control_panel.add_widget(r4)

        r5 = BoxLayout(spacing=dp(3), size_hint_y=0.15)
        lang = BoxLayout(spacing=dp(2), size_hint_x=0.2)
        self.btn_en = PlasticButton(text="EN", is_active=True)
        self.btn_fa = PlasticButton(text="FA")
        self.btn_en.bind(on_release=lambda x: self.set_lang('en'))
        self.btn_fa.bind(on_release=lambda x: self.set_lang('fa'))
        lang.add_widget(self.btn_en)
        lang.add_widget(self.btn_fa)
        r5.add_widget(lang)
        
        self.btn_reset = PlasticButton(text="Reset", btn_color=[0.9, 0.7, 0.1, 1], size_hint_x=0.2)
        self.btn_reset.bind(on_release=self.reset_all)
        self.btn_save = PlasticButton(text="Save Memory", btn_color=[0.1, 0.6, 0.2, 1], size_hint_x=0.3)
        self.btn_save.bind(on_release=self.save_memory_click)
        self.btn_recall = PlasticButton(text="Recall Memory", btn_color=[1, 0.4, 0.7, 1], size_hint_x=0.3)
        self.btn_recall.bind(on_release=self.recall_memory_click)
        r5.add_widget(self.btn_reset)
        r5.add_widget(self.btn_save)
        r5.add_widget(self.btn_recall)
        self.control_panel.add_widget(r5)

        r6 = BoxLayout(spacing=dp(3), size_hint_y=0.13)
        self.btn_undo = PlasticButton(text="< Back Scan", btn_color=[0.8, 0.4, 0.1, 1])
        self.btn_undo.bind(on_release=self.undo_click)
        self.btn_redo = PlasticButton(text="Forward Scan >", btn_color=[0.1, 0.5, 0.8, 1])
        self.btn_redo.bind(on_release=self.redo_click)
        self.btn_save_jpg = PlasticButton(text="Save JPG", btn_color=[0.1, 0.6, 0.2, 1])
        self.btn_save_jpg.bind(on_release=self.save_jpeg_click)
        r6.add_widget(self.btn_undo)
        r6.add_widget(self.btn_redo)
        r6.add_widget(self.btn_save_jpg)
        self.control_panel.add_widget(r6)

        self.root_layout.add_widget(self.monitor)
        self.root_layout.add_widget(self.control_panel)

    def set_lang(self, l):
        self.lang = l
        self.btn_en.is_active = (l == 'en')
        self.btn_fa.is_active = (l == 'fa')
        self.update_ui_language()

    def _update_bg(self, *args):
        self.root_layout.canvas.before.clear()
        with self.root_layout.canvas.before:
            Color(0.72, 0.72, 0.72, 1)
            Rectangle(pos=self.root_layout.pos, size=self.root_layout.size)
            Color(0.65, 0.65, 0.65, 0.2)
            for i in range(0, int(self.root_layout.height), int(dp(9))):
                Line(points=[self.root_layout.x, self.root_layout.y+i, self.root_layout.x+self.root_layout.width, self.root_layout.y+i], width=1)

    def _update_target_bg(self, i, v=None):
        i.canvas.before.clear()
        with i.canvas.before:
            if self.compare_active or self.get_cut_segments():
                Color(1.0, 1.0, 1.0, 1.0)
            else:
                Color(0.92, 0.83, 0.48, 1)
            RoundedRectangle(pos=(i.x+dp(1), i.y+dp(1)), size=(i.width-dp(2), i.height-dp(2)), radius=[dp(5)])
            if self.compare_active or self.get_cut_segments():
                Color(0, 0, 0, 0.15)
            else:
                Color(0, 0, 0, 0.2)
            Line(points=[i.x+dp(2), i.y+i.height-dp(2), i.x+i.width-dp(2), i.y+i.height-dp(2)], width=1)

    def open_keypad(self, i):
        KeypadPopup(target_widget=i, callback=self.keypad_callback).open()

    def keypad_callback(self, t, v):
        if t in self.segs:
            t.value_text = v
            for key, b in zip(self.edge_keys, self.segs):
                if b == t:
                    self.ui_entry_values[key] = v
        else:
            if t == self.in_ref:
                t.value_text = v
                try:
                    self.ui_ref_soil_val = float(v)
                except Exception:
                    pass
            else:
                t.value_text = f"{v} M"
                try:
                    if t == self.in_w:
                        self.ui_width_val = float(v)
                    elif t == self.in_l:
                        self.ui_length_val = float(v)
                except Exception:
                    pass
        self.push_state()
        if self.get_cut_segments():
            self.scanning = False
            self.fibo_active = False
            self.gpr_active = False
        self.monitor.redraw()

    def safe_float(self, value):
        try:
            return float(value)
        except Exception:
            return None

    def clamp(self, value, lo, hi):
        return max(lo, min(hi, value))

    def _update_target_text(self, target_label, value_m):
         return f"{self.translate(target_label)}: {self.convert_digits(f'{value_m:.2f} M')}"

    def lerp(self, a, b, t):
        return a + (b - a) * t

    def hex_to_rgb(self, hex_str):
        hex_str = hex_str.lstrip('#')
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

    def point_to_segment_distance(self, px, py, x1, y1, x2, y2):
        vx = x2 - x1
        vy = y2 - y1
        wx = px - x1
        wy = py - y1
        c1 = vx * wx + vy * wy
        if c1 <= 0:
            return math.hypot(px - x1, py - y1)
        c2 = vx * vx + vy * vy
        if c2 <= 1e-12:
            return math.hypot(px - x1, py - y1)
        t = c1 / (vx * vx + vy * vy)
        if t >= 1:
            return math.hypot(px - x2, py - y2)
        projx = x1 + t * vx
        projy = y1 + t * vy
        return math.hypot(px - projx, py - projy)

    def project_point_to_segment(self, px, py, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        seg_len2 = dx * dx + dy * dy
        if seg_len2 <= 1e-12:
            return x1, y1
        t = ((px - x1) * dx + (py - y1) * dy) / seg_len2
        t = self.clamp(t, 0.0, 1.0)
        return x1 + t * dx, y1 + t * dy

    def is_value_in_main_range(self, v):
        return v is not None and 0 <= v <= 100000

    def should_allow_circle_rendering(self, vals):
        return any(self.is_value_in_main_range(vals.get(k)) for k in self.edge_keys)

    def filter_circles_for_display(self, circles, vals):
        if not circles:
            return []
        if not self.should_allow_circle_rendering(vals):
            return []
        return circles

    def valid_entries_dict(self):
        vals = {}
        ref_soil = getattr(self, 'ref_soil_val', 600.0)
        if ref_soil <= 0:
            ref_soil = 600.0
        if ref_soil < 600.0:
            gamma = math.pow(ref_soil / 600.0, 1.6)
            beta = math.pow(600.0 / ref_soil, 0.6)
        else:
            gamma = math.pow(ref_soil / 600.0, 0.6)
            beta = math.pow(600.0 / ref_soil, 0.5)
        for key in self.edge_keys:
            raw_v = self.safe_float(self.entry_values.get(key, ""))
            if raw_v is not None:
                ratio = raw_v / ref_soil
                if ratio < 1.0:
                    corrected_v = 600.0 * math.pow(ratio, gamma)
                else:
                    corrected_v = 600.0 * math.pow(ratio, beta)
                vals[key] = corrected_v
            else:
                vals[key] = None
        return vals

    def color_from_stops(self, value, vmin, vmax, stops):
        if abs(vmax - vmin) < 1e-12:
            t = 0.5
        else:
            t = self.clamp((value - vmin) / (vmax - vmin), 0.0, 1.0)
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                u = (t - t0) / (t1 - t0) if abs(t1 - t0) > 1e-12 else 0.0
                r = int(self.lerp(c0[0], c1[0], u))
                g = int(self.lerp(c0[1], c1[1], u))
                b = int(self.lerp(c0[2], c1[2], u))
                return (r, g, b)
        rr, gg, bb = stops[-1][1]
        return (rr, gg, bb)

    def classify_target(self, v):
        if v is None or v < 0 or v > 100000:
            return ("natural", "#00AA00", "#FFFFFF")
        if 0 <= v <= 100:
            return ("silver", "#808080", "#FFFFFF")
        elif 100 <= v <= 150:
            return ("gold", "#FF0000", "#FFFFFF")
        elif 150 <= v <= 250:
            return ("copper", "#FFA500", "#000000")
        elif 250 <= v <= 350:
            return ("brass", "#FFD700", "#000000")
        elif 350 <= v <= 500:
            return ("iron", "#8B4513", "#FFFFFF")
        elif 500 <= v <= 700:
            return ("No Target", "#D3D3D3", "#000000")
        elif 700 <= v <= 1100:
            return ("water", "#0000FF", "#FFFFFF")
        elif 1100 <= v <= 3000:
            return ("No Target", "#D3D3D3", "#000000")
        elif 3000 <= v <= 15000:
            return ("Small Void", self.PURPLE, "#FFFFFF")
        elif 15000 <= v <= 25000:
            return ("Medium Void", self.PURPLE, "#FFFFFF")
        elif 25000 <= v <= 100000:
            return ("Big Void", self.PURPLE, "#FFFFFF")
        return ("No Target", "#D3D3D3", "#000000")

    def has_void_circle(self):
        for c in self.detected_circles:
            if c.get("label") in ["Void", "Small Void", "Medium Void", "Big Void"]:
                return True
        return False

    def get_closest_edge_or_chord_value(self, xr, yr, vals):
        sides = {
            "p1p2": (0.0, 0.0, 1.0, 0.0),
            "p2p4": (1.0, 0.0, 1.0, 1.0),
            "p4p3": (1.0, 1.0, 0.0, 1.0),
            "p3p1": (0.0, 1.0, 0.0, 0.0)
        }
        chords = {
            "p1p4": (0.0, 0.0, 1.0, 1.0),
            "p2p3": (1.0, 0.0, 0.0, 1.0)
        }
        best_side_dist = float('inf')
        closest_side_key = None
        for key, (x1, y1, x2, y2) in sides.items():
            v = vals.get(key)
            if v is None or not self.is_value_in_main_range(v):
                continue
            dist = self.point_to_segment_distance(xr, yr, x1, y1, x2, y2)
            if dist < best_side_dist:
                best_side_dist = dist
                closest_side_key = key

        best_chord_dist = float('inf')
        closest_chord_key = None
        for key, (x1, y1, x2, y2) in chords.items():
            v = vals.get(key)
            if v is None or not self.is_value_in_main_range(v):
                continue
            dist = self.point_to_segment_distance(xr, yr, x1, y1, x2, y2)
            if dist < best_chord_dist:
                best_chord_dist = dist
                closest_chord_key = key

        side_val = vals.get(closest_side_key) if closest_side_key else None
        chord_val = vals.get(closest_chord_key) if closest_chord_key else None

        if side_val is not None and chord_val is not None:
            return side_val if side_val < chord_val else chord_val
        elif side_val is not None:
            return side_val
        elif chord_val is not None:
            return chord_val
        return None

    def get_closest_line_key(self, cx, cy):
        best_key = None
        min_dist = float('inf')
        for key in self.edge_keys:
            endpoints = self.get_segment_endpoints(key)
            if endpoints[0] is not None and endpoints[1] is not None:
                d = self.point_to_segment_distance(cx, cy, endpoints[0][0], endpoints[0][1], endpoints[1][0], endpoints[1][1])
                if d < min_dist:
                    min_dist = d
                    best_key = key
        return best_key

    def evaluate_skeleton_or_chamber(self, circ):
        val = circ.get("target_value", 0.0)
        label = circ.get("label", "")
        if label in ["water", "natural", "Void", "Small Void", "Medium Void", "Big Void"]:
            return None
        
        cx = circ.get("center_x_ratio", 0.5)
        cy = circ.get("center_y_ratio", 0.5)
        lk = self.get_closest_line_key(cx, cy)
        if not lk:
            return None
            
        vals = self.valid_entries_dict()
        lk_val = vals.get(lk)
        if lk_val is None or not (0 <= lk_val <= 500):
            return None
            
        neighbors = self.line_neighbors().get(lk, [])
        neighbor_vals = [vals.get(nk) for nk in neighbors if vals.get(nk) is not None]
        
        count_700_3000 = sum(1 for v in neighbor_vals if 700 <= v <= 3000)
        count_3000_100000 = sum(1 for v in neighbor_vals if 3000 < v <= 100000)
        
        if count_3000_100000 >= 3:
            return "chamber"
        elif (count_700_3000 >= 3) or (count_700_3000 + count_3000_100000 >= 3):
            return "skeleton"
            
        return None

    def get_closest_matching_input_value(self, xr, yr, vals, target_label, target_value):
        segment_dists = []
        for key in self.edge_keys:
            v = vals.get(key)
            if v is None or not self.is_value_in_main_range(v):
                continue
            endpoints = self.get_segment_endpoints(key)
            if endpoints[0] is not None and endpoints[1] is not None:
                dist = self.point_to_segment_distance(xr, yr, endpoints[0][0], endpoints[0][1], endpoints[1][0], endpoints[1][1])
                segment_dists.append((dist, v, key))
        if not segment_dists:
            return target_value
        segment_dists.sort(key=lambda x: x[0])
        min_dist = segment_dists[0][0]
        candidates = [item for item in segment_dists if item[0] <= min_dist + 0.15]
        candidate_values = [item[1] for item in candidates]
        is_void = (target_value is not None and target_value >= 3000) or (target_label in ["Void", "Small Void", "Medium Void", "Big Void"])
        if is_void:
            return max(candidate_values)
        else:
            return min(candidate_values)

    def resistance_relative_palette_color(self, value, vmin, vmax, invert_for_void=False, x_ratio=None, y_ratio=None):
        if value < 0 or value > 100000:
            return (0, 170, 0)
        if abs(vmax - vmin) < 1e-12:
            t = 0.5
        else:
            t = self.clamp((value - vmin) / (vmax - vmin), 0.0, 1.0)

        if self.expansion_level != 0:
            if self.expansion_level < 0:
                t_green = 0.5
                factor = max(0.0, 1.0 - 0.10 * abs(self.expansion_level))
                t = t_green + (t - t_green) * factor
            else:
                has_void_or_water = False
                if self.detected_circles:
                    for circ in self.detected_circles:
                        if circ.get("label") in ["Void", "Small Void", "Medium Void", "Big Void", "water"]:
                            has_void_or_water = True
                            break
                spatial_bias = 1.0
                if x_ratio is not None and y_ratio is not None:
                    vals = self.valid_entries_dict()
                    if has_void_or_water:
                        largest_edge_key = self.get_largest_edge_key(vals)
                        if largest_edge_key:
                            a, b = self.get_segment_endpoints(largest_edge_key)
                            if a is not None and b is not None:
                                dist_to_edge = self.point_to_segment_distance(x_ratio, y_ratio, a[0], a[1], b[0], b[1])
                                spatial_bias = 1.3 - 0.6 * dist_to_edge
                    else:
                        smallest_side_key = None
                        min_side_val = float('inf')
                        for k in self.side_keys:
                            v = vals.get(k)
                            if v is not None and v < min_side_val:
                                min_side_val = v
                                smallest_side_key = k
                        if smallest_side_key:
                            a, b = self.get_segment_endpoints(smallest_side_key)
                            if a is not None and b is not None:
                                dist_to_edge = self.point_to_segment_distance(x_ratio, y_ratio, a[0], a[1], b[0], b[1])
                                spatial_bias = 1.3 - 0.6 * dist_to_edge
                shift = 0.10 * self.expansion_level * spatial_bias
                if has_void_or_water:
                    t = self.clamp(t + shift, 0.0, 1.0)
                else:
                    t = self.clamp(t - shift, 0.0, 1.0)

        t_smooth = t * t * (3.0 - 2.0 * t)

        if self.fibo_active:
            label_max, color_max, _ = self.classify_target(vmax)
            if label_max in ["Void", "Small Void", "Medium Void", "Big Void"]:
                stops = [
                    (0.00, (0, 100, 30)),     
                    (0.15, (0, 150, 40)),     
                    (0.40, (0, 195, 55)),     
                    (0.60, (110, 210, 50)),   
                    (0.75, (235, 235, 0)),    
                    (0.88, (230, 200, 80)),   
                    (0.95, (220, 180, 230)),  
                    (1.00, (210, 170, 255))   
                ]
            else:
                stops = [
                    (0.00, (0, 100, 30)),
                    (0.03, (0, 120, 35)),
                    (0.07, (0, 140, 40)),
                    (0.15, (0, 160, 45)),
                    (0.35, (0, 195, 55)),
                    (0.50, (0, 220, 75)),
                    (0.60, (0, 195, 55)),
                    (0.70, (0, 205, 65)),     
                    (0.82, (0, 185, 50)),     
                    (0.90, (110, 210, 50)),   
                    (0.97, (130, 180, 45)),   
                    (1.00, (140, 160, 40))    
                ]
            
            rgb_min = (0, 120, 35)
            has_custom_min = False
            if x_ratio is not None and y_ratio is not None and self.detected_circles:
                total_weight = 0.0
                r_sum, g_sum, b_sum = 0.0, 0.0, 0.0
                for circ in self.detected_circles:
                    if circ.get("label") in ["Void", "Small Void", "Medium Void", "Big Void", "natural"]:
                        continue
                    cx, cy = circ["center_x_ratio"], circ["center_y_ratio"]
                    dist = math.hypot(x_ratio - cx, y_ratio - cy)
                    weight = 1.0 / (dist * dist + 1e-4)
                    c_rgb = self.hex_to_rgb(circ.get("fill_color", "#FF0000"))
                    r_sum += c_rgb[0] * weight
                    g_sum += c_rgb[1] * weight
                    b_sum += c_rgb[2] * weight
                    total_weight += weight
                if total_weight > 0.0:
                    rgb_min = (int(r_sum / total_weight), int(g_sum / total_weight), int(b_sum / total_weight))
                    has_custom_min = True

            if not has_custom_min:
                label_min, color_min, _ = self.classify_target(vmin)
                if label_min in ["silver", "gold", "copper", "brass", "iron", "water", "Unknown", "No Target"]:
                    rgb_min = self.hex_to_rgb(color_min)
                    has_custom_min = True

            if has_custom_min:
                stops[0] = (0.00, (max(0, int(rgb_min[0] * 0.5)), max(0, int(rgb_min[1] * 0.5)), max(0, int(rgb_min[2] * 0.5))))
                stops[1] = (0.03, rgb_min)
                stops[2] = (0.07, (max(0, int(self.lerp(rgb_min[0], 0, 0.4))), max(0, int(self.lerp(rgb_min[1], 140, 0.4))), max(0, int(self.lerp(rgb_min[2], 40, 0.4)))))

        elif 700 <= vmin <= 1100:
            stops = [
                (0.00, (0, 0, 150)),
                (0.05, (0, 120, 255)),
                (0.15, (0, 195, 55)),
                (0.50, (0, 205, 75)),
                (1.00, (30, 150, 30))
            ]
        else:
            stops = [
                (0.00, (115, 0, 0)),
                (0.03, (235, 0, 0)),
                (0.07, (255, 90, 0)),
                (0.12, (255, 215, 0)),
                (0.18, (150, 230, 0)),
                (0.50, (0, 195, 55)),
                (0.88, (0, 205, 75)),
                (0.93, (0, 175, 235)),
                (0.96, (0, 65, 220)),
                (0.98, (60, 0, 180)),
                (1.00, (95, 0, 145))
            ]
            rgb_min = (235, 0, 0)
            has_custom_min = False
            if x_ratio is not None and y_ratio is not None and self.detected_circles:
                total_weight = 0.0
                r_sum, g_sum, b_sum = 0.0, 0.0, 0.0
                for circ in self.detected_circles:
                    if circ.get("label") in ["Void", "Small Void", "Medium Void", "Big Void", "natural"]:
                        continue
                    cx, cy = circ["center_x_ratio"], circ["center_y_ratio"]
                    dist = math.hypot(x_ratio - cx, y_ratio - cy)
                    weight = 1.0 / (dist * dist + 1e-4)
                    c_rgb = self.hex_to_rgb(circ.get("fill_color", "#FF0000"))
                    r_sum += c_rgb[0] * weight
                    g_sum += c_rgb[1] * weight
                    b_sum += c_rgb[2] * weight
                    total_weight += weight
                if total_weight > 0.0:
                    rgb_min = (int(r_sum / total_weight), int(g_sum / total_weight), int(b_sum / total_weight))
                    has_custom_min = True

            if not has_custom_min:
                label_min, color_min, _ = self.classify_target(vmin)
                if label_min in ["silver", "gold", "copper", "brass", "iron", "water", "Unknown", "No Target"]:
                    rgb_min = self.hex_to_rgb(color_min)
                    has_custom_min = True

            if has_custom_min:
                stops[0] = (0.00, (max(0, int(rgb_min[0] * 0.5)), max(0, int(rgb_min[1] * 0.5)), max(0, int(rgb_min[2] * 0.5))))
                stops[1] = (0.03, rgb_min)
                stops[2] = (0.07, (max(0, int(self.lerp(rgb_min[0], 255, 0.4))), max(0, int(self.lerp(rgb_min[1], 90, 0.4))), max(0, int(self.lerp(rgb_min[2], 0, 0.4)))))

            if not self.fibo_active:
                label_max, color_max, _ = self.classify_target(vmax)
                if label_max in ["Void", "Small Void", "Medium Void", "Big Void"]:
                    rgb_max = self.hex_to_rgb(color_max)
                    stops[-2] = (0.98, rgb_max)
                    stops[-1] = (1.00, (max(0, int(rgb_max[0] * 0.6)), max(0, int(rgb_max[1] * 0.6)), max(0, int(rgb_max[2] * 0.6))))

        return self.color_from_stops(t_smooth, 0.0, 1.0, stops)

    def build_gaussian_kernel_1d(self, sigma):
        sigma = max(0.01, float(sigma))
        radius = max(1, int(3.0 * sigma))
        kernel = []
        s2 = sigma * sigma
        for i in range(-radius, radius + 1):
            kernel.append(math.exp(-(i * i) / (2.0 * s2)))
        total = sum(kernel)
        return [k / total for k in kernel]

    def gaussian_blur_2d(self, grid, sigma):
        if sigma <= 0.01:
            return [row[:] for row in grid]
        kernel = self.build_gaussian_kernel_1d(sigma)
        radius = len(kernel) // 2
        ny = len(grid)
        nx = len(grid[0]) if ny > 0 else 0
        temp = [[0.0 for _ in range(nx)] for _ in range(ny)]
        for y in range(ny):
            for x in range(nx):
                s = 0.0
                for k in range(-radius, radius + 1):
                    xx = int(self.clamp(x + k, 0, nx - 1))
                    s += grid[y][xx] * kernel[k + radius]
                temp[y][x] = s
        out = [[0.0 for _ in range(nx)] for _ in range(ny)]
        for y in range(ny):
            for x in range(nx):
                s = 0.0
                for k in range(-radius, radius + 1):
                    yy = int(self.clamp(y + k, 0, ny - 1))
                    s += temp[yy][x] * kernel[k + radius]
                out[y][x] = s
        return out

    def line_neighbors(self):
        return {
            "p1p4": ["p1p2", "p3p1", "p2p4", "p4p3"],
            "p2p3": ["p1p2", "p2p4", "p3p1", "p4p3"],
            "p1p2": ["p3p1", "p2p4", "p1p4", "p2p3"],
            "p2p4": ["p1p2", "p4p3", "p1p4", "p2p3"],
            "p4p3": ["p2p4", "p3p1", "p1p4", "p2p3"],
            "p3p1": ["p1p2", "p4p3", "p1p4", "p2p3"],
        }

    def side_diag_relation(self):
        return {
            "p1p2": ["p1p4", "p2p3"], "p2p4": ["p1p4", "p2p3"],
            "p4p3": ["p1p4", "p2p3"], "p3p1": ["p1p4", "p2p3"],
        }

    def is_center_red_focus_condition(self, vals):
        d1 = vals.get("p1p4")
        d2 = vals.get("p2p3")
        if not self.is_value_in_main_range(d1) or not self.is_value_in_main_range(d2):
            return False
        side_vals = [vals.get(k) for k in self.side_keys if self.is_value_in_main_range(vals.get(k))]
        if not side_vals:
            return False
        side_min = min(side_vals)
        side_avg = sum(side_vals) / len(side_vals)
        diag_avg = (d1 + d2) / 2.0
        return (d1 < side_min) and (d2 < side_min) and (side_avg > diag_avg)

    def should_use_center_red_focus(self, vals):
        if not self.is_center_red_focus_condition(vals):
            return False
        side_case = self.get_small_side_candidate_when_diags_dominate(vals)
        if side_case is None:
            return True
        side_val = side_case["side_value"]
        diag_min = side_case["diag_min"]
        if side_val > diag_min:
            return False
        return True

    def values_are_in_same_class_range(self, a, b):
        if not self.is_value_in_main_range(a) or not self.is_value_in_main_range(b):
            return False
        la, _, _ = self.classify_target(a)
        lb, _, _ = self.classify_target(b)
        return la == lb

    def diagonal_side_support(self, diag_key, vals):
        if diag_key == "p1p4":
            group_a, group_b = ["p3p1", "p4p3"], ["p1p2", "p2p4"]
        elif diag_key == "p2p3":
            group_a, group_b = ["p1p2", "p3p1"], ["p2p4", "p4p3"]
        else:
            return {"a": 0.0, "b": 0.0}
        valid_vals = [vv for vv in vals.values() if self.is_value_in_main_range(vv)]
        if not valid_vals:
            return {"a": 0.0, "b": 0.0}
        vmin, vmax = min(valid_vals), max(valid_vals)
        if abs(vmax - vmin) < 1e-12:
            return {"a": 0.0, "b": 0.0}
        def avg_low(group):
            arr = [vals.get(k) for k in group if self.is_value_in_main_range(vals.get(k))]
            if not arr:
                return 0.0
            t = self.clamp((sum(arr)/len(arr) - vmin) / (vmax - vmin), 0.0, 1.0)
            return 1.0 - t
        return {"a": avg_low(group_a), "b": avg_low(group_b)}

    def get_void_special_center_pos(self, vals):
        for k in self.edge_keys:
            v = vals.get(k)
            if v is None or not (3000 <= v <= 100000):
                return None
        v_side = {k: vals[k] for k in self.side_keys}
        v_diag = {k: vals[k] for k in self.diag_keys}
        max_side_val = max(v_side.values())
        if v_diag["p1p4"] <= max_side_val or v_diag["p2p3"] <= max_side_val:
            return None
        d1, d2 = v_diag["p1p4"], v_diag["p2p3"]
        if abs(d1 - d2) < 1e-5:
            return 0.5, 0.5
        largest_side_key = max(v_side, key=v_side.get)
        midpoints = {"p1p2": (0.5, 0.0), "p2p4": (1.0, 0.5), "p4p3": (0.5, 1.0), "p3p1": (0.0, 0.5)}
        mx, my = midpoints[largest_side_key]
        cx = 0.5 + (mx - 0.5) * 0.18
        cy = 0.5 + (my - 0.5) * 0.18
        return self.clamp(cx, 0.05, 0.95), self.clamp(cy, 0.05, 0.95)

    def build_line_sources(self, vals):
        p1, p2, p3, p4 = (0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0)
        mapping = [
            ("p1p2", p1, p2, 1.00, 0.10), ("p2p4", p2, p4, 1.00, 0.10),
            ("p4p3", p4, p3, 1.00, 0.10), ("p3p1", p3, p1, 1.00, 0.10),
            ("p1p4", p1, p4, 1.20, 0.085), ("p2p3", p2, p3, 1.20, 0.085),
        ]
        valid_vals = [v for v in vals.values() if self.is_value_in_main_range(v)]
        if not valid_vals:
            return None
        vmin, vmax = min(valid_vals), max(valid_vals)
        neighbors = self.line_neighbors()
        side_diag_map = self.side_diag_relation()
        is_void_spec = (self.get_void_special_center_pos(vals) is not None)
        sources = []
        for key, a, b, base_weight, sigma in mapping:
            v = vals.get(key)
            if not self.is_value_in_main_range(v):
                continue
            effective_value = v
            no_circle_on_edge = False
            if key in self.side_keys:
                related_diags = side_diag_map.get(key, [])
                matched_diags = []
                if not is_void_spec:
                    for dk in related_diags:
                        dv = vals.get(dk)
                        if self.values_are_in_same_class_range(v, dv):
                            matched_diags.append(dv)
                if matched_diags:
                    no_circle_on_edge = True
                    effective_value = (v + sum(matched_diags) / len(matched_diags)) / 2.0
            t = 0.0 if abs(vmax - vmin) < 1e-12 else self.clamp((effective_value - vmin) / (vmax - vmin), 0.0, 1.0)
            relative_low = 1.0 - t
            neighbors_list = neighbors.get(key, [])
            neighbor_vals = []
            for nk in neighbors_list:
                nv = vals.get(nk)
                if self.is_value_in_main_range(nv):
                    if key in self.side_keys and self.values_are_in_same_class_range(v, nv):
                        neighbor_vals.append((v + nv) / 2.0)
                    else:
                        neighbor_vals.append(nv)
            if neighbor_vals and abs(vmax - vmin) > 1e-12:
                neighbor_avg = sum(neighbor_vals) / len(neighbor_vals)
                neighbor_low = 1.0 - self.clamp((neighbor_avg - vmin) / (vmax - vmin), 0.0, 1.0)
            else:
                neighbor_low = relative_low
            diag_boost = 1.0
            diag_side_support = {"a": 0.0, "b": 0.0}
            if key in self.diag_keys and relative_low > 0.6:
                diag_boost = 1.20
                diag_side_support = self.diagonal_side_support(key, vals)
            sources.append({
                "key": key, "a": a, "b": b, "value": v, "effective_value": effective_value,
                "base_weight": base_weight * diag_boost, "sigma": sigma,
                "relative_low": relative_low, "neighbor_low": neighbor_low,
                "no_circle_on_edge": no_circle_on_edge, "diag_side_support": diag_side_support,
            })
        return sources, vmin, vmax

    def compute_fibo_cell_value(self, x, y, sources, global_vmin, global_vmax):
        if not sources:
            return 15000.0
        phi = 1.6180339887
        dx = x + 0.03 * math.sin(phi * 5.0 * y)
        dy = y + 0.03 * math.cos(phi * 5.0 * x)
        sum_val = 0.0
        sum_w = 0.0
        for src in sources:
            dist_a = math.hypot(dx - src["a"][0], dy - src["a"][1])
            dist_b = math.hypot(dx - src["b"][0], dy - src["b"][1])
            d = dist_a + dist_b - math.hypot(src["a"][0] - src["b"][0], src["a"][1] - src["b"][1])
            effective_sigma = src["sigma"] * 1.55 if src["key"] in self.diag_keys else src["sigma"] * 1.25
            w = math.exp(-(d * d) / (2.0 * effective_sigma * effective_sigma)) * src["base_weight"]
            local_pull = 0.70 * src["relative_low"] + 0.30 * src["neighbor_low"]
            if src["key"] in self.diag_keys:
                supp = src.get("diag_side_support", {"a": 0.0, "b": 0.0})
                wa, wb = self.diagonal_half_plane_weight(src["key"], dx, dy)
                gate = self.clamp(0.15 + 0.85 * (wa * supp.get("a", 0.0) + wb * supp.get("b", 0.0)), 0.15, 1.0)
                local_pull *= gate
                w *= (0.45 + 0.55 * gate)
            sum_val += w * self.lerp(src["effective_value"], global_vmin, 0.52 * local_pull)
            sum_w += w
        return (sum_val / sum_w) if sum_w > 1e-12 else (global_vmin + global_vmax) / 2.0

    def build_center_red_focus_grid(self, nx, ny, vals, vmin, vmax):
        d1 = vals.get("p1p4")
        d2 = vals.get("p2p3")
        side_vals = [vals[k] for k in self.side_keys if self.is_value_in_main_range(vals.get(k))]
        diag_min = min(d1, d2)
        side_avg = sum(side_vals) / max(1, len(side_vals))
        outer_target = self.clamp(max(side_avg, diag_min + 0.55 * max(1.0, vmax - vmin)), vmin, vmax)
        s1, s2 = 1.0/max(d1, 1e-9), 1.0/max(d2, 1e-9)
        w1, w2 = (s1/(s1+s2), s2/(s1+s2)) if (s1+s2) > 1e-12 else (0.5, 0.5)
        proj1 = self.project_point_to_segment(0.5, 0.5, 0.0, 0.0, 1.0, 1.0)
        bx, by = w1 * proj1[0] + w2 * proj1[0], w1 * proj1[1] + w2 * proj1[1]
        smaller_diag = "p1p4" if d1 <= d2 else "p2p3"
        larger_diag = "p2p3" if d1 <= d2 else "p1p4"
        a1, b1 = self.get_segment_endpoints(smaller_diag)
        a2, b2 = self.get_segment_endpoints(larger_diag)
        p1x, p1y = self.project_point_to_segment(bx, by, a1[0], a1[1], b1[0], b1[1])
        p2x, p2y = self.project_point_to_segment(bx, by, a2[0], a2[1], b2[0], b2[1])
        t = self.clamp((vals.get(larger_diag) or 0.0) / max((vals.get(smaller_diag) or 0.0) + (vals.get(larger_diag) or 0.0), 1e-9), 0.0, 1.0)
        focus_x = self.lerp(p2x, p1x, t)
        focus_y = self.lerp(p2y, p1y, t)
        phi = 1.6180339887
        grid = []
        for j in range(ny):
            row = []
            y = j / (ny - 1) if ny > 1 else 0.5
            for i in range(nx):
                x = i / (nx - 1) if nx > 1 else 0.5
                if self.fibo_active:
                    dx = x + 0.03 * math.sin(phi * 5.0 * y)
                    dy = y + 0.03 * math.cos(phi * 5.0 * x)
                    r = math.hypot(dx - focus_x, dy - focus_y)
                    core = math.pow(phi, -(r * r) / (2.0 * 0.22 * 0.22))
                else:
                    dx = x + 0.045 * math.sin(3.6 * y + 0.8) + 0.03 * math.cos(5.2 * y)
                    r = math.hypot(dx - focus_x, dy - focus_y)
                    core = math.exp(-(r * r) / (2.0 * 0.22 * 0.22))
                edge_bias = self.clamp(((abs(dx - 0.5) / 0.5) + (abs(dy - 0.5) / 0.5)) / 2.0, 0.0, 1.0)
                row.append(self.lerp(self.lerp(outer_target, vmax, 0.20 * edge_bias), diag_min, core))
            grid.append(row)
        return self.gaussian_blur_2d(grid, 1.2)

    def diagonal_half_plane_weight(self, key, x, y):
        s = (y - x) if key == "p1p4" else (y + x - 1.0)
        band = 0.06
        if s >= band:
            return 1.0, 0.0
        if s <= -band:
            return 0.0, 1.0
        t = (s + band) / (2.0 * band + 1e-9)
        return t, 1.0 - t

    def compute_cell_value(self, x, y, sources, global_vmin, global_vmax):
        if not sources:
            return 15000.0
        dx = x + 0.045 * math.sin(3.6 * y + 0.8) + 0.02 * math.cos(5.2 * x)
        dy = y + 0.045 * math.sin(3.6 * x + 1.2) + 0.02 * math.cos(5.2 * y)
        low_corners = []
        vals = self.valid_entries_dict()
        sides = {k: vals.get(k) for k in self.side_keys}
        if not any(v is None for v in sides.values()):
            min_side_val = min(sides.values())
            all_vals = [v for v in vals.values() if v is not None]
            v_span = max(all_vals) - min(all_vals) if all_vals else 1.0
            tolerance = max(35.0, 0.25 * v_span)
            if abs(sides["p1p2"] - min_side_val) <= tolerance and abs(sides["p3p1"] - min_side_val) <= tolerance:
                low_corners.append({"vertex": (0.0, 0.0), "sides": ["p1p2", "p3p1"]})
            if abs(sides["p1p2"] - min_side_val) <= tolerance and abs(sides["p2p4"] - min_side_val) <= tolerance:
                low_corners.append({"vertex": (1.0, 0.0), "sides": ["p1p2", "p2p4"]})
            if abs(sides["p2p4"] - min_side_val) <= tolerance and abs(sides["p4p3"] - min_side_val) <= tolerance:
                low_corners.append({"vertex": (1.0, 1.0), "sides": ["p2p4", "p4p3"]})
            if abs(sides["p4p3"] - min_side_val) <= tolerance and abs(sides["p3p1"] - min_side_val) <= tolerance:
                low_corners.append({"vertex": (0.0, 1.0), "sides": ["p4p3", "p3p1"]})
        sum_val = 0.0
        sum_w = 0.0
        for src in sources:
            dist_a = math.hypot(dx - src["a"][0], dy - src["a"][1])
            dist_b = math.hypot(dx - src["b"][0], dy - src["b"][1])
            d = dist_a + dist_b - math.hypot(src["a"][0] - src["b"][0], src["a"][1] - src["b"][1])
            effective_sigma = src["sigma"] * 1.55 if src["key"] in self.diag_keys else src["sigma"] * 1.25
            w = math.exp(-(d * d) / (2.0 * effective_sigma * effective_sigma)) * src["base_weight"]
            local_pull = 0.70 * src["relative_low"] + 0.30 * src["neighbor_low"]
            for corner in low_corners:
                if src["key"] in corner["sides"]:
                    d_v = math.hypot(dx - corner["vertex"][0], dy - corner["vertex"][1])
                    if d_v < 0.40:
                        damping = 0.15 + 0.85 * ((d_v/0.40)**2)
                        w *= damping
                        local_pull *= damping
            if src["key"] in self.diag_keys:
                supp = src.get("diag_side_support", {"a": 0.0, "b": 0.0})
                wa, wb = self.diagonal_half_plane_weight(src["key"], dx, dy)
                gate = self.clamp(0.15 + 0.85 * (wa * supp.get("a", 0.0) + wb * supp.get("b", 0.0)), 0.15, 1.0)
                local_pull *= gate
                w *= (0.45 + 0.55 * gate)
            sum_val += w * self.lerp(src["effective_value"], global_vmin, 0.52 * local_pull)
            sum_w += w
        return (sum_val / sum_w) if sum_w > 1e-12 else (global_vmin + global_vmax) / 2.0

    def compute_cluster_compact_diameter(self, cluster_set, nx, ny):
        cluster_list = list(cluster_set)
        if not cluster_list:
            return 0.0
        boundary = []
        for (x, y) in cluster_list:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                xx, yy = x + dx, y + dy
                if not (0 <= xx < nx and 0 <= yy < ny) or ((xx, yy) not in cluster_set):
                    boundary.append((x, y))
                    break
        if not boundary:
            boundary = cluster_list[:]
        if len(boundary) > 260:
            boundary = boundary[::max(1, len(boundary) // 260)]
        pts = cluster_list[:]
        if len(pts) > 900:
            pts = pts[::max(1, len(pts) // 900)]
        sum_min_dist = 0.0
        for (x, y) in pts:
            best = min(math.hypot(x - bx, y - by) for (bx, by) in boundary)
            sum_min_dist += best
        diag = math.hypot(nx - 1, ny - 1)
        return (sum_min_dist / max(1, len(pts))) / diag if diag > 1e-9 else 0.0

    def get_cluster_boundary_points(self, cluster_set, nx, ny):
        boundary = []
        for (x, y) in cluster_set:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if not (0 <= x+dx < nx and 0 <= y+dy < ny) or ((x+dx, y+dy) not in cluster_set):
                    boundary.append((x, y))
                    break
        return boundary if boundary else list(cluster_set)

    def repel_circle_from_edges(self, xr, yr, radius_ratio):
        safe_margin = max(0.04, radius_ratio * 1.0)
        return self.clamp(xr, safe_margin, 1.0 - safe_margin), self.clamp(yr, safe_margin, 1.0 - safe_margin)

    def shift_towards_nearest_line(self, cx, cy, diameter_m):
        d_bottom = cy
        d_top = 1.0 - cy
        d_left = cx
        d_right = 1.0 - cx
        min_d = min(d_bottom, d_top, d_left, d_right)
        shift_amount = 0.12
        dx, dy = 0.0, 0.0
        if min_d == d_bottom:
            dy = -shift_amount
        elif min_d == d_top:
            dy = shift_amount
        elif min_d == d_left:
            dx = -shift_amount
        elif min_d == d_right:
            dx = shift_amount
        new_cx = cx + dx
        new_cy = cy + dy
        radius_ratio = (diameter_m / 2.0) / max(min(self.width_val, self.length_val), 1e-9)
        return self.repel_circle_from_edges(new_cx, new_cy, radius_ratio)

    def get_side_segment(self, key):
        segs = {"p1p2": (0.0, 0.0, 1.0, 0.0), "p2p4": (1.0, 0.0, 1.0, 1.0), "p4p3": (1.0, 1.0, 0.0, 1.0), "p3p1": (0.0, 1.0, 0.0, 0.0)}
        return segs.get(key)

    def get_segment_endpoints(self, key):
        seg = self.get_side_segment(key) or ( (0.0,0.0,1.0,1.0) if key=="p1p4" else ((1.0,0.0,0.0,1.0) if key=="p2p3" else None) )
        return ((seg[0], seg[1]), (seg[2], seg[3])) if seg else (None, None)

    def get_smallest_chord_key(self, vals):
        candidates = [(vals.get(k), k) for k in self.diag_keys if self.is_value_in_main_range(vals.get(k))]
        return min(candidates, key=lambda t: t[0])[1] if candidates else None

    def get_largest_edge_key(self, vals):
        candidates = [(vals.get(k), k) for k in self.edge_keys if vals.get(k) is not None and self.is_value_in_main_range(vals.get(k))]
        return max(candidates, key=lambda t: t[0])[1] if candidates else None

    def move_void_toward_largest_edge(self, x, y, vals, pull_percent):
        largest_key = self.get_largest_edge_key(vals)
        if not largest_key:
            return x, y
        a, b = self.get_segment_endpoints(largest_key)
        if not a or not b:
            return x, y
        px, py = self.project_point_to_segment(x, y, a[0], a[1], b[0], b[1])
        pull_t = self.clamp(pull_percent / 100.0, 0.0, 1.0)
        return self.clamp(self.lerp(x, px, pull_t), 0.0, 1.0), self.clamp(self.lerp(y, py, pull_t), 0.0, 1.0)

    def move_point_toward_chord_only(self, x, y, chord_key, chord_percent):
        if not chord_key:
            return x, y
        a, b = self.get_segment_endpoints(chord_key)
        if not a or not b:
            return x, y
        px, py = self.project_point_to_segment(x, y, a[0], a[1], b[0], b[1])
        pull_t = self.clamp(chord_percent / 100.0, 0.0, 1.0)
        return self.clamp(self.lerp(x, px, pull_t), 0.0, 1.0), self.clamp(self.lerp(y, py, pull_t), 0.0, 1.0)

    def detect_soil_contamination(self, vals):
        valid_vals = [vals.get(k) for k in self.edge_keys if self.is_value_in_main_range(vals.get(k))]
        if len(valid_vals) < len(self.edge_keys):
            return False
        if self.width_val <= 3.0 or self.length_val <= 3.0:
            return False
        diff = max(valid_vals) - min(valid_vals)
        return diff <= 100.0

    def get_two_smallest_diagonals_condition(self, vals):
        d1 = vals.get("p1p4")
        d2 = vals.get("p2p3")
        if not self.is_value_in_main_range(d1) or not self.is_value_in_main_range(d2):
            return None
        side_vals = []
        for k in self.side_keys:
            v = vals.get(k)
            if not self.is_value_in_main_range(v):
                return None
            side_vals.append(v)
        if not side_vals:
            return None
        side_min = min(side_vals)
        if d1 < side_min and d2 < side_min:
            return {
                "p1p4": d1,
                "p2p3": d2,
                "smaller_diag": "p1p4" if d1 <= d2 else "p2p3",
                "larger_diag": "p2p3" if d1 <= d2 else "p1p4"
            }
        return None

    def get_small_side_candidate_when_diags_dominate(self, vals):
        d1, d2 = vals.get("p1p4"), vals.get("p2p3")
        if not self.is_value_in_main_range(d1) or not self.is_value_in_main_range(d2):
            return None
        diag_min, diag_max = min(d1, d2), max(d1, d2)
        valid_sides = sorted([(vals.get(k), k) for k in self.side_keys if self.is_value_in_main_range(vals.get(k))], key=lambda x: x[0])
        if not valid_sides:
            return None
        all_vals = [v for v in vals.values() if self.is_value_in_main_range(v)]
        span = max(all_vals) - min(all_vals) if all_vals else 0
        threshold = diag_max + 0.45 * span
        for side_v, side_k in valid_sides:
            if diag_min < side_v <= threshold:
                return {"side_key": side_k, "side_value": side_v, "diag_min": diag_min, "diag_max": diag_max}
        return {"side_key": valid_sides[0][1], "side_value": valid_sides[0][0], "diag_min": diag_min, "diag_max": diag_max}

    def get_side_direction_vector(self, side_key):
        dirs = {
            "p1p2": ((0.0, -1.0), (0.5, 0.12)), 
            "p2p4": ((1.0, 0.0), (0.88, 0.5)), 
            "p4p3": ((0.0, 1.0), (0.5, 0.88)), 
            "p3p1": ((-1.0, 0.0), (0.12, 0.5))
        }
        return dirs.get(side_key, ((0.0, 0.0), (0.5, 0.5)))

    def is_red_present_at_ratio(self, xr, yr):
        if not self.heatmap_data:
            return False
        grid, nx, ny = self.heatmap_data["grid"], self.heatmap_data["nx"], self.heatmap_data["ny"]
        vmin, vmax = self.heatmap_data["min"], self.heatmap_data["max"]
        ix = int(round(self.clamp(xr, 0.0, 1.0) * (nx - 1)))
        iy = int(round(self.clamp(yr, 0.0, 1.0) * (ny - 1)))
        return False if (vmax - vmin) <= 1e-12 else (self.clamp((grid[iy][ix] - vmin)/(vmax - vmin), 0.0, 1.0) <= 0.18)

    def is_red_present_in_center_and_side(self, side_key):
        return self.is_red_present_at_ratio(0.5, 0.5) and self.is_red_present_at_ratio(*self.get_side_direction_vector(side_key)[1])

    def build_balanced_side_circle_position(self, side_key, vals):
        side_val = vals.get(side_key)
        if not self.is_value_in_main_range(side_val):
            return 0.5, 0.5
        diags = [vals.get(k) for k in self.diag_keys if self.is_value_in_main_range(vals.get(k))]
        if not diags:
            return self.get_side_direction_vector(side_key)[1]
        diag_min = min(diags)
        all_vals = [v for v in vals.values() if self.is_value_in_main_range(v)]
        span = max(all_vals) - min(all_vals) if all_vals else 1e-9
        closeness = 1.0 - self.clamp((side_val - diag_min)/(0.35 * span), 0.0, 1.0)
        _, anchor = self.get_side_direction_vector(side_key)
        sc_key = self.get_smallest_chord_key(vals)
        if not sc_key:
            return anchor
        a, b = self.get_segment_endpoints(sc_key)
        if not a or not b:
            return anchor
        c_proj_x, c_proj_y = self.project_point_to_segment(anchor[0], anchor[1], a[0], a[1], b[0], b[1])
        mid_x = self.lerp(anchor[0], c_proj_x, (self.chord_pull/100.0) * (0.25 + 0.75*closeness))
        mid_y = self.lerp(anchor[1], c_proj_y, (self.chord_pull/100.0) * (0.25 + 0.75*closeness))
        side_shift = 0.0
        left_k, right_k = ("p3p1", "p2p4") if side_key in ["p1p2", "p4p3"] else ("p1p2", "p4p3")
        if self.is_value_in_main_range(vals.get(left_k)) and self.is_value_in_main_range(vals.get(right_k)):
            side_shift = 0.10 * self.expansion_level * self.clamp((vals[left_k] - vals[right_k]) / (vals[left_k] + vals[right_k] + 1e-4), -1.0, 1.0)
        if side_key in ["p1p2", "p4p3"]:
            mid_x += side_shift
        else:
            mid_y += side_shift
        return self.clamp(mid_x, 0.05, 0.95), self.clamp(mid_y, 0.05, 0.95)

    def build_warning_arrow_for_edge(self, side_key, color=(17, 17, 17, 255)):
        direction, anchor = self.get_side_direction_vector(side_key)
        sx = anchor[0] * 0.82 + 0.09
        sy = anchor[1] * 0.82 + 0.09
        return {
            "start_x_ratio": self.clamp(sx, 0.06, 0.94), "start_y_ratio": self.clamp(sy, 0.06, 0.94),
            "end_x_ratio": self.clamp(sx + direction[0]*0.10, 0.02, 0.98), "end_y_ratio": self.clamp(sx + direction[1]*0.10, 0.02, 0.98),
            "side_key": side_key, "color": color
        }

    def detect_low_res_zones_multi(self, grid, nx, ny):
        flat = [vv for row in grid for vv in row]
        if not flat:
            return []
        gmin = min(flat)
        vmax = max(flat)
        span = vmax - gmin
        if span <= 1e-12:
            return []
        threshold = gmin + 0.08 * span
        mask = [[grid[j][i] <= threshold for i in range(nx)] for j in range(ny)]
        visited = [[False for _ in range(nx)] for _ in range(ny)]
        clusters = []
        for j in range(ny):
            for i in range(nx):
                if mask[j][i] and not visited[j][i]:
                    cluster = []
                    q = [(i, j)]
                    visited[j][i] = True
                    qi = 0
                    while qi < len(q):
                        cx, cy = q[qi]
                        qi += 1
                        cluster.append((cx, cy))
                        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            xx, yy = cx + dx, cy + dy
                            if 0 <= xx < nx and 0 <= yy < ny and mask[yy][xx] and not visited[yy][xx]:
                                visited[yy][xx] = True
                                q.append((xx, yy))
                    if len(cluster) > 15:
                        clusters.append(cluster)
        clusters.sort(key=len, reverse=True)
        clusters = clusters[:8]
        min_d = self.min_diameter
        max_d = self.max_diameter
        if max_d < min_d:
            max_d = min_d
        results = []
        for cluster in clusters:
            cluster_set = set(cluster)
            avg_x = sum(p[0] for p in cluster) / len(cluster)
            avg_y = sum(p[1] for p in cluster) / len(cluster)
            peak_p = min(cluster, key=lambda p: grid[p[1]][p[0]])
            min_cluster_val = grid[peak_p[1]][peak_p[0]]
            xr = avg_x / (nx - 1) if (nx > 1) else 0.5
            yr = avg_y / (ny - 1) if (ny > 1) else 0.5
            min_c_x = min(p[0] for p in cluster) / (nx - 1) if nx > 1 else 0.0
            max_c_x = max(p[0] for p in cluster) / (nx - 1) if nx > 1 else 1.0
            min_c_y = min(p[1] for p in cluster) / (ny - 1) if ny > 1 else 0.0
            max_c_y = max(p[1] for p in cluster) / (ny - 1) if ny > 1 else 1.0
            zw = (max_c_x - min_c_x) * self.width_val
            zh = (max_c_y - min_c_y) * self.length_val
            border_bbox = (zw + zh) / 2.0
            compact_ratio = self.compute_cluster_compact_diameter(cluster_set, nx, ny)
            avg_dim_m = (self.width_val + self.length_val) / 2.0
            border_compact = (compact_ratio * avg_dim_m) * 2.2
            diameter_m = self.clamp(0.55 * border_bbox + 0.45 * border_compact, min_d, max_d)
            radius_ratio = (diameter_m / 2.0) / max(min(self.width_val, self.length_val), 1e-9)
            xr, yr = self.repel_circle_from_edges(xr, yr, radius_ratio)
            local_val = min_cluster_val
            label, fill_color, text_color = self.classify_target(local_val)
            results.append({
                "center_x_ratio": xr, "center_y_ratio": yr, "diameter_m": diameter_m, "target_value": local_val,
                "label": label, "fill_color": fill_color, "text_color": text_color, "source_type": "cluster",
                "cluster_bounds": {"min_c_x": min_c_x, "max_c_x": max_c_x, "min_c_y": min_c_y, "max_c_y": max_c_y}
            })
        results.sort(key=lambda c: c["target_value"])
        return results

    def detect_high_res_zones_multi(self, grid, nx, ny):
        flat = [vv for row in grid for vv in row]
        if not flat:
            return []
        gmin, vmax = min(flat), max(flat)
        span = vmax - gmin
        if span <= 1e-12:
            return []
        threshold = vmax - 0.18 * span
        mask = [[grid[j][i] >= threshold for i in range(nx)] for j in range(ny)]
        visited = [[False for _ in range(nx)] for _ in range(ny)]
        clusters = []
        for i in range(ny):
            for j in range(nx):
                if mask[i][j] and not visited[i][j]:
                    cluster, q = [], [(j, i)]
                    visited[i][j] = True
                    qi = 0
                    while qi < len(q):
                        cx, cy = q[qi]
                        qi += 1
                        cluster.append((cx, cy))
                        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            if 0 <= cx+dx < nx and 0 <= cy+dy < ny and mask[cy+dy][cx+dx] and not visited[cy+dy][cx+dx]:
                                visited[cy+dy][cx+dx] = True
                                q.append((cx+dx, cy+dy))
                    if len(cluster) > 15:
                        clusters.append(cluster)
        clusters.sort(key=len, reverse=True)
        clusters = clusters[:8]
        min_d = self.min_diameter
        max_d = self.max_diameter
        if max_d < min_d:
            max_d = min_d
        results = []
        for cluster in clusters:
            cluster_set = set(cluster)
            avg_x = sum(p[0] for p in cluster) / len(cluster)
            text_avg_y = sum(p[1] for p in cluster) / len(cluster)
            avg_y = text_avg_y
            peak_p = max(cluster, key=lambda p: grid[p[1]][p[0]])
            max_cluster_val = grid[peak_p[1]][peak_p[0]]
            xr = avg_x / (nx - 1) if (nx > 1) else 0.5
            yr = avg_y / (ny - 1) if (ny > 1) else 0.5
            min_cx = min(p[0] for p in cluster)/(nx-1)
            max_cx = max(p[0] for p in cluster)/(nx-1)
            min_cy = min(p[1] for p in cluster)/(ny-1)
            max_cy = max(p[1] for p in cluster)/(ny-1)
            diameter_m = self.clamp(0.55*((max_cx-min_cx)*self.width_val + (max_cy-min_cy)*self.length_val) + 0.45*(self.compute_cluster_compact_diameter(cluster_set, nx, ny)*(self.width_val+self.length_val))*2.2, min_d, max_d)
            xr, yr = self.repel_circle_from_edges(xr, yr, (diameter_m/2.0)/max(min(self.width_val, self.length_val), 1e-9))
            label, fill_color, text_color = self.classify_target(max_cluster_val)
            results.append({
                "center_x_ratio": xr, "center_y_ratio": yr, "diameter_m": diameter_m, "target_value": max_cluster_val,
                "label": label, "fill_color": fill_color, "text_color": text_color, "source_type": "cluster",
                "cluster_bounds": {"min_cx": min_cx, "max_cx": max_cx, "min_cy": min_cy, "max_cy": max_cy}
            })
        results.sort(key=lambda c: c["target_value"], reverse=True)
        return results

    def get_min_value_in_circle(self, cx_ratio, cy_ratio, radius_ratio):
        if not self.heatmap_data:
            return 0.0
        grid = self.heatmap_data["grid"]
        grid_ny = len(grid)
        grid_nx = len(grid[0]) if grid_ny > 0 else 0
        min_val = float('inf')
        for j in range(grid_ny):
            ry = j / (grid_ny - 1) if grid_ny > 1 else 0.5
            for i in range(grid_nx):
                rx = i / (grid_nx - 1) if grid_nx > 1 else 0.5
                if math.hypot(rx - cx_ratio, ry - cy_ratio) <= radius_ratio:
                    if grid[j][i] < min_val:
                        min_val = grid[j][i]
        return min_val if min_val != float('inf') else 0.0

    def get_max_value_in_circle(self, cx_ratio, cy_ratio, radius_ratio):
        if not self.heatmap_data:
            return 0.0
        grid = self.heatmap_data["grid"]
        grid_ny = len(grid)
        grid_nx = len(grid[0]) if grid_ny > 0 else 0
        max_val = float('-inf')
        for j in range(grid_ny):
            ry = j / (grid_ny - 1) if grid_ny > 1 else 0.5
            for i in range(grid_nx):
                rx = i / (grid_nx - 1) if grid_nx > 1 else 0.5
                if math.hypot(rx - cx_ratio, ry - cy_ratio) <= radius_ratio:
                    if grid[j][i] > max_val:
                        max_val = grid[j][i]
        return max_val if max_val != float('-inf') else 0.0

    def compute_triangle_weights(self, vals, side_key, chord1_key, chord2_key, is_void):
        v_s = self.safe_float(vals.get(side_key))
        v_c1 = self.safe_float(vals.get(chord1_key))
        v_c2 = self.safe_float(vals.get(chord2_key))
        v_s = v_s if (v_s is not None and 0 <= v_s <= 100000) else 600.0
        v_c1 = v_c1 if (v_c1 is not None and 0 <= v_c1 <= 100000) else 600.0
        v_c2 = v_c2 if (v_c2 is not None and 0 <= v_c2 <= 100000) else 600.0
        v_s = max(1.0, v_s)
        v_c1 = max(1.0, v_c1)
        v_c2 = max(1.0, v_c2)
        if is_void:
            u_s = v_s
            u_c1 = v_c1
            u_c2 = v_c2
        else:
            u_s = 1.0 / v_s
            u_c1 = 1.0 / v_c1
            u_c2 = 1.0 / v_c2
        total = u_s + u_c1 + u_c2
        if total <= 1e-9:
            return 0.333, 0.333, 0.333
        return u_s / total, u_c1 / total, u_c2 / total

    def refine_target_positions(self, dt):
        if not self.detected_circles:
            return
        vals = self.valid_entries_dict()
        for circ in self.detected_circles:
            if circ.get("source_type") == "special_void_triangle":
                continue
            cx = circ["center_x_ratio"]
            cy = circ["center_y_ratio"]
            diameter_m = circ["diameter_m"]
            d_p1p2 = cy
            d_p2p4 = 1.0 - cx
            d_p4p3 = 1.0 - cy
            d_p3p1 = cx
            sides_dists = [
                (d_p1p2, "p1p2", (0.0, 0.0, 1.0, 0.0)),
                (d_p2p4, "p2p4", (1.0, 0.0, 1.0, 1.0)),
                (d_p4p3, "p4p3", (1.0, 1.0, 0.0, 1.0)),
                (d_p3p1, "p3p1", (0.0, 1.0, 0.0, 0.0))
            ]
            sides_dists.sort(key=lambda x: x[0])
            closest_side_dist, side_key, side_coords = sides_dists[0]
            is_void = circ.get("target_value", 0.0) >= 3000 or circ.get("label") in ["Void", "Small Void", "Medium Void", "Big Void"]
            w_s, w_c1, w_c2 = self.compute_triangle_weights(vals, side_key, "p1p4", "p2p3", is_void)
            proj_x_s, proj_y_s = self.project_point_to_segment(cx, cy, *side_coords)
            proj_x_c1, proj_y_c1 = self.project_point_to_segment(cx, cy, 0.0, 0.0, 1.0, 1.0)
            proj_x_c2, proj_y_c2 = self.project_point_to_segment(cx, cy, 1.0, 0.0, 0.0, 1.0)
            weighted_x = w_s * proj_x_s + w_c1 * proj_x_c1 + w_c2 * proj_x_c2
            weighted_y = w_s * proj_y_s + w_c1 * proj_y_c1 + w_c2 * proj_y_c2
            cx = self.lerp(cx, weighted_x, 0.35)
            cy = self.lerp(cy, weighted_y, 0.35)
            radius_ratio = (diameter_m / 2.0) / max(min(self.width_val, self.length_val), 1e-9)
            circ["center_x_ratio"], circ["center_y_ratio"] = self.repel_circle_from_edges(cx, cy, radius_ratio)
        self.update_target_boxes()
        self.invalidate_render_cache()
        if hasattr(self, 'monitor') and self.monitor:
            self.monitor.redraw()

    def calculate_geophysics_heatmap(self):
        self.invalidate_render_cache()
        self.warning_arrows = []
        self.center_red_focus_mode = False
        vals = self.valid_entries_dict()
        if self.get_cut_segments():
            self.heatmap_data = None
            self.detected_circles = []
            self.update_target_boxes()
            return
        self.soil_contaminated = self.detect_soil_contamination(vals)
        result = self.build_line_sources(vals)
        if not result:
            self.heatmap_data = None
            self.min_point = None
            self.max_point = None
            self.detected_circles = []
            self.update_target_boxes()
            return
        sources, vmin, vmax = result
        nx, ny = 140, 140
        if self.should_use_center_red_focus(vals):
            self.center_red_focus_mode = True
            value_grid = self.build_center_red_focus_grid(nx, ny, vals, vmin, vmax)
            if self.signal_correction_level != 0:
                factor = 0.35 if self.signal_correction_level >= 0 else 0.15
                value_grid = self.gaussian_blur_2d(value_grid, max(0.10, 1.2 + factor * self.signal_correction_level))
        else:
            value_grid = []
            for j in range(ny):
                row = []
                y = j / (ny - 1) if ny > 1 else 0.5
                for i in range(nx):
                    x = i / (nx - 1) if nx > 1 else 0.5
                    row.append(self.compute_cell_value(x, y, sources, vmin, vmax))
                value_grid.append(row)
            factor = 0.35 if self.signal_correction_level >= 0 else 0.15
            value_grid = self.gaussian_blur_2d(value_grid, max(0.10, 0.90 + factor * self.signal_correction_level))
        flat = [vv for row in value_grid for vv in row]
        gmin, vmax = min(flat), max(flat)
        min_i, min_j = 0, 0
        max_i, max_j = 0, 0
        min_val, max_val = value_grid[0][0], value_grid[0][0]
        for j in range(ny):
            for i in range(nx):
                v = value_grid[j][i]
                if v < min_val:
                    min_val, min_i, min_j = v, i, j
                if v > max_val:
                    max_val, max_i, max_j = v, i, j
        min_xr = self.clamp(min_i / (nx - 1) if nx > 1 else 0.5, 0.10, 0.90)
        min_yr = self.clamp(min_j / (ny - 1) if ny > 1 else 0.5, 0.10, 0.90)
        max_xr = self.clamp(max_i / (nx - 1) if nx > 1 else 0.5, 0.10, 0.90)
        max_yr = self.clamp(max_j / (ny - 1) if ny > 1 else 0.5, 0.10, 0.90)
        self.min_point = {"x_ratio": min_xr, "y_ratio": min_yr, "value": min_val}
        self.max_point = {"x_ratio": max_xr, "y_ratio": max_yr, "value": max_val}
        self.heatmap_data = {"grid": value_grid, "nx": nx, "ny": ny, "min": gmin, "max": vmax, "sources": sources}
        self.width_m = self.width_val
        self.height_m = self.length_val
        if self.soil_contaminated:
            self.detected_circles = []
            self.update_target_boxes()
            return
        self.detected_circles = []
        if self.should_allow_circle_rendering(vals):
            low_vals_entered = [v for v in vals.values() if v is not None and ((0 <= v <= 500) or (700 <= v <= 1100))]
            void_vals_entered = [v for v in vals.values() if v is not None and (3000 <= v <= 100000)]
            unknown_vals_entered = [v for v in vals.values() if v is not None and ((500 < v < 700) or (1100 < v < 3000))]
            min_d = self.min_diameter
            max_d = self.max_diameter
            if max_d < min_d:
                max_d = min_d
            d = self.clamp(min(self.width_val, self.length_val) * 0.20, min_d, max_d)
            d1 = vals.get("p1p4")
            d2 = vals.get("p2p3")
            sides = [vals.get(k) for k in self.side_keys if self.is_value_in_main_range(vals.get(k))]
            diagonals_are_largest = False
            if (d1 is not None and self.is_value_in_main_range(d1) and d2 is not None and self.is_value_in_main_range(d2) and len(sides) == 4):
                if d1 > max(sides) and d2 > max(sides):
                    diagonals_are_largest = True
            if low_vals_entered:
                candidates_low = self.detect_low_res_zones_multi(value_grid, nx, ny)
                low_spots = [c for c in candidates_low if (0 <= c["target_value"] <= 600) or (650 <= c["target_value"] <= 1300)]
                low_spots = low_spots[:2]
                if not low_spots:
                    entered_low_val = min(low_vals_entered)
                    cx, cy = min_xr, min_yr
                    cx, cy = self.shift_towards_nearest_line(cx, cy, d)
                    label, fill_color, text_color = self.classify_target(entered_low_val)
                    self.detected_circles.append({
                        "center_x_ratio": cx, "center_y_ratio": cy, "diameter_m": d, "target_value": entered_low_val,
                        "label": label, "fill_color": fill_color, "text_color": text_color, "source_type": "fallback"
                    })
                else:
                    for spot in low_spots:
                        cx, cy = spot["center_x_ratio"], spot["center_y_ratio"]
                        cx, cy = self.shift_towards_nearest_line(cx, cy, spot["diameter_m"])
                        spot_d = spot["diameter_m"]
                        label, fill_color, text_color = self.classify_target(spot["target_value"])
                        self.detected_circles.append({
                            "center_x_ratio": cx, "center_y_ratio": cy, "diameter_m": spot_d, "target_value": spot["target_value"],
                            "label": label, "fill_color": fill_color, "text_color": text_color, "source_type": "cluster"
                        })
            if void_vals_entered:
                if diagonals_are_largest:
                    if d1 >= d2:
                        s_p1 = (vals.get("p1p2") or 0.0) + (vals.get("p3p1") or 0.0)
                        s_p4 = (vals.get("p2p4") or 0.0) + (vals.get("p4p3") or 0.0)
                        if s_p4 >= s_p1:
                            if (vals.get("p4p3") or 0.0) >= (vals.get("p2p4") or 0.0):
                                inside_triangle = lambda x, y: (y >= x and y >= 1.0 - x)
                            else:
                                inside_triangle = lambda x, y: (y < x and y >= 1.0 - x)
                        else:
                            if (vals.get("p1p2") or 0.0) >= (vals.get("p3p1") or 0.0):
                                inside_triangle = lambda x, y: (y < x and y < 1.0 - x)
                            else:
                                inside_triangle = lambda x, y: (y >= x and y < 1.0 - x)
                    else:
                        s_p2 = (vals.get("p1p2") or 0.0) + (vals.get("p2p4") or 0.0)
                        s_p3 = (vals.get("p3p1") or 0.0) + (vals.get("p4p3") or 0.0)
                        if s_p3 >= s_p2:
                            if (vals.get("p4p3") or 0.0) >= (vals.get("p3p1") or 0.0):
                                inside_triangle = lambda x, y: (y >= x and y >= 1.0 - x)
                            else:
                                inside_triangle = lambda x, y: (y >= x and y < 1.0 - x)
                        else:
                            if (vals.get("p1p2") or 0.0) >= (vals.get("p2p4") or 0.0):
                                inside_triangle = lambda x, y: (y < x and y < 1.0 - x)
                            else:
                                inside_triangle = lambda x, y: (y < x and y >= 1.0 - x)
                    max_val_tri = float('-inf')
                    best_i, best_j = 0, 0
                    for j in range(ny):
                        y = j / (ny - 1) if ny > 1 else 0.5
                        for i in range(nx):
                            x = i / (nx - 1) if nx > 1 else 0.5
                            if inside_triangle(x, y):
                                grid_val = value_grid[j][i]
                                if grid_val > max_val_tri:
                                    max_val_tri = grid_val
                                    best_i, best_j = i, j
                    cx = best_i / (nx - 1) if nx > 1 else 0.5
                    cy = best_j / (ny - 1) if ny > 1 else 0.5
                    d_size = self.clamp(min(self.width_val, self.length_val) * 0.20, min_d, max_d)
                    radius_ratio = (d_size / 2.0) / max(min(self.width_val, self.length_val), 1e-9)
                    cx, cy = self.repel_circle_from_edges(cx, cy, radius_ratio)
                    label, fill_color, text_color = self.classify_target(max_val_tri)
                    self.detected_circles.append({
                        "center_x_ratio": cx, "center_y_ratio": cy, "diameter_m": d_size, "target_value": max_val_tri,
                        "label": label, "fill_color": fill_color, "text_color": text_color, "source_type": "special_void_triangle"
                    })
                else:
                    candidates_high = self.detect_high_res_zones_multi(value_grid, nx, ny)
                    void_spots = [c for c in candidates_high if 3000 <= c["target_value"] <= 100000]
                    if void_spots:
                        spot = void_spots[0]
                        cx, cy = self.move_void_toward_largest_edge(spot["center_x_ratio"], spot["center_y_ratio"], vals, self.void_pull)
                        cx, cy = self.shift_towards_nearest_line(cx, cy, spot["diameter_m"])
                        self.detected_circles.append({
                            "center_x_ratio": cx, "center_y_ratio": cy, "diameter_m": spot["diameter_m"], "target_value": spot["target_value"],
                            "label": spot["label"], "fill_color": spot["fill_color"], "text_color": spot["text_color"], "source_type": "cluster"
                        })
                    else:
                        entered_void_val = max(void_vals_entered)
                        cx, cy = self.move_void_toward_largest_edge(max_xr, max_yr, vals, self.void_pull)
                        cx, cy = self.shift_towards_nearest_line(cx, cy, d)
                        label, fill_color, text_color = self.classify_target(entered_void_val)
                        self.detected_circles.append({
                            "center_x_ratio": cx, "center_y_ratio": cy, "diameter_m": d, "target_value": entered_void_val,
                            "label": label, "fill_color": fill_color, "text_color": text_color, "source_type": "fallback"
                        })
            if unknown_vals_entered and not low_vals_entered and not void_vals_entered:
                entered_unk_val = unknown_vals_entered[0]
                cx, cy = min_xr, min_yr
                cx, cy = self.shift_towards_nearest_line(cx, cy, d)
                label, fill_color, text_color = self.classify_target(entered_unk_val)
                self.detected_circles.append({
                    "center_x_ratio": cx, "center_y_ratio": cy, "diameter_m": d, "target_value": entered_unk_val,
                    "label": label, "fill_color": fill_color, "text_color": text_color, "source_type": "fallback"
                })
        if self.heatmap_data and self.detected_circles:
            for circ in self.detected_circles:
                if circ.get("source_type") == "special_void_triangle":
                    continue
                orig_val = circ["target_value"]
                orig_label = circ["label"]
                closest_val = self.get_closest_matching_input_value(circ["center_x_ratio"], circ["center_y_ratio"], vals, orig_label, orig_val)
                if closest_val is not None:
                    target_val = closest_val
                else:
                    r_ratio = (circ["diameter_m"] / 2.0) / max(self.width_val, 1e-9)
                    if orig_val >= 3000:
                        target_val = self.get_max_value_in_circle(circ["center_x_ratio"], circ["center_y_ratio"], r_ratio)
                    else:
                        target_val = self.get_min_value_in_circle(circ["center_x_ratio"], circ["center_y_ratio"], r_ratio)
                circ["target_value"] = target_val
                label, fill_color, text_color = self.classify_target(target_val)
                circ["label"] = label
                circ["fill_color"] = fill_color
                circ["text_color"] = text_color
        def in_neutral_range(v):
            if v is None:
                return False
            return (501 <= v <= 699) or (1101 <= v <= 2999)
        def in_metal_or_water_range(v):
            if v is None:
                return False
            return (0 <= v <= 500) or (700 <= v <= 1100)
        all_6_valid = True
        for k in self.edge_keys:
            if vals.get(k) is None:
                all_6_valid = False
                break
        if all_6_valid:
            diag_neutral = all(in_neutral_range(vals.get(dk)) for dk in self.diag_keys)
            num_neutral_sides = sum(1 for sk in self.side_keys if in_neutral_range(vals.get(sk)))
            metal_water_sides = [sk for sk in self.side_keys if in_metal_or_water_range(vals.get(sk))]
            if diag_neutral and num_neutral_sides == 3 and len(metal_water_sides) == 1:
                target_edge = metal_water_sides[0]
                target_val = vals.get(target_edge)
                _, fill_hex, _ = self.classify_target(target_val)
                fill_lower = fill_hex.lower()
                if fill_lower == "#0000ff":
                    arrow_color = (255, 255, 255, 255)
                elif fill_lower == "#ffd700":
                    arrow_color = (0, 0, 0, 255)
                elif fill_lower == "#ff0000":
                    arrow_color = (255, 255, 255, 255)
                elif fill_lower == "#8b4513":
                    arrow_color = (255, 255, 255, 255)
                elif fill_lower == "#ffa500":
                    arrow_color = (0, 0, 0, 255)
                elif fill_lower in ["#808080", "#d3d3d3"]:
                    arrow_color = (0, 0, 0, 255)
                else:
                    arrow_color = (255, 255, 255, 255)
                self.warning_arrows.append(self.build_warning_arrow_for_edge(target_edge, arrow_color))
        if self.width_val <= 3.0 and self.length_val <= 3.0:
            if self.detected_circles:
                metals_water = [c for c in self.detected_circles if c.get("target_value", 0) < 3000]
                voids = [c for c in self.detected_circles if c.get("target_value", 0) >= 3000]
                best_metal = None
                best_void = None
                if metals_water:
                    best_metal = min(metals_water, key=lambda x: x.get("target_value", 999999))
                if voids:
                    best_void = max(voids, key=lambda x: x.get("target_value", -999999))
                if best_metal and best_void:
                    ref = getattr(self, 'ref_soil_val', 600.0)
                    contrast_metal = abs(best_metal.get("target_value", 0) - ref) / max(1.0, ref)
                    contrast_void = abs(best_void.get("target_value", 0) - ref) / max(1.0, ref)
                    if contrast_metal >= contrast_void:
                        self.detected_circles = [best_metal]
                    else:
                        self.detected_circles = [best_void]
                elif best_metal:
                    self.detected_circles = [best_metal]
                elif best_void:
                    self.detected_circles = [best_void]
        self.detected_circles = self.filter_circles_for_display(self.detected_circles, vals)
        self.refine_target_positions(0)
        Clock.schedule_once(self.refine_target_positions, 0.0002)

    def compute_gpr_fibonacci_value(self, rx, ry, vmin, vmax, min_xr, min_yr):
        phi = 1.61803398875
        centers = []
        if self.detected_circles:
            for circ in self.detected_circles:
                centers.append((circ["center_x_ratio"], circ["center_y_ratio"]))
        if not centers:
            centers.append((min_xr, min_yr))
        final_t_list = []
        for cx, cy in centers:
            dx = (rx - cx) * self.width_val
            dy = (ry - cy) * self.length_val
            r = math.hypot(dx, dy)
            fib_radii = [0.13, 0.21, 0.34, 0.55, 0.89, 1.44, 2.33, 3.77]
            wave_sum = 0.0
            weight_sum = 0.0
            for idx, fib_r in enumerate(fib_radii):
                w_i = 1.0 / (phi ** idx)
                diff = r - fib_r
                wave_width = 0.05 * fib_r + 0.02
                wave_val = math.exp(-(diff * diff) / (2.0 * (wave_width) ** 2))
                wave_sum += w_i * wave_val
                weight_sum += w_i
            normalized_wave = (wave_sum / weight_sum) if weight_sum > 0 else 0.0
            theta = math.atan2(dy, dx)
            try:
                wave_spiral_phase = math.cos(3.0 * theta - 4.0 * math.log(r + 0.05))
            except Exception:
                wave_spiral_phase = 0.0
            base_t = 1.0 - math.exp(-r / 0.9)
            final_t = self.clamp(base_t - 0.35 * normalized_wave * (1.0 + 0.25 * wave_spiral_phase), 0.0, 1.0)
            final_t_list.append(final_t)
        min_final_t = min(final_t_list)
        bg_noise = 0.06 * math.sin(rx * 14.5 + ry * 10.3) + 0.04 * math.cos(rx * 27.2 - ry * 23.4) + 0.02 * math.sin(rx * 58.1 + ry * 44.9)
        fibo_t = self.clamp(min_final_t + bg_noise, 0.0, 1.0)
        return vmin + fibo_t * (vmax - vmin)

    def start_gpr_zigzag_scan(self):
        if self.check_cuts_and_warn():
            self.scanning = False
            self.fibo_active = False
            self.gpr_active = False
            return
        self.loaded_scan_name = ""
        self.scanning = True
        self.width_val = self.ui_width_val
        self.length_val = self.ui_length_val
        self.ref_soil_val = self.ui_ref_soil_val
        self.entry_values = self.ui_entry_values.copy()
        self.calculate_geophysics_heatmap()
        self.scan_cols = 45
        self.scan_rows = 45
        self.scan_grid = [[None for _ in range(self.scan_cols)] for _ in range(self.scan_rows)]
        self.scan_current_col = 0
        self.scan_current_row = 0
        self.scan_direction_up = True
        self.sampled_points = []
        self.final_min_points = []
        self.transition_step = 0
        self.gpr_fibo_skeleton_visible = False
        Clock.schedule_once(self.run_scan_step, 0.015)

    def run_scan_step(self, dt):
        if not self.scanning:
            return
        if self.check_cuts_and_warn():
            self.scanning = False
            self.fibo_active = False
            self.gpr_active = False
            self.monitor.redraw()
            return
        steps_per_tick = 15
        for _ in range(steps_per_tick):
            if not self.scanning:
                break
            rx = self.scan_current_col / (self.scan_cols - 1) if self.scan_cols > 1 else 0.5
            ry = self.scan_current_row / (self.scan_rows - 1) if self.scan_rows > 1 else 0.5
            if self.heatmap_data is not None:
                vmin = self.heatmap_data["min"]
                vmax = self.heatmap_data["max"]
                min_xr = self.min_point["x_ratio"] if self.min_point else 0.5
                min_yr = self.min_point["y_ratio"] if self.min_point else 0.5
                if self.fibo_active:
                    val = self.compute_gpr_fibonacci_value(rx, ry, vmin, vmax, min_xr, min_yr)
                else:
                    grid = self.heatmap_data["grid"]
                    g_ny = len(grid)
                    g_nx = len(grid[0]) if g_ny > 0 else 1
                    ix = int(self.clamp(rx * (g_nx - 1), 0, g_nx - 1))
                    iy = int(self.clamp(ry * (g_ny - 1), 0, g_ny - 1))
                    val = grid[iy][ix]
                self.scan_grid[self.scan_current_col][self.scan_current_row] = val
                self.sampled_points.append((rx, ry, val))
            if self.scan_direction_up:
                self.scan_current_col += 1
                if self.scan_current_col >= self.scan_cols:
                    self.scan_current_col = self.scan_cols - 1
                    self.scan_current_row += 1
                    self.scan_direction_up = False
            else:
                self.scan_current_col -= 1
                if self.scan_current_col < 0:
                    self.scan_current_col = 0
                    self.scan_current_row += 1
                    self.scan_direction_up = True
            if self.scan_current_row >= self.scan_rows:
                self.finish_scan()
                break
        self.invalidate_render_cache()
        self.monitor.redraw()
        if self.scanning:
            Clock.schedule_once(self.run_scan_step, 0.015)

    def finish_scan(self):
        self.scanning = False
        self.transition_step = 1
        self.invalidate_render_cache()
        self.monitor.redraw()
        Clock.schedule_once(self.auto_transition_step_2, 0.04)

    def auto_transition_step_2(self, dt):
        if not self.scanning:
            self.transition_step = 2
            self.invalidate_render_cache()
            self.monitor.redraw()
            if self.fibo_active:
                Clock.schedule_once(self.enable_gpr_fibo_skeleton, 1.0)
            else:
                Clock.schedule_once(self.auto_transition_step_3, 0.04)

    def auto_transition_step_3(self, dt):
        if not self.scanning:
            self.transition_step = 3
            self.invalidate_render_cache()
            self.monitor.redraw()
            Clock.schedule_once(self.enable_gpr_fibo_skeleton, 1.0)

    def enable_gpr_fibo_skeleton(self, dt):
        if not self.scanning:
            self.gpr_fibo_skeleton_visible = True
            self.invalidate_render_cache()
            self.monitor.redraw()

    def safe_draw_ellipse(self, draw, box, fill=None, outline=None, width=1):
        try:
            draw.ellipse(box, fill=fill, outline=outline, width=width)
        except TypeError:
            draw.ellipse(box, fill=fill, outline=outline)

    def safe_draw_rectangle(self, draw, box, fill=None, outline=None, width=1):
        try:
            draw.rectangle(box, fill=fill, outline=outline, width=width)
        except TypeError:
            draw.rectangle(box, fill=fill, outline=outline)

    def safe_draw_rounded_rectangle(self, draw, box, radius=5, fill=None, outline=None, width=1):
        try:
            draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
        except AttributeError:
            try:
                draw.rectangle(box, fill=fill, outline=outline, width=width)
            except TypeError:
                draw.rectangle(box, fill=fill, outline=outline)

    def get_render_texture(self):
        if hasattr(self, '_cached_render_texture') and self._cached_render_texture is not None:
            return self._cached_render_texture
        img = self.generate_visualization_image()
        if img is None:
            return None
        try:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
            data = img.tobytes("raw", "RGBA")
            tex = Texture.create(size=img.size, colorfmt="rgba")
            tex.blit_buffer(data, colorfmt="rgba", bufferfmt="ubyte")
            self._cached_render_texture = tex
            return tex
        except Exception as e:
            print("Texture generation failed:", e)
            return None

    def draw_pil_arrow_head_custom(self, draw, px, py, dx, dy, color, size=12):
        bx = px - size * dx
        by = py - size * dy
        perp_x = -dy
        perp_y = dx
        lx = bx + size * 0.4 * perp_x
        ly = by + size * 0.4 * perp_y
        rx = bx - size * 0.4 * perp_x
        ry = by - size * 0.4 * perp_y
        draw.polygon([(px, py), (lx, ly), (rx, ry)], fill=color)

    def draw_irregular_stone(self, draw, cx, cy, r_avg, index, fill_rgb, outline_rgb, alpha):
        vertices = []
        num_pts = 6
        for i in range(num_pts):
            angle = 2 * math.pi * i / num_pts
            noise_factor = 0.75 + 0.25 * math.sin(index * 1.7 + i * 2.3)
            size_variation = 0.8 + 0.4 * math.cos(index * 3.1)
            r = r_avg * noise_factor * size_variation
            rx = cx + r * math.cos(angle)
            ry = cy + r * math.sin(angle)
            vertices.append((rx, ry))
        draw.polygon(vertices, fill=fill_rgb + (alpha,), outline=outline_rgb + (alpha,))

    def draw_river_pebble(self, draw, cx, cy, r_avg, index, fill_rgb, outline_rgb, alpha):
        vertices = []
        num_pts = 8
        for i in range(num_pts):
            angle = 2 * math.pi * i / num_pts
            noise_factor = 0.82 + 0.18 * math.sin(index * 1.9 + i * 1.3)
            size_variation = 0.85 + 0.3 * math.cos(index * 2.7)
            r = r_avg * noise_factor * size_variation
            rx = cx + r * math.cos(angle)
            ry = cy + r * math.sin(angle)
            vertices.append((rx, ry))
        draw.polygon(vertices, fill=fill_rgb + (alpha,), outline=outline_rgb + (alpha,))

    def draw_centered_text(self, draw, position, text, font, fill):
        cx, cy = position
        try:
            draw.text((cx, cy), text, fill=fill, font=font, anchor="mm")
        except TypeError:
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                draw.text((cx - tw/2, cy - th/2 - bbox[1]/2), text, fill=fill, font=font)
            except AttributeError:
                try:
                    tw, th = draw.textsize(text, font=font)
                    draw.text((cx - tw/2, cy - th/2), text, fill=fill, font=font)
                except AttributeError:
                    tw = len(text) * (font.size * 0.6 if font else 8)
                    th = (font.size if font else 12)
                    draw.text((cx - tw/2, cy - th/2), text, fill=fill, font=font)

    def draw_pil_sad_sticker(self, draw, w, h):
        cx, cy = w / 2.0, h / 2.0
        rad_size = w * 0.15
        self.safe_draw_ellipse(draw, [cx - rad_size, cy - rad_size, cx + rad_size, cy + rad_size], fill=(255, 213, 74, 255), outline=(17, 17, 17, 255), width=2)
        eye_r, eye_dx, eye_dy = max(2.0, rad_size * 0.08), rad_size * 0.28, rad_size * 0.18
        self.safe_draw_ellipse(draw, [cx - eye_dx - eye_r, cy - eye_dy - eye_r, cx - eye_dx + eye_r, cy - eye_dy + eye_r], fill=(17, 17, 17, 255))
        self.safe_draw_ellipse(draw, [cx + eye_dx - eye_r, cy - eye_dy - eye_r, cx + eye_dx + eye_r, cy - eye_dy + eye_r], fill=(17, 17, 17, 255))
        try:
            draw.arc([cx - rad_size*0.55/2, cy + rad_size*0.34 - rad_size*0.32/2, cx + rad_size*0.55/2, cy + rad_size*0.34 + rad_size*0.32/2], 180, 360, fill=(17, 17, 17, 255), width=max(2, int(rad_size*0.06)))
        except TypeError:
            draw.arc([cx - rad_size*0.55/2, cy + rad_size*0.34 - rad_size*0.32/2, cx + rad_size*0.55/2, cy + rad_size*0.34 + rad_size*0.32/2], 180, 360, fill=(17, 17, 17, 255))

    def generate_visualization_image(self, w=800, h=800):
        if Image is None or ImageDraw is None:
            return None
        cuts = self.get_cut_segments()
        if cuts:
            img = Image.new("RGBA", (w, h), (230, 230, 230, 255))
            draw = ImageDraw.Draw(img)
            self.safe_draw_rectangle(draw, [0, 0, w, h], outline="black", width=4)
            for cx_corner, cy_corner in [(0, h), (w, h), (0, 0), (w, 0)]:
                draw.ellipse([cx_corner-6, cy_corner-6, cx_corner+6, cy_corner+6], fill="black")
            margin = 12
            seg_points = {
                "p1p2": ((margin, h - margin), (w - margin, h - margin)),
                "p2p4": ((w - margin, h - margin), (w - margin, margin)),
                "p4p3": ((w - margin, margin), (margin, margin)),
                "p3p1": ((margin, margin), (margin, h - margin)),
                "p1p4": ((margin, h - margin), (w - margin, margin)),
                "p2p3": ((w - margin, h - margin), (margin, margin))
            }
            for key, (A, B) in seg_points.items():
                if key in cuts:
                    dx = B[0] - A[0]
                    dy = B[1] - A[1]
                    L = math.hypot(dx, dy)
                    ux, uy = dx / L, dy / L
                    split_ratio = 0.25 if key in ["p1p4", "p2p3"] else 0.5
                    cx = A[0] + L * split_ratio * ux
                    cy = A[1] + L * split_ratio * uy
                    gap_len = 108.0
                    c1x = cx - (gap_len / 2.0) * ux
                    c1y = cy - (gap_len / 2.0) * ux
                    c2x = cx + (gap_len / 2.0) * ux
                    c2y = cy + (gap_len / 2.0) * ux
                    line_color = (255, 255, 255, 255) if self.blink_state else (0, 0, 0, 255)
                    draw.line([A[0], A[1], c1x, c1y], fill=line_color, width=6)
                    draw.line([c2x, c2y, B[0], B[1]], fill=line_color, width=6)
                    if self.blink_state:
                        self.draw_pil_arrow_head_custom(draw, c1x, c1y, ux, uy, (255, 0, 0, 255), size=26)
                        self.draw_pil_arrow_head_custom(draw, c2x, c2y, -ux, -uy, (255, 0, 0, 255), size=26)
                    draw.ellipse([c1x - 8, c1y - 8, c1x + 8, c1y + 8], fill=(255, 0, 0, 255))
                    draw.ellipse([c2x - 8, c2y - 8, c2x + 8, c2y + 8], fill=(255, 0, 0, 255))
                    warn_size = 28
                    w_pts = [
                        (cx, cy - warn_size),
                        (cx - warn_size * 1.1, cy + warn_size * 0.9),
                        (cx + warn_size * 1.1, cy + warn_size * 0.9)
                    ]
                    draw.polygon(w_pts, fill=(255, 193, 7, 255), outline=(0, 0, 0, 255))
                    try:
                        draw.text((cx - 6, cy - 10), "!", fill=(0, 0, 0, 255), font=self.get_pil_font(24, bold=True))
                    except Exception:
                        pass
                    warn_text = "پراپ قطع است" if self.lang == 'fa' else "Probe Disconnected"
                    if self.lang == 'fa':
                        warn_text = self.shape_text(warn_text)
                    f_warn = self.get_pil_font(22, bold=True)
                    try:
                        bbox = draw.textbbox((0, 0), warn_text, font=f_warn)
                        tw = bbox[2] - bbox[0]
                        th = bbox[3] - bbox[1]
                    except AttributeError:
                        tw, th = len(warn_text) * 12, 24
                    draw.text((cx - tw / 2, cy - warn_size - th - 10), warn_text, fill=(200, 0, 0, 255), font=f_warn)
                else:
                    if key in ["p1p4", "p2p3"]:
                        self.draw_pil_dashed_line(draw, A[0], A[1], B[0], B[1], (0, 0, 0, 255), width=2, dash=(10, 8))
                    else:
                        draw.line([A[0], A[1], B[0], B[1]], fill=(0, 0, 0, 255), width=3)
            return img

        img = Image.new("RGBA", (w, h), (230, 230, 230, 255))
        draw = ImageDraw.Draw(img)

        if self.show_geo_var and self.heatmap_data is not None and not self.gpr_active and not self.fibo_active and not self.compare_active:
            grid, nx, ny = self.heatmap_data["grid"], self.heatmap_data["nx"], self.heatmap_data["ny"]
            vmin, vmax = self.heatmap_data["min"], self.heatmap_data["max"]
            invert_for_void = self.has_void_circle()
            heatmap_img = Image.new("RGB", (nx, ny))
            for j in range(ny):
                yr = j / (ny - 1) if ny > 1 else 0.5
                for i in range(nx):
                    xr = i / (nx - 1) if nx > 1 else 0.5
                    rgb_color = self.resistance_relative_palette_color(grid[j][i], vmin, vmax, invert_for_void, xr, yr)
                    heatmap_img.putpixel((i, ny - 1 - j), rgb_color)
            img.paste(heatmap_img.resize((w, h), RESAMPLE_FILTER), (0, 0))
            self.draw_pil_contours_for_screen(draw, w, h, grid, nx, ny, vmin, vmax, max(4, 14 + 6*self.signal_correction_level))

        elif (self.gpr_active or self.fibo_active) and hasattr(self, 'scan_grid') and self.scan_grid is not None and not self.compare_active:
            self.draw_pil_gpr(draw, w, h, img)

        elif self.compare_active and self.heatmap_data is not None:
            nx, ny = 140, 140
            grid_geo = self.heatmap_data["grid"] if self.heatmap_data else []
            vmin = self.heatmap_data["min"] if self.heatmap_data else 0.0
            vmax = self.heatmap_data["max"] if self.heatmap_data else 100000.0
            min_xr = self.min_point["x_ratio"] if self.min_point else 0.5
            min_yr = self.min_point["y_ratio"] if self.min_point else 0.5
            invert_for_void = self.has_void_circle()
            span = vmax - vmin if vmax > vmin else 1.0

            img_geo = Image.new("RGBA", (nx, ny))
            self.fibo_active = False
            for j in range(ny):
                yr = j / (ny - 1) if ny > 1 else 0.5
                for i in range(nx):
                    xr = i / (nx - 1) if nx > 1 else 0.5
                    r_c, g_c, b_c = self.resistance_relative_palette_color(grid_geo[j][i], vmin, vmax, invert_for_void, xr, yr)
                    img_geo.putpixel((i, ny - 1 - j), (r_c, g_c, b_c, 255))

            img_fibo = Image.new("RGBA", (nx, ny))
            self.fibo_active = True
            for j in range(ny):
                ry = j / (ny - 1) if ny > 1 else 0.5
                for i in range(nx):
                    rx = i / (nx - 1) if nx > 1 else 0.5
                    val_fib = self.compute_gpr_fibonacci_value(rx, ry, vmin, vmax, min_xr, min_yr)
                    r_c, g_c, b_c = self.resistance_relative_palette_color(val_fib, vmin, vmax, invert_for_void, rx, ry)
                    img_fibo.putpixel((i, ny - 1 - j), (r_c, g_c, b_c, 255))

            img_gpr = Image.new("RGBA", (nx, ny))
            self.fibo_active = False
            R_red = 0.60
            gpr_centers = []
            if self.detected_circles:
                for circ in self.detected_circles[:2]:
                    gpr_centers.append((circ["center_x_ratio"], circ["center_y_ratio"]))
            else:
                gpr_centers.append((min_xr, min_yr))

            for j in range(ny):
                ry = j / (ny - 1) if ny > 1 else 0.5
                for i in range(nx):
                    rx = i / (nx - 1) if nx > 1 else 0.5
                    val_ana = grid_geo[j][i]
                    min_dist_m = float('inf')
                    for cx, cy in gpr_centers:
                        dist_m = math.hypot((rx - cx)*self.width_val, (ry - cy)*self.length_val)
                        if dist_m < min_dist_m:
                            min_dist_m = dist_m
                    if min_dist_m <= R_red:
                        val = self.lerp(val_ana, vmin, (1.0 - min_dist_m / R_red))
                    elif (val_ana - vmin)/span < 0.18:
                        val = vmin + 0.18*span
                    else:
                        val = val_ana
                    r_c, g_c, b_c = self.resistance_relative_palette_color(val, vmin, vmax, invert_for_void, rx, ry)
                    img_gpr.putpixel((i, ny - 1 - j), (r_c, g_c, b_c, 255))

            self.fibo_active = False
            img_geo_resized = img_geo.resize((w, h), RESAMPLE_FILTER)
            img_fibo_resized = img_fibo.resize((w, h), RESAMPLE_FILTER)
            img_gpr_resized = img_gpr.resize((w, h), RESAMPLE_FILTER)

            blend_first_two = Image.blend(img_geo_resized, img_fibo_resized, alpha=0.5)
            final_blend = Image.blend(blend_first_two, img_gpr_resized, alpha=0.333)
            img.paste(final_blend, (0, 0))
            draw = ImageDraw.Draw(img)
            self.draw_pil_contours_for_screen(draw, w, h, grid_geo, nx, ny, vmin, vmax, max(4, 14 + 6*self.signal_correction_level))

            overlapping_zones = []
            if self.detected_circles:
                for circ in self.detected_circles[:2]:
                    overlapping_zones.append((circ["center_x_ratio"], circ["center_y_ratio"]))
            else:
                overlapping_zones.append((min_xr, min_yr))

            for idx, (cx, cy) in enumerate(overlapping_zones):
                min_fib_val = float('inf')
                xf_local, yf_local = cx, cy
                if grid_geo:
                    for j in range(ny):
                        ry = j / (ny - 1) if ny > 1 else 0.5
                        for i in range(nx):
                            rx = i / (nx - 1) if nx > 1 else 0.5
                            if math.hypot(rx - cx, ry - cy) <= 0.20:
                                self.fibo_active = True
                                val_fib = self.compute_gpr_fibonacci_value(rx, ry, vmin, vmax, min_xr, min_yr)
                                self.fibo_active = False
                                if val_fib < min_fib_val:
                                    min_fib_val = val_fib
                                    xf_local, yf_local = rx, ry
                x_avg = (cx + cx + xf_local) / 3.0
                y_avg = (cy + cy + yf_local) / 3.0
                x_m = x_avg * self.width_val
                y_m = y_avg * self.length_val
                val = circ.get("target_value", 0.0) if self.detected_circles else vmin
                label = circ.get("label", "No Target") if self.detected_circles else "No Target"
                depth_text = "—"
                if self.show_depth_overlay and self.detected_circles:
                    depth_text = f"{self.calculate_target_depth(circ):.2f} m"
                translated_label = self.translate(label)
                if self.lang == 'fa':
                    x_m_str = self.convert_digits(f"{x_m:.2f}")
                    y_m_str = self.convert_digits(f"{y_m:.2f}")
                    val_str = self.convert_digits(f"{val:.0f}")
                    idx_str = self.convert_digits(str(idx+1))
                    depth_str = self.convert_digits(depth_text).replace("m", "متر")
                    raw_text = f"هدف {idx_str}:  [b][size=20sp]{translated_label}[/b][/size]      مقدار: {val_str}\nX = {x_m_str} متر        Y = {y_m_str} متر\nعمق (H) = {depth_str}"
                    target_text = self.shape_text(raw_text)
                else:
                    target_text = f"Target {idx+1}:  [b][size=20sp]{translated_label}[/size][/b]      Value: {val:.0f}\nX = {x_m:.2f} m        Y = {y_m:.2f} m\nDepth (H) = {depth_text}"
                cx_pix = x_avg * w
                cy_pix = h - y_avg * h

                circle_overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                ol_draw = ImageDraw.Draw(circle_overlay)
                px_per_m = w / max(self.width_val, 1e-9)
                radius = (0.5 * px_per_m) / 2.0
                ol_draw.ellipse([cx_pix - radius, cy_pix - radius, cx_pix + radius, cy_pix + radius], fill=(255, 255, 255, 40), outline=(255, 255, 255, 255), width=3)
                ol_draw.ellipse([cx_pix - 4, cy_pix - 4, cx_pix + 4, cy_pix + 4], fill=(255, 255, 255, 255))
                img.paste(circle_overlay, (0, 0), circle_overlay)

                self.draw_pil_dashed_line(draw, 0, cy_pix + 1, cx_pix, cy_pix + 1, (0, 0, 0, 255), 2, (10, 8))
                self.draw_pil_dashed_line(draw, cx_pix + 1, cy_pix, cx_pix + 1, h, (0, 0, 0, 255), 2, (10, 8))
                self.draw_pil_dashed_line(draw, 0, cy_pix, cx_pix, cy_pix, (0, 0, 0, 255), 2, (10, 8))
                self.draw_pil_dashed_line(draw, cx_pix, cy_pix, cx_pix, h, (0, 0, 0, 255), 2, (10, 8))

        self.safe_draw_rectangle(draw, [0, 0, w, h], outline="black", width=4)
        self.draw_pil_dashed_line(draw, 0, 0, w, h, (40, 40, 40, 255), 2, (10, 8))
        self.draw_pil_dashed_line(draw, 0, h, w, 0, (40, 40, 40, 255), 2, (10, 8))
        for cx, cy in [(0, h), (w, h), (0, 0), (w, 0)]:
            draw.ellipse([cx-6, cy-6, cx+6, cy+6], fill="black")

        target_w = w - 100
        target_h = h - 100
        font_sz = 80
        for fs in range(250, 10, -5):
            f_test = self.get_pil_font(fs, bold=True)
            if not f_test:
                continue
            try:
                test_img = Image.new("RGBA", (1, 1))
                test_draw = ImageDraw.Draw(test_img)
                if hasattr(test_draw, 'textbbox'):
                    box = test_draw.textbbox((0, 0), "Cornix\nWinner", font=f_test)
                    tw = box[2] - box[0]
                    th = box[3] - box[1]
                else:
                    tw, th = test_draw.multiline_textsize("Cornix\nWinner", font=f_test)
                if tw <= target_w and th <= target_h:
                    font_sz = fs
                    break
            except Exception:
                tw = 6 * fs * 0.65
                th = fs * 2.3
                if tw <= target_w and th <= target_h:
                    font_sz = fs
                    break

        font_watermark_screen = self.get_pil_font(font_sz, bold=True)
        if font_watermark_screen:
            self.draw_rotated_text(img, "Cornix\nWinner", (w // 2, h // 2 - 35), 0, font_watermark_screen, (0, 0, 0, 18))

        if self.soil_contaminated:
            self.draw_pil_soil_contamination_overlay(draw, w, h)
            self.draw_pil_sad_sticker(draw, w, h)

        elif self.detected_circles and not self.compare_active:
            px_per_m = w / max(self.width_val, 1e-9)
            in_gpr_or_fibo = self.gpr_active or self.fibo_active

            for idx, circ in enumerate(self.detected_circles):
                cx = circ["center_x_ratio"] * w
                cy = h - circ["center_y_ratio"] * h
                radius = max(12.0, (circ["diameter_m"] * px_per_m) / 2.0)
                show_guide_lines = False
                if not in_gpr_or_fibo:
                    show_guide_lines = True
                else:
                    show_guide_lines = getattr(self, 'gpr_fibo_skeleton_visible', False)
                if self.fibo_active:
                    show_guide_lines = False
                if show_guide_lines:
                    self.draw_pil_dashed_line(draw, 0, cy, cx, cy, (0, 0, 0, 255), 1, (8, 6))
                    self.draw_pil_dashed_line(draw, cx, cy, cx, h, (0, 0, 0, 255), 1, (8, 6))
                
                fill_hex = circ.get("fill_color", "#ff0000")
                label = circ.get("label", "")
                if not in_gpr_or_fibo:
                    self.safe_draw_ellipse(draw, [cx-radius, cy-radius, cx+radius, cy+radius], fill=(int(fill_hex[1:3], 16), int(fill_hex[3:5], 16), int(fill_hex[5:7], 16), 255), outline=(58, 58, 58, 255), width=3)
                    text_inside = str(idx + 1) if label not in ["Unknown", "No Target"] else "!"
                    if self.lang == 'fa':
                        text_inside = self.convert_digits(text_inside)
                    font_sz = int(max(24, min(radius * 1.35, 75)))
                    f_circle = self.get_pil_font(font_sz, bold=True)
                    fill_lower = fill_hex.lower()
                    if fill_lower == "#0000ff":
                        tc = (255, 255, 255, 255)
                    elif fill_lower == "#ffd700":
                        tc = (0, 0, 0, 255)
                    elif fill_lower == "#ff0000":
                        tc = (255, 255, 255, 255)
                    elif fill_lower == "#8b4513":
                        tc = (255, 255, 255, 255)
                    elif fill_lower in ["#8000ff", self.PURPLE.lower()]:
                        tc = (255, 255, 255, 255)
                    elif fill_lower == "#ffa500":
                        tc = (0, 0, 0, 255)
                    elif fill_lower in ["#808080", "#d3d3d3"]:
                        tc = (0, 0, 0, 255)
                    else:
                        tc = (255, 255, 255, 255)
                    self.draw_centered_text(draw, (cx, cy), text_inside, f_circle, tc)
                
                is_water_or_void = label in ["water", "Void", "Small Void", "Medium Void", "Big Void"]
                if self.fibo_active and not self.scanning and self.transition_step >= 2 and is_water_or_void:
                    num_fragments = 18
                    for i in range(num_fragments):
                        angle = 2 * math.pi * i / num_fragments
                        if i % 2 == 0:
                            p1 = (cx + (radius * 1.15) * math.cos(angle), cy + (radius * 1.15) * math.sin(angle))
                            p2 = (cx + (radius * 1.45) * math.cos(angle - 0.11), cy + (radius * 1.45) * math.sin(angle - 0.11))
                            p3 = (cx + (radius * 1.45) * math.cos(angle + 0.11), cy + (radius * 1.45) * math.sin(angle + 0.11))
                        else:
                            p1 = (cx + (radius * 1.45) * math.cos(angle), cy + (radius * 1.45) * math.sin(angle))
                            p2 = (cx + (radius * 1.15) * math.cos(angle - 0.11), cy + (radius * 1.15) * math.sin(angle - 0.11))
                            p3 = (cx + (radius * 1.15) * math.cos(angle + 0.11), cy + (radius * 1.15) * math.sin(angle + 0.11))
                        draw.polygon([p1, p2, p3], fill=(140, 140, 140, 255), outline=(60, 60, 60, 255))
                
                vis_mode = self.evaluate_skeleton_or_chamber(circ)
                can_draw_skeleton = False
                can_draw_chamber = False
                
                if not self.fibo_active:
                    show_mode_allowed = False
                    if not in_gpr_or_fibo:
                        show_mode_allowed = True
                    else:
                        show_mode_allowed = getattr(self, 'gpr_fibo_skeleton_visible', False)
                        
                    if show_mode_allowed:
                        if vis_mode == "skeleton":
                            can_draw_skeleton = True
                        elif vis_mode == "chamber":
                            can_draw_chamber = True

                if can_draw_skeleton:
                    px_per_m_x = w / max(self.width_val, 1e-9)
                    px_per_m_y = h / max(self.length_val, 1e-9)
                    sk_w = int(max(40.0, min(w * 0.4, 0.5 * px_per_m_x)))
                    sk_h = int(max(80.0, min(h * 0.8, 1.0 * px_per_m_y)))
                    sk_img = Image.new("RGBA", (sk_w, sk_h), (0, 0, 0, 0))
                    ol_draw = ImageDraw.Draw(sk_img)
                    ol_draw.rectangle([0, 0, sk_w, sk_h], fill=(70, 45, 20, 255))
                    stone_radius_c = min(sk_w, sk_h) * 0.05
                    stone_radius_c = max(3.0, min(14.0, stone_radius_c))
                    stone_fill_c = (130, 130, 130, 255)
                    stone_outline_c = (80, 80, 80, 255)
                    def draw_stone_c(sx_c, sy_c):
                        ol_draw.ellipse([sx_c - stone_radius_c, sy_c - stone_radius_c, sx_c + stone_radius_c, sy_c + stone_radius_c], fill=stone_fill_c, outline=stone_outline_c, width=1)
                    num_x_c = max(5, int(sk_w / (stone_radius_c * 2.2)))
                    for i_s_c in range(num_x_c + 1):
                        t_s_c = i_s_c / num_x_c
                        px_s_c = t_s_c * sk_w
                        draw_stone_c(px_s_c, 0)
                        draw_stone_c(px_s_c, sk_h)
                    num_y_c = max(8, int(sk_h / (stone_radius_c * 2.2)))
                    for j_s_c in range(1, num_y_c):
                        t_s_c = j_s_c / num_y_c
                        py_s_c = t_s_c * sk_h
                        draw_stone_c(0, py_s_c)
                        draw_stone_c(sk_w, py_s_c)
                    scx_c = sk_w / 2.0
                    scy_c = sk_h / 2.0
                    bone_color_c = (245, 245, 230, 255)
                    bone_outline_c = (100, 100, 100, 255)
                    skull_r_c = min(sk_w, sk_h) * 0.08
                    skull_cy_c = scy_c - sk_h * 0.33
                    ol_draw.ellipse([scx_c - skull_r_c, skull_cy_c - skull_r_c, scx_c + skull_r_c, skull_cy_c + skull_r_c], fill=bone_color_c, outline=bone_outline_c, width=1)
                    eye_r_c = skull_r_c * 0.25
                    ol_draw.ellipse([scx_c - skull_r_c * 0.4 - eye_r_c, skull_cy_c - skull_r_c * 0.1 - eye_r_c, scx_c - skull_r_c * 0.4 + eye_r_c, skull_cy_c - skull_r_c * 0.1 + eye_r_c], fill=(0, 0, 0, 255))
                    ol_draw.ellipse([scx_c + skull_r_c * 0.4 - eye_r_c, skull_cy_c - skull_r_c * 0.1 - eye_r_c, scx_c + skull_r_c * 0.4 + eye_r_c, skull_cy_c - skull_r_c * 0.1 + eye_r_c], fill=(0, 0, 0, 255))
                    ol_draw.polygon([(scx_c, skull_cy_c + skull_r_c * 0.25), (scx_c - skull_r_c * 0.15, skull_cy_c + skull_r_c * 0.45), (scx_c + skull_r_c * 0.15, skull_cy_c + skull_r_c * 0.45)], fill=(0, 0, 0, 255))
                    spine_top_c = skull_cy_c + skull_r_c
                    spine_bottom_c = scy_c + sk_h * 0.15
                    ol_draw.line([scx_c, spine_top_c, scx_c, spine_bottom_c], fill=bone_color_c, width=4)
                    shoulder_w_c = sk_w * 0.32
                    ol_draw.line([scx_c - shoulder_w_c, spine_top_c + 4, scx_c + shoulder_w_c, spine_top_c + 4], fill=bone_color_c, width=3)
                    rib_start_y_c = spine_top_c + sk_h * 0.06
                    rib_end_y_c = spine_top_c + sk_h * 0.32
                    num_ribs_c = 5
                    for r_i_c in range(num_ribs_c):
                        ry_pos_c = rib_start_y_c + (r_i_c / (num_ribs_c - 1)) * (rib_end_y_c - rib_start_y_c)
                        rib_w_c = sk_w * 0.26 * (1.0 - 0.22 * abs(r_i_c - 2) / 2.0)
                        ol_draw.ellipse([scx_c - rib_w_c, ry_pos_c - 4, scx_c + rib_w_c, ry_pos_c + 4], outline=bone_color_c, width=2)
                    pelvis_w_c = sk_w * 0.22
                    ol_draw.ellipse([scx_c - pelvis_w_c, spine_bottom_c - 6, scx_c + pelvis_w_c, spine_bottom_c + 6], fill=bone_color_c, outline=bone_outline_c, width=1)
                    elbow_y_c = spine_top_c + sk_h * 0.24
                    hand_y_c = spine_top_c + sk_h * 0.42
                    ol_draw.line([scx_c - shoulder_w_c, spine_top_c + 4, scx_c - shoulder_w_c - sk_w * 0.04, elbow_y_c], fill=bone_color_c, width=3)
                    ol_draw.line([scx_c - shoulder_w_c - sk_w * 0.04, elbow_y_c, scx_c - shoulder_w_c + sk_w * 0.02, hand_y_c], fill=bone_color_c, width=3)
                    ol_draw.line([scx_c + shoulder_w_c, spine_top_c + 4, scx_c + shoulder_w_c + sk_w * 0.04, elbow_y_c], fill=bone_color_c, width=3)
                    ol_draw.line([scx_c + shoulder_w_c + sk_w * 0.04, elbow_y_c, scx_c + shoulder_w_c - sk_w * 0.02, hand_y_c], fill=bone_color_c, width=3)
                    pelvis_w_c = sk_w * 0.22
                    ol_draw.ellipse([scx_c - pelvis_w_c, spine_bottom_c - 6, scx_c + pelvis_w_c, spine_bottom_c + 6], fill=bone_color_c, outline=bone_outline_c, width=1)
                    pelvis_l_x_c = scx_c - pelvis_w_c * 0.6
                    pelvis_r_x_c = scx_c + pelvis_w_c * 0.6
                    knee_y_c = spine_bottom_c + sk_h * 0.24
                    foot_y_c = spine_bottom_c + sk_h * 0.45
                    ol_draw.line([pelvis_l_x_c, spine_bottom_c, pelvis_l_x_c - sk_w * 0.03, knee_y_c], fill=bone_color_c, width=3)
                    ol_draw.line([pelvis_l_x_c - sk_w * 0.03, knee_y_c, pelvis_l_x_c, foot_y_c], fill=bone_color_c, width=3)
                    ol_draw.line([pelvis_r_x_c, spine_bottom_c, pelvis_r_x_c + sk_w * 0.03, knee_y_c], fill=bone_color_c, width=3)
                    ol_draw.line([pelvis_r_x_c + sk_w * 0.03, knee_y_c, pelvis_r_x_c, foot_y_c], fill=bone_color_c, width=3)
                    min_pt = self.min_point
                    if min_pt:
                        mx_pix = min_pt["x_ratio"] * w
                        my_pix = h - min_pt["y_ratio"] * h
                        dx_v = mx_pix - cx
                        dy_v = my_pix - cy
                        if math.hypot(dx_v, dy_v) > 1e-3:
                            angle_deg = math.degrees(math.atan2(dy_v, dx_v)) + 90.0
                        else:
                            angle_deg = 0.0
                    else:
                        angle_deg = 0.0
                    try:
                        rotated_sk = sk_img.rotate(-angle_deg, expand=True, resample=Image.Resampling.BICUBIC)
                    except AttributeError:
                        rotated_sk = sk_img.rotate(-angle_deg, expand=True, resample=Image.BICUBIC)
                    skeleton_alpha_factor = 0.4 if in_gpr_or_fibo else 0.5
                    r_sk, g_sk, b_sk, a_sk = rotated_sk.split()
                    a_sk = a_sk.point(lambda p: int(p * skeleton_alpha_factor))
                    rotated_sk = Image.merge("RGBA", (r_sk, g_sk, b_sk, a_sk))
                    rw_r, rh_r = rotated_sk.size
                    img.paste(rotated_sk, (int(cx - rw_r/2), int(cy - rh_r/2)), rotated_sk)
                    draw = ImageDraw.Draw(img)

                elif can_draw_chamber:
                    px_per_m_x = w / max(self.width_val, 1e-9)
                    px_per_m_y = h / max(self.length_val, 1e-9)
                    
                    chamber_w_m = 0.70  
                    chamber_h_m = 1.00  
                    chamber_w = int(chamber_w_m * px_per_m_x)
                    chamber_h = int(chamber_h_m * px_per_m_y)
                    
                    min_pt = self.min_point
                    if min_pt:
                        mx_pix = min_pt["x_ratio"] * w
                        my_pix = h - min_pt["y_ratio"] * h
                        dx_v = mx_pix - cx
                        dy_v = my_pix - cy
                        if math.hypot(dx_v, dy_v) > 1e-3:
                            angle_deg = math.degrees(math.atan2(dy_v, dx_v)) + 90.0
                        else:
                            angle_deg = 0.0
                    else:
                        angle_deg = 0.0
                        
                    pad = int(max(chamber_w, chamber_h) * 0.5) + 10
                    ch_img_w = chamber_w + pad * 2
                    ch_img_h = chamber_h + pad * 2
                    ch_img = Image.new("RGBA", (ch_img_w, ch_img_h), (0, 0, 0, 0))
                    ch_draw = ImageDraw.Draw(ch_img)
                    
                    self.safe_draw_rectangle(ch_draw, [pad + 1, pad + 1, pad + chamber_w - 1, pad + chamber_h - 1], fill=(128, 0, 255, 60))
                    
                    stone_radius = max(8.0, min(chamber_w, chamber_h) * 0.11)
                    
                    num_x_stones = int(chamber_w / (stone_radius * 1.1)) + 1
                    for idx_s in range(num_x_stones):
                        tx_s = idx_s / max(1, num_x_stones - 1)
                        sx_s = pad + tx_s * chamber_w
                        ch_draw.ellipse([sx_s - stone_radius, pad - stone_radius, sx_s + stone_radius, pad + stone_radius], fill=(0, 0, 0, 255))
                        ch_draw.ellipse([sx_s - stone_radius, pad + chamber_h - stone_radius, sx_s + stone_radius, pad + chamber_h + stone_radius], fill=(0, 0, 0, 255))
                        
                    num_y_stones = int(chamber_h / (stone_radius * 1.1)) + 1
                    for jdy_s in range(num_y_stones):
                        ty_s = jdy_s / max(1, num_y_stones - 1)
                        sy_s = pad + ty_s * chamber_h
                        ch_draw.ellipse([pad - stone_radius, sy_s - stone_radius, pad + stone_radius, sy_s + stone_radius], fill=(0, 0, 0, 255))
                        ch_draw.ellipse([pad + chamber_w - stone_radius, sy_s - stone_radius, pad + chamber_w + stone_radius, sy_s + stone_radius], fill=(0, 0, 0, 255))
                    
                    try:
                        rotated_ch = ch_img.rotate(-angle_deg, expand=True, resample=Image.Resampling.BICUBIC)
                    except AttributeError:
                        rotated_ch = ch_img.rotate(-angle_deg, expand=True, resample=Image.BICUBIC)
                        
                    rw_r, rh_r = rotated_ch.size
                    img.paste(rotated_ch, (int(cx - rw_r/2), int(cy - rh_r/2)), rotated_ch)
                    draw = ImageDraw.Draw(img)
                    
                    box_text = "احتمالا فلز داخل فضای خالی یا خاک ماسه ای است" if self.lang == 'fa' else "Probably metal inside void or sandy soil"
                    if self.lang == 'fa':
                        box_text = self.shape_text(box_text)
                        
                    f_box = self.get_pil_font(13, bold=True)
                    try:
                        if hasattr(draw, 'textbbox'):
                            box_t = draw.textbbox((0, 0), box_text, font=f_box)
                            tw = box_t[2] - box_t[0]
                            th = box_t[3] - box_t[1]
                        else:
                            tw, th = draw.textsize(box_text, font=f_box)
                    except Exception:
                        tw = len(box_text) * 7.5
                        th = 15
                        
                    padding_x, padding_y = 12, 8
                    box_w = tw + padding_x * 2
                    box_h = th + padding_y * 2

                    space_left = cx
                    space_right = w - cx
                    space_top = cy
                    space_bottom = h - cy
                    
                    dx_sign = 1 if space_right > space_left else -1
                    dy_sign = 1 if space_bottom > space_top else -1
                    
                    mag = math.hypot(dx_sign, dy_sign * 0.7)
                    ux_away = dx_sign / mag if mag > 0 else 1.0
                    uy_away = (dy_sign * 0.7) / mag if mag > 0 else 0.0
                    
                    half_w = chamber_w / 2.0
                    half_h = chamber_h / 2.0
                    
                    theta_rad = math.radians(-angle_deg)
                    cos_t = math.cos(theta_rad)
                    sin_t = math.sin(theta_rad)
                    local_dir_x = ux_away * cos_t - uy_away * sin_t
                    local_dir_y = ux_away * sin_t + uy_away * cos_t
                    
                    t_candidates = []
                    if abs(local_dir_x) > 1e-5:
                        t_candidates.append(half_w / abs(local_dir_x))
                    if abs(local_dir_y) > 1e-5:
                        t_candidates.append(half_h / abs(local_dir_y))
                    t_edge = min(t_candidates) if t_candidates else half_w
                    
                    t_edge_outer = t_edge + stone_radius
                    
                    touch_x = cx + t_edge_outer * ux_away
                    touch_y = cy + t_edge_outer * uy_away
                    
                    arrow_len = 28.0
                    arrow_start_x = touch_x + arrow_len * ux_away
                    arrow_start_y = touch_y + arrow_len * uy_away
                    
                    bx_center_x = arrow_start_x + (box_w / 2.0) * ux_away
                    bx_center_y = arrow_start_y + (box_h / 2.0) * uy_away
                    
                    bx_left = bx_center_x - box_w / 2.0
                    bx_top = bx_center_y - box_h / 2.0
                    
                    bx_left = self.clamp(bx_left, 20.0, w - box_w - 20.0)
                    bx_top = self.clamp(bx_top, 20.0, h - box_h - 20.0)
                    
                    self.draw_pil_arrow(draw, arrow_start_x, arrow_start_y, touch_x, touch_y, color=(255, 165, 0, 255), width=3)
                    
                    self.safe_draw_rounded_rectangle(draw, [bx_left, bx_top, bx_left + box_w, bx_top + box_h], radius=6, fill=(35, 35, 35, 230), outline=(255, 165, 0, 255), width=2)
                    
                    text_x = bx_left + padding_x + tw / 2
                    text_y = bx_top + padding_y + th / 2
                    self.draw_centered_text(draw, (text_x, text_y), box_text, f_box, (255, 255, 255, 255))

        if self.warning_arrows and not self.soil_contaminated and not self.gpr_active and not self.fibo_active and not self.compare_active:
            for arr in self.warning_arrows:
                arr_color = arr.get("color", (17, 17, 17, 255))
                self.draw_pil_arrow(draw, arr["start_x_ratio"]*w, h - arr["start_y_ratio"]*h, arr["end_x_ratio"]*w, h - arr["end_y_ratio"]*h, arr_color, 3)

        if self.fibo_active and ImageFilter is not None:
            img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
            draw = ImageDraw.Draw(img)
        return img

    def draw_pil_dashed_line(self, draw, x0, y0, x1, y1, fill, width=1, dash=(5, 5)):
        dist = math.hypot(x1 - x0, y1 - y0)
        if dist == 0:
            return
        ux, uy = (x1 - x0) / dist, (y1 - y0) / dist
        step = sum(dash)
        for i in range(0, int(dist), step):
            sx, sy = x0 + i * ux, y0 + i * uy
            ex, ey = sx + dash[0] * ux, sy + dash[0] * uy
            draw.line([sx, sy, ex, ey], fill=fill, width=width)

    def draw_pil_contours_for_screen(self, draw, w, h, grid, nx, ny, vmin, vmax, levels, color=(58, 58, 58, 255)):
        contour_vals = [vmin + (text_k + 1) * (vmax - vmin) / (levels + 1) for text_k in range(levels)]
        def interp(p1, p2, v1, v2, level):
            if abs(v2 - v1) < 1e-12:
                return p1
            t = self.clamp((level - v1) / (v2 - v1), 0.0, 1.0)
            return (p1[0] + t*(p2[0]-p1[0]), p1[1] + t*(p2[1]-p1[1]))
        for level in contour_vals:
            for j in range(ny - 1):
                for i in range(nx - 1):
                    pts = []
                    mx0, mx1 = i / (nx - 1), (i + 1) / (nx - 1)
                    my0, my1 = j / (ny - 1), (j + 1) / (ny - 1)
                    if (grid[j][i] - level) * (grid[j][i+1] - level) < 0:
                        pts.append(interp((mx0, my0), (mx1, my0), grid[j][i], grid[j][i+1], level))
                    if (grid[j][i+1] - level) * (grid[j+1][i+1] - level) < 0:
                        pts.append(interp((mx1, my0), (mx1, my1), grid[j][i+1], grid[j+1][i+1], level))
                    if (grid[j+1][i] - level) * (grid[j+1][i+1] - level) < 0:
                        pts.append(interp((mx0, my1), (mx1, my1), grid[j+1][i], grid[j+1][i+1], level))
                    if (grid[j][i] - level) * (grid[j+1][i] - level) < 0:
                        pts.append(interp((mx0, my0), (mx0, my1), grid[j][i], grid[j+1][i], level))
                    if len(pts) == 2:
                        draw.line([pts[0][0]*w, h - pts[0][1]*h, pts[1][0]*w, h - pts[1][1]*h], fill=color, width=1)

    def draw_pil_gpr(self, draw, w, h, img):
        sg_ny = len(self.scan_grid)
        sg_nx = len(self.scan_grid[0]) if sg_ny > 0 else 1
        if self.transition_step > 0:
            step = self.transition_step
            render_nx, render_ny, blur_sigma, R_red = (60, 60, 0.5, 0.90) if step==1 else ((100, 100, 1.0, 0.75) if step==2 else (140, 140, 1.5, 0.60))
            trans_grid = [[0.0 for _ in range(render_nx)] for _ in range(render_ny)]
            ag_grid = self.heatmap_data["grid"] if self.heatmap_data else None
            ag_ny = len(ag_grid) if ag_grid else 1
            ag_nx = len(ag_grid[0]) if ag_grid and ag_ny > 0 else 1
            flat_ana = [vv for row in ag_grid for vv in row] if ag_grid else []
            vmin, vmax = min(flat_ana) if flat_ana else 0.0, max(flat_ana) if flat_ana else 100000.0
            span = vmax - vmin if vmax > vmin else 1.0
            min_xr = self.min_point["x_ratio"] if self.min_point else 0.5
            min_yr = self.min_point["y_ratio"] if self.min_point else 0.5
            for j in range(render_ny):
                ry = j / (render_ny - 1) if render_ny > 1 else 0.5
                for i in range(render_nx):
                    rx = i / (render_nx - 1) if render_nx > 1 else 0.5
                    val_pix = self.scan_grid[int(self.clamp(ry*(sg_ny-1), 0, sg_ny-1))][int(self.clamp(rx*(sg_nx-1), 0, sg_nx-1))]
                    if val_pix is None:
                        val_pix = vmin + 0.5 * span
                    if self.fibo_active:
                        val_fib = self.compute_gpr_fibonacci_value(rx, ry, vmin, vmax, min_xr, min_yr)
                        val = self.lerp(val_pix, val_fib, step/2.0)
                    else:
                        val_ana = ag_grid[int(self.clamp(ry*(ag_ny-1), 0, ag_ny-1))][int(self.clamp(rx*(ag_nx-1), 0, ag_nx-1))] if ag_grid else val_pix
                        val = self.lerp(val_pix, val_ana, step/3.0)
                        dist_m = math.hypot((rx - min_xr)*self.width_val, (ry - min_yr)*self.length_val)
                        if dist_m <= R_red:
                            val = self.lerp(val, vmin, (1.0 - dist_m / R_red) * (step/3.0))
                        elif (val - vmin)/span < 0.18:
                            val = vmin + self.lerp((val - vmin)/span, 0.18, step/3.0)*span
                    trans_grid[j][i] = val
            trans_grid = self.gaussian_blur_2d(trans_grid, blur_sigma)
            flat_trans = [vv for row in trans_grid for vv in row]
            tmin, tmax = min(flat_trans) if flat_trans else vmin, max(flat_trans) if flat_trans else vmax
            heatmap_img = Image.new("RGB", (render_nx, render_ny))
            invert_for_void = self.has_void_circle()
            for j in range(render_ny):
                ry_local = j / (render_ny - 1) if render_ny > 1 else 0.5
                for i in range(render_nx):
                    rx_local = i / (render_nx - 1) if render_nx > 1 else 0.5
                    rgb_color = self.resistance_relative_palette_color(trans_grid[j][i], tmin, tmax, invert_for_void, rx_local, ry_local)
                    heatmap_img.putpixel((i, render_ny - 1 - j), rgb_color)
            img.paste(heatmap_img.resize((w, h), RESAMPLE_FILTER), (0, 0))
            draw = ImageDraw.Draw(img)
            if step >= 2:
                self.draw_pil_contours_for_screen(draw, w, h, trans_grid, render_nx, render_ny, tmin, tmax, 14, (58, 58, 58, 255))
        else:
            scanned_vals = [self.scan_grid[r][c] for r in range(sg_ny) for c in range(sg_nx) if self.scan_grid[r][c] is not None]
            if scanned_vals:
                curr_min, curr_max = min(scanned_vals), max(scanned_vals)
                cell_w, cell_h = w / sg_nx, h / sg_ny
                for r in range(sg_ny):
                    for c in range(sg_nx):
                        val = self.scan_grid[r][c]
                        if val is not None:
                            if abs(val - curr_min) < 0.1:
                                rgb_color = (255, 0, 0)
                            else:
                                rgb_color = self.resistance_relative_palette_color(val, curr_min, curr_max)
                            draw.rectangle([c*cell_w, h - (r+1)*cell_h, (c+1)*cell_w, h - r*cell_h], fill=(rgb_color[0], rgb_color[1], rgb_color[2], 255))
        if self.final_min_points:
            for rx, ry, val, color in self.final_min_points:
                cx, cy = rx * w, h - ry * h
                fc = (255, 0, 0, 255) if color == "red" else (255, 165, 0, 255)
                self.safe_draw_ellipse(draw, [cx-4, cy-4, cx+4, cy+4], fill=fc, outline=(0, 0, 0, 255), width=1)
        if self.scanning:
            cell_w, cell_h = w / self.scan_cols, h / self.scan_rows
            self.safe_draw_rectangle(draw, [self.scan_current_col*cell_w, h - (self.scan_current_row+1)*cell_h, (self.scan_current_col+1)*cell_w, h - self.scan_current_row*cell_h], fill=None, outline=(255, 255, 0, 255), width=2)

    def draw_pil_soil_contamination_overlay(self, draw, w, h):
        spacing, dot_r, row = 30, 2, 0
        yy = spacing // 2
        while yy <= h - spacing // 2:
            xx = spacing // 2 if row % 2 else 0
            while xx <= w - spacing // 2:
                draw.ellipse([xx - dot_r, yy - dot_r, xx + dot_r, yy + dot_r], fill=(0, 0, 0, 255))
                xx += spacing
            yy += spacing
            row += 1

    def draw_pil_arrow(self, draw, x0, y0, x1, y1, color=(255, 0, 0), width=4):
        draw.line([x0, y0, x1, y1], fill=color, width=width)
        angle = math.atan2(y1 - y0, x1 - x0)
        arrow_size = 15
        p1 = (x1 - arrow_size * math.cos(angle - math.pi/6), y1 - arrow_size * math.sin(angle - math.pi/6))
        p2 = (x1 - arrow_size * math.cos(angle + math.pi/6), y1 - arrow_size * math.sin(angle + math.pi/6))
        draw.polygon([(x1, y1), p1, p2], fill=color)

    def draw_pil_edge_labels(self, draw, w, h):
        e = {k: self.ui_entry_values[k] for k in self.edge_keys}
        font = self.get_pil_font(12, bold=True)
        def draw_txt(text, cx, cy):
            if not text: return
            try:
                box = draw.textbbox((0, 0), text, font=font)
                tw, th = box[2] - box[0], box[3] - box[1]
            except Exception:
                tw, th = len(text) * 7, 12
            draw_txt_cx = cx - tw / 2
            draw_txt_cy = cy - th / 2
            draw.text((draw_txt_cx, draw_txt_cy), text, fill=(0, 0, 0, 255), font=font)
        draw_txt(e["p1p2"], w / 2, h - 20)
        draw_txt(e["p2p4"], w - 30, h / 2)
        draw_txt(e["p4p3"], w / 2, 20)
        draw_txt(e["p3p1"], 30, h / 2)
        draw_txt(e["p1p4"], w / 2 - 25, h / 2 - 25)
        draw_txt(e["p2p3"], w / 2 + 25, h / 2 + 25)

    def get_pil_font(self, text_size, bold=False):
        try:
            from kivy.resources import resource_find
            font_path = resources.resource_find('fonts/DejaVuSans.ttf')
            if font_path:
                return ImageFont.truetype(font_path, text_size)
        except Exception:
            pass
        for font_name in ["arialb.ttf" if bold else "arial.ttf", "LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf", "sans-serif"]:
            try:
                return ImageFont.truetype(font_name, text_size)
            except Exception:
                pass
        try:
            return ImageFont.load_default(size=text_size)
        except Exception:
            return ImageFont.load_default()

    def draw_rotated_text(self, img, text, position, angle, font, fill):
        if not text:
            return
        temp_img = Image.new("RGBA", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        try:
            if hasattr(temp_draw, 'textbbox'):
                box = temp_draw.textbbox((0, 0), text, font=font)
                tw = box[2] - box[0]
                th = box[3] - box[1]
            else:
                tw, th = temp_draw.multiline_textsize(text, font=font)
        except Exception:
            lines = text.split('\n')
            tw = max(len(line) for line in lines) * (font.size * 0.6)
            th = len(lines) * font.size * 1.2
        pad = 30
        txt_w = int(tw) + pad * 2
        txt_h = int(th) + pad * 2
        txt_img = Image.new("RGBA", (txt_w, txt_h), (0, 0, 0, 0))
        txt_draw = ImageDraw.Draw(txt_img)
        try:
            txt_draw.multiline_text((txt_w / 2, txt_h / 2), text, fill=fill, font=font, align="center", anchor="mm")
        except Exception:
            lines = text.split('\n')
            y = pad
            for line in lines:
                try:
                    lw, lh = txt_draw.textsize(line, font=font)
                except Exception:
                    lw, lh = len(line) * (font.size * 0.6), font.size
                txt_draw.text(((txt_w - lw) / 2, y), line, fill=fill, font=font)
                y += lh + 4
        try:
            rotated_img = txt_img.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
        except AttributeError:
            rotated_img = txt_img.rotate(angle, expand=True, resample=Image.BICUBIC)
        rw, rh = rotated_img.size
        text_px, text_py = position
        paste_x = int(text_px - rw / 2)
        paste_y = int(text_py - rh / 2)
        img.paste(rotated_img, (paste_x, paste_y), rotated_img)

    def geo_click(self, *args):
        if self.check_cuts_and_warn():
            return
        self.show_geo_var = True
        self.fibo_active = False
        self.gpr_active = False
        self.compare_active = False
        self.scanning = False
        self.transition_step = 0
        self.gpr_fibo_skeleton_visible = False
        self.calculate_geophysics_heatmap()
        self.invalidate_render_cache()
        self.update_button_states()
        self._update_target_bg(self.t1, None)
        self._update_target_bg(self.t2, None)
        self.monitor.redraw()

    def fibo_click(self, *args):
        if self.check_cuts_and_warn():
            return
        self.show_geo_var = False
        self.fibo_active = True
        self.gpr_active = False
        self.compare_active = False
        self.start_gpr_zigzag_scan()
        self.invalidate_render_cache()
        self.update_button_states()
        self._update_target_bg(self.t1, None)
        self._update_target_bg(self.t2, None)
        self.monitor.redraw()

    def gpr_click(self, *args):
        if self.check_cuts_and_warn():
            return
        self.gpr_active = True
        self.show_geo_var = False
        self.fibo_active = False
        self.compare_active = False
        self.start_gpr_zigzag_scan()
        self.invalidate_render_cache()
        self.update_button_states()
        self._update_target_bg(self.t1, None)
        self._update_target_bg(self.t2, None)
        self.monitor.redraw()

    def compare_click(self, *args):
        if self.check_cuts_and_warn():
            return
        self.compare_active = not self.compare_active
        if self.compare_active:
            self.show_geo_var = False
            self.fibo_active = False
            self.gpr_active = False
            self.scanning = False
            self.transition_step = 0
            self.gpr_fibo_skeleton_visible = False
            self.calculate_geophysics_heatmap()
        else:
            self.show_geo_var = True
            self.calculate_geophysics_heatmap()
        self.invalidate_render_cache()
        self.update_button_states()
        self._update_target_bg(self.t1, None)
        self._update_target_bg(self.t2, None)
        self.monitor.redraw()

    def update_button_states(self):
        self.btn_geo.is_active = self.show_geo_var
        self.btn_fibo.is_active = self.fibo_active
        self.btn_gpr.is_active = self.gpr_active
        self.btn_compare.is_active = self.compare_active

    def deep_click(self, *args):
        self.show_depth_overlay = not self.show_depth_overlay
        self.update_target_boxes()
        self.invalidate_render_cache()
        self.monitor.redraw()

    def plus_click(self, *args):
        if self.heatmap_data is None:
            self.show_popup("Expansion", "Please run scan first.")
            return
        if self.expand_neg_count > 0:
            self.expand_neg_count -= 1
        else:
            if self.expand_pos_count < 10:
                self.expand_pos_count += 1
            else:
                self.show_popup("Expansion", "Maximum 10 expansion steps.")
                return
        self.expansion_level = self.expand_pos_count - self.expand_neg_count
        self.update_plus_minus_labels()
        self.invalidate_render_cache()
        self.monitor.redraw()

    def minus_click(self, *args):
        if self.heatmap_data is None:
            self.show_popup("Expansion", "Please run scan first.")
            return
        if self.expand_pos_count > 0:
            self.expand_pos_count -= 1
        else:
            if self.expand_neg_count < 10:
                self.expand_neg_count += 1
            else:
                self.show_popup("Expansion", "Maximum 10 contraction steps.")
                return
        self.expansion_level = self.expand_pos_count - self.expand_neg_count
        self.update_plus_minus_labels()
        self.invalidate_render_cache()
        self.monitor.redraw()

    def update_plus_minus_labels(self):
        neg_count_str = self.convert_digits(str(self.expand_neg_count))
        pos_count_str = self.convert_digits(str(self.expand_pos_count))
        self.btn_minus.text = f"— ({neg_count_str})"
        self.btn_plus.text = f"+ ({pos_count_str})"

    def calculate_target_depth(self, circ):
        val = circ.get("target_value", 15000.0)
        base_depth = 1.5 + (val / 10000.0) * 2.0
        return max(0.5, min(8.0, base_depth))

    def update_target_boxes(self):
        cuts = self.get_cut_segments()
        if cuts:
            seg_vertices = {
                "p1p2": {"P1", "P2"}, "p2p4": {"P2", "P4"}, "p4p3": {"P4", "P3"},
                "p3p1": {"P3", "P1"}, "p1p4": {"P1", "P4"}, "p2p3": {"P2", "P3"}
            }
            names_en = " and ".join(cuts)
            names_fa = " و ".join(cuts)
            common_vertex = None
            if len(cuts) >= 2:
                common = seg_vertices[cuts[0]]
                for c in cuts[1:]:
                    common = common.intersection(seg_vertices[c])
                if common:
                    common_vertex = list(common)[0]
            if self.lang == 'fa':
                warning_title = "[color=#FF3333][b]⚠ هشدار قطعی کابل[/b][/color]"
                if len(cuts) == 1:
                    msg = f"کابل {cuts[0]} قطع است"
                else:
                    msg = f"کابل‌های {names_fa} قطع هستند"
                    if common_vertex:
                        msg += f"\nو به احتمال زیاد {common_vertex} قطعی کابل دارد"
                self.t1.text = self.shape_text(f"{warning_title}\n{msg}")
                self.t2.text = self.shape_text(f"[color=#FF9900][b]اتصال فیزیکی پراپ‌ها را بررسی کنید[/b][/color]\nپراپ مشترک احتمالی: {common_vertex if common_vertex else 'نامشخص'}")
            else:
                warning_title = "[color=#FF3333][b]⚠ Cable Fault Warning[/b][/color]"
                if len(cuts) == 1:
                    msg = f"Cable {cuts[0]} is disconnected"
                else:
                    msg = f"Cables {names_en} are disconnected"
                    if common_vertex:
                        msg += f"\nMost likely {common_vertex} has a broken cable"
                self.t1.text = f"{warning_title}\n{msg}"
                self.t2.text = f"[color=#FF9900][b]Check physical probe connections[/b][/color]\nCommon Probe: {common_vertex if common_vertex else 'None'}"
            return
        self.t1.text = self.translate("Target 1:\nX=                         Y=\nDepth (H) = —")
        self.t2.text = self.translate("Target 2:\nX=                         Y=\nDepth (H) = —")
        if self.soil_contaminated or not self.detected_circles:
            return
        if self.compare_active:
            nx, ny = 140, 140
            grid_geo = self.heatmap_data["grid"] if self.heatmap_data else []
            vmin = self.heatmap_data["min"] if self.heatmap_data else 0.0
            vmax = self.heatmap_data["max"] if self.heatmap_data else 100000.0
            min_xr = self.min_point["x_ratio"] if self.min_point else 0.5
            min_yr = self.min_point["y_ratio"] if self.min_point else 0.5
            for idx, circ in enumerate(self.detected_circles[:2]):
                cx, cy = circ["center_x_ratio"], circ["center_y_ratio"]
                min_fib_val = float('inf')
                xf_local, yf_local = cx, cy
                if grid_geo:
                    for j in range(ny):
                        ry = j / (ny - 1) if ny > 1 else 0.5
                        for i in range(nx):
                            rx = i / (nx - 1) if nx > 1 else 0.5
                            if math.hypot(rx - cx, ry - cy) <= 0.20:
                                self.fibo_active = True
                                val_fib = self.compute_gpr_fibonacci_value(rx, ry, vmin, vmax, min_xr, min_yr)
                                self.fibo_active = False
                                if val_fib < min_fib_val:
                                    min_fib_val = val_fib
                                    xf_local, yf_local = rx, ry
                x_avg = (cx + cx + xf_local) / 3.0
                y_avg = (cy + cy + yf_local) / 3.0
                x_m = x_avg * self.width_val
                y_m = y_avg * self.length_val
                val = circ.get("target_value", 0.0)
                label = circ.get("label", "No Target")
                depth_text = "—"
                if self.show_depth_overlay:
                    depth_text = f"{self.calculate_target_depth(circ):.2f} m"
                translated_label = self.translate(label)
                if self.lang == 'fa':
                    x_m_str = self.convert_digits(f"{x_m:.2f}")
                    y_m_str = self.convert_digits(f"{y_m:.2f}")
                    val_str = self.convert_digits(f"{val:.0f}")
                    idx_str = self.convert_digits(str(idx+1))
                    depth_str = self.convert_digits(depth_text).replace("m", "متر")
                    raw_text = f"هدف {idx_str}:  [b][size=20sp]{translated_label}[/b][/size]      مقدار: {val_str}\nX = {x_m_str} متر        Y = {y_m_str} متر\nعمق (H) = {depth_str}"
                    target_text = self.shape_text(raw_text)
                else:
                    target_text = f"Target {idx+1}:  [b][size=20sp]{translated_label}[/size][/b]      Value: {val:.0f}\nX = {x_m:.2f} m        Y = {y_m:.2f} m\nDepth (H) = {depth_text}"
                
                if idx == 0:
                    self.t1.text = target_text
                elif idx == 1:
                    self.t2.text = target_text
        else:
            if len(self.detected_circles) >= 1:
                c1 = self.detected_circles[0]
                label1, val1 = c1.get("label", "No Target"), c1.get("target_value", 0.0)
                x1_m = c1.get("center_x_ratio", 0.5) * self.width_val
                y1_m = c1.get("center_y_ratio", 0.5) * self.length_val
                translated_label1 = self.translate(label1)
                
                if self.lang == 'fa':
                    depth1_text = f"{self.calculate_target_depth(c1):.2f} m" if self.show_depth_overlay else "—"
                    x1_str = self.convert_digits(f"{x1_m:.2f}")
                    y1_str = self.convert_digits(f"{y1_m:.2f}")
                    val1_str = self.convert_digits(f"{val1:.0f}")
                    depth1_str = self.convert_digits(depth1_text).replace("m", "متر")
                    raw_text = f"هدف ۱:  [b][size=20sp]{translated_label1}[/b][/size]      مقدار: {val1_str}\nX = {x1_str} متر        Y = {y1_str} متر\nعمق (H) = {depth1_str}"
                    self.t1.text = self.shape_text(raw_text)
                else:
                    depth1 = f"{self.calculate_target_depth(c1):.2f} m" if self.show_depth_overlay else "—"
                    self.t1.text = f"Target 1:  [b][size=20sp]{translated_label1}[/size][/b]      Value: {val1:.0f}\nX = {x1_m:.2f} m        Y = {y1_m:.2f} m\nDepth (H) = {depth1}"
                    
            if len(self.detected_circles) >= 2:
                c2 = self.detected_circles[1]
                label2, val2 = c2.get("label", "No Target"), c2.get("target_value", 0.0)
                x2_m = c2.get("center_x_ratio", 0.5) * self.width_val
                y2_m = c2.get("center_y_ratio", 0.5) * self.length_val
                translated_label2 = self.translate(label2)
                
                if self.lang == 'fa':
                    depth2_text = f"{self.calculate_target_depth(c2):.2f} m" if self.show_depth_overlay else "—"
                    x2_str = self.convert_digits(f"{x2_m:.2f}")
                    y2_str = self.convert_digits(f"{y2_m:.2f}")
                    val2_str = self.convert_digits(f"{val2:.0f}")
                    depth2_str = self.convert_digits(depth2_text).replace("m", "متر")
                    raw_text = f"هدف ۲:  [b][size=20sp]{translated_label2}[/b][/size]      مقدار: {val2_str}\nX = {x2_str} متر        Y = {y2_str} متر\nعمق (H) = {depth2_str}"
                    self.t2.text = self.shape_text(raw_text)
                else:
                    depth2 = f"{self.calculate_target_depth(c2):.2f} m" if self.show_depth_overlay else "—"
                    self.t2.text = f"Target 2:  [b][size=20sp]{translated_label2}[/size][/b]      Value: {val2:.0f}\nX = {x2_m:.2f} m        Y = {y2_m:.2f} m\nDepth (H) = {depth2}"

    def get_frequency_data(self, label):
        freqs = {
            "silver": {"range": "130 Hz - 140 Hz", "tx": "135.0 Hz", "rx": "134.9 Hz"},
            "gold": {"range": "240 Hz - 250 Hz", "tx": "245.0 Hz", "rx": "244.7 Hz"},
            "copper": {"range": "380 Hz - 390 Hz", "tx": "385.0 Hz", "rx": "384.6 Hz"},
            "brass": {"range": "450 Hz - 460 Hz", "tx": "455.0 Hz", "rx": "454.4 Hz"},
            "iron": {"range": "70 Hz - 80 Hz", "tx": "75.0 Hz", "rx": "74.1 Hz"},
            "water": {"range": "1.0 kHz - 1.5 kHz", "tx": "1.20 kHz", "rx": "1.15 kHz"},
            "Void": {"range": "10 Hz - 15 Hz", "tx": "12.0 Hz", "rx": "12.0 Hz"},
            "Small Void": {"range": "10 Hz - 15 Hz", "tx": "12.0 Hz", "rx": "12.0 Hz"},
            "Medium Void": {"range": "10 Hz - 15 Hz", "tx": "12.0 Hz", "rx": "12.0 Hz"},
            "Big Void": {"range": "10 Hz - 15 Hz", "tx": "12.0 Hz", "rx": "12.0 Hz"},
            "natural": {"range": "480 Hz - 520 Hz", "tx": "500.0 Hz", "rx": "499.8 Hz"}
        }
        return freqs.get(label, {
            "range": "140 Hz - 160 Hz",
            "tx": "150.0 Hz",
            "rx": "149.5 Hz"
        })

    def update_report_bg(self, instance, value):
        self.report_bg_rect.pos = self.report_container.pos
        self.report_bg_rect.size = self.report_container.size

    def show_report_popup(self, *args):
        if self.get_cut_segments():
            self.show_popup("Error", "Cannot generate report when probe is disconnected." if self.lang=='en' else "در حالت قطعی پراپ امکان گزارش‌گیری نیست.")
            return
        if not self.detected_circles:
            self.show_popup("Error", "Please run scan first.")
            return
            
        self.report_target_idx = 0
        self.report_container = FloatLayout()
        with self.report_container.canvas.before:
            Color(0.04, 0.04, 0.04, 1)
            self.report_bg_rect = Rectangle(pos=self.report_container.pos, size=self.report_container.size)
        self.report_container.bind(pos=self.update_report_bg, size=self.update_report_bg)
        
        self.report_nav_box = BoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
        self.btn_close_report = PlasticButton(text="Close" if self.lang=='en' else "بستن", btn_color=[0.8, 0.2, 0.2, 1], size_hint_x=0.5)
        self.btn_next_report = PlasticButton(text="Next Target" if self.lang=='en' else "تارگت بعدی", btn_color=[0.11, 0.51, 0.84, 1], size_hint_x=0.5)
        
        self.btn_close_report.bind(on_release=lambda x: self.report_popup.dismiss())
        self.btn_next_report.bind(on_release=self.toggle_report_target)
        
        self.report_nav_box.add_widget(self.btn_close_report)
        if len(self.detected_circles) > 1:
            self.report_nav_box.add_widget(self.btn_next_report)
            
        self.report_popup = Popup(
            title=self.translate("Work Report"),
            content=self.report_container,
            size_hint=(0.9, 0.72),
            auto_dismiss=False
        )
        self.build_report_layout()
        self.report_popup.open()

    def report_popup_close(self, instance):
        if hasattr(self, 'report_popup_dialog') and self.report_popup_dialog:
            self.report_popup_dialog.dismiss()

    def toggle_report_target(self, *args):
        self.report_target_idx = 1 - self.report_target_idx
        if self.report_target_idx == 0:
            self.btn_next_report.text = "تارگت بعدی" if self.lang == 'fa' else "Next Target"
        else:
            self.btn_next_report.text = "تارگت قبلی" if self.lang == 'fa' else "Prev Target"
        self.build_report_layout()

    def build_report_layout(self):
        self.report_container.clear_widgets()
        watermark = Label(
            text="Cornix\nWinner", font_size='48sp', bold=True,
            color=[0.6, 0.05, 0.15, 0.16], halign='center', valign='middle',
            size_hint=(1, 1), pos_hint={'x': 0, 'y': 0}
        )
        watermark.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        self.report_container.add_widget(watermark)
        
        content_box = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8), size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        
        from kivy.uix.scrollview import ScrollView
        sv = ScrollView(size_hint=(1, 0.85))
        grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        
        circ = self.detected_circles[self.report_target_idx]
        target_num = self.report_target_idx + 1
        material_trans = self.translate(circ["label"])
        
        x_m = circ["center_x_ratio"] * self.width_val
        y_m = circ["center_y_ratio"] * self.length_val
        depth_m = self.calculate_target_depth(circ)
        diameter_cm = circ["diameter_m"] * 100.0
        
        raw_vals = [self.safe_float(v) for v in self.entry_values.values() if v is not None and v != ""]
        if len(raw_vals) > 1:
            v_max = max(raw_vals)
            v_min = min(raw_vals)
            v_avg = sum(raw_vals) / len(raw_vals)
            asymmetry = (v_max - v_min) / max(1.0, v_avg)
            error_cm = int(asymmetry * 35.0 + 3.0)
            error_cm = max(3, min(90, error_cm))
        else:
            error_cm = 5
            
        ref = self.ref_soil_val
        if ref < 200:
            soil_type = "Very Wet / Muddy" if self.lang == 'en' else "بسیار مرطوب / گلی"
        elif ref < 600:
            soil_type = "Moist / Normal" if self.lang == 'en' else "مرطوب / نرمال"
        elif ref < 1500:
            soil_type = "Semi-Dry" if self.lang == 'en' else "نیمه خشک"
        else:
            soil_type = "Very Dry / Sandy" if self.lang == 'en' else "بسیار خشک / ماسه‌ای"
            
        contrast = abs(circ["target_value"] - ref) / max(1.0, ref) * 100.0
        contrast_str = f"{contrast:.1f}%"
        
        freq_info = self.get_frequency_data(circ["label"])
        tx_freq = freq_info["tx"]
        rx_freq = freq_info["rx"]
        freq_range = freq_info["range"]
        
        if self.lang == 'fa':
            target_name = self.convert_digits(str(target_num))
            mat_str = self.shape_text(material_trans)
            x_str = self.convert_digits(f"{x_m:.2f}")
            y_str = self.convert_digits(f"{y_m:.2f}")
            depth_str = self.convert_digits(f"{depth_m:.2f}")
            diam_str = self.convert_digits(f"{diameter_cm:.1f}")
            err_str = self.convert_digits(str(error_cm))
            ref_str = self.convert_digits(f"{ref:.0f}")
            contrast_farsi = self.convert_digits(contrast_str)
            soil_farsi = self.shape_text(soil_type)
            tx_freq = self.convert_digits(tx_freq)
            rx_freq = self.convert_digits(rx_freq)
            freq_range = self.convert_digits(freq_range)
            
            rows = [
                ("نام هدف (Target):", f"Target {target_name}"),
                ("جنس کالیبره‌شده (Material):", mat_str),
                ("مختصات افقی هندسی (X):", f"{x_str} متر"),
                ("مختصات عمودی هندسی (Y):", f"{y_str} متر"),
                ("عمق برآورد شده هدف (Deep):", f"{depth_str} متر"),
                ("قطر محدوده آلوده هدف:", f"{diam_str} سانتی‌متر"),
                ("تلرانس خطای نقطه‌زنی:", f"±{err_str} سانتی‌متر"),
                ("فرکانس ارسال (TX):", tx_freq),
                ("فرکانس دریافتی (RX):", rx_freq),
                ("محدوده فرکانس مجاز:", freq_range),
                ("مقاومت مرجع خاک:", f"{ref_str} اهم"),
                ("رطوبت و رسانایی زمین:", soil_farsi),
                ("شدت تضاد هادی هدف:", contrast_farsi)
            ]
        else:
            rows = [
                ("Target Name:", f"Target {target_num}"),
                ("Material:", material_trans),
                ("X Coordinate:", f"{x_m:.2f} m"),
                ("Y Coordinate:", f"{y_m:.2f} m"),
                ("Target Depth (Deep):", f"{depth_m:.2f} m"),
                ("Contamination Dia:", f"{diameter_cm:.1f} cm"),
                ("Error Tolerance:", f"±{error_cm} m"),
                ("Transmit Freq (TX):", tx_freq),
                ("Receive Freq (RX):", rx_freq),
                ("Frequency Range:", freq_range),
                ("Soil Ref Resistance:", f"{ref:.0f} Ohm"),
                ("Soil Type Estimate:", soil_type),
                ("Signal Contrast:", contrast_str)
            ]
            
        title_lbl = Label(
            text=f"[b]{self.translate('Target 1 Report') if target_num == 1 else self.translate('Target 2 Report')}[/b]", 
            markup=True, color=[1, 1, 1, 1], font_size='15sp', size_hint_y=None, height=dp(30), halign='center'
        )
        title_lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        content_box.add_widget(title_lbl)
        
        for k, v in rows:
            k_lbl = Label(
                text=f"[b]{k}[/b]", markup=True, color=[1, 1, 1, 1], font_size='13sp',
                size_hint_y=None, height=dp(25), halign='left', valign='middle', padding=(dp(15), 0)
            )
            k_lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            
            v_lbl = Label(
                text=f"[b]{v}[/b]", markup=True, color=[0.95, 0.95, 0.1, 1], font_size='11sp',
                size_hint_y=None, height=dp(25), halign='right', valign='middle', padding=(dp(15), 0)
            )
            v_lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            
            grid.add_widget(k_lbl)
            grid.add_widget(v_lbl)
            
        sv.add_widget(grid)
        content_box.add_widget(sv)
        
        if self.report_nav_box.parent:
            self.report_nav_box.parent.remove_widget(self.report_nav_box)
            
        content_box.add_widget(self.report_nav_box)
        self.report_container.add_widget(content_box)

    def refresh_scan(self, *args):
        try:
            if self.check_cuts_and_warn():
                return
            self.loaded_scan_name = ""
            
            self.width_val = self.ui_width_val
            self.length_val = self.ui_length_val
            self.ref_soil_val = self.ui_ref_soil_val
            self.entry_values = self.ui_entry_values.copy()
            
            self.push_state()
            self.expand_pos_count = 0
            self.expand_neg_count = 0
            self.expansion_level = 0
            self.signal_correction_level = 0
            self.gpr_fibo_skeleton_visible = False
            self.update_plus_minus_labels()
            self.calculate_geophysics_heatmap()
            self.invalidate_render_cache()
            if self.gpr_active or self.fibo_active:
                self.start_gpr_zigzag_scan()
            else:
                self.monitor.redraw()
        except Exception as e:
            self.show_popup("Error", str(e))

    def reset_all(self, *args):
        self.push_state()
        self.ui_width_val = 5.0
        self.ui_length_val = 5.0
        self.ui_ref_soil_val = 600.0
        self.width_val = 5.0
        self.length_val = 5.0
        self.ref_soil_val = 600.0
        self.in_w.value_text = "5.0 M"
        self.in_l.value_text = "5.0 M"
        self.in_ref.value_text = "600"
        self.chord_pull, self.void_pull = 35.0, 50.0
        for k in self.edge_keys:
            self.ui_entry_values[k] = ""
            self.entry_values[k] = ""
            for seg_btn in self.segs:
                if seg_btn.label_text.upper() == k.upper():
                    seg_btn.value_text = ""
        self.heatmap_data, self.detected_circles, self.warning_arrows = None, [], []
        self.soil_contaminated, self.center_red_focus_mode, self.show_depth_overlay = False, False, True
        self.gpr_active, self.scanning, self.scan_grid = False, False, None
        self.fibo_active = False
        self.compare_active = False
        self.show_geo_var = True
        self.sampled_points, self.final_min_points, self.transition_step = [], [], 0
        self.expand_pos_count, self.expand_neg_count, self.expansion_level = 0, 0, 0
        self.loaded_scan_name = ""
        self.gpr_fibo_skeleton_visible = False
        self.update_plus_minus_labels()
        self.update_button_states()
        self._update_target_bg(self.t1, None)
        self._update_target_bg(self.t2, None)
        self.update_target_boxes()
        self.invalidate_render_cache()
        self.push_state()
        self.monitor.redraw()

    def show_popup(self, title, text):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        translated_text = self.translate(text)
        lbl = Label(text=translated_text, halign='center', valign='middle', size_hint_y=0.7)
        lbl.bind(size=lambda s, v: setattr(lbl, 'text_size', v))
        content.add_widget(lbl)
        btn = PlasticButton(text=self.translate("Close"), btn_color=[0.8, 0.2, 0.2, 1], size_hint_y=0.3)
        popup = Popup(title=self.translate(title), content=content, size_hint=(0.85, 0.45))
        btn.bind(on_release=popup.dismiss)
        content.add_widget(btn)
        popup.open()

    def show_input_popup(self, title, hint, callback):
        from kivy.uix.textinput import TextInput
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        inp = TextInput(text="", placeholder_text=self.translate(hint), multiline=False, size_hint_y=0.4)
        content.add_widget(inp)
        btns = BoxLayout(spacing=5, size_hint_y=0.4)
        btn_ok = PlasticButton(text="OK", btn_color=[0.1, 0.6, 0.2, 1])
        btn_cancel = PlasticButton(text="Cancel", btn_color=[0.8, 0.2, 0.2, 1])
        btns.add_widget(btn_ok)
        btns.add_widget(btn_cancel)
        content.add_widget(btns)
        popup = Popup(title=self.translate(title), content=content, size_hint=(0.85, 0.45))
        
        def on_ok(*args):
            callback(inp.text)
            popup.dismiss()
            
        btn_ok.bind(on_release=on_ok)
        btn_cancel.bind(on_release=popup.dismiss)
        popup.open()

    def show_contamination_help(self, *args):
        msg_en = ("The scanned environment has very severe contamination, this contamination is either related to surface metals or to the soil properties of this spot. To be sure, please first remove the surface metals from the ground with a loop metal detector and scan again, if the problem is not resolved, this environment is dirty.")
        msg_fa = ("محیط اسکن شده دارای آلودگی بسیار شدید است، این آلودگی یا مربوط به فلزات سطحی یا به ویژگی‌های خاک این نقطه مربوط می‌شود. برای اطمینان لطفا ابتدا فلزات سطحی را توسط فلزیاب لوپی از زمین خارج کرده و مجددا اسکن کنید. در صورت عدم رفع مشکل، این محیط آلوده است.")
        self.show_popup("Contamination Warning" if self.lang=='en' else "هشدار آلودگی خاک", msg_fa if self.lang=='fa' else msg_en)

    def undo_click(self, *args):
        if self.history_index > 0:
            self.history_index -= 1
            self.load_state(self.history[self.history_index])
            self.monitor.redraw()
        else:
            self.show_popup("Info", "No more undo steps available." if self.lang=='en' else "مرحله قبلی وجود ندارد.")

    def redo_click(self, *args):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.load_state(self.history[self.history_index])
            self.monitor.redraw()
        else:
            self.show_popup("Info", "No more redo steps available." if self.lang=='en' else "مرحله بعدی وجود ندارد.")

    def push_state(self):
        state = {
            "ui_entry_values": self.ui_entry_values.copy(),
            "ui_width_val": self.ui_width_val,
            "ui_length_val": self.ui_length_val,
            "ui_ref_soil_val": self.ui_ref_soil_val,
            "expand_pos_count": self.expand_pos_count,
            "expand_neg_count": self.expand_neg_count,
            "expansion_level": self.expansion_level,
            "show_geo_var": self.show_geo_var,
            "fibo_active": self.fibo_active,
            "gpr_active": self.gpr_active,
            "compare_active": self.compare_active,
            "loaded_scan_name": self.loaded_scan_name
        }
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        self.history.append(state)
        if len(self.history) > 30:
            self.history.pop(0)
        self.history_index = len(self.history) - 1

    def load_state(self, state):
        self.ui_entry_values = state["ui_entry_values"].copy()
        self.entry_values = self.ui_entry_values.copy()
        self.ui_width_val = state["ui_width_val"]
        self.ui_length_val = state["ui_length_val"]
        self.ui_ref_soil_val = state["ui_ref_soil_val"]
        self.width_val = self.ui_width_val
        self.length_val = self.ui_length_val
        self.ref_soil_val = self.ui_ref_soil_val
        
        self.in_w.value_text = f"{self.width_val} M"
        self.in_l.value_text = f"{self.length_val} M"
        self.in_ref.value_text = f"{self.ref_soil_val:.0f}"
        
        for k in self.edge_keys:
            v = self.ui_entry_values.get(k, "")
            for seg_btn in self.segs:
                if seg_btn.label_text.upper() == k.upper():
                    seg_btn.value_text = v
                    
        self.expand_pos_count = state["expand_pos_count"]
        self.expand_neg_count = state["expand_neg_count"]
        self.expansion_level = state["expansion_level"]
        self.update_plus_minus_labels()
        
        self.show_geo_var = state["show_geo_var"]
        self.fibo_active = state["fibo_active"]
        self.gpr_active = state["gpr_active"]
        self.compare_active = state["compare_active"]
        self.loaded_scan_name = state["loaded_scan_name"]
        self.update_button_states()

    def get_storage_root(self, is_internal):
        try:
            if os.path.exists('/storage/emulated/0'):
                if is_internal:
                    return '/storage/emulated/0'
                else:
                    if os.path.exists('/storage'):
                        try:
                            for item in os.listdir('/storage'):
                                if item not in ['emulated', 'self', 'root']:
                                    ext_path = os.path.join('/storage', item)
                                    if os.path.isdir(ext_path):
                                        return ext_path
                        except Exception:
                            pass
                        return '/storage'
                    return '/storage/emulated/0'
            else:
                return os.path.expanduser("~")
        except Exception:
            return os.path.expanduser("~")

    def sanitize_filename(self, filename):
        illegal_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        if not filename.strip():
            filename = f"scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return filename

    def ask_filename_and_save(self, is_internal, save_type):
        default_name = f"scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        title = self.translate("Enter Filename")
        
        def on_name_entered(typed_name):
            sanitized = self.sanitize_filename(typed_name)
            if save_type == "json":
                self.execute_save_memory(is_internal, sanitized)
            elif save_type == "png":
                self.execute_save_jpeg(is_internal, sanitized)
                
        VirtualKeyboardPopup(title=title, callback=on_name_entered, default_text=default_name).open()

    def save_memory_click(self, *args):
        if self.get_cut_segments():
            self.show_popup("Error", "Cannot save scan when probe is disconnected." if self.lang=='en' else "در حالت قطعی پراپ امکان ذخیره‌سازی نیست.")
            return
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text=self.translate("Save Memory to:"), size_hint_y=0.3, font_size='14sp', bold=True)
        content.add_widget(lbl)
        
        btn_internal = PlasticButton(text=self.translate("Internal Storage"), btn_color=[0.1, 0.5, 0.8, 1], size_hint_y=0.35)
        btn_cancel = PlasticButton(text=self.translate("Cancel"), btn_color=[0.8, 0.2, 0.2, 1], size_hint_y=0.35)
        
        content.add_widget(btn_internal)
        content.add_widget(btn_cancel)
        
        popup_loc = Popup(title=self.translate("Save Memory"), content=content, size_hint=(0.85, 0.4))
        
        def choose_internal(*args):
            popup_loc.dismiss()
            self.ask_filename_and_save(is_internal=True, save_type="json")
            
        btn_internal.bind(on_release=choose_internal)
        btn_cancel.bind(on_release=popup_loc.dismiss)
        popup_loc.open()

    def execute_save_memory(self, is_internal, filename):
        if not filename.endswith(".json"):
            filename += ".json"
            
        state = {
            "width": str(self.ui_width_val), 
            "height": str(self.ui_length_val),
            "ref_soil": str(self.ui_ref_soil_val),
            "expand_pos": self.expand_pos_count, 
            "expand_neg": self.expand_neg_count, 
            "expansion_level": self.expansion_level,
            "entries": self.ui_entry_values.copy()
        }
        
        try:
            root = self.get_storage_root(is_internal)
            folder = os.path.join(root, "Cornix Winner Scan")
            os.makedirs(folder, exist_ok=True)
            filepath = os.path.join(folder, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=4, ensure_ascii=False)
                
            title = "Success"
            msg = f"Scan saved successfully to:\n{filepath}"
            self.show_popup(title, msg)
        except Exception as e:
            try:
                fallback_folder = os.path.join(self.user_data_dir, "Cornix Winner Scan")
                os.makedirs(fallback_folder, exist_ok=True)
                filepath = os.path.join(fallback_folder, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(state, f, indent=4, ensure_ascii=False)
                    
                title = "Success (Fallback)"
                msg = f"Public write failed. Saved to App safe storage:"
                self.show_popup(title, f"{msg}\n{filepath}")
            except Exception as e2:
                title = "Error"
                self.show_popup(title, f"Could not save file:\n{str(e2)}")

    def recall_memory_click(self, *args):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text=self.translate("Recall Memory"), size_hint_y=0.3, font_size='14sp', bold=True)
        content.add_widget(lbl)
        
        btn_internal = PlasticButton(text=self.translate("Internal Storage"), btn_color=[0.1, 0.5, 0.8, 1], size_hint_y=0.35)
        btn_cancel = PlasticButton(text=self.translate("Cancel"), btn_color=[0.8, 0.2, 0.2, 1], size_hint_y=0.35)
        
        content.add_widget(btn_internal)
        content.add_widget(btn_cancel)
        
        popup_loc = Popup(title=self.translate("Recall Memory"), content=content, size_hint=(0.85, 0.4))
        
        def choose_internal(*args):
            popup_loc.dismiss()
            self.recall_memory_with_location(is_internal=True)
            
        btn_internal.bind(on_release=choose_internal)
        btn_cancel.bind(on_release=popup_loc.dismiss)
        popup_loc.open()

    def recall_memory_with_location(self, is_internal):
        target_dir = ""
        try:
            root_dir = self.get_storage_root(is_internal)
            target_dir = os.path.join(root_dir, "Cornix Winner Scan")
        except Exception:
            pass
            
        valid_dir = False
        try:
            if target_dir and os.path.exists(target_dir) and os.listdir(target_dir):
                valid_dir = True
        except Exception:
            pass
            
        if not valid_dir:
            fallback_dir = os.path.join(self.user_data_dir, "Cornix Winner Scan")
            try:
                if os.path.exists(fallback_dir) and os.listdir(fallback_dir):
                    target_dir = fallback_dir
                    valid_dir = True
            except Exception:
                pass
                
        if not valid_dir:
            self.show_popup("Recall", "No saved scans found")
            return
            
        try:
            files = [f for f in os.listdir(target_dir) if f.endswith(".json")]
        except Exception as e:
            self.show_popup("Error", "Could not read storage directory due to permission limits.")
            return
            
        if not files:
            self.show_popup("Recall", "No json files found")
            return

        self.recall_files_list = files
        self.recall_target_dir = target_dir
        self.current_search_query = ""
        content = BoxLayout(orientation='vertical', padding=10, spacing=5)
        
        search_row = BoxLayout(spacing=dp(5), size_hint_y=0.15)
        self.btn_search_trigger = PlasticButton(text=self.translate("Search: [Click to type]"), btn_color=[0.2, 0.4, 0.4, 1])
        btn_clear_search = PlasticButton(text="X", btn_color=[0.7, 0.2, 0.2, 1], size_hint_x=0.2)
        search_row.add_widget(self.btn_search_trigger)
        search_row.add_widget(btn_clear_search)
        content.add_widget(search_row)

        from kivy.uix.scrollview import ScrollView
        sv = ScrollView(size_hint_y=0.7)
        self.file_list_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.file_list_grid.bind(minimum_height=self.file_list_grid.setter('height'))
        sv.add_widget(self.file_list_grid)
        content.add_widget(sv)

        btn_close = PlasticButton(text=self.translate("Cancel"), btn_color=[0.8, 0.2, 0.2, 1], size_hint_y=0.15)
        content.add_widget(btn_close)
        popup = Popup(title=self.translate("Select Scan File"), content=content, size_hint=(0.85, 0.8))
        btn_close.bind(on_release=popup.dismiss)

        def load_and_dismiss(filename):
            self.load_from_json(os.path.join(self.recall_target_dir, filename))
            popup.dismiss()

        def populate_file_list(query=""):
            self.file_list_grid.clear_widgets()
            filtered_files = []
            for f in self.recall_files_list:
                if not query or query.lower() in f.lower():
                    filtered_files.append(f)
                
            if not filtered_files:
                lbl_empty = Label(text=self.translate("No matches found"), size_hint_y=None, height=dp(40))
                self.file_list_grid.add_widget(lbl_empty)
                return

            for f in filtered_files:
                btn = PlasticButton(text=f, btn_color=[0.3, 0.3, 0.3, 1], size_hint_y=None, height=dp(40))
                btn.bind(on_release=lambda instance, filename=f: load_and_dismiss(filename))
                self.file_list_grid.add_widget(btn)

        def trigger_search_keyboard(*args):
            def on_search_query_submitted(query):
                self.current_search_query = query
                self.btn_search_trigger.text = self.translate("Search: [Click to type]") if not query else f"{self.translate('Search:')} {query}"
                populate_file_list(query)
            
            VirtualKeyboardPopup(
                title=self.translate("Type query / متن جستجو را وارد کنید"),
                callback=on_search_query_submitted,
                default_text=self.current_search_query
            ).open()

        def clear_search_query(*args):
            self.current_search_query = ""
            self.btn_search_trigger.text = self.translate("Search: [Click to type]")
            populate_file_list("")

        self.btn_search_trigger.bind(on_release=trigger_search_keyboard)
        btn_clear_search.bind(on_release=clear_search_query)
        populate_file_list("")
        popup.open()

    def load_from_json(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.ui_width_val = float(data.get("width", "5.0"))
            self.ui_length_val = float(data.get("height", "5.0"))
            self.ui_ref_soil_val = float(data.get("ref_soil", "600.0"))
            self.width_val = self.ui_width_val
            self.length_val = self.ui_length_val
            self.ref_soil_val = self.ui_ref_soil_val
            self.in_w.value_text = f"{self.width_val} M"
            self.in_l.value_text = f"{self.length_val} M"
            self.in_ref.value_text = f"{self.ref_soil_val:.0f}"
            entries = data.get("entries", {})
            for k in self.edge_keys:
                v = entries.get(k, "")
                self.ui_entry_values[k] = v
                self.entry_values[k] = v
                for seg_btn in self.segs:
                    if seg_btn.label_text.upper() == k.upper():
                        seg_btn.value_text = v
            self.loaded_scan_name = os.path.basename(filepath)
            self.push_state()
            self.invalidate_render_cache()
            self.calculate_geophysics_heatmap()
            self.monitor.redraw()
            self.show_popup("Success", "Scan recalled successfully!")
        except Exception as e:
            self.show_popup("Error", f"Failed to load scan:\n{str(e)}")

    def save_jpeg_click(self, *args):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text=self.translate("Save Image to:"), size_hint_y=0.3, font_size='14sp', bold=True)
        content.add_widget(lbl)
        
        btn_internal = PlasticButton(text=self.translate("Internal Storage"), btn_color=[0.1, 0.5, 0.8, 1], size_hint_y=0.35)
        btn_cancel = PlasticButton(text=self.translate("Cancel"), btn_color=[0.8, 0.2, 0.2, 1], size_hint_y=0.35)
        
        content.add_widget(btn_internal)
        content.add_widget(btn_cancel)
        
        popup_loc = Popup(title=self.translate("Save Image"), content=content, size_hint=(0.85, 0.4))
        
        def choose_internal(*args):
            popup_loc.dismiss()
            self.ask_filename_and_save(is_internal=True, save_type="png")
            
        btn_internal.bind(on_release=choose_internal)
        btn_cancel.bind(on_release=popup_loc.dismiss)
        popup_loc.open()

    def execute_save_jpeg(self, is_internal, filename):
        if not filename.endswith(".png"):
            filename += ".png"
            
        try:
            root = self.get_storage_root(is_internal)
            folder = os.path.join(root, "Cornix Winner")
            os.makedirs(folder, exist_ok=True)
            filepath = os.path.join(folder, filename)
            self.monitor.export_to_png(filepath)
            title = "Success"
            msg = f"Screenshot saved successfully to:\n{filepath}"
            self.show_popup(title, msg)
        except Exception as e:
            try:
                fallback_folder = os.path.join(self.user_data_dir, "Cornix Winner")
                os.makedirs(fallback_folder, exist_ok=True)
                filepath = os.path.join(fallback_folder, filename)
                self.monitor.export_to_png(filepath)
                title = "Success (Fallback)"
                msg = f"Public write failed. Saved to App safe storage:"
                self.show_popup(title, f"{msg}\n{filepath}")
            except Exception as e2:
                title = "Error"
                self.show_popup(title, f"Could not save file:\n{str(e2)}")


if __name__ == '__main__':
    MainApp().run()