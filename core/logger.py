import datetime
import os


class TimestampLogger:

    def __init__(self, stream):

        self.stream = stream
        self.at_line_start = True

        self.log_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            ),
            "logs"
        )

        os.makedirs(
            self.log_dir,
            exist_ok=True
        )

        self.current_date = None
        self.log_file = None

        self._update_log_file()

    def _update_log_file(self):

        today = datetime.date.today()

        if today == self.current_date:
            return

        if self.log_file:
            self.log_file.close()

        self.current_date = today

        filename = (
            f"authenticator-{today.strftime('%Y-%m-%d')}.log"
        )

        filepath = os.path.join(
            self.log_dir,
            filename
        )

        self.log_file = open(
            filepath,
            "a",
            encoding="utf-8"
        )

        self._cleanup_old_logs()

    def _cleanup_old_logs(self):

        cutoff = (
            self.current_date
            - datetime.timedelta(days=3)
        )

        for filename in os.listdir(self.log_dir):

            if not filename.startswith(
                "authenticator-"
            ):
                continue

            if not filename.endswith(".log"):
                continue

            try:

                date_string = filename[
                    len("authenticator-"):-len(".log")
                ]

                file_date = datetime.datetime.strptime(
                    date_string,
                    "%Y-%m-%d"
                ).date()

                if file_date < cutoff:

                    os.remove(
                        os.path.join(
                            self.log_dir,
                            filename
                        )
                    )

            except ValueError:

                continue

    def write(self, message):

        if not message:
            return

        self._update_log_file()

        if (
            self.at_line_start
            and message.strip()
        ):

            timestamp = datetime.datetime.now().strftime(
                "[%Y-%m-%d %H:%M:%S] "
            )

            self.log_file.write(timestamp)

        self.log_file.write(message)
        self.log_file.flush()

        self.at_line_start = message.endswith(
            "\n"
        )

    def flush(self):

        self.log_file.flush()


def setup_logging():

    import sys

    sys.stdout = TimestampLogger(
        sys.stdout
    )

    sys.stderr = TimestampLogger(
        sys.stderr
    )