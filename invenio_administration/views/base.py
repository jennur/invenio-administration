# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio Administration views base module."""
from functools import partial

from flask import current_app, render_template
from flask.views import MethodView
from flask_security import roles_required
from invenio_search_ui.searchconfig import search_app_config

from invenio_administration.errors import InvalidResource
from invenio_administration.marshmallow_utils import jsonify_schema

# class AdminViewType(MethodViewType):
#     """Metaclass for :class:`AdminView`."""
#
#     def __init__(cls, name, bases, d):
#         super().__init__(name, bases, d)
#         if "extension" in d:
#             cls._extension = d["extension"]
#


class AdminBaseView(MethodView):
    """Base view for admin views."""

    _extension = None
    name = None
    category = None
    endpoint = None
    template = "invenio_administration/index.html"
    url = None

    decorators = [roles_required("admin")]

    def __init__(
        self,
        name=__name__,
        category=None,
        endpoint=None,
        url=None,
        extension=None,
        admin=None,
    ):
        """Constructor."""
        if self._extension is None:
            self._extension = extension

        if self.name is None:
            self.name = name

        if self.category is None:
            self.category = category

        self.administration = admin

        self.endpoint = self._get_endpoint(endpoint)
        self.url = url or self._get_view_url(self.url)

        # Default view
        if self.get is None:
            raise Exception(
                "Cannot instantiate administration view"
                f" {self.__class__.__name__} "
                "without a default GET view"
            )

    @property
    def endpoint_location_name(self):
        """Get name for endpoint location e.g: 'administration.index'."""
        if self.administration is None:
            return self.endpoint
        return f"{self.administration.endpoint}.{self.endpoint}"

    @classmethod
    def _get_view_extension(cls, extension=None):
        """Get the flask extension of the view."""
        if extension:
            return current_app.extensions[extension]
        return current_app.extensions[cls._extension]

    def _get_endpoint(self, endpoint=None):
        """Generate Flask endpoint name.

        Defaults to class name if not provided.
        """
        if endpoint:
            return endpoint

        if not self.endpoint:
            return f"{self.name.lower()}"

    def _get_view_url(self, url):
        """Generate URL for the view. Override to change default behavior."""
        if url is None:
            if isinstance(self, self.administration.dashboard_view_class):
                url = "/"
            else:
                url = "/%s" % self.endpoint
        else:
            if not url.startswith("/"):
                url = "%s/%s" % (self.administration.url, url)

        return url

    def _get_template(self):
        return self.template

    def render(self, **kwargs):
        """Render template."""
        kwargs["admin_base_template"] = self.administration.base_template
        return render_template(self._get_template(), **kwargs)

    def get(self):
        """GET view method."""
        return self.render()


class AdminResourceBaseView(AdminBaseView):
    """Base view for admin resources."""

    display_edit = False
    display_delete = False
    resource_config = None
    resource = None
    actions = {}
    schema = None

    def __init__(
        self,
        name=__name__,
        category=None,
        endpoint=None,
        url=None,
        extension=None,
        admin=None,
    ):
        """Constructor."""
        super().__init__(name, category, endpoint, url, extension, admin)

        if self._extension is None:
            raise Exception(
                f"Cannot instanciate resource view {self.__class__.__name__} "
                f"without an associated flask extension."
            )
        if self.resource_config is None:
            raise Exception(
                f"Cannot instanciate resource view {self.__class__.__name__} "
                f"without a resource."
            )

    @classmethod
    def set_schema(cls):
        """Set schema."""
        cls.schema = cls._get_service_schema()

    @classmethod
    def set_resource(cls, extension=None):
        """Set resource."""
        cls.resource = cls._get_resource(extension)

    @classmethod
    def _get_resource(cls, extension=None):
        extension = cls._get_view_extension(extension)
        try:
            return getattr(extension, cls.resource_config)
        except AttributeError:
            raise InvalidResource(resource=cls.resource_config, view=cls.__name__)

    @classmethod
    def _get_service_schema(cls):
        # schema.schema due to the schema wrapper imposed,
        # when the actual class needed
        return cls.resource.service.schema.schema()

    def _schema_to_json(self, schema):
        return jsonify_schema(schema)

    def serialize_actions(self):
        """Serialize actions for the resource view.

        {"action_name":
        {"text": "BLA"
         #"api_endpoint": either from links.actions or provided by the resource

         If provided by resource,
         there will be no mapping on the frontend side.

         Also means we don't have links generated with permissions.
         Best to have a specialized component,
         which knows from where to read the endpoint.

         "payload_schema": schema in json

        """


class AdminResourceDetailView(AdminResourceBaseView):
    """Details view based on given config."""

    item_field_exclude_list = None
    item_field_list = None
    template = "invenio_administration/details.html"

    def get(self, pid_value=None):
        """GET view method."""
        schema = self._get_service_schema()
        serialize_schema = self._schema_to_json(schema)

        # TODO context processor?
        return self.render(**{"schema": serialize_schema})


class AdminResourceListView(AdminResourceBaseView):
    """List view based on provided resource."""

    display_create = False

    # decides if there is a detail view
    display_read = True

    search_config_name = None
    search_facets_config_name = None
    search_sort_config_name = None
    sort_options = {}
    available_facets = {}
    column_exclude_list = None
    columns = None
    template = "invenio_administration/search.html"
    search_api_endpoint = None

    search_request_headers = {"Accept": "application/vnd.inveniordm.v1+json"}

    def get_search_request_headers(self):
        """Get search request headers."""
        return self.search_request_headers

    def get_search_app_name(self):
        """Get search app name."""
        if self.search_config_name is None:
            return f"{self.name.upper()}_SEARCH"
        return self.search_config_name

    def get_search_api_endpoint(self):
        """Get search API endpoint."""
        blueprint_name = f"{self.resource.config.blueprint_name}.search"
        if self.search_api_endpoint:
            return self.search_api_endpoint

        # TODO improve fetching of the api endpoint
        blueprint_rule = (
            current_app.wsgi_app.app.mounts["/api"]
            .url_map._rules_by_endpoint[blueprint_name][0]
            .rule
        )

        api_endpoint = f"/api/{blueprint_rule}"
        return api_endpoint

    def init_search_config(self):
        """Build search view config."""
        return partial(
            search_app_config,
            config_name=self.get_search_app_name(),
            available_facets=current_app.config[self.search_facets_config_name],
            sort_options=current_app.config[self.search_sort_config_name],
            endpoint=self.get_search_api_endpoint(),
            headers=self.get_search_request_headers(),
        )

    def get_sort_options(self):
        """Get search sort options."""
        if not self.sort_options:
            return self.resource.service.config.search.sort_options
        return self.sort_options

    def get_available_facets(self):
        """Get search available facets."""
        if not self.available_facets:
            return self.resource.service.config.search.facets
        return self.available_facets

    def get(self):
        """GET view method."""
        search_conf = self.init_search_config()
        schema = self._get_service_schema()
        return self.render(
            **{
                "search_config": search_conf,
                "resource_schema": schema,
                "columns": self.columns,
            }
        )


class AdminResourceViewSet:
    """View set based on resource.

    Provides a list view and a details view given the provided configuration.
    """

    resource = None
    display_create = False

    # decides if there is a detail view
    display_read = True
    display_edit = False
    display_delete = False

    actions = None

    sort_options = ()
    available_filters = None
    column_exclude_list = None
    column_list = None

    item_field_exclude_list = None
    item_field_list = None

    list_view = None
    details_view = None

    def list_view(self):
        """List view."""
        pass

    def details_view(self):
        """Details view."""
        pass
