from controller.app_controller import AppController
from view.app_view import AppView


def main():
    controller = AppController()
    view = AppView(controller)
    view.mainloop()


if __name__ == "__main__":
    main()
