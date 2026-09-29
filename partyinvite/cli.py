"""命令行入口：跑组队邀请样例。"""

import argparse

from .party import Party, accept, invite


def build_parser():
    parser = argparse.ArgumentParser(prog="party-invite", description="组队邀请")
    parser.add_argument("--sample", default="timeout", help="timeout / full")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.sample == "timeout":
        party = Party("leader")
        invite(party, "late", 0, ttl=30)
        accept(party, "late", 500)  # 早已超时
        print("joined=%s members=%d" % ("late" in party.members, len(party.members)))
    elif args.sample == "full":
        party = Party("leader", capacity=4)
        for name in ("p1", "p2", "p3"):
            invite(party, name, 0)
            accept(party, name, 1)
        invite(party, "p4", 2)
        accept(party, "p4", 3)  # 已经满员
        print("members=%d capacity=%d" % (len(party.members), party.capacity))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
