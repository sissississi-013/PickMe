import re
from models import TrafficEntry, TrafficSummary
from bot_db import match_bot

LOG_PATTERN = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) \S+" (?P<status>\d+) \S+ '
    r'"[^"]*" "(?P<user_agent>[^"]*)"'
)

def parse_log_line(line: str) -> TrafficEntry | None:
    m = LOG_PATTERN.match(line.strip())
    if not m:
        return None

    ip = m.group("ip")
    user_agent = m.group("user_agent")
    bot = match_bot(user_agent)

    if bot:
        classification = bot.category
        bot_name = bot.name
        operator = bot.operator
    else:
        classification = "human"
        bot_name = None
        operator = None

    return TrafficEntry(
        ip=ip,
        timestamp=m.group("timestamp"),
        method=m.group("method"),
        path=m.group("path"),
        status=int(m.group("status")),
        user_agent=user_agent,
        classification=classification,
        bot_name=bot_name,
        operator=operator,
    )

def classify_log(log_path: str) -> TrafficSummary:
    entries: list[TrafficEntry] = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            entry = parse_log_line(line)
            if entry:
                entries.append(entry)

    per_bot: dict[str, int] = {}
    counts = {"human": 0, "ai_crawler": 0, "ai_agent": 0, "shopping_agent": 0, "unknown": 0}

    for e in entries:
        counts[e.classification] = counts.get(e.classification, 0) + 1
        if e.bot_name:
            per_bot[e.bot_name] = per_bot.get(e.bot_name, 0) + 1

    return TrafficSummary(
        total_requests=len(entries),
        human=counts["human"],
        ai_crawler=counts["ai_crawler"],
        ai_agent=counts["ai_agent"],
        shopping_agent=counts["shopping_agent"],
        unknown=counts["unknown"],
        per_bot=per_bot,
        entries=entries,
    )
