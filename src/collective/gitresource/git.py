# -*- coding: utf-8 -*-
import logging
import re
from AccessControl import ClassSecurityInfo
import Globals

from Products.Five import BrowserView
from dulwich import web
from dulwich.objects import hex_to_sha
from dulwich.web import HTTPGitApplication
from dulwich.web import HTTPGitRequest


logger = logging.getLogger('collective.gitresource')


def __getstate__(self):
    def get_slots(klass):
        slots = getattr(klass, '__slots__', [])
        if isinstance(slots, tuple):
            slots = list(slots)
        elif isinstance(slots, str):
            slots = list([slots])
        for base_klass in klass.__bases__:
            slots.extend(get_slots(base_klass))
        return list(set(slots))

    names = list(getattr(self, '__dict__', {}).keys())
    names += get_slots(self.__class__)

    state = dict([(name, getattr(self, name)) for name in names])

    if '_sha' in state:
        state['_sha'] = None
    return state


def __setstate__(self, state):
    for key, value in state.items():
        setattr(self, key, value)

    if '_sha' in state and hasattr(self, 'sha'):
        self.sha()
    if '_sha' in state and hasattr(self, '_hexsha'):
        self._sha = hex_to_sha(self._hexsha)


def handle_service_request(req, backend, mat):
    service = mat.group().lstrip('/')
    logger.info('Handling service request for %s', service)

    handler_cls = req.handlers.get(service, None)
    if handler_cls is None:
        yield req.forbidden('Unsupported service %s' % service)
        return

    req.nocache()
    write = req.respond(web.HTTP_OK, 'application/x-%s-result' % service)

    fp = req.request.BODYFILE
    proto = web.ReceivableProtocol(fp.read, write)
    handler = handler_cls(backend, [web.url_prefix(mat)], proto, http_req=req)
    handler.handle()


class GitView(BrowserView, HTTPGitApplication):

    security = ClassSecurityInfo()

    services_overrides = {
        ('POST', re.compile('/git-upload-pack$')): handle_service_request,
        ('POST', re.compile('/git-receive-pack$')): handle_service_request,
    }

    def __init__(self, context, request, path=''):
        BrowserView.__init__(self, context, request)
        HTTPGitApplication.__init__(self, backend=self)
        self.path = '/' + path.strip('/')
        self.services = HTTPGitApplication.services.copy()
        self.services.update(self.services_overrides)

#   XXX: This would protect the call, but cannot get Git to authenticate...
#   security.declareProtected('plone.resourceeditor: Manage Sources',
#                             '__call__')
    def __call__(self, environ=None, start_response=None):
        path = self.path
        method = self.request['REQUEST_METHOD']
        req = GitRequest(self.request, dumb=False, handlers=self.handlers)

        mat = handler = None
        for service_method, service_path in self.services.iterkeys():
            if service_method != method:
                continue
            mat = service_path.search(path)
            if mat:
                handler = self.services[service_method, service_path]
                break

        if handler is None:
            return req.not_found(
                'Sorry, that method is not supported: {0:s}'.format(path))

        refs = self.open_repository().refs
        head = refs['HEAD']

        # Store HEAD before changes
        if method == 'POST':
            for name in refs.keys():
                if name != 'HEAD' and refs[name] == refs['HEAD']:
                    head = name

        # Execute
        result = handler(req, self, mat)
        for text in result:
            self.request.response.write(text)

        # Fix HEAD after changes
        if method == 'POST':
            try:
                refs['HEAD'] = refs[head]
            except KeyError:
                pass

        return self.request.response

    def open_repository(self, path=None):
        # noinspection PyProtectedMember
        return self.context.repository._repo

Globals.InitializeClass(GitView)


class GitRequest(HTTPGitRequest):
    def __init__(self, request, dumb=False, handlers=None):
        super(GitRequest, self).__init__(
            request.environ, self.start_response, dumb, handlers)
        self.request = request

    def start_response(self, status, headers):
        request = self.request
        for header in headers:
            request.response.setHeader(*header)
        status, reason = status.split(' ', 1)
        request.response.setStatus(int(status), reason)
        return request.response.write