import re
import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client['matchmaking_bot']
embeds_col = db['embeds']
guilds_col = db['guilds']
tracked_emb_col = db['tracked_embeds']


def get_embed(uid: str) -> dict:
    return embeds_col.find_one({'_id': uid})


def get_all_embeds():
    return embeds_col.find({})


def get_guild(gid: str) -> dict:
    return guilds_col.find_one({'_id': gid})


def get_all_guilds():
    return guilds_col.find({})


def get_current_participation(embed_id, uid) -> bool:
    temp = embeds_col.find_one({'_id': embed_id})
    # print(uid)
    # print(temp)
    # print(uid in temp['participating'] or uid in temp['mb_participating'] or uid in temp['not_participating'])
    return [temp['participating'], temp['mb_participating'], temp['not_participating']]


def get_when_notified(embed_id):
    return embeds_col.find_one({'_id': embed_id})['when_notified']


def get_tracked_embed(embed_id):
    return tracked_emb_col.find_one({'list_messages': embed_id})


def create_embed(embed_id, author, guild, game_id: str = 0, game_password: str = None, game_rules: str = None,
                 starting_time=None, author_avatar: str = None) -> bool:
    a = embeds_col.insert_one({
        '_id': embed_id,
        'author': author,
        "guild": guild,
        "game_id": game_id,
        "game_password": game_password,
        "game_rules": game_rules,
        "starting_time": starting_time,
        "author_avatar": author_avatar,
        "notify": True,
        "when_notified": 0,
        "participating": [],
        "mb_participating": [],
        "not_participating": []
    })
    tracked_emb_col.insert_one({
        '_id': embed_id,
        'messages': [],
        'list_messages': []
        })
    return a


def set_notify(embed_id, state):
    return embeds_col.update_one({'_id': embed_id}, {
        '$set': {
            'when_notified': state
        }
    })


def update_embed(embed_id, target, value):
    return embeds_col.update_one({'_id': embed_id}, {
        '$set': {
            target: value
        }
    })


def update_when_notified(embed_id, state):
    return embeds_col.update_one({'_id': embed_id}, {
        '$set': {
            'notify': state
        }
    })


def add_participation(embed_id, target, uid) -> bool:
    return embeds_col.update_one({'_id': embed_id}, {
        '$push': {target: {
            "name": uid[0], 
            'uid': uid[1]
            }
        }
    })


def try_pull_all_reactions(embed_id, uid):
    return embeds_col.update_one({'_id': embed_id}, {
        '$pull': {
                'participating': uid,
                'mb_participating': uid,
                'not_participating': uid
            }
    })


def remove_participation(embed_id, target, uid) -> bool:
    return embeds_col.update_one({'_id': embed_id}, {
        '$pull': {target: uid}
    })


def add_guild(guild, invite_url, channel, role) -> bool:
    return guilds_col.insert_one({
        '_id': guild,
        'invite_url': invite_url,
        'channel': channel,
        'ping_role': role
    })


def remove_guild(guild) -> bool:
    return guilds_col.remove({'_id': guild})


def track_embed(embed_id, em_id, channel):
    return tracked_emb_col.update_one({'_id': embed_id}, {
        '$push': {'messages': {
            'channel': channel,
            'embed_messages_id': em_id
        },
            "list_messages": em_id
        }
    })

def remove_embed(embed_id):
    return embeds_col.delete_one({'_id': embed_id})


def remove_tracked_embed(embed_id):
    return tracked_emb_col.delete_one({'_id': embed_id})


def clear_all_embeds():
    tracked_emb_col.delete_many({})
    embeds_col.delete_many({})
