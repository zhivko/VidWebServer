import logging
from MyFlask import MyFlask



logger = logging.getLogger(__name__)
handler = logging.StreamHandler(MyFlask.app().config['LOG_FILE'])
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.setLevel(MyFlask.app().config['LOG_LEVEL'])
