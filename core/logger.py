import datetime

from core.paths import data_path


class TimestampLogger:

    def __init__(self, stream):

        self.stream = stream
        self.at_line_start = True

        self.log_dir = data_path(
            "logs"
        )

        self.log_dir.mkdir(
            parents=True,
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

        filepath = (
            self.log_dir / filename
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

        for filepath in self.log_dir.iterdir():

            if not filepath.is_file():
                continue

            filename = filepath.name

            if not filename.startswith(
                "authenticator-"
            ):
                continue

            if not filename.endswith(
                ".log"
            ):
                continue

            try:

                date_string = filename[
                    len("authenticator-"):
                    -len(".log")
                ]

                file_date = (
                    datetime.datetime.strptime(
                        date_string,
                        "%Y-%m-%d"
                    ).date()
                )

                if file_date < cutoff:

                    filepath.unlink()

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

            timestamp = (
                datetime.datetime.now().strftime(
                    "[%Y-%m-%d %H:%M:%S] "
                )
            )

            self.log_file.write(
                timestamp
            )

        self.log_file.write(
            message
        )

        self.log_file.flush()

        self.at_line_start = (
            message.endswith("\n")
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