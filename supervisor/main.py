from input import Controller
from ui import run


def main():
    print("Hello from supervisor!")

    def on_a_press():
        print("A button pressed!")

    def on_b_press():
        print("B button pressed!")

    # controller = Controller()

    # controller.on_button_down(0, on_a_press)  # Button 0 = usually A / Cross
    # controller.on_button_down(1, on_b_press)  # Button 1 = usually B / Circle

    # controller.start()

    run()


if __name__ == "__main__":
    main()
