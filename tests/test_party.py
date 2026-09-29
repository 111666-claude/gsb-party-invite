import unittest

from partyinvite.party import Party, PartyError, accept, invite


class InviteTest(unittest.TestCase):
    def test_invite_recorded(self):
        party = Party("leader")
        invite(party, "a", 0, ttl=60)
        self.assertEqual(party.invites["a"], 60)

    def test_leader_is_member(self):
        self.assertEqual(Party("leader").members, ["leader"])

    def test_error_type(self):
        self.assertTrue(issubclass(PartyError, ValueError))


class AcceptTest(unittest.TestCase):
    def test_accept_adds_member(self):
        party = Party("leader")
        invite(party, "a", 0)
        accept(party, "a", 1)
        self.assertIn("a", party.members)

    def test_accept_clears_invite(self):
        party = Party("leader")
        invite(party, "a", 0)
        accept(party, "a", 1)
        self.assertNotIn("a", party.invites)


if __name__ == "__main__":
    unittest.main()
