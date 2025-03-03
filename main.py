from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.text import LabelBase
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.progressbar import ProgressBar
from kivy.core.audio import SoundLoader
from kivy.uix.filechooser import FileChooserListView


import json
import os
from datetime import datetime
import re
import random
# 註冊繁體中文字體
LabelBase.register(name='NotoSerifCJKtc',
                   fn_regular=r'10_NotoSerifCJKtc\OTF\TraditionalChinese\NotoSerifCJKtc-Regular.otf')

class StudyHelperApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_file = "study_data.json"
        self.log_file = "study_log.json"
        self.plans = []  # 存儲學習計畫
        self.load_data()  # 載入資料
        self.current_time_label = None  
        self.text_color = (1, 0.5, 0.5, 1)
        self.remaining_time = 0
        self.started=False # 是否已經計時
        self.selected_music = None  
        self.music_player = None 

    def save_data(self):
        data = {"plans": self.plans}
        with open(self.data_file, "w") as file:
            json.dump(data, file)

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as file:
                try:
                    data = json.load(file)
                    self.plans = data.get("plans", [])
                except json.JSONDecodeError:
                    self.plans = []
                    self.save_data()
        else:
            self.plans = []
            self.save_data()

    def save_log(self, plan):
        log_file = "log.json"
        if not os.path.exists(log_file):
            log_data = {}
        else:
            with open(log_file, "r") as file:
                try:
                    log_data = json.load(file)
                except json.JSONDecodeError:
                    log_data = {}

        # 獲取今日日期
        today = datetime.now().strftime("%Y-%m-%d")

        # 更新LOG
        if plan["name"] not in log_data:
            log_data[plan["name"]] = []
        if today not in log_data[plan["name"]]:
            log_data[plan["name"]].append(today)

        # 保存LOG
        with open(log_file, "w") as file:
            json.dump(log_data, file, ensure_ascii=False, indent=4)

    def build(self):

        self.sm = ScreenManager()

        self.current_time_label = Label(
            text=self.get_current_time(),
            font_name="NotoSerifCJKtc",
            font_size="18sp",
            halign="left",
            valign="middle",
            size_hint=(1, 0.1)
        )
        Clock.schedule_interval(self.update_time, 1)  # 每秒更新時間

        # 第一頁：學習計劃管理
        plan_screen = Screen(name="plans")
        plan_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)


        plan_layout.add_widget(self.current_time_label)

        self.plan_input = TextInput(hint_text="輸入學習計劃名稱...", multiline=False, font_name="NotoSerifCJKtc")
        self.due_date_input = TextInput(hint_text="輸入截止日期 (YYYY-MM-DD)...", multiline=False, font_name="NotoSerifCJKtc")
        add_plan_button = Button(text="新增計劃", on_press=self.add_plan, font_name="NotoSerifCJKtc", size_hint=(1, 0.3))
        view_plans_button = Button(text="檢視計劃", on_press=lambda x: self.switch_screen("view_plans"), font_name="NotoSerifCJKtc", size_hint=(1, 0.3))

        self.daily_checkbox = CheckBox()
        self.weekly_checkbox = CheckBox()

        self.daily_checkbox.bind(active=self.on_daily_checkbox_active)
        self.weekly_checkbox.bind(active=self.on_weekly_checkbox_active)

        checkbox_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.3))
        checkbox_layout.add_widget(Label(text="每日", font_name="NotoSerifCJKtc"))
        checkbox_layout.add_widget(self.daily_checkbox)
        checkbox_layout.add_widget(Label(text="每周", font_name="NotoSerifCJKtc"))
        checkbox_layout.add_widget(self.weekly_checkbox)

        plan_layout.add_widget(Label(text="學習計劃管理", font_name="NotoSerifCJKtc", font_size="24sp"))
        plan_layout.add_widget(self.plan_input)
        plan_layout.add_widget(self.due_date_input)
        plan_layout.add_widget(checkbox_layout)
        plan_layout.add_widget(add_plan_button)
        plan_layout.add_widget(view_plans_button)

        plan_screen.add_widget(plan_layout)
        self.sm.add_widget(plan_screen)

        # 第二頁：檢視計劃
        view_plans_screen = Screen(name="view_plans")
        view_plans_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.plan_list = GridLayout(cols=1, size_hint_y=None)
        self.plan_list.bind(minimum_height=self.plan_list.setter('height'))
        self.update_plan_list()
        plan_scroll = ScrollView(size_hint=(1, 0.8))  
        plan_scroll.add_widget(self.plan_list)
        view_plans_layout.add_widget(plan_scroll)

        back_button = Button(text="返回", on_press=lambda x: self.switch_screen("plans"), font_name="NotoSerifCJKtc",size_hint=(1, 0.2))
        view_plans_layout.add_widget(back_button)

        view_plans_screen.add_widget(view_plans_layout)
        self.sm.add_widget(view_plans_screen)

        # 第三頁：今日進度
        progress_screen = Screen(name="progress")
        progress_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.progress_list = GridLayout(cols=1, size_hint_y=None)
        self.progress_list.bind(minimum_height=self.progress_list.setter('height'))
        self.update_progress_list()
        progress_scroll = ScrollView(size_hint=(1, 0.8))
        progress_scroll.add_widget(self.progress_list)
        progress_layout.add_widget(progress_scroll)

        back_to_main_button = Button(text="返回", on_press=lambda x: self.switch_screen("plans"), font_name="NotoSerifCJKtc",size_hint=(1, 0.2))
        progress_layout.add_widget(back_to_main_button)

        progress_screen.add_widget(progress_layout)
        self.sm.add_widget(progress_screen)

        # 第四頁：亞洲鬧鐘
        asain_screen = Screen(name="asain")
        asain_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        timer_input_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), spacing=10,pos_hint={'top': 1})
        self.minutes_input = TextInput(hint_text="分鐘", multiline=False, input_filter='int', font_name="NotoSerifCJKtc",size_hint=(1, 0.5))
        self.seconds_input = TextInput(hint_text="秒數", multiline=False, input_filter='int', font_name="NotoSerifCJKtc",size_hint=(1, 0.5))
        start_timer_button = Button(text="開始計時", font_name="NotoSerifCJKtc", on_press=self.start_timer,size_hint=(1, 0.5),background_color=(0.13, 0.55, 0.13, 1.0),background_normal='')

        timer_input_layout.add_widget(self.minutes_input)
        timer_input_layout.add_widget(self.seconds_input)
        timer_input_layout.add_widget(start_timer_button)


        select_music_button = Button(
            text="選擇音樂",
            font_name="NotoSerifCJKtc",
            size_hint=(0.5, 0.5),  
            on_press=self.open_music_selector
        )
       

        self.title_label = Label(
            text="SLEEP MODE",
            font_size=20,
            color=(0.3, 1, 0.3, 1),
            size_hint=(1, None),
            height=40
        )

        self.timer_label = Label(
            text="00:00",
            font_name="NotoSerifCJKtc",
            font_size="48sp",
            halign="center",
            size_hint=(1, 0.3),
            color=self.text_color
        )

        self.status_label = Label(
            text="Ready to sleep",
            font_size=14,
            color=self.text_color,
            size_hint=(1, None),
            height=40
        )

        self.progress = ProgressBar(max=self.remaining_time, value=0, size_hint=(1, None), height=30)

        asain_layout.add_widget(timer_input_layout)
        asain_layout.add_widget(self.title_label)
        asain_layout.add_widget(self.timer_label)
        asain_layout.add_widget(self.progress)
        asain_layout.add_widget(self.status_label)
        

        back_to_main_button = Button(text="返回", on_press=lambda x: self.switch_screen("plans"), font_name="NotoSerifCJKtc", size_hint=(1, 0.5))
        color_button = Button(
            text="顏色",
            font_name="NotoSerifCJKtc",
            size_hint=(1,0.5),
            on_press=self.choose_color
        )   

        button_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), spacing=10)

        stop_timer_button = Button(
            text="暫停",
            font_name="NotoSerifCJKtc",
            on_press=self.stop_timer,
            size_hint=(1, 0.5),
            background_color=(1.0, 0.2, 0.2, 1.0),
            background_normal='',
            )
        stop_timer_button.opacity = 0  
        stop_timer_button.disabled = True

      
        timer_input_layout.add_widget(stop_timer_button)
        self.stop_timer_button = stop_timer_button
        button_layout.add_widget(color_button)
        button_layout.add_widget(select_music_button)
        button_layout.add_widget(back_to_main_button)
        asain_layout.add_widget(button_layout)
        asain_screen.add_widget(asain_layout)
        self.sm.add_widget(asain_screen)

    
        nav_layout = BoxLayout(size_hint=(1, 0.1))
        btn_plan = Button(text="學習計劃", on_press=lambda x: self.switch_screen("plans"), font_name="NotoSerifCJKtc")
        btn_progress = Button(text="今日進度", on_press=lambda x: self.switch_screen("progress"), font_name="NotoSerifCJKtc")
        btn_asain = Button(text="亞洲鬧鐘", on_press=lambda x: self.switch_screen("asain"), font_name="NotoSerifCJKtc")
        nav_layout.add_widget(btn_plan)
        nav_layout.add_widget(btn_progress)
        nav_layout.add_widget(btn_asain)
        main_layout = BoxLayout(orientation='vertical')
        
        main_layout.add_widget(self.sm)
        main_layout.add_widget(nav_layout)

        return main_layout
    
    def get_current_time(self):
        """獲取當前時間的字串格式"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def update_time(self, dt):
        """更新時間 Label 的文字"""
        self.current_time_label.text = self.get_current_time()

    def switch_screen(self, screen_name):
        self.sm.current = screen_name
        if screen_name == "view_plans":
            self.update_plan_list()  
        elif screen_name == "progress":
            self.update_progress_list()  

    def validate_date(self, date_text):
        """驗證日期格式"""
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_text):
            return False
        try:
            datetime.strptime(date_text, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def show_error_popup(self, message):
        """顯示錯誤彈窗"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, font_name="NotoSerifCJKtc"))
        close_button = Button(text="關閉", size_hint=(1, 0.3), font_name="NotoSerifCJKtc")
        popup = Popup(title="ERROR!", content=content, size_hint=(0.7, 0.4))
        close_button.bind(on_press=popup.dismiss)
        content.add_widget(close_button)
        popup.open()

    def add_plan(self, instance):
        """新增學習計劃"""
        name = self.plan_input.text
        due_date = self.due_date_input.text
        daily = self.daily_checkbox.active
        weekly = self.weekly_checkbox.active

        if not name:
            self.show_error_popup("請輸入學習計劃名稱！")
            return

        if not self.validate_date(due_date):
            self.show_error_popup("日期格式錯誤！請輸入 YYYY-MM-DD。")
            return

        if not (daily or weekly):
            self.show_error_popup("請選擇每日或每周計劃！")
            return
        
        input_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        today = datetime.now().date()  

        if input_date < today:
            self.show_error_popup("不要當時空旅人")
            return
        create_date = today.strftime("%Y-%m-%d")
        self.plans.append({
            "name": name,
            "due_date": due_date,
            "daily": daily,
            "weekly": weekly,
            "create_date": create_date, 
            "status": "Pending"
        })
        self.save_data()
        self.update_plan_list()
        self.plan_input.text = ""
        self.due_date_input.text = ""
        self.daily_checkbox.active = False
        self.weekly_checkbox.active = False

    def update_plan_list(self):
        """更新計劃清單"""
        self.plan_list.clear_widgets()
        today = datetime.now().date()  

        for plan in self.plans:
            due_date = datetime.strptime(plan['due_date'], "%Y-%m-%d").date()
            if due_date < today and plan['status'] != "Completed":
                plan['status'] = "Completed"

        self.save_data()

        if not self.plans:
            no_plan_label = Label(
                text="目前沒有建立的學習計劃，請至新建計劃頁面建立。",
                font_name="NotoSerifCJKtc",
                size_hint_y=None,
                height=40
            )
            self.plan_list.add_widget(no_plan_label)
            return

        for plan in self.plans:
            frequency = lambda condition: "每日" if plan["daily"] else "每周"
            plan_label = Label(
                text=f"{plan['name']} (到期日: {plan['due_date']}) - 狀態: {plan['status']} - 週期: {frequency(plan)}",
                size_hint_y=None,
                height=40,
                font_name="NotoSerifCJKtc"
            )
            delete_button = Button(
                text="刪除",
                size_hint_y=None,
                height=40,
                font_name="NotoSerifCJKtc"
            )
            delete_button.bind(on_press=lambda instance, p=plan: self.delete_plan(p))
            self.plan_list.add_widget(plan_label)
            self.plan_list.add_widget(delete_button)
        
    def delete_plan(self, plan):
        """刪除計劃"""
        self.plans.remove(plan)
        self.save_data()
        self.update_plan_list()
    def update_progress_list(self):
        """更新今日進度清單"""
        self.progress_list.clear_widgets()
        today = datetime.now().strftime("%Y-%m-%d")  

        for plan in self.plans:
            if plan["status"] == "Completed":
                continue  
            is_daily = plan.get("daily", False)
            is_weekly_due = (
                plan.get("weekly", False) and
                (datetime.now().date() - datetime.strptime(plan["create_date"], "%Y-%m-%d").date()).days % 7 == 0
            )

            if is_daily or is_weekly_due:
                signed_today = self.check_log(plan, today)

                progress_label = Label(
                    text=f"今日進度: {plan['name']}",
                    size_hint_y=None,
                    height=40,
                    font_name="NotoSerifCJKtc"
                )
                complete_button = Button(
                    text="已完成" if signed_today else "完成今日進度",
                    size_hint_y=None,
                    height=40,
                    font_name="NotoSerifCJKtc",
                    disabled=signed_today  # 禁用按鈕如果已簽到
                )
                complete_button.bind(on_press=lambda instance, p=plan, b=complete_button: self.complete_daily_progress(p, b))
                self.progress_list.add_widget(progress_label)
                self.progress_list.add_widget(complete_button)

    def check_log(self, plan, today):
        """檢查 LOG 文件中是否有該計劃的今日記錄"""
        log_file = "log.json"


        if not os.path.exists(log_file):
            return False

        with open(log_file, "r") as file:
            try:
                log_data = json.load(file)
            except json.JSONDecodeError:
                return False

        plan_logs = log_data.get(plan["name"], [])
        return today in plan_logs


    def complete_daily_progress(self, plan, button):
        """標記今日進度為完成並記錄日誌"""
        self.save_log(plan)  
        button.text = "已完成"  
        button.disabled = True  



    def on_daily_checkbox_active(self, checkbox, value):
        if value:
            self.weekly_checkbox.active = False

    def on_weekly_checkbox_active(self, checkbox, value):
        if value:
            self.daily_checkbox.active = False
    def start_timer(self, instance):
        """開始計時"""
        try:
            if self.started==False or (self.minutes_input.text!="" and self.seconds_input.text!=""):
                self.started=True
                if self.remaining_time > 0:
                    Clock.unschedule(self.update_timer)
                    # 顯示停止按鈕
                    self.stop_timer_button.opacity = 1
                    self.stop_timer_button.disabled = False
                minutes = int(self.minutes_input.text) if self.minutes_input.text else 0
                seconds = int(self.seconds_input.text) if self.seconds_input.text else 0
                self.remaining_time = minutes * 60 + seconds
                if self.remaining_time > 0:
                    self.progress.max = self.remaining_time
                    self.update_timer_label()
                    self.timer_event = Clock.schedule_interval(self.update_timer, 1)
                # 顯示停止按鈕
                    self.stop_timer_button.opacity = 1
                    self.stop_timer_button.disabled = False
                self.minutes_input.text=""
                self.seconds_input.text=""
            elif self.started==True :
                Clock.unschedule(self.update_timer)
                self.is_paused = False
                self.stop_timer_button.disabled = False
                if self.remaining_time > 0:
                    self.progress.max = self.remaining_time
                    self.update_timer_label()
                    self.timer_event = Clock.schedule_interval(self.update_timer, 1)
        except ValueError:
            self.status_label.text = "請輸入有效的時間！"

    def stop_timer(self, instance):
        """停止計時器"""
        self.timer_event.cancel()
        self.is_paused = True
        self.stop_timer_button.disabled = True

    def update_timer(self, dt):
        """更新倒計時"""
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.update_timer_label()
            self.progress.value = self.progress.max - self.remaining_time
        else:
            Clock.unschedule(self.update_timer)
            self.timer_label.text = "時間到！"
            self.show_time_up_popup()
            # 隱藏停止按鈕
            self.stop_timer_button.opacity = 0
            self.stop_timer_button.disabled = True
            self.started==False

    def update_timer_label(self):
        """更新計時器顯示"""
        minutes, seconds = divmod(self.remaining_time, 60)
        self.timer_label.text = f"{minutes:02}:{seconds:02}"
    
    def show_time_up_popup(self):
        """顯示隨機題目，並要求使用者輸入正確答案才能關閉彈窗"""
        def cls(instance):
            if self.music_player:
                self.music_player.stop()
            popup.dismiss()

        if self.selected_music:
            self.play_selected_music()

        # 題目和答案列表
        questions = [
            ("123.45 + 67.89 - 45.67 =", 145.67),
            ("456.7 × 1.2 + 78.56 =", 626.6),
            ("789.01 - 123.45 + 67.89 =", 733.45),
            ("234.56 + 78.9 × 1.1 =", 321.35),
            ("567.89 - 45 × 2.3 =", 464.39),
            ("123.45 + 456 × 0.89 =", 529.29),
            ("78.9 × 4.5 - 67.89 =", 287.16),
            ("345.67 - 78.91 + 123.45 =", 390.21),
            ("567.8 × 0.6 + 45.67 =", 386.35),
            ("23.4 × 9.61 - 44.134 =", 180.74)
        ]
        

        question, correct_answer = random.choice(questions)
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        content.add_widget(Label(text=f"題目: {question}", font_name="NotoSerifCJKtc"))
    
        answer_input = TextInput(hint_text="輸入答案", multiline=False, size_hint=(1, 1), font_name="NotoSerifCJKtc")
        content.add_widget(answer_input)
        error_message = Label(text="", color=(1, 0, 0, 1), font_name="NotoSerifCJKtc")
        content.add_widget(error_message)
        retry_button = Button(text="重新輸入", size_hint=(1, 1), opacity=0, font_name="NotoSerifCJKtc")
        content.add_widget(retry_button)
        close_button = Button(text="關閉", size_hint=(1, 0.3), font_name="NotoSerifCJKtc")
        close_button.opacity = 0  # 使按鈕完全透明
        content.add_widget(close_button)
        def check_answer(instance):
            try:
                user_answer = float(answer_input.text)
                if user_answer == correct_answer:
                    close_button.opacity = 1  # 顯示關閉按鈕
                    retry_button.opacity = 0  # 隱藏重新輸入按鈕
                    error_message.text = "" 
                else:
                    error_message.text = "輸入錯誤，請重新輸入！"  
                    retry_button.opacity = 1  # 顯示重新輸入按鈕
            except ValueError:
                error_message.text = "無效的數字，請重新輸入！"  
                retry_button.opacity = 1  # 顯示重新輸入按鈕
        def reset_input(instance):
            answer_input.text = ""  # 清空輸入框
            error_message.text = ""  
            retry_button.opacity = 0  # 隱藏重新輸入按鈕

        
        popup = Popup(title="TIME UP!", content=content, size_hint=(0.7, 0.4), auto_dismiss=False )


        close_button.bind(on_press=cls)
        answer_input.bind(on_text_validate=check_answer)
        
        retry_button.bind(on_press=reset_input)
        popup.open()

    def choose_color(self, instance):
        """打開顏色選擇器"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        color_picker = ColorPicker(size_hint=(1, 1))
        content.add_widget(color_picker)

        select_button = Button(
            text="選擇",
            font_name="NotoSerifCJKtc",
            size_hint=(1, None),
            height=40,
            on_press=lambda x: self.apply_selected_color(color_picker.color)
        )
        content.add_widget(select_button)

        self.color_popup = Popup(
            title="COLOR",
            content=content,
            size_hint=(0.9, 0.9),
            auto_dismiss=True
        )
        self.color_popup.open()

    def apply_selected_color(self, color):
        self.text_color = color
        self.timer_label.color = color
        self.status_label.color = color
        self.color_popup.dismiss()

    def play_selected_music(self):
        """播放選擇的音樂"""
        if self.music_player:
            self.music_player.stop()
        
        self.music_player = SoundLoader.load(self.selected_music)
        if self.music_player:
            self.music_player.play()

    def select_music(self, path, selection):
        """儲存選擇的音樂"""
        if selection:
            self.selected_music = os.path.join(path, selection[0])
            print(f"選擇的音樂: {self.selected_music}")
        self.music_popup.dismiss()
    
    def open_music_selector(self, instance):
        """打開音樂選擇器"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        file_chooser = FileChooserListView(filters=["*.mp3", "*.wav", "*.ogg"], size_hint=(1, 1))
        content.add_widget(file_chooser)

        select_button = Button(
            text="確定選擇",
            size_hint=(1, None),
            height=40,
            on_press=lambda x: self.select_music(file_chooser.path, file_chooser.selection),
            font_name="NotoSerifCJKtc"
        )
        content.add_widget(select_button)

        self.music_popup = Popup(
            title="choose music",
            content=content,
            size_hint=(0.9, 0.9),
            auto_dismiss=True
        )
        self.music_popup.open()

       
if __name__ == '__main__':
    StudyHelperApp().run()
