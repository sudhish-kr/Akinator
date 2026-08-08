"""Curated and templated yes/no questions for the knowledge seed catalog."""

from __future__ import annotations

QUESTION_CATEGORIES: list[str] = [
    "Physical appearance",
    "Gender",
    "Age",
    "Nationality",
    "Profession",
    "Sports",
    "Movies",
    "TV",
    "Anime",
    "Cartoons",
    "Gaming",
    "Science",
    "History",
    "Politics",
    "Music",
    "Literature",
    "Mythology",
    "Technology",
    "Relationships",
    "Awards",
    "Personality",
    "Fictional traits",
    "Time period",
]

# Kid-friendly legacy questions used by likelihood RULES in generate_knowledge_seed.py
_LEGACY: list[tuple[str, str, float]] = [
    ("Is this a made-up character?", "Fictional traits", 0.55),
    ("Is this a real person?", "Personality", 0.52),
    ("Is this person still alive?", "Age", 0.48),
    ("Is this from a movie?", "Movies", 0.58),
    ("Is this from anime?", "Anime", 0.56),
    ("Is this from a video game?", "Gaming", 0.55),
    ("Is this from a TV show?", "TV", 0.54),
    ("Is this a superhero?", "Movies", 0.45),
    ("Is this from a cartoon?", "Cartoons", 0.56),
    ("Is this from an old legend?", "Mythology", 0.57),
    ("Is this a sports player?", "Sports", 0.58),
    ("Is this a scientist?", "Science", 0.55),
    ("Is this from long ago?", "History", 0.52),
    ("Is this a musician?", "Music", 0.56),
    ("Is this a writer?", "Literature", 0.52),
    ("Is this a political leader?", "Politics", 0.55),
    ("Is this a business leader?", "Technology", 0.50),
    ("Is this a hero?", "Fictional traits", 0.48),
    ("Is this a villain?", "Fictional traits", 0.46),
    ("Is this about magic?", "Fictional traits", 0.50),
    ("Is this sci-fi?", "Fictional traits", 0.48),
    ("Are they from Asia?", "Nationality", 0.42),
    ("Are they from Europe?", "Nationality", 0.40),
    ("Are they from the Americas?", "Nationality", 0.40),
    ("Are they known today?", "Time period", 0.45),
    ("Were they famous in the 1900s?", "Time period", 0.44),
    ("Do they wear a costume?", "Physical appearance", 0.38),
    ("Are they a kid or teen?", "Age", 0.42),
    ("Have they won big awards?", "Awards", 0.48),
    ("Is this about space?", "Science", 0.40),
    ("Are they linked to war?", "History", 0.44),
    ("Are they on a famous team?", "Relationships", 0.42),
]

# Old RULES / override strings → new kid-friendly catalog text
LEGACY_TEXT_RENAMES: dict[str, str] = {
    "Is this character fictional?": "Is this a made-up character?",
    "Is this person alive today?": "Is this person still alive?",
    "Is this associated with movies?": "Is this from a movie?",
    "Is this from anime or manga?": "Is this from anime?",
    "Is this from television?": "Is this from a TV show?",
    "Is this from comics or superhero media?": "Is this a superhero?",
    "Is this from a cartoon or animated series?": "Is this from a cartoon?",
    "Is this from mythology or legend?": "Is this from an old legend?",
    "Is this an athlete or sports figure?": "Is this a sports player?",
    "Is this a scientist or inventor?": "Is this a scientist?",
    "Is this a historical figure from before 1900?": "Is this from long ago?",
    "Is this known for music?": "Is this a musician?",
    "Is this known for literature or writing?": "Is this a writer?",
    "Is this known for business or technology entrepreneurship?": "Is this a business leader?",
    "Is this character primarily a hero / protagonist?": "Is this a hero?",
    "Is this character a villain or antagonist?": "Is this a villain?",
    "Is this associated with magic or fantasy?": "Is this about magic?",
    "Is this associated with science fiction?": "Is this sci-fi?",
    "Is this person/character from Asia?": "Are they from Asia?",
    "Is this person/character from Europe?": "Are they from Europe?",
    "Is this person/character from the Americas?": "Are they from the Americas?",
    "Is this primarily known in the 21st century?": "Are they known today?",
    "Is this primarily known from the 20th century?": "Were they famous in the 1900s?",
    "Does this character wear a costume or mask?": "Do they wear a costume?",
    "Is this a child or teenager (in their main story)?": "Are they a kid or teen?",
    "Is this known for winning major awards or titles?": "Have they won big awards?",
    "Is this associated with space or astronomy?": "Is this about space?",
    "Is this associated with war or military leadership?": "Are they linked to war?",
    "Is this a member of a famous team or group?": "Are they on a famous team?",
}

_CURATED_BY_CATEGORY: dict[str, list[tuple[str, float]]] = {
    "Physical appearance": [
        ("Do they have blonde or light hair?", 0.28),
        ("Do they have dark brown or black hair?", 0.28),
        ("Do they have red hair?", 0.22),
        ("Do they have gray or white hair?", 0.24),
        ("Do they have a weird hair color?", 0.20),
        ("Are they very tall?", 0.26),
        ("Are they very short?", 0.24),
        ("Do they have a beard?", 0.30),
        ("Do they wear glasses?", 0.25),
        ("Do they have scars or marks?", 0.22),
        ("Are they often in a uniform?", 0.32),
        ("Do they wear a hat?", 0.24),
        ("Are they very strong looking?", 0.28),
        ("Do they have tattoos?", 0.20),
        ("Are they often in fancy clothes?", 0.26),
        ("Do they wear a cape?", 0.22),
        ("Are they bald?", 0.24),
        ("Do they have pointy ears?", 0.30),
    ],
    "Gender": [
        ("Are they a boy or man?", 0.50),
        ("Are they a girl or woman?", 0.50),
        ("Are they usually shown as a boy?", 0.48),
        ("Are they usually shown as a girl?", 0.48),
        ("Are they a queen or princess?", 0.32),
        ("Are they a king or prince?", 0.32),
        ("Do people call them he?", 0.46),
        ("Do people call them she?", 0.46),
        ("Are they a mom in their story?", 0.30),
        ("Are they a dad in their story?", 0.30),
        ("Are they a brother or sister?", 0.28),
        ("Are they married?", 0.26),
        ("Are they single in their story?", 0.24),
        ("Did their partner die?", 0.18),
        ("Are they a female god?", 0.28),
        ("Are they a male god?", 0.28),
        ("Are they a warrior?", 0.26),
        ("Are they a wizard or witch?", 0.24),
    ],
    "Age": [
        ("Are they very old?", 0.32),
        ("Are they middle-aged?", 0.30),
        ("Are they a young adult?", 0.32),
        ("Were they born before 1950?", 0.38),
        ("Were they born after 1980?", 0.36),
        ("Were they born in the 1990s?", 0.28),
        ("Were they born in the 2000s?", 0.22),
        ("Do they live forever?", 0.26),
        ("Are they a baby or toddler?", 0.18),
        ("Did they die young?", 0.24),
        ("Did they live past 80?", 0.26),
        ("Are they a student in their story?", 0.30),
        ("Are they retired now?", 0.22),
        ("Are they hundreds of years old?", 0.24),
        ("Are they an adult in their story?", 0.34),
        ("Are they still working today?", 0.36),
    ],
    "Nationality": [
        ("Are they from Africa?", 0.28),
        ("Are they from Australia?", 0.20),
        ("Are they from the Middle East?", 0.24),
        ("Are they from the United States?", 0.38),
        ("Are they from the United Kingdom?", 0.34),
        ("Are they from Japan?", 0.32),
        ("Are they from China?", 0.30),
        ("Are they from India?", 0.30),
        ("Are they from France?", 0.28),
        ("Are they from Germany?", 0.28),
        ("Are they from Brazil?", 0.26),
        ("Are they from Canada?", 0.26),
        ("Are they from Italy?", 0.26),
        ("Are they from Spain?", 0.24),
        ("Are they from Mexico?", 0.24),
        ("Are they from South Korea?", 0.24),
        ("Are they from Russia?", 0.26),
        ("Are they from Sweden or Norway?", 0.22),
    ],
    "Profession": [
        ("Are they a doctor?", 0.32),
        ("Are they a lawyer or judge?", 0.28),
        ("Are they a teacher?", 0.30),
        ("Are they an actor?", 0.36),
        ("Are they a chef?", 0.22),
        ("Are they a news reporter?", 0.26),
        ("Are they in the army?", 0.30),
        ("Are they a police officer?", 0.28),
        ("Are they a pilot or space traveler?", 0.24),
        ("Are they an artist?", 0.26),
        ("Are they a fashion model?", 0.22),
        ("Are they a comedian?", 0.26),
        ("Are they a religious leader?", 0.24),
        ("Are they a farmer?", 0.18),
        ("Are they an engineer?", 0.26),
        ("Are they a spy?", 0.24),
        ("Are they royalty?", 0.28),
        ("Are they a pirate?", 0.22),
    ],
    "Sports": [
        ("Are they famous for soccer?", 0.38),
        ("Are they famous for basketball?", 0.36),
        ("Are they famous for tennis?", 0.32),
        ("Are they famous for football?", 0.30),
        ("Are they famous for baseball?", 0.30),
        ("Are they famous for golf?", 0.28),
        ("Are they famous for boxing?", 0.30),
        ("Are they famous for cricket?", 0.28),
        ("Are they famous for hockey?", 0.26),
        ("Are they famous for swimming?", 0.26),
        ("Are they famous for running?", 0.28),
        ("Are they famous for gymnastics?", 0.24),
        ("Are they famous for racing?", 0.26),
        ("Did they win an Olympic medal?", 0.34),
        ("Do they hold a world record?", 0.30),
        ("Are they a coach, not a player?", 0.22),
        ("Are they famous for martial arts?", 0.26),
        ("Are they famous for skiing?", 0.22),
    ],
    "Movies": [
        ("Are they from a superhero movie?", 0.42),
        ("Are they from a scary movie?", 0.32),
        ("Are they from a funny love movie?", 0.28),
        ("Are they from a big action movie?", 0.38),
        ("Are they from a Disney or Pixar movie?", 0.34),
        ("Are they from a sci-fi movie?", 0.36),
        ("Are they from a fantasy movie?", 0.34),
        ("Are they from a war movie?", 0.30),
        ("Are they from a spy movie?", 0.32),
        ("Are they a movie director?", 0.28),
        ("Are they a famous movie star?", 0.36),
        ("Are they from a book-based movie?", 0.32),
        ("Are they from a movie with sequels?", 0.34),
        ("Are they from an old black-and-white movie?", 0.22),
        ("Are they from a kung fu movie?", 0.26),
        ("Are they from a cowboy movie?", 0.22),
        ("Are they from a singing movie?", 0.24),
        ("Are they from a Studio Ghibli movie?", 0.28),
    ],
    "TV": [
        ("Are they from a sitcom?", 0.34),
        ("Are they from a crime TV show?", 0.32),
        ("Are they from a hospital TV show?", 0.28),
        ("Are they from a fantasy TV show?", 0.32),
        ("Are they from a reality TV show?", 0.26),
        ("Are they from a talk show?", 0.22),
        ("Are they from a streaming TV show?", 0.34),
        ("Are they from a soap opera?", 0.22),
        ("Are they from a sci-fi TV show?", 0.34),
        ("Are they from a kids TV show?", 0.30),
        ("Are they from a game show?", 0.20),
        ("Are they from a news show?", 0.22),
        ("Are they from a British TV show?", 0.28),
        ("Are they from a short TV series?", 0.24),
        ("Are they from a superhero TV show?", 0.30),
        ("Are they from a cooking TV show?", 0.20),
        ("Are they from a police TV show?", 0.30),
        ("Are they from a school TV show?", 0.28),
    ],
    "Anime": [
        ("Are they from an action anime?", 0.38),
        ("Are they from a love story anime?", 0.28),
        ("Are they from a robot anime?", 0.30),
        ("Are they from another-world anime?", 0.32),
        ("Do they have special powers?", 0.36),
        ("Are they a ninja or samurai?", 0.28),
        ("Are they from a sports anime?", 0.26),
        ("Are they from a daily-life anime?", 0.24),
        ("Are they from a magic-girl anime?", 0.26),
        ("Are they from a scary anime?", 0.24),
        ("Are they from a Ghibli anime?", 0.26),
        ("Are they from a long anime series?", 0.34),
        ("Do they change into another form?", 0.28),
        ("Are they from a grown-up anime?", 0.26),
        ("Are they a student in their anime?", 0.30),
        ("Are they from a pirate adventure anime?", 0.28),
        ("Are they from a battle anime?", 0.28),
        ("Do they have a special move or weapon?", 0.30),
    ],
    "Cartoons": [
        ("Are they from a classic cartoon?", 0.28),
        ("Are they from a Nickelodeon cartoon?", 0.30),
        ("Are they from Cartoon Network?", 0.30),
        ("Are they a talking animal?", 0.34),
        ("Are they from an old Saturday cartoon?", 0.26),
        ("Are they from a Disney TV cartoon?", 0.28),
        ("Are they from a grown-up cartoon?", 0.30),
        ("Are they from a clay cartoon?", 0.20),
        ("Are they a sidekick character?", 0.28),
        ("Are they from a preschool cartoon?", 0.24),
        ("Are they from a superhero cartoon?", 0.28),
        ("Are they from a Hanna-Barbera cartoon?", 0.22),
        ("Are they from a DreamWorks cartoon?", 0.24),
        ("Are they known for a catchphrase?", 0.26),
        ("Are they from an online cartoon?", 0.22),
        ("Are they from an anime-style cartoon?", 0.26),
        ("Are they a bad guy in a cartoon?", 0.30),
        ("Are they from a family adventure cartoon?", 0.28),
    ],
    "Gaming": [
        ("Are they from a Nintendo game?", 0.38),
        ("Are they from a shooter game?", 0.32),
        ("Are they from a role-playing game?", 0.36),
        ("Are they from a fighting game?", 0.32),
        ("Are they from a jumping platform game?", 0.34),
        ("Are they from a scary game?", 0.30),
        ("Are they from an online multiplayer game?", 0.32),
        ("Are they from a phone game?", 0.26),
        ("Are they from a PlayStation game?", 0.28),
        ("Are they from an Xbox game?", 0.26),
        ("Are they from a PC game?", 0.30),
        ("Are they a playable game character?", 0.34),
        ("Are they from an open-world game?", 0.32),
        ("Are they from an old arcade game?", 0.28),
        ("Are they from a sports video game?", 0.26),
        ("Are they from a strategy game?", 0.24),
        ("Are they from a battle royale game?", 0.26),
        ("Are they from a small indie game?", 0.24),
    ],
    "Science": [
        ("Are they a physics scientist?", 0.32),
        ("Are they a biology scientist?", 0.30),
        ("Are they a chemistry scientist?", 0.28),
        ("Are they a math expert?", 0.28),
        ("Do they study health and medicine?", 0.30),
        ("Did they win a Nobel science prize?", 0.34),
        ("Do they study animals and nature?", 0.28),
        ("Do they study tiny particles?", 0.26),
        ("Do they work with computers?", 0.32),
        ("Do they study stars and planets?", 0.28),
        ("Do they study climate and nature?", 0.26),
        ("Do they study genes and DNA?", 0.28),
        ("Do they explain science on TV?", 0.30),
        ("Do they study atoms and energy?", 0.26),
        ("Do they work on robots or AI?", 0.28),
        ("Do they study dinosaurs?", 0.24),
        ("Do they study the brain?", 0.24),
        ("Are they a made-up scientist?", 0.30),
    ],
    "History": [
        ("Are they from ancient Greece or Rome?", 0.32),
        ("Are they from ancient Egypt?", 0.28),
        ("Are they from medieval times?", 0.30),
        ("Are they from the Renaissance?", 0.28),
        ("Are they from the 1700s?", 0.26),
        ("Are they from the 1800s?", 0.30),
        ("Are they a king or queen?", 0.34),
        ("Are they a rebel leader?", 0.30),
        ("Are they an explorer?", 0.28),
        ("Are they linked to World War I?", 0.26),
        ("Are they linked to World War II?", 0.32),
        ("Are they linked to the Civil War?", 0.24),
        ("Are they linked to building an empire?", 0.26),
        ("Are they an old philosopher?", 0.28),
        ("Are they from the Cold War era?", 0.26),
        ("Are they a civil rights leader?", 0.28),
        ("Are they from ancient China?", 0.28),
        ("Are they from Viking times?", 0.22),
    ],
    "Politics": [
        ("Are they a head of a country?", 0.38),
        ("Are they a U.S. president?", 0.34),
        ("Are they a prime minister?", 0.32),
        ("Are they a harsh ruler?", 0.28),
        ("Are they a diplomat?", 0.24),
        ("Are they in a royal family?", 0.28),
        ("Are they linked to the United Nations?", 0.22),
        ("Are they a civil rights activist?", 0.28),
        ("Do they fight for women's rights?", 0.24),
        ("Are they linked to socialism?", 0.26),
        ("Are they linked to conservatism?", 0.26),
        ("Are they linked to liberal politics?", 0.26),
        ("Are they a senator or MP?", 0.28),
        ("Are they a governor or mayor?", 0.26),
        ("Are they known for a big speech?", 0.28),
        ("Are they linked to independence fights?", 0.26),
        ("Did they win a Nobel Peace Prize?", 0.28),
        ("Are they still in politics today?", 0.30),
    ],
    "Music": [
        ("Are they a pop singer?", 0.36),
        ("Are they a rock musician?", 0.34),
        ("Are they a rap artist?", 0.32),
        ("Are they a classical composer?", 0.30),
        ("Are they a country singer?", 0.26),
        ("Are they a jazz musician?", 0.26),
        ("Are they a K-pop singer?", 0.28),
        ("Are they a singer-songwriter?", 0.32),
        ("Are they in a famous band?", 0.34),
        ("Are they a solo singer?", 0.32),
        ("Did they win a Grammy?", 0.32),
        ("Do they play the guitar?", 0.30),
        ("Do they play the piano?", 0.28),
        ("Do they play the drums?", 0.24),
        ("Do they play the violin?", 0.24),
        ("Are they an opera singer?", 0.22),
        ("Are they a DJ or beat maker?", 0.26),
        ("Are they known for a music video?", 0.28),
    ],
    "Literature": [
        ("Are they a book author?", 0.32),
        ("Are they a poet?", 0.28),
        ("Are they a play writer?", 0.26),
        ("Are they from a fantasy book?", 0.34),
        ("Are they from a mystery book?", 0.30),
        ("Are they from a sci-fi book?", 0.32),
        ("Are they from a kids book?", 0.30),
        ("Are they from an old 1800s book?", 0.28),
        ("Are they from a Shakespeare play?", 0.28),
        ("Did they win a Nobel book prize?", 0.26),
        ("Are they from a teen book?", 0.28),
        ("Are they from a comic book?", 0.30),
        ("Are they a book detective?", 0.28),
        ("Are they from a dystopia book?", 0.26),
        ("Are they from a love story book?", 0.24),
        ("Are they from a scary book?", 0.24),
        ("Are they a news writer?", 0.24),
        ("Are they from a book series?", 0.32),
    ],
    "Mythology": [
        ("Are they from Greek myths?", 0.38),
        ("Are they from Norse myths?", 0.34),
        ("Are they from Egyptian myths?", 0.32),
        ("Are they from Hindu myths?", 0.30),
        ("Are they from Japanese myths?", 0.28),
        ("Are they from Roman myths?", 0.30),
        ("Are they a god or goddess?", 0.36),
        ("Are they a myth hero?", 0.34),
        ("Are they a myth monster?", 0.30),
        ("Are they linked to the underworld?", 0.26),
        ("Are they linked to the sea?", 0.26),
        ("Are they a trickster?", 0.26),
        ("Are they from Celtic myths?", 0.24),
        ("Are they from Chinese myths?", 0.26),
        ("Are they from Aztec myths?", 0.24),
        ("Are they linked to creation stories?", 0.24),
        ("Are they linked to war?", 0.28),
        ("Are they linked to love?", 0.24),
    ],
    "Technology": [
        ("Did they start a big tech company?", 0.36),
        ("Are they linked to Apple?", 0.30),
        ("Are they linked to Microsoft?", 0.28),
        ("Are they linked to Google?", 0.28),
        ("Are they linked to Amazon?", 0.28),
        ("Are they linked to Tesla?", 0.28),
        ("Are they linked to social media?", 0.32),
        ("Are they a software coder?", 0.30),
        ("Do they work on AI?", 0.30),
        ("Do they work on space travel?", 0.28),
        ("Are they a big investor?", 0.26),
        ("Are they linked to crypto?", 0.24),
        ("Do they make computer chips?", 0.24),
        ("Do they work on free software?", 0.24),
        ("Are they a billionaire?", 0.30),
        ("Are they linked to game companies?", 0.26),
        ("Are they linked to online shopping?", 0.26),
        ("Are they known for a big product launch?", 0.28),
    ],
    "Relationships": [
        ("Are they part of a famous duo?", 0.30),
        ("Are they part of a famous trio?", 0.26),
        ("Are they a group leader?", 0.32),
        ("Are they a sidekick?", 0.26),
        ("Are they in a royal family?", 0.28),
        ("Are they in a band?", 0.30),
        ("Are they on a sports team?", 0.32),
        ("Are they on a superhero team?", 0.30),
        ("Are they a mentor to others?", 0.28),
        ("Are they a rival to someone famous?", 0.26),
        ("Are they married to someone famous?", 0.24),
        ("Are they siblings with someone famous?", 0.22),
        ("Are they in a made-up guild?", 0.24),
        ("Are they an only child?", 0.20),
        ("Are they an orphan in their story?", 0.24),
        ("Are they in a famous made-up family?", 0.28),
        ("Did they help start a group?", 0.26),
        ("Are they known for a best friendship?", 0.26),
    ],
    "Awards": [
        ("Did they win an Oscar?", 0.30),
        ("Did they win a Grammy?", 0.28),
        ("Did they win an Emmy?", 0.26),
        ("Did they win a Nobel Prize?", 0.28),
        ("Did they win Olympic gold?", 0.30),
        ("Did they win a Pulitzer Prize?", 0.24),
        ("Did they win a Tony Award?", 0.22),
        ("Did they win a Golden Globe?", 0.24),
        ("Were they knighted or honored?", 0.24),
        ("Are they in a hall of fame?", 0.26),
        ("Did they win a big book prize?", 0.22),
        ("Did they win a big soccer award?", 0.24),
        ("Did they win MVP in their sport?", 0.26),
        ("Did they get a national medal?", 0.22),
        ("Did they win a big film festival prize?", 0.22),
        ("Did they win many Grammys?", 0.26),
        ("Did they win a big tech prize?", 0.20),
        ("Are they in Guinness World Records?", 0.24),
    ],
    "Personality": [
        ("Are they known for being funny?", 0.28),
        ("Are they known for being serious?", 0.26),
        ("Are they known for being controversial?", 0.28),
        ("Do they do a lot of charity work?", 0.26),
        ("Are they known for speaking their mind?", 0.26),
        ("Are they known for being private?", 0.24),
        ("Are they known for being charming?", 0.28),
        ("Are they known for being rebellious?", 0.26),
        ("Are they known for being wise?", 0.26),
        ("Are they known for being quirky?", 0.26),
        ("Are they known for being confident?", 0.26),
        ("Are they known for being kind?", 0.26),
        ("Are they known for being tough?", 0.26),
        ("Are they known for being shy?", 0.22),
        ("Are they known for being outgoing?", 0.24),
        ("Are they known for a catchphrase?", 0.28),
        ("Are they seen as a role model?", 0.26),
        ("Are they known for beating hard odds?", 0.28),
    ],
    "Fictional traits": [
        ("Do they have super strength?", 0.30),
        ("Can they fly?", 0.28),
        ("Do they use magic?", 0.32),
        ("Do they use a sword?", 0.28),
        ("Do they use guns?", 0.26),
        ("Are they an alien?", 0.28),
        ("Are they a robot?", 0.26),
        ("Are they undead like a vampire?", 0.26),
        ("Can they change shape?", 0.24),
        ("Are they royalty in their world?", 0.28),
        ("Are they a gray-area hero?", 0.28),
        ("Do they have a secret identity?", 0.30),
        ("Do they live a very long time?", 0.26),
        ("Do they have a sad backstory?", 0.26),
        ("Are they from a broken future world?", 0.26),
        ("Do they have a pet or animal friend?", 0.24),
        ("Are they a mentor figure?", 0.26),
        ("Do they die and come back?", 0.22),
    ],
    "Time period": [
        ("Are they mainly from the 1800s?", 0.30),
        ("Are they mainly from the 1700s?", 0.26),
        ("Are they mainly from before the 1700s?", 0.28),
        ("Are they mainly from the 1960s?", 0.24),
        ("Are they mainly from the 1970s?", 0.24),
        ("Are they mainly from the 1980s?", 0.26),
        ("Are they mainly from the 1990s?", 0.28),
        ("Are they mainly from the 2000s?", 0.30),
        ("Are they mainly from the 2010s?", 0.30),
        ("Are they from ancient times?", 0.30),
        ("Are they from medieval times?", 0.28),
        ("Are they from the Renaissance?", 0.26),
        ("Are they from Victorian times?", 0.26),
        ("Are they from the 1920s?", 0.22),
        ("Are they from the Great Depression?", 0.20),
        ("Are they from the Cold War?", 0.24),
        ("Are they from the future?", 0.26),
        ("Are they from a fantasy world?", 0.28),
    ],
}

# Flatten legacy + curated into CURATED_QUESTIONS export
CURATED_QUESTIONS: list[tuple[str, str, float]] = list(_LEGACY)
_seen_legacy_texts = {t.casefold() for t, _, _ in _LEGACY}
for category, items in _CURATED_BY_CATEGORY.items():
    for text, ig in items:
        if text.casefold() not in _seen_legacy_texts:
            CURATED_QUESTIONS.append((text, category, ig))

# Template expansion pools
_HAIR_COLORS = [
    "blonde", "brown", "black", "red", "auburn", "silver", "white", "blue", "pink", "green",
]
_SPORTS = [
    "soccer", "basketball", "tennis", "golf", "boxing", "cricket", "swimming", "cycling",
    "skiing", "rugby", "volleyball", "wrestling", "archery", "fencing", "surfing",
]
_INSTRUMENTS = [
    "guitar", "piano", "drums", "violin", "saxophone", "trumpet", "flute", "cello",
    "bass guitar", "harmonica", "ukulele", "keyboard", "harp", "banjo", "clarinet",
]
_MYTHOLOGIES = [
    "Greek", "Norse", "Egyptian", "Roman", "Hindu", "Japanese", "Celtic", "Chinese",
    "Aztec", "Mayan", "Persian", "Slavic", "Polynesian", "Inuit", "African",
]
_COUNTRIES = [
    "the United States", "the United Kingdom", "Japan", "China", "India", "France",
    "Germany", "Brazil", "Canada", "Italy", "Spain", "Mexico", "South Korea", "Russia",
    "Australia", "Argentina", "Egypt", "Nigeria", "Sweden", "Turkey",
]
_PROFESSIONS = [
    "doctor", "lawyer", "teacher", "engineer", "architect", "chef", "pilot", "soldier",
    "journalist", "artist", "scientist", "farmer", "mechanic", "nurse", "firefighter",
]
_ANIME_TROPES = [
    "a power boost", "a rival", "a mentor", "a special move", "a school uniform",
    "a sad past", "a funny friend", "a love triangle", "a big contest", "a beach day",
    "extra filler episodes", "a time jump",
]
_GAME_GENRES = [
    "action", "role-playing", "shooter", "platform", "puzzle", "racing", "fighting",
    "scary", "open-world", "stealth", "battle royale", "story", "music", "tower defense",
    "exploration",
]
_AWARD_TYPES = [
    "Oscar", "Grammy", "Emmy", "Tony", "Nobel Prize", "Pulitzer", "Golden Globe",
    "Olympic gold medal", "Ballon d'Or", "MVP", "Cannes film prize", "Booker Prize",
    "MTV video award", "Brit Award", "country music award",
]
_TV_GENRES = [
    "sitcom", "crime", "medical", "reality", "talk", "documentary", "soap opera",
    "anthology", "miniseries", "late-night", "news", "game",
]
_MOVIE_GENRES = [
    "horror", "comedy", "romance", "action", "thriller", "war", "western", "musical",
    "documentary", "mystery", "true story", "animated", "superhero", "disaster",
]
_SCIENCE_FIELDS = [
    "physics", "chemistry", "biology", "stars", "rocks", "the mind", "nature",
    "dinosaurs", "the brain", "genes", "weather", "oceans",
]
_HISTORICAL_ERA = [
    "Ancient Rome", "Ancient Greece", "Ancient Egypt", "the Middle Ages", "the Renaissance",
    "the Industrial Revolution", "World War I", "World War II", "the Cold War",
    "the American Revolution", "the French Revolution", "Viking times",
]
_TECH_COMPANIES = [
    "Apple", "Microsoft", "Google", "Amazon", "Meta", "Tesla", "IBM", "Intel",
    "Samsung", "Sony", "Netflix", "Spotify", "Adobe", "Oracle", "Nvidia",
]
_PERSONALITY_TRAITS = [
    "optimistic", "gloomy", "ambitious", "lazy", "loyal", "sneaky", "calm", "impulsive",
    "creative", "logical", "caring", "cold",
]
_FICTIONAL_POWERS = [
    "mind reading", "moving things with their mind", "invisibility", "time travel",
    "healing", "fire powers", "ice powers", "lightning powers", "super speed", "super smarts",
]


def _template_questions() -> list[tuple[str, str, float]]:
    """Generate additional questions from templates."""
    out: list[tuple[str, str, float]] = []

    for color in _HAIR_COLORS:
        out.append((f"Do they have {color} hair?", "Physical appearance", 0.20))

    for sport in _SPORTS:
        out.append((f"Are they famous for {sport}?", "Sports", 0.28))

    for inst in _INSTRUMENTS:
        out.append((f"Do they play the {inst}?", "Music", 0.22))

    for myth in _MYTHOLOGIES:
        out.append((f"Are they from {myth} myths?", "Mythology", 0.26))

    for country in _COUNTRIES:
        out.append((f"Are they from {country}?", "Nationality", 0.24))

    for prof in _PROFESSIONS:
        out.append((f"Are they a {prof}?", "Profession", 0.24))

    for trope in _ANIME_TROPES:
        out.append((f"Does their anime have {trope}?", "Anime", 0.20))

    for genre in _GAME_GENRES:
        out.append((f"Are they from a {genre} game?", "Gaming", 0.24))

    for award in _AWARD_TYPES:
        out.append((f"Did they win a {award}?", "Awards", 0.22))

    for genre in _TV_GENRES:
        out.append((f"Are they from a {genre} TV show?", "TV", 0.24))

    for genre in _MOVIE_GENRES:
        out.append((f"Are they from a {genre} movie?", "Movies", 0.24))

    for field in _SCIENCE_FIELDS:
        out.append((f"Do they study {field}?", "Science", 0.22))

    for era in _HISTORICAL_ERA:
        out.append((f"Are they linked to {era}?", "History", 0.24))

    for company in _TECH_COMPANIES:
        out.append((f"Are they linked to {company}?", "Technology", 0.22))

    for trait in _PERSONALITY_TRAITS:
        out.append((f"Are they known for being {trait}?", "Personality", 0.20))

    for power in _FICTIONAL_POWERS:
        out.append((f"Do they have {power}?", "Fictional traits", 0.22))

    for role in ["warrior", "wizard", "princess", "knight", "assassin", "healer"]:
        out.append((f"Are they a {role}?", "Gender", 0.22))

    for decade in ["1920s", "1930s", "1940s", "1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s"]:
        out.append((f"Were they born in the {decade}?", "Age", 0.22))

    for rel in ["best friend", "mentor", "rival", "crush", "parent", "sibling", "partner"]:
        out.append((f"Are they known for a {rel}?", "Relationships", 0.20))

    for studio in ["Disney", "Pixar", "DreamWorks", "Nickelodeon", "Cartoon Network", "Adult Swim"]:
        out.append((f"Are they from a {studio} cartoon?", "Cartoons", 0.24))

    for office in ["president", "prime minister", "senator", "governor", "mayor", "monarch"]:
        out.append((f"Are they a {office}?", "Politics", 0.26))

    for lit in ["mystery", "romance", "horror", "fantasy", "sci-fi", "history", "satire"]:
        out.append((f"Are they from a {lit} book?", "Literature", 0.22))

    for century in ["16th", "17th", "18th", "19th", "20th", "21st"]:
        out.append((f"Are they mainly from the {century} century?", "Time period", 0.26))

    return out


def build_question_catalog(min_count: int = 520) -> list[dict]:
    """Build deduplicated question catalog with per-category minimums."""
    min_per_category = 15
    seen: set[str] = set()
    catalog: list[dict] = []
    per_category: dict[str, int] = {cat: 0 for cat in QUESTION_CATEGORIES}

    def add(text: str, category: str, initial_ig: float) -> None:
        key = text.casefold().strip()
        if not key or key in seen:
            return
        if category not in QUESTION_CATEGORIES:
            return
        ig = max(0.12, min(0.65, round(initial_ig, 2)))
        seen.add(key)
        catalog.append(
            {
                "text": text.strip(),
                "category": category,
                "is_active": True,
                "avg_information_gain": ig,
                "times_asked": 0,
            }
        )
        per_category[category] += 1

    for text, category, ig in CURATED_QUESTIONS:
        add(text, category, ig)

    for text, category, ig in _template_questions():
        add(text, category, ig)

    if len(catalog) < min_count:
        raise RuntimeError(
            f"Question catalog has {len(catalog)} entries; need >= {min_count}. "
            f"Per-category: {per_category}"
        )
    for category in QUESTION_CATEGORIES:
        if per_category[category] < min_per_category:
            raise RuntimeError(
                f"Category {category!r} has {per_category[category]} questions; "
                f"need >= {min_per_category}"
            )

    return catalog


def legacy_question_texts() -> set[str]:
    """Return the legacy question texts required by likelihood RULES."""
    return {text for text, _, _ in _LEGACY}
