from Helpers.JsonObject import JsonObject
from Structures.Client import SuperClient

class Message:

    media_types = ["voice", "animation", "audio", "photo", "video"]
    urls = []
    numbers = []
    mentioned = []

    def __init__(self, client: SuperClient, message_or_callback):  # type: ignore
        self.__client = client
        self.is_callback = (
            True if "CallbackQuery" in str(type(message_or_callback)) else False
        )

        if self.is_callback:
            self.__m = message_or_callback.message
            self.message_id = self.__m.id
            self.message = message_or_callback.data
            self.query_id = message_or_callback.id
            self.sender = JsonObject(
                {
                    "user_id": message_or_callback.from_user.id,
                    "user_name": message_or_callback.from_user.username,
                    "user_profile_id": getattr(
                        message_or_callback.from_user.photo, "big_file_id", None
                    ),
                }
            )
        else:
            self.__m = message_or_callback
            self.sender = JsonObject(
                {
                    "user_id": self.__m.from_user.id,
                    "user_name": self.__m.from_user.username,
                    "user_profile_id": getattr(
                        self.__m.from_user.photo, "big_file_id", None
                    ),
                }
            )
        self.chat_info = self.__m.chat
        self.chat_title = self.chat_info.title
        self.chat_photo = self.chat_info.photo.big_file_id
        self.reply_to_message = self.__m.reply_to_message
        self.chat_type = str(self.__m.chat.type)[len("ChatType.") :].strip()
        self.chat_id = self.chat_info.id

        if self.reply_to_message:
            self.reply_to_message.replied_user = JsonObject(
                {
                    "user_id": self.reply_to_message.from_user.id,
                    "user_name": self.reply_to_message.from_user.username,
                    "user_profile_id": getattr(
                        self.reply_to_message.from_user.photo, "big_file_id", None
                    ),
                }
            )
            self.msg_type = (
                str(self.reply_to_message.media).split(".")[-1].lower()
                if self.reply_to_message.media
                else None
            )
        else:
            self.msg_type = (
                str(self.__m.media).split(".")[-1].lower() if self.__m.media else None
            )

        if self.is_callback is False:
            if self.msg_type and self.__m.caption:
                self.message = self.__m.caption
            else:
                self.message = self.__m.text

        if self.msg_type in self.media_types:
            if self.reply_to_message:
                self.file_id = getattr(
                    getattr(self.reply_to_message, self.msg_type, {}), "file_id", None
                )
                return
            self.file_id = getattr(
                getattr(self.__m, self.msg_type, {}), "file_id", None
            )

    async def get_valid_user_ids(self, message):
        valid_users = []
        try:
            mentions = [word for word in message.split() if word.startswith("@")]
            for mention in mentions:
                user = await self.__client.get_users(mention)
                valid_users.append(
                    JsonObject(
                        {
                            "user_id": user.id,
                            "user_name": user.username,
                            "user_profile_id": getattr(user.photo, "big_file_id", None),
                        }
                    )
                )
        except Exception as e:
            pass

        return valid_users

    async def build(self):
        self.bot_username = (await self.__client.get_me()).username
        self.bot_userid = (await self.__client.get_me()).id
        self.urls = self.__client.utils.extract_links(self.message)
        self.numbers = self.__client.utils.extract_numbers(self.message)
        self.isAdmin = await self.__client.admincheck(self.__m)
        self.mentioned = await self.get_valid_user_ids(self.message)
        if self.reply_to_message:
            reply_user = self.reply_to_message.from_user
            self.mentioned.append(
                {
                    "user_id": reply_user.id,
                    "user_name": reply_user.username,
                    "user_profile_id": getattr(reply_user.photo, "big_file_id", None),
                }
            )
        return self


    def raw(self):
        return self.__m
