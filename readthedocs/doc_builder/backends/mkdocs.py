import re
import fnmatch
import os
import logging
import json
import yaml

from django.conf import settings
from django.template import Context, loader as template_loader

from doc_builder.base import BaseBuilder, restoring_chdir
from search.utils import parse_content_from_file, parse_headers_from_file, parse_sections_from_file
from projects.utils import run
from projects.constants import LOG_TEMPLATE
from tastyapi import apiv2

log = logging.getLogger(__name__)

TEMPLATE_DIR = '%s/readthedocs/templates/mkdocs/readthedocs' % settings.SITE_ROOT
OVERRIDE_TEMPLATE_DIR = '%s/readthedocs/templates/mkdocs/overrides' % settings.SITE_ROOT


class BaseMkdocs(BaseBuilder):

    """
    Mkdocs builder
    """

    def __init__(self, *args, **kwargs):
        super(BaseMkdocs, self).__init__(*args, **kwargs)
        self.old_artifact_path = os.path.join(self.version.project.checkout_path(self.version.slug), self.build_dir)

    def append_conf(self, **kwargs):
        """
        Set mkdocs config values
        """

        # Pull mkdocs config data
        try:
            user_config = yaml.safe_load(open('mkdocs.yml', 'r'))
        except IOError:
            user_config = {
                'site_name': self.version.project.name,
            }

        # Handle custom docs dirs

        docs_dir = self.docs_dir(docs_dir=user_config.get('docs_dir'))
        self.create_index(extension='md')
        user_config['docs_dir'] = docs_dir

        # Set mkdocs config values

        MEDIA_URL = getattr(settings, 'MEDIA_URL', 'https://media.readthedocs.org')

        # Mkdocs needs a full domain here because it tries to link to local media files
        if not MEDIA_URL.startswith('http'):
            MEDIA_URL = 'http://localhost:8000' + MEDIA_URL

        if 'extra_javascript' in user_config:
            user_config['extra_javascript'].append('readthedocs-data.js')
            user_config['extra_javascript'].append(
                'readthedocs-dynamic-include.js')
            user_config['extra_javascript'].append(
                '%sjavascript/readthedocs-doc-embed.js' % MEDIA_URL)
        else:
            user_config['extra_javascript'] = [
                'readthedocs-data.js',
                'readthedocs-dynamic-include.js',
                '%sjavascript/readthedocs-doc-embed.js' % MEDIA_URL,
            ]

        if 'extra_css' in user_config:
            user_config['extra_css'].append(
                '%s/css/badge_only.css' % MEDIA_URL)
            user_config['extra_css'].append(
                '%s/css/readthedocs-doc-embed.css' % MEDIA_URL)
        else:
            user_config['extra_css'] = [
                '%scss/badge_only.css' % MEDIA_URL,
                '%scss/readthedocs-doc-embed.css' % MEDIA_URL,
            ]

        if 'pages' not in user_config:
            user_config['pages'] = []
            for root, dirnames, filenames in os.walk(docs_dir):
                for filename in filenames:
                    if fnmatch.fnmatch(filename, '*.md') or fnmatch.fnmatch(filename, '*.markdown'):
                        if docs_dir != '.':
                            root_path = root.replace(docs_dir, '')
                            full_path = os.path.join(root_path, filename.lstrip('/')).lstrip('/')
                        else:
                            if root == '.':
                                root_path = ''
                            else:
                                root_path = re.sub('^./', '', root)
                            full_path = os.path.join(root_path, filename.lstrip('/')).lstrip('/')
                        user_config['pages'].append([full_path])

        # Set our custom theme dir for mkdocs
        if 'theme_dir' not in user_config:
            user_config['theme_dir'] = TEMPLATE_DIR

        yaml.dump(user_config, open('mkdocs.yml', 'w'))

        # RTD javascript writing

        READTHEDOCS_DATA = {
            'project': self.version.project.slug,
            'version': self.version.slug,
            'language': self.version.project.language,
            'page': None,
            'theme': "readthedocs",
            'builder': "mkdocs",
            'docroot': docs_dir,
            'source_suffix': ".md",
            'api_host': getattr(settings, 'SLUMBER_API_HOST', 'https://readthedocs.org'),
            'commit': self.version.project.vcs_repo(self.version.slug).commit,
        }
        data_json = json.dumps(READTHEDOCS_DATA, indent=4)
        data_ctx = Context({
            'data_json': data_json,
            'current_version': READTHEDOCS_DATA['version'],
            'slug': READTHEDOCS_DATA['project'],
            'html_theme': READTHEDOCS_DATA['theme'],
            'pagename': None,
        })
        data_string = template_loader.get_template(
            'doc_builder/data.js.tmpl'
        ).render(data_ctx)

        data_file = open(os.path.join(docs_dir, 'readthedocs-data.js'), 'w+')
        data_file.write(data_string)
        data_file.write('\nREADTHEDOCS_DATA["page"] = mkdocs_page_name')
        data_file.close()

        include_ctx = Context({
            'global_analytics_code': getattr(settings, 'GLOBAL_ANALYTICS_CODE', 'UA-17997319-1'),
            'user_analytics_code': self.version.project.analytics_code,
        })
        include_string = template_loader.get_template(
            'doc_builder/include.js.tmpl'
        ).render(include_ctx)
        include_file = open(os.path.join(docs_dir, 'readthedocs-dynamic-include.js'), 'w+')
        include_file.write(include_string)
        include_file.close()

    @restoring_chdir
    def build(self, **kwargs):
        checkout_path = self.version.project.checkout_path(self.version.slug)
        #site_path = os.path.join(checkout_path, 'site')
        os.chdir(checkout_path)
        # Actual build
        build_command = "{command} {builder} --site-dir={build_dir} --theme=readthedocs".format(
            command=self.version.project.venv_bin(version=self.version.slug, bin='mkdocs'),
            builder=self.builder,
            build_dir=self.build_dir,
        )
        results = run(build_command, shell=True)
        return results


class MkdocsHTML(BaseMkdocs):
    type = 'mkdocs'
    builder = 'build'
    build_dir = '_build/html'


class MkdocsJSON(BaseMkdocs):
    type = 'mkdocs_json'
    builder = 'json'
    build_dir = '_build/json'
