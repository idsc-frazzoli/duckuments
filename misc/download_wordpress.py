#!/usr/bin/env python
import sys
import traceback

from mcdp_docs import logger

try:
    import yaml
    import MySQLdb

    # Open database connection
    db = MySQLdb.connect("frankfurt.co-design.science",
                         "readonly", "readonly", "duckietown_wp1")

    # prepare a cursor object using cursor() method

    cursor = db.cursor()
    cmd = 'SELECT ID, user_login, display_name FROM wp_users;';
    # execute SQL query using execute() method.
    cursor.execute(cmd)
    n = cursor.rowcount

    users = {}
    id2user = {}
    for ID, user_login, display_name in cursor.fetchall():
        display_name = display_name.strip()
        id2user[ID] = user_login
        user_url = 'https://www.duckietown.org/community/pm_profile?uid=%s' % ID
        users[user_login] = dict(name=display_name, user_url=user_url)
    #
    # print yaml.dump(id2user)
    # print yaml.dump(users)

    cmd = 'SELECT ID, post_date, post_title, post_type, post_name, post_author FROM wp_posts WHERE post_status = "publish"';
    # execute SQL query using execute() method.
    cursor.execute(cmd)

    post_name2post = {}
    id2post_name = {}
    for data in cursor.fetchall():
        id_, post_date, post_title, post_type, post_name, post_author = data
        id_ = int(id_)
        if post_author not in id2user:
            logger.info('Could not find author for post "%s"' % post_title)
            author = None
        else:
            author = id2user[post_author]

        url = 'https://www.duckietown.org/?p=%s' % id_
        id2post_name[id_] = post_name
        post_name2post[post_name] = dict(date=post_date, type=post_type,
                                         title=post_title, url=url, author=author, tags=[])

    id2term = {}
    cmd = 'SELECT term_id, name, slug FROM `wp_terms`;'
    cursor.execute(cmd)
    for term_id, name, slug in cursor.fetchall():
        term_id = int(term_id)
        id2term[term_id] = dict(name=name, slug=slug)

    cmd = 'SELECT object_id, term_taxonomy_id FROM `wp_term_relationships`;'
    cursor.execute(cmd)
    for object_id, term_taxonomy_id in cursor.fetchall():
        object_id = int(object_id)
        term_taxonomy_id = int(term_taxonomy_id)

        if object_id in id2post_name:
            post_name = id2post_name[object_id]
            if term_taxonomy_id in id2term:
                slug = id2term[term_taxonomy_id]['slug']
                post_name2post[post_name]['tags'].append(slug)
            else:
                logger.info('Could not find %r in id2term: %s ' % (term_taxonomy_id, id2term))
        else:
            pass
            # logger.info('Could not find object_id %r in id2post: %s' % (object_id, list(id2post_name)))

    results = {}

    results['users'] = users
    results['posts'] = post_name2post

    print yaml.dump(results)

    # disconnect from server
    db.close()
except Exception as e:
    logger.error(traceback.format_exc(e))
    sys.exit(2)
