"""组队邀请状态机：邀请、超时、满员与队长转移。"""


class PartyError(ValueError):
    """组队操作不合法，消息里带上相关队员名字。"""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class Party:
    """一支队伍。"""

    def __init__(self, leader, capacity=4):
        self.leader = leader
        self.capacity = capacity
        self.members = [leader]
        self.invites = {}
        self._member_set = {leader}


def invite(party, name, now, ttl=60):
    """发出邀请：已在队、重复邀请、队伍已满都拒绝。"""
    if name in party._member_set:
        raise PartyError("%s 已在队伍中，不能重复邀请" % name)
    expire_at = party.invites.get(name)
    if expire_at is not None and now <= expire_at:
        raise PartyError("%s 已有待处理的邀请" % name)
    if len(party.members) >= party.capacity:
        raise PartyError("队伍已满（%d/%d），无法邀请 %s" % (len(party.members), party.capacity, name))
    party.invites[name] = now + ttl
    return party


def accept(party, name, now):
    """接受邀请：重复加入、无邀请、已过期、满员都拒绝。"""
    if name in party._member_set:
        raise PartyError("%s 已是队员，不能重复加入" % name)
    expire_at = party.invites.get(name)
    if expire_at is None:
        raise PartyError("%s 没有待处理的邀请" % name)
    if now > expire_at:
        del party.invites[name]
        raise PartyError("%s 的邀请已过期" % name)
    if len(party.members) >= party.capacity:
        raise PartyError("队伍已满（%d/%d），%s 无法加入" % (len(party.members), party.capacity, name))
    party.members.append(name)
    party._member_set.add(name)
    del party.invites[name]
    return party


def transfer_leader(party, name):
    """转移队长：新队长必须在队里，原队长降为普通成员。"""
    if name not in party._member_set:
        raise PartyError("%s 不在队伍中，无法接任队长" % name)
    party.leader = name
    return party
