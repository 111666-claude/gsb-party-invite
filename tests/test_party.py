import random
import time
import unittest

from partyinvite.party import Party, PartyError, accept, invite, transfer_leader


class RefParty:
    """参考实现：只做超时校验 + 容量校验 + 去重。"""

    def __init__(self, leader, capacity):
        self.leader = leader
        self.capacity = capacity
        self.members = [leader]
        self.invites = {}


def ref_invite(party, name, now, ttl=60):
    party.invites[name] = now + ttl


def ref_accept(party, name, now):
    expire_at = party.invites.get(name)
    if expire_at is None:
        raise PartyError("no pending invite for %s" % name)
    if now > expire_at:
        raise PartyError("invite for %s expired" % name)
    if name in party.members:
        raise PartyError("%s already in party" % name)
    if len(party.members) >= party.capacity:
        raise PartyError("party is full")
    party.members.append(name)
    del party.invites[name]


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

    def test_accept_without_invite_rejected(self):
        party = Party("leader")
        with self.assertRaises(PartyError):
            accept(party, "ghost", 1)


class TimeoutTest(unittest.TestCase):
    def test_expired_invite_rejected(self):
        party = Party("leader")
        invite(party, "late", 0, ttl=30)
        with self.assertRaises(PartyError):
            accept(party, "late", 500)
        self.assertNotIn("late", party.members)
        self.assertEqual(len(party.members), 1)

    def test_boundary_still_valid(self):
        party = Party("leader")
        invite(party, "a", 0, ttl=30)
        accept(party, "a", 30)  # now == expire_at 未过期
        self.assertIn("a", party.members)

    def test_one_past_boundary_rejected(self):
        party = Party("leader")
        invite(party, "a", 0, ttl=30)
        with self.assertRaises(PartyError):
            accept(party, "a", 31)


class CapacityTest(unittest.TestCase):
    def test_full_party_rejects(self):
        party = Party("leader", capacity=4)
        for name in ("p1", "p2", "p3"):
            invite(party, name, 0)
            accept(party, name, 1)
        invite(party, "p4", 2)
        with self.assertRaises(PartyError):
            accept(party, "p4", 3)
        self.assertEqual(len(party.members), 4)
        self.assertLessEqual(len(party.members), party.capacity)

    def test_capacity_one(self):
        party = Party("leader", capacity=1)
        invite(party, "a", 0)
        with self.assertRaises(PartyError):
            accept(party, "a", 1)


class DuplicateTest(unittest.TestCase):
    def test_double_accept_rejected(self):
        party = Party("leader")
        invite(party, "a", 0)
        accept(party, "a", 1)
        with self.assertRaises(PartyError):
            accept(party, "a", 2)
        self.assertEqual(party.members.count("a"), 1)

    def test_leader_cannot_accept_own_invite(self):
        party = Party("leader")
        invite(party, "leader", 0)
        with self.assertRaises(PartyError):
            accept(party, "leader", 1)
        self.assertEqual(party.members, ["leader"])


class TransferTest(unittest.TestCase):
    def test_transfer_to_member(self):
        party = Party("leader")
        invite(party, "a", 0)
        accept(party, "a", 1)
        transfer_leader(party, "a")
        self.assertEqual(party.leader, "a")
        self.assertIn("leader", party.members)  # 原队长降为普通成员

    def test_transfer_to_non_member_rejected(self):
        party = Party("leader")
        with self.assertRaises(PartyError):
            transfer_leader(party, "outsider")
        self.assertEqual(party.leader, "leader")


class InvariantTest(unittest.TestCase):
    def test_replay_same_batch_same_result(self):
        def run():
            party = Party("leader", capacity=3)
            invite(party, "a", 0, ttl=10)
            invite(party, "b", 0, ttl=10)
            invite(party, "a", 5, ttl=10)  # 重复邀请刷新过期时间
            for name, now in (("a", 14), ("b", 20), ("c", 1)):
                try:
                    accept(party, name, now)
                except PartyError:
                    pass
            return party.members

        self.assertEqual(run(), run())

    def test_no_duplicates_and_within_capacity(self):
        party = Party("leader", capacity=4)
        for i in range(10):
            invite(party, "p%d" % i, 0)
        for i in range(10):
            try:
                accept(party, "p%d" % i, 1)
            except PartyError:
                pass
        self.assertEqual(len(party.members), len(set(party.members)))
        self.assertLessEqual(len(party.members), party.capacity)


class DifferentialTest(unittest.TestCase):
    def test_matches_reference_on_random_sequences(self):
        rng = random.Random(20260930)
        diffs = 0
        for _ in range(200):
            capacity = rng.randint(1, 6)
            mine = Party("leader", capacity=capacity)
            ref = RefParty("leader", capacity=capacity)
            names = ["n%d" % i for i in range(8)]
            now = 0
            for _ in range(rng.randint(5, 40)):
                now += rng.randint(0, 20)
                name = rng.choice(names)
                if rng.random() < 0.5:
                    ttl = rng.choice((5, 30, 60))
                    invite(mine, name, now, ttl=ttl)
                    ref_invite(ref, name, now, ttl=ttl)
                else:
                    err_mine = err_ref = None
                    try:
                        accept(mine, name, now)
                    except PartyError as exc:
                        err_mine = type(exc).__name__
                    try:
                        ref_accept(ref, name, now)
                    except PartyError as exc:
                        err_ref = type(exc).__name__
                    if err_mine != err_ref or mine.members != ref.members:
                        diffs += 1
            if mine.members != ref.members or mine.invites != ref.invites:
                diffs += 1
        self.assertEqual(diffs, 0)


class ScaleTest(unittest.TestCase):
    def test_100k_invites_accepts_under_1s(self):
        party = Party("leader", capacity=100)
        start = time.perf_counter()
        for i in range(100_000):
            invite(party, "u%d" % i, 0, ttl=10_000)
        for i in range(100_000):
            try:
                accept(party, "u%d" % i, 1)
            except PartyError:
                pass
        elapsed = time.perf_counter() - start
        self.assertEqual(len(party.members), 100)
        self.assertLess(elapsed, 1.0, "took %.3fs" % elapsed)


if __name__ == "__main__":
    unittest.main()
