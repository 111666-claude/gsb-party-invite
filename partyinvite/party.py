"""组队邀请状态机：邀请、超时、满员与队长转移。

缺陷：超时邀请仍可接受、不看人数上限、同一人可以重复加入、队长转移没实现。
"""


class PartyError(ValueError):
    """输入不合法。缺陷：不带邀请人名字。"""

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


def invite(party, name, now, ttl=60):
    """发出邀请。缺陷：不查满员、不查重复邀请。"""
    party.invites[name] = now + ttl
    return party


def accept(party, name, now):
    """接受邀请。缺陷：不看过期时间、不看人数上限、也不去重。"""
    party.members.append(name)
    party.invites.pop(name, None)
    return party
