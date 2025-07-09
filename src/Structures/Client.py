from io import BytesIO
import os
from pyrogram import enums
from pyromod import Client
import random

import requests
from Helpers.Logger import get_logger
from Helpers.Utils import Utils
from Structures.Database import Database as db


class SuperClient(Client):
    def __init__(
        self,
        name: str,
        api_id: int,
        api_hash: str,
        bot_token: str,
        user_db_filepath: str,
        chat_db_filepath: str,
        prefix: str,
        owner_id: int,
        bot_id:int
    ):
        super().__init__(
            name=name, api_id=api_id, api_hash=api_hash, bot_token=bot_token
        )
        self.prifix = prefix
        self.log = get_logger()
        self.database = user_db_filepath, chat_db_filepath
        self.utils = Utils()
        self.owner_id = owner_id
        self.bot_id = bot_id


    @property
    def db(self):
        return db(self.database)

    async def admincheck(self, message):
        if message.chat.type in ("group", "supergroup", "channel"):
            isadmin = await self.get_chat_member(message.chat.id, message.from_user.id)
            return (str(isadmin.status)[len("ChatMemberStatus.") :].strip() in ["OWNER", "ADMINISTRATOR"])

    
    async def get_admins_and_owner(self, chat_id):
        admins_info = []
        owner_info = None
    
        async for member in self.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            user = member.user
            username = user.username if user.username else f"{user.first_name or ''} {user.last_name or ''}".strip()
            if member.status == "creator":
                owner_info = (username, user.id)
            elif member.status == "administrator":
                admins_info.append((username, user.id))
        return owner_info, admins_info
    
    def calculate_rank(self, entity_type, entity_id, all_entities):
        sorted_entities = sorted(all_entities, key=lambda x: x["xp"], reverse=True)
        
        id_key = "user_id" if entity_type == "USER" else "chat_id"
        
        for index, entity in enumerate(sorted_entities, start=1):
            if entity.get(id_key) == entity_id:
                return index
        return -1

    
    def process_leveling(self, data, xp_gained=None):
        xp = data["xp"]
        lvl = data["lvl"]
        if xp_gained is None:
            xp_gained = random.randint(1, 3)
        total_xp = data["xp"] + xp_gained
        last_lvl = lvl
        lvled_up = False

        while total_xp >= (5 * (lvl ** 2) + 50):
            lvl += 1
            lvled_up = True

        previouslvlxp = 5 * ((lvl - 1) ** 2) + 50 if lvl > 0 else 0
        nextlvlxp = 5 * (lvl ** 2) + 50
        currentxp = total_xp
        return xp, lvl, last_lvl, lvled_up, previouslvlxp, nextlvlxp, currentxp, total_xp
    
    async def xp_lvl(self, entity_type, message, xp_gained=None):
        if entity_type == "USER":
            xp, lvl, last_lvl, lvled_up, previouslvlxp, nextlvlxp, currentxp, total_xp = self.process_leveling(self.db.User.get_user(message.sender.user_id), xp_gained)
            self.db.User.update_user(message.sender.user_id, {"xp": total_xp, "lvl": lvl})
            rank = self.calculate_rank(entity_type, message.sender.user_id, self.db.User.get_all_users())
            self.db.User.update_user(message.sender.user_id, {"rank": rank})
            name = message.sender.user_name
        elif entity_type == "CHAT":
            xp, lvl, last_lvl, lvled_up, previouslvlxp, nextlvlxp, currentxp, total_xp = self.process_leveling(self.db.Chat.get_chat_data(message.chat_id), xp_gained)
            self.db.Chat.update_chat_datas(message.chat_id, {"xp": total_xp, "lvl": lvl})
            rank = self.calculate_rank(entity_type, message.chat_id, self.db.Chat.get_all_chat_datas())
            self.db.Chat.update_chat_datas(message.chat_id, {"rank": rank})
            name = message.chat_title

        if lvled_up:
            if entity_type == "USER":
                profile_photo = message.sender.user_profile_id
            elif entity_type == "CHAT":
                profile_photo = message.chat_photo
            avatar_url = self.utils.img_to_url(
                await self.download_media(
                    profile_photo,
                    file_name=f'Images/{profile_photo}.jpg'
                )
            )
            os.remove(f"src/Images/{profile_photo}.jpg")
            rankcard_url = (
                "https://vacefron.nl/api/rankcard"
                f"?username={name}"
                f"&avatar={avatar_url}"
                f"&level={lvl}"
                f"&rank={rank}"
                f"&currentxp={currentxp}"
                f"&nextlevelxp={nextlvlxp}"
                f"&previouslevelxp={previouslvlxp}"
                f"&custombg=https://media.discordapp.net/attachments/1022533781040672839/1026849383104397312/image0.jpg"
                f"&xpcolor=00ffff"
                f"&isboosting=false"
                f"&circleavatar=true"
            )
            response = requests.get(rankcard_url)
            image_bytes = BytesIO(response.content)
            await self.send_photo(
                message.chat_id,
                image_bytes,
                caption=f"@{name} leveled up to level **{lvl}** **#{rank}**!"
            )
            self.db.User.lvl_garined(message.sender.user_id, xp, last_lvl, lvl)



