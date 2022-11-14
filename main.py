from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import *
from kivymd.uix.behaviors import *
from kivymd.toast import toast
from kivy.properties import *
from kivy.clock import Clock
import requests
import threading

current_user = ""

all_messages = []
all_messages_data = []

class Internet(object):
    def __init__(self):
        self.base_url = "https://bilal2008.pythonanywhere.com/"
        self.login_url = self.base_url+"login"
        self.get_messages_url = self.base_url+"get"
        self.send_url = self.base_url+"send"
        self.status_url = self.base_url+"status/"
        #return self.get(self.base_url)
    def post(self, url, data):
        return requests.post(url, data=data).text
    def get(self, url):
        return requests.get(url).text
    def login(self, username, password):
        answer = self.post(self.login_url, {"username": username, "password": password})
        if answer == "False":
            return False
        return True
    def get_messages(self, me, person):
        answer = self.post(self.get_messages_url, {"from": me, "person": person})
        return eval(answer)
    def get_status(self, name):
        return self.get(self.status_url+name)
    def get_accounts(self):
        answer = eval(self.get(self.base_url))
        ac = answer["accounts"]
        st = answer["status"]
        a = []
        for i in ac:
            s = (st[i["name"]] == "green")
            a.append([i["name"], s])
        return a
    def send(self, msg, to):
        global current_user
        self.post(self.send_url, {"from": current_user, "to": to, "msg": msg})

class YourMessage(MDScreen, RectangularRippleBehavior, DeclarativeBehavior):
    text = StringProperty("Message")

class NewMessage(MDScreen, RectangularRippleBehavior, DeclarativeBehavior):
    text = StringProperty("Message")
    person = StringProperty("Khalil")

class ChatItem(TwoLineIconListItem):
    """Chat list item (cli)"""

class HomeScreen(MDScreen):
    """Home Screen"""

class ListScreen(MDScreen):
    all_other_users = ListProperty()
    def on_enter(self, *args, **kwargs):
        global current_user
        for i in self.all_other_users:
            self.ids.chat_list.remove_widget(i)
        self.all_other_users = []
        try:
            all_persons = Internet().get_accounts()
        except:
            toast("No Internet Connection!")
            return "error"
        all_persons.remove([current_user, 1])
        self.all_other_users = []
        for i in all_persons:
            item = ChatItem(text=i[0], secondary_text="Online" if i[1] else "Offline")
            self.all_other_users.append(item)
            self.ids.chat_list.add_widget(item)
        self.clock = Clock.schedule_interval(lambda x: threading.Thread(target=self.check_status_for_all).start(), 2)
    def check_status_for_all(self):
        global current_user
        try:
            all_persons = Internet().get_accounts()
        except:
            toast("No Internet Connection!")
            return "error"
        all_persons.remove([current_user, 1])
        for x in all_persons:
            for y in self.all_other_users:
                if x[0] == y.text:
                    if ("Online" if x[1] else "Offline") == y.secondary_text:
                        break
                    else:
                        y.secondary_text = ("Online" if x[1] else "Offline")
                        break
    def on_leave(self, *args, **kwargs):
        self.clock.cancel()

class ChatScreen(MDScreen):
    status ="free"
    chatter = StringProperty("")
    def back(self, m):
        m.current = "list"
    def on_enter(self, *args, **kwargs):
        threading.Thread(target=self.check_status).start()
        threading.Thread(target=self.check_every_thing).start()
        self.clock = Clock.schedule_interval(lambda x: threading.Thread(target=self.check_every_thing).start(), 2)
        self.clock_ = Clock.schedule_interval(lambda x: self.update(), 1)
        self._clock_ = Clock.schedule_interval(lambda x: threading.Thread(target=self.check_status).start(), 2)
    def on_leave(self, *args, **kwargs):
        self.clock.cancel()
        self.clock_.cancel()
        self._clock_.cancel()
        self.ids.spinner.active = True
    def check_status(self):
        try:
            a = Internet().get_status(self.chatter)
        except:
            toast("No Internet Connection!")
            return "error"
        if a != self.ids.title_bar.c:
            self.ids.title_bar.c = a
            self.ids.title_bar.md_bg_color = a
    def check_every_thing(self):
        if self.status != "free":
            return "al klaar"
        global all_messages_data, current_user
        self.status = "checking"
        try:
            a = Internet().get_messages(current_user, self.chatter)
        except:
            toast("No Internet Connection!")
            return "error"
        if a == all_messages_data:
            self.status = "free"
            self.ids.spinner.active = False
            return "Goeie"
        self.status = "warning"
        self.fetch()
    def fetch(self):
        if self.status != "warning":
            return "warning"
        self.status = "busy"
        global all_messages_data, current_user, all_messages
        try:
            a = Internet().get_messages(current_user, self.chatter)
        except:
            toast("No Internet Connection!")
            return "error"
        all_messages_data = a
        self.status = "update"
    def update(self):
        if self.status != "update":
            return "i'm waiting"
        global all_messages, all_messages_data
        self.all_ = []
        for x in all_messages_data:
            if x["from"] == current_user:
                self.all_.append(YourMessage(text=x["msg"]))
            else:
                self.all_.append(NewMessage(text=x["msg"], person=x["from"]))
        self.clean()
        all_messages = self.all_
        self.refresh()
        self.status = "free"
    def refresh(self):
        global all_messages
        for i in all_messages[::-1]:
            self.ids.content.add_widget(i)
        self.ids.spinner.active = False
    def clean(self):
        global all_messages
        for i in all_messages:
            self.ids.content.remove_widget(i)
    def send(self, text):
        text = text.replace("\t", "    ")
        if text.replace(" ", "").replace("\n", "").replace("\t", "") == "":
            return False
        global all_messages, all_messages_data, current_user
        try:
            Internet().send(text, self.chatter)
        except:
            toast("No Internet Connection!")
            return "error"
        all_messages_data.append({"from": current_user, "to": self.chatter, "msg": text})
        self.clean()
        all_messages.append(YourMessage(text=text))
        self.refresh()

class Main(MDApp):
    def chat_with(self, name):
        self.chat_screen.chatter = name
        self.screen_manager.current = "chat"
    def set_name(self, name):
        global current_user
        current_user = name
    def get_name(self):
        global current_user
        return current_user
    def check_infos(self, username, password, username_widget, password_widget):
        try:
            a = Internet().login(username, password)
        except:
            toast("No Internet Connection!")
            return "error"
        if a:
            self.set_name(username)
            toast("Hallo "+self.get_name()+"!")
            self.screen_manager.current = "list"
            self.set_focus(self.chat_screen.ids.message)
            Internet().send(f"{self.get_name()} aan~~", "~~ALL")
        else:
            username_widget.error = True
            password_widget.error = True
            toast("Gebruikersnaam of wachtwoord is fout!")
            self.set_focus(username_widget)
        password_widget.text, username_widget.text = "", ""
    def set_focus(self, widget):
        widget.focus = True
    def on_pause(self, *args, **kwargs):
        try:
            Internet().send(f"{self.get_name()} uit~~", "~~ALL")
        except:
            toast("No Internet Connection!")
            return "error"
    def on_stop(self, *args, **kwargs):
        try:
            Internet().send(f"{self.get_name()} uit~~", "~~ALL")
        except:
            toast("No Internet Connection!")
            return "error"
    def build(self):
        self.title = "Mem-Chat"
        self.icon = "icon.png"
        self.theme_cls.primary_palette = "Purple"
        self.screen_manager = MDScreenManager()
        self.home_screen = HomeScreen(name="home")
        self.chat_screen = ChatScreen(name="chat")
        self.list_screen = ListScreen(name="list")
        self.screen_manager.add_widget(self.home_screen)
        self.screen_manager.add_widget(self.chat_screen)
        self.screen_manager.add_widget(self.list_screen)
        return self.screen_manager

if __name__ == '__main__':
    APP = Main()
    APP.run()