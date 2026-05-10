from __future__ import annotations


class SpawnStatus:
    PENDING = "pending"
    CLAIMED = "claimed"
    DONE = "done"
    FAILED = "failed"

    ALL = [PENDING, CLAIMED, DONE, FAILED]
    SET = set(ALL)


class Table:
    SPAWN = "aia_robot_spawn_request"
    STATE = "aia_robot_state"
    EVENT = "aia_robot_event"
    FEEDBACK = "aia_robot_feedback"
    DECISION = "aia_robot_decision"
    TRACE = "aia_robot_trace_summary"

    BRIDGE = [STATE, EVENT, FEEDBACK, DECISION, TRACE]
    ALL = [SPAWN] + BRIDGE


class SqlFile:
    SPAWN = "sql/aia_robot_spawn_request_mysql55.sql"
    BRIDGE = "sql/aia_robot_schema.sql"


class ClassId:
    ROYAL = 0
    KNIGHT = 1
    ELF = 2
    WIZARD = 3

    BY_NAME = {
        "royal": ROYAL,
        "knight": KNIGHT,
        "elf": ELF,
        "wizard": WIZARD,
    }
