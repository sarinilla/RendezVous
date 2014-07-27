import os
import math
import warnings

from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.properties import BooleanProperty, ListProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.actionbar import ActionBar
from kivy.uix.label import Label
from kivy.uix.popup import Popup

from rendezvous import FileReader, GameSettings


class BackgroundCategory(object):

    """Set of available backgrounds with an arbitrary order and price.

    Attributes:
      name -- human-readable category name
      price -- number of kisses to purchase each background
      backgrounds -- [['filename', index]]

    """

    def __init__(self, name, price=5):
        self.name = name
        self.price = price
        self.backgrounds = []

        

    def __str__(self):
        return self.name

    def add(self, filename, index):
        self.backgrounds.append((filename, index))

    def __iter__(self):
        return iter(self.backgrounds)

    def __len__(self):
        return len(self.backgrounds)


class BackgroundDisplay(BoxLayout):

    """Display one available background image."""

    screen = ObjectProperty()
    filename = StringProperty()
    index = NumericProperty()
    popup = ObjectProperty()
    label = BooleanProperty(True)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            App.get_running_app().purchase_background(self.filename,
                                                      self.index, self.popup)
            return True
        return super(BackgroundDisplay, self).on_touch_up(touch)

    def get_name(self):
        try:
            if int(self.filename[:3]) == self.index:
                return self.filename[3:-4].strip()
        except ValueError: pass
        return self.filename[:-4]

    def get_color(self, *args):
        if self.filename == GameSettings.BACKGROUND:
            return (0, 0, 1, 1)
        elif self.filename in self.screen.purchased:
                return (1, 1, 1, 1)
        return (0, 0, 0, 0)


class CategoryIcon(BoxLayout):

    """Show the category name plus a selection of icons."""

    screen = ObjectProperty()
    category = ObjectProperty()

    def __init__(self, **kwargs):
        super(CategoryIcon, self).__init__(**kwargs)
        label = Label(text=self.category.name,
                              halign="left", valign="middle",
                              size_hint=(3, 1))
        label.bind(size=label.setter('text_size'))
        self.add_widget(label)
        for filename, index in self.category.backgrounds[:3]:
            self.add_widget(BackgroundDisplay(screen=self.screen,
                                              filename=filename,
                                              index=index,
                                              label=False))
        for i in range(3 - len(self.category.backgrounds)):
            self.add_widget(Widget())
        self.bind(size=self._set_pad)

    def _set_pad(self, *args):
        self.padding = self.size[0] * 0.05, self.size[1] * 0.01

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self._show_category()
            return True
        return super(CategoryIcon, self).on_touch_up(touch)

    def _show_category(self):
        popup = Popup(title="%s Backgrounds" % self.category.name)
        self.scroller = ScrollView(do_scroll_x=False)
        self.grid = GridLayout(cols=3, size_hint_y=None)
        for filename, index in self.category.backgrounds:
            self.grid.add_widget(BackgroundDisplay(screen=self.screen,
                                                   filename=filename,
                                                   index=index,
                                                   popup=popup))
        for i in range(3 - len(self.category.backgrounds)):
            self.grid.add_widget(Widget())
        self.scroller.bind(size=self._resize)
        self.scroller.add_widget(self.grid)
        popup.add_widget(self.scroller)
        popup.open()

    def _resize(self, *args):
        rows = math.ceil(len(self.category.backgrounds) / 3)
        self.grid.size = (self.scroller.size[0],
                          rows * self.scroller.size[0] / 3)
        

class BackgroundCategoryDisplay(Screen):

    """Maintain a list of available and purchased backgrounds for display.

    Attributes:
      available -- list of BackgroundCategory objects
      purchased -- list of purchased filenames

    """

    purchased = ListProperty()

    def __init__(self, player_file=None, **kwargs):
        Screen.__init__(self, **kwargs)        
        self.purchased = []
        if player_file is None:
            self._purchased_file = os.path.join("player", "backgrounds.txt")
        else: self._purchased_file = player_file
        self._read_purchased()
        self.purchased_cat = BackgroundCategory('Purchased')
        
        self.categories = []
        self._available_file = os.path.join("data", "Backgrounds.txt")
        self._read_available()

        layout = BoxLayout(orientation="vertical")
        layout.add_widget(ActionBar(size_hint=(1, .125)))
        scroller = ScrollView(do_scroll_x=False)
        self.grid = GridLayout(cols=1, size_hint_y=None)
        self.grid.add_widget(CategoryIcon(screen=self,
                                          category=self.purchased_cat))
        self.bind(size=self._resize_grid)
        for cat in self.categories:
            self.grid.add_widget(CategoryIcon(screen=self,
                                              category=cat))
        scroller.add_widget(self.grid)
        layout.add_widget(scroller)
        self.add_widget(layout)

    def _resize_grid(self, *args):
        self.grid.height = self.width / 6 * (1 + len(self.categories))

    def __getitem__(self, key):
        for cat in self.categories:
            if cat.name.upper() == key.upper():
                return cat
        raise KeyError('Invalid background category: %s' % key)

    def _read_available(self):
        current_category = None
        for tag, value in FileReader(self._available_file):
            
            if tag == 'CATEGORY':
                try:
                    current_category = self[value]
                except KeyError:
                    current_category = BackgroundCategory(value)
                    self.categories.append(current_category)
                continue

            try:
                index = int(tag)
            except ValueError:
                warnings.warn("Invalid background index: %s" % tag)
                continue

            filename = self._find_file(index, value)
            if filename is None:
                warnings.warn("Background file not found: [%s]%s"
                              % (tag, value))
            else:
                current_category.add(filename, index)
                if filename in self.purchased:
                    self.purchased_cat.add(filename, index)

    def _find_file(self, index, file):
        path = os.path.join("data", "backgrounds")
        for filename in (os.path.join(path, "%03d%s.png" % (index, file)),
                         os.path.join(path, "%03d%s" % (index, file)),
                         os.path.join(path, "%03d %s.png" % (index, file)),
                         os.path.join(path, "%03d %s" % (index, file)),
                         os.path.join(path, "%s.png" % file),
                         os.path.join(path, file),
                         file):                         
            if os.path.isfile(filename):
                return os.path.basename(filename)
        return None

    def _read_purchased(self):
        if not os.path.isfile(self._purchased_file):
            self.purchased = [GameSettings.BACKGROUND]
            return
        f = open(self._purchased_file, 'r')
        for filename in f.readlines():
            self.purchased.append(filename.strip())
        f.close()

    def purchase(self, filename, index):
        self.purchased.append(filename)
        self.purchased_cat.add(filename, index)
        f = open(self._purchased_file, 'w')
        for filename in self.purchased:
            f.write('%s\n' % filename)
        f.close()
        
        
