# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║          ✦  C D X S H A N T O ✦   P R E M I U M  ✦                  ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════════╝
#
#  ╭──────────────────────────────────────────────────────────────────╮
#  │  ◆ PROJECT   ›  FREE FIRE SMART SQUAD + AUTO CREATE + MOVEMENT   │
#  │  ◆ MODULE    ›  Main.py                                          │
#  │  ◆ AUTHOR    ›  CDX_SHANTO                                        │
#  │  ◆ ENGINE    ›  Python 3.10+                                     │
#  ╰──────────────────────────────────────────────────────────────────╯
#
#  © 2026 CDX SHANTO — All rights reserved.
# ════════════════════════════════════════════════════════════════════════
import sys, os, json, time, uuid, random, asyncio, base64, struct, socket
import itertools, traceback, ssl, hmac, hashlib, string, re, subprocess, math
import httpx
import aiohttp
import aiohttp.web
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from google_play_scraper import app as play_scraper
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from protobuf_decoder.protobuf_decoder import Parser
from message_ids import MESSAGE_ID_TO_NAME
import thunderFF_pb2

try:
    import StartMatch_pb2
except Exception:
    StartMatch_pb2 = None

try:
    import reqClan_pb2
    _CLAN_PB_AVAILABLE = True
except Exception:
    _CLAN_PB_AVAILABLE = False

# ==================== CONFIG ====================
WEB_HOST = "0.0.0.0"
WEB_PORT = int(os.environ.get("SERVER_PORT") or os.environ.get("PORT") or "8086")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
TOKEN_CACHE_FILE = os.path.join(BASE_DIR, "token_cache.json")
DEVICES_FILE = os.path.join(BASE_DIR, "devices.json")
TOKEN_CACHE_TTL = 86400 * 7
NETWORK_REFERENCE_FILE = os.path.join(BASE_DIR, "network_capture_reference.json")

# The CSV capture contains DNS/connection metadata only. It is useful for
# diagnostics, but it does not reveal encrypted HTTPS paths or game payloads.
def load_network_reference():
    try:
        with open(NETWORK_REFERENCE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        endpoints = data.get("endpoints", [])
        domains = sorted({
            str(item.get("domain", "")).strip()
            for item in endpoints
            if isinstance(item, dict) and item.get("domain")
        })
        protocols = sorted({
            str(item.get("protocol", "")).strip().upper()
            for item in endpoints
            if isinstance(item, dict) and item.get("protocol")
        })
        return {
            "loaded": True,
            "record_count": int(data.get("record_count", 0) or 0),
            "package_name": data.get("package_name", []),
            "domains": domains,
            "protocols": protocols,
            "endpoint_count": len(endpoints),
            "note": str(data.get("note", "")),
        }
    except FileNotFoundError:
        return {"loaded": False, "reason": "network_capture_reference.json not found"}
    except Exception as exc:
        return {"loaded": False, "reason": f"invalid network reference: {exc}"}

NETWORK_REFERENCE = load_network_reference()
INDEX_HTML_PATH = os.path.join(BASE_DIR, "rafin_txt_565", "index.html")

START_MATCH_INTERVAL = 8.0
NEW_MATCH_DELAY = 4.0
MAX_MATCH_DURATION = 600
MATCH_IDLE_TIMEOUT = 240

NO_MATCH_RESTART_ENABLED = True
NO_MATCH_RESTART_TIMEOUT = 10800.0
NO_MATCH_RESTART_GRACE = 999999.0

_accept_friend_request = True
DEBUG_ALL_PACKETS = True

TEAM_MODE = True
TEAM_SIZE = 4
TEAM_READY_DELAY = 5.0
TEAM_INVITE_WAIT = 2.5
CLAN_ID_DEFAULT = "3106357440"
BOT_NAME_PREFIX = "NKGuild*"
DEV_UID = ""

# ==================== ANTI-AFK MOVEMENT ====================
ANTI_AFK_ENABLED = True
ANTI_AFK_TICK_HZ = 6.0
ANTI_AFK_SPAWN_DELAY = 3.0
ANTI_AFK_RADIUS = 800
ANTI_AFK_SPEED = 55
ANTI_AFK_SPRINT_SPEED = 95
ANTI_AFK_IDLE_CHANCE = 0.08
ANTI_AFK_SPRINT_CHANCE = 0.35
ANTI_AFK_DECISION_SEC = 2.5
ANTI_AFK_PING_EVERY = 2.0
ANTI_AFK_JUMP_EVERY = 20.0

ANALOG_DIRECTIONS = [
    (0.0, 1.0, "maju"), (0.0, -1.0, "mundur"),
    (-1.0, 0.0, "kiri"), (1.0, 0.0, "kanan"),
    (-0.7, 0.7, "maju-kiri"), (0.7, 0.7, "maju-kanan"),
    (-0.7, -0.7, "mundur-kiri"), (0.7, -0.7, "mundur-kanan"),
    (0.0, 0.0, "idle"),
]

ENABLE_SPEED_MOVEMENT = True
MOVEMENT_SPEED_MIN = 0.96
MOVEMENT_SPEED_MAX = 1.02
MOVEMENT_PATTERN = "circle"
MOVEMENT_TICK_MS = 100
MOVEMENT_RADIUS = 180
MOVEMENT_UPDATE_SPEED_EVERY = 4.0

MOVEMENT_STATE_IDLE_CHANCE = 0.10
MOVEMENT_STATE_WALK_CHANCE = 0.28
MOVEMENT_STATE_RUN_CHANCE = 0.32
MOVEMENT_STATE_SPRINT_CHANCE = 0.10
MOVEMENT_STATE_JUMP_CHANCE = 0.08
MOVEMENT_STATE_CROUCH_CHANCE = 0.06
MOVEMENT_STATE_PRONE_CHANCE = 0.06

PLAYER_STATE_MAP = {"idle": 0, "walk": 1, "run": 1, "sprint": 1, "jump": 2, "crouch": 3, "prone": 4}
MOVE_STATE_MAP = {"idle": 0, "walk": 1, "run": 2, "sprint": 3, "jump": 4, "crouch": 1, "prone": 1}
STATE_SPEED = {"idle": 0, "walk": 45, "run": 70, "sprint": 95, "jump": 55, "crouch": 25, "prone": 15}

ENABLE_NEWBIE_CHARACTER = False
NEWBIE_SELECT_BEFORE_TEAM = False
NEWBIE_SELECT_DELAY = 1.5
NEWBIE_SELECT_RETRY = 2
NEWBIE_SELECT_WAIT_AFTER = 2.0
NEWBIE_ITEM_ID_1 = 102000011
NEWBIE_ITEM_ID_2 = 102000026
NEWBIE_ITEM_ID_3 = 102000037
NEWBIE_ITEM_ID_EXTRA = 102000023
NEWBIE_SUB4_FIELD_3 = 50
NEWBIE_SUB4_FIELD_5_2 = 4806
NEWBIE_SUB4_FIELD_8 = 1
NEWBIE_SUB4_FIELD_11 = 11679599800712232

AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
KEYSTREAM = bytes([0x30, 0x30, 0x30, 0x32, 0x30, 0x31, 0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x32, 0x30, 0x31, 0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x32, 0x30, 0x31, 0x37, 0x30, 0x30, 0x30, 0x30, 0x30, 0x32, 0x30])
HEX_KEY = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
API_KEY = HEX_KEY.encode()

REGION_LANG = {
    "ME": "ar", "IND": "hi", "ID": "id", "VN": "vi", "TH": "th", "BD": "bn",
    "PK": "ur", "TW": "zh", "RU": "ru", "SAC": "es", "BR": "pt", "NA": "pt",
    "SG": "pt", "US": "pt"
}

# ╔══════════════════════════════════════════════════════════════════════╗
# ║   ✦  PREMIUM CONSOLE DESIGN LAYER  ✦  (SHANTO Edition)            ║
# ╚══════════════════════════════════════════════════════════════════════╝

class PX:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    ITALIC  = "\033[3m"
    UNDER   = "\033[4m"
    BLINK   = "\033[5m"

    GOLD    = "\033[38;5;220m"
    AMBER   = "\033[38;5;214m"
    ROSE    = "\033[38;5;204m"
    MAGENTA = "\033[38;5;200m"
    VIOLET  = "\033[38;5;135m"
    INDIGO  = "\033[38;5;99m"
    CYAN    = "\033[38;5;51m"
    TEAL    = "\033[38;5;44m"
    MINT    = "\033[38;5;121m"
    LIME    = "\033[38;5;118m"
    EMERALD = "\033[38;5;48m"
    SKY     = "\033[38;5;117m"
    SLATE   = "\033[38;5;245m"
    SILVER  = "\033[38;5;250m"
    WHITE   = "\033[38;5;255m"
    CRIMSON = "\033[38;5;197m"
    CORAL   = "\033[38;5;209m"
    PEACH   = "\033[38;5;216m"
    BG_DARK = "\033[48;5;236m"

I = {
    "ok": "◈", "err": "◇", "warn": "◉", "info": "◎", "star": "✦", "spark": "✧",
    "dot": "•", "arrow": "▸", "check": "✔", "cross": "✘", "bolt": "⚡", "flame": "🔥",
    "gem": "💎", "crown": "👑", "shield": "🛡", "rocket": "🚀", "target": "🎯", "pulse": "◐",
}

def _ts():
    return datetime.now().strftime("%H:%M:%S")

def _fmt(msg, color, icon, tag, level_style=""):
    ts = f"{PX.SLATE}{_ts()}{PX.RESET}"
    badge = f"{color}{PX.BOLD}╭─{icon}─╮{PX.RESET}"
    label = f"{color}{PX.BOLD}{tag}{PX.RESET}"
    body = f"{level_style}{PX.SILVER}{msg}{PX.RESET}"
    return f"{ts} {badge} {label} {PX.DIM}{PX.SLATE}▸{PX.RESET} {body}"

def print_success(t):
    print(_fmt(t, PX.EMERALD, I["ok"], "OK   "), flush=True)
    try:
        bot_state.log(t, "success")
    except Exception:
        pass

def print_error(t):
    print(_fmt(t, PX.CRIMSON, I["err"], "FAIL "), flush=True)
    try:
        bot_state.log(t, "error")
    except Exception:
        pass

def print_warning(t):
    print(_fmt(t, PX.AMBER, I["warn"], "WARN "), flush=True)
    try:
        bot_state.log(t, "warning")
    except Exception:
        pass

def print_info(t):
    print(_fmt(t, PX.CYAN, I["info"], "INFO "), flush=True)
    try:
        bot_state.log(t, "info")
    except Exception:
        pass

def print_premium(t, color=PX.GOLD, icon=I["star"], tag="EVENT"):
    print(_fmt(t, color, icon, f"{tag:<5}"), flush=True)
    try:
        bot_state.log(t, "info")
    except Exception:
        pass

def print_banner():
    R = PX.RESET; b = PX.BOLD
    gold, rose, cyan, violet, silver, teal = PX.GOLD, PX.ROSE, PX.CYAN, PX.VIOLET, PX.SILVER, PX.TEAL
    print()
    print(f"{violet}    ╔══════════════════════════════════════════════════════════╗{R}")
    print(f"{violet}    ║{R}   {gold}{b}✦  V A N D U C D E V  ✦{R}   {rose}{b}P R E M I U M{R}    {violet}║{R}")
    print(f"{violet}    ╠══════════════════════════════════════════════════════════╣{R}")
    print(f"{violet}    ║{R}   {cyan}▸ HỆ THỐNG BOT QUÂN ĐOÀN FREE FIRE THÔNG MINH{R}          {violet}║{R}")
    print(f"{violet}    ║{R}   {silver}▸ Auto Create · Anti-AFK · Smart Squad · Team{R}          {violet}║{R}")
    print(f"{violet}    ║{R}   {teal}▸ Engine v2.1  ·  Python 3.10+{R}                         {violet}║{R}")
    print(f"{violet}    ╚══════════════════════════════════════════════════════════╝{R}")
    print(f"{PX.SLATE}              © 2026 SHANTO — All rights reserved.{R}")
    print()

# ==================== STATE ====================
class BotState:
    def __init__(self):
        self.accounts: Dict[str, dict] = {}
        self.account_credentials: Dict[str, dict] = {}
        self.account_workers: Dict[str, asyncio.Task] = {}
        self.auth_to_game_id: Dict[str, str] = {}
        self.game_to_auth_id: Dict[str, str] = {}
        self.account_token_map: Dict[str, str] = {}
        self.paused: set = set()
        self.writers: Dict[str, list] = {}
        self.logs: List[dict] = []
        self.total_matches = 0
        self.matches_started = 0
        self.total_exp_gained = 0
        self.create_progress: List[str] = []
        self.creating = False
        self.start_time = time.time()
        self.expected_workers = 0
        self._writer_lock = asyncio.Lock()

    def log(self, msg, level="info"):
        try:
            t = datetime.now().strftime("%H:%M:%S")
            self.logs.append({"t": time.time(), "time": t, "message": str(msg), "level": level})
            if len(self.logs) > 500:
                self.logs = self.logs[-500:]
        except Exception:
            pass

    def register_account(self, uid, nickname, region="ID", level=1, exp=0,
                         likes=0, token=None, auth_uid=None):
        uid = str(uid)
        existing = self.accounts.get(uid, {})
        self.accounts[uid] = {
            "uid": uid, "nickname": nickname, "region": region,
            "level": level, "exp": exp, "likes": likes,
            "token": token, "auth_uid": auth_uid,
            "status": "ONLINE", "current_exp": exp,
            "initial_exp": existing.get("initial_exp", exp),
            "gained_exp": existing.get("gained_exp", 0),
            "matches": existing.get("matches", 0),
            "active_matches": 0,
            "uptime_seconds": existing.get("uptime_seconds", 0),
            "last_match_time": existing.get("last_match_time", "Running..."),
            "is_paused": False,
        }

    def update_status(self, uid, status, matches=0):
        uid = str(uid)
        if uid in self.accounts:
            self.accounts[uid]["status"] = status
            self.accounts[uid]["active_matches"] = matches
            self.accounts[uid]["is_paused"] = (status == "PAUSED")

    def update_exp(self, uid, exp, level=None):
        uid = str(uid)
        if uid in self.accounts:
            a = self.accounts[uid]
            old = a.get("current_exp", 0)
            if exp > old:
                a["gained_exp"] = a.get("gained_exp", 0) + (exp - old)
                self.total_exp_gained += (exp - old)
            a["current_exp"] = exp; a["exp"] = exp
            if level:
                a["level"] = level

    def increment_match(self, uid):
        self.total_matches += 1
        uid = str(uid)
        if uid in self.accounts:
            self.accounts[uid]["matches"] = self.accounts[uid].get("matches", 0) + 1
            self.accounts[uid]["last_match_time"] = datetime.now().strftime("%H:%M:%S")

    def increment_match_started(self):
        self.matches_started += 1

    def register_writer(self, uid, w):
        self.writers.setdefault(str(uid), []).append(w)

    def unregister_writer(self, uid, w):
        try:
            self.writers.get(str(uid), []).remove(w)
        except Exception:
            pass

    def close_writers_for_account(self, uid):
        for w in list(self.writers.get(str(uid), [])):
            try:
                w.close()
            except Exception:
                pass
        self.writers[str(uid)] = []

    def is_paused(self, uid):
        return str(uid) in self.paused

bot_state = BotState()

_team_state = {
    "peers": {},
    "leader_uid": None,
    "team_code": None,
    "team_codes": {},
    "squads": [],
    "locked_squads": [],
    "uid_to_leader": {},
    "uid_to_squad_idx": {},
    "partition_sig": None,
    "lock": asyncio.Lock(),
}
_restricted_57_uids: set = {"18951141012", "18951142384"}

def _split_squad_sizes(n: int) -> List[int]:
    if n <= 0:
        return []
    if n <= 4:
        return [n]
    rem = n % 4
    if rem == 0:
        return [4] * (n // 4)
    if rem == 2:
        return [4] * (n // 4) + [2]
    if rem == 3:
        return [4] * (n // 4) + [3]
    return [4] * (n // 4 - 1) + [3, 2]

def _compute_smart_squads(peers_dict: dict) -> List[List[str]]:
    def _sort_key(u):
        return int(u) if str(u).isdigit() else 999999999999
    all_uids = sorted([str(k) for k in peers_dict.keys()], key=_sort_key)
    healthy = [u for u in all_uids if u not in _restricted_57_uids]
    restricted = [u for u in all_uids if u in _restricted_57_uids]

    squads: List[List[str]] = []
    if len(healthy) >= 2 and len(restricted) >= 2:
        idx = 0
        for sz in _split_squad_sizes(len(healthy)):
            squads.append(healthy[idx:idx + sz])
            idx += sz
        idx = 0
        for sz in _split_squad_sizes(len(restricted)):
            squads.append(restricted[idx:idx + sz])
            idx += sz
    else:
        ordered = healthy + restricted
        idx = 0
        for sz in _split_squad_sizes(len(ordered)):
            squads.append(ordered[idx:idx + sz])
            idx += sz
    return [s for s in squads if s]

_restart_state = {"lock": asyncio.Lock(), "finished_bots": set(), "target": None, "restarting": False}

async def _mark_bot_match_finished(account_id):
    pass

_no_match_state = {"lock": asyncio.Lock(), "global_last_match": None, "restart_triggered": False}

async def _mark_match_found(account_id=None):
    async with _no_match_state["lock"]:
        _no_match_state["global_last_match"] = time.time()

_ALLOWED_RESTART_STATUSES = {"ONLINE", "SEARCHING"}
_team_stuck_state = {"lock": asyncio.Lock(), "in_team_since": {}, "triggered": False}

async def _mark_team_joined(uid):
    uid = str(uid)
    async with _team_stuck_state["lock"]:
        if uid not in _team_stuck_state["in_team_since"]:
            _team_stuck_state["in_team_since"][uid] = time.time()
            print_info(f"[TEAM-STUCK] {uid} JOINED")

async def _clear_team_joined(uid):
    uid = str(uid)
    async with _team_stuck_state["lock"]:
        _team_stuck_state["in_team_since"].pop(uid, None)

async def _team_member_count() -> int:
    async with _team_state["lock"]:
        return len(_team_state["peers"])

def _all_bots_are_online_or_searching() -> bool:
    active_statuses = []
    for uid, acc in bot_state.accounts.items():
        status = str(acc.get("status", "")).upper().strip()
        if status in ("", "OFFLINE"):
            continue
        active_statuses.append(status)
    if not active_statuses:
        return False
    return all(st in _ALLOWED_RESTART_STATUSES for st in active_statuses)

def _any_bot_in_match() -> bool:
    for uid, acc in bot_state.accounts.items():
        if "IN_MATCH" in str(acc.get("status", "")).upper():
            return True
    return False

async def _no_match_watchdog():
    if not NO_MATCH_RESTART_ENABLED:
        return
    await asyncio.sleep(NO_MATCH_RESTART_GRACE)
    async with _no_match_state["lock"]:
        if _no_match_state["global_last_match"] is None:
            _no_match_state["global_last_match"] = time.time()
    print_info(f"[NO-MATCH] watchdog aktif timeout={NO_MATCH_RESTART_TIMEOUT:.0f}s")
    while True:
        await asyncio.sleep(10.0)
        try:
            if _restart_state["restarting"] or _no_match_state["restart_triggered"]:
                return
            if _any_bot_in_match():
                async with _no_match_state["lock"]:
                    _no_match_state["global_last_match"] = time.time()
                async with _team_stuck_state["lock"]:
                    now = time.time()
                    for uid in list(_team_stuck_state["in_team_since"].keys()):
                        _team_stuck_state["in_team_since"][uid] = now
                continue
            now = time.time()
            stuck_uids = []
            team_size = await _team_member_count()
            async with _team_stuck_state["lock"]:
                for uid, since in list(_team_stuck_state["in_team_since"].items()):
                    async with _team_state["lock"]:
                        still_in_team = uid in _team_state["peers"]
                    if not still_in_team:
                        del _team_stuck_state["in_team_since"][uid]
                        continue
                    if now - since >= NO_MATCH_RESTART_TIMEOUT:
                        stuck_uids.append((uid, now - since))
            if stuck_uids and team_size >= TEAM_SIZE and not _any_bot_in_match():
                async with _team_stuck_state["lock"]:
                    if _team_stuck_state["triggered"]:
                        continue
                    _team_stuck_state["triggered"] = True
                msg = f"[TEAM-STUCK] {len(stuck_uids)} bot joined team no match ≥{NO_MATCH_RESTART_TIMEOUT:.0f}s"
                print_warning(msg)
                async with _restart_state["lock"]:
                    _restart_state["restarting"] = True
                await _schedule_restart()
                return
            if not _all_bots_are_online_or_searching():
                async with _no_match_state["lock"]:
                    _no_match_state["global_last_match"] = time.time()
                continue
            async with _no_match_state["lock"]:
                last = _no_match_state["global_last_match"] or 0
            elapsed = time.time() - last
            if elapsed >= NO_MATCH_RESTART_TIMEOUT:
                if not _all_bots_are_online_or_searching():
                    continue
                async with _no_match_state["lock"]:
                    if _no_match_state["restart_triggered"]:
                        continue
                    _no_match_state["restart_triggered"] = True
                msg = f"[NO-MATCH] No match for {elapsed:.0f}s → restart!"
                print_warning(msg)
                async with _restart_state["lock"]:
                    _restart_state["restarting"] = True
                await _schedule_restart()
                return
        except Exception as e:
            print_warning(f"[NO-MATCH] error: {e}")

async def _schedule_restart():
    await asyncio.sleep(10.0)
    print_warning("[RESTART] 🔄 Đang reset toàn bộ phiên để tìm trận mới...")
    async with _restart_state["lock"]:
        _restart_state["finished_bots"].clear()
        _restart_state["target"] = None
        _restart_state["restarting"] = False
    async with _team_state["lock"]:
        _team_state["peers"].clear()
        _team_state["leader_uid"] = None
        _team_state["team_code"] = None
        _team_state["team_codes"].clear()
        _team_state["squads"].clear()
        _team_state["locked_squads"].clear()
        _team_state["uid_to_leader"].clear()
        _team_state["uid_to_squad_idx"].clear()
        _team_state["partition_sig"] = None
    async with _no_match_state["lock"]:
        _no_match_state["global_last_match"] = time.time()
        _no_match_state["restart_triggered"] = False
    async with _team_stuck_state["lock"]:
        _team_stuck_state["in_team_since"].clear()
        _team_stuck_state["triggered"] = False

class C:
    GREEN = PX.EMERALD; FAIL = PX.CRIMSON; WARNING = PX.AMBER
    CYAN = PX.CYAN; MAGENTA = PX.MAGENTA; WHITE = PX.WHITE; ENDC = PX.RESET

GGRE_RAW = bytes.fromhex(
    "47475245010101006d020000b260ee08e1f86b4c57f9c70f86bba26ed5d1436bcf52e142db3249d905eded757764991ca31a8373cdd26eab91b80f3f1f6f262f4f10b895d7b6937ddba30a27197453890e9da49373f736c679b8254e2f8e1623e91084a5fdd5374fe478ff99e010834553fddeb0bec4018d142e49df9bb236675b67e852f92a43586f7a7d4d0d7a197a1d4da32714dab4d069ad53214e2c33b3877420a12459738c4c619cbd815fa878bbd104776bb3e1ac7818d5397b04a666ac57f682763ff2df31bc2f846ddc7904f3dce1bda0c4b01f9698e9166f98c84f92640abe3f6317834a42e5c12573b46842c1a6ea8fe6ca9c006dca48a2087e1f983dfb5692771e4a0b15b337ad669b1d08b40862b176bace5331b49a767375b1a8469012aa70a67b55fe71b72478201d0b3ac7269c064c960361e92ee7ba8a42cc6b582bf9b965fb388fa9172ad44c4b073ac23c02080a6bcd106b691ffdf4c7cf71e42f2063fcf196e9bddc5e85be1fe5048eb1b31b460efbb46d76195eef9904c4cba326f2e17ff51fec17dd965aa06dadd4ab07d6966e4a7c38e8afd66dfde56c872bb87516a8f7313c797e4d80e5ad4a5f7afad95c1e0449254adae052e71a3fb98399f93ab30848e0d23252dd45e6fd41bc5fa7303dfb846a8fd713a0032a0b0ae96dfba1bbe41d20abd8099e2cb7fccc329d25bd153029139ef05d090a5093ea557693c0a8d491395b8a23ca844b3887dd5dfc29ac06f4b9be87883a793211b973465e2644c4f5de02b8ab01571401203fc2740423826858cc6da0194c195d27aac4ec4b9d23d506c1501d06440aca3fc180926d75d4a004d3dff21eb4ea1e8c86e6c9627248eff953e1d192d5c8efc006a7e512388ef2ebdb72ee3ad42d719f28e8f994e12ebf4c79f2ffe3abd7408ccd2236a7b89b2606247a732c10c4"
)

def _encode_proto_std(fields):
    out = b""
    for f in sorted(fields.keys()):
        v = fields[f]
        if isinstance(v, bool):
            out += encode_varint((f << 3) | 0) + encode_varint(int(v))
        elif isinstance(v, int):
            out += encode_varint((f << 3) | 0) + encode_varint(v)
        elif isinstance(v, (str, bytes)):
            if isinstance(v, str):
                v = v.encode()
            out += encode_varint((f << 3) | 2) + encode_varint(len(v)) + v
    return out

def _generate_new_device() -> dict:
    device_list = [
        ("Samsung", "SM-G998B", "Adreno (TM) 660", "Android OS 12 / API-31"),
        ("Xiaomi", "2201122G", "Adreno (TM) 730", "Android OS 13 / API-33"),
        ("Realme", "RMX3700", "Mali-G710", "Android OS 14 / API-34"),
        ("OnePlus", "CPH2451", "Adreno (TM) 740", "Android OS 13 / API-33"),
        ("OPPO", "CPH2611", "Adreno (TM) 720", "Android OS 14 / API-34"),
    ]
    brand, model, gpu, os_ver = random.choice(device_list)
    return {
        "unique_device_id": f"Google|{uuid.uuid4()}",
        "brand": brand, "model": model,
        "gpu_renderer": gpu, "system_software": os_ver,
        "screen_width": random.choice([1080, 1440, 720]),
        "screen_height": random.choice([2400, 3200, 1600]),
        "screen_dpi": str(random.randint(300, 420)),
        "memory": random.randint(2800, 6500)
    }

def get_device_for_account(acc_key: str) -> dict:
    devices = {}
    if os.path.exists(DEVICES_FILE):
        try:
            with open(DEVICES_FILE, "r", encoding="utf-8") as f:
                devices = json.load(f)
                if not isinstance(devices, dict):
                    devices = {}
        except Exception:
            devices = {}
    if acc_key in devices:
        return devices[acc_key]
    nd = _generate_new_device()
    devices[acc_key] = nd
    try:
        with open(DEVICES_FILE, "w", encoding="utf-8") as f:
            json.dump(devices, f, indent=2)
    except Exception:
        pass
    return nd

_DNS_CACHE: Dict[str, Tuple[str, float]] = {}
_DNS_CACHE_TTL = 300.0

async def resolve_host_cloudflare(hostname: str) -> str:
    if not hostname:
        return hostname
    parts = hostname.split('.')
    if len(parts) == 4 and all(p.isdigit() for p in parts):
        return hostname
    now = time.time()
    if hostname in _DNS_CACHE:
        ip, exp = _DNS_CACHE[hostname]
        if now < exp:
            return ip
    try:
        loop = asyncio.get_running_loop()
        info = await loop.getaddrinfo(hostname, None, family=socket.AF_INET, proto=socket.IPPROTO_TCP)
        if info:
            ip = info[0][4][0]
            _DNS_CACHE[hostname] = (ip, now + _DNS_CACHE_TTL)
            return ip
    except Exception:
        if "clientbp.ggpolarbear.com" in hostname:
            return "104.28.197.151"
    return hostname

def optimize_tcp_socket(sock):
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131072)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131072)
    except Exception:
        pass

async def safe_close_writer(writer):
    if not writer:
        return
    try:
        if not writer.is_closing():
            writer.close()
        await asyncio.wait_for(writer.wait_closed(), timeout=1.5)
    except Exception:
        pass

def optimize_udp_socket(sock):
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131072)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131072)
    except Exception:
        pass
    if sys.platform == "win32":
        try:
            sock.ioctl(0x9800000C, b"\x00\x00\x00\x00")
        except Exception:
            pass

client = httpx.AsyncClient(
    verify=False, timeout=15.0,
    limits=httpx.Limits(max_connections=300, max_keepalive_connections=150)
)
_LOGIN_SEMAPHORE = asyncio.Semaphore(4)

CRC7_TABLE = bytes([
    0,9,18,27,36,45,54,63,72,65,90,83,108,101,126,119,
    25,16,11,2,61,52,47,38,81,88,67,74,117,124,103,110,
    50,59,32,41,22,31,4,13,122,115,104,97,94,87,76,69,
    43,34,57,48,15,6,29,20,99,106,113,120,71,78,85,92,
    100,109,118,127,64,73,82,91,44,37,62,55,8,1,26,19,
    125,116,111,102,89,80,75,66,53,60,39,46,17,24,3,10,
    86,95,68,77,114,123,96,105,30,23,12,5,58,51,40,33,
    79,70,93,84,107,98,121,112,7,14,21,28,35,42,49,56,
    65,72,83,90,101,108,119,126,9,0,27,18,45,36,63,54,
    88,81,74,67,124,117,110,103,16,25,2,11,52,61,38,47,
    115,122,97,104,87,94,69,76,59,50,41,32,31,22,13,4,
    106,99,120,113,78,71,92,85,34,43,48,57,6,15,20,29,
    37,44,55,62,1,8,19,26,109,100,127,118,73,64,91,82,
    60,53,46,39,24,17,10,3,116,125,102,111,80,89,66,75,
    23,30,5,12,51,58,33,40,95,86,77,68,123,114,105,96,
    14,7,28,21,42,35,56,49,70,79,84,93,98,107,112,121,
])
_DELTA = 0x9E3779B9
_ROUNDS = 16
_FIELD_SIZES = {0: 1, 1: 2, 2: 2, 3: 1, 4: 2}
_FIELD_NAMES = {0: "sendOption", 1: "cmd", 2: "orderId", 3: "flags", 4: "length"}

def encode_varint(n: int) -> bytes:
    out = bytearray()
    if n < 0:
        n &= 0xFFFFFFFFFFFFFFFF
    while True:
        b = n & 0x7F; n >>= 7
        if n:
            b |= 0x80
        out.append(b)
        if not n:
            break
    return bytes(out)

def _pb_varint(fn, val):
    return encode_varint((fn << 3) | 0) + encode_varint(val)

def _pb_length(fn, val):
    enc = val.encode('utf-8') if isinstance(val, str) else val
    return encode_varint((fn << 3) | 2) + encode_varint(len(enc)) + enc

def create_proto(fields) -> bytes:
    packet = bytearray()
    for field, value in fields.items():
        if isinstance(field, str):
            field = int(field)
        if isinstance(value, dict):
            packet.extend(_pb_length(field, bytes(create_proto(value))))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    packet.extend(_pb_length(field, bytes(create_proto(item))))
                elif isinstance(item, str):
                    packet.extend(_pb_length(field, item))
                elif isinstance(item, (bytes, bytearray)):
                    packet.extend(_pb_length(field, bytes(item)))
                elif isinstance(item, bool):
                    packet.extend(_pb_varint(field, 1 if item else 0))
                elif isinstance(item, int):
                    packet.extend(_pb_varint(field, item))
        elif isinstance(value, bool):
            packet.extend(_pb_varint(field, 1 if value else 0))
        elif isinstance(value, int):
            packet.extend(_pb_varint(field, value))
        elif isinstance(value, str):
            packet.extend(_pb_length(field, value))
        elif isinstance(value, (bytes, bytearray)):
            packet.extend(_pb_length(field, bytes(value)))
    return bytes(packet)

def encrypt_aes(hex_data: str) -> str:
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(bytes.fromhex(hex_data), AES.block_size)).hex()

def decode_varint(data, offset):
    result = 0; shift = 0
    while offset < len(data):
        byte = data[offset]
        result |= (byte & 0x7F) << shift
        offset += 1
        if not (byte & 0x80):
            return result, offset
        shift += 7
    return None, offset

def decode_protobuf_2(data):
    result = {}; offset = 0; data_len = len(data)
    while offset < data_len:
        header, offset = decode_varint(data, offset)
        if header is None:
            break
        fn = header >> 3; wt = header & 0x7
        if wt == 0:
            v, offset = decode_varint(data, offset)
            if v is not None:
                result[fn] = v
        elif wt == 2:
            length, offset = decode_varint(data, offset)
            if length is None:
                break
            value = data[offset:offset + length]; offset += length
            try:
                s = value.decode('utf-8')
                result[fn] = s if s else value.hex()
            except UnicodeDecodeError:
                nested = decode_protobuf_2(value)
                result[fn] = nested if nested else value.hex()
        elif wt == 1:
            offset += 8
        elif wt == 3:
            offset += 4
        else:
            break
    return result

def extract_raw_fields(data: bytes) -> dict:
    result = {}; offset = 0; data_len = len(data)
    while offset < data_len:
        header, offset = decode_varint(data, offset)
        if header is None:
            break
        fn = header >> 3; wt = header & 0x7
        if wt == 0:
            v, offset = decode_varint(data, offset)
            if v is not None:
                result[fn] = v
        elif wt == 2:
            length, offset = decode_varint(data, offset)
            if length is None or offset + length > data_len:
                break
            result[fn] = bytes(data[offset:offset + length]); offset += length
        elif wt == 1:
            offset += 8
        elif wt == 3:
            offset += 4
        else:
            break
    return result

def _parse_results_sync(results):
    out = {}
    for r in results:
        fd = {"wire_type": r.wire_type}
        if r.wire_type == "varint":
            fd["data"] = r.data
        elif r.wire_type in ("string", "bytes"):
            fd["data"] = r.data
        elif r.wire_type == "length_delimited":
            if hasattr(r.data, "results"):
                fd["data"] = _parse_results_sync(r.data.results)
            elif isinstance(r.data, list):
                fd["data"] = _parse_results_sync(r.data)
            else:
                fd["data"] = str(r.data)
        out[str(r.field)] = fd
    return out

def decode_protobuf_dict(data: bytes) -> dict:
    try:
        parsed = Parser().parse(data)
        return _parse_results_sync(parsed)
    except Exception:
        return {}

async def decode_protobuf_async(data):
    try:
        parsed = Parser().parse(data)
        return json.dumps(_parse_results_sync(parsed))
    except Exception:
        return "{}"

async def has_ssan_zig(n: int) -> bytes:
    try:
        n = int(n)
    except Exception:
        n = 0
    z = (n << 1) & 0xFFFFFFFFFFFFFFFF
    out = bytearray()
    while z >= 0x80:
        out.append((z & 0x7F) | 0x80); z >>= 7
    out.append(z); return bytes(out)

async def uleb_encode(n: int) -> bytes:
    try:
        n = int(n)
    except Exception:
        n = 0
    if n < 0:
        n &= 0xFFFFFFFFFFFFFFFF
    out = bytearray()
    while True:
        b = n & 0x7F; n >>= 7
        if n:
            b |= 0x80
        out.append(b)
        if not n:
            break
    return bytes(out)

async def zigzag_encode_signed(n: int) -> bytes:
    try:
        n = int(n)
    except Exception:
        n = 0
    zz = (n << 1) ^ (n >> 63)
    if zz < 0:
        zz = -zz
    zz &= 0xFFFFFFFFFFFFFFFF
    out = bytearray()
    while True:
        b = zz & 0x7F; zz >>= 7
        if zz:
            b |= 0x80
        out.append(b)
        if not zz:
            break
    return bytes(out)

def create_packet(Pk, N, K, V):
    if isinstance(K, str):
        K = bytes.fromhex(K) if len(K) == 32 else K.encode()
    if isinstance(V, str):
        V = bytes.fromhex(V) if len(V) == 32 else V.encode()
    PkEnc = AES.new(K, AES.MODE_CBC, V).encrypt(pad(bytes.fromhex(Pk), 16)).hex()
    L = len(PkEnc) // 2
    hexlen = hex(L)[2:]
    if len(hexlen) % 2 != 0:
        hexlen = '0' + hexlen
    total_pad = 12 - len(N) - len(hexlen)
    if total_pad < 0:
        total_pad = 0
    return bytes.fromhex(N + ('0' * total_pad) + hexlen + PkEnc)

def _f32_bits(val: float) -> int:
    return struct.unpack("<I", struct.pack("<f", float(val)))[0]

async def build_movement_packet_2001(key_bytes, msg_key, player_state, x, y, z,
                                     tick, counter, move_state, account_uid,
                                     room_code=None, slot_id=1, phase="arena",
                                     angle=0.0, speed=0.0, vel_y=0.0, s1=0, s2=2,
                                     player_match_id=1):
    if room_code:
        _, nr = await layouts_from_mask(room_code)
    else:
        nr = [0, 1, 4, 3]

    pid_val = int(player_match_id) & 0x7F if player_match_id else 1
    body = bytearray(await uleb_encode((1 << 24) | pid_val))

    body += await zigzag_encode_signed(int(round(x)))
    body += await zigzag_encode_signed(int(round(y)))
    body += await zigzag_encode_signed(int(round(z)))

    ca = math.cos(angle)
    sa = math.sin(angle)
    fx = max(-100, min(100, int(round(100.0 * ca))))
    fy = -24 if s1 == 2 else 0
    fz = max(-100, min(100, int(round(100.0 * sa))))
    body += await zigzag_encode_signed(fx)
    body += await zigzag_encode_signed(fy)
    body += await zigzag_encode_signed(fz)

    if s1 in (4, 2):
        mx, mz = 0, 100
    elif s1 == 1 and s2 == 11:
        mx, mz = 0, 0
    elif speed > 1.0:
        mx, mz = fx, fz
    else:
        mx, mz = 0, 0
    body += await zigzag_encode_signed(mx)
    body += await zigzag_encode_signed(mz)

    vx = int(round((speed * ca) / 10.0))
    vy = int(round(vel_y / 10.0))
    vz = int(round((speed * sa) / 10.0))
    body += await zigzag_encode_signed(vx)
    body += await zigzag_encode_signed(vy)
    body += await zigzag_encode_signed(vz)

    body += await uleb_encode(int(s1))
    body += await uleb_encode(int(s2))

    pitch = -0.25
    cp = math.cos(pitch)
    sp = math.sin(pitch)
    cam_x = ca * cp
    cam_y = sp
    cam_z = sa * cp
    body += await uleb_encode(_f32_bits(cam_x))
    body += await uleb_encode(_f32_bits(cam_y))
    body += await uleb_encode(_f32_bits(cam_z))

    body += b"\x00\x00"
    body += struct.pack("<I", int(tick))
    body += await uleb_encode(int(counter) & 0xFFFFFFFF)
    return await build_packet(msg_key, nr, 0, 2001, None, 0, bytes(body), key_bytes, encrypted=False)

class MovementController:
    def __init__(self, account_id, account_region, key, iv,
                 tcp_writer=None, udp_sock=None, udp_server=None,
                 udp_key_bytes=None, match_code=None, slot_id=None):
        self.account_id = int(account_id) if str(account_id).isdigit() else 0
        self.region = str(account_region).upper()
        self.key = key; self.iv = iv
        self.tcp_writer = tcp_writer
        self.udp_sock = udp_sock
        self.udp_server = udp_server
        self.udp_key = udp_key_bytes
        self.match_code = match_code
        self.slot_id = max(1, min(4, int(slot_id))) if slot_id is not None else 1

        self.player_match_id = None
        self.phase = "island"
        self.air_s1 = 4
        self.air_s2 = 0
        self.spawn_x = 5751; self.spawn_y = 1400160; self.spawn_z = 1650
        self.ground_y = 1400160
        self.x = float(self.spawn_x); self.y = float(self.spawn_y); self.z = float(self.spawn_z)
        self.has_real_coords = False
        self.has_real_ground_coords = False
        self.plane_x = None; self.plane_y = None; self.plane_z = None

        self.tick = 18; self.counter = 0
        self.angle = ((self.slot_id - 1) * (math.pi / 2.0)) + random.uniform(-0.3, 0.3)
        self.state = "sprint"
        self.cur_speed = 0.0
        self.vel_y = 0.0
        self.pkt_s1 = 0
        self.pkt_s2 = 2
        self.speed_mul = random.uniform(MOVEMENT_SPEED_MIN, MOVEMENT_SPEED_MAX)
        self._msg_keys = [0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6a, 0x6b, 0x6c]
        self._key_idx = 0

        self._stop_evt = asyncio.Event()
        self._clock_stop = asyncio.Event()
        self._task = None
        self._clock_task = None
        self._last_decision = 0.0
        self._last_speed_change = 0.0
        self._last_jump_t = 0.0
        self._jump_start_t = 0.0
        self._last_clock_echo_t = 0.0
        self._start_time = 0.0
        self.last_srv_pos = None
        self._stuck_ref_pos = None
        self._stuck_ref_t = 0.0

    async def _echo_clock_sync(self, raw_tick_bytes: bytes):
        if not self.udp_sock or not self.udp_server or not self.udp_key:
            return
        try:
            loop = asyncio.get_running_loop()
            _, nr = await layouts_from_mask(self.match_code)
            mk = self._msg_keys[self._key_idx % len(self._msg_keys)]
            pkt = await build_packet(mk, nr, 0, 2000, None, 0, raw_tick_bytes, self.udp_key, encrypted=False)
            await loop.sock_sendto(self.udp_sock, pkt, self.udp_server)
            self._last_clock_echo_t = time.time()
        except Exception:
            pass

    def handle_server_frame(self, frame):
        cmd = frame.get("cmd")
        content = frame.get("content")
        if not content:
            return
        try:
            def _dec_v(b, off):
                res = 0; s = 0; cur = off
                while cur < len(b):
                    bt = b[cur]; res |= (bt & 0x7F) << s; cur += 1; s += 7
                    if not (bt & 0x80):
                        break
                return res, cur
            def _dec_zz(n):
                return (n >> 1) ^ -(n & 1)

            if cmd == 2000 and len(content) >= 1:
                _, end_off = _dec_v(content, 0)
                if end_off >= 1:
                    asyncio.create_task(self._echo_clock_sync(bytes(content[:end_off])))
                return

            if cmd == 2001 and len(content) >= 15 and content[:2] == b"\x00\x02" and 1 <= content[2] <= 64:
                pid = content[2]
                if self.player_match_id is None:
                    self.player_match_id = pid
                elif pid != self.player_match_id:
                    return
                cur = 3
                vx, cur = _dec_v(content, cur)
                vy, cur = _dec_v(content, cur)
                vz, cur = _dec_v(content, cur)
                zx, zy, zz = _dec_zz(vx), _dec_zz(vy), _dec_zz(vz)

                s1, s2 = 0, 0
                try:
                    for _ in range(8):
                        _, cur = _dec_v(content, cur)
                    s1, cur = _dec_v(content, cur)
                    s2, cur = _dec_v(content, cur)
                except Exception:
                    pass

                now = time.time()
                if zy >= 800000:
                    self.phase = "island"
                    self.ground_y = zy
                    self.spawn_x = zx; self.spawn_y = zy; self.spawn_z = zz
                    self.x = float(zx); self.y = float(zy); self.z = float(zz)
                    self.has_real_coords = True
                    return

                if s1 == 3:
                    self.phase = "plane"
                    self.has_real_coords = True
                    self.plane_x = zx; self.plane_y = zy; self.plane_z = zz
                    self.x = float(zx); self.y = float(zy); self.z = float(zz)
                    return

                if s1 in (4, 2) or (s1 == 1 and s2 == 10 and not self.has_real_ground_coords):
                    self.has_real_coords = True
                    if self.phase != "airborne":
                        self.phase = "airborne"
                        self.x = float(zx); self.y = float(zy); self.z = float(zz)
                        self.angle = ((self.slot_id - 1) * (math.pi / 2.0)) + random.uniform(-0.35, 0.35)
                    else:
                        self.y = float(zy)
                        if math.hypot(self.x - zx, self.z - zz) > 3000.0:
                            self.x = float(zx); self.z = float(zz)
                    self.air_s1 = s1 if s1 in (4, 2) else 2
                    self.air_s2 = s2
                    return

                if zy < 250000:
                    self.phase = "ground"
                    if not self.has_real_ground_coords:
                        self.spawn_x = zx; self.spawn_y = zy; self.spawn_z = zz
                        self.ground_y = zy
                        self.x = float(zx); self.y = float(zy); self.z = float(zz)
                        self.has_real_coords = True; self.has_real_ground_coords = True
                        self.last_srv_pos = (zx, zy, zz)
                        self._stuck_ref_pos = (zx, zy, zz); self._stuck_ref_t = now
                        self.angle = ((self.slot_id - 1) * (math.pi / 2.0)) + random.uniform(-0.3, 0.3)
                        self.state = "sprint"
                        return

                    self.last_srv_pos = (zx, zy, zz)
                    is_jumping = (self.state == "jump" and (now - self._jump_start_t) < 0.85)
                    if s1 == 0 and not is_jumping:
                        self.ground_y = zy; self.y = float(zy)

                    if math.hypot(self.x - zx, self.z - zz) > 6000.0:
                        self.x = float(zx); self.z = float(zz)
                        if not is_jumping:
                            self.ground_y = zy; self.y = float(zy)
                        self.angle = (self.angle + random.uniform(1.8, 4.4)) % (2.0 * math.pi)

                    if self._stuck_ref_pos is None:
                        self._stuck_ref_pos = (zx, zy, zz); self._stuck_ref_t = now
                    elif (now - self._stuck_ref_t) >= 2.5:
                        moved_xz = math.hypot(zx - self._stuck_ref_pos[0], zz - self._stuck_ref_pos[2])
                        self._stuck_ref_pos = (zx, zy, zz); self._stuck_ref_t = now
                        if moved_xz < 400.0 and self.cur_speed > 1000.0:
                            self.x = float(zx); self.z = float(zz); self.ground_y = zy
                            self.angle = (self.angle + random.uniform(2.0, 4.2)) % (2.0 * math.pi)
                            if not is_jumping:
                                self._jump_start_t = now; self._last_jump_t = now; self.state = "jump"
        except Exception:
            pass

    def _pick_state(self) -> str:
        r = random.random()
        if r < 0.72:
            return "sprint"
        if r < 0.90:
            return "run"
        return "walk"

    def _step_position(self, dt):
        now = time.time()
        elapsed = now - self._start_time if self._start_time > 0 else 0.0

        if elapsed > 45.0 and self.phase in ("init", "island", "plane") and not self.has_real_ground_coords:
            slot_off = (self.slot_id - 1) * 800
            if self.plane_x is not None and self.plane_z is not None:
                self.spawn_x = self.plane_x + slot_off; self.spawn_z = self.plane_z + slot_off
                self.spawn_y = 9229; self.ground_y = 9229
                self.x = float(self.spawn_x); self.y = float(self.spawn_y); self.z = float(self.spawn_z)
                self.phase = "ground"; self.has_real_coords = True; self.has_real_ground_coords = True

        if self.phase in ("init", "island"):
            self.tick = 18; self.ground_y = self.spawn_y
            self.y = float(self.ground_y); self.vel_y = 0.0
            speed = 5600.0 * self.speed_mul
            self.pkt_s1 = 1; self.pkt_s2 = 11; self.cur_speed = speed
            self.x += math.cos(self.angle) * speed * dt
            self.z += math.sin(self.angle) * speed * dt
            if (self.x - self.spawn_x) ** 2 + (self.z - self.spawn_z) ** 2 > 35000.0 ** 2:
                self.angle = math.atan2(self.spawn_z - self.z, self.spawn_x - self.x) + random.uniform(-0.35, 0.35)
            return

        if self.phase == "airborne":
            self.cur_speed = 6200.0; self.vel_y = -11800.0
            self.pkt_s1 = self.air_s1; self.pkt_s2 = 0; self.tick = 17
            self.x += math.cos(self.angle) * self.cur_speed * dt
            self.z += math.sin(self.angle) * self.cur_speed * dt
            self.y += self.vel_y * dt
            return

        self.tick = 18
        if self.state == "jump":
            j_prog = (now - self._jump_start_t) / 0.85
            if 0.0 <= j_prog < 1.0:
                self.y = float(self.ground_y) + 698.0 * 4.0 * j_prog * (1.0 - j_prog)
                self.vel_y = 3285.0 * (1.0 - 2.0 * j_prog)
                self.pkt_s1 = 1; self.pkt_s2 = 11; speed = 5550.0
            else:
                self.y = float(self.ground_y); self.vel_y = -3300.0
                self.pkt_s1 = 1; self.pkt_s2 = 0; self.state = "sprint"; speed = 5600.0
        else:
            self.y = float(self.ground_y); self.vel_y = 0.0
            if self.state == "walk":
                speed = 3400.0 * self.speed_mul; self.pkt_s1 = 0; self.pkt_s2 = 1
            elif self.state in ("run", "sprint"):
                speed = 5600.0 * self.speed_mul; self.pkt_s1 = 1; self.pkt_s2 = 11
            else:
                speed = 0.0; self.pkt_s1 = 0; self.pkt_s2 = 0

        self.cur_speed = speed
        if speed > 0.0:
            self.x += math.cos(self.angle) * speed * dt
            self.z += math.sin(self.angle) * speed * dt
            if (self.x - self.spawn_x) ** 2 + (self.z - self.spawn_z) ** 2 > 120000.0 ** 2:
                self.angle = math.atan2(self.spawn_z - self.z, self.spawn_x - self.x) + random.uniform(-0.35, 0.35)

    async def _send_udp(self):
        if not self.udp_sock or not self.udp_server or not self.udp_key or self.phase == "plane":
            return False
        try:
            loop = asyncio.get_running_loop()
            time_ms = int((time.time() - self._start_time) * 1000) & 0xFFFFFFFF
            mk = self._msg_keys[self._key_idx % len(self._msg_keys)]
            self._key_idx += 1
            pkt = await build_movement_packet_2001(
                self.udp_key, mk, PLAYER_STATE_MAP.get(self.state, 1),
                self.x, self.y, self.z, self.tick, time_ms, MOVE_STATE_MAP.get(self.state, 2),
                self.account_id, room_code=self.match_code, slot_id=self.slot_id,
                phase=self.state, angle=self.angle, speed=self.cur_speed,
                vel_y=self.vel_y, s1=self.pkt_s1, s2=self.pkt_s2,
                player_match_id=self.player_match_id or 1
            )
            await loop.sock_sendto(self.udp_sock, pkt, self.udp_server)
            return True
        except Exception:
            return False

    async def _clock_sync_loop(self):
        if not self.udp_sock or not self.udp_server or not self.udp_key:
            return
        loop = asyncio.get_running_loop()
        _, nr = await layouts_from_mask(self.match_code)
        tick_val = 60
        try:
            await asyncio.sleep(2.5)
            while not self._clock_stop.is_set():
                try:
                    if (time.time() - self._last_clock_echo_t) > 4.5:
                        body = await uleb_encode(tick_val)
                        pkt = await build_packet(0x68, nr, 0, 2000, None, 0, body, self.udp_key, encrypted=False)
                        await loop.sock_sendto(self.udp_sock, pkt, self.udp_server)
                        tick_val = (tick_val + 60) & 0xFFFFFFFF
                    await asyncio.wait_for(self._clock_stop.wait(), timeout=2.0)
                    break
                except asyncio.TimeoutError:
                    pass
                except asyncio.CancelledError:
                    break
        except asyncio.CancelledError:
            pass

    async def _loop(self):
        self._start_time = time.time()
        if self.udp_sock and self.udp_server and self.udp_key:
            try:
                loop = asyncio.get_running_loop()
                ru, _ = await layouts_from_mask(self.match_code)
                loading_end = await build_packet(0x60, ru, 2, 899, 8, 1, b"", self.udp_key)
                await loop.sock_sendto(self.udp_sock, loading_end, self.udp_server)
            except Exception:
                pass
        await asyncio.sleep(1.0)
        interval = MOVEMENT_TICK_MS / 1000.0
        last_t = time.time()
        self._last_jump_t = last_t; self._last_decision = last_t; self._last_speed_change = last_t
        while not self._stop_evt.is_set():
            now = time.time()
            dt = now - last_t; last_t = now
            if dt <= 0.0 or dt > 0.25:
                dt = interval
            if self.phase == "ground":
                if self.state != "jump" and (now - self._last_jump_t) >= random.uniform(3.8, 6.2):
                    self._last_jump_t = now; self._jump_start_t = now; self.state = "jump"
                if self.state != "jump" and (now - self._last_decision) >= random.uniform(3.0, 5.5):
                    self.state = self._pick_state()
                    self.angle = (self.angle + random.uniform(-0.9, 0.9)) % (2.0 * math.pi)
                    self._last_decision = now
                if now - self._last_speed_change >= MOVEMENT_UPDATE_SPEED_EVERY:
                    self.speed_mul = random.uniform(MOVEMENT_SPEED_MIN, MOVEMENT_SPEED_MAX)
                    self._last_speed_change = now
            if self.phase != "plane":
                self._step_position(dt)
                await self._send_udp()
            try:
                await asyncio.wait_for(self._stop_evt.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass

    def start(self):
        if self._task and not self._task.done():
            return
        self._stop_evt.clear(); self._clock_stop.clear()
        self._task = asyncio.create_task(self._loop())
        self._clock_task = asyncio.create_task(self._clock_sync_loop())

    async def stop(self):
        self._stop_evt.set(); self._clock_stop.set()
        for t in (self._task, self._clock_task):
            if t:
                try:
                    await asyncio.wait_for(t, timeout=3.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    t.cancel()

# ==================== TEAM PACKETS ====================
def _team_packet_prefix(region="ID"):
    reg = str(region or "ID").upper()
    return "0519" if reg == "BD" else ("0514" if reg == "IND" else "0515")

def create_team(key, iv, region="ID", game_version="1.132.9"):
    region = (str(region).upper() if region else "ID")
    fields = {
        1: 1,
        2: {
            2: bytes.fromhex("01"), 3: 1, 4: 3, 5: "en",
            8: {1: "IDC3", 2: 123, 3: region}, 9: 1,
            10: bytes.fromhex("01090a0b1219202729"), 11: 2, 13: 1,
            14: {
                1: "08FBA33B4BABE2790205390333330000009700050092005F72697EB2134DCBB2467625142201040e38e848dc0e748c3f6aa04d81000000ff1113090dcacfa16d",
                2: 478, 3: "7e585d55", 4: "y[Z]", 6: 12, 7: "15686677735a7506101c",
                8: str(game_version), 9: 3, 10: 1, 11: "03626253513637754174"
            },
            19: 329, 21: bytes.fromhex("374f521955"),
            24: {1: 21}, 27: "a_6534489873065906362"
        }
    }
    return create_packet(create_proto(fields).hex(), _team_packet_prefix(region), key, iv)

def leave_team(account_id, key, iv, region="ID"):
    reg = str(region).upper() if region else "ID"
    pfx = "0519" if reg == "BD" else ("0514" if reg == "IND" else "0515")
    return create_packet(create_proto({1: 7, 2: {1: int(account_id)}}).hex(), pfx, key, iv)

def invite_player_in_team(target_uid, key, iv, region="ID"):
    region = (str(region).upper() if region else "ID")
    return create_packet(
        create_proto({1: 2, 2: {1: int(target_uid), 2: region, 4: 1}}).hex(),
        _team_packet_prefix(region), key, iv
    )

def accept_team_invite(target_uid, group_id, key, iv, region="ID", game_version="1.132.9"):
    region = (str(region).upper() if region else "ID")
    fields = {
        1: 4,
        2: {
            1: int(target_uid), 3: int(target_uid),
            4: bytes.fromhex("0107090a0b120f19202729"), 8: 1,
            9: {
                1: "08FBA33B0522052002041B0222220007000C00010004000547E265AE1080779546762514110104076fa2e8770e748c3f6a68ed75000000ff08080500cacfa16d",
                2: 235, 3: {14: 80, 11: 86}, 4: "{Y\\R", 6: 13, 7: {2: 4},
                8: str(game_version), 9: 2, 10: 1, 11: "0362625351"
            },
            10: str(group_id), 11: {1: "IDC3", 2: 107, 3: region},
            13: "en", 16: "374f5219", 20: {1: 21}, 23: "a_6534489873065906362",
            24: "https://dl-sg-production.freefiremobile.com/", 27: {1: 2, 2: 4}
        }
    }
    return create_packet(create_proto(fields).hex(), _team_packet_prefix(region), key, iv)

def start_match_team(account_id, key, iv, region="ID"):
    region = (str(region).upper() if region else "ID")
    fields = {1: 9, 2: {1: int(account_id), 7: {1: "IDC3", 2: 410, 3: region}}}
    return create_packet(create_proto(fields).hex(), _team_packet_prefix(region), key, iv)

def ready_for_game(uid, key, iv, region="ID"):
    reg = str(region).upper() if region else "ID"
    pfx = "0519" if reg == "BD" else ("0514" if reg == "IND" else "0515")
    fields = {1: 15, 2: {1: int(uid), 2: 1}}
    return create_packet(create_proto(fields).hex(), pfx, key, iv)

def _extract_key_iv(res_json):
    if "__RAW_HEX__" in res_json and "__OFFSET__" in res_json:
        try:
            raw = bytes.fromhex(res_json["__RAW_HEX__"])
            off = int(res_json["__OFFSET__"])
            rf = extract_raw_fields(raw[off:])
            for kf, vf in [(22, 23), (24, 25), (6, 7)]:
                k = rf.get(kf); v = rf.get(vf)
                if isinstance(k, (bytes, bytearray)) and len(k) == 16 and \
                   isinstance(v, (bytes, bytearray)) and len(v) == 16:
                    return bytes(k), bytes(v)
        except Exception:
            pass
    found = {}
    for k, v in res_json.items():
        if str(k).startswith("__") or not isinstance(v, dict):
            continue
        data = v.get("data")
        raw = None
        if isinstance(data, (bytes, bytearray)) and len(data) == 16:
            raw = bytes(data)
        elif isinstance(data, str) and len(data) == 32:
            try:
                c = bytes.fromhex(data)
                if len(c) == 16:
                    raw = c
            except Exception:
                pass
        if raw and len(raw) == 16:
            try:
                found[int(k)] = raw
            except Exception:
                pass
    if len(found) < 2:
        return None, None
    for kf, vf in [(22, 23), (24, 25), (6, 7)]:
        if kf in found and vf in found:
            return found[kf], found[vf]
    sk = sorted(found.keys())
    return found[sk[0]], found[sk[1]]

async def aes_encrypt(payload, key, iv):
    return AES.new(key, AES.MODE_CBC, iv).encrypt(pad(payload, AES.block_size))

def get_app_version():
    try:
        return play_scraper('com.dts.freefireth').get('version')
    except Exception:
        return "1.132.9"

async def version_config(region="ID"):
    app_version = get_app_version()
    lang = REGION_LANG.get(region.upper(), "en")
    url = (
        f"https://version.ggwhitehawk.com/live/ver.php?version={app_version}"
        f"&lang={lang}&device=android&channel=android&appstore=googleplay"
        f"&region={region.upper()}&whitelist_version=1.3.0&whitelist_sp_version=1.0.0"
    )
    try:
        r = await client.get(url)
        j = r.json()
        server_url = j.get("server_url")
        remote_version = j.get("remote_version")
        latest_release_version = j.get("latest_release_version")
        gops = [u.strip() for u in j.get("gop_url", "").split(";") if u.strip()]
        gop_1 = gops[0] if gops else "https://ffmconnect.ppmainecoonghj.com"
        if not server_url:
            return None
        return latest_release_version, remote_version, server_url, gop_1, app_version
    except Exception:
        return None

async def get_access_token(uid, password):
    url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    hdrs = {
        "Host": "100067.connect.garena.com",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; SM-G998B)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br", "Connection": "close"
    }
    data = {
        "uid": str(uid), "password": password, "response_type": "token",
        "client_type": "2", "client_secret": HEX_KEY, "client_id": "100067"
    }
    for _ in range(4):
        try:
            r = await client.post(url, headers=hdrs, data=data)
            if r.status_code == 200:
                j = r.json()
                oid = j.get("open_id"); at = j.get("access_token"); pf = j.get("platform", 4)
                if oid and at:
                    return oid, at, pf
        except Exception:
            pass
        await asyncio.sleep(0.7)
    return None

def generate_signature(payload_str):
    return hmac.new(API_KEY, payload_str.encode(), hashlib.sha256).hexdigest()

async def register_account(password, gop_url, app_version):
    rp = {"app_id": 100067, "client_type": 2, "password": password, "source": 2}
    payload = json.dumps(rp, separators=(',', ':'))
    sig = generate_signature(payload)
    headers = {
        "User-Agent": f"GarenaMSDK/4.0.44(SM-E135F ;Android 14;en;GB;app {app_version} 2019118525;)",
        "Authorization": f"Signature {sig}", "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8"
    }
    for _ in range(3):
        try:
            connector = aiohttp.TCPConnector(resolver=aiohttp.ThreadedResolver())
            async with aiohttp.ClientSession(connector=connector) as s:
                async with s.post(f"{gop_url}/api/v2/oauth/guest:register",
                                  headers=headers, data=payload,
                                  timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    data = json.loads(await resp.text())
                    if data.get("code") == 0:
                        return data["data"]["uid"]
        except Exception:
            pass
        await asyncio.sleep(1.0)
    return None

async def grant_token(uid, password, gop_url, app_version):
    for _ in range(3):
        try:
            connector = aiohttp.TCPConnector(resolver=aiohttp.ThreadedResolver())
            gp = {
                "client_id": 100067, "client_secret": HEX_KEY, "client_type": 2,
                "device_id": f"02-{uuid.uuid4()}", "password": password,
                "response_type": "token", "uid": int(uid)
            }
            payload = json.dumps(gp, separators=(',', ':'))
            sig = generate_signature(payload)
            headers = {
                "User-Agent": f"GarenaMSDK/4.0.44(SM-E135F ;Android 14;en;GB;app {app_version} 2019118525;)",
                "Authorization": f"Signature {sig}", "Accept": "application/json",
                "Content-Type": "application/json; charset=utf-8"
            }
            async with aiohttp.ClientSession(connector=connector) as s:
                async with s.post(f"{gop_url}/api/v2/oauth/guest/token:grant",
                                  headers=headers, data=payload,
                                  timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    data = json.loads(await resp.text())
                    if data.get("code") == 0:
                        return data["data"]
        except Exception:
            pass
        await asyncio.sleep(1.0)
    return None

async def get_payload(access_token, open_id, platform, version, lang_code=None, region="IND"):
    # Build a region-consistent payload. The previous implementation always
    # advertised a fixed client version/device ID even when version_config()
    # returned a different India release version.
    region = str(region or "IND").strip().upper()
    lang_code = lang_code or REGION_LANG.get(region, "en")
    device_id = f"Google|{uuid.uuid4()}"
    major_login = {
        "3": str(datetime.now())[:-7], "4": "free fire", "5": 1,
        "7": str(version), "8": "Android OS 14 / API-34 (UP1A.231005.007/E156BXXS6AYD4)",
        "9": "Handheld", "10": "airtel", "11": "CarrierDataNetwork",
        "12": 2340, "13": 1080, "14": "295",
        "15": "ARM64 FP ASIMD AES | 2200 | 8", "16": 5586,
        "17": "Mali-G57 MC2", "18": "OpenGL ES 3.2 v1.r38p1",
        "19": device_id, "20": "27.61.46.111", "21": lang_code,
        "22": str(open_id), "23": str(platform), "24": "Handheld",
        "25": "samsung SM-A155F", "26": region, "29": str(access_token),
        "30": 1, "41": "airtel", "42": "4G",
        "57": "7428b253defc164018c604a1ebbfebdf",
        "60": 108009, "61": 3859, "62": 5023, "64": 3987,
        "65": 108009, "66": 3987, "67": 108009, "70": 4, "73": 3,
        "74": "/data/app/~~OlJmIW-Yzl-44x2WnJP4Nw==/com.garena.game.ffi-_eDk_pQQMiFk1YUeqwJBvQ==/lib/arm64",
        "76": 3,
        "77": "dd9d4c174e0472d34b7fd34bd5924bc9|/data/app/~~OlJmIW-Yzl-44x2WnJP4Nw==/com.garena.game.ffi-_eDk_pQQMiFk1YUeqwJBvQ==/base.apk",
        "78": 3, "79": 2, "81": "64", "83": "2019121269",
        "85": 3, "86": "OpenGLES2", "87": 8191, "88": int(platform),
        "90": "Coimbatore" if region == "IND" else "",
        "91": "TN" if region == "IND" else "",
        "92": 9570, "93": "android",
        "94": "KqsHT54jON6bxITmlrRyOrXWBqKqZ4BoqPzT/mhtriAfRt2dt7gC8pnAJfj11alcEUA5sD8BshSYQhxXT9RFmU6YzcI1FKK4MwxJcF4+kvelPD1H",
        "95": 111207, "96": "{\"cur_rate\":null,\"support_etc2\":false}",
        "97": 1, "99": str(platform), "100": str(platform),
        "104": 11921, "105": 1,
        "106": "https://dl-tata.freefireind.in/live/ABHotUpdates/|https://core-tata.freefireind.in/live/ABHotUpdates/|dff941d41e6e3a9e76f05ed71fdc8d87",
        "107": "1.6168622e0868ddbd",
    }
    get_login_data_dict = dict(major_login)
    # Keep the login-data packet's India locale fields explicit as in the
    # known regional payload layout, without mutating the MajorLogin packet.
    if region == "IND":
        get_login_data_dict["90"] = "Coimbatore"
        get_login_data_dict["91"] = "TN"
    proto1 = create_proto(major_login).hex()
    proto2 = create_proto(get_login_data_dict).hex()
    return bytes.fromhex(encrypt_aes(proto1)), bytes.fromhex(encrypt_aes(proto2))


async def major_login(payload, login_url, release_version):
    url = f"{login_url.rstrip('/')}/MajorLogin"
    req_headers = {
        "Accept": "*/*", "Authorization": "Bearer ",
        "Content-Type": "application/x-www-form-urlencoded",
        "ReleaseVersion": f"{release_version}", "User-Agent": "UnityPlayer/2018.4.12f1",
        "X-GA": "v1 1", "X-GA-SV": str(int(time.time())), "X-Unity-Version": "2018.4.12f1"
    }
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False; ssl_context.verify_mode = ssl.CERT_NONE
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.post(url, headers=req_headers, data=payload, ssl=ssl_context) as response:
                response_content = await response.read()
                if response.status != 200 or len(response_content) < 200:
                    return None
                best = None; best_score = -1; best_off = 0
                for offset in [64, 0, 48, 32, 80, 16, 128, 8, 96, 60, 56, 40, 24, 20, 12, 4]:
                    if offset >= len(response_content):
                        continue
                    cb = response_content[offset:]
                    cand = None
                    try:
                        cand = decode_protobuf_dict(cb)
                    except Exception:
                        cand = None
                    if not cand:
                        try:
                            c2 = decode_protobuf_2(cb)
                            if c2:
                                cand = {str(k): {"data": v} for k, v in c2.items()}
                        except Exception:
                            cand = None
                    if not cand:
                        continue
                    keys = set(cand.keys())
                    has_jwt = ("8" in keys) or (8 in keys)
                    has_url = ("10" in keys) or (10 in keys)
                    score = len(cand) + (100 if has_jwt else 0) + (50 if has_url else 0)
                    if score > best_score:
                        best = cand; best_score = score; best_off = offset
                    if has_jwt and has_url:
                        break
                if not best or (("8" not in best) and (8 not in best)):
                    return None
                best["__RAW_HEX__"] = response_content.hex()
                best["__OFFSET__"] = best_off
                return best
    except Exception:
        return None

async def get_login_data(payload, jwt_token, server_url, release_version):
    url = f"{server_url.rstrip('/')}/GetLoginData"
    hdrs = {
        "Accept": "*/*", "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/x-www-form-urlencoded",
        "ReleaseVersion": f"{release_version}", "User-Agent": "UnityPlayer/2018.4.12f1",
        "X-GA": "v1 1", "X-GA-SV": str(int(time.time())), "X-Unity-Version": "2018.4.12f1"
    }
    try:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False; ssl_ctx.verify_mode = ssl.CERT_NONE
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as s:
            async with s.post(url, headers=hdrs, data=payload, ssl=ssl_ctx) as r:
                if r.status != 200:
                    return None
                content = await r.read()
                for off in [0, 64, 48, 32, 80, 16, 128, 8, 96]:
                    if off >= len(content):
                        continue
                    try:
                        c = decode_protobuf_dict(content[off:])
                        if c and len(c) >= 3:
                            return c
                    except Exception:
                        pass
                for off in [0, 64, 48, 32, 80]:
                    if off >= len(content):
                        continue
                    c = decode_protobuf_2(content[off:])
                    if c and len(c) >= 3:
                        return {str(k): {"data": v} for k, v in c.items()}
        return None
    except Exception:
        return None

async def get_player_personal_show(target_uid, jwt_token, server_url, release_version):
    url = f"{server_url}/GetPlayerPersonalShow"
    payload = bytes.fromhex(encrypt_aes(create_proto({"1": int(target_uid)}).hex()))
    hdrs = {
        "authorization": f"Bearer {jwt_token}",
        "host": server_url.replace("https://", "").split("/")[0],
        "x-ga": "v1 1", "content-type": "application/x-www-form-urlencoded",
        "releaseversion": f"{release_version}",
        "user-agent": "UnityPlayer/2022.3.47f1", "accept": "*/*",
        "x-unity-version": "2022.3.47f1"
    }
    try:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False; ssl_ctx.verify_mode = ssl.CERT_NONE
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as s:
            async with s.post(url, headers=hdrs, data=payload, ssl=ssl_ctx) as r:
                if r.status != 200:
                    return None
                return decode_protobuf_2(await r.read())
    except Exception:
        return None

# ==================== CLAN ====================
def _get_region_from_jwt(jwt_token):
    try:
        p = jwt_token.split('.')[1]
        p += '=' * (-len(p) % 4)
        d = json.loads(base64.urlsafe_b64decode(p))
        return (d.get('lock_region') or d.get('noti_region') or 'BD').upper()
    except Exception:
        return "ID"


def _get_region_url(region):
    region = str(region or "ID").upper()
    if region == "BD":
        return "https://clientbp.ggpolarbear.com"
    if region == "IND":
        return "https://clientbp.freefireind.in"
    if region in ["BR", "US", "NA"]:
        return "https://client.us.freefiremobile.com"
    return "https://clientbp.ggpolarbear.com"


def _create_clan_payload(clan_id):
    if not _CLAN_PB_AVAILABLE:
        return None
    try:
        msg = reqClan_pb2.MyMessage()
        msg.field_1 = int(clan_id)
        raw = msg.SerializeToString()
        return AES.new(AES_KEY, AES.MODE_CBC, AES_IV).encrypt(pad(raw, AES.block_size))
    except Exception as e:
        print_error(f"CLAN payload: {e}")
        return None


async def join_clan(jwt_token, clan_id):
    if not _CLAN_PB_AVAILABLE:
        print_warning("CLAN join unavailable: reqClan_pb2 not loaded")
        return False
    try:
        region = _get_region_from_jwt(jwt_token)
        base_url = _get_region_url(region)
        url = base_url.rstrip("/") + "/RequestJoinClan"
        host = base_url.replace("https://", "")
        payload = _create_clan_payload(clan_id)
        if not payload:
            return False
        hdrs = {
            "Authorization": f"Bearer {jwt_token}",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB55",
            "Content-Type": "application/octet-stream",
            "Host": host,
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
        }
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.post(url, headers=hdrs, data=payload, ssl=ssl_ctx) as response:
                if response.status == 200:
                    print_success(f"CLAN Join sent for {clan_id} ({region})")
                    return True
                print_warning(f"CLAN Join status {response.status} ({region})")
                return False
    except Exception as e:
        print_error(f"CLAN {e}")
        return False

async def build_tcp_startup_packet(account_id, token, server_time, key, iv, region="ID", typ='OnLine'):
    uid_hex = f"{int(account_id):016x}"
    ts_hex = f"{int(server_time):08x}"
    enc = (await aes_encrypt(token.encode(), key, iv)).hex()
    enc_len = f"{len(enc) // 2:08x}"
    reg = str(region).upper() if region else "ID"
    if typ == 'OnLine':
        pfx = '7219' if reg == 'BD' else ('7214' if reg == 'IND' else '7215')
        return f"{pfx}{uid_hex}{ts_hex}00000000{enc_len}{enc}"
    pfx = '8119' if reg == 'BD' else ('8114' if reg == 'IND' else '8115')
    return f"{pfx}{uid_hex}{ts_hex}{enc_len}{enc}"

async def send_keep_alive(region="ID"):
    reg = str(region).upper() if region else "ID"
    return bytes.fromhex("0219" if reg == "ID" else ("0214" if reg == "IND" else "0215"))

async def start_game_battle_royale(region, client_version, writer, key, iv):
    packet = bytes.fromhex("0314000001e0a8c1becfcdd1a311df1b23e218f8b6ae1df958f76dfeb6bfd0399d153d1f9687174c189de3900d11f3eb8fd92cd831c482b06adec14632935703a0423b76051274d67f1381e5794cc6256079d1514ad9f9fa864733257d8e5910e9ba2f048dbe5008ba23d7e4db609ceb46ab823a50a15d0692d44c73d1f6c8e9ee33462952f2685ef8b32faea409a9b61ea091f3a36a727773dbb8316c01dfa6512dbe5b3a3ce6c8310783386c9c70c8fe143f6bc39854fdd1fffd157e52ef006a9e1e944b252a0072154aa34a45b7a5f080d7043eaf0ec6dd884b62b906781cdecca9d49f50f521c4a57dcefc4e5c274f242dcad6489dae6795c2173803fb1d343f64d47699164508e95709a43f018efca4eab791ff4010aab17d1926f7d5e11983249879940d90d5f257ad66dc0e193716addb278510de0afa48825d24ec20724382d731a2f2258ace8a4e614bfb620dc90ee9c3a87e5deaed1d44efdb561e320bc9faab91aea632d060f4ffa268067ab588edd6342c086059accb30d036b3cf766858f54b434d446935912e0e9c21b7e22ace9f17852366bd2390988f82545239e54baafcfd7bcd75d8a69a327019f8b608d80a49cbb6a65b31eec3fcab74afee3da4a9d59e367edd3f32d8eb0b8b516bcfbc1e104bd8c8bda5b76f8e5190ec1898d004dc")
    try:
        proto = thunderFF_pb2.StartMatch()
        proto.ParseFromString(packet)
        if hasattr(proto.main, 'region_list') and len(proto.main.region_list) > 0:
            proto.main.region_list[0].region = region
            if len(proto.main.region_list) > 1:
                proto.main.region_list[1].region = region
        if hasattr(proto.main, 'client_version'):
            proto.main.client_version.remote_version = client_version
        p = proto.SerializeToString()
    except Exception:
        p = packet
    reg = str(region).upper() if region else "BD"
    pkt_prefix = '0319' if reg == 'BD' else ('0314' if reg == 'IND' else '0315')
    encrypted_packet = (await aes_encrypt(p, key, iv)).hex()
    hex_length = f"{len(encrypted_packet) // 2:08x}"
    writer.write(bytes.fromhex(pkt_prefix + hex_length + encrypted_packet))
    await writer.drain()

async def tea_enc(v0, v1, k0, k1, k2, k3):
    s = 0
    for _ in range(_ROUNDS):
        s = (s + _DELTA) & 0xFFFFFFFF
        v0 = (v0 + (((((v1 << 4) & 0xFFFFFFFF) + k0) & 0xFFFFFFFF ^ ((v1 + s) & 0xFFFFFFFF) ^ (((v1 >> 5) + k1) & 0xFFFFFFFF)))) & 0xFFFFFFFF
        v1 = (v1 + (((((v0 << 4) & 0xFFFFFFFF) + k2) & 0xFFFFFFFF ^ ((v0 + s) & 0xFFFFFFFF) ^ (((v0 >> 5) + k3) & 0xFFFFFFFF)))) & 0xFFFFFFFF
    return v0, v1

async def tea_dec(v0, v1, k0, k1, k2, k3):
    s = (_DELTA * _ROUNDS) & 0xFFFFFFFF
    for _ in range(_ROUNDS):
        v1 = (v1 - (((((v0 << 4) & 0xFFFFFFFF) + k2) & 0xFFFFFFFF ^ ((v0 + s) & 0xFFFFFFFF) ^ (((v0 >> 5) + k3) & 0xFFFFFFFF)))) & 0xFFFFFFFF
        v0 = (v0 - (((((v1 << 4) & 0xFFFFFFFF) + k0) & 0xFFFFFFFF ^ ((v1 + s) & 0xFFFFFFFF) ^ (((v1 >> 5) + k1) & 0xFFFFFFFF)))) & 0xFFFFFFFF
        s = (s - _DELTA) & 0xFFFFFFFF
    return v0, v1

async def tea_cbc_encrypt(padded, key_bytes):
    k0, k1, k2, k3 = (struct.unpack_from("<I", key_bytes, o)[0] for o in (0, 4, 8, 12))
    out = bytearray(len(padded)); pc = bytearray(8); pi = bytearray(8)
    for i in range(0, len(padded), 8):
        x = bytearray(8)
        for j in range(8):
            x[j] = padded[i + j] ^ pc[j]
        e0, e1 = await tea_enc(struct.unpack_from("<I", x, 0)[0], struct.unpack_from("<I", x, 4)[0], k0, k1, k2, k3)
        enc = bytearray(8)
        struct.pack_into("<I", enc, 0, e0); struct.pack_into("<I", enc, 4, e1)
        for j in range(8):
            out[i + j] = enc[j] ^ pi[j]
        pc[:] = out[i:i + 8]; pi[:] = x
    return bytes(out)

async def tea_cbc_decrypt(body, key_bytes):
    k0, k1, k2, k3 = (struct.unpack_from("<I", key_bytes, o)[0] for o in (0, 4, 8, 12))
    out = bytearray(len(body)); pi = bytearray(8); pc = bytearray(8)
    x = bytearray(8); dec = bytearray(8)
    for i in range(0, len(body), 8):
        for j in range(8):
            x[j] = body[i + j] ^ pi[j]
        d0, d1 = await tea_dec(struct.unpack_from("<I", x, 0)[0], struct.unpack_from("<I", x, 4)[0], k0, k1, k2, k3)
        struct.pack_into("<I", dec, 0, d0); struct.pack_into("<I", dec, 4, d1)
        for j in range(8):
            out[i + j] = dec[j] ^ pc[j]
        pc[:] = body[i:i + 8]; pi[:] = dec
    return bytes(out)

async def build_padded(content):
    pad_len = (8 - (len(content) + 10) % 8) % 8
    return bytes([pad_len, 0, 0]) + b"\x00" * pad_len + content + b"\x00" * 7

async def encode_header(layout, so, cmd, oid, flags, length, k, v80):
    out = bytearray()
    for code in layout:
        val = {0: so, 1: cmd, 2: oid, 3: flags, 4: length}[code]
        if _FIELD_SIZES[code] == 1:
            out.append((val & 0xFF) ^ k)
        else:
            v = ((val & 0xFFFF) ^ v80) & 0xFFFF
            out.append(v & 0xFF); out.append((v >> 8) & 0xFF)
    return bytes(out)

async def crc7_buff(crc, buf):
    c = crc & 0x7F
    for b in buf:
        c = CRC7_TABLE[((2 * (c & 0xFF)) ^ (b & 0xFF)) & 0xFF] & 0x7F
    return c & 0x7F

async def sv_frame(msg_key, layout, so, cmd, oid, flags, content, key, encrypted=True):
    k = key[0]; v80 = ((k << 8) | k) & 0xFFFF
    body = await tea_cbc_encrypt(await build_padded(content), key) if encrypted else content
    hdr = bytearray([msg_key, 0]) + await encode_header(layout, so, cmd, oid, flags, len(body), k, v80)
    pkt = bytearray(hdr + body)
    pkt[1] = await crc7_buff(0, bytes(pkt[2:])) & 0x7F
    return bytes(pkt)

async def build_match_startup_packets(token, udp_key, match_code, account_id, block_val,
                                      server_ip="", region="ID", client_version="1.132.9",
                                      client_version_code="2019121229",
                                      access_token="", mode_id=1, map_id=1):
    token = token.strip()
    udp_key = bytes.fromhex(udp_key)
    match_code = [int(ch) for ch in str(match_code).strip()]
    thunder_jwt = token[:660] if len(token) > 660 else token
    sharma_jwt = token[660:] if len(token) > 660 else ""
    eth = thunder_jwt.encode() if isinstance(thunder_jwt, str) else thunder_jwt
    esh = sharma_jwt.encode() if isinstance(sharma_jwt, str) else sharma_jwt
    garena420 = await has_ssan_zig(len(eth)) + eth
    reg = str(region).upper() if region else "ID"
    csoversea_block = bytes.fromhex(
        "ca0163736f7665727365612e7374726f6e67686f6c642e66726565666972656d6f62696c652e636f6d"
        "3b302e302e302e303b33342e3132362e37362e34353b33342e38372e3137372e31343b33342e38372e"
        "3137302e3233303b33352e3138352e3138332e35370000000000000100000000000000000000000001"
        "00000800000100000000000100a8a2d7bebd8d8bdf110200"
    )
    mid = bytes.fromhex('0000000001000102030101') + await has_ssan_zig(len(reg)) + reg.encode()
    mid += bytes.fromhex('0001030003000004')
    mid += await has_ssan_zig(len(client_version)) + client_version.encode()
    mid += await has_ssan_zig(len(client_version_code)) + client_version_code.encode()
    mid += csoversea_block
    clean_ip = server_ip.split(':')[0] if server_ip else "0.0.0.0"
    mid += await has_ssan_zig(len(clean_ip)) + clean_ip.encode()
    clean_acc_tok = access_token.strip() if access_token else ""
    if clean_acc_tok:
        mid += await has_ssan_zig(len(clean_acc_tok)) + clean_acc_tok.encode()
    mid += await has_ssan_zig(len(esh)) + esh
    tg = (
        await uleb_encode(int(account_id)) + await uleb_encode(int(block_val)) +
        await uleb_encode(1) + await uleb_encode(int(mode_id)) +
        await uleb_encode(int(block_val)) + await uleb_encode(int(map_id)) + mid
    )
    process = await sv_frame(0x5E, match_code, 2, 447, 0, 1, garena420, udp_key)
    loading = await sv_frame(0x5A, match_code, 2, 448, 1, 1, tg, udp_key)
    return process.hex(), loading.hex()

async def build_hello_packet(text, key, layout):
    data = text.encode("utf-8")
    if len(data) > 25:
        raise ValueError("too long")
    content = b"\x10\x00\x00\x00" + data + b"\x00" * (29 - 4 - len(data))
    k = key[0]; v80 = ((k << 8) | k) & 0xFFFF
    layout = [int(c) for c in str(layout).strip()] if isinstance(layout, str) else list(layout)
    padded = await build_padded(content)
    enc_body = await tea_cbc_encrypt(padded, key)
    hbytes = await encode_header(layout, 1, 1, 0, 1, len(enc_body), k, v80)
    pkt = bytearray([0x63, 0x00]) + hbytes + enc_body
    pkt[1] = await crc7_buff(0, pkt[2:]) & 0x7F
    return bytes(pkt).hex()

async def classify(frame):
    cmd = frame["cmd"]
    msg_name = MESSAGE_ID_TO_NAME.get(cmd, f"UNKNOWN_{cmd}")
    if msg_name == "UDP_HELLO":
        return "HELLO"
    if msg_name == "UDP_ACK":
        return "ACK"
    if msg_name == "UDP_PING":
        return "PING"
    if msg_name == "RUDP_JOIN_MATCH":
        return "JOIN_MATCH"
    return msg_name

async def build_packet(msg_key, layout, so, cmd, oid, flags, content, key, encrypted=True):
    k = key[0]; v80 = ((k << 8) | k) & 0xFFFF
    body = await tea_cbc_encrypt(await build_padded(content), key) if encrypted else content
    hdr = bytearray([msg_key, 0])
    for code in layout:
        val = {0: so, 1: cmd, 2: oid, 3: flags, 4: len(body)}[code]
        if _FIELD_SIZES[code] == 1:
            hdr.append((val & 0xFF) ^ k)
        else:
            v = ((val & 0xFFFF) ^ v80) & 0xFFFF
            hdr.append(v & 0xFF); hdr.append((v >> 8) & 0xFF)
    pkt = bytearray(hdr + body)
    pkt[1] = await crc7_buff(0, bytes(pkt[2:])) & 0x7F
    return bytes(pkt)

async def layouts_from_mask(mask):
    if isinstance(mask, (bytes, bytearray)):
        mask = mask.decode("utf-8", errors="ignore")
    s = "".join(ch for ch in str(mask).strip() if ch in "01234")
    ru = [int(c) for c in s] if len(s) == 5 else [0, 1, 4, 3, 2]
    nr = [c for c in ru if c != 2]
    return ru, nr

async def reply_for(frame, key, mask, ack_key=0x68, ping_key=0x6D, hello_key=0x5B, ack_style="short"):
    ru, nr = await layouts_from_mask(mask)
    typ = await classify(frame)
    if typ == "HELLO":
        if ack_style == "echo":
            content = frame["content"] if frame["content"] else b"\x10\x00\x00\x00"
            return typ, await build_packet(hello_key, nr, 1, 1, None, 1, content, key)
        return typ, await build_packet(ack_key, nr, 0, 2, None, 1, b"\x01\x00", key)
    if typ == "ACK":
        return typ, await build_packet(ack_key, nr, 0, 2, None, 1, frame["content"] or b"\x01\x00", key)
    if typ == "PING":
        c = frame["content"]
        counter = c[:4] if len(c) >= 4 else c
        return typ, await build_packet(ping_key, nr, 0, 3, None, 0, counter + b"\x00\x00\x00", key, encrypted=False)
    if typ == "JOIN_MATCH":
        return typ, await build_packet(ack_key, nr, 0, 2, None, 1, b"\x02\x00", key)
    return typ, None

async def keepalive_ping(sock, ip, port, key_bytes, mask, stop_event):
    nr = (await layouts_from_mask(mask))[1]
    ping_keys = [0x66, 0x6D, 0x69, 0x6C, 0x6B, 0x6E, 0x6F, 0x70]
    loop = asyncio.get_event_loop(); i = 0
    while not stop_event.is_set():
        pk = ping_keys[i % len(ping_keys)]
        counter = int(time.time() * 1000) & 0xFFFFFFFF
        pkt = await build_packet(pk, nr, 0, 3, None, 0, struct.pack("<I", counter) + b"\x00\x00\x00", key_bytes, encrypted=False)
        try:
            await loop.sock_sendto(sock, pkt, (ip, port))
        except Exception:
            pass
        i += 1
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=3.0)
        except asyncio.TimeoutError:
            pass

async def try_header(buf, layout, k, v80):
    off = 2; out = {}
    for code in layout:
        size = _FIELD_SIZES[code]
        if off + size > len(buf):
            return None
        out[_FIELD_NAMES[code]] = (buf[off] ^ k) if size == 1 else (((buf[off] | (buf[off + 1] << 8)) ^ v80) & 0xFFFF)
        off += size
    out["headerLen"] = off
    return out

async def oicq_unpad(padded):
    if not padded or len(padded) < 8:
        return None
    if not all(padded[-1 - i] == 0 for i in range(7)):
        return None
    pad_len = padded[0] & 0x07
    s = 3 + pad_len; e = len(padded) - 7
    return padded[s:e] if s < e else b""

async def decode_packet(packet, key, mask=None):
    data = bytes(packet) if isinstance(packet, bytes) else bytes.fromhex(packet)
    if len(data) < 8:
        return None
    k = key[0]; v80 = ((k << 8) | k) & 0xFFFF
    crc_ok = (data[1] & 0x7F) == await crc7_buff(0, data[2:])
    candidates = []
    if mask:
        ru, nr = await layouts_from_mask(mask)
        layouts = [("RUDP", ru), ("nonRUDP", nr)]
        if nr != [0, 1, 4, 3]:
            layouts.append(("nonRUDP", [0, 1, 4, 3]))
        if ru != [0, 1, 4, 3, 2]:
            layouts.append(("RUDP", [0, 1, 4, 3, 2]))
    else:
        layouts = [("RUDP", list(p)) for p in itertools.permutations([0, 1, 2, 3, 4])]
        layouts += [("nonRUDP", list(p)) for p in itertools.permutations([0, 1, 3, 4])]
    for idx_l, (kind, layout) in enumerate(layouts):
        f = await try_header(data, layout, k, v80)
        if not f or f["flags"] > 7 or f["sendOption"] > 7:
            continue
        exact_len = (f["length"] == len(data) - f["headerLen"])
        ack_piggy = bool(f["flags"] & 4) and (0 <= f["length"] <= len(data) - f["headerLen"] - 1) and (len(data) - f["headerLen"] - f["length"] <= 32)
        if not (exact_len or ack_piggy):
            continue
        body = data[len(data) - f["length"]:] if f["length"] > 0 else b""
        content = None
        if f["flags"] & 1:
            if len(body) < 8 or len(body) % 8 != 0:
                continue
            padded = await tea_cbc_decrypt(body, key)
            content = await oicq_unpad(padded)
            if content is None:
                continue
        else:
            content = body
        score = (2 if crc_ok else 0) + (2 if idx_l < 2 else 0) + (1 if exact_len else 0) + (1 if content is not None else 0)
        candidates.append({
            "kind": kind, "layout": layout, "headerLen": f["headerLen"],
            "msgKey": data[0], "cmd": f["cmd"], "flags": f["flags"],
            "sendOption": f["sendOption"], "orderId": f.get("orderId"),
            "length": f["length"], "content": content, "crcOk": crc_ok, "score": score
        })
    if not candidates:
        return None
    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates[0]

_match_counters: Dict[str, int] = {}
_match_counter_lock = asyncio.Lock()

async def _inc_match(uid):
    async with _match_counter_lock:
        _match_counters[uid] = _match_counters.get(uid, 0) + 1
        return _match_counters[uid]

async def _dec_match(uid):
    async with _match_counter_lock:
        if uid in _match_counters and _match_counters[uid] > 0:
            _match_counters[uid] -= 1
        return _match_counters.get(uid, 0)

_token_cache_memo: Dict[str, Any] = {}
_token_cache_memo_time: float = 0.0
_TOKEN_CACHE_MEMO_TTL = 5.0

def _json_serializer(obj):
    if isinstance(obj, (bytes, bytearray)):
        return {"__bytes_hex__": bytes(obj).hex()}
    raise TypeError(f"Type {type(obj)} not serializable")

def _json_deserializer(obj):
    if isinstance(obj, dict):
        if "__bytes_hex__" in obj and len(obj) == 1:
            try:
                return bytes.fromhex(obj["__bytes_hex__"])
            except Exception:
                return b""
        return {k: _json_deserializer(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_deserializer(x) for x in obj]
    return obj

def _load_token_cache():
    global _token_cache_memo, _token_cache_memo_time
    now = time.time()
    if _token_cache_memo and (now - _token_cache_memo_time) < _TOKEN_CACHE_MEMO_TTL:
        return _token_cache_memo
    if not os.path.exists(TOKEN_CACHE_FILE):
        return {}
    try:
        with open(TOKEN_CACHE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return {}
        parsed = _json_deserializer(json.loads(content))
        _token_cache_memo = parsed; _token_cache_memo_time = now
        return parsed
    except Exception:
        return {}

def _save_token_cache(cache):
    global _token_cache_memo, _token_cache_memo_time
    try:
        with open(TOKEN_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, default=_json_serializer)
        _token_cache_memo = cache; _token_cache_memo_time = time.time()
    except Exception:
        pass

def cache_get(uid):
    cache = _load_token_cache()
    e = cache.get(str(uid))
    if not e:
        return None
    if time.time() - e.get("cached_at", 0) > TOKEN_CACHE_TTL:
        cache_invalidate(uid); return None
    if str(e.get("account_id", "")).isdigit():
        e["account_id"] = int(e["account_id"])
    if not isinstance(e.get("login_payload_data"), (bytes, bytearray)):
        cache_invalidate(uid); return None
    return e

def cache_set(uid, data):
    cache = _load_token_cache()
    e = dict(data); e["cached_at"] = time.time()
    cache[str(uid)] = e; _save_token_cache(cache)

def cache_invalidate(uid):
    cache = _load_token_cache()
    if str(uid) in cache:
        del cache[str(uid)]; _save_token_cache(cache)

_squad_match_slots: Dict[str, Dict[str, int]] = {}
_squad_slot_lock = asyncio.Lock()
_bot_is_external_invite: Dict[str, bool] = {}

async def _assign_squad_slot(uid_str: str, match_key: str = "default", is_external: bool = False) -> int:
    async with _squad_slot_lock:
        m_slots = _squad_match_slots.setdefault(str(match_key), {})
        if uid_str in m_slots:
            return m_slots[uid_str]
        taken = set(m_slots.values())
        if is_external:
            taken.add(1)
            candidate_slots = (2, 3, 4)
        else:
            candidate_slots = (1, 2, 3, 4)
        assigned = next((s for s in candidate_slots if s not in taken), candidate_slots[len(m_slots) % len(candidate_slots)])
        m_slots[uid_str] = assigned
        return assigned

async def _release_squad_slot(uid_str: str, match_key: str = "default"):
    async with _squad_slot_lock:
        m_key = str(match_key)
        if m_key in _squad_match_slots:
            _squad_match_slots[m_key].pop(uid_str, None)
            if not _squad_match_slots[m_key]:
                _squad_match_slots.pop(m_key, None)

async def play_game(server_ip_port, thunder, sharma, udp_key, match_code,
                    account_id, player_region, client_version, key, iv, match_index):
    match_start_time = time.time()
    ping_task = None; sock = None
    ping_stop = asyncio.Event()
    movement_ctrl = None
    uid_str = str(account_id)
    completed_cleanly = False
    try:
        ip, port = server_ip_port.split(":")
        port = int(port)
        resolved_ip = await resolve_host_cloudflare(ip)
        loop = asyncio.get_event_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind(('0.0.0.0', 0))
        except Exception:
            pass
        optimize_udp_socket(sock); sock.setblocking(False)
        udp_key_bytes = bytes.fromhex(udp_key)
        hello_packet = await build_hello_packet(f"{account_id}_2585", udp_key_bytes, match_code)
        await loop.sock_sendto(sock, bytes.fromhex(hello_packet), (resolved_ip, port))
        ack_state = "waiting_for_hello_reply"
        thunder_sent = False
        thunder_sent_time = 0.0
        last_thunder_retry = 0.0
        join_match_received = False
        local_closed = False
        send_lock = asyncio.Lock()
        ping_task = asyncio.create_task(keepalive_ping(sock, resolved_ip, port, udp_key_bytes, match_code, ping_stop))
        last_activity = time.time()
        match_key = f"{server_ip_port}_{match_code}"
        is_ext = _bot_is_external_invite.get(uid_str, False)
        assigned_slot = await _assign_squad_slot(uid_str, match_key, is_external=is_ext)
        movement_ctrl = MovementController(
            account_id=account_id, account_region=player_region,
            key=key, iv=iv, tcp_writer=None,
            udp_sock=sock, udp_server=(resolved_ip, port),
            udp_key_bytes=udp_key_bytes, match_code=match_code,
            slot_id=assigned_slot
        )

        async def _emit_startup_burst():
            await loop.sock_sendto(sock, bytes.fromhex(thunder), (resolved_ip, port))
            await asyncio.sleep(0.25)
            prepare_ack = await build_packet(0x68, (await layouts_from_mask(match_code))[1], 0, 2, None, 1, b"\x01\x00", udp_key_bytes)
            await loop.sock_sendto(sock, prepare_ack, (resolved_ip, port))
            await asyncio.sleep(0.35)
            await loop.sock_sendto(sock, bytes.fromhex(sharma), (resolved_ip, port))
            await asyncio.sleep(0.25)
            ru, _ = await layouts_from_mask(match_code)
            await loop.sock_sendto(sock, await build_packet(0x60, ru, 2, 899, 2, 1, b"", udp_key_bytes), (resolved_ip, port))
            await loop.sock_sendto(sock, await build_packet(0x60, ru, 2, 899, 8, 1, b"", udp_key_bytes), (resolved_ip, port))

        async def send_thunder_sharma_inline():
            nonlocal ack_state, thunder_sent, thunder_sent_time, last_thunder_retry
            if thunder_sent:
                return
            async with send_lock:
                if thunder_sent:
                    return
                try:
                    thunder_sent = True
                    thunder_sent_time = time.time()
                    last_thunder_retry = thunder_sent_time
                    await _emit_startup_burst()
                    ack_state = "thunder_sharma_sent"
                    movement_ctrl.start()
                except Exception:
                    pass

        while not local_closed:
            now_t = time.time()
            if now_t - match_start_time > MAX_MATCH_DURATION:
                completed_cleanly = True; break
            if ack_state == "thunder_sharma_sent":
                if (now_t - last_activity) > MATCH_IDLE_TIMEOUT:
                    completed_cleanly = movement_ctrl.has_real_coords; break
                if not movement_ctrl.has_real_coords:
                    if (now_t - match_start_time) > 65.0:
                        completed_cleanly = False; break
                    if thunder_sent_time > 0 and (now_t - last_thunder_retry) >= 8.0:
                        last_thunder_retry = now_t
                        try:
                            ru, _ = await layouts_from_mask(match_code)
                            await loop.sock_sendto(sock, await build_packet(0x60, ru, 2, 899, 2, 1, b"", udp_key_bytes), (resolved_ip, port))
                            await loop.sock_sendto(sock, await build_packet(0x60, ru, 2, 899, 8, 1, b"", udp_key_bytes), (resolved_ip, port))
                        except Exception:
                            pass
            try:
                response, server_addr = await asyncio.wait_for(loop.sock_recvfrom(sock, 65535), timeout=2.0)
                if response:
                    last_activity = time.time()
                    frame = await decode_packet(response, udp_key_bytes, match_code)
                    if frame:
                        if movement_ctrl:
                            movement_ctrl.handle_server_frame(frame)
                        ptype = await classify(frame)
                        if frame['cmd'] == 103:
                            completed_cleanly = True; local_closed = True; continue
                        if frame['cmd'] == 101:
                            try:
                                ack = await build_packet(0x68, (await layouts_from_mask(match_code))[1], 0, 2, None, 1, b"\x01\x00", udp_key_bytes)
                                await loop.sock_sendto(sock, ack, server_addr)
                            except Exception:
                                pass
                            continue
                        if ptype in ["ACK", "PING", "HELLO", "JOIN_MATCH"]:
                            if ptype == "HELLO" and ack_state == "waiting_for_hello_reply":
                                _, reply = await reply_for(frame, udp_key_bytes, match_code, ack_style="short")
                                if reply:
                                    await loop.sock_sendto(sock, reply, server_addr)
                                ack_state = "ack_sent_waiting"
                            elif ptype == "ACK":
                                if ack_state == "waiting_for_hello_reply":
                                    _, reply = await reply_for(frame, udp_key_bytes, match_code)
                                    if reply:
                                        await loop.sock_sendto(sock, reply, server_addr)
                                    ack_state = "ready_to_send_thunder"
                                elif ack_state == "ack_sent_waiting":
                                    ack_state = "ready_to_send_thunder"
                                else:
                                    _, reply = await reply_for(frame, udp_key_bytes, match_code)
                                    if reply:
                                        await loop.sock_sendto(sock, reply, server_addr)
                            elif ptype == "PING":
                                _, reply = await reply_for(frame, udp_key_bytes, match_code)
                                if reply:
                                    await loop.sock_sendto(sock, reply, server_addr)
                            elif ptype == "JOIN_MATCH" and not join_match_received:
                                _, reply = await reply_for(frame, udp_key_bytes, match_code)
                                if reply:
                                    await loop.sock_sendto(sock, reply, server_addr)
                                    join_match_received = True
            except asyncio.TimeoutError:
                if ack_state in ("ready_to_send_thunder", "ack_sent_waiting") and not thunder_sent:
                    await send_thunder_sharma_inline()
                elif ack_state == "waiting_for_hello_reply":
                    if (time.time() - last_activity) > 5.0:
                        try:
                            pkt = await build_hello_packet(f"{account_id}_2585", udp_key_bytes, match_code)
                            await loop.sock_sendto(sock, bytes.fromhex(pkt), (resolved_ip, port))
                        except Exception:
                            pass
                        last_activity = time.time()
                    if (time.time() - match_start_time) > 25.0:
                        break
                elif ack_state == "thunder_sharma_sent":
                    if (time.time() - last_activity) > MATCH_IDLE_TIMEOUT:
                        completed_cleanly = movement_ctrl.has_real_coords; break
            except Exception:
                await asyncio.sleep(0.5)
            if ack_state == "ready_to_send_thunder" and not thunder_sent:
                await send_thunder_sharma_inline()
        return f"match #{match_index} finished"
    except Exception:
        return f"match #{match_index} error"
    finally:
        try:
            await _release_squad_slot(uid_str, match_key)
        except Exception:
            pass
        _bot_is_external_invite.pop(uid_str, None)
        if movement_ctrl:
            try:
                await movement_ctrl.stop()
            except Exception:
                pass
        if completed_cleanly:
            try:
                bot_state.increment_match(uid_str)
                async def _post_exp(uid):
                    for wait in (5.0, 8.0, 12.0):
                        await asyncio.sleep(wait)
                        await refresh_account_profile(uid)
                asyncio.create_task(_post_exp(uid_str))
            except Exception:
                pass
        ping_stop.set()
        if ping_task:
            ping_task.cancel()
            try:
                await ping_task
            except asyncio.CancelledError:
                pass
        if sock:
            try:
                sock.close()
            except Exception:
                pass
        remaining = await _dec_match(uid_str)
        try:
            bot_state.update_status(uid_str, "ONLINE" if remaining == 0 else "IN_MATCH", remaining)
        except Exception:
            pass

def _extract_invite_fields(dec: dict, dec2: dict, own_id_str: str):
    """0500 প্যাকেট থেকে সম্ভাব্য group_id এবং inviter_uid নিরাপদে বের করা।"""
    def _unwrap(v):
        if isinstance(v, dict) and "data" in v:
            return v["data"]
        return v

    f5_raw = _unwrap(dec.get("5") or dec.get(5))
    f5_2 = dec2.get(5) if isinstance(dec2.get(5), dict) else {}

    def _collect_strings(obj, out):
        if isinstance(obj, str):
            s = obj.strip()
            if 10 <= len(s) <= 64 and not s.isdigit():
                out.append(s)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                val = _unwrap(v)
                if k in (8, "8", 10, "10") and isinstance(val, str) and len(val.strip()) >= 6:
                    out.insert(0, val.strip())
                _collect_strings(val, out)
        elif isinstance(obj, list):
            for it in obj:
                _collect_strings(it, out)

    def _collect_uids(obj, out):
        if isinstance(obj, int):
            s = str(obj)
            if 7 <= len(s) <= 15 and s != own_id_str:
                out.append(s)
        elif isinstance(obj, str) and obj.isdigit():
            if 7 <= len(obj) <= 15 and obj != own_id_str:
                out.append(obj)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                val = _unwrap(v)
                if k in (1, "1", 2, "2", 3, "3", 6, "6") and str(val).isdigit() and 7 <= len(str(val)) <= 15 and str(val) != own_id_str:
                    out.insert(0, str(val))
                _collect_uids(val, out)
        elif isinstance(obj, list):
            for it in obj:
                _collect_uids(it, out)

    str_cands: List[str] = []
    uid_cands: List[str] = []
    for src in (f5_2, f5_raw, dec2, dec):
        _collect_strings(src, str_cands)
        _collect_uids(src, uid_cands)

    group_id = str_cands[0] if str_cands else None
    inviter = uid_cands[0] if uid_cands else None
    return inviter, group_id

async def functional_lone_wolf(addrs, starter_packet, account_region, client_version,
                               key, iv, account_id="", account_data=None, max_reconnects=999999):
    reconnects = 0
    ip, port = addrs.split(":")
    play_matches: List[asyncio.Task] = []
    no_response_count = 0
    search_attempts = 0
    last_start_time = 0.0
    uid_str = str(account_id)

    current_token = starter_packet
    current_key = key; current_iv = iv
    current_account_data = account_data
    _writer_ref = {"w": None}
    _team_active = {"flag": True}
    _match_played = {"flag": False}

    async def _team_coordinator():
        try:
            while _team_active["flag"] and not _match_played["flag"]:
                if bot_state.is_paused(uid_str):
                    return
                wait_t0 = time.time()
                while _team_active["flag"] and not _match_played["flag"]:
                    async with _team_state["lock"]:
                        n = len(_team_state["peers"])
                    in_match_count = sum(
                        1 for u, a in bot_state.accounts.items()
                        if "IN_MATCH" in str(a.get("status", "")).upper()
                    )
                    total_workers = max(getattr(bot_state, "expected_workers", 0), n)
                    expected_n = max(2, total_workers - in_match_count)
                    wait_elapsed = time.time() - wait_t0
                    required_n = min(max(2, int(TEAM_SIZE)), max(2, int(expected_n)))

                    if n >= required_n or wait_elapsed >= 20.0:
                        break
                    if bot_state.is_paused(uid_str):
                        return
                    await asyncio.sleep(0.5)

                await asyncio.sleep(1.5)
                async with _team_state["lock"]:
                    now_ts = time.time()
                    valid_locked = []
                    for lsq in _team_state.get("locked_squads", []):
                        m_list = [u for u in lsq.get("members", []) if u in _team_state["peers"]]
                        if len(m_list) >= 2 and m_list[0] == lsq["members"][0] and (now_ts - lsq.get("created_at", 0.0)) < 75.0:
                            valid_locked.append({"members": m_list, "created_at": lsq["created_at"]})
                    locked_uids = {u for lsq in valid_locked for u in lsq["members"]}
                    unassigned_peers = {u: p for u, p in _team_state["peers"].items() if u not in locked_uids}
                    if len(unassigned_peers) >= 2:
                        for sq in _compute_smart_squads(unassigned_peers):
                            if len(sq) >= 2:
                                valid_locked.append({"members": list(sq), "created_at": now_ts})
                    _team_state["locked_squads"] = valid_locked
                    squads = [list(lsq["members"]) for lsq in valid_locked]
                    _team_state["squads"] = squads
                    _team_state["uid_to_leader"].clear()
                    _team_state["uid_to_squad_idx"].clear()
                    my_squad = None
                    my_squad_idx = 0
                    for s_idx, sq in enumerate(squads, start=1):
                        lead_u = sq[0]
                        for u in sq:
                            _team_state["uid_to_leader"][u] = lead_u
                            _team_state["uid_to_squad_idx"][u] = s_idx
                        if uid_str in sq:
                            my_squad = list(sq)
                            my_squad_idx = s_idx
                    if squads:
                        _team_state["leader_uid"] = squads[0][0]
                    sig = tuple(tuple(sq) for sq in squads)
                    if _team_state.get("partition_sig") != sig and squads:
                        _team_state["partition_sig"] = sig
                        print_info(f"[SQUAD] Formed squads: {squads}")
                    peers_snapshot = dict(_team_state["peers"])

                if not my_squad or len(my_squad) < 2:
                    await asyncio.sleep(3.5)
                    continue

                my_leader = my_squad[0]
                if my_leader != uid_str:
                    # মেম্বার বট লিডারের ইনভাইটের জন্য অপেক্ষা করবে
                    member_wait_t0 = time.time()
                    while _team_active["flag"] and not _match_played["flag"] and (time.time() - member_wait_t0) < 70.0:
                        await asyncio.sleep(1.0)
                        if bot_state.is_paused(uid_str):
                            return
                        async with _team_state["lock"]:
                            cur_lead = _team_state["uid_to_leader"].get(uid_str)
                            lead_in_lobby = (my_leader in _team_state["peers"])
                        if not lead_in_lobby or (cur_lead and cur_lead != my_leader):
                            break
                    continue

                # লিডার রুম তৈরি করে মেম্বারদের ইনভাইট পাঠাবে
                await asyncio.sleep((my_squad_idx - 1) * 0.5)
                own_id_num = int(current_account_data.get('account_id', uid_str)) if current_account_data else int(uid_str)
                try:
                    w = _writer_ref["w"]
                    if w and not w.is_closing():
                        w.write(leave_team(own_id_num, current_key, current_iv, region=account_region))
                        await w.drain()
                        await asyncio.sleep(0.6)
                        w.write(create_team(current_key, current_iv, region=account_region, game_version=client_version))
                        await w.drain()
                except Exception:
                    pass
                await asyncio.sleep(2.0)

                for peer_uid in my_squad[1:]:
                    peer_info = peers_snapshot.get(peer_uid, {})
                    peer_acc_id = None
                    try:
                        peer_acc_id = peer_info["data"].get("account_id")
                    except Exception:
                        pass
                    target_id = int(peer_acc_id or peer_uid)
                    try:
                        w = _writer_ref["w"]
                        if w and not w.is_closing():
                            w.write(invite_player_in_team(target_id, current_key, current_iv, region=account_region))
                            await w.drain()
                    except Exception:
                        pass
                    await asyncio.sleep(0.8)

                # মেম্বারদের টিমে জয়েন হওয়ার জন্য যথেষ্ট সময় দেওয়া
                await asyncio.sleep(8.0)
                try:
                    bot_state.update_status(uid_str, "SEARCHING", 0)
                except Exception:
                    pass

                leader_cycles = 0
                while _team_active["flag"] and not _match_played["flag"] and leader_cycles < 3:
                    leader_cycles += 1
                    try:
                        if bot_state.is_paused(uid_str):
                            break
                        async with _team_state["lock"]:
                            if _team_state["uid_to_leader"].get(uid_str) != uid_str:
                                break
                        w = _writer_ref["w"]
                        if w and not w.is_closing():
                            w.write(start_match_team(own_id_num, current_key, current_iv, region=account_region))
                            await w.drain()
                    except Exception:
                        pass
                    try:
                        await asyncio.wait_for(asyncio.sleep(16.0), timeout=16.5)
                    except asyncio.TimeoutError:
                        pass

                if _team_active["flag"] and not _match_played["flag"]:
                    async with _team_state["lock"]:
                        _team_state["locked_squads"] = [
                            lsq for lsq in _team_state.get("locked_squads", [])
                            if lsq.get("members", [None])[0] != uid_str
                        ]
                    try:
                        w = _writer_ref["w"]
                        if w and not w.is_closing():
                            w.write(leave_team(own_id_num, current_key, current_iv, region=account_region))
                            await w.drain()
                    except Exception:
                        pass
                    await asyncio.sleep(1.5)
        except asyncio.CancelledError:
            raise
        except Exception:
            pass

    try:
        while True:
            while bot_state.is_paused(uid_str):
                try:
                    bot_state.update_status(uid_str, "PAUSED", 0)
                except Exception:
                    pass
                await asyncio.sleep(1.0)
            writer = None; gateway_ping_task = None; team_coord_task = None
            try:
                if current_account_data:
                    fresh = None
                    if current_account_data.get('auth_type') == 'guest' and current_account_data.get('auth_uid'):
                        fresh = cache_get(str(current_account_data['auth_uid']))
                    elif current_account_data.get('auth_type') == 'token' and current_account_data.get('auth_token'):
                        fresh = cache_get(f"tok_{current_account_data['auth_token'][:20]}")
                    if fresh:
                        current_account_data = fresh
                        current_key = fresh['aes_ak']; current_iv = fresh['iv_i']
                        uid_str = str(fresh.get('account_id', uid_str))
                        current_token = await build_tcp_startup_packet(
                            fresh['account_id'], fresh['token'], fresh['server_time'],
                            current_key, current_iv,
                            region=fresh.get('region', account_region), typ='OnLine'
                        )
                    else:
                        raise ConnectionError("Cache expired")

                resolved_ip = await resolve_host_cloudflare(ip)
                reader, writer = await asyncio.open_connection(resolved_ip, int(port))
                bot_state.register_writer(uid_str, writer)
                _writer_ref["w"] = writer
                raw_sock = writer.get_extra_info('socket')
                if raw_sock:
                    optimize_tcp_socket(raw_sock)
                writer.write(bytes.fromhex(current_token)); await writer.drain()

                try:
                    init_ka = await send_keep_alive(account_region)
                    if init_ka and not writer.is_closing():
                        writer.write(init_ka)
                        await asyncio.wait_for(writer.drain(), timeout=3)
                except Exception:
                    pass

                async def func_gateway_keepalive():
                    ka_bytes = await send_keep_alive(account_region)
                    while True:
                        await asyncio.sleep(5)
                        try:
                            if writer and not writer.is_closing():
                                writer.write(ka_bytes); await writer.drain()
                        except Exception:
                            break

                gateway_ping_task = asyncio.create_task(func_gateway_keepalive())

                own_id_init = int(current_account_data.get('account_id', uid_str)) if current_account_data else int(uid_str)
                try:
                    if writer and not writer.is_closing():
                        writer.write(leave_team(own_id_init, current_key, current_iv, region=account_region))
                        await writer.drain()
                except Exception:
                    pass

                reconnects = 0; no_response_count = 0
                async with _team_state["lock"]:
                    _team_state["peers"][uid_str] = {
                        "writer": writer, "data": current_account_data,
                        "key": current_key, "iv": current_iv
                    }
                    if _team_state["leader_uid"] is None:
                        _team_state["leader_uid"] = uid_str
                try:
                    await _mark_team_joined(uid_str)
                except Exception:
                    pass

                async def send_solo_start_match():
                    nonlocal search_attempts
                    search_attempts += 1
                    try:
                        bot_state.update_status(uid_str, "SEARCHING", 0)
                        await asyncio.sleep(random.uniform(0.2, 0.4))
                        rdy = ready_for_game(own_id_init, current_key, current_iv, region=account_region)
                        if writer and not writer.is_closing():
                            writer.write(rdy); await writer.drain()
                        await asyncio.sleep(1.0)
                        await start_game_battle_royale(account_region, client_version, writer, current_key, current_iv)
                    except Exception:
                        pass

                if not _match_played["flag"]:
                    if not TEAM_MODE:
                        await send_solo_start_match()
                    else:
                        team_coord_task = asyncio.create_task(_team_coordinator())

                _accepted_groups = set()
                _tcp_buf = bytearray()
                while True:
                    play_matches[:] = [m for m in play_matches if not m.done()]
                    if bot_state.is_paused(uid_str):
                        break
                    if _match_played["flag"]:
                        try:
                            data = await asyncio.wait_for(reader.read(8192), timeout=1.0)
                        except asyncio.TimeoutError:
                            continue
                        if not data:
                            raise ConnectionError("Connection closed")
                        continue

                    now = asyncio.get_running_loop().time()
                    if not TEAM_MODE and len(play_matches) == 0 and (now - last_start_time >= START_MATCH_INTERVAL):
                        await send_solo_start_match()
                        last_start_time = now

                    data = None
                    while len(_tcp_buf) >= 5:
                        if _tcp_buf[1] == 0x00:
                            plen = int.from_bytes(_tcp_buf[2:5], "big")
                            if 0 <= plen <= 131072:
                                if len(_tcp_buf) < 5 + plen:
                                    break
                                data = bytes(_tcp_buf[:5 + plen])
                                del _tcp_buf[:5 + plen]
                                break
                        data = bytes(_tcp_buf)
                        _tcp_buf.clear()
                        break

                    if data is None:
                        try:
                            chunk = await asyncio.wait_for(reader.read(8192), timeout=0.5)
                        except asyncio.TimeoutError:
                            no_response_count += 1; continue
                        if not chunk:
                            raise ConnectionError("Connection closed")
                        no_response_count = 0
                        _tcp_buf.extend(chunk)
                        continue

                    hex_data = data.hex(); packet_length = len(data)

                    # ==================== TEAM / INVITE PACKET (0500) ====================
                    if hex_data.startswith("0500") and packet_length > 10:
                        try:
                            inner = bytes.fromhex(hex_data[10:])
                            dec2 = decode_protobuf_2(inner) or {}
                            dec = decode_protobuf_dict(inner)
                            if not dec and dec2:
                                dec = {str(k): {"data": v} for k, v in dec2.items()}

                            d4w = dec.get("4") or dec.get(4)
                            d4 = d4w.get("data") if isinstance(d4w, dict) and "data" in d4w else (d4w or dec2.get(4))
                            f5_2 = dec2.get(5) if isinstance(dec2.get(5), dict) else {}

                            if d4 == 1 and isinstance(f5_2.get(6), dict):
                                honor_val = f5_2[6].get(64)
                                if isinstance(honor_val, int):
                                    if honor_val < 60:
                                        _restricted_57_uids.add(uid_str)
                                    else:
                                        _restricted_57_uids.discard(uid_str)

                            inviter, group_id = _extract_invite_fields(dec, dec2, uid_str)
                            if inviter and group_id:
                                inviter_str = str(inviter)
                                is_ext = (inviter_str not in bot_state.accounts) and (inviter_str not in bot_state.account_workers)
                                async with _team_state["lock"]:
                                    assigned_leader = _team_state["uid_to_leader"].get(uid_str)
                                is_own_squad_leader = (assigned_leader == uid_str)

                                if is_ext or (not is_own_squad_leader and (assigned_leader is None or inviter_str == str(assigned_leader))):
                                    grp_key = (inviter_str, str(group_id))
                                    if grp_key not in _accepted_groups:
                                        _accepted_groups.add(grp_key)
                                        _bot_is_external_invite[uid_str] = is_ext
                                        if writer and not writer.is_closing():
                                            writer.write(leave_team(own_id_init, current_key, current_iv, region=account_region))
                                            await writer.drain()
                                            await asyncio.sleep(0.25)
                                            writer.write(accept_team_invite(
                                                int(inviter_str), group_id,
                                                current_key, current_iv,
                                                region=account_region,
                                                game_version=client_version
                                            ))
                                            await writer.drain()
                        except Exception:
                            pass
                        continue

                    # ==================== MATCH FOUND PACKET (0300) ====================
                    if hex_data.startswith("0300") and packet_length >= 300:
                        async with _team_state["lock"]:
                            _team_state["peers"].pop(uid_str, None)
                            _team_state["uid_to_leader"].pop(uid_str, None)
                            _team_state["uid_to_squad_idx"].pop(uid_str, None)
                            _team_state["locked_squads"] = [
                                lsq for lsq in _team_state.get("locked_squads", [])
                                if uid_str not in lsq.get("members", [])
                            ]
                            if _team_state["leader_uid"] == uid_str:
                                _team_state["leader_uid"] = None
                                _team_state["team_code"] = None
                        try:
                            await _mark_match_found(uid_str)
                            await _clear_team_joined(uid_str)
                        except Exception:
                            pass
                        if team_coord_task and not team_coord_task.done():
                            team_coord_task.cancel()
                        team_coord_task = None
                        _team_active["flag"] = True
                        _accepted_groups.clear()

                        try:
                            res = json.loads(await decode_protobuf_async(hex_data[10:]))
                            token = udp_key = match_code = server_ip_port = None
                            match_account_id = block_val = None
                            if '42' in res and 'data' in res['42']:
                                match_code = res['42']['data']
                            if '5' in res and 'data' in res['5']:
                                rf5 = res['5']['data']
                                server_ip_port = rf5.get('2', {}).get('data')
                                udp_key = rf5.get('3', {}).get('data')
                                token = rf5.get('4', {}).get('data')
                                block_val = rf5.get('1', {}).get('data')
                                if '42' in rf5:
                                    match_code = rf5['42']['data']
                            if '1' in res and 'data' in res['1']:
                                match_account_id = res['1']['data']

                            effective_acc_id = match_account_id or account_id or "BD_BOT"
                            if token and udp_key and match_code and server_ip_port:
                                if isinstance(match_code, (bytes, bytearray)):
                                    match_code = match_code.decode("utf-8", errors="ignore").strip()
                                else:
                                    match_code = str(match_code).strip()
                                acc_tok = current_account_data.get('access_token', '') if current_account_data else ""
                                thunder, sharma = await build_match_startup_packets(
                                    token, udp_key, match_code, effective_acc_id, block_val or 0,
                                    server_ip=server_ip_port, region=account_region,
                                    client_version=client_version, access_token=acc_tok,
                                    mode_id=1, map_id=1
                                )
                                match_index = await _inc_match(uid_str)
                                bot_state.increment_match_started()
                                bot_state.update_status(uid_str, "IN_MATCH (TEAM)", 1)

                                new_match = asyncio.create_task(
                                    play_game(
                                        server_ip_port, thunder, sharma, udp_key,
                                        match_code, effective_acc_id, account_region or "VN",
                                        client_version, current_key, current_iv,
                                        match_index=match_index
                                    )
                                )
                                play_matches.append(new_match)

                                async def drain_gw():
                                    while not new_match.done():
                                        try:
                                            dg = await asyncio.wait_for(reader.read(4096), timeout=1.0)
                                            if not dg:
                                                break
                                        except asyncio.TimeoutError:
                                            continue
                                        except Exception:
                                            break

                                drain_task = asyncio.create_task(drain_gw())
                                try:
                                    await new_match
                                finally:
                                    drain_task.cancel()
                                    try:
                                        await drain_task
                                    except asyncio.CancelledError:
                                        pass
                                play_matches[:] = [m for m in play_matches if not m.done()]
                                _match_played["flag"] = False
                                _team_active["flag"] = True
                                await asyncio.sleep(2.0)
                                break
                        except Exception:
                            continue
            except asyncio.CancelledError:
                raise
            except Exception as e:
                if "Cache expired" in str(e):
                    await asyncio.sleep(2); break
                reconnects += 1
                if reconnects > max_reconnects:
                    reconnects = 0; break
                await asyncio.sleep(min(reconnects * 0.5, 2.0))
            finally:
                _team_active["flag"] = False
                async with _team_state["lock"]:
                    _team_state["peers"].pop(uid_str, None)
                    _team_state["uid_to_leader"].pop(uid_str, None)
                    _team_state["uid_to_squad_idx"].pop(uid_str, None)
                    if _team_state["leader_uid"] == uid_str:
                        _team_state["leader_uid"] = None
                        _team_state["team_code"] = None
                try:
                    await _clear_team_joined(uid_str)
                except Exception:
                    pass
                if team_coord_task and not team_coord_task.done():
                    team_coord_task.cancel()
                    try:
                        await team_coord_task
                    except asyncio.CancelledError:
                        pass
                if gateway_ping_task:
                    gateway_ping_task.cancel()
                if writer:
                    bot_state.unregister_writer(uid_str, writer)
                    await safe_close_writer(writer)
                if not _match_played["flag"]:
                    _team_active["flag"] = True
    except asyncio.CancelledError:
        raise
    finally:
        for m in play_matches:
            if not m.done():
                m.cancel()

async def informational(addrs, starter_packet, key, iv, region="ID",
                        account_id="", max_reconnects=3, account_data=None):
    uid_str = str(account_id); reconnects = 0
    ip, port = addrs.split(":")
    while True:
        while uid_str and bot_state.is_paused(uid_str):
            await asyncio.sleep(1.0)
        writer = None; ping_task = None
        try:
            resolved_ip = await resolve_host_cloudflare(ip)
            reader, writer = await asyncio.open_connection(resolved_ip, int(port))
            if uid_str:
                bot_state.register_writer(uid_str, writer)
            raw_sock = writer.get_extra_info('socket')
            if raw_sock:
                optimize_tcp_socket(raw_sock)
            writer.write(bytes.fromhex(starter_packet)); await writer.drain()
            reconnects = 0
            async def info_ka():
                ka = await send_keep_alive(region)
                while True:
                    await asyncio.sleep(5)
                    try:
                        if writer and not writer.is_closing():
                            writer.write(ka); await writer.drain()
                    except Exception:
                        break
            ping_task = asyncio.create_task(info_ka())
            while True:
                if uid_str and bot_state.is_paused(uid_str):
                    if ping_task:
                        ping_task.cancel()
                    if uid_str:
                        bot_state.unregister_writer(uid_str, writer)
                    await safe_close_writer(writer); writer = None
                    while bot_state.is_paused(uid_str):
                        await asyncio.sleep(1.0)
                    break
                try:
                    data = await asyncio.wait_for(reader.read(8192), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                if not data:
                    raise ConnectionError("closed")
        except asyncio.CancelledError:
            if ping_task:
                ping_task.cancel()
            if uid_str:
                bot_state.unregister_writer(uid_str, writer)
            await safe_close_writer(writer); raise
        except Exception:
            if ping_task:
                ping_task.cancel()
            if uid_str:
                bot_state.unregister_writer(uid_str, writer)
            await safe_close_writer(writer)
            reconnects += 1
            if reconnects > max_reconnects:
                await asyncio.sleep(3); reconnects = 0
            else:
                await asyncio.sleep(1)

def _register_credentials(ad):
    try:
        bot_state.account_credentials[str(ad['account_id'])] = ad
        if ad.get('auth_uid'):
            bot_state.account_credentials[str(ad['auth_uid'])] = ad
    except Exception:
        pass

async def refresh_account_profile(ad_or_uid):
    try:
        if isinstance(ad_or_uid, str):
            uid = str(ad_or_uid); ad = bot_state.account_credentials.get(uid)
        else:
            ad = ad_or_uid; uid = str(ad.get('account_id'))
        if not ad:
            return
        token = ad.get('token'); acc_id = ad.get('account_id')
        srv = ad.get('server_url'); rel = ad.get('release_version')
        if not (token and acc_id and srv and rel):
            return
        data = await get_player_personal_show(int(acc_id), token, srv, rel)
        if not data:
            return
        pd = data.get(1, {}) if isinstance(data.get(1), dict) else {}
        nickname = pd.get(3); lvl = pd.get(6); exp = pd.get(7)
        if exp is None:
            return
        exp = int(exp); lvl = int(lvl) if lvl else 1
        aid = str(acc_id)
        if aid not in bot_state.accounts:
            bot_state.register_account(aid, nickname or f"Player_{aid}", region=ad.get('region', 'BD'), level=lvl, exp=exp, auth_uid=ad.get('auth_uid'))
            return
        bot_state.update_exp(aid, exp, lvl)
        if nickname:
            bot_state.accounts[aid]["nickname"] = nickname
    except Exception:
        pass

async def process_account_uid_pass(uid, password, region_override=None):
    requested_region = str(region_override or "ID").strip().upper()
    cached = cache_get(uid)
    # Do not reuse a token/session cached for a different game region.
    if cached and str(cached.get("region", "")).strip().upper() == requested_region:
        aid = str(cached['account_id'])
        nick = cached.get('nickname', f"Player_{aid}")
        lvl = cached.get('level', 1); expv = cached.get('exp', 0)
        print_premium(f"Online (cache): {aid} | {nick} | region={cached.get('region')}",
                      color=PX.MINT, icon=I["check"])
        bot_state.register_account(aid, nick, cached.get('region', requested_region),
            lvl, expv, cached.get('likes',0), auth_uid=str(uid))
        _register_credentials(cached); return cached
    if cached:
        cache_invalidate(uid)
        print_warning(f"[LOGIN] Cache region mismatch; fresh {requested_region} login required")
    print_info(f"LOGIN UID: {uid} | requested_region={requested_region}")
    try:
        async with _LOGIN_SEMAPHORE:
            vc = await version_config(requested_region)
            if not vc:
                print_error(f"[LOGIN] Version config unavailable for region={requested_region}")
                return None
            release_version, client_version, server_url, gop_1, app_version = vc
            if not (release_version and client_version and server_url):
                print_error(f"[LOGIN] Incomplete version config for region={requested_region}")
                return None
            tg = await get_access_token(uid, password)
            if not tg:
                print_error(f"[LOGIN] Garena access-token grant failed for UID={uid}")
                return None
            open_id, access_token, platform = tg
            major_payload, login_payload = await get_payload(
                access_token, open_id, platform, client_version,
                region=requested_region)
            res_json = await major_login(major_payload, server_url, release_version)
            if not res_json:
                print_error(f"[LOGIN] MajorLogin rejected/undecodable for region={requested_region}")
                return None
            def _gd(k):
                v = res_json.get(str(k), res_json.get(k))
                if isinstance(v, dict) and "data" in v:
                    return v["data"]
                if v is not None and not isinstance(v, dict):
                    return v
                return None
            acc_id_raw = _gd(1); region_raw = _gd(2) or requested_region
            jwt_token = _gd(8); server_url_raw = _gd(10); server_time = _gd(21)
            aes_ak, iv_i = _extract_key_iv(res_json)
            if not acc_id_raw or not jwt_token or not server_url_raw or not aes_ak or not iv_i:
                print_error("[LOGIN] MajorLogin response missing account/JWT/server/AES fields")
                return None
            getlogin_json = await get_login_data(
                login_payload, jwt_token, server_url_raw, release_version)
            if not getlogin_json:
                print_error(f"[LOGIN] GetLoginData failed for UID={uid} region={requested_region}")
                return None
        def _gf(f, d=None):
            item = getlogin_json.get(str(f), getlogin_json.get(f))
            v = item.get("data") if isinstance(item, dict) else item
            return v if v is not None else d
        level = int(_gf(6,1) or 1); exp = int(_gf(7,0) or 0)
        likes = int(_gf(8,0) or 0)
        nickname = _gf(4, f"Player_{acc_id_raw}") or f"Player_{acc_id_raw}"
        region = str(region_raw or _gf(3, requested_region) or requested_region).upper()
        acc_id = str(acc_id_raw)
        bot_state.register_account(acc_id, nickname, region, level, exp, likes, auth_uid=str(uid))
        print_premium(f"Login: {acc_id} | {nickname} | Lvl {level} | region={region}",
                      color=PX.GOLD, icon=I["gem"])
        ad = {'account_id':acc_id_raw,'nickname':nickname,'region':region,
            'level':level,'exp':exp,'likes':likes,'open_id':open_id,
            'access_token':access_token,'platform':str(platform),
            'token':jwt_token,'server_time':server_time,
            'aes_ak':aes_ak,'iv_i':iv_i,
            'functional_addrs':_gf(14),'informational_addrs':_gf(32),
            'release_version':release_version,'client_version':client_version,
            'server_url':server_url_raw,'login_payload_data':login_payload,
            'auth_type':'guest','auth_uid':uid,'auth_password':password}
        _register_credentials(ad); cache_set(uid, ad); return ad
    except Exception as e:
        print_error(f"login err: {e}"); return None


async def run_account_worker(ad, label, region_override=None, clan_override=None):
    acc_id = str(ad['account_id'])
    info_task = None; exp_task = None
    try:
        reg = region_override or ad.get('region', 'BD')
        tcp_online = await build_tcp_startup_packet(ad['account_id'], ad['token'], ad['server_time'], ad['aes_ak'], ad['iv_i'], region=reg, typ='OnLine')
        tcp_chat = await build_tcp_startup_packet(ad['account_id'], ad['token'], ad['server_time'], ad['aes_ak'], ad['iv_i'], region=reg, typ='ChaT')
        if clan_override:
            try:
                await asyncio.sleep(1.0)
                await join_clan(ad['token'], clan_override)
            except Exception:
                pass
        info_task = asyncio.create_task(informational(ad['informational_addrs'], tcp_chat, ad['aes_ak'], ad['iv_i'], region=reg, account_id=acc_id, account_data=ad))

        async def exp_refresher():
            while True:
                await asyncio.sleep(90 + random.uniform(-10, 10))
                fresh = bot_state.account_credentials.get(acc_id)
                if fresh:
                    await refresh_account_profile(fresh)

        exp_task = asyncio.create_task(exp_refresher())
        await functional_lone_wolf(
            ad['functional_addrs'], tcp_online, reg, ad['client_version'],
            ad['aes_ak'], ad['iv_i'], account_id=acc_id, account_data=ad
        )
    except asyncio.CancelledError:
        raise
    except Exception:
        pass
    finally:
        for t in (info_task, exp_task):
            if t and not t.done():
                t.cancel()
        for t in (info_task, exp_task):
            if t:
                try:
                    await t
                except Exception:
                    pass

async def account_loop_guest(uid, password, region_override=None, clan_override=None):
    uid_str = str(uid)
    bot_state.account_workers[uid_str] = asyncio.current_task()
    acc_id = None
    while True:
        try:
            bot_state.update_status(uid_str, "CONNECTING")
            ad = await process_account_uid_pass(uid_str, password, region_override)
            if not ad:
                await asyncio.sleep(15); continue
            acc_id = str(ad['account_id'])
            bot_state.account_workers[acc_id] = asyncio.current_task()
            bot_state.auth_to_game_id[uid_str] = acc_id
            bot_state.game_to_auth_id[acc_id] = uid_str
            await run_account_worker(ad, acc_id, region_override, clan_override)
            await asyncio.sleep(3)
        except asyncio.CancelledError:
            try:
                bot_state.update_status(uid_str, "OFFLINE")
                if acc_id:
                    bot_state.update_status(acc_id, "OFFLINE")
            except Exception:
                pass
            try:
                await _clear_team_joined(uid_str)
                if acc_id:
                    await _clear_team_joined(acc_id)
            except Exception:
                pass
            break
        except Exception:
            await asyncio.sleep(10)

async def _autoload_accounts():
    accounts = None
    # Priority 1: Read from ACCOUNTS_JSON env var (for Render / cloud deploy)
    env_accounts = os.environ.get("ACCOUNTS_JSON", "").strip()
    if env_accounts:
        try:
            accounts = json.loads(env_accounts)
            print_info("Loaded accounts from ACCOUNTS_JSON environment variable")
        except Exception as e:
            print_error(f"Failed to parse ACCOUNTS_JSON env var: {e}")
            accounts = None
    # Priority 2: Read from accounts.json file
    if accounts is None:
        if not os.path.exists(ACCOUNTS_FILE):
            return
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                accounts = json.load(f) or []
        except Exception:
            return
    if not isinstance(accounts, list) or not accounts:
        return
    bot_state.expected_workers = sum(
        1 for a in accounts if isinstance(a, dict) and str(a.get("uid", "")).strip() and str(a.get("password", "")).strip()
    )
    for a in accounts:
        try:
            if not isinstance(a, dict):
                continue
            uid = str(a.get("uid", "")).strip()
            password = str(a.get("password", "")).strip()
            region = str(a.get("region", "")).strip() or None
            clan_id = str(a.get("clan_id", "")).strip() or CLAN_ID_DEFAULT
            if not uid or not password:
                continue
            task = asyncio.create_task(account_loop_guest(uid, password, region_override=region, clan_override=clan_id))
            bot_state.account_workers[uid] = task
            await asyncio.sleep(0.25)
        except Exception:
            pass

async def api_ping(request):
    return aiohttp.web.json_response({"pong": True, "app": "SHANTO", "version": "2.1"})

async def start_web_server():
    app = aiohttp.web.Application()
    app.router.add_get("/", api_ping)
    app.router.add_get("/health", api_ping)
    app.router.add_get("/api/ping", api_ping)
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    for attempt in range(5):
        try:
            site = aiohttp.web.TCPSite(runner, WEB_HOST, WEB_PORT)
            await site.start()
            print(f"Health server listening on {WEB_HOST}:{WEB_PORT}")
            break
        except OSError:
            if attempt == 4:
                raise
            await asyncio.sleep(1.0)
    return runner

async def main():
    print_banner()
    if NETWORK_REFERENCE.get("loaded"):
        print_success(
            "Network reference loaded: "
            f"{NETWORK_REFERENCE['record_count']} captured Free Fire records, "
            f"{NETWORK_REFERENCE['endpoint_count']} endpoint entries, "
            f"{len(NETWORK_REFERENCE['domains'])} domains; "
            f"protocols={','.join(NETWORK_REFERENCE['protocols']) or 'n/a'}"
        )
        print_info("Observed domains: " + ", ".join(NETWORK_REFERENCE['domains']))
        print_warning(
            "Capture is metadata-only; encrypted HTTPS contents are unavailable. "
            "Observed hosts are diagnostic references and are not forced as API/server routes."
        )
    else:
        print_warning("Network reference not loaded: " + NETWORK_REFERENCE.get("reason", "unknown error"))
    try:
        await start_web_server()
    except Exception:
        return
    try:
        await _autoload_accounts()
    except Exception:
        pass
    asyncio.create_task(_no_match_watchdog())
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        for t in list(bot_state.account_workers.values()):
            t.cancel()
        await asyncio.gather(*bot_state.account_workers.values(), return_exceptions=True)
        try:
            await client.aclose()
        except Exception:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
