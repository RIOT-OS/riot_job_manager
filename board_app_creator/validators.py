import os
import shutil

from django.core.exceptions import ValidationError
from django.conf import settings
import vcs

def validate_git_repository(value):
    path = os.path.join(settings.RIOT_REPO_BASE_PATH, 'tmp')
    try:
        vcs.get_repository(path, 'git', value)
    except vcs.VCSError, e:
        raise ValidationError(e)
    finally:
        try:
            shutil.rmtree(path)
        except OSError:
            pass
