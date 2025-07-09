import importlib.util
import os
import re
import random
from datetime import datetime
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

        # === AFK Handling ===
        mentionedUser = M.mentioned[0] if M.mentioned else None
        mentionedUserId = getattr(mentionedUser, "user_id", None)
        mentionedAFK = (
            self.__client.db.User.get_user(mentionedUserId).get("afk", {"is_afk": False})
            if mentionedUserId else {"is_afk": False}
        )

        repliedUser = getattr(M.reply_to_message, "replied_user", None)
        repliedUserId = repliedUser.user_id if repliedUser else None
        repliedAFK = self.__client.db.User.get_user(repliedUserId).get("afk", {"is_afk": False})

        userData = self.__client.db.User.get_user(M.sender.user_id)

        if M.message.split()[0] != "/afk":
            if userData["afk"]["is_afk"]:
                currentTime = datetime.now().time().strftime("%H:%M:%S")
                self.__client.db.User.set_afk(M.sender.user_id, False, None, currentTime)
                await self.__client.send_message(
                    M.chat_id,
                    f"__@{M.sender.user_name} nice to see you again!__"
                )

        if mentionedAFK["is_afk"] and repliedAFK["is_afk"]:
            return await self.__client.send_message(
                M.chat_id,
                f"__@{M.sender.user_name} @{mentionedUser.user_name} is currently offline.\n"
                f"**Reason** : {mentionedAFK.get('afk_reason', 'None')}__"
            )
        elif mentionedAFK["is_afk"]:
            await self.__client.send_message(
                M.chat_id,
                f"__@{M.sender.user_name} @{mentionedUser.user_name} is currently offline.\n"
                f"**Reason** : {mentionedAFK.get('afk_reason', 'None')}__"
            )
        elif repliedAFK["is_afk"]:
            await self.__client.send_message(
                M.chat_id,
                f"__@{M.sender.user_name} @{repliedUser.user_name} is currently offline.\n"
                f"**Reason** : {repliedAFK.get('afk_reason', 'None')}__"
            )

        # === Message Logging if Not Command ===
        if not isCommand:
            self.__client.log.info(
                f"[MSG]: From {M.chat_type} by {M.sender.user_name} "
                f"({'ADMIN' if M.isAdmin else 'NOT ADMIN'})"
            )
            return
        # === Command Parsing and Execution ===
        if messageText == self.__client.prifix:
            return await self.__client.send_message(
                M.chat_id,
                f"__Enter a command following {self.__client.prifix}__"
            )

        commandName = commandContext[0]
        commandObj = self.commandMap.get(commandName)

        if not commandObj:
            return await self.__client.send_message(
                M.chat_id,
                "__Command does not available!!__"
            )

        if commandObj.config.xp:
            try:
               await self.__client.xp_lvl("USER",M)
            except Exception as e:
               self.__client.log.info(e)
               pass

        if commandObj.config.OwnerOnly and M.sender.user_id != self.__client.owner_id:
            return await self.__client.send_message(
                M.chat_id,
                "__This command can only be used by the **BOT owner**!!__"
            )

        if commandObj.config.AdminOnly and M.isAdmin:
            return await self.__client.send_message(
                M.chat_id,
                "__This command can only be used by an admin!!__"
            )

        self.__client.log.info(
            f"[CMD]: {self.__client.prifix}{commandName} from {M.chat_type} "
            f"by {M.sender.user_name} "
            f"({'ADMIN' if M.isAdmin else 'NOT ADMIN'})"
        )

        await commandObj.exec(M, commandContext)
        
        try: 
            if M.chat_type == "SUPERGROUP" :
                chat_data = self.__client.db.Chat.get_chat_data(M.chat_id)
                msg_count = chat_data.get("stats").get("msg_count", 0) + 1
                self.__client.db.Chat.update_chat_datas(M.chat_id, {"stats": {"msg_count": msg_count}})
                if M.sender.user_id not in chat_data.get("stats").get("active_users") :
                    active_users = chat_data.get("stats").get("active_users")
                    active_users.append(M.sender.user_id)
                    self.__client.db.Chat.update_chat_datas(M.chat_id, {"stats": {"active_users": active_users}})
    
                milestones = [500, 1000, 5000, 10000, 20000, 50000, 100000]
                if msg_count in milestones:
                    await self.__client.send_message(
                        M.chat_id,
                        f"🎉 Congratulations! This group has reached **{msg_count:,}** messages! Keep chatting!"
                    )
                await self.__client.xp_lvl("CHAT", M, random.randint(1, 2))
        except Exception as e:
            self.__client.log.info(e)
            pass

            


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
