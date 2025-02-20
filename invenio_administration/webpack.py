# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2022 CERN.
# Copyright (C) 2019-2022 Northwestern University.
# Copyright (C)      2022 TU Wien.
# Copyright (C)      2022 Graz University of Technology.
#
# Invenio App RDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""JS/CSS Webpack bundles for theme."""

from invenio_assets.webpack import WebpackThemeBundle

theme = WebpackThemeBundle(
    __name__,
    "assets",
    default="semantic-ui",
    themes={
        "semantic-ui": dict(
            entry={
                "invenio-administration-search":
                    "./js/invenio_administration/search/search.js",
                "base-admin-theme":
                    "./js/invenio_administration/theme.js"
            },
            dependencies={
                "@babel/runtime": "^7.9.0",
                "i18next": "^20.3.0",
                "i18next-browser-languagedetector": "^6.1.0",
                "luxon": "^1.23.0",
                "path": "^0.12.7",
                "prop-types": "^15.7.2",
                "react-copy-to-clipboard": "^5.0.0",
                "react-i18next": "^11.11.0",
                "react-invenio-forms": "^0.10.0",
                "react-searchkit": "^2.0.0",
                "yup": "^0.32.0",
            },
            aliases={
                # Define Semantic-UI theme configuration needed by
                # Invenio-Theme in order to build Semantic UI (in theme.js
                # entry point). theme.config itself is provided by
                # cookiecutter-invenio-rdm.
                "@js/invenio_administration": "js/invenio_administration",
                "@translations/invenio_administration":
                    "translations/invenio_administration",
            },
        ),
    },
)
