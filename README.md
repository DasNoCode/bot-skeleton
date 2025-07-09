# Bot Skeleton 🤖

A **clean, modular, and scalable Telegram bot Skeleton** powered by **Python** and **Pyrogram** — designed for easy plugin creation, command handling, and future extensibility.

## ⚙️ Features

- 🧩 **Modular Architecture** – All commands and logic are organized in reusable classes.
- 🚀 **Command Handler** – Custom command system with access control (admin/owner/XP-based).
- 🛠 **Structured Codebase** – Follows a well-organized folder hierarchy for better maintainability.
- 🎯 **Message Flow Logic** – Efficiently routes and handles messages with clear condition checks.

---

## 🧱 File Structure

```
src/
├── main.py                # Entry point for the bot
├── Handler/
│   ├── __init__.py
│   ├── MessageHandler.py  # Core message router
│   └── ...                # Other handlers (CommandHandler, EventHandler, etc.)
├── config/
│   └── settings.py        # API tokens and environment config
├── utils/
│   └── helpers.py         # Common utility functions
└── Structures/
    ├── Command/
    │   └── BaseCommand.py # Base class for all commands
    └── Message.py         # Message wrapper class
```

---

## 🔄 Message Flow

```
[Start: User sends a message]
            |
            v
[main.py receives message]
            |
            v
[MessageHandler.handler() is called]
            |
            v
[Is message a command? (starts with prefix)]
       /           \
     No             Yes
     |               |
     v               v
[Log/Handle     [Parse command name and args]
 as regular          |
 message]            v
                  [Find Command in commandMap]
                       |
                       v
            [Is command found?]
                 /       \
               No         Yes
               |           |
               v           v
    [Send "Command    [Check permissions & XP]
     not available"         |
     message]               v
                    [Run command.exec()]
                          |
                          v
               [Command responds to user]
                          |
                          v
                      [Log/XP/Stats]
                          |
                          v
                        [End]
```

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/DasNoCode/bot-skeleton.git
cd bot-skeleton/src
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the bot

Edit `config/settings.py`:

```python
API_ID = 123456
API_HASH = "your_api_hash"
BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
OWNER_ID = 123456789
```

### 4. Run the bot

```bash
python3 main.py
```

---

## 💬 Creating a Command

To add a new command, create a file under `Structures/Command/` (or your custom command folder) using this format:

```python
from Structures.Command.BaseCommand import BaseCommand
from Structures.Message import Message

class Command(BaseCommand):

    def __init__(self, client, handler):
        super().__init__(
            client,
            handler,
            {
                "command": "hi",
                "category": "core",
                "xp": True,
                "AdminOnly": False,
                "OwnerOnly": False,
                "description": {"content": "Say hello to the bot"},
            },
        )

    async def exec(self, M: Message, context):
        await self.client.send_message(
            M.chat_id, f"Hey, @{M.sender.user_name} how is your day today? Use /help to use the Bot!"
        )
```

The bot automatically detects and loads commands via its internal command map system.

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you’d like to change.

---

## 📄 License

Licensed under the **MIT License** — feel free to use and modify.

---

### 🧭 Getting Help?

- Read Pyrogram Docs → https://docs.pyrogram.org  
- Review command examples in `Structures/Command/`  
- Open an issue if something breaks!
