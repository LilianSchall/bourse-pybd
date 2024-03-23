# -*- coding: utf-8 -*-

'''
  Ma version de logging. Je la préfère au fichier de configuration car elle permet
  de savoir dans quel fichier je suis (cf __name__ dans l'appel).

  Pour ce qui est du seuil de déclanchement des avertissements il est préférable
  de ne rien mettre dans les autres fichier ainsi il suffit de modifier la valeur
  par défaut ici pour que toute la bibliothèque change le seuil.

  cf https://docs.python.org/2/howto/logging.html pour la doc

  >>> from testfixtures import LogCapture
  >>> l = LogCapture()
  >>> getLogger(__name__, level=logging.DEBUG).error('doctest'); print(l)
  mylogging ERROR
    doctest
'''

import logging
import logging.handlers

INFO = logging.INFO
DEBUG = logging.DEBUG

log_level = logging.DEBUG  # change this if you want a another default variable

def getLogger(name, level=log_level,
              filename=None, file_level=None):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # create file handle if needed
    if filename is not None:
        print("Logs of %s go to %s" % (name, filename))
        fh = logging.handlers.RotatingFileHandler(filename, maxBytes=10*1024*1024, backupCount=3)
        if file_level is None:
            fh.setLevel(level)
        else:
            fh.setLevel(file_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    else:
        # create console handler and set level to debug
        sh = logging.StreamHandler()
        sh.set_name("handler of %s" % name)
        sh.setLevel(level)
        sh.setFormatter(formatter)
        logger.addHandler(sh)
    return logger


