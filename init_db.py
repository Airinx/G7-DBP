import sqlite3

def init_db():
    conn = sqlite3.connect('vn_game.db')
    
    # อ่านไฟล์ schema.sql เพื่อรีเซ็ตตาราง
    with open('schema.sql', encoding='utf-8') as f:
        conn.executescript(f.read())
    c = conn.cursor()

    # --- 1. Character
    # 1=Lin, 2=You(player), 99=Narration
    c.execute("INSERT INTO characters VALUES (1,'Lin','#FFD1DC')")  
    c.execute("INSERT INTO characters VALUES (2,'You','#CCCCFF')")
    c.execute("INSERT INTO characters VALUES (99,'','#FFFFFF')")

    # --- 2. Expressions
    expressions = [
        (1, 'normal', 'lin_normal.png'), 
        (2, 'happy', 'lin_happy.png'),
        (3, 'sad', 'lin_sad.png'),
        (4, 'blush', 'lin_blush.png'),
        (5, 'cry', 'lin_cry.png'),
        (6, 'shy', 'lin_shy.png'),
        (7, 'sticker', 'sticker.png'),        
    ]
    for e in expressions:
        c.execute("INSERT INTO expressions VALUES (?,?,?)", e)
    

    # --- 3. Scenes
    scenes = [
        (1, 1, 'classroom', 'bg-classroom.png'),
        (2, 1, 'cafe', 'bg-cafe.png'),
        (3, 1, 'bedroom (Day1)', 'bg-bedroom.png'),
        (4, 2, 'library', 'bg-library.png'),
        (5, 2, 'skywalk', 'bg-skywalk.png'),
        (6, 3, 'music', 'bg-music.png'),
        (7, 3, 'rain', 'bg-rain.png'),
        (8, 1, 'prog', 'bg-pp.png'),
        (9, 2, 'bg-bedroom (Day2)', 'bg-bedroom.png'),
        (99, 0, 'ending scene', 'bg-black.png')
    ]
    for s in scenes:
        c.execute("INSERT INTO scenes VALUES (?,?,?,?)", s)

    # --- 4. Dialogues
    dialogues = [

        # === DAY 1: The Beginning ===
        # SCENE 1: Classroom
        (1, 8, 8, None, "The professor announces the FOUNDATION OF PROGRAMMING pair project. Students immediately begin looking for partners...", 2),
        (2, 1, 99, None, "Lin is still sitting quietly in her seat. You watch her for a moment before deciding to walk over.", 3),
        (3, 1, 2, None, "Lin... you're student ID 68051299, right? Looks like we have to do the project together.", None),

        # Choice results
        (4, 1, 1, 6, "Alright then. I'll do my best.", 5),
        (5, 1, 2, None, "Same here.", 6),
        (6, 1, 1, 1, "Then... nice to work with you.", 7),

        # SCENE 2: Cafe
        (7, 2, 99, None, "In the afternoon, you invite Lin to talk about the project at a quiet cafe.", 8),
        (8, 2, 2, None, "I wanted to talk about the project with you... but also...", 9),
        (9, 2, 2, None, "(I kind of want to change the topic... what should I talk about?)", None),

        # Positive
        (10, 2, 1, 2, "Thanks for asking... Actually, I prefer reading quietly more than anything.", 11),
        (11, 2, 99, None, "The atmosphere becomes more relaxed. Lin begins to smile a little.", 12),

        # Negative
        (110, 2, 1, 1, "I see... then let's continue working on the project.", 111),
        (111, 2, 99, None, "You continue discussing the project. The atmosphere feels a little tense, but the conversation goes on.", 12),

        # Night Chat
        (12, 3, 99, None, "That night, you pick up your phone, hesitating whether you should text her.", 13),
        (13, 3, 2, None, "Maybe I should just text her...", None),
        (14, 3, 99, 7, "Lin replies with a short message and a cute sticker at the end...", 15),

        # === DAY 2: Memories ===
        # Library
        (15, 4, 1, 1, "Looking for a book? I really like this corner.", 16),
        (16, 4, 1, 3, "But... people say I'm strange for liking dark quiet corners like this.", 17),
        (17, 4, 2, None, "(Lin looks a little sad... what should I say?)", None),

        # Positive
        (18, 4, 1, 4, "Really...? You actually think that?", 19),
        (19, 4, 2, None, "Of course. Being yourself is the best thing you can do.", 20),

        # Negative
        (180, 4, 1, 3, "Maybe... I really am strange. Sorry if I made you uncomfortable.", 190),
        (190, 4, 2, None, "Ah... I didn't mean it like that. I was just being honest.", 20),

        # Rooftop
        (20, 5, 99, None, "In the evening, Lin invites you to the skywalk.", 21),
        (21, 5, 1, 1, "The view here is beautiful... it feels peaceful.", 22),
        (22, 5, 1, 3, "Honestly... do you ever get tired of me being like this?", None),

        # Positive
        (23, 5, 1, 6, "Really? Thank you ^^", 24),
        (24, 5, 99, None, "Lin's face turns slightly red. The atmosphere between you begins to change.", 25),

        # Negative
        (230, 5, 1, 3, "I see... I'll try to improve myself. Sorry about that.", 240),
        (240, 5, 99, None, "Lin lowers her head. The atmosphere becomes a little awkward.", 25),

        # Night Chat 2
        (25, 9, 99, None, "You send Lin a message, but she reads it and doesn't reply for almost an hour...", 26),
        (26, 9, 2, None, "(What should I do...? Did I say something wrong?)", None),

        # Positive
        (27, 9, 99, None, "After a while, Lin replies: 'Sorry ^^ I was busy for a bit.'", 28),

        # Negative
        (270, 9, 99, None, "You decide to delete the message... and that night, no reply ever comes.", 28),

        # === DAY 3: Honesty ===
        # Music Room
        (28, 6, 2, None, "This song... it reminds me of you.", 29),
        (29, 6, 1, 1, "Hm? Why is that?", None),

        # Positive
        (30, 6, 1, 6, "I see... I'm glad to hear that.", 31),

        # Negative
        (300, 6, 1, 1, "Oh... I thought you meant it.", 31),

        # Rain Scene
        (31, 7, 99, None, "Rain begins to fall heavily. Lin stands quietly, something clearly bothering her.", 32),
        (32, 7, 2, None, "Lin... you don't look okay today.", None),

        (33, 7, 1, 5, "Sniff... I'm just... scared...", 34),
        (34, 7, 1, 5, "If you get tired of me... you'll disappear too, right? Just like everyone else.", 35),
        (35, 7, 2, None, "(So this is what she's been holding inside all this time...)", None),

        # Positive
        (36, 7, 1, 5, "You... promise, okay?", 37),

        # Negative
        (380, 7, 1, 3, "I understand... I'll try not to be so strange.", 37),

        (37, 7, 99, None, "The sound of the rain slowly fades... it's time for this relationship to become clear.", 999),

        # === ENDINGS ===

        # GOOD END
        (100, 99, 99, None, "GOOD END — The One Who Stayed", 1001),
        (1001, 99, 99, None, "Lin: 'Thank you... for staying here.'", 1002),
        (1002, 99, 99, None, "Lin: 'Even though I don't talk much... even though I'm awkward... you never walked away.'", 1003),
        (1003, 99, 99, None, "Lin: 'At first I was really scared... scared that one day you'd disappear like everyone else.'", 1004),
        (1004, 99, 99, None, "Lin: 'But now... I think I believe it.'", 1005),
        (1005, 99, 99, None, "Lin: 'That you'll still be here... even if one day I turn around.'", 1006),
        (1006, 99, 99, None, "She gives you a gentle smile — the warmest smile you've ever seen.", 1007),
        (1007, 99, 99, None, "And this time... when she turns around,", 1008),
        (1008, 99, 99, None, "the person standing there... is still me.", None),

        # NORMAL END
        (101, 99, 99, None, "NORMAL END — A Relationship That Needs Time", 1011),
        (1011, 99, 99, None, "Lin: 'Thank you... for saying that to me.'", 1012),
        (1012, 99, 99, None, "Lin: 'But for me... it might be a little too soon.'", 1013),
        (1013, 99, 99, None, "Lin: 'I want to get to know you a little more first.'", 1014),
        (1014, 99, 99, None, "Lin: 'If one day... you still want to stand beside me,'", 1015),
        (1015, 99, 99, None, "Lin: 'then maybe we can talk about this again.'", 1016),
        (1016, 99, 99, None, "She gives a shy smile before looking away.", 1017),
        (1017, 99, 99, None, "Some relationships don't end...", 1018),
        (1018, 99, 99, None, "they just need time before someone turns around again.", None),

        # BAD END
        (102, 99, 99, None, "BAD END — The Place Without You", 1021),
        (1021, 99, 99, None, "Lin: 'I-I'm sorry...'", 1022),
        (1022, 99, 99, None, "Lin: 'I was really happy that you chose me...'", 1023),
        (1023, 99, 99, None, "Lin: 'But I'm scared... that one day you'll turn and look somewhere else.'", 1024),
        (1024, 99, 99, None, "Lin: 'I don't want to wait for the day you realize the person you want beside you... isn't me.'", 1025),
        (1025, 99, 99, None, "Lin: 'If one day you turn around...'", 1026),
        (1026, 99, 99, None, "Lin: 'I hope... I'll still be here.'", 1027),
        (1027, 99, 99, None, "She lowers her gaze and slowly turns away.", 1028),
        (1028, 99, 99, None, "But this time, the one who never turns back... is her.", None)

    ]
    
    for d in dialogues:
        c.execute("INSERT INTO dialogues VALUES (?,?,?,?,?,?)", d)

    # --- 5. Choices
    choices = [

        # Day 1: Scene 1
        (1, 3, "I'm glad it's you. Nice to work with you.", 3, 4, 0),
        (2, 3, "Oh, it's you. Nice to meet you.", 1, 4, 0),

        # Day 1: Scene 2
        (3, 9, "Ask about the things she likes", 2, 10, 0),
        (4, 9, "Only talk about the project", 0, 110, 0),

        # Day 1: Night
        (5, 13, "Send her a song", 3, 14, 0),
        (6, 13, "Ask if she's still awake", 1, 14, 0),

        # Day 2: Library
        (7, 17, "That's part of your charm.", 3, 18, 0),
        (8, 17, "Well... it is kind of strange.", -2, 180, 0),

        # Day 2: skywalk
        (9, 22, "I could never get tired of you.", 5, 23, 1),
        (10, 22, "Sometimes... but it's okay.", -1, 230, 0),

        # Day 2: Night 2
        (11, 26, "Text: 'No need to reply right away.'", 3, 27, 0),
        (12, 26, "Delete the message", -1, 270, 0),

        # Day 3: Music
        (13, 29, "It feels warm somehow... listening to it with you.", 4, 30, 0),
        (14, 29, "I don't really think much about it.", 0, 300, 0),

        # Day 3: Rain
        (15, 32, "If you don't want to talk, I'll just sit here with you.", 4, 33, 1),
        (16, 32, "What happened? You can tell me.", 1, 33, 0),

        # Day 3: The Promise
        (17, 35, "I can't promise anything big... but if one day you turn around, I promise I'll still be here.", 5, 36, 1),
        (18, 35, "Well... maybe if you didn't act so weird and annoying all the time.", -100, 380, 0)

        ]

    for ch in choices:
        c.execute(
         "INSERT INTO choices (id, parent_dialogue_id, text_label, score_impact, next_dialogue_id) VALUES (?, ?, ?, ?, ?)",
        ch[:5]
    )
    conn.commit()
    conn.close()

    print("o(*▽*)o")

if __name__ == '__main__':
    init_db()