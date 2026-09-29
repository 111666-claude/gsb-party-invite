import random
import time
import unittest

from partyinvite.party import Party, PartyError, accept, invite, transfer_leader


class InviteTest(unittest.TestCase):
    def test_invite_recorded(self):
        party = Party("leader")
        invite(party, "a", 0, ttl=60)
        self.assertEqual(party.invites["a"], 60)

    def test_leader_is_member(self):
        self.assertEqual(Party("leader").members, ["leader"])

    def test_error_type(self):
        self.assertTrue(issubclass(PartyError, ValueError))

    def test_invite_existing_member_rejected(self):
        party = Party("leader")
        with self.assertRaises(PartyError):
            invite(party, "leader", 0)

    def test_duplicate_pending_invite_rejected(self):
        party = Party("leader")
        invite(party, "a", 0, ttl=60)
        with self.assertRaises(PartyError):
            invite(party, "a", 10)
        self.assertEqual(party.invites["a"], 60)

    def test_reinvite_after_expiry_allowed(self):
        party = Party("leader")
        invite(party, "a", 0, ttl=10)
        invite(party, "a", 100, ttl=10)
        self.assertEqual(party.invites["a"], 110)

    def test_invite_when_full_rejected(self):
        party = Party("leader", capacity=2)
        invite(party, "a", 0)
        accept(party, "a", 1)
        with self.assertRaises(PartyError):
            invite(party, "b", 1)


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

    def test_expired_invite_rejected(self):
        party = Party("leader")
        invite(party, "late", 0, ttl=30)
        with self.assertRaises(PartyError):
            accept(party, "late", 500)
        self.assertEqual(party.members, ["leader"])
        self.assertNotIn("late", party.invites)

    def test_accept_at_exact_expiry_allowed(self):
        party = Party("leader")
        invite(party, "a", 0, ttl=30)
        accept(party, "a", 30)
        self.assertIn("a", party.members)

    def test_accept_without_invite_rejected(self):
        party = Party("leader")
        with self.assertRaises(PartyError):
            accept(party, "ghost", 0)

    def test_full_party_rejects_join(self):
        party = Party("leader", capacity=4)
        for name in ("p1", "p2", "p3"):
            invite(party, name, 0)
            accept(party, name, 1)
        # 满员后邀请本身也会被拒绝，直接构造邀请再接受来验证 accept 的容量检查
        party.invites["p4"] = 100
        with self.assertRaises(PartyError):
            accept(party, "p4", 3)
        self.assertEqual(len(party.members), 4)
        self.assertLessEqual(len(party.members), party.capacity)

    def test_duplicate_accept_rejected(self):
        party = Party("leader")
        invite(party, "a", 0)
        accept(party, "a", 1)
        with self.assertRaises(PartyError):
            accept(party, "a", 2)
        self.assertEqual(party.members.count("a"), 1)
        self.assertEqual(len(party.members), len(set(party.members)))


class TransferTest(unittest.TestCase):
    def test_transfer_to_member(self):
        party = Party("leader")
        invite(party, "a", 0)
        accept(party, "a", 1)
        transfer_leader(party, "a")
        self.assertEqual(party.leader, "a")
        self.assertIn("leader", party.members)  # 原队长降为普通成员
        self.assertEqual(len(party.members), 2)

    def test_transfer_to_non_member_rejected(self):
        party = Party("leader")
        with self.assertRaises(PartyError):
            transfer_leader(party, "ghost")
        self.assertEqual(party.leader, "leader")


class RefParty:
    """参考实现：只做超时校验 + 容量校验 + 去重。"""

    def __init__(self, leader, capacity):
        self.leader = leader
        self.capacity = capacity
        self.members = [leader]
        self.invites = {}

    def invite(self, name, now, ttl=60):
        if name in self.members:
            raise PartyError("member")
        exp = self.invites.get(name)
        if exp is not None and now <= exp:
            raise PartyError("pending")
        if len(self.members) >= self.capacity:
            raise PartyError("full")
        self.invites[name] = now + ttl

    def accept(self, name, now):
        if name in self.members:
            raise PartyError("dup")
        exp = self.invites.get(name)
        if exp is None:
            raise PartyError("no invite")
        if now > exp:
            del self.invites[name]
            raise PartyError("expired")
        if len(self.members) >= self.capacity:
            raise PartyError("full")
        self.members.append(name)
        del self.invites[name]


def random_ops(rng, capacity, count):
    names = ["n%d" % i for i in range(capacity + 2)]
    ops = []
    now = 0
    for _ in range(count):
        now += rng.choice([0, 1, 5, 50])
        kind = rng.choice(["invite", "accept"])
        if kind == "invite":
            ops.append(("invite", rng.choice(names), now, rng.choice([1, 10, 60])))
        else:
            ops.append(("accept", rng.choice(names), now, None))
    return ops


def run_ops(ops, capacity, impl):
        party = impl("leader", capacity)
        errors = []
        for kind, name, now, ttl in ops:
            try:
                if kind == "invite":
                    if impl is Party:
                        invite(party, name, now, ttl=ttl)
                    else:
                        party.invite(name, now, ttl=ttl)
                else:
                    if impl is Party:
                        accept(party, name, now)
                    else:
                        party.accept(name, now)
                errors.append(None)
            except PartyError:
                errors.append(kind)
        return party, errors


class DifferentialTest(unittest.TestCase):
    def test_matches_reference_200_sequences(self):
        rng = random.Random(20260930)
        for _ in range(200):
            capacity = rng.randint(2, 6)
            ops = random_ops(rng, capacity, rng.randint(10, 60))
            got, got_err = run_ops(ops, capacity, Party)
            ref, ref_err = run_ops(ops, capacity, RefParty)
            self.assertEqual(got.members, ref.members)
            self.assertEqual(got.invites, ref.invites)
            self.assertEqual(got_err, ref_err)
            self.assertEqual(len(got.members), len(set(got.members)))
            self.assertLessEqual(len(got.members), capacity)

    def test_replay_is_deterministic(self):
        rng = random.Random(7)
        ops = random_ops(rng, 4, 100)
        first, first_err = run_ops(ops, 4, Party)
        second, second_err = run_ops(ops, 4, Party)
        self.assertEqual(first.members, second.members)
        self.assertEqual(first.invites, second.invites)
        self.assertEqual(first_err, second_err)


class ScaleTest(unittest.TestCase):
    def test_100_members_100k_ops_under_1s(self):
        party = Party("leader", capacity=100)
        start = time.perf_counter()
        for i in range(99):
            invite(party, "m%d" % i, 0)
            accept(party, "m%d" % i, 1)
        now = 10
        for i in range(100000):
            name = "x%d" % (i % 1000)
            try:
                invite(party, name, now, ttl=5)
            except PartyError:
                pass
            try:
                accept(party, name, now + 10)  # 已过期
            except PartyError:
                pass
            now += 1
        elapsed = time.perf_counter() - start
        self.assertEqual(len(party.members), 100)
        self.assertEqual(len(party.members), len(set(party.members)))
        self.assertLessEqual(len(party.members), party.capacity)
        self.assertLess(elapsed, 1.0, "100k invite/accept took %.3fs" % elapsed)


if __name__ == "__main__":
    unittest.main()
