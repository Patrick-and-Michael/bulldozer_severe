"""Let's learn to test with neo4j!  Maybe."""
from bs.models import graph, url, password, Quest, User, Usergroup, username
from py2neo import Graph, Relationship, authenticate
import unittest

if username and password:
    authenticate(url.strip('http://'), username, password)


class TestModelMethods(unittest.TestCase):
    def setUp(self):
        self.graph = graph

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
        """Add a new user and check that the graph is updated."""
        self.user3 = User('testjim')
        self.user3.register('jimspw')
        user3_node = self.user3.get()
        user3_node.add_label('Test')
        self.graph.push(user3_node)

        self.usernode = self.graph.find_one("User", property_key="username",
                                            property_value=self.user3.username)
        self.assertEqual(self.user3.username, self.usernode['username'])

    def test_add_member_to_group(self):
        """Add user2 to usergroup1 and check that membership is updated."""
        self.usergroup1.add_member(self.user2)
        check_list = [member.username for member in self.usergroup1.find_users_by_rel('in')]
        self.assertIn(self.user2.username, check_list)
 
    def test_add_owner_to_group(self):
        """Add user2 to usergroup1 and check that membership is updated."""
        self.usergroup1.add_owner(self.user2)
        check_list = [owner.username for owner in self.usergroup1.find_users_by_rel('owns')]
        self.assertIn(self.user2.username, check_list)

    def test_new_owner_is_member_of_group(self):
        """Add user2 to usergroup1 as an owner and check that membership is updated."""
        self.usergroup1.add_owner(self.user2)
        check_list = [member.username for member in self.usergroup1.find_users_by_rel('in')]
        self.assertIn(self.user2.username, check_list)

    def test_add_quest(self):
        """Add a new quest to a usergroup."""
        self.newquest = Quest(group=self.usergroup1, questname='newquest').register(self.usergroup1, self.user1, 'newquest', {'xp': 100, 'gold': 100})
        self.newquest.quest_node.add_label('Test')
        for rel in graph.match(start_node=self.newquest.quest_node, rel_type='pays'):
            rel.end_node.add_label('Test')
        self.assertEqual(self.newquest.creator, self.user1)
        self.assertIn(('gold', 100), self.newquest.v_reward)


print('this worked')

if __name__ == '__main__':
    unittest.main()
