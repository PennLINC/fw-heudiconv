import logging
import pprint
import pandas as pd
from .cli.export import get_nested


logger = logging.getLogger(__name__)


def generate_participants_file(sessions_list, tsvs, dry_run=False):

    if tsvs['participants_auto']:

        logger.info("Generating participants.tsv auto-magically")
        logger.debug(pprint.pprint(tsvs))

    elif tsvs['participants_file'] is not None:

        logger.info("Generating participants.tsv from file")
        logger.debug(pprint.pprint(tsvs))

    else:
        return


def generate_sessions_file(sessions_list, tsvs, dry_run=False):

    if tsvs['sessions_auto']:

        logger.info("Generating *_sessions.tsv's auto-magically")
        logger.debug(pprint.pprint(tsvs))

    elif tsvs['sessions_file'] is not None:

        logger.info("Generating *_sessions.tsv's from file")
        logger.debug(pprint.pprint(tsvs))

    else:
        return
