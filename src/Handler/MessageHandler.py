import importlib.util
import os
import re
import random
from Structures.Client import SuperClient
from Structures.Message import Message


class MessageHandler:

    def __init__(self, client: SuperClient):
        self.__client = client
        self.commandMap = {}

    async def handler(self, M: Message):
        messageText = M.message
        commandContext = self.parseArgs(messageText)

        if messageText is None:
            return

        isCommand = messageText.startswith(self.__client.prifix)
        commandName = commandContext[0]
        commandObj = self.commandMap.get(commandName)

        # === Message Logging if Not Command ===
        if not isCommand:
            self.__client.log.info(
                f"[MSG]: From {M.chat_type} by {M.sender.user_name} "
                f"({M.user_status})"
            )
            return

        if not commandObj:
            return await self.__client.send_message(
                M.chat_id,
                "Command does not available!!"
            )

        if commandObj.config.ChatOnly and M.chat_type not in ["GROUP", "SUPERGROUP", "CHANNEL"]:
            return await self.__client.send_message(M.chat_id, f"@{M.sender.user_name} this command can't be used in PRIVATE chat!")

        if messageText == self.__client.prifix:
            return await self.__client.send_message(
                M.chat_id,
                f"Enter a command following {self.__client.prifix}"
            )

        if commandObj.config.xp:
            try:
                await self.__client.xp_lvl("USER", M)
            except Exception as e:
                self.__client.log.info(e)
                pass

        if commandObj.config.OwnerOnly and M.sender.user_id != self.__client.owner_id:
            return await self.__client.send_message(
                M.chat_id,
                "This command can only be used by the **BOT owner**!!"
            )

        if commandObj.config.AdminOnly and M.isAdmin is False:
            return await self.__client.send_message(
                M.chat_id,
                "This command can only be used by an admin!!"
            )

        self.__client.log.info(
            f"[CMD]: {self.__client.prifix}{commandName} from {M.chat_type} "
            f"by {M.sender.user_name} "
            f"{M.user_status}"
        )

        await commandObj.exec(M, commandContext)

        if M.chat_type == "SUPERGROUP":
            chat_data = self.__client.db.Chat.get_chat_data(M.chat_id)
            messages_count = chat_data.get("stats", {}).get("messages_count", 0) + 1
            active_users = chat_data.get("stats", {}).get("active_users", [])
            if M.sender.user_id not in active_users:
                active_users.append(M.sender.user_id)
            self.__client.db.Chat.update_chat_datas(M.chat_id, {
                "stats": {
                    "messages_count": messages_count,
                    "active_users": active_users
                }
            })
            milestones = [500, 1000, 5000, 10000, 20000, 50000, 100000]
            if messages_count in milestones:
                await self.__client.send_message(
                    M.chat_id,
                    f"🎉 Congratulations! This group has reached **{messages_count:,}** messages! Keep chatting!"
                )
                await self.__client.xp_lvl("CHAT", M, random.randint(1, 5))

    def loadCommands(self, folderPath):
        for fileName in os.listdir(folderPath):
            if not fileName.endswith(".py"):
                continue

            moduleName = fileName[:-3]
            filePath = os.path.join(folderPath, fileName)

            spec = importlib.util.spec_from_file_location(moduleName, filePath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            commandClass = getattr(module, "Command")
            commandInstance = commandClass(self.__client, self)

            self.commandMap[commandInstance.config.command] = commandInstance
            self.__client.log.notice(f"Loaded: {commandInstance.config.command} from {filePath}")

            aliases = getattr(commandInstance.config, "aliases", [])
            for alias in aliases:
                self.commandMap[alias] = commandInstance

        self.__client.log.info("Successfully Loaded all the commands")

    def parseArgs(self, rawText):
        if rawText is None:
            return None

        argsList = rawText.split(" ")
        command = argsList.pop(0).lower()[len(self.__client.prifix):] if argsList else ""
        text = " ".join(argsList)
        flags = {
            key: (value if value else None)
            for key, value in re.findall(r"--(\w+)(?:=(\S*))?", rawText)
        }

        return (command, text, flags, argsList, rawText)

    def loadApis(self):
        pass
