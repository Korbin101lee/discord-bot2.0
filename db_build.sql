CREATE TABLE IF NOT EXISTS guilds(
    GuildID integer PRIMARY KEY,
    Prefix text DEFAULT "+"
);

CREATE TABLE IF NOT EXISTS logs(
    LogId integer PRIMARY KEY AUTOINCREMENT,
    GuildID integer DEFAULT 0,
    UserID text,
    ModeratorId integer DEFAULT 0,
    TypeOfWarn text,
    Reason text,
    TimeOfDay text
);
