import requests
import os
import logging
from logging.config import fileConfig
from sbol.sbolerror import *
from sbol.constants import *
from sbol.config import Config, ConfigOptions
from requests.exceptions import HTTPError
import pprint
import getpass


LOGGING_CONFIG = 'logging_config.ini'


class PartShop:
    """A class which provides an API front-end for online bioparts repositories"""

    def __init__(self, url, spoofed_url=''):
        """

        :param url: The URL of the online repository (as a str)
        :param spoofed_url:
        """
        self.logger = logging.getLogger(__name__)
        # set up logger
        if os.path.exists(LOGGING_CONFIG):
            fileConfig(LOGGING_CONFIG)
        else:
            self.logger.setLevel(logging.INFO)
        # initialize member variables
        self.resource = url
        self.key = ''
        self.spoofed_resource = spoofed_url
        if len(url) > 0 and url[-1] == '/':
            raise SBOLError(SBOLErrorCode.SBOL_ERROR_INVALID_ARGUMENT,
                            'PartShop initialization failed. The resource URL should not contain a terminal backlash')
        if len(spoofed_url) > 0 and spoofed_url[-1] == '/':
            raise SBOLError(SBOLErrorCode.SBOL_ERROR_INVALID_ARGUMENT,
                            'PartShop initialization failed. The spoofed URL should not contain a terminal backslash')

    def count(self):
        """Return the count of objects contained in a PartShop"""
        raise NotImplementedError('Not yet implemented')

    def sparqlQuery(self, query):
        """Issue a SPARQL query"""
        raise NotImplementedError('Not yet implemented')

    def pull(self, uris, doc, recursive=True):
        """Retrieve an object from an online resource
        :param uris: A list of SBOL objects you want to retrieve, or a single SBOL object URI
        :param doc: A document to add the data to
        :param recursive: Whether the GET request should be recursive
        :return:
        """
        # IMPLEMENTATION NOTE: rdflib.Graph.parse() actually lets you pass a URL as an argument.
        # I decided to not use this method, because I couldn't find an easy way to get the response
        # code, set HTTP headers, etc. In addition, I would need to use requests for submitting
        # new SBOL data anyway.
        endpoints = []
        if type(uris) is str:
            endpoints.append(uris)
        elif type(uris) is list:
            endpoints = uris
        else:
            raise TypeError('URIs must be str or list. Found: ' + str(type(uris)))
        for uri in endpoints:
            uri += '/sbol'
            if not recursive:
                uri += 'nr'
            if Config.getOption(ConfigOptions.VERBOSE.value):
                self.logger.debug('Issuing GET request ' + uri)
            # Issue GET request
            response = requests.get(uri)
            pp = pprint.PrettyPrinter(indent=4)  # DEBUG
            pp.pprint(str(response.content))  # DEBUG
            if response.status_code == 404:
                raise SBOLError(SBOLErrorCode.SBOL_ERROR_NOT_FOUND, 'Part not found. Unable to pull: ' + uri)
            elif response.status_code == 401:
                raise SBOLError(SBOLErrorCode.SBOL_ERROR_HTTP_UNAUTHORIZED, 'Please log in with valid credentials')
            elif not response:
                raise SBOLError(SBOLErrorCode.SBOL_ERROR_BAD_HTTP_REQUEST, response)
            # Add content to document
            serialization_format = Config.getOption('serialization_format')
            Config.setOption('serialization_format', serialization_format)
            doc.readString(response.content)
            doc.resource_namespaces.add(self.resource)

    def submit(self, doc, collection='', overwrite=0):
        """Submit a SBOL Document to SynBioHub
        :param doc: The Document to submit
        :param collection: The URI of a SBOL Collection to which the Document contents will be uploaded
        :param overwrite: An integer code: 0 (default) - do not overwrite, 1 - overwrite, 2 - merge
        :return:
        """
        raise NotImplementedError('Not yet implemented')
        # if collection == '':
        #     # If a Document is submitted as a new collection, then Document metadata must be specified
        #     if len(doc.displayId) == 0 or len(doc.name) == 0 or len(doc.description) == 0:
        #         raise SBOLError(SBOLErrorCode.SBOL_ERROR_INVALID_ARGUMENT,
        #                         'Cannot submit Document. The Document must be assigned a displayId, name, and ' +
        #                         'description for upload.')
        # else:
        #     if Config.getOption(ConfigOptions.VERBOSE.value) is True:
        #         self.logger.info('Submitting Document to an existing collection: ' + collection)
        # if Config.getOption(ConfigOptions.SERIALIZATION_FORMAT.value) == 'rdfxml':
        #     self.addSynBioHubAnnotations(doc)
        # data = {}
        # if len(doc.displayId) > 0:
        #     data['id'] = doc.displayId
        # if len(doc.version) > 0:
        #     data['version'] = doc.version
        # if len(doc.name) > 0:
        #     data['name'] = doc.name
        # if len(doc.description) > 0:
        #     data['description'] = doc.description
        # citations = ''
        # for citation in doc.citations:
        #     citations += citation + ','
        # citations = citations[0:-1]  # chop off final comma
        # data['citations'] = citations
        # keywords = ''
        # for kw in doc.keywords:
        #     keywords += kw + ','
        # keywords = keywords[0:-1]
        # data['keywords'] = keywords
        # data['overwrite_merge'] = overwrite
        # data['user'] = self.key
        # data['file'] = doc.writeString()
        # if collection != '':
        #     data['rootCollections'] = collection
        # # Send POST request
        # response = requests.post(self.resource + '/submit',
        #                          data=data,
        #                          headers={'Accept': 'text/plain', 'X-authorization': self.key})
        # if response:
        #     return response
        # elif response.status_code == 401:
        #     raise SBOLError(SBOLErrorCode.SBOL_ERROR_BAD_HTTP_REQUEST,
        #                     'You must login with valid credentials before submitting')
        # else:
        #     raise SBOLError(SBOLErrorCode.SBOL_ERROR_BAD_HTTP_REQUEST,
        #                     'HTTP post request failed with: ' + str(response))

    def login(self, user_id, password=''):
        """In order to submit to a PartShop, you must login first.
        Register on [SynBioHub](http://synbiohub.org) to obtain account credentials.
        :param user_id: User ID
        :param password: User password
        :return:
        """
        if password is None or password == '':
            password = getpass.getpass()
        # SECURITY NOTE" Including the password in the query string as plaintext is bad practice,
        # but HTTPS should encrypt it for us.
        response = requests.get(
            self.resource,
            params={'email': user_id, 'password': password},
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        if not response:
            raise SBOLError(SBOLErrorCode.SBOL_ERROR_BAD_HTTP_REQUEST,
                            'Login failed due to an HTTP error: ' + str(response))

    # def addSynBioHubAnnotations(self, doc):
    #     doc.addNamespace("http://wiki.synbiohub.org/wiki/Terms/synbiohub#", "sbh")
    #     for id, toplevel_obj in doc.SBOLObjects:
    #         toplevel_obj.apply(None, None)  # TODO

