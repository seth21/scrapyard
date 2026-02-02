from controller.app_controller import Controller

class App:
    def __init__(self):
        #Initialize Controller
        self.controller = Controller()
        self.controller.run()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app = App()


