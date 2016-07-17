"""Let's learn to test with neo4j!  Maybe."""
from bs.models import url, password, Quest, User, Usergroup, username
from py2neo import Graph, Relationship, authenticate
import unittest
import tempfile

if username and password:
    authenticate(url.strip('http://'), username, password)

class TestQuestMethods(unittest.TestCase):
    def setUp(self):
        self.graph = Graph('{}/db/test/'.format(url))
        self.user1 = User('testdoug').register('dougspw')
        self.user2 = User('testbob').register('bobspw')
        self.usergroup1 = Usergroup(groupname='testgroup', session=self.user1).register(self.user1)

    def tearDown(self):
        self.graph.run("MATCH (n) DETACH DELETE n")
        self.graph.unbind()

    def test_new_user(self):
        self.user3 = User('testjim').register('jimspw')
        self.usernode = self.graph.find_one("User", property_key="username", property_value=self.user3.username)
        self.assertEqual(self.user3.username, self.usernode['username'])


print('this worked')

if __name__ == '__main__':
    unittest.main()
