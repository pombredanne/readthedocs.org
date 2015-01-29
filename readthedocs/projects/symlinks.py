import os
import logging

from django.conf import settings
import redis

from core.utils import run_on_app_servers
from projects.constants import LOG_TEMPLATE
from tastyapi import apiv2

log = logging.getLogger(__name__)


def symlink_cnames(version):
    """
    OLD
    Link from HOME/user_builds/cnames/<cname> ->
              HOME/user_builds/<project>/rtd-builds/
    NEW
    Link from HOME/user_builds/cnametoproject/<cname> ->
              HOME/user_builds/<project>/
    """
    try:
        redis_conn = redis.Redis(**settings.REDIS)
        cnames = redis_conn.smembers('rtd_slug:v1:%s' % version.project.slug)
    except redis.ConnectionError:
        log.error(LOG_TEMPLATE.format(project=version.project.slug, version=version.slug, msg='Failed to symlink cnames, Redis error.'), exc_info=True)
        return
    for cname in cnames:
        log.debug(LOG_TEMPLATE.format(project=version.project.slug, version=version.slug, msg="Symlinking CNAME: %s" % cname))
        docs_dir = version.project.rtd_build_path(version.slug)
        # Chop off the version from the end.
        docs_dir = '/'.join(docs_dir.split('/')[:-1])
        # Old symlink location -- Keep this here til we change nginx over
        symlink = version.project.cnames_symlink_path(cname)
        run_on_app_servers('mkdir -p %s' % '/'.join(symlink.split('/')[:-1]))
        run_on_app_servers('ln -nsf %s %s' % (docs_dir, symlink))
        # New symlink location
        new_docs_dir = version.project.doc_path
        new_cname_symlink = os.path.join(getattr(settings, 'SITE_ROOT'), 'cnametoproject', cname)
        run_on_app_servers('mkdir -p %s' % '/'.join(new_cname_symlink.split('/')[:-1]))
        run_on_app_servers('ln -nsf %s %s' % (new_docs_dir, new_cname_symlink))


def symlink_subprojects(version):
    """
    Link from HOME/user_builds/project/subprojects/<project> ->
              HOME/user_builds/<project>/rtd-builds/
    """
    # Subprojects
    if getattr(settings, 'DONT_HIT_DB', True):
        subproject_slugs = [data['slug'] for data in apiv2.project(version.project.pk).subprojects.get()['subprojects']]
    else:
        rels = version.project.subprojects.all()
        subproject_slugs = [rel.child.slug for rel in rels]
    for slug in subproject_slugs:
        slugs = [slug]
        if '_' in slugs[0]:
            slugs.append(slugs[0].replace('_', '-'))
        for subproject_slug in slugs:
            log.debug(LOG_TEMPLATE.format(project=version.project.slug, version=version.slug, msg="Symlinking subproject: %s" % subproject_slug))

            # The directory for this specific subproject
            symlink = version.project.subprojects_symlink_path(subproject_slug)
            run_on_app_servers('mkdir -p %s' % '/'.join(symlink.split('/')[:-1]))

            # Where the actual docs live
            docs_dir = os.path.join(settings.DOCROOT, subproject_slug, 'rtd-builds')
            run_on_app_servers('ln -nsf %s %s' % (docs_dir, symlink))


def symlink_translations(version):
    """
    Link from HOME/user_builds/project/translations/<lang> ->
              HOME/user_builds/<project>/rtd-builds/
    """
    translations = {}

    if getattr(settings, 'DONT_HIT_DB', True):
        for trans in (apiv2
                      .project(version.project.pk)
                      .translations.get()['translations']):
            translations[trans['language']] = trans['slug']
    else:
        for trans in version.project.translations.all():
            translations[trans.language] = trans.slug

    # Default language, and pointer for 'en'
    version_slug = version.project.slug.replace('_', '-')
    translations[version.project.language] = version_slug
    if not translations.has_key('en'):
        translations['en'] = version_slug

    run_on_app_servers(
        'mkdir -p {0}'
        .format(os.path.join(version.project.doc_path, 'translations')))

    for (language, slug) in translations.items():
        log.debug(LOG_TEMPLATE.format(
            project=version.project.slug,
            version=version.slug,
            msg="Symlinking translation: %s->%s" % (language, slug)
        ))

        # The directory for this specific translation
        symlink = version.project.translations_symlink_path(language)
        translation_path = os.path.join(settings.DOCROOT, slug, 'rtd-builds')
        run_on_app_servers('ln -nsf {0} {1}'.format(translation_path, symlink))


def symlink_single_version(version):
    """
    Link from HOME/user_builds/<project>/single_version ->
              HOME/user_builds/<project>/rtd-builds/<default_version>/
    """
    default_version = version.project.get_default_version()
    log.debug(LOG_TEMPLATE.format(project=version.project.slug, version=default_version, msg="Symlinking single_version"))

    # The single_version directory
    symlink = version.project.single_version_symlink_path()
    run_on_app_servers('mkdir -p %s' % '/'.join(symlink.split('/')[:-1]))

    # Where the actual docs live
    docs_dir = os.path.join(settings.DOCROOT, version.project.slug, 'rtd-builds', default_version)
    run_on_app_servers('ln -nsf %s %s' % (docs_dir, symlink))


def remove_symlink_single_version(version):
    """Remove single_version symlink"""
    log.debug(LOG_TEMPLATE.format(
        project=version.project.slug,
        version=version.project.get_default_version(),
        msg="Removing symlink for single_version")
    )
    symlink = version.project.single_version_symlink_path()
    run_on_app_servers('rm -f %s' % symlink)
