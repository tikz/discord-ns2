import logging
import os
import re
from ftplib import FTP
import config
import utils

logger = logging.getLogger(__name__)
utils.logger_formatter(logger)

class Logs():
    def __init__(self):
        self.log_dir = config.LOCAL_LOGS_PATH

        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self.sync()

    def sync(self):
        ftp = FTP(config.FTP_ADDRESS)
        ftp.login(user=config.FTP_USER, passwd=config.FTP_PASSWORD)
        for ftp_file_path in ftp.nlst(config.FTP_LOGS_PATH):
            filename = ftp_file_path.split('/')[-1]
            try:
                # Raise exception when size is different or file does not exists
                local_file_size = os.path.getsize(self.log_dir + filename)
                if local_file_size != ftp.size(ftp_file_path):
                    raise FileNotFoundError
            except Exception as e:
                logger.info('FTP get: {}'.format(ftp_file_path))
                ftp.retrbinary('RETR ' + ftp_file_path, open(self.log_dir + filename, 'wb').write)

    def search(self, text):
        found = []
        pattern = re.compile(text, re.IGNORECASE)
        for log in os.listdir(self.log_dir):
            log_path = os.path.join(self.log_dir, log)
            data = open(log_path, 'r', errors='replace')
            for lines in data.readlines():
                if re.search(pattern, lines):
                    for found_line in re.split(r'=', lines):
                        found.append('{} {}'.format(log, found_line))
        return found


if config.ENABLE_FTP_LOGS:
    logs = Logs()
