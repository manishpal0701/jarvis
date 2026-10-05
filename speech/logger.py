import logging
import sys
import os

def get_logger(name: str = "JarvisSpeech") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        if os.environ.get("DEBUG") == "1":
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
            
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Prevent propagation to root logger to avoid duplicate logs in main application
        logger.propagate = False
        
    return logger
