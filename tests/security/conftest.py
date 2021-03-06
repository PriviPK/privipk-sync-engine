from gevent import monkey
monkey.patch_all(aggressive=False)

# fixtures that are available by default
from tests.util.base import (config, db, log, absolute_path, default_namespace,
                             default_account)
from tests.util.base import (config, db, log, message, thread,
                             default_namespace, absolute_path, default_account)


def pytest_generate_tests(metafunc):
    if 'db' in metafunc.fixturenames:
        dumpfile = absolute_path(config()['BASE_DUMP'])
        savedb = False

        metafunc.parametrize('db', [(dumpfile, savedb)], indirect=True)
