from kivy.properties import NumericProperty
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button


class NumericInput(TextInput):

    def insert_text(self, substring, from_undo=False):
        backup = self.text
        super(NumericInput, self).insert_text(substring, from_undo)
        try: int(self.text)
        except ValueError:
            self.text = backup


class SpinBox(BoxLayout):

    value = NumericProperty()
    minimum = NumericProperty()
    maximum = NumericProperty()

    def __init__(self, **kwargs):
        super(SpinBox, self).__init__(**kwargs)

        self._text_box = NumericInput(text=str(self.value),
                                      multiline=False,
                                      on_text_validate=self._from_text)
        self._up_button = Button(text="^", on_release=self._increment)
        self._down_button = Button(text="v", on_release=self._decrement)
        
        self.add_widget(self._text_box)
        layout = BoxLayout(orientation="vertical", size_hint=(.5, 1))
        layout.add_widget(self._up_button)
        layout.add_widget(self._down_button)
        self.add_widget(layout)

    def on_value(self, instance, value):
        if value < self.minimum:
            self.value = self.minimum
        elif value > self.maximum:
            self.value = self.maximum
        else:
            self._text_box.text = str(value)

    def _from_text(self, *args):
        self.value = int(self._text_box.text)

    def _increment(self, *args):
        self.value += 1

    def _decrement(self, *args):
        self.value -= 1


if __name__ == '__main__':
    from kivy.app import App
    app = App()
    app.root = SpinBox(minimum=-10, maximum=10)
    app.run()
