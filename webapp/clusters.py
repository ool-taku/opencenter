#!/usr/bin/env python

import json
from pprint import pprint

from chef.exceptions import ChefServerError
from flask import Blueprint, Flask, Response, request
from flask import session, jsonify, url_for, current_app
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import UnmappedInstanceError

from db.database import db_session
from db.models import Nodes, Roles, Clusters
from errors import (
    http_bad_request,
    http_conflict,
    http_not_found,
    http_not_implemented)

clusters = Blueprint('clusters', __name__)


@clusters.route('/', methods=['GET', 'POST'])
def list_clusters():
    if request.method == 'POST':
        if 'name' in request.json:
            name = request.json['name']
            desc = None
            if 'description' in request.json:
                desc = request.json['description']
            config = None
            if 'config' in request.json:
                config = json.dumps(request.json['config'])
            cluster = Clusters(name=name, description=desc, config=config)
            try:
                db_session.add(cluster)
                # FIXME(rp): Transactional problem
                # NOTE(shep): setting override_attributes as part of
                #  the create, due to the lag time of chef.search
                current_app.backend.create_cluster(
                    name,
                    desc,
                    config if (config is None) else json.loads(config))
                db_session.commit()
                # have to unravel json object from the db
                cls = dict()
                for col in cluster.__table__.columns.keys():
                    if col == 'config':
                        tmp = getattr(cluster, col)
                        cls[col] = tmp if (tmp is None) else json.loads(tmp)
                    else:
                        cls[col] = getattr(cluster, col)
                href = request.base_url + str(cluster.id)
                msg = {'status': 201,
                       'message': 'Cluster Created',
                       'cluster': cls,
                       'ref': href}
                resp = jsonify(msg)
                resp.headers['Location'] = href
                resp.status_code = 201
            except IntegrityError, e:
                # This is thrown on duplicate rows
                db_session.rollback()
                return http_conflict(e)
            except ChefServerError, e:
                # This is thrown on duplicate environments
                db_session.rollback()
                return http_conflict(e)
        else:
            return http_bad_request('name')
    else:
        cluster_list = {"clusters": []}
        for row in Clusters.query.all():
            tmp = dict()
            for col in row.__table__.columns.keys():
                if col == 'config':
                    val = getattr(row, col)
                    tmp[col] = val if (val is None) else json.loads(val)
                else:
                    tmp[col] = getattr(row, col)
            cluster_list['clusters'].append(tmp)
        resp = jsonify(cluster_list)
    return resp


@clusters.route('/<cluster_id>', methods=['GET', 'PUT', 'DELETE', 'PATCH'])
def cluster_by_id(cluster_id):
    if request.method == 'PATCH' or request.method == 'POST':
        return http_not_implemented()
    elif request.method == 'PUT':
        r = Clusters.query.filter_by(id=cluster_id).first()
        # FIXME(rp): renames break the backend association
        if 'name' in request.json:
            r.name = request.json['name']
        if 'description' in request.json:
            r.description = request.json['description']
        if 'config' in request.json:
            r.config = json.dumps(request.json['config'])
        #TODO(shep): this is an un-excepted db call
        db_session.commit()
        cls = dict()
        for c in r.__table__.columns.keys():
            if c == 'config':
                cls[c] = json.loads(getattr(r, c))
            else:
                cls[c] = getattr(r, c)
        resp = jsonify(cls)
    elif request.method == 'DELETE':
        r = Clusters.query.filter_by(id=cluster_id).first()
        try:
            db_session.delete(r)
            db_session.commit()

            # FIXME(rp): Transaction
            current_app.backend.delete_cluster(r.name)

            msg = {'status': 200, 'message': 'Cluster deleted'}

            resp = jsonify(msg)
            resp.status_code = 200
        except UnmappedInstanceError, e:
            return http_not_found()
    else:
        r = Clusters.query.filter_by(id=cluster_id).first()
        if r is None:
            return http_not_found()
        else:
            cls = dict()
            for c in r.__table__.columns.keys():
                if c == 'config':
                    cls[c] = json.loads(getattr(r, c))
                else:
                    cls[c] = getattr(r, c)
            resp = jsonify(cls)
    return resp
