"""Shared transport/storage helpers; each service owns a different SQLite file."""
import hashlib
import hmac
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from fastapi import Header, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from .domain import DomainError, TASKS


class Command(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_version: int = Field(ge=1)
    action: str
    values: dict[str, Any] = Field(default_factory=dict)


def principal(authorization: str = Header(default='')):
    token = authorization.removeprefix('Bearer ')
    candidates = [
        (os.getenv('NZ_CLIENT_TOKEN', 'demo-client-token'), {'subject': 'demo-client', 'role': 'client'}),
        (os.getenv('NZ_OTHER_TOKEN', 'demo-other-token'), {'subject': 'other-client', 'role': 'client'}),
        (os.getenv('NZ_OFFICER_TOKEN', 'demo-officer-token'), {'subject': 'demo-officer', 'role': 'officer'}),
        (os.getenv('NZ_INTERNAL_TOKEN', 'demo-internal-token'), {'subject': 'incident-service', 'role': 'internal'}),
    ]
    for secret, user in candidates:
        if authorization.startswith('Bearer ') and secret and hmac.compare_digest(token, secret):
            return user
    raise HTTPException(401, 'A valid demo bearer token is required')


def authorise(user, case=None, officer=False):
    if officer and user['role'] != 'officer':
        raise HTTPException(403, 'Officer role required')
    if case and user['role'] != 'officer' and case['owner'] != user['subject']:
        raise HTTPException(403, 'This case belongs to another user')
    if user['role'] == 'internal':
        raise HTTPException(403, 'Internal token is limited to licence context')


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
              PRAGMA journal_mode=WAL;
              CREATE TABLE IF NOT EXISTS cases(id TEXT PRIMARY KEY, body TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT, process TEXT, task_id TEXT, activity TEXT, timestamp TEXT,
                resource TEXT, actor TEXT);
              CREATE TABLE IF NOT EXISTS idempotency(scope TEXT, key TEXT, fingerprint TEXT,
                case_id TEXT, PRIMARY KEY(scope,key));
              CREATE TABLE IF NOT EXISTS licences(id TEXT PRIMARY KEY, body TEXT NOT NULL);
            ''')

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def append_events(db, case, ids, actor):
        for task in ids:
            label, resource = TASKS[task]
            db.execute('INSERT INTO events(case_id,process,task_id,activity,timestamp,resource,actor) VALUES (?,?,?,?,?,?,?)',
                       (case['id'],case['process'],task,label,datetime.now(timezone.utc).isoformat(),resource,actor))

    def create(self, process, data, user, key):
        authorise(user)
        if not key or len(key)>128:
            raise HTTPException(400, 'Idempotency-Key of 1 to 128 characters required')
        scope = user['subject'] + ':' + process
        fingerprint = hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            previous = db.execute('SELECT * FROM idempotency WHERE scope=? AND key=?',(scope,key)).fetchone()
            if previous:
                if previous['fingerprint'] != fingerprint:
                    raise HTTPException(409, 'Idempotency key reused with different payload')
                return json.loads(db.execute('SELECT body FROM cases WHERE id=?',(previous['case_id'],)).fetchone()['body'])
            case = {'id': process+'-'+uuid.uuid4().hex[:12], 'process':process,
                    'owner':user['subject'],'state':'SUBMITTED','version':1,'data':data,
                    'created_at':datetime.now(timezone.utc).isoformat(),
                    'updated_at':datetime.now(timezone.utc).isoformat()}
            db.execute('INSERT INTO cases VALUES (?,?)',(case['id'],json.dumps(case)))
            self.append_events(db,case,[{'P1':'A1','P2':'V1','P3':'I1'}[process]],user['subject'])
            db.execute('INSERT INTO idempotency VALUES (?,?,?,?)',(scope,key,fingerprint,case['id']))
            return case

    def get(self, case_id):
        with self.connect() as db:
            row = db.execute('SELECT body FROM cases WHERE id=?',(case_id,)).fetchone()
        if not row:
            raise HTTPException(404, 'Case not found')
        return json.loads(row['body'])

    def apply(self, case_id, expected, user, function):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT body FROM cases WHERE id=?',(case_id,)).fetchone()
            if not row:
                raise HTTPException(404,'Case not found')
            old = json.loads(row['body'])
            authorise(user,old)
            if old['version'] != expected:
                raise HTTPException(409,'Stale version; reload before retrying')
            try:
                new, tasks = function(old,db)
            except DomainError as e:
                raise HTTPException(409,str(e)) from e
            new['version'] = old['version'] + 1
            new['updated_at'] = datetime.now(timezone.utc).isoformat()
            db.execute('UPDATE cases SET body=? WHERE id=?',(json.dumps(new),case_id))
            self.append_events(db,new,tasks,user['subject'])
            return new

    def events(self, case_id=None):
        with self.connect() as db:
            rows = db.execute('SELECT * FROM events'+(' WHERE case_id=?' if case_id else '')+' ORDER BY seq',
                              (case_id,) if case_id else ()).fetchall()
            return [dict(r) for r in rows]

    def list_owned(self, table, user):
        """Lists obey the same ownership policy as individual-record reads."""
        authorise(user)
        if table not in ('cases', 'licences'):
            raise ValueError('Unsupported table')
        with self.connect() as db:
            rows = db.execute(f'SELECT body FROM {table} ORDER BY rowid DESC').fetchall()
        records = [json.loads(row['body']) for row in rows]
        return [item for item in records if user['role'] == 'officer' or item['owner'] == user['subject']]

    def get_licence(self, licence_id, db=None):
        if db is None:
            with self.connect() as conn:
                return self.get_licence(licence_id,conn)
        row = db.execute('SELECT body FROM licences WHERE id=?',(licence_id,)).fetchone()
        if not row:
            raise HTTPException(404,'Prototype licence not found')
        return json.loads(row['body'])
