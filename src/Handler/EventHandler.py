from pyrogram.types import ChatPermissions

from Structures.Client import SuperClient


class EventHandler:

    def __init__(self, client: SuperClient):
        self.__client = client

    async def handler(self, message):
        self.message = message
        chat_id = message.chat.id

        event = self.__client.db.Chat.get_all_events()
        if chat_id not in event:
            return

        event_type = str(self.message.service).split(".")[-1]

        if event_type == "NEW_CHAT_MEMBERS":
            members = self.message.new_chat_members
            for member in members:
                await self.__client.send_message(
                    self.message.chat.id,
                    f"__@{member.username} has joined the Chat !__",
                )

        elif event_type == "LEFT_CHAT_MEMBERS":
            await self.__client.send_message(
                self.message.chat.id,
                f"__@{self.message.left_chat_member.username} has left the Chat.__",
            )

        elif event_type == "PINNED_MESSAGE":
            await self.__client.send_message(
                self.message.chat.id,
                f"__A new message has been pinned by @{self.message.from_user.username}.\nCheck now !__",
            )
