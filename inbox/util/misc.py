import os, sys, pkgutil, time
from inbox.log import get_logger


def or_none(value, selector):
    if value is None:
        return None
    else:
        return selector(value)


def strip_plaintext_quote(text):
    """
    Strip out quoted text with no inline responses.

    TODO: Make sure that the line before the quote looks vaguely like
    a quote header. May be hard to do in an internationalized manner?

    """
    found_quote = False
    lines = text.strip().splitlines()
    quote_start = None
    for i, line in enumerate(lines):
        if line.startswith('>'):
            found_quote = True
            if quote_start is None:
                quote_start = i
        else:
            found_quote = False
    if found_quote:
        return '\n'.join(lines[:quote_start-1])
    else:
        return text


def parse_ml_headers(headers):
    """
    Parse the mailing list headers described in RFC 4021,
    these headers are optional (RFC 2369).

    """
    attrs = {}
    attrs['List-Archive'] = headers.get('List-Archive')
    attrs['List-Help'] = headers.get('List-Help')
    attrs['List-Id'] = headers.get('List-Id')
    attrs['List-Owner'] = headers.get('List-Owner')
    attrs['List-Post'] = headers.get('List-Post')
    attrs['List-Subscribe'] = headers.get('List-Subscribe')
    attrs['List-Unsubscribe'] = headers.get('List-Unsubscribe')

    return attrs


def parse_references(references, in_reply_to):
    """
    Determine the message_ids that the message references, as per JWZ.
    (http://www.jwz.org/doc/threading.html)

    Returns
    -------
    str
        references : a string of tab-separated message_ids.

    """
    replyto = in_reply_to.split()[0] if in_reply_to else in_reply_to

    if not references:
        return replyto

    separator = '\t'
    if replyto not in references:
        references += (separator + replyto)
    return references


def timed(fn):
    """ A decorator for timing methods. """
    def timed_fn(self, *args, **kwargs):
        start_time = time.time()
        ret = fn(self, *args, **kwargs)

        # TODO some modules like gmail.py don't have self.logger
        try:
            if self.log:
                fn_logger = self.log
        except AttributeError:
            fn_logger = get_logger()
            # out = None
        fn_logger.info("[timer] {0} took {1:.3f} seconds.".format(str(fn), float(time.time() - start_time)))
        return ret
    return timed_fn


# From: http://stackoverflow.com/a/8556471
def load_modules(base_module):
    """
    Imports all modules underneath `base_module` in the module tree.

    Note that if submodules are located in different directory trees, you
    need to use `pkgutil.extend_path` to make all the folders appear in
    the module's `__path__`.

    Returns
    -------
    list
        All the modules in the base module tree.
    """
    modules = []

    base_name = base_module.__name__
    base_path = base_module.__path__

    for importer, module_name, _ in pkgutil.iter_modules(base_path):
        full_module_name = '{0}.{1}'.format(base_name, module_name)

        if full_module_name not in sys.modules:
            module = importer.find_module(module_name).load_module(
                full_module_name)
        else:
            module = sys.modules[full_module_name]
        modules.append(module)

    return modules