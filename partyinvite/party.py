"""组队邀请状态机：邀请、超时、满员与队长转移。"""


class PartyError(ValueError):
    """输入不合法。"""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class Party:
    """一支队伍。"""

    def __init__(self, leader, capacity=4):
        self.leader = leader
        self.capacity = capacity
        self.members = [leader]
        self._member_set = {leader}
        self.invites = {}


def invite(party, name, now, ttl=60):
    """发出邀请，记录过期时间；重复邀请只刷新过期时间。"""
    party.invites[name] = now + ttl
    return party


def accept(party, name, now):
    """接受邀请：过期、满员、重复加入都拒绝并抛 PartyError。"""
    expire_at = party.invites.get(name)
    if expire_at is None:
        raise PartyError("no pending invite for %s" % name)
    if now > expire_at:
        raise PartyError("invite for %s expired" % name)
    if name in party._member_set:
        raise PartyError("%s already in party" % name)
    if len(party.members) >= party.capacity:
        raise PartyError("party is full (%d/%d)" % (len(party.members), party.capacity))
    party.members.append(name)
    party._member_set.add(name)
    del party.invites[name]
    return party


def transfer_leader(party, name):
    """转移队长：新队长必须在队里，原队长降为普通成员。"""
    if name not in party._member_set:
        raise PartyError("%s is not a party member" % name)
    party.leader = name
    return party
