"""Simple Calendar - month view, tap a day to add or delete events.
Kivy app; events are saved to events.json in the app's private storage."""
import calendar
import json
import os
from datetime import date

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

BG = (0.965, 0.969, 0.961, 1)
INK = (0.086, 0.125, 0.108, 1)
MUT = (0.42, 0.46, 0.44, 1)
HEAD = (0.09, 0.188, 0.169, 1)
ACC = (0.184, 0.42, 0.31, 1)
SOFT = (0.875, 0.918, 0.875, 1)
WHITE = (1, 1, 1, 1)
DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def flat_button(text, bg, fg=WHITE, **kw):
    return Button(text=text, background_normal="", background_color=bg, color=fg, **kw)


class CalendarApp(App):
    title = "Calendar"

    def build(self):
        Window.clearcolor = BG
        self.today = date.today()
        self.year, self.month = self.today.year, self.today.month
        self.path = os.path.join(self.user_data_dir, "events.json")
        self.events = self.load()

        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))
        head = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(6))
        head.add_widget(flat_button("<", HEAD, size_hint_x=None, width=dp(56),
                                    on_release=lambda *_: self.shift(-1)))
        self.title_lbl = Label(font_size=dp(20), bold=True, color=INK)
        head.add_widget(self.title_lbl)
        head.add_widget(flat_button(">", HEAD, size_hint_x=None, width=dp(56),
                                    on_release=lambda *_: self.shift(1)))
        root.add_widget(head)

        names = GridLayout(cols=7, size_hint_y=None, height=dp(28))
        for n in DAYS:
            names.add_widget(Label(text=n, color=MUT, font_size=dp(13)))
        root.add_widget(names)

        self.grid = GridLayout(cols=7, rows=6, spacing=dp(3))
        root.add_widget(self.grid)
        root.add_widget(flat_button("Today", ACC, size_hint_y=None, height=dp(48),
                                    on_release=lambda *_: self.go_today()))
        self.render()
        return root

    # ---- storage ----
    def load(self):
        try:
            with open(self.path, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return {}

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as fh:
                json.dump(self.events, fh, ensure_ascii=False)
        except OSError:
            pass

    # ---- month view ----
    def shift(self, delta):
        m = self.month - 1 + delta
        self.year += m // 12
        self.month = m % 12 + 1
        self.render()

    def go_today(self):
        self.year, self.month = self.today.year, self.today.month
        self.render()

    def render(self):
        self.title_lbl.text = f"{calendar.month_name[self.month]} {self.year}"
        self.grid.clear_widgets()
        weeks = calendar.Calendar(firstweekday=6).monthdayscalendar(self.year, self.month)
        weeks += [[0] * 7] * (6 - len(weeks))
        for week in weeks:
            for day in week:
                if not day:
                    self.grid.add_widget(Label())
                    continue
                d = date(self.year, self.month, day)
                has = bool(self.events.get(d.isoformat()))
                is_today = d == self.today
                bg = ACC if is_today else (SOFT if has else WHITE)
                fg = WHITE if is_today else INK
                text = f"{day}\n•" if has else str(day)
                self.grid.add_widget(flat_button(
                    text, bg, fg, on_release=lambda _b, d=d: self.open_day(d)))

    # ---- day dialog ----
    def open_day(self, d):
        key = d.isoformat()
        box = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(8))
        lst = GridLayout(cols=1, size_hint_y=None, spacing=dp(4))
        lst.bind(minimum_height=lst.setter("height"))
        sv = ScrollView()
        sv.add_widget(lst)
        box.add_widget(sv)
        entry = TextInput(hint_text="New event", multiline=False,
                          size_hint_y=None, height=dp(44))
        box.add_widget(entry)

        def fill():
            lst.clear_widgets()
            items = self.events.get(key, [])
            if not items:
                lst.add_widget(Label(text="No events yet", color=(0.7, 0.7, 0.7, 1),
                                     size_hint_y=None, height=dp(40)))
            for i, text in enumerate(items):
                row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(4))
                lbl = Label(text=text, halign="left", valign="middle")
                lbl.bind(size=lambda w, s: setattr(w, "text_size", (s[0], s[1])))
                row.add_widget(lbl)
                row.add_widget(flat_button("X", (0.75, 0.22, 0.17, 1),
                                           size_hint_x=None, width=dp(44),
                                           on_release=lambda _b, i=i: remove(i)))
                lst.add_widget(row)

        def add(*_):
            text = entry.text.strip()
            if text:
                self.events.setdefault(key, []).append(text)
                entry.text = ""
                self.save()
                fill()
                self.render()

        def remove(i):
            self.events[key].pop(i)
            if not self.events[key]:
                del self.events[key]
            self.save()
            fill()
            self.render()

        entry.bind(on_text_validate=add)
        btns = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        btns.add_widget(flat_button("Add event", ACC, on_release=add))
        close = flat_button("Close", HEAD)
        btns.add_widget(close)
        box.add_widget(btns)
        fill()
        pop = Popup(title=d.strftime("%A, %B %d, %Y"), content=box, size_hint=(0.92, 0.7))
        close.bind(on_release=pop.dismiss)
        pop.open()


if __name__ == "__main__":
    CalendarApp().run()
