from windows_toasts import Toast, WindowsToaster


APP_NAME = "CampusAuthenticator"

toaster = WindowsToaster(APP_NAME)


def notify(title, message):
    """
    Displays a Windows toast notification.
    """

    toast = Toast()

    toast.text_fields = [
        title,
        message
    ]

    toaster.show_toast(toast)

if __name__ == "__main__":

    notify(
        "CampusAuthenticator",
        "This is a CampusAuthenticator test notification!"
    )