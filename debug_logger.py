
import logging
import os

# Configure logging to write to a file
logging.basicConfig(filename='backend_debug.log', level=logging.ERROR, 
                    format='%(asctime)s %(levelname)s: %(message)s')

def log_exception(e):
    logging.error(f"Exception occurred: {str(e)}", exc_info=True)
