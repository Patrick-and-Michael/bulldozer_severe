"""Let's learn to test with neo4j!  Maybe."""
from bs.models import url, password, Quest, User, Usergroup, username
from py2neo import Graph, Relationship, authenticate
import unittest

if username and password:
    authenticate(url.strip('http://'), username, password)


class TestQuestMethods(unittest.TestCase):
    def setUp(self):
        self.graph = Graph('{}/db/test/'.format(url))

        self.user1 = User('testdoug')
        self.user2 = User('testbob')

        self.user1.register('dougspw')
        self.user2.register('bobspw')

        self.usergroup1 = Usergroup(groupname='testgroup',
                                    session={'username': self.user1.username})
        self.usergroup1.register(self.user1)

        for obj in [self.user1, self.user2, self.usergroup1]:
            node = obj.get()
            node.add_label('Test')
            self.graph.push(node)

    def tearDown(self):
        """Delete all 'test' nodes."""
        self.graph.run("MATCH (n:Test) DETACH DELETE n")

    def test_new_user(self):
        self.user3 = User('testjim')
        self.user3.register('jimspw')
        user3_node = self.user3.get()
        user3_node.add_label('Test')
        self.graph.push(user3_node)

        self.usernode = self.graph.find_one("User", property_key="username",
                                            property_value=self.user3.username)
        self.assertEqual(self.user3.username, self.usernode['username'])


print('this worked')

if __name__ == '__main__':
    unittest.main()
