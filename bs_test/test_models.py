"""Let's learn to test with neo4j!  Maybe."""
import os
from ..bs.models import graph, Quest, User, Usergroup
import unittest
import tempfile


class TestQuestMethods(unittest.TestCase):
    def setup(self):
        self.user1 = User()


print('this worked')

if __name__ == '__main__':
    unittest.main()
