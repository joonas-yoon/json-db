import os
import json
import pytest

from json_as_db import Client, Database
from utils import file, logger


CUR_DIR = os.path.dirname(os.path.realpath(__file__))
DB_FILENAME = 'basic.json'
DB_FILEPATH = os.path.join(CUR_DIR, '..', 'samples', DB_FILENAME)
REC_ID = 'kcbPuqpfV3YSHT8YbECjvh'
REC_ID_2 = 'jmJKBJBAmGESC3rGbSb62T'
REC_ID_NOT_EXIST = 'N0t3xIstKeyV41ueString'


def setup_db() -> Database:
    logger.debug('setup: (file) '+ DB_FILEPATH)

    with open(DB_FILEPATH, 'r') as f:
        data = json.load(f)

    db = Database(data)
    db.__path__ = DB_FILEPATH
    db.__name__ = DB_FILENAME
    return db


@pytest.fixture()
def db() -> Database:
    yield setup_db()


def test_read_db_attributes(db: Database):
    record = db.get(REC_ID)

    assert isinstance(record.get('list'), list)
    assert record.get('booleanTrue') == True
    assert record.get('booleanFalse') == False
    assert record.get('randomInteger') == 123
    assert record.get('randomString') == 'keyboard-cat'
    assert record.get('not-exists-key') == None


def test_db_add(db: Database):
    assert db.count() == 2
    item = {
        'randomInteger': 111,
    }
    new_id = db.add(item)
    assert type(new_id) is str
    assert db.count() == 3

    found = db.get(new_id)
    assert found == item


def test_db_add_many(db: Database):
    assert db.count() == 2
    item_1 = {
        'randomInteger': 111,
    }
    item_2 = {
        'randomInteger': 999,
    }
    new_ids = db.add([item_1, item_2])
    assert type(new_ids) is list
    assert len(new_ids) == 2
    assert db.count() == 4

    assert db.get(new_ids[0]) == item_1
    assert db.get(new_ids[1]) == item_2


def test_db_remove(db: Database):
    assert db.count() == 2

    try:
        db.remove(REC_ID_NOT_EXIST)
    except KeyError:
        pass

    target = db.get(REC_ID)
    removed = db.remove(REC_ID)
    assert db.count() == 1
    assert removed == target
    assert None == db.get(REC_ID)
    try:
        db.remove(REC_ID)
    except KeyError:
        pass


def test_db_remove_single_list(db: Database):
    assert db.count() == 2
    target = db.get(REC_ID)
    removed = db.remove([REC_ID])
    assert db.count() == 1
    assert type(removed) is list
    assert removed[0] == target


def test_db_remove_many(db: Database):
    assert db.count() == 2
    target_1 = db.get(REC_ID)
    target_2 = db.get(REC_ID_2)
    removed = db.remove([REC_ID, REC_ID_2])
    assert db.count() == 0
    assert type(removed) is list
    assert removed[0] == target_1
    assert removed[1] == target_2


def test_db_get_by_id(db: Database):
    found = db.get(REC_ID)
    assert found['randomInteger'] == 123


def test_db_get_by_ids(db: Database):
    found = db.get([REC_ID, REC_ID_2])
    assert found[0]['randomInteger'] == 123
    assert found[1]['randomInteger'] == 321


def test_db_modify_by_id(db: Database):
    target = {
        'newString': 'demian',
    }
    db.modify(REC_ID, target)
    assert db.get(REC_ID) == target


def test_db_modify_by_ids(db: Database):
    keys = [REC_ID, REC_ID_2]
    values = [
        {
            'nulla': ['non', 'malesuada'],
        },
        {
            'suspendisse': {
                'at': 'nulla quis',
            },
        }
    ]
    db.modify(keys, values)
    assert db.get(keys[0]) == values[0]
    assert db.get(keys[1]) == values[1]


def test_db_modify_wrong_params(db: Database):
    try:
        # 1 key, 2 values
        db.modify(REC_ID, [{}, {}])
        # 1 key but list, 1 value
        db.modify([REC_ID], {})
        # 2 keys, 1 value in list
        db.modify([REC_ID, REC_ID_2], [{}])
    except ValueError:
        pass


def test_db_all(db: Database):
    records = db.all()
    logger.debug(records)
    assert len(records) == 2
    cat_names = set(map(lambda rec: rec['randomString'], records))
    expected = set(['keyboard-cat', 'cheshire-cat'])
    assert expected == cat_names


def test_db_clear(db: Database):
    assert db.count() == 2
    db.clear()
    assert db.count() == 0


def test_db_find(db: Database):
    result = db.find(lambda x: True)
    assert len(result) == db.count()
    found = db.find(lambda x: x['randomInteger'] == 123)
    assert found == [REC_ID]
    found = db.find(lambda x: 'alice' in x['list'])
    assert found == [REC_ID_2]
    found = db.find(lambda x: False)
    assert found == []
    found = db.find(lambda x: x['randomString'].endswith('cat'))
    assert len(found) == 2
    assert set(found) == set([REC_ID, REC_ID_2])


def test_db_has(db: Database):
    assert db.has(REC_ID) == True
    assert db.has(REC_ID_2) == True
    assert db.has(REC_ID_NOT_EXIST) == False


def test_db_has_many(db: Database):
    assert db.has([REC_ID, REC_ID_2]) == [True, True]
    assert db.has([REC_ID, REC_ID_NOT_EXIST]) == [True, False]
    assert db.has([REC_ID_NOT_EXIST, REC_ID_2]) == [False, True]

    for has in db.has([REC_ID, REC_ID_NOT_EXIST, REC_ID_2]):
        assert type(has) is bool


def test_db_count(db: Database):
    assert db.count() == 2


def test_db_drop(db: Database):
    dropped_count = db.drop()
    assert dropped_count == 2
    dropped_count = db.drop()
    assert dropped_count == 0


def test_db_commit(db: Database):
    db.commit()
    pytest.skip()


def test_db_rollback(db: Database):
    db.rollback()
    pytest.skip()


@pytest.mark.asyncio
async def test_db_save():
    temp_dir = os.path.join(CUR_DIR, 'test_save')
    try:
        file.remove(temp_dir)
    except FileNotFoundError:
        pass

    samples = [
        {"id": "ZoomIn", "label": "Zoom In"},
        {"id": "ZoomOut", "label": "Zoom Out"},
        {"id": "OriginalView", "label": "Original View"},
    ]

    client = Client(temp_dir)
    db = await client.create_database('db')
    logger.debug(f'[before saving] {db}')
    db.add(samples)
    logger.debug(f'[after saving] {db}')

    logger.debug(f'[saving path] {db.filepath}')
    kwargs = {
        'file_kwds': {'encoding': 'utf-8'},
        'json_kwds': {'indent': 4},
    }
    await db.save(**kwargs)

    with open(f'{temp_dir}/db.json', 'r', encoding='utf-8') as f:
        saved = json.load(f)
        logger.debug(f'[saved] {saved}')

    saved = await client.get_database('db')
    assert saved == db

    file.remove(temp_dir)
