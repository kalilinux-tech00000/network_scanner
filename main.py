import os
os.environ['KIVY_NO_ENV_CONFIG'] = '1'
from kivy.app import App
from kivy.uix.label import Label
class NetScanApp(App):
    def build(self):
        return Label(text='Network Scanner - Fixed for APK build!\n\nBuild successful. Scan features coming soon.')
if __name__ == '__main__':
    NetScanApp().run()