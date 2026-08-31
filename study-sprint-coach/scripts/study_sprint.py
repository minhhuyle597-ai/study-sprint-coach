import argparse
import datetime as dt
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path, PurePosixPath, PureWindowsPath


READY_KINDS = {"md", "txt", "csv", "json"}
EXTRACTION_KINDS = {"pdf", "pptx", "docx", "xlsx", "xls"}
SOURCE_STATUSES = {"ready", "needs_extraction", "unsupported"}


def parse_date(value):
    try:
        return dt.date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"invalid ISO date: {value}") from error


def atomic_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise


def source_manifest(materials):
    root = Path(materials).resolve()
    if not root.is_dir():
        raise ValueError("materials must be an existing directory")
    files = []
    for candidate in root.rglob("*"):
        if not candidate.is_file() or not candidate.resolve().is_relative_to(root):
            continue
        relative = candidate.relative_to(root).as_posix()
        files.append((relative, candidate))
    sources = []
    for relative, candidate in sorted(files):
        kind = candidate.suffix.lower().lstrip(".")
        status = "ready" if kind in READY_KINDS else (
            "needs_extraction" if kind in EXTRACTION_KINDS else "unsupported"
        )
        digest = hashlib.sha256()
        with candidate.open("rb") as handle:
            for block in iter(lambda: handle.read(65536), b""):
                digest.update(block)
        sources.append({
            "path": relative,
            "kind": kind,
            "size": candidate.stat().st_size,
            "sha256": digest.hexdigest(),
            "status": status,
        })
    return sources


def initialize(args):
    as_of = parse_date(args.as_of) if args.as_of else dt.date.today()
    deadline = parse_date(args.deadline)
    if deadline < as_of:
        raise ValueError("deadline must not be before as-of date")
    if args.minutes_per_day <= 0:
        raise ValueError("minutes per day must be greater than zero")
    if not 0 <= args.target_score <= 100:
        raise ValueError("target score must be in [0, 100]")
    state = {
        "version": 1,
        "mode": "exam",
        "deadline": deadline.isoformat(),
        "minutes_per_day": args.minutes_per_day,
        "target_score": float(args.target_score),
        "sources": source_manifest(args.materials),
        "topics": [],
        "sessions": [],
        "plan": {"as_of": None, "schedule": [], "backlog": []},
    }
    atomic_write(args.state, state)


def load_json(path, label):
    try:
        with Path(path).open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid {label}: {error}") from error


def integer(value, label, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
        raise ValueError(f"{label} is out of range")
    return value


def number(value, label, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")
    if (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
        raise ValueError(f"{label} is out of range")
    return value


def nonempty_string(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def validate_sources(payload):
    if not isinstance(payload, list):
        raise ValueError("state sources must be a list")
    sources, paths = [], set()
    required = {"path", "kind", "size", "sha256", "status"}
    for index, candidate in enumerate(payload):
        label = f"state source {index}"
        if not isinstance(candidate, dict) or not required <= candidate.keys():
            raise ValueError(f"{label} is missing required fields")
        source = dict(candidate)
        path = nonempty_string(source["path"], f"{label} path")
        posix_path = PurePosixPath(path)
        if (path != posix_path.as_posix() or posix_path.is_absolute()
                or PureWindowsPath(path).is_absolute() or ".." in posix_path.parts):
            raise ValueError(f"{label} path must be a normalized relative path")
        if path in paths:
            raise ValueError(f"duplicate state source path: {path}")
        paths.add(path)
        nonempty_string(source["kind"], f"{label} kind")
        integer(source["size"], f"{label} size", 0)
        digest = nonempty_string(source["sha256"], f"{label} sha256")
        if len(digest) != 64 or any(character not in "0123456789abcdefABCDEF" for character in digest):
            raise ValueError(f"{label} sha256 must be a 64-character hexadecimal digest")
        status = nonempty_string(source["status"], f"{label} status")
        if status not in SOURCE_STATUSES:
            raise ValueError(f"{label} status is invalid")
        sources.append(source)
    return sources


def validate_topics(payload, ready_sources):
    if not isinstance(payload, list):
        raise ValueError("topics must be a JSON list")
    identifiers, names, topics = set(), set(), []
    required = {
        "id", "name", "relevance", "mastery", "mastery_attempts", "score_gain",
        "minutes", "evidence", "mastery_check",
    }
    for index, candidate in enumerate(payload):
        label = f"topic {index}"
        if not isinstance(candidate, dict) or not required <= candidate.keys():
            raise ValueError(f"{label} is missing required fields")
        topic = dict(candidate)
        topic_id = nonempty_string(topic["id"], f"{label} id")
        name = nonempty_string(topic["name"], f"{label} name")
        if topic_id in identifiers or name in names:
            raise ValueError("topic IDs and names must be unique")
        identifiers.add(topic_id)
        names.add(name)
        topic["relevance"] = number(topic["relevance"], f"{label} relevance", 0, 1)
        topic["mastery"] = number(topic["mastery"], f"{label} mastery", 0, 1)
        topic["mastery_attempts"] = integer(topic["mastery_attempts"], f"{label} mastery_attempts", 0)
        topic["score_gain"] = number(topic["score_gain"], f"{label} score_gain", 0)
        topic["minutes"] = integer(topic["minutes"], f"{label} minutes", 1)
        topic["remaining_minutes"] = integer(
            topic.get("remaining_minutes", topic["minutes"]),
            f"{label} remaining_minutes", 0, topic["minutes"],
        )
        evidence = topic["evidence"]
        if not isinstance(evidence, list) or not evidence:
            raise ValueError(f"{label} evidence must be a non-empty list")
        for evidence_index, entry in enumerate(evidence):
            if not isinstance(entry, dict):
                raise ValueError(f"{label} evidence {evidence_index} must be an object")
            source = nonempty_string(entry.get("source"), f"{label} evidence source")
            if source not in ready_sources:
                raise ValueError(f"{label} evidence source is not ready in state sources: {source}")
            nonempty_string(entry.get("locator"), f"{label} evidence locator")
        nonempty_string(topic["mastery_check"], f"{label} mastery_check")
        topic["priority"] = (
            topic["relevance"] * (1 - topic["mastery"]) * topic["score_gain"] / topic["minutes"]
        )
        topics.append(topic)
    return sorted(topics, key=lambda topic: (-topic["priority"], topic["id"]))


def validate_state(state, as_of):
    if not isinstance(state, dict):
        raise ValueError("state must be a JSON object")
    if integer(state.get("version"), "state version") != 1:
        raise ValueError("unsupported state version")
    nonempty_string(state.get("mode"), "state mode")
    deadline = parse_date(nonempty_string(state.get("deadline"), "state deadline"))
    integer(state.get("minutes_per_day"), "state minutes_per_day", 1)
    number(state.get("target_score"), "state target_score", 0, 100)
    sources = validate_sources(state.get("sources"))
    ready_sources = {source["path"] for source in sources if source["status"] == "ready"}
    topics = validate_topics(state.get("topics"), ready_sources)
    if not isinstance(state.get("sessions"), list):
        raise ValueError("state sessions must be a list")
    saved_plan = state.get("plan")
    if (not isinstance(saved_plan, dict)
            or {"as_of", "schedule", "backlog"} - saved_plan.keys()
            or not isinstance(saved_plan["schedule"], list)
            or not isinstance(saved_plan["backlog"], list)):
        raise ValueError("state plan must include as_of, schedule, and backlog containers")
    saved_as_of = saved_plan["as_of"]
    if saved_as_of is not None and parse_date(nonempty_string(saved_as_of, "state plan as_of")) > deadline:
        raise ValueError("state plan as_of must not be after deadline")
    if as_of > deadline:
        raise ValueError("as-of date must not be after deadline")
    return topics, ready_sources


def make_plan(state, topics, as_of):
    deadline = parse_date(state.get("deadline", ""))
    minutes_per_day = integer(state.get("minutes_per_day"), "state minutes_per_day", 1)
    days = []
    date = as_of
    while date <= deadline:
        days.append([date.isoformat(), minutes_per_day])
        date += dt.timedelta(days=1)
    schedule, backlog, day_index = [], [], 0
    for topic in topics:
        unscheduled = topic["remaining_minutes"]
        while unscheduled and day_index < len(days):
            date, available = days[day_index]
            minutes = min(unscheduled, available)
            schedule.append({
                "date": date,
                "topic_id": topic["id"],
                "topic_name": topic["name"],
                "minutes": minutes,
                "evidence": topic["evidence"],
                "mastery_check": topic["mastery_check"],
            })
            unscheduled -= minutes
            days[day_index][1] -= minutes
            if days[day_index][1] == 0:
                day_index += 1
        if unscheduled:
            backlog.append({
                "topic_id": topic["id"],
                "topic_name": topic["name"],
                "remaining_minutes": unscheduled,
            })
    return {"as_of": as_of.isoformat(), "schedule": schedule, "backlog": backlog}


def plan(args):
    as_of = parse_date(args.as_of)
    state = load_json(args.state, "state")
    _, ready_sources = validate_state(state, as_of)
    topics = validate_topics(load_json(args.topics, "topics"), ready_sources)
    result = make_plan(state, topics, as_of)
    state["topics"] = topics
    state["plan"] = result
    atomic_write(args.state, state)
    print(json.dumps(result, ensure_ascii=False))


def validate_results(payload, topics):
    if not isinstance(payload, dict) or {"date", "items"} - payload.keys():
        raise ValueError("results must include date and items")
    parse_date(payload["date"])
    items = payload["items"]
    if not isinstance(items, list) or not items:
        raise ValueError("results items must be a non-empty list")
    by_id = {topic["id"]: topic for topic in topics}
    seen = set()
    for index, item in enumerate(items):
        label = f"result item {index}"
        if not isinstance(item, dict) or {"topic_id", "correct", "total", "minutes_spent"} - item.keys():
            raise ValueError(f"{label} is missing required fields")
        topic_id = nonempty_string(item["topic_id"], f"{label} topic_id")
        if topic_id not in by_id:
            raise ValueError(f"unknown topic ID: {topic_id}")
        if topic_id in seen:
            raise ValueError(f"duplicate topic ID: {topic_id}")
        seen.add(topic_id)
        total = integer(item["total"], f"{label} total", 1)
        integer(item["correct"], f"{label} correct", 0, total)
        minutes = integer(item["minutes_spent"], f"{label} minutes_spent", 0)
        if minutes > by_id[topic_id]["remaining_minutes"]:
            raise ValueError(f"{label} minutes_spent exceeds remaining_minutes")


def record(args):
    as_of = parse_date(args.as_of)
    state = load_json(args.state, "state")
    topics, ready_sources = validate_state(state, as_of)
    payload = load_json(args.results, "results")
    validate_results(payload, topics)
    by_id = {topic["id"]: topic for topic in topics}
    for item in payload["items"]:
        topic = by_id[item["topic_id"]]
        old_attempts = topic["mastery_attempts"]
        topic["mastery"] = (topic["mastery"] * old_attempts + item["correct"]) / (old_attempts + item["total"])
        topic["mastery_attempts"] = old_attempts + item["total"]
        topic["remaining_minutes"] -= item["minutes_spent"]
    topics = validate_topics(topics, ready_sources)
    sessions = state["sessions"]
    result = make_plan(state, topics, as_of)
    state["topics"] = topics
    state["sessions"] = [*sessions, payload]
    state["plan"] = result
    atomic_write(args.state, state)
    print(json.dumps(state, ensure_ascii=False))


def build_parser():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--materials", required=True)
    init.add_argument("--deadline", required=True)
    init.add_argument("--minutes-per-day", type=int, required=True)
    init.add_argument("--target-score", type=float, required=True)
    init.add_argument("--state", required=True)
    init.add_argument("--as-of")
    init.set_defaults(handler=initialize)
    plan_command = commands.add_parser("plan")
    plan_command.add_argument("--state", required=True)
    plan_command.add_argument("--topics", required=True)
    plan_command.add_argument("--as-of", required=True)
    plan_command.set_defaults(handler=plan)
    record_command = commands.add_parser("record")
    record_command.add_argument("--state", required=True)
    record_command.add_argument("--results", required=True)
    record_command.add_argument("--as-of", required=True)
    record_command.set_defaults(handler=record)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.handler(args)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
