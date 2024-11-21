
from app import app
import logging
import sys

log_levels = {"CRITICAL": logging.CRITICAL,"ERROR": logging.ERROR,"WARNING": logging.WARNING,"INFO": logging.INFO,"DEBUG": logging.DEBUG}

log_level = log_levels.get("DEBUG", logging.DEBUG)

logging.basicConfig(stream=sys.stdout,
                    format="[%(asctime)s] [%(module)s][%(levelname)s] %(message)s",
                    level=log_level,
                    datefmt="%Y-%m-%d %H:%M:%S %z")

logging.getLogger().setLevel(log_level)


loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
for logger in loggers:
    logger.setLevel(log_level)



@app.after_request
def set_response_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response




if __name__ == "__main__":
    app.run(debug=False)