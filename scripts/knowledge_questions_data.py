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

# Legacy question texts required by likelihood RULES in generate_knowledge_seed.py
_LEGACY: list[tuple[str, str, float]] = [
    ("Is this character fictional?", "Fictional traits", 0.55),
    ("Is this a real person?", "Personality", 0.52),
    ("Is this person alive today?", "Age", 0.48),
    ("Is this associated with movies?", "Movies", 0.58),
    ("Is this from anime or manga?", "Anime", 0.56),
    ("Is this from a video game?", "Gaming", 0.55),
    ("Is this from television?", "TV", 0.54),
    ("Is this from comics or superhero media?", "Movies", 0.45),
    ("Is this from a cartoon or animated series?", "Cartoons", 0.56),
    ("Is this from mythology or legend?", "Mythology", 0.57),
    ("Is this an athlete or sports figure?", "Sports", 0.58),
    ("Is this a scientist or inventor?", "Science", 0.55),
    ("Is this a historical figure from before 1900?", "History", 0.52),
    ("Is this known for music?", "Music", 0.56),
    ("Is this known for literature or writing?", "Literature", 0.52),
    ("Is this a political leader?", "Politics", 0.55),
    ("Is this known for business or technology entrepreneurship?", "Technology", 0.50),
    ("Is this character primarily a hero / protagonist?", "Fictional traits", 0.48),
    ("Is this character a villain or antagonist?", "Fictional traits", 0.46),
    ("Is this associated with magic or fantasy?", "Fictional traits", 0.50),
    ("Is this associated with science fiction?", "Fictional traits", 0.48),
    ("Is this person/character from Asia?", "Nationality", 0.42),
    ("Is this person/character from Europe?", "Nationality", 0.40),
    ("Is this person/character from the Americas?", "Nationality", 0.40),
    ("Is this primarily known in the 21st century?", "Time period", 0.45),
    ("Is this primarily known from the 20th century?", "Time period", 0.44),
    ("Does this character wear a costume or mask?", "Physical appearance", 0.38),
    ("Is this a child or teenager (in their main story)?", "Age", 0.42),
    ("Is this known for winning major awards or titles?", "Awards", 0.48),
    ("Is this associated with space or astronomy?", "Science", 0.40),
    ("Is this associated with war or military leadership?", "History", 0.44),
    ("Is this a member of a famous team or group?", "Relationships", 0.42),
]

_CURATED_BY_CATEGORY: dict[str, list[tuple[str, float]]] = {
    "Physical appearance": [
        ("Does this person or character have blonde or light-colored hair?", 0.28),
        ("Does this person or character have dark brown or black hair?", 0.28),
        ("Does this person or character have red or auburn hair?", 0.22),
        ("Does this person or character have white, silver, or gray hair?", 0.24),
        ("Does this person or character have an unusual hair color (blue, pink, green, etc.)?", 0.20),
        ("Is this person or character notably tall?", 0.26),
        ("Is this person or character notably short or petite?", 0.24),
        ("Does this person or character have a beard or mustache?", 0.30),
        ("Does this person or character wear glasses?", 0.25),
        ("Does this person or character have visible scars or marks?", 0.22),
        ("Is this person or character often depicted wearing a uniform?", 0.32),
        ("Does this person or character have a distinctive hat or headwear?", 0.24),
        ("Is this person or character muscular or physically imposing?", 0.28),
        ("Does this person or character have tattoos or body art?", 0.20),
        ("Is this person or character often shown in formal attire?", 0.26),
        ("Does this person or character have a cape or cloak?", 0.22),
        ("Is this person or character bald or mostly bald?", 0.24),
        ("Does this person or character have pointed ears or non-human features?", 0.30),
    ],
    "Gender": [
        ("Is this person or character male?", 0.50),
        ("Is this person or character female?", 0.50),
        ("Is this person or character typically portrayed as male?", 0.48),
        ("Is this person or character typically portrayed as female?", 0.48),
        ("Is this person or character non-binary or gender-fluid in canon?", 0.18),
        ("Is this person or character a queen, empress, or princess?", 0.32),
        ("Is this person or character a king, emperor, or prince?", 0.32),
        ("Is this person or character commonly referred to with he/him pronouns?", 0.46),
        ("Is this person or character commonly referred to with she/her pronouns?", 0.46),
        ("Is this person or character a mother or maternal figure?", 0.30),
        ("Is this person or character a father or paternal figure?", 0.30),
        ("Is this person or character a sibling in their main story?", 0.28),
        ("Is this person or character married or in a long-term partnership?", 0.26),
        ("Is this person or character single in their most famous portrayal?", 0.24),
        ("Is this person or character a widow or widower?", 0.18),
        ("Is this person or character depicted as androgynous?", 0.20),
        ("Is this person or character a goddess or female deity?", 0.28),
        ("Is this person or character a god or male deity?", 0.28),
    ],
    "Age": [
        ("Is this person or character elderly (roughly 60+)?", 0.32),
        ("Is this person or character middle-aged (roughly 35–59)?", 0.30),
        ("Is this person or character a young adult (roughly 18–34)?", 0.32),
        ("Was this person born before 1950?", 0.38),
        ("Was this person born after 1980?", 0.36),
        ("Was this person born in the 1990s?", 0.28),
        ("Was this person born in the 2000s?", 0.22),
        ("Is this person or character ageless or immortal?", 0.26),
        ("Is this person or character depicted as an infant or toddler?", 0.18),
        ("Did this person die young (before age 40)?", 0.24),
        ("Did this person live past age 80?", 0.26),
        ("Is this person or character a student in their main story?", 0.30),
        ("Is this person or character retired in real life or in canon?", 0.22),
        ("Is this person or character centuries or millennia old?", 0.24),
        ("Is this person or character an adult in their main story?", 0.34),
        ("Is this person or character still active in their career today?", 0.36),
    ],
    "Nationality": [
        ("Is this person or character from Africa?", 0.28),
        ("Is this person or character from Australia or Oceania?", 0.20),
        ("Is this person or character from the Middle East?", 0.24),
        ("Is this person or character from the United States?", 0.38),
        ("Is this person or character from the United Kingdom?", 0.34),
        ("Is this person or character from Japan?", 0.32),
        ("Is this person or character from China?", 0.30),
        ("Is this person or character from India?", 0.30),
        ("Is this person or character from France?", 0.28),
        ("Is this person or character from Germany?", 0.28),
        ("Is this person or character from Brazil?", 0.26),
        ("Is this person or character from Canada?", 0.26),
        ("Is this person or character from Italy?", 0.26),
        ("Is this person or character from Spain?", 0.24),
        ("Is this person or character from Mexico?", 0.24),
        ("Is this person or character from South Korea?", 0.24),
        ("Is this person or character from Russia?", 0.26),
        ("Is this person or character from Scandinavia (Denmark, Norway, Sweden, etc.)?", 0.22),
    ],
    "Profession": [
        ("Is this person a doctor or medical professional?", 0.32),
        ("Is this person a lawyer or judge?", 0.28),
        ("Is this person a teacher or professor?", 0.30),
        ("Is this person an actor or actress?", 0.36),
        ("Is this person a chef or restaurateur?", 0.22),
        ("Is this person a journalist or news anchor?", 0.26),
        ("Is this person a military officer or soldier?", 0.30),
        ("Is this person a police officer or detective?", 0.28),
        ("Is this person a pilot or astronaut?", 0.24),
        ("Is this person an artist or painter?", 0.26),
        ("Is this person a fashion model?", 0.22),
        ("Is this person a comedian or stand-up performer?", 0.26),
        ("Is this person a religious leader or clergy member?", 0.24),
        ("Is this person a farmer or agricultural worker?", 0.18),
        ("Is this person an architect or engineer?", 0.26),
        ("Is this person a spy or secret agent?", 0.24),
        ("Is this person a royalty or nobility figure?", 0.28),
        ("Is this person a pirate or outlaw?", 0.22),
    ],
    "Sports": [
        ("Is this person known for soccer (football)?", 0.38),
        ("Is this person known for basketball?", 0.36),
        ("Is this person known for tennis?", 0.32),
        ("Is this person known for American football?", 0.30),
        ("Is this person known for baseball?", 0.30),
        ("Is this person known for golf?", 0.28),
        ("Is this person known for boxing or combat sports?", 0.30),
        ("Is this person known for cricket?", 0.28),
        ("Is this person known for hockey (ice or field)?", 0.26),
        ("Is this person known for swimming or aquatic sports?", 0.26),
        ("Is this person known for track and field or athletics?", 0.28),
        ("Is this person known for gymnastics?", 0.24),
        ("Is this person known for motorsport or racing?", 0.26),
        ("Is this person an Olympic medalist?", 0.34),
        ("Is this person a world-record holder in their sport?", 0.30),
        ("Is this person a coach or manager rather than a player?", 0.22),
        ("Is this person known for martial arts?", 0.26),
        ("Is this person known for skiing or winter sports?", 0.22),
    ],
    "Movies": [
        ("Is this character from a superhero film?", 0.42),
        ("Is this character from a horror movie?", 0.32),
        ("Is this character from a romantic comedy?", 0.28),
        ("Is this character from an action or blockbuster franchise?", 0.38),
        ("Is this character from a Disney or Pixar animated film?", 0.34),
        ("Is this character from a science-fiction film?", 0.36),
        ("Is this character from a fantasy film?", 0.34),
        ("Is this character from a war or historical drama film?", 0.30),
        ("Is this character from a spy or thriller film?", 0.32),
        ("Is this person a film director?", 0.28),
        ("Is this person a famous Hollywood actor?", 0.36),
        ("Is this character from a movie based on a book?", 0.32),
        ("Is this character from a movie series with multiple sequels?", 0.34),
        ("Is this character from a classic black-and-white era film?", 0.22),
        ("Is this character from a martial-arts film?", 0.26),
        ("Is this character from a Western film?", 0.22),
        ("Is this character from a musical film?", 0.24),
        ("Is this character from a Studio Ghibli film?", 0.28),
    ],
    "TV": [
        ("Is this character from a sitcom?", 0.34),
        ("Is this character from a crime or detective series?", 0.32),
        ("Is this character from a medical or hospital drama?", 0.28),
        ("Is this character from a fantasy or period TV drama?", 0.32),
        ("Is this character from a reality TV show?", 0.26),
        ("Is this character from a late-night or talk show?", 0.22),
        ("Is this character from a streaming-service original series?", 0.34),
        ("Is this character from a long-running soap opera?", 0.22),
        ("Is this character from a science-fiction TV series?", 0.34),
        ("Is this character from a children's TV program?", 0.30),
        ("Is this character from a game show?", 0.20),
        ("Is this character from a news or documentary program?", 0.22),
        ("Is this character from a British TV series?", 0.28),
        ("Is this character from an anthology or limited series?", 0.24),
        ("Is this character from a superhero TV show?", 0.30),
        ("Is this character from a cooking or lifestyle show?", 0.20),
        ("Is this character from a police procedural?", 0.30),
        ("Is this character from a teen or high-school drama?", 0.28),
    ],
    "Anime": [
        ("Is this character from a shonen action anime?", 0.38),
        ("Is this character from a shojo romance anime?", 0.28),
        ("Is this character from a mecha anime?", 0.30),
        ("Is this character from an isekai (other-world) anime?", 0.32),
        ("Does this character have superpowers or special abilities?", 0.36),
        ("Is this character a ninja or samurai?", 0.28),
        ("Is this character from a sports anime?", 0.26),
        ("Is this character from a slice-of-life anime?", 0.24),
        ("Is this character from a magical-girl anime?", 0.26),
        ("Is this character from a horror or psychological anime?", 0.24),
        ("Is this character from a Studio Ghibli anime?", 0.26),
        ("Is this character from a long-running anime franchise?", 0.34),
        ("Does this character transform or have multiple forms?", 0.28),
        ("Is this character from a seinen or mature anime?", 0.26),
        ("Is this character a student at a school in their anime?", 0.30),
        ("Is this character from a One Piece–style adventure anime?", 0.28),
        ("Is this character from a Dragon Ball–style battle anime?", 0.28),
        ("Does this character use a signature weapon or technique?", 0.30),
    ],
    "Cartoons": [
        ("Is this character from a classic Looney Tunes–style cartoon?", 0.28),
        ("Is this character from a Nickelodeon cartoon?", 0.30),
        ("Is this character from a Cartoon Network series?", 0.30),
        ("Is this character an anthropomorphic animal?", 0.34),
        ("Is this character from a Saturday-morning cartoon era show?", 0.26),
        ("Is this character from a Disney animated TV series?", 0.28),
        ("Is this character from an adult animated comedy?", 0.30),
        ("Is this character from a stop-motion animated series?", 0.20),
        ("Is this character a sidekick or comic-relief figure?", 0.28),
        ("Is this character from a preschool or early-education cartoon?", 0.24),
        ("Is this character from a superhero cartoon?", 0.28),
        ("Is this character from a Hanna-Barbera production?", 0.22),
        ("Is this character from a DreamWorks animated series?", 0.24),
        ("Is this character known for catchphrases or silly humor?", 0.26),
        ("Is this character from a web cartoon or online animation?", 0.22),
        ("Is this character from an anime-influenced Western cartoon?", 0.26),
        ("Is this character a villain in a cartoon?", 0.30),
        ("Is this character from a family-friendly adventure cartoon?", 0.28),
    ],
    "Gaming": [
        ("Is this character from a Nintendo franchise?", 0.38),
        ("Is this character from a first-person shooter game?", 0.32),
        ("Is this character from a role-playing game (RPG)?", 0.36),
        ("Is this character from a fighting game?", 0.32),
        ("Is this character from a platformer game?", 0.34),
        ("Is this character from a survival or horror game?", 0.30),
        ("Is this character from a multiplayer online game?", 0.32),
        ("Is this character from a mobile game?", 0.26),
        ("Is this character from a PlayStation exclusive?", 0.28),
        ("Is this character from an Xbox exclusive?", 0.26),
        ("Is this character from a PC gaming franchise?", 0.30),
        ("Is this character a playable protagonist?", 0.34),
        ("Is this character from an open-world game?", 0.32),
        ("Is this character from a retro arcade game?", 0.28),
        ("Is this character from a sports video game?", 0.26),
        ("Is this character from a strategy or simulation game?", 0.24),
        ("Is this character from a battle royale game?", 0.26),
        ("Is this character from an indie game?", 0.24),
    ],
    "Science": [
        ("Is this person a physicist?", 0.32),
        ("Is this person a biologist or life scientist?", 0.30),
        ("Is this person a chemist?", 0.28),
        ("Is this person a mathematician?", 0.28),
        ("Is this person known for medical or health research?", 0.30),
        ("Is this person a Nobel Prize winner in science?", 0.34),
        ("Is this person associated with evolution or natural history?", 0.28),
        ("Is this person associated with quantum physics?", 0.26),
        ("Is this person associated with computer science?", 0.32),
        ("Is this person a famous astronomer?", 0.28),
        ("Is this person known for environmental or climate science?", 0.26),
        ("Is this person associated with genetics or DNA research?", 0.28),
        ("Is this person a science communicator or popularizer?", 0.30),
        ("Is this person associated with nuclear or atomic research?", 0.26),
        ("Is this person associated with robotics or AI research?", 0.28),
        ("Is this person associated with paleontology or dinosaurs?", 0.24),
        ("Is this person associated with neuroscience?", 0.24),
        ("Is this character a fictional scientist?", 0.30),
    ],
    "History": [
        ("Is this person from ancient Greece or Rome?", 0.32),
        ("Is this person from ancient Egypt?", 0.28),
        ("Is this person from medieval Europe?", 0.30),
        ("Is this person from the Renaissance era?", 0.28),
        ("Is this person from the 18th century?", 0.26),
        ("Is this person from the 19th century?", 0.30),
        ("Is this person a monarch or royal ruler?", 0.34),
        ("Is this person a revolutionary or rebel leader?", 0.30),
        ("Is this person an explorer or navigator?", 0.28),
        ("Is this person associated with World War I?", 0.26),
        ("Is this person associated with World War II?", 0.32),
        ("Is this person associated with the American Civil War?", 0.24),
        ("Is this person associated with colonialism or empire-building?", 0.26),
        ("Is this person a philosopher from antiquity?", 0.28),
        ("Is this person associated with the Cold War era?", 0.26),
        ("Is this person associated with civil-rights or liberation movements?", 0.28),
        ("Is this person from ancient China or East Asia?", 0.28),
        ("Is this person from the Viking or Norse era?", 0.22),
    ],
    "Politics": [
        ("Is this person a current or former head of state?", 0.38),
        ("Is this person a U.S. president?", 0.34),
        ("Is this person a prime minister?", 0.32),
        ("Is this person a dictator or authoritarian ruler?", 0.28),
        ("Is this person a diplomat or ambassador?", 0.24),
        ("Is this person a member of a royal family?", 0.28),
        ("Is this person associated with the United Nations?", 0.22),
        ("Is this person a civil-rights activist?", 0.28),
        ("Is this person a feminist or women's-rights advocate?", 0.24),
        ("Is this person associated with socialism or communism?", 0.26),
        ("Is this person associated with conservatism or the right wing?", 0.26),
        ("Is this person associated with liberalism or the left wing?", 0.26),
        ("Is this person a senator or parliament member?", 0.28),
        ("Is this person a governor or regional leader?", 0.26),
        ("Is this person known for a famous speech?", 0.28),
        ("Is this person associated with independence movements?", 0.26),
        ("Is this person a Nobel Peace Prize laureate?", 0.28),
        ("Is this person still actively involved in politics?", 0.30),
    ],
    "Music": [
        ("Is this person a pop musician?", 0.36),
        ("Is this person a rock musician?", 0.34),
        ("Is this person a hip-hop or rap artist?", 0.32),
        ("Is this person a classical composer?", 0.30),
        ("Is this person a country musician?", 0.26),
        ("Is this person a jazz musician?", 0.26),
        ("Is this person a K-pop artist?", 0.28),
        ("Is this person a singer-songwriter?", 0.32),
        ("Is this person a member of a famous band or group?", 0.34),
        ("Is this person a solo artist?", 0.32),
        ("Is this person a Grammy Award winner?", 0.32),
        ("Is this person known for playing the guitar?", 0.30),
        ("Is this person known for playing the piano or keyboard?", 0.28),
        ("Is this person known for playing the drums?", 0.24),
        ("Is this person known for playing the violin or strings?", 0.24),
        ("Is this person an opera singer?", 0.22),
        ("Is this person a DJ or electronic music producer?", 0.26),
        ("Is this person known for a famous music video?", 0.28),
    ],
    "Literature": [
        ("Is this person a novelist?", 0.32),
        ("Is this person a poet?", 0.28),
        ("Is this person a playwright?", 0.26),
        ("Is this character from a fantasy novel?", 0.34),
        ("Is this character from a mystery or detective novel?", 0.30),
        ("Is this character from a science-fiction novel?", 0.32),
        ("Is this character from a children's book?", 0.30),
        ("Is this character from a classic 19th-century novel?", 0.28),
        ("Is this character from a Shakespeare play?", 0.28),
        ("Is this person a Nobel Prize winner in literature?", 0.26),
        ("Is this character from a young-adult (YA) novel?", 0.28),
        ("Is this character from a comic book or graphic novel?", 0.30),
        ("Is this character a detective or investigator in literature?", 0.28),
        ("Is this character from a dystopian novel?", 0.26),
        ("Is this character from a romance novel?", 0.24),
        ("Is this character from a horror novel?", 0.24),
        ("Is this person a journalist or essayist?", 0.24),
        ("Is this character from a series with multiple books?", 0.32),
    ],
    "Mythology": [
        ("Is this figure from Greek mythology?", 0.38),
        ("Is this figure from Norse mythology?", 0.34),
        ("Is this figure from Egyptian mythology?", 0.32),
        ("Is this figure from Hindu mythology?", 0.30),
        ("Is this figure from Japanese mythology?", 0.28),
        ("Is this figure from Roman mythology?", 0.30),
        ("Is this figure a god or goddess?", 0.36),
        ("Is this figure a hero or demigod?", 0.34),
        ("Is this figure a monster or creature?", 0.30),
        ("Is this figure associated with the underworld?", 0.26),
        ("Is this figure associated with the sea or oceans?", 0.26),
        ("Is this figure a trickster?", 0.26),
        ("Is this figure from Celtic mythology?", 0.24),
        ("Is this figure from Chinese mythology?", 0.26),
        ("Is this figure from Aztec or Mesoamerican mythology?", 0.24),
        ("Is this figure associated with creation myths?", 0.24),
        ("Is this figure associated with war or battle?", 0.28),
        ("Is this figure associated with love or beauty?", 0.24),
    ],
    "Technology": [
        ("Is this person a tech company founder or CEO?", 0.36),
        ("Is this person associated with Apple?", 0.30),
        ("Is this person associated with Microsoft?", 0.28),
        ("Is this person associated with Google or Alphabet?", 0.28),
        ("Is this person associated with Amazon?", 0.28),
        ("Is this person associated with Tesla or electric vehicles?", 0.28),
        ("Is this person associated with social media platforms?", 0.32),
        ("Is this person a software developer or programmer?", 0.30),
        ("Is this person associated with artificial intelligence?", 0.30),
        ("Is this person associated with space exploration companies?", 0.28),
        ("Is this person a venture capitalist or investor?", 0.26),
        ("Is this person associated with cryptocurrency or blockchain?", 0.24),
        ("Is this person associated with semiconductors or hardware?", 0.24),
        ("Is this person associated with open-source software?", 0.24),
        ("Is this person a billionaire?", 0.30),
        ("Is this person associated with gaming companies?", 0.26),
        ("Is this person associated with e-commerce?", 0.26),
        ("Is this person known for a famous product launch or keynote?", 0.28),
    ],
    "Relationships": [
        ("Is this person or character part of a famous duo?", 0.30),
        ("Is this person or character part of a famous trio?", 0.26),
        ("Is this person or character a leader of a group or organization?", 0.32),
        ("Is this person or character a sidekick to someone more famous?", 0.26),
        ("Is this person or character part of a royal family?", 0.28),
        ("Is this person or character part of a band or musical group?", 0.30),
        ("Is this person or character part of a sports team?", 0.32),
        ("Is this person or character part of a superhero team?", 0.30),
        ("Is this person or character a mentor to others?", 0.28),
        ("Is this person or character a rival to another famous figure?", 0.26),
        ("Is this person or character married to another famous person?", 0.24),
        ("Is this person or character siblings with another famous figure?", 0.22),
        ("Is this person or character part of a fictional guild or clan?", 0.24),
        ("Is this person or character an only child?", 0.20),
        ("Is this person or character an orphan in their story?", 0.24),
        ("Is this person or character part of a famous fictional family?", 0.28),
        ("Is this person or character a founding member of an organization?", 0.26),
        ("Is this person or character known for a famous friendship?", 0.26),
    ],
    "Awards": [
        ("Has this person won an Oscar or Academy Award?", 0.30),
        ("Has this person won a Grammy Award?", 0.28),
        ("Has this person won an Emmy Award?", 0.26),
        ("Has this person won a Nobel Prize?", 0.28),
        ("Has this person won an Olympic gold medal?", 0.30),
        ("Has this person won a Pulitzer Prize?", 0.24),
        ("Has this person won a Tony Award?", 0.22),
        ("Has this person won a Golden Globe?", 0.24),
        ("Has this person been knighted or received a royal honor?", 0.24),
        ("Has this person been inducted into a hall of fame?", 0.26),
        ("Has this person won a Booker Prize or major literary award?", 0.22),
        ("Has this person won a Ballon d'Or or major soccer award?", 0.24),
        ("Has this person won a MVP award in their sport?", 0.26),
        ("Has this person received a Presidential Medal or national honor?", 0.22),
        ("Has this person won a Cannes or major film festival award?", 0.22),
        ("Has this person won multiple Grammy Awards?", 0.26),
        ("Has this person won a Turing Award or major tech honor?", 0.20),
        ("Is this person a record-holder recognized by Guinness World Records?", 0.24),
    ],
    "Personality": [
        ("Is this person known for being humorous or comedic?", 0.28),
        ("Is this person known for being serious or stoic?", 0.26),
        ("Is this person known for being controversial?", 0.28),
        ("Is this person known for philanthropy or charity work?", 0.26),
        ("Is this person known for being outspoken or blunt?", 0.26),
        ("Is this person known for being shy or private?", 0.24),
        ("Is this person known for being charismatic or charming?", 0.28),
        ("Is this person known for being rebellious?", 0.26),
        ("Is this person known for being wise or philosophical?", 0.26),
        ("Is this person known for being eccentric or quirky?", 0.26),
        ("Is this person known for being arrogant or confident?", 0.26),
        ("Is this person known for being kind or compassionate?", 0.26),
        ("Is this person known for being ruthless or aggressive?", 0.26),
        ("Is this person known for being introverted?", 0.22),
        ("Is this person known for being extroverted?", 0.24),
        ("Is this person known for a famous quote or catchphrase?", 0.28),
        ("Is this person widely considered a role model?", 0.26),
        ("Is this person known for overcoming adversity?", 0.28),
    ],
    "Fictional traits": [
        ("Does this character have superhuman strength?", 0.30),
        ("Can this character fly or levitate?", 0.28),
        ("Does this character use magic?", 0.32),
        ("Does this character wield a sword?", 0.28),
        ("Does this character use guns or firearms?", 0.26),
        ("Is this character an alien or extraterrestrial?", 0.28),
        ("Is this character a robot, android, or AI?", 0.26),
        ("Is this character undead (vampire, zombie, ghost, etc.)?", 0.26),
        ("Is this character a shapeshifter?", 0.24),
        ("Is this character royalty in their fictional world?", 0.28),
        ("Is this character an antihero?", 0.28),
        ("Does this character have a secret identity?", 0.30),
        ("Is this character immortal or very long-lived?", 0.26),
        ("Does this character have a tragic backstory?", 0.26),
        ("Is this character from a dystopian or post-apocalyptic setting?", 0.26),
        ("Does this character have animal companions or pets?", 0.24),
        ("Is this character a mentor figure?", 0.26),
        ("Does this character die and return in their story?", 0.22),
    ],
    "Time period": [
        ("Is this person or character primarily associated with the 19th century?", 0.30),
        ("Is this person or character primarily associated with the 18th century?", 0.26),
        ("Is this person or character primarily associated with the 17th century or earlier?", 0.28),
        ("Is this person or character primarily associated with the 1960s?", 0.24),
        ("Is this person or character primarily associated with the 1970s?", 0.24),
        ("Is this person or character primarily associated with the 1980s?", 0.26),
        ("Is this person or character primarily associated with the 1990s?", 0.28),
        ("Is this person or character primarily associated with the 2000s?", 0.30),
        ("Is this person or character primarily associated with the 2010s?", 0.30),
        ("Is this person or character from ancient times (before 500 CE)?", 0.30),
        ("Is this person or character from the medieval period?", 0.28),
        ("Is this person or character from the Renaissance?", 0.26),
        ("Is this person or character from the Victorian era?", 0.26),
        ("Is this person or character from the Roaring Twenties?", 0.22),
        ("Is this person or character from the Great Depression era?", 0.20),
        ("Is this person or character from the Cold War period?", 0.24),
        ("Is this person or character set in the future?", 0.26),
        ("Is this person or character set in a timeless or fantasy world?", 0.28),
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
    "blonde", "brunette", "black", "red", "auburn", "silver", "white", "blue", "pink", "green",
]
_SPORTS = [
    "soccer", "basketball", "tennis", "golf", "boxing", "cricket", "swimming", "cycling",
    "skiing", "rugby", "volleyball", "wrestling", "archery", "fencing", "surfing",
]
_INSTRUMENTS = [
    "guitar", "piano", "drums", "violin", "saxophone", "trumpet", "flute", "cello",
    "bass guitar", "harmonica", "ukulele", "synthesizer", "harp", "banjo", "clarinet",
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
    "a power-up transformation", "a rival character", "a mentor figure", "a catchphrase attack",
    "a school uniform", "a tragic past", "a comedic sidekick", "a love triangle",
    "a tournament arc", "a beach episode", "a filler arc", "a time skip",
]
_GAME_GENRES = [
    "action-adventure", "role-playing", "first-person shooter", "platform", "puzzle",
    "racing", "fighting", "survival horror", "sandbox", "stealth", "battle royale",
    "visual novel", "rhythm", "tower defense", "metroidvania",
]
_AWARD_TYPES = [
    "Oscar", "Grammy", "Emmy", "Tony", "Nobel Prize", "Pulitzer", "Golden Globe",
    "Olympic gold medal", "Ballon d'Or", "MVP", "Cannes Palme d'Or", "Booker Prize",
    "MTV Video Music Award", "Brit Award", "Academy of Country Music Award",
]
_TV_GENRES = [
    "sitcom", "crime drama", "medical drama", "reality", "talk show", "documentary",
    "soap opera", "anthology", "miniseries", "late-night", "news", "game show",
]
_MOVIE_GENRES = [
    "horror", "comedy", "romance", "action", "thriller", "war", "western", "musical",
    "documentary", "noir", "biographical", "animated", "superhero", "disaster",
]
_SCIENCE_FIELDS = [
    "physics", "chemistry", "biology", "astronomy", "geology", "psychology",
    "ecology", "paleontology", "neuroscience", "genetics", "meteorology", "oceanography",
]
_HISTORICAL_ERA = [
    "Ancient Rome", "Ancient Greece", "Ancient Egypt", "the Middle Ages", "the Renaissance",
    "the Industrial Revolution", "World War I", "World War II", "the Cold War",
    "the American Revolution", "the French Revolution", "the Viking Age",
]
_TECH_COMPANIES = [
    "Apple", "Microsoft", "Google", "Amazon", "Meta", "Tesla", "IBM", "Intel",
    "Samsung", "Sony", "Netflix", "Spotify", "Adobe", "Oracle", "Nvidia",
]
_PERSONALITY_TRAITS = [
    "optimistic", "pessimistic", "ambitious", "lazy", "loyal", "betrayal-prone",
    "patient", "impulsive", "creative", "analytical", "empathetic", "cold",
]
_FICTIONAL_POWERS = [
    "telepathy", "telekinesis", "invisibility", "time travel", "healing", "fire manipulation",
    "ice manipulation", "lightning powers", "super speed", "super intelligence",
]


def _template_questions() -> list[tuple[str, str, float]]:
    """Generate additional questions from templates."""
    out: list[tuple[str, str, float]] = []

    for color in _HAIR_COLORS:
        out.append(
            (f"Does this person or character have {color} hair?", "Physical appearance", 0.20)
        )

    for sport in _SPORTS:
        out.append((f"Is this person famous for {sport}?", "Sports", 0.28))

    for inst in _INSTRUMENTS:
        out.append((f"Is this person known for playing the {inst}?", "Music", 0.22))

    for myth in _MYTHOLOGIES:
        out.append((f"Is this figure from {myth} mythology?", "Mythology", 0.26))

    for country in _COUNTRIES:
        out.append((f"Is this person from {country}?", "Nationality", 0.24))

    for prof in _PROFESSIONS:
        out.append((f"Is this person a {prof}?", "Profession", 0.24))

    for trope in _ANIME_TROPES:
        out.append((f"Does this anime character have {trope}?", "Anime", 0.20))

    for genre in _GAME_GENRES:
        out.append((f"Is this character from a {genre} game?", "Gaming", 0.24))

    for award in _AWARD_TYPES:
        out.append((f"Has this person won a {award}?", "Awards", 0.22))

    for genre in _TV_GENRES:
        out.append((f"Is this character from a {genre} TV show?", "TV", 0.24))

    for genre in _MOVIE_GENRES:
        out.append((f"Is this character from a {genre} movie?", "Movies", 0.24))

    for field in _SCIENCE_FIELDS:
        out.append((f"Is this person associated with {field}?", "Science", 0.22))

    for era in _HISTORICAL_ERA:
        out.append((f"Is this person associated with {era}?", "History", 0.24))

    for company in _TECH_COMPANIES:
        out.append((f"Is this person associated with {company}?", "Technology", 0.22))

    for trait in _PERSONALITY_TRAITS:
        out.append((f"Is this person known for being {trait}?", "Personality", 0.20))

    for power in _FICTIONAL_POWERS:
        out.append((f"Does this character have {power}?", "Fictional traits", 0.22))

    # Gender expansions
    for role in ["warrior", "wizard", "princess", "knight", "assassin", "healer"]:
        out.append((f"Is this character a {role}?", "Gender", 0.22))

    # Age decade templates
    for decade in ["1920s", "1930s", "1940s", "1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s"]:
        out.append(
            (f"Was this person born in the {decade}?", "Age", 0.22)
        )

    # Relationship templates
    for rel in ["best friend", "mentor", "rival", "love interest", "parent", "sibling", "partner"]:
        out.append(
            (f"Is this character known for a famous {rel} relationship?", "Relationships", 0.20)
        )

    # Cartoon network/style
    for studio in ["Disney", "Pixar", "DreamWorks", "Nickelodeon", "Cartoon Network", "Adult Swim"]:
        out.append((f"Is this character from a {studio} production?", "Cartoons", 0.24))

    # Politics office
    for office in ["president", "prime minister", "senator", "governor", "mayor", "monarch"]:
        out.append((f"Is this person a {office}?", "Politics", 0.26))

    # Literature genre
    for lit in ["mystery", "romance", "horror", "fantasy", "sci-fi", "historical fiction", "satire"]:
        out.append((f"Is this character from a {lit} book?", "Literature", 0.22))

    # Time period century
    for century in ["16th", "17th", "18th", "19th", "20th", "21st"]:
        out.append(
            (f"Is this person or character primarily from the {century} century?", "Time period", 0.26)
        )

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
