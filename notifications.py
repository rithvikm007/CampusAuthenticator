from queue import Empty, Queue


_notification_queue = Queue()
_console_notifier = None


def set_console_notifier(notifier):
    global _console_notifier
    _console_notifier = notifier


def notify(title, message):
    _notification_queue.put(
        (title, message)
    )

    if _console_notifier:
        _console_notifier(
            title,
            message
        )


def get_pending_notifications():
    notifications = []

    while True:
        try:
            notifications.append(
                _notification_queue.get_nowait()
            )
        except Empty:
            break

    return notifications


def setup_windows_toasts():
    from windows_toasts import (
        Toast,
        WindowsToaster
    )

    toaster = WindowsToaster(
        "CampusAuthenticator"
    )

    def show(title, message):
        toast = Toast()
        toast.text_fields = [
            title,
            message
        ]
        toaster.show_toast(toast)

    set_console_notifier(show)


if __name__ == "__main__":

    setup_windows_toasts()

    notify(
        "CampusAuthenticator",
        "This is a test notification!"
    )