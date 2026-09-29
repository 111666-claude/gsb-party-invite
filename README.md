# party-invite

组队邀请状态机：邀请、超时、满员与队长转移，只用 Python 标准库。

```
python3 -m partyinvite.cli --sample timeout
python3 -m partyinvite.cli --sample full
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **过期邀请不能接受**：`now > expire_at` 时 `accept` 必须拒绝并返回 `PartyError`。
  `--sample timeout`（邀请 TTL 30 秒，500 秒后才接受）按口径是 `joined=False members=1`，
  现在照样加入，给 `joined=True members=2`。
- **满员不能进**：成员数达到 `capacity` 时拒绝并返回 `PartyError`。
  `--sample full`（容量 4、已有 4 人）按口径是 `members=4`，现在给 `members=5`。
- **同一人不能重复加入**：重复接受同一个邀请要报错。
- **队长转移**：队长可以指定新队长，新队长必须在队里（现在完全没实现）。
- 不变量：成员列表无重复；`len(members) <= capacity`；同一批邀请重复处理结果相同。
- 规模：单队 100 人、10 万次邀请/接受 1 秒内完成，内存 O(成员数 + 待处理邀请)。

## 现在的行为

- `accept` 完全不看 `party.invites` 里的过期时间。
- `accept` 不看 `capacity`，成员可以超出上限。
- 同一个名字可以重复 append 进 `members`。

## 输出

```
joined=False members=1
members=4 capacity=4
```

## 目录

```
partyinvite/party.py   邀请与接受
partyinvite/cli.py     命令行入口
tests/                 unittest 用例
```
