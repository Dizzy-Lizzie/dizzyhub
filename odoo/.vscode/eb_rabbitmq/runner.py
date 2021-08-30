# copied from https://github.com/OCA/queue/blob/14.0/queue_job/jobrunner/runner.py

class QueueJobRunner(object):
    def __init__(
        self,
        scheme="http",
        host="localhost",
        port=8069,
        user=None,
        password=None,
        channel_config_string=None,
    ):
        self.scheme = scheme
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.channel_manager = ChannelManager()
        if channel_config_string is None:
            channel_config_string = _channels()
        self.channel_manager.simple_configure(channel_config_string)
        self.db_by_name = {}
        self._stop = False
        self._stop_pipe = os.pipe()

    @classmethod
    def from_environ_or_config(cls):
        scheme = os.environ.get("ODOO_QUEUE_JOB_SCHEME") or queue_job_config.get(
            "scheme"
        )
        host = (
            os.environ.get("ODOO_QUEUE_JOB_HOST")
            or queue_job_config.get("host")
            or config["http_interface"]
        )
        port = (
            os.environ.get("ODOO_QUEUE_JOB_PORT")
            or queue_job_config.get("port")
            or config["http_port"]
        )
        user = os.environ.get("ODOO_QUEUE_JOB_HTTP_AUTH_USER") or queue_job_config.get(
            "http_auth_user"
        )
        password = os.environ.get(
            "ODOO_QUEUE_JOB_HTTP_AUTH_PASSWORD"
        ) or queue_job_config.get("http_auth_password")
        runner = cls(
            scheme=scheme or "http",
            host=host or "localhost",
            port=port or 8069,
            user=user,
            password=password,
        )
        return runner

    def get_db_names(self):
        if config["db_name"]:
            db_names = config["db_name"].split(",")
        else:
            db_names = odoo.service.db.exp_list(True)
        return db_names

    def close_databases(self, remove_jobs=True):
        for db_name, db in self.db_by_name.items():
            try:
                if remove_jobs:
                    self.channel_manager.remove_db(db_name)
                db.close()
            except Exception:
                _logger.warning("error closing database %s", db_name, exc_info=True)
        self.db_by_name = {}

    def initialize_databases(self):
        for db_name in self.get_db_names():
            db = Database(db_name)
            if db.has_queue_job:
                self.db_by_name[db_name] = db
                with db.select_jobs("state in %s", (NOT_DONE,)) as cr:
                    for job_data in cr:
                        self.channel_manager.notify(db_name, *job_data)
                _logger.info("queue job runner ready for db %s", db_name)

    def run_jobs(self):
        now = _odoo_now()
        for job in self.channel_manager.get_jobs_to_run(now):
            if self._stop:
                break
            _logger.info("asking Odoo to run job %s on db %s", job.uuid, job.db_name)
            self.db_by_name[job.db_name].set_job_enqueued(job.uuid)
            _async_http_get(
                self.scheme,
                self.host,
                self.port,
                self.user,
                self.password,
                job.db_name,
                job.uuid,
            )

    def process_notifications(self):
        for db in self.db_by_name.values():
            if not db.conn.notifies:
                # If there are no activity in the queue_job table it seems that
                # tcp keepalives are not sent (in that very specific scenario),
                # causing some intermediaries (such as haproxy) to close the
                # connection, making the jobrunner to restart on a socket error
                db.keep_alive()
            while db.conn.notifies:
                if self._stop:
                    break
                notification = db.conn.notifies.pop()
                uuid = notification.payload
                with db.select_jobs("uuid = %s", (uuid,)) as cr:
                    job_datas = cr.fetchone()
                    if job_datas:
                        self.channel_manager.notify(db.db_name, *job_datas)
                    else:
                        self.channel_manager.remove_job(uuid)

    def wait_notification(self):
        for db in self.db_by_name.values():
            if db.conn.notifies:
                # something is going on in the queue, no need to wait
                return
        # wait for something to happen in the queue_job tables
        # we'll select() on database connections and the stop pipe
        conns = [db.conn for db in self.db_by_name.values()]
        conns.append(self._stop_pipe[0])
        # look if the channels specify a wakeup time
        wakeup_time = self.channel_manager.get_wakeup_time()
        if not wakeup_time:
            # this could very well be no timeout at all, because
            # any activity in the job queue will wake us up, but
            # let's have a timeout anyway, just to be safe
            timeout = SELECT_TIMEOUT
        else:
            timeout = wakeup_time - _odoo_now()
        # wait for a notification or a timeout;
        # if timeout is negative (ie wakeup time in the past),
        # do not wait; this should rarely happen
        # because of how get_wakeup_time is designed; actually
        # if timeout remains a large negative number, it is most
        # probably a bug
        _logger.debug("select() timeout: %.2f sec", timeout)
        if timeout > 0:
            conns, _, _ = select.select(conns, [], [], timeout)
            if conns and not self._stop:
                for conn in conns:
                    conn.poll()

    def stop(self):
        _logger.info("graceful stop requested")
        self._stop = True
        # wakeup the select() in wait_notification
        os.write(self._stop_pipe[1], b".")

    def run(self):
        _logger.info("starting")
        while not self._stop:
            # outer loop does exception recovery
            try:
                _logger.info("initializing database connections")
                # TODO: how to detect new databases or databases
                #       on which queue_job is installed after server start?
                self.initialize_databases()
                _logger.info("database connections ready")
                # inner loop does the normal processing
                while not self._stop:
                    self.process_notifications()
                    self.run_jobs()
                    self.wait_notification()
            except KeyboardInterrupt:
                self.stop()
            except InterruptedError:
                # Interrupted system call, i.e. KeyboardInterrupt during select
                self.stop()
            except Exception:
                _logger.exception(
                    "exception: sleeping %ds and retrying", ERROR_RECOVERY_DELAY
                )
                self.close_databases()
                time.sleep(ERROR_RECOVERY_DELAY)
        self.close_databases(remove_jobs=False)
        _logger.info("stopped")