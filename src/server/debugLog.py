import logging
from os import mkdir
from pathlib import Path
from datetime import datetime as dt

class DebugLog:
    def __init__(self, log_dir='/app/logs', log_level=logging.DEBUG):
        self.fastapi_logger_error = logging.getLogger('uvicorn.error')
        self.fastapi_logger_error.setLevel(log_level)
        self.fastapi_logger_access = logging.getLogger('uvicorn.access')
        self.fastapi_logger_access.setLevel(log_level)
        self.logger = logging.getLogger('cuicuisine')
        self.logger.setLevel(log_level)
        self.isEnabled = True

        # Create the log directory if it doesn't exist
        logDir = Path(log_dir)
        if not logDir.exists():
            mkdir(log_dir)

        # Create the log file
        log_file = logDir.joinpath(f"cuicuisine_{dt.now().strftime("%Y%m%d")}.log")
        
        # Create a file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        
        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # Create a logging format
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to the logger
        self.fastapi_logger_error.addHandler(file_handler)
        self.fastapi_logger_access.addHandler(file_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, message):
        self.logger.debug(message)
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def critical(self, message):
        self.logger.critical(message)