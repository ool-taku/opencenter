# vim: tabstop=4 shiftwidth=4 softtabstop=4
import json
import os
import random
import roush
import string
import unittest
import tempfile
import time

from test_roush import RoushTestCase
from setup import RoushTest

from db.database import init_db
import webapp


def _randomStr(size):
    return "".join(random.choice(string.ascii_lowercase) for x in range(size))


class ClusterCreateTests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.foo = webapp.Thing('roush', configfile='local.conf', debug=True)
        init_db(self.foo.config['database_uri'])
        self.app = self.foo.test_client()
        self.name = _randomStr(10)
        self.desc = _randomStr(30)
        self.attribs = {_randomStr(5): _randomStr(10),
                        _randomStr(5): {_randomStr(5): _randomStr(10)},
                        _randomStr(5): [_randomStr(10), _randomStr(10)]}
        self.content_type = 'application/json'
        self.shep = 30

    def test_create_cluster_with_desc_and_override_attributes(self):
        data = {'name': self.name,
                'description': self.desc,
                'config': self.attribs}
        resp = self.app.post('/clusters/',
                             content_type=self.content_type,
                             data=json.dumps(data))
        self.assertEquals(resp.status_code, 201)
        out = json.loads(resp.data)
        self.assertEquals(out['status'], 201)
        self.assertEquals(out['message'], 'Cluster Created')
        self.assertEquals(out['cluster']['name'], self.name)
        self.assertEquals(out['cluster']['description'], self.desc)
        self.assertEquals(out['cluster']['config'], self.attribs)

        # Cleanup the cluster we created
        if self.foo.config['backend'] != "null":
            time.sleep(2 * self.shep)  # chef-solr indexing can be slow
        resp = self.app.delete('/clusters/%s' % out['cluster']['id'],
                               content_type=self.content_type)
        self.assertEquals(resp.status_code, 200)
        out = json.loads(resp.data)
        self.assertEquals(out['status'], 200)
        self.assertEquals(out['message'], 'Cluster deleted')

    def test_create_cluster_with_desc_and_no_override_attributes(self):
        data = {'name': self.name,
                'description': self.desc}
        resp = self.app.post('/clusters/',
                             content_type=self.content_type,
                             data=json.dumps(data))
        self.assertEquals(resp.status_code, 201)
        out = json.loads(resp.data)
        self.assertEquals(out['status'], 201)
        self.assertEquals(out['message'], 'Cluster Created')
        self.assertEquals(out['cluster']['name'], self.name)
        self.assertEquals(out['cluster']['description'], self.desc)
        self.assertEquals(out['cluster']['config'], None)

        # Cleanup the cluster we created
        if self.foo.config['backend'] != "null":
            time.sleep(2 * self.shep)  # chef-solr indexing can be slow
        resp = self.app.delete('/clusters/%s' % out['cluster']['id'],
                               content_type=self.content_type)
        self.assertEquals(resp.status_code, 200)
        out = json.loads(resp.data)
        self.assertEquals(out['status'], 200)
        self.assertEquals(out['message'], 'Cluster deleted')

    def test_create_cluster_with_override_attributes_and_no_desc(self):
        data = {'name': self.name,
                'config': self.attribs}
        resp = self.app.post('/clusters/',
                             content_type=self.content_type,
                             data=json.dumps(data))
        self.assertEquals(resp.status_code, 201)
        out = json.loads(resp.data)
        self.assertEquals(out['status'], 201)
        self.assertEquals(out['message'], 'Cluster Created')
        self.assertEquals(out['cluster']['name'], self.name)
        self.assertEquals(out['cluster']['description'], None)
        self.assertEquals(out['cluster']['config'], self.attribs)

        # Cleanup the cluster we created
        if self.foo.config['backend'] != "null":
            time.sleep(2 * self.shep)  # chef-solr indexing can be slow
        resp = self.app.delete('/clusters/%s' % out['cluster']['id'],
                               content_type=self.content_type)
        self.assertEquals(resp.status_code, 200)
        out = json.loads(resp.data)
        self.assertEquals(out['status'], 200)
        self.assertEquals(out['message'], 'Cluster deleted')

    def test_create_cluster_with_no_desc_and_no_override_attributes(self):
        data = {'name': self.name}
        resp = self.app.post('/clusters/',
                             content_type=self.content_type,
                             data=json.dumps(data))
        self.assertEquals(resp.status_code, 201)
        out = json.loads(resp.data)
        self.assertEquals(out['status'], 201)
        self.assertEquals(out['message'], 'Cluster Created')
        self.assertEquals(out['cluster']['name'], self.name)
        self.assertEquals(out['cluster']['description'], None)
        self.assertEquals(out['cluster']['config'], None)

        # Cleanup the cluster we created
        if self.foo.config['backend'] != "null":
            time.sleep(2 * self.shep)  # chef-solr indexing can be slow
        resp = self.app.delete('/clusters/%s' % out['cluster']['id'],
                               content_type=self.content_type)
        self.assertEquals(resp.status_code, 200)
        out = json.loads(resp.data)
        self.assertEquals(out['status'], 200)
        self.assertEquals(out['message'], 'Cluster deleted')

    def test_create_cluster_without_name(self):
        data = {'description': self.desc,
                'config': self.attribs}
        resp = self.app.post('/clusters/',
                             content_type=self.content_type,
                             data=json.dumps(data))
        self.assertEquals(resp.status_code, 400)
        out = json.loads(resp.data)
        self.assertEquals(out['status'], 400)
        self.assertTrue('was not provided' in out['message'])


class ClusterUpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.foo = webapp.Thing('roush', configfile='local.conf', debug=True)
        init_db(self.foo.config['database_uri'])
        self.app = self.foo.test_client()
        self.name = _randomStr(10)
        self.desc = _randomStr(30)
        self.attribs = {"package_component": "essex-final",
                        "monitoring": {"metric_provider": "null"}}
        self.content_type = 'application/json'
        self.shep = 30
        self.create_data = {'name': self.name,
                            'description': self.desc,
                            'config': self.attribs}
        tmp = self.app.post('/clusters/',
                            content_type=self.content_type,
                            data=json.dumps(self.create_data))
        self.json = json.loads(tmp.data)
        self.cluster_id = self.json['cluster']['id']
        if self.foo.config['backend'] != 'null':
            time.sleep(2 * self.shep)  # chef-solr indexing can be slow

    def test_update_cluster_with_description_and_override_attributes(self):
        pass

    def test_update_cluster_with_description_and_no_override_attributes(self):
        pass

    def test_update_cluster_with_override_attributes_and_no_description(self):
        pass

    def test_update_cluster_with_no_data(self):
        pass

    @classmethod
    def tearDownClass(self):
        tmp_resp = self.app.delete('/clusters/%s' + str(self.cluster_id),
                                   content_type=self.content_type)


#class ClusterTestCase(RoushTest):
#
#    @classmethod
#    def setup(cls):
#         # Create a cluster
#        cls.cluster_name = _randomStr(10)
#        cls.cluster_desc = _randomStr(30)
#        cluster_data = {"name": cls.cluster_name,
#                            "description": cls.cluster_desc}
#        tmp = cls.app.post('/clusters/', data=json.dumps(cluster_data),
#                            content_type='application/json')
#        assert tmp.status_code == 201,\
#            "Unable to create cluster %s" % cluster_name
#        cls.cluster_json = json.loads(tmp.data)
#        cls.cluster_id = cls.cluster_json['cluster']['id']
#
#    @classmethod
#    def cleanup(cls):
#        # Delete our test cluster
#        tmp = cls.app.delete('/clusters/%s' % cls.cluster_id)
#        assert tmp.status_code == 200, "Status code %s is not 200" % (
#            tmp.status_code)
#        data = json.loads(tmp.data)
#        assert data['status'] == tmp.status_code,\
#            "Status %s returned in data does not match response code %s" % (
#                data['status'], tmp.status_code)
#        assert data['message'] == 'Cluster deleted',\
#            "Message %s is not Cluster deleted" % (data['message'])
#
#    def test_create_cluster(self):
#        #cluster is created in setup.  We should verify it is created
#        #as expected.
#        response = self.app.get("/clusters/%s" % (self.cluster_id))
#        cluster = json.loads(response.data)
#        self.assertEqual(response.status_code, 200)
#        self.assertEqual(self.cluster_id, cluster['id'])
#        self.assertEqual(self.cluster_name, cluster['name'])
#        self.assertEqual(self.cluster_desc, cluster['description'])
#
#    def test_update_cluster(self):
#        # update cluster attributes
#        new_desc = "updated description"
#        new_cluster = {"description": new_desc}
#        resp = self.app.put('/clusters/%s' % self.cluster_id,
#                            data=json.dumps(new_cluster),
#                            content_type='application/json')
#        self.assertEqual(resp.status_code, 200)
#        tmp_data = json.loads(resp.data)
#        self.assertEqual(tmp_data['description'], new_desc)
#
#
#if __name__ == '__main__':
#    unittest.main()
