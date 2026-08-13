
CREATE TABLE IF NOT EXISTS users(
 id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id TEXT UNIQUE, username TEXT,
 first_name TEXT, coins INTEGER NOT NULL DEFAULT 5000, xp INTEGER NOT NULL DEFAULT 0,
 level INTEGER NOT NULL DEFAULT 1, referral_code TEXT UNIQUE, referred_by TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, last_daily TEXT
);
CREATE TABLE IF NOT EXISTS cases(
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, price_coins INTEGER NOT NULL,
 price_stars INTEGER NOT NULL, theme TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS items(
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, rarity TEXT NOT NULL,
 sell_coins INTEGER NOT NULL, theme TEXT NOT NULL, image TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS case_items(
 case_id INTEGER NOT NULL, item_id INTEGER NOT NULL, drop_chance REAL NOT NULL,
 PRIMARY KEY(case_id,item_id)
);
CREATE TABLE IF NOT EXISTS inventory(
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, item_id INTEGER NOT NULL,
 obtained_case_id INTEGER, obtained_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, sold_at TEXT
);
CREATE TABLE IF NOT EXISTS transactions(
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, type TEXT NOT NULL,
 amount INTEGER NOT NULL, currency TEXT NOT NULL, note TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS tasks(
 id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT,
 reward_coins INTEGER NOT NULL DEFAULT 0, reward_xp INTEGER NOT NULL DEFAULT 0,
 kind TEXT NOT NULL DEFAULT 'daily', active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS user_tasks(
 user_id INTEGER NOT NULL, task_id INTEGER NOT NULL, progress INTEGER NOT NULL DEFAULT 0,
 claimed INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(user_id,task_id)
);
CREATE TABLE IF NOT EXISTS promo_codes(
 code TEXT PRIMARY KEY, reward_coins INTEGER NOT NULL DEFAULT 0,
 max_uses INTEGER NOT NULL DEFAULT 1, uses INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS promo_uses(code TEXT NOT NULL,user_id INTEGER NOT NULL,PRIMARY KEY(code,user_id));
CREATE TABLE IF NOT EXISTS audit_log(
 id INTEGER PRIMARY KEY AUTOINCREMENT, admin TEXT, action TEXT, payload TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS purchases(
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
 telegram_payment_charge_id TEXT UNIQUE, product_code TEXT, stars INTEGER,
 status TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT OR REPLACE INTO cases(id,name,price_coins,price_stars,theme,active) VALUES(1,"VLDST // NEON",1000,15,"neon",1);
INSERT OR REPLACE INTO cases(id,name,price_coins,price_stars,theme,active) VALUES(2,"VLDST CORE",1000,15,"core",1);
INSERT OR REPLACE INTO cases(id,name,price_coins,price_stars,theme,active) VALUES(3,"VLDST PULSE",5000,25,"pulse",1);
INSERT OR REPLACE INTO cases(id,name,price_coins,price_stars,theme,active) VALUES(4,"VLDST AURA",15000,50,"aura",1);
INSERT OR REPLACE INTO cases(id,name,price_coins,price_stars,theme,active) VALUES(5,"VLDST VOID",30000,75,"void",1);
INSERT OR REPLACE INTO cases(id,name,price_coins,price_stars,theme,active) VALUES(6,"VLDST OVERDRIVE",60000,100,"overdrive",1);
INSERT OR REPLACE INTO cases(id,name,price_coins,price_stars,theme,active) VALUES(8,"VLDST RIFT",150000,110,"rift",1);
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(54,"VLDST RIFT GOD","MYTHIC",500000,"rift","/assets-code/item/54.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(53,"Rift Reaper","LEGENDARY",180000,"rift","/assets-code/item/53.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(52,"Rift Blaster","EPIC",90000,"rift","/assets-code/item/52.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(51,"Rift Reactor","EPIC",65000,"rift","/assets-code/item/51.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(50,"Rift Core","RARE",40000,"rift","/assets-code/item/50.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(49,"Rift Crystal","RARE",30000,"rift","/assets-code/item/49.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(48,"Rift Energy","COMMON",18000,"rift","/assets-code/item/48.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(47,"Rift Shard","COMMON",15000,"rift","/assets-code/item/47.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(46,"OVERDRIVE GOD","MYTHIC",280000,"overdrive","/assets-code/item/46.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(45,"OVERDRIVE X","LEGENDARY",120000,"overdrive","/assets-code/item/45.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(44,"Overdrive Gun","EPIC",65000,"overdrive","/assets-code/item/44.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(43,"Overdrive Reactor","EPIC",50000,"overdrive","/assets-code/item/43.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(42,"Turbo Core","RARE",33000,"overdrive","/assets-code/item/42.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(41,"Overdrive Crystal","RARE",25000,"overdrive","/assets-code/item/41.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(40,"Heat Core","COMMON",14000,"overdrive","/assets-code/item/40.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(39,"Overdrive Cell","COMMON",12000,"overdrive","/assets-code/item/39.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(38,"VOID KING","MYTHIC",150000,"void","/assets-code/item/38.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(37,"Void Reaper","LEGENDARY",60000,"void","/assets-code/item/37.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(36,"Void Shield","EPIC",30000,"void","/assets-code/item/36.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(35,"Void Reactor","EPIC",25000,"void","/assets-code/item/35.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(34,"Shadow Core","RARE",15000,"void","/assets-code/item/34.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(33,"Void Crystal","RARE",12000,"void","/assets-code/item/33.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(32,"Dark Energy","COMMON",7000,"void","/assets-code/item/32.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(31,"Void Fragment","COMMON",6000,"void","/assets-code/item/31.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(30,"AURA Phantom","MYTHIC",75000,"aura","/assets-code/item/30.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(29,"AURA Blade","LEGENDARY",30000,"aura","/assets-code/item/29.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(28,"AURA Shield","EPIC",15000,"aura","/assets-code/item/28.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(27,"AURA Reactor","EPIC",12000,"aura","/assets-code/item/27.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(26,"Sky Core","RARE",7500,"aura","/assets-code/item/26.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(25,"Aura Crystal","RARE",6000,"aura","/assets-code/item/25.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(24,"Aura Crystal","COMMON",6000,"aura","/assets-code/item/24.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(23,"Blue Gem","COMMON",3500,"aura","/assets-code/item/23.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(22,"Aura Shard","COMMON",3000,"aura","/assets-code/item/22.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(21,"PULSE TITAN","MYTHIC",30000,"pulse","/assets-code/item/21.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(20,"Pulse Gun","LEGENDARY",12000,"pulse","/assets-code/item/20.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(19,"Pulse Reactor","EPIC",5500,"pulse","/assets-code/item/19.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(18,"Neon Crystal","RARE",3000,"pulse","/assets-code/item/18.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(17,"Pulse Core","RARE",2500,"pulse","/assets-code/item/17.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(16,"Pulse Chip","COMMON",1400,"pulse","/assets-code/item/16.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(15,"Green Energy","COMMON",1200,"pulse","/assets-code/item/15.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(14,"Pulse Battery","COMMON",1000,"pulse","/assets-code/item/14.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(13,"CORE Overlord","MYTHIC",8000,"core","/assets-code/item/13.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(12,"VLDST Blade","LEGENDARY",3500,"core","/assets-code/item/12.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(11,"Core Crystal","EPIC",1500,"core","/assets-code/item/11.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(10,"Power Cell","RARE",850,"core","/assets-code/item/10.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(9,"Blue Core","RARE",700,"core","/assets-code/item/9.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(8,"Steel Chip","COMMON",350,"core","/assets-code/item/8.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(7,"Energy Cell","COMMON",300,"core","/assets-code/item/7.svg");
INSERT OR REPLACE INTO items(id,name,rarity,sell_coins,theme,image) VALUES(6,"Core Fragment","COMMON",250,"core","/assets-code/item/6.svg");
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(1,6,45);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(1,7,25);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(1,8,15);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(1,9,8);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(1,10,5);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(1,11,2);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(2,6,60);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(2,9,25);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(2,11,10);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(2,12,4.5);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(2,13,0.5);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(3,14,20);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(3,15,20);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(3,16,20);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(3,17,10);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(3,18,10);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(3,19,8);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(3,20,7);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(3,21,5);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(4,22,20);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(4,23,20);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(4,24,10);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(4,25,10);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(4,26,10);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(4,27,8);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(4,28,8);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(4,29,7);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(4,30,5);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(5,31,20);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(5,32,20);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(5,33,10);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(5,34,10);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(5,35,8);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(5,36,8);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(5,37,7);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(5,38,4.5);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(6,39,15);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(6,40,15);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(6,41,9.5);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(6,42,9.5);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(6,43,7);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(6,44,7);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(6,45,5);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(6,46,3);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(8,47,13.5);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(8,48,13.5);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(8,49,10);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(8,50,10);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(8,51,7.5);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(8,52,7.5);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(8,53,4.5);
INSERT OR REPLACE INTO case_items(case_id,item_id,drop_chance) VALUES(8,54,2);

INSERT OR IGNORE INTO tasks(id,title,description,reward_coins,reward_xp,kind) VALUES
(1,'Ежедневный вход','Забери дневную награду',500,25,'daily'),
(2,'Открой 1 кейс','Сделай первое открытие',300,40,'game'),
(3,'Продай предмет','Продай любой предмет',250,30,'game'),
(4,'Пригласи друга','Пригласи нового игрока',1000,100,'referral'),
(5,'Собери 5 предметов','Добавь 5 предметов в инвентарь',750,80,'collection');


-- VLDST STAR SHOP / BOOSTS / PREMIUM / MINI GAME
CREATE TABLE IF NOT EXISTS star_shop(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 code TEXT UNIQUE NOT NULL,
 title TEXT NOT NULL,
 description TEXT NOT NULL,
 subtitle TEXT,
 kind TEXT NOT NULL,
 stars INTEGER NOT NULL,
 duration_days INTEGER NOT NULL DEFAULT 7,
 multiplier REAL NOT NULL DEFAULT 1,
 active INTEGER NOT NULL DEFAULT 1,
 sort_order INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS user_boosts(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL,
 code TEXT NOT NULL,
 multiplier REAL NOT NULL DEFAULT 1,
 expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS user_premium(
 user_id INTEGER PRIMARY KEY,
 product_code TEXT NOT NULL,
 expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pending_purchases(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL,
 payload TEXT UNIQUE NOT NULL,
 product_code TEXT NOT NULL,
 stars INTEGER NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS game_scores(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL,
 score INTEGER NOT NULL,
 reward INTEGER NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO star_shop(code,title,description,subtitle,kind,stars,duration_days,multiplier,sort_order) VALUES
("boost_x2","BOOST ×2","Удваивает награды за задания и мини-игры.","7 DAYS • REWARD BOOST","boost",25,7,2,1),
("boost_x3","BOOST ×3","Утраивает награды за задания и мини-игры.","7 DAYS • REWARD BOOST","boost",50,7,3,2),
("boost_x5","BOOST ×5","Пятикратный множитель наград.","3 DAYS • ULTRA BOOST","boost",80,3,5,3),
("premium_30","VLDST PREMIUM","Premium-профиль, бейдж, дополнительные задания и бонус к XP.","30 DAYS • PREMIUM PASS","premium",100,30,1,10),
("premium_90","VLDST PREMIUM+","Расширенный Premium Pass на 90 дней.","90 DAYS • PREMIUM PASS","premium",250,90,1,11),
("frame_neon","NEON PROFILE","Неоновая рамка профиля и эксклюзивный бейдж.","PERMANENT • PROFILE COSMETIC","cosmetic",30,3650,1,20),
("sticker_pack","VLDST STICKERS","Коллекционный набор VLDST-стикеров.","PERMANENT • COSMETIC","cosmetic",40,3650,1,21);


CREATE TABLE IF NOT EXISTS user_cosmetics(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL,
 code TEXT NOT NULL,
 obtained_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(user_id,code)
);
