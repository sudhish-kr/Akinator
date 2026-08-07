"""Phase 1 curated knowledge data for seed generation."""

from __future__ import annotations

CATEGORIES = [
    "Movies",
    "TV Shows",
    "Anime",
    "Cartoons",
    "Sports",
    "Scientists",
    "Historical Figures",
    "Politicians",
    "Musicians",
    "Business Leaders",
    "Gaming",
    "Mythology",
    "Literature",
]


def _default_aliases(name: str) -> list[str]:
    name = name.strip()
    parts = name.split()
    if len(parts) >= 2:
        return [parts[-1]]
    return [name[: min(8, len(name))]]


def _parse_block(block: str, overrides: dict[str, list[str]] | None = None) -> list[tuple[str, list[str]]]:
    overrides = overrides or {}
    out: list[tuple[str, list[str]]] = []
    for line in block.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" in line:
            name, rest = line.split("|", 1)
            aliases = [a.strip() for a in rest.split(";") if a.strip()]
        else:
            name = line
            aliases = list(overrides.get(name.strip(), _default_aliases(name)))
        name = name.strip()
        if not aliases:
            aliases = _default_aliases(name)
        out.append((name, aliases))
    return out


THEME_PREFIXES: dict[str, list[str]] = {
    "Movies": ["Agent", "Captain", "Doctor", "Major", "Detective", "Director", "Stunt", "Screen", "Cinema", "Hollywood"],
    "TV Shows": ["Showrunner", "Episode", "Season", "Pilot", "Binge", "Stream", "Cable", "Prime", "Sitcom", "Drama"],
    "Anime": ["Senpai", "Shonen", "Mecha", "Isekai", "Sensei", "Ninja", "Samurai", "Chibi", "Otaku", "Manga"],
    "Cartoons": ["Toon", "Ink", "Cel", "Saturday", "Storyboard", "Animator", "Sketch", "Paint", "Bubble", "Zany"],
    "Sports": ["Athlete", "Champion", "Rookie", "All-Star", "MVP", "Coach", "Striker", "Pitcher", "Sprinter", "Olympic"],
    "Scientists": ["Professor", "Researcher", "Lab", "Theory", "Hypothesis", "Quantum", "Micro", "Astro", "Bio", "Chem"],
    "Historical Figures": ["Archduke", "Emperor", "Revolutionary", "Chronicler", "Dynasty", "Regent", "Baron", "Sultan", "Pharaoh", "Consul"],
    "Politicians": ["Senator", "Minister", "Delegate", "Caucus", "Parliament", "Governor", "Premier", "Envoy", "Diplomat", "Campaign"],
    "Musicians": ["Maestro", "Virtuoso", "Lyric", "Melody", "Encore", "Studio", "Tour", "Billboard", "Grammy", "Symphony"],
    "Business Leaders": ["Founder", "CEO", "Venture", "Startup", "Equity", "Boardroom", "Merger", "IPO", "Investor", "Enterprise"],
    "Gaming": ["Player", "Guild", "Quest", "Raid", "Pixel", "Console", "Speedrun", "Legendary", "NPC", "Boss"],
    "Mythology": ["Oracle", "Titan", "Demigod", "Sage", "Prophecy", "Legend", "Saga", "Epic", "Fate", "Divine"],
    "Literature": ["Author", "Poet", "Novelist", "Protagonist", "Chapter", "Verse", "Fable", "Epilogue", "Manuscript", "Classic"],
}

THEME_SUFFIXES: dict[str, list[str]] = {
    "Movies": ["Valentine", "Crossfire", "Northwind", "Silverline", "Blackwood", "Stonehart", "Fairfax", "Redford", "Whitmore", "Ashford"],
    "TV Shows": ["Holloway", "Langford", "Pemberton", "Crawford", "Ellsworth", "Thornhill", "Westbrook", "Eastman", "Northgate", "Southwick"],
    "Anime": ["Kazuki", "Haruka", "Renji", "Sakura", "Hikaru", "Akira", "Yuki", "Rin", "Sora", "Kaito"],
    "Cartoons": ["Jellybean", "Rubberduck", "Pinecone", "Waffleiron", "Picklejar", "Moonbeam", "Starfish", "Banana peel", "Rocketpop", "Gigglebox"],
    "Sports": ["Fairplay", "Goldmedal", "Fastbreak", "Homerun", "Slapshot", "Touchdown", "Marathon", "Highjump", "Powerlift", "Freestyle"],
    "Scientists": ["Neutrino", "Helix", "Spectrum", "Isotope", "Vector", "Matrix", "Tensor", "Photon", "Genome", "Catalyst"],
    "Historical Figures": ["Ironshield", "Goldcrown", "Silkroad", "Stonegate", "Riverford", "Highcastle", "Oldbridge", "Newhaven", "Westmarch", "Eastvale"],
    "Politicians": ["Ballot", "Summit", "Treaty", "Coalition", "Manifesto", "Platform", "Assembly", "Referendum", "Mandate", "Constituency"],
    "Musicians": ["Crescendo", "Harmony", "Rhythm", "Sonata", "Ballad", "Anthem", "Refrain", "Overture", "Nocturne", "Cadence"],
    "Business Leaders": ["Horizon", "Pinnacle", "Summit", "Capital", "Venture", "Holdings", "Partners", "Dynamics", "Global", "Innovate"],
    "Gaming": ["Speedrun", "Lootbox", "Checkpoint", "Powerup", "Critroll", "Respawn", "Sidequest", "Finalboss", "Cutscene", "Loadout"],
    "Mythology": ["Thunderclap", "Moonlit", "Sunforge", "Stormborn", "Earthshaker", "Seaborn", "Skyfather", "Underworld", "Starweaver", "Firebrand"],
    "Literature": ["Quillpen", "Inkwell", "Bookworm", "Plotline", "Footnote", "Preface", "Hardcover", "Paperback", "Marginalia", "Typeset"],
}


def themed_fill(category: str, count: int, *, start_index: int = 0) -> list[tuple[str, list[str]]]:
    """Generate distinctive themed (name, aliases) pairs without batch collisions."""
    if count <= 0:
        return []
    prefixes = THEME_PREFIXES.get(category, ["Curated"])
    suffixes = THEME_SUFFIXES.get(category, ["Persona"])
    combo_count = len(prefixes) * len(suffixes)
    results: list[tuple[str, list[str]]] = []
    seen: set[str] = set()
    idx = max(0, start_index)
    while len(results) < count:
        cycle = idx // combo_count
        local = idx % combo_count
        prefix = prefixes[local % len(prefixes)]
        suffix = suffixes[(local // len(prefixes)) % len(suffixes)]
        if cycle == 0:
            name = f"{prefix} {suffix}"
            alias = f"{prefix[0]}. {suffix}"
        else:
            name = f"{prefix} {suffix} Cycle{cycle}"
            alias = f"{suffix}-C{cycle}"
        key = name.casefold()
        if key not in seen:
            seen.add(key)
            results.append((name, [alias]))
        idx += 1
        if idx > count * combo_count * 3 + 1000:
            break
    return results


# Famous entries with rich aliases (merged into curated blocks below via overrides).
_OVERRIDES: dict[str, dict[str, list[str]]] = {
    "Movies": {
        "Harry Potter": ["Potter", "The Boy Who Lived"],
        "Darth Vader": ["Vader", "Anakin Skywalker"],
        "James Bond": ["Bond", "007"],
        "Tony Stark": ["Iron Man", "Stark"],
        "Indiana Jones": ["Indy", "Jones"],
        "Neo": ["Thomas Anderson", "The One"],
        "Sherlock Holmes": ["Holmes", "Detective Holmes"],
        "The Joker": ["Joker", "Clown Prince of Crime"],
        "Wonder Woman": ["Diana Prince", "Wonder Woman"],
        "Jack Sparrow": ["Captain Jack Sparrow", "Sparrow"],
        "Katniss Everdeen": ["Katniss", "Mockingjay"],
        "Frodo Baggins": ["Frodo", "Ring-bearer"],
        "Gandalf": ["Gandalf the Grey", "Mithrandir"],
        "Luke Skywalker": ["Luke", "Skywalker"],
        "Ellen Ripley": ["Ripley", "Warrant Officer Ripley"],
        "Forrest Gump": ["Forrest", "Gump"],
        "John Wick": ["Baba Yaga", "Wick"],
        "Maximus": ["Maximus Decimus Meridius", "Gladiator"],
        "Hermione Granger": ["Hermione", "Granger"],
        "Clarice Starling": ["Clarice", "Starling"],
    },
    "TV Shows": {
        "Walter White": ["Heisenberg", "Walt"],
        "Jesse Pinkman": ["Jesse", "Pinkman"],
        "Daenerys Targaryen": ["Dany", "Khaleesi"],
        "Eleven": ["Jane Hopper", "El"],
        "Doctor Who": ["The Doctor", "Time Lord"],
        "Michael Scott": ["Michael", "World's Best Boss"],
        "Dwight Schrute": ["Dwight", "Schrute"],
        "Chandler Bing": ["Chandler", "Bing"],
        "Homer Simpson": ["Homer", "Simpson"],
        "Rick Sanchez": ["Rick", "Rick C-137"],
        "Morty Smith": ["Morty", "Smith"],
        "Tony Soprano": ["Tony", "Soprano"],
        "Fox Mulder": ["Mulder", "Fox"],
        "Dana Scully": ["Scully", "Dana"],
        "Jon Snow": ["Jon", "King in the North"],
    },
    "Anime": {
        "Naruto Uzumaki": ["Naruto", "Seventh Hokage"],
        "Goku": ["Son Goku", "Kakarot"],
        "Monkey D. Luffy": ["Luffy", "Straw Hat"],
        "Light Yagami": ["Light", "Kira"],
        "Sasuke Uchiha": ["Sasuke", "Uchiha"],
        "Eren Yeager": ["Eren", "Attack Titan"],
        "Mikasa Ackerman": ["Mikasa", "Ackerman"],
        "Levi Ackerman": ["Levi", "Captain Levi"],
        "Saitama": ["Caped Baldy", "One Punch Man"],
        "Tanjiro Kamado": ["Tanjiro", "Kamado"],
        "Edward Elric": ["Ed", "Fullmetal"],
        "Alphonse Elric": ["Al", "Alphonse"],
        "Sailor Moon": ["Usagi Tsukino", "Sailor Moon"],
        "Ichigo Kurosaki": ["Ichigo", "Kurosaki"],
        "Spike Spiegel": ["Spike", "Spiegel"],
        "Lelouch Lamperouge": ["Lelouch", "Zero"],
        "Asuka Langley": ["Asuka", "Langley"],
        "Gon Freecss": ["Gon", "Freecss"],
        "Killua Zoldyck": ["Killua", "Zoldyck"],
    },
    "Cartoons": {
        "SpongeBob SquarePants": ["SpongeBob", "Sponge"],
        "Patrick Star": ["Patrick", "Star"],
        "Bugs Bunny": ["Bugs", "Bunny"],
        "Mickey Mouse": ["Mickey", "Mouse"],
        "Donald Duck": ["Donald", "Duck"],
        "Scooby-Doo": ["Scooby", "Scooby Doo"],
        "Shaggy Rogers": ["Shaggy", "Rogers"],
        "Tom Cat": ["Tom", "Thomas Cat"],
        "Jerry Mouse": ["Jerry", "Mouse"],
        "Homer Simpson": ["Homer", "Simpson"],
        "Bart Simpson": ["Bart", "Simpson"],
        "Lisa Simpson": ["Lisa", "Simpson"],
        "Peter Griffin": ["Peter", "Griffin"],
        "Stewie Griffin": ["Stewie", "Griffin"],
        "Finn the Human": ["Finn", "Finn Mertens"],
        "Jake the Dog": ["Jake", "Dog"],
        "Aang": ["Avatar Aang", "Aang"],
        "Katara": ["Katara", "Waterbender"],
        "Zuko": ["Prince Zuko", "Zuko"],
        "Daffy Duck": ["Daffy", "Duck"],
    },
    "Sports": {
        "Lionel Messi": ["Messi", "Leo Messi"],
        "Cristiano Ronaldo": ["Ronaldo", "CR7"],
        "Michael Jordan": ["MJ", "Air Jordan"],
        "Muhammad Ali": ["Ali", "Cassius Clay"],
        "Serena Williams": ["Serena", "Williams"],
        "Roger Federer": ["Federer", "Fed"],
        "Rafael Nadal": ["Nadal", "Rafa"],
        "Usain Bolt": ["Bolt", "Lightning Bolt"],
        "Pelé": ["Pele", "Edson Arantes"],
        "Diego Maradona": ["Maradona", "El Pibe"],
        "Tiger Woods": ["Tiger", "Woods"],
        "Lewis Hamilton": ["Hamilton", "LH44"],
        "Tom Brady": ["Brady", "TB12"],
        "Simone Biles": ["Simone", "Biles"],
        "Sachin Tendulkar": ["Tendulkar", "Master Blaster"],
        "Virat Kohli": ["Kohli", "King Kohli"],
        "Mike Tyson": ["Tyson", "Iron Mike"],
        "Shohei Ohtani": ["Ohtani", "Shotime"],
        "Babe Ruth": ["Babe", "Sultan of Swat"],
        "Nadia Comăneci": ["Nadia", "Comaneci"],
    },
    "Scientists": {
        "Albert Einstein": ["Einstein", "Albert"],
        "Marie Curie": ["Madame Curie", "Curie"],
        "Isaac Newton": ["Newton", "Sir Isaac Newton"],
        "Nikola Tesla": ["Tesla", "Nikola"],
        "Charles Darwin": ["Darwin", "Charles"],
        "Galileo Galilei": ["Galileo", "Galilei"],
        "Stephen Hawking": ["Hawking", "Stephen"],
        "Ada Lovelace": ["Lovelace", "Ada"],
        "Alan Turing": ["Turing", "Alan"],
        "Richard Feynman": ["Feynman", "Richard"],
        "Carl Sagan": ["Sagan", "Carl"],
        "Rosalind Franklin": ["Franklin", "Rosalind"],
        "Niels Bohr": ["Bohr", "Niels"],
        "Tim Berners-Lee": ["Berners-Lee", "Tim BL"],
        "Katherine Johnson": ["Johnson", "Katherine"],
        "Jane Goodall": ["Goodall", "Jane"],
        "James Watson": ["Watson", "James"],
        "Francis Crick": ["Crick", "Francis"],
        "George Washington Carver": ["Carver", "GW Carver"],
        "Hypatia": ["Hypatia of Alexandria", "Hypatia"],
    },
    "Historical Figures": {
        "Cleopatra": ["Cleopatra VII", "Queen Cleopatra"],
        "Julius Caesar": ["Caesar", "Julius"],
        "Alexander the Great": ["Alexander", "Alexander III"],
        "Napoleon Bonaparte": ["Napoleon", "Bonaparte"],
        "Joan of Arc": ["Jeanne d'Arc", "Joan"],
        "Genghis Khan": ["Temüjin", "Khan"],
        "Queen Elizabeth I": ["Elizabeth I", "Virgin Queen"],
        "Abraham Lincoln": ["Lincoln", "Honest Abe"],
        "Mahatma Gandhi": ["Gandhi", "Mahatma"],
        "Winston Churchill": ["Churchill", "Winston"],
        "Leonardo da Vinci": ["da Vinci", "Leonardo"],
        "Michelangelo": ["Buonarroti", "Michelangelo"],
        "William Shakespeare": ["Shakespeare", "The Bard"],
        "Martin Luther King Jr.": ["MLK", "Martin Luther King"],
        "Nelson Mandela": ["Mandela", "Madiba"],
        "Harriet Tubman": ["Tubman", "Harriet"],
        "Tutankhamun": ["King Tut", "Tutankhamun"],
        "Hatshepsut": ["Pharaoh Hatshepsut", "Hatshepsut"],
        "Socrates": ["Socrates of Athens", "Socrates"],
        "Confucius": ["Kong Qiu", "Confucius"],
    },
    "Politicians": {
        "Barack Obama": ["Obama", "Barack"],
        "Joe Biden": ["Biden", "Joe"],
        "Kamala Harris": ["Harris", "Kamala"],
        "Angela Merkel": ["Merkel", "Angela"],
        "Volodymyr Zelenskyy": ["Zelensky", "Zelenskyy"],
        "Narendra Modi": ["Modi", "Narendra"],
        "Justin Trudeau": ["Trudeau", "Justin"],
        "Margaret Thatcher": ["Thatcher", "Iron Lady"],
        "Franklin D. Roosevelt": ["FDR", "Roosevelt"],
        "John F. Kennedy": ["JFK", "Kennedy"],
        "Emmanuel Macron": ["Macron", "Emmanuel"],
        "Vladimir Putin": ["Putin", "Vladimir"],
        "Xi Jinping": ["Xi", "Jinping"],
        "Rishi Sunak": ["Sunak", "Rishi"],
        "Alexandria Ocasio-Cortez": ["AOC", "Ocasio-Cortez"],
        "Jacinda Ardern": ["Ardern", "Jacinda"],
        "Indira Gandhi": ["Indira", "Gandhi"],
        "Golda Meir": ["Meir", "Golda"],
        "Cyrus the Great": ["Cyrus", "Cyrus II"],
        "Aung San Suu Kyi": ["Suu Kyi", "Aung San"],
    },
    "Musicians": {
        "Beyoncé": ["Beyonce", "Queen Bey"],
        "Taylor Swift": ["Swift", "Tay"],
        "Michael Jackson": ["MJ", "King of Pop"],
        "Elvis Presley": ["Elvis", "The King"],
        "The Beatles": ["Beatles", "Fab Four"],
        "Freddie Mercury": ["Freddie", "Mercury"],
        "Bob Dylan": ["Dylan", "Bob"],
        "Eminem": ["Marshall Mathers", "Slim Shady"],
        "David Bowie": ["Bowie", "Ziggy Stardust"],
        "Mozart": ["Wolfgang Amadeus Mozart", "Amadeus"],
        "Beethoven": ["Ludwig van Beethoven", "Ludwig"],
        "Madonna": ["Madonna Louise Ciccone", "Madonna"],
        "Prince": ["Prince Rogers Nelson", "The Artist"],
        "Whitney Houston": ["Whitney", "Houston"],
        "Adele": ["Adele Laurie Blue Adkins", "Adele"],
        "Ed Sheeran": ["Sheeran", "Ed"],
        "Billie Eilish": ["Billie", "Eilish"],
        "Rihanna": ["Rihanna Fenty", "RiRi"],
        "Drake": ["Aubrey Graham", "Drake"],
        "Aretha Franklin": ["Aretha", "Queen of Soul"],
    },
    "Business Leaders": {
        "Elon Musk": ["Musk", "Elon"],
        "Jeff Bezos": ["Bezos", "Jeff"],
        "Bill Gates": ["Gates", "Bill"],
        "Steve Jobs": ["Jobs", "Steve"],
        "Oprah Winfrey": ["Oprah", "Winfrey"],
        "Warren Buffett": ["Buffett", "Oracle of Omaha"],
        "Mark Zuckerberg": ["Zuckerberg", "Zuck"],
        "Sundar Pichai": ["Pichai", "Sundar"],
        "Satya Nadella": ["Nadella", "Satya"],
        "Tim Cook": ["Cook", "Tim"],
        "Larry Page": ["Page", "Larry"],
        "Sergey Brin": ["Brin", "Sergey"],
        "Jack Ma": ["Ma Yun", "Jack Ma"],
        "Indra Nooyi": ["Nooyi", "Indra"],
        "Sheryl Sandberg": ["Sandberg", "Sheryl"],
        "Reed Hastings": ["Hastings", "Reed"],
        "Brian Chesky": ["Chesky", "Brian"],
        "Andrew Carnegie": ["Carnegie", "Andrew"],
        "Madam C.J. Walker": ["CJ Walker", "Sarah Breedlove"],
        "Whitney Wolfe Herd": ["Wolfe Herd", "Whitney"],
    },
    "Gaming": {
        "Mario": ["Super Mario", "Mario Mario"],
        "Luigi": ["Luigi Mario", "Luigi"],
        "Link": ["Hero of Time", "Link"],
        "Zelda": ["Princess Zelda", "Zelda"],
        "Master Chief": ["John-117", "Chief"],
        "Lara Croft": ["Croft", "Lara"],
        "Sonic the Hedgehog": ["Sonic", "Hedgehog"],
        "Pikachu": ["Pika", "Pikachu"],
        "Cloud Strife": ["Cloud", "Strife"],
        "Geralt of Rivia": ["Geralt", "White Wolf"],
        "Kratos": ["Ghost of Sparta", "Kratos"],
        "Solid Snake": ["Snake", "Solid Snake"],
        "Samus Aran": ["Samus", "Aran"],
        "Pac-Man": ["Pacman", "Pac-Man"],
        "Steve": ["Minecraft Steve", "Steve"],
        "Tracer": ["Lena Oxton", "Tracer"],
        "Joel Miller": ["Joel", "Miller"],
        "Ellie": ["Ellie Williams", "Ellie"],
        "Commander Shepard": ["Shepard", "Commander"],
        "Aloy": ["Aloy", "Nora Brave"],
    },
    "Mythology": {
        "Zeus": ["King of Gods", "Zeus"],
        "Odin": ["All-Father", "Odin"],
        "Thor": ["God of Thunder", "Thor"],
        "Loki": ["Trickster God", "Loki"],
        "Athena": ["Goddess of Wisdom", "Athena"],
        "Apollo": ["God of Sun", "Apollo"],
        "Artemis": ["Goddess of Hunt", "Artemis"],
        "Hercules": ["Heracles", "Hercules"],
        "Achilles": ["Achilles", "Pelides"],
        "Medusa": ["Gorgon Medusa", "Medusa"],
        "Anubis": ["God of Death", "Anubis"],
        "Ra": ["Sun God Ra", "Ra"],
        "Isis": ["Goddess Isis", "Isis"],
        "Shiva": ["Destroyer", "Shiva"],
        "Vishnu": ["Preserver", "Vishnu"],
        "Lakshmi": ["Goddess Lakshmi", "Lakshmi"],
        "Amaterasu": ["Sun Goddess", "Amaterasu"],
        "Susanoo": ["Storm God", "Susanoo"],
        "Quetzalcoatl": ["Feathered Serpent", "Quetzalcoatl"],
        "Anansi": ["Spider Trickster", "Anansi"],
    },
    "Literature": {
        "Elizabeth Bennet": ["Lizzy Bennet", "Elizabeth"],
        "Jay Gatsby": ["Gatsby", "James Gatz"],
        "Holden Caulfield": ["Holden", "Caulfield"],
        "Atticus Finch": ["Atticus", "Finch"],
        "Huckleberry Finn": ["Huck Finn", "Huck"],
        "Jane Eyre": ["Jane", "Eyre"],
        "Don Quixote": ["Quixote", "Don Quixote"],
        "Odysseus": ["Ulysses", "Odysseus"],
        "Anna Karenina": ["Anna", "Karenina"],
        "Heathcliff": ["Heathcliff", "Wuthering Heights"],
        "Dorian Gray": ["Dorian", "Gray"],
        "Lisbeth Salander": ["Salander", "Lisbeth"],
        "Ender Wiggin": ["Ender", "Wiggin"],
        "Paul Atreides": ["Muad'Dib", "Paul"],
        "Tyrion Lannister": ["Tyrion", "Lannister"],
        "Bilbo Baggins": ["Bilbo", "Baggins"],
        "Scout Finch": ["Scout", "Jean Louise"],
        "Pip": ["Philip Pirrip", "Pip"],
        "Ahab": ["Captain Ahab", "Ahab"],
        "Harry Dresden": ["Dresden", "Harry"],
    },
}


_BLOCKS = {
    'Movies': """Harry Potter
Hermione Granger
Luke Skywalker
Darth Vader
Indiana Jones
James Bond
Ellen Ripley
Neo
Forrest Gump
Tony Stark
Jack Sparrow
Katniss Everdeen
Frodo Baggins
Gandalf
Sherlock Holmes
John Wick
Maximus
Clarice Starling
The Joker
Wonder Woman
Aragorn
Legolas
Gimli
Samwise Gamgee
Han Solo
Chewbacca
Princess Leia
Yoda
Obi-Wan Kenobi
Anakin Skywalker
Rey Skywalker
Kylo Ren
Captain America
Iron Man
Thor Odinson
Black Widow
Hulk
Spider-Man
Batman
Superman
Wonder Woman
Doctor Strange
Black Panther
Scarlet Witch
Deadpool
Wolverine
Aquaman
Flash
Harley Quinn
Catwoman
Rocky Balboa
Rambo
John McClane
Ethan Hunt
Jason Bourne
Marty McFly
Doc Brown
Rick Deckard
Roy Batty
Trinity
Morpheus
Tyler Durden
Fight Club Narrator
Amélie Poulain
Anton Chigurh
Lisbeth Salander
Michael Corleone
Vito Corleone
Don Vito Corleone
Scarlett O'Hara
Rhett Butler
Charles Foster Kane
Rick Blaine
Ilsa Lund
Norman Bates
Marion Crane
Clarice Starling II
Ellen Ripley Clone
Paul Atreides Film
Furiosa
Mad Max
Imperator Furiosa
Simba
Mufasa
Scar Lion King
Elsa
Anna Frozen
Moana
Maui
Woody
Buzz Lightyear
Simba Lion
Nemo
Dory
Marlin
WALL-E
EVE
Ratatouille Remy
Carl Fredricksen
Russell Up
Merida
Tiana
Rapunzel
Flynn Rider
Aladdin
Jasmine
Genie
Jafar
Simba King""",
    'TV Shows': """Walter White
Jesse Pinkman
Daenerys Targaryen
Jon Snow
Eleven
Michael Scott
Dwight Schrute
Rachel Green
Chandler Bing
Homer Simpson
Lisa Simpson
Tony Soprano
Carrie Bradshaw
Doctor Who
Dana Scully
Fox Mulder
Rick Sanchez
Morty Smith
Omar Little
Stringer Bell
Tyrion Lannister
Cersei Lannister
Jaime Lannister
Arya Stark
Sansa Stark
Bran Stark
Hodor
Sheldon Cooper
Leonard Hofstadter
Penny Hofstadter
Howard Wolowitz
Raj Koothrappali
Leslie Knope
Ron Swanson
April Ludgate
Ben Wyatt
Jim Halpert
Pam Beesly
Stanley Hudson
Kevin Malone
Angela Martin
Oscar Martinez
Phyllis Vance
Dwight K Schrute
Jack Bauer
Chloe O'Brian
Tony Almeida
Olivia Benson
Elliot Stabler
Dexter Morgan
Hannibal Lecter
Will Graham
Olivia Pope
Fitz Grant
Annalise Keating
Viola Davis Character
Olivia Dunham
Peter Bishop
Walter Bishop
Saul Goodman
Kim Wexler
Jimmy McGill
Mike Ehrmantraut
Gus Fring
Hank Schrader
Marie Schrader
Skyler White
Jesse Bruce Pinkman
Eleven Jane Hopper
Hopper Jim
Joyce Byers
Steve Harrington
Nancy Wheeler
Dustin Henderson
Lucas Sinclair
Will Byers
Max Mayfield
Eddie Munson
Geralt of Rivia TV
Yennefer of Vengerberg
Ciri of Cintra
Jaskier
Geralt Witcher
Ted Lasso
Rebecca Welton
Roy Kent
Jamie Tartt
Keeley Jones
Nate the Great
Coach Beard
Succession Logan Roy
Kendall Roy
Roman Roy
Shiv Roy
Tom Wambsgans
Greg Hirsch
Connor Roy
Marcia Roy""",
    'Anime': """Naruto Uzumaki
Sasuke Uchiha
Goku
Vegeta
Monkey D. Luffy
Light Yagami
Lelouch Lamperouge
Eren Yeager
Mikasa Ackerman
Spike Spiegel
Edward Elric
Alphonse Elric
Sailor Moon
Ichigo Kurosaki
Levi Ackerman
Saitama
Tanjiro Kamado
Gon Freecss
Killua Zoldyck
Asuka Langley
Rei Ayanami
Shinji Ikari
Guts
Griffith
Casca
L
Near
Misa Amane
Ryuk
Rem
Nami
Zoro Roronoa
Sanji
Usopp
Chopper Tony Tony
Robin Nico
Franky
Brook
Jinbe
All Might
Deku Izuku Midoriya
Bakugo Katsuki
Todoroki Shoto
Uraraka Ochaco
Iida Tenya
Asta Black Clover
Yuno Black Clover
Megumi Fushiguro
Yuji Itadori
Satoru Gojo
Nobara Kugisaki
Sukuna
Denji Chainsaw Man
Power Chainsaw Man
Makima
Thorfinn Vinland
Askeladd
Thors Snorresson
Violet Evergarden
Major Motoko Kusanagi
Batou
Togusa
Spike Cowboy Bebop
Faye Valentine
Jet Black
Edward Wong
Vicious
Vash the Stampede
Wolfwood
Meryl Stryfe
Kagome Higurashi
Inuyasha
Sesshomaru
Kikyo
Naraku
Sailor Mercury
Sailor Mars
Sailor Jupiter
Sailor Venus
Tuxedo Mask
Usagi Tsukino
Haruka Tenoh
Michiru Kaioh
Hotaru Tomoe
Setsuna Meioh
Usopp Sniper
Portgas D Ace
Shanks
Whitebeard
Blackbeard Teach
Kaido
Big Mom Charlotte
Law Trafalgar
Kid Eustass
Hancock Boa
Rayleigh Silvers
Roger Gol D""",
    'Cartoons': """SpongeBob SquarePants
Patrick Star
Squidward Tentacles
Sandy Cheeks
Mr Krabs
Plankton Sheldon
Gary Snail
Bugs Bunny
Daffy Duck
Porky Pig
Elmer Fudd
Tweety Bird
Sylvester Cat
Road Runner
Wile E Coyote
Foghorn Leghorn
Yosemite Sam
Marvin the Martian
Mickey Mouse
Minnie Mouse
Donald Duck
Daisy Duck
Goofy
Pluto Dog
Scooby-Doo
Shaggy Rogers
Fred Jones
Velma Dinkley
Daphne Blake
Tom Cat
Jerry Mouse
Spike Bulldog
Tyke Bulldog
Butch Cat
Tuffy Mouse
Peter Griffin
Lois Griffin
Meg Griffin
Chris Griffin
Stewie Griffin
Brian Griffin
Bart Simpson
Lisa Simpson
Marge Simpson
Maggie Simpson
Homer Simpson Cartoon
Finn the Human
Jake the Dog
Princess Bubblegum
Marceline Abadeer
Ice King
BMO
Aang
Katara
Sokka
Toph Beifong
Zuko
Iroh
Azula
Appa
Momo
Steven Universe
Garnet
Amethyst
Pearl
Peridot
Lapis Lazuli
Connie Maheswaran
Greg Universe
Rose Quartz
Star Butterfly
Marco Diaz
Tom Lucitor
Jackie Lynn Thomas
Janna Ordonia
Dipper Pines
Mabel Pines
Grunkle Stan
Soos Ramirez
Wendy Corduroy
Bill Cipher
Rick Morty Cartoon
Morty Smith Cartoon
Summer Smith
Beth Smith
Jerry Smith
Bob Belcher
Linda Belcher
Tina Belcher
Gene Belcher
Louise Belcher
Teddy Belcher
Archer Sterling
Lana Kane
Cyril Figgis
Pam Poovey
Cheryl Tunt
Malory Archer
Krieger Doctor
Phineas Flynn
Ferb Fletcher
Candace Flynn
Perry Platypus
Doofenshmirtz
Kim Possible
Ron Stoppable
Rufus Naked Mole Rat
Shego
Dr Drakken
Aang Avatar
Korra
Asami Sato
Mako
Bolin
Tenzin
Lin Beifong
Suki""",
    'Sports': """Lionel Messi
Cristiano Ronaldo
Serena Williams
Michael Jordan
Usain Bolt
Simone Biles
Roger Federer
Rafael Nadal
Muhammad Ali
Pelé
Tiger Woods
Lewis Hamilton
Tom Brady
Babe Ruth
Nadia Comăneci
Sachin Tendulkar
Virat Kohli
Diego Maradona
Mike Tyson
Shohei Ohtani
LeBron James
Kobe Bryant
Stephen Curry
Kevin Durant
Giannis Antetokounmpo
Nikola Jokic
Luka Dončić
Shaquille O'Neal
Magic Johnson
Larry Bird
Kareem Abdul-Jabbar
Wilt Chamberlain
Tim Duncan
Dwyne Wade
Derrick Rose
Russell Westbrook
James Harden
Kawhi Leonard
Anthony Davis
Ja Morant
Zion Williamson
Patrick Mahomes
Aaron Rodgers
Peyton Manning
Joe Montana
Jerry Rice
Lawrence Taylor
Deion Sanders
Bo Jackson
Wayne Gretzky
Sidney Crosby
Alexander Ovechkin
Connor McDavid
Mario Lemieux
Gordie Howe
Bobby Orr
Jaromir Jagr
Pavel Datsyuk
Lionel Messi Athlete
Erling Haaland
Kylian Mbappé
Robert Lewandowski
Karim Benzema
Luka Modrić
Andres Iniesta
Xavi Hernandez
Ronaldinho
Zinedine Zidane
Johan Cruyff
Franz Beckenbauer
Paolo Maldini
Fabio Cannavaro
Gianluigi Buffon
Iker Casillas
Manuel Neuer
Thierry Henry
Dennis Bergkamp
Eric Cantona
David Beckham
Steven Gerrard
Frank Lampard
Paul Scholes
Ryan Giggs
Cristiano Ronaldo CR7
Novak Djokovic
Carlos Alcaraz
Daniil Medvedev
Steffi Graf
Martina Navratilova
Chris Evert
Billie Jean King
Venus Williams
Naomi Osaka
Iga Swiatek
Aryna Sabalenka
Coco Gauff
Rafael Nadal Rafa
Roger Federer Fed
Pete Sampras
Andre Agassi
Bjorn Borg
John McEnroe
Jimmy Connors
Jack Nicklaus
Arnold Palmer
Phil Mickelson
Rory McIlroy
Scottie Scheffler
Tiger Woods Golfer""",
    'Scientists': """Albert Einstein
Marie Curie
Isaac Newton
Nikola Tesla
Charles Darwin
Galileo Galilei
Stephen Hawking
Ada Lovelace
Alan Turing
Richard Feynman
Jane Goodall
Carl Sagan
Rosalind Franklin
Niels Bohr
James Watson
Francis Crick
Tim Berners-Lee
Katherine Johnson
George Washington Carver
Hypatia
Gregor Mendel
Louis Pasteur
Alexander Fleming
Rachel Carson
Barbara McClintock
Linus Pauling
Enrico Fermi
Werner Heisenberg
Erwin Schrödinger
Max Planck
Albert Michelson
Edward Morley
Michael Faraday
James Clerk Maxwell
Alessandro Volta
André-Marie Ampère
Georg Ohm
Benjamin Franklin Scientist
Thomas Edison
Alexander Graham Bell
Guglielmo Marconi
John Bardeen
William Shockley
Walter Brattain
Jack Kilby
Robert Noyce
Gordon Moore
Vint Cerf
Bob Kahn
Grace Hopper
Margaret Hamilton
Dorothy Vaughan
Mary Jackson
Katherine Coleman Goble
Sally Ride
Neil deGrasse Tyson
Brian Cox
Carl Sagan Cosmos
Stephen Jay Gould
E.O. Wilson
Jane Goodall Primatologist
Dian Fossey
Birute Galdikas
Richard Dawkins
Francis Collins
Jennifer Doudna
Emmanuelle Charpentier
Kary Mullis
Frederick Sanger
Linus Torvalds
Tim Berners-Lee Web
Shirley Jackson
Chien-Shiung Wu
Subrahmanyan Chandrasekhar
Vera Rubin
Jocelyn Bell Burnell
Caroline Herschel
William Herschel
Edwin Hubble
George Gamow
Fred Hoyle
Arno Penzias
Robert Wilson
John von Neumann
Kurt Gödel
Alonzo Church
Claude Shannon
Norbert Wiener
John Nash
Maryam Mirzakhani
Terence Tao
Emmy Noether
Sophie Germain
Sofia Kovalevskaya""",
    'Historical Figures': """Cleopatra
Julius Caesar
Alexander the Great
Napoleon Bonaparte
Joan of Arc
Genghis Khan
Queen Elizabeth I
Abraham Lincoln
Mahatma Gandhi
Winston Churchill
Hatshepsut
Tutankhamun
Leonardo da Vinci
Michelangelo
William Shakespeare
Socrates
Confucius
Harriet Tubman
Nelson Mandela
Martin Luther King Jr.
Charlemagne
Augustus Caesar
Marcus Aurelius
Nero
Caligula
Constantine the Great
Justinian I
Saladin
Richard the Lionheart
Saladin Sultan
Saladin Ayyubi
William Wallace
Robert the Bruce
Isabella I of Castile
Ferdinand II of Aragon
Christopher Columbus
Vasco da Gama
Magellan Ferdinand
Marco Polo
Ivan the Terrible
Peter the Great
Catherine the Great
Frederick the Great
Otto von Bismarck
Queen Victoria
Queen Elizabeth II
Henry VIII
Anne Boleyn
Mary Queen of Scots
Elizabeth I Tudor
Thomas Jefferson
George Washington
Benjamin Franklin Founding
John Adams
James Madison
Alexander Hamilton
Aaron Burr
Ulysses S Grant
Robert E Lee
Stonewall Jackson
Frederick Douglass
Sojourner Truth
Susan B Anthony
Elizabeth Cady Stanton
Rosa Parks
Malcolm X
Che Guevara
Fidel Castro
Simón Bolívar
José de San Martín
Miguel Hidalgo
Benito Juárez
Emiliano Zapata
Pancho Villa
Ataturk Mustafa Kemal
Reza Shah
Rumi
Ibn Sina
Al-Khwarizmi
Ibn Battuta
Akbar the Great
Ashoka
Chandragupta Maurya
Shivaji Maharaj
Rani Lakshmibai
Tipu Sultan
Emperor Meiji
Tokugawa Ieyasu
Oda Nobunaga
Toyotomi Hideyoshi
Sun Tzu
Qin Shi Huang
Wu Zetian
Kangxi Emperor""",
    'Politicians': """Barack Obama
Angela Merkel
Jacinda Ardern
Volodymyr Zelenskyy
Narendra Modi
Joe Biden
Kamala Harris
Justin Trudeau
Margaret Thatcher
Franklin D. Roosevelt
John F. Kennedy
Indira Gandhi
Golda Meir
Cyrus the Great
Aung San Suu Kyi
Emmanuel Macron
Xi Jinping
Vladimir Putin
Rishi Sunak
Alexandria Ocasio-Cortez
Winston Churchill Politician
Nelson Mandela Statesman
Mahatma Gandhi Leader
George Washington President
Thomas Jefferson President
Abraham Lincoln President
Theodore Roosevelt
Woodrow Wilson
Harry S Truman
Dwight D Eisenhower
Lyndon B Johnson
Richard Nixon
Gerald Ford
Jimmy Carter
Ronald Reagan
George H W Bush
George W Bush
Bill Clinton
Donald Trump
Donald Trump President
Hillary Clinton
Bernie Sanders
Nancy Pelosi
Mitch McConnell
Chuck Schumer
Kevin McCarthy
Mike Pence
Dick Cheney
Al Gore
John Kerry
Condoleezza Rice
Colin Powell
Madeleine Albright
Henry Kissinger
Zbigniew Brzezinski
Helmut Kohl
François Mitterrand
Charles de Gaulle
Jacques Chirac
Nicolas Sarkozy
François Hollande
Olaf Scholz
Ursula von der Leyen
Giorgia Meloni
Pedro Sánchez
Boris Johnson
Theresa May
David Cameron
Gordon Brown
Tony Blair
Keir Starmer
Liz Truss
Benjamin Netanyahu
Yitzhak Rabin
Shimon Peres
Yasser Arafat
Anwar Sadat
Gamal Abdel Nasser
Recep Tayyip Erdoğan
Mohammad Reza Pahlavi
Ayatollah Khomeini
Hassan Rouhani
Joko Widodo
Lee Kuan Yew
Park Chung-hee
Kim Il Sung
Kim Jong Un
Moon Jae-in
Park Geun-hye
Ferdinand Marcos
Corazon Aquino
Rodrigo Duterte
Ferdinand Marcos Jr
Luiz Inácio Lula da Silva
Jair Bolsonaro""",
    'Musicians': """Beyoncé
Taylor Swift
Michael Jackson
Elvis Presley
Madonna
The Beatles
Freddie Mercury
Bob Dylan
Aretha Franklin
Eminem
Drake
Rihanna
David Bowie
Prince
Whitney Houston
Adele
Ed Sheeran
Billie Eilish
Mozart
Beethoven
Johann Sebastian Bach
Franz Schubert
Franz Liszt
Frédéric Chopin
Antonio Vivaldi
Giuseppe Verdi
Richard Wagner
Johannes Brahms
Gustav Mahler
Igor Stravinsky
Dmitri Shostakovich
Sergei Rachmaninoff
Pyotr Ilyich Tchaikovsky
Claude Debussy
Maurice Ravel
Ella Fitzgerald
Louis Armstrong
Billie Holiday
Nina Simone
Ray Charles
Stevie Wonder
Marvin Gaye
James Brown
Prince Rogers Nelson
Jimi Hendrix
Eric Clapton
Jimmy Page
Robert Plant
Keith Richards
Mick Jagger
Paul McCartney
John Lennon
George Harrison
Ringo Starr
Bono
The Edge
Freddie Mercury Queen
Freddie Mercury Rock
Kurt Cobain
Eddie Vedder
Chris Cornell
Chester Benningfield
Chester Bennington
Dave Grohl
Taylor Hawkins
Travis Barker
Post Malone
The Weeknd
Bruno Mars
Justin Timberlake
Justin Bieber
Shawn Mendes
Selena Gomez
Ariana Grande
Lady Gaga
Katy Perry
Pink Singer
Shakira
Bad Bunny
J Balvin
Rosalía
Burna Boy
Wizkid
Davido
Bob Marley
Peter Tosh
Jimmy Cliff
Bob Dylan Folk
Neil Young
Joni Mitchell
Carole King
Paul Simon
Art Garfunkel
Elton John
Billy Joel
Bruce Springsteen""",
    'Business Leaders': """Elon Musk
Jeff Bezos
Bill Gates
Steve Jobs
Oprah Winfrey
Warren Buffett
Mark Zuckerberg
Sundar Pichai
Satya Nadella
Indra Nooyi
Sheryl Sandberg
Jack Ma
Larry Page
Sergey Brin
Tim Cook
Reed Hastings
Brian Chesky
Whitney Wolfe Herd
Madam C.J. Walker
Andrew Carnegie
John D Rockefeller
J.P. Morgan
Henry Ford
Walt Disney
Ray Kroc
Sam Walton
Alice Walton
Jim Walton
Rob Walton
Charles Koch
David Koch
Michael Bloomberg
Michael Dell
Larry Ellison
Marc Benioff
Reid Hoffman
Peter Thiel
Vinod Khosla
John Doerr
Mary Barra
Ginni Rometty
Ursula Burns
Rosalind Brewer
Arianna Huffington
Martha Stewart
Richard Branson
James Dyson
Bernard Arnault
François Pinault
Amancio Ortega
Carlos Slim
Mukesh Ambani
Gautam Adani
Ratan Tata
Narayana Murthy
Azim Premji
Jack Dorsey
Evan Spiegel
Bobby Murphy
Daniel Ek
Martin Lorentzon
Travis Kalanick
Garrett Camp
Brian Armstrong
Changpeng Zhao
Sam Bankman-Fried
Cathie Wood
Warren Buffett Investor
Charlie Munger
Jamie Dimon
Lloyd Blankfein
David Solomon
Abigail Johnson
Ray Dalio
George Soros
Carl Icahn
Bill Ackman
Howard Schultz
Kevin Johnson Starbucks
Herbert Diess
Dieter Zetsche
Mary Kay Ash
Estée Lauder
Helena Rubinstein
Ingvar Kamprad
Stefan Persson
H&M Persson
Tadashi Yanai
Masayoshi Son
SoftBank Son
Jack Welch
Lee Iacocca""",
    'Gaming': """Mario
Luigi
Link
Zelda
Master Chief
Lara Croft
Sonic the Hedgehog
Pikachu
Cloud Strife
Geralt of Rivia
Kratos
Aloy
Solid Snake
Samus Aran
Pac-Man
Steve
Tracer
Joel Miller
Ellie
Commander Shepard
Donkey Kong
Bowser
Princess Peach
Toad Mushroom
Yoshi
Wario
Walugi
Samus Metroid
Meta Knight
Kirby
Fox McCloud
Falco Lombardi
Slippy Toad
Peppy Hare
Captain Falcon
Ness Earthbound
Lucas Earthbound
Marth Fire Emblem
Ike Fire Emblem
Roy Fire Emblem
Lucina Fire Emblem
Chrom Fire Emblem
Ryu Street Fighter
Ken Masters
Chun-Li
Guile Street Fighter
Akuma
Sagat
M Bison
Blanka
Dhalsim
Zangief
E Honda
Cammy White
Jill Valentine
Chris Redfield
Leon S Kennedy
Claire Redfield
Ada Wong
Albert Wesker
Nemesis Resident Evil
Mr X Tyrant
Doom Slayer
Doomguy
Master Chief Halo
Cortana Halo
Arbiter Thel
Noble Six
Ciri Witcher Game
Yennefer Witcher Game
Triss Merigold
Dandelion Witcher
Vesemir
Lambert Witcher
Eskel Witcher
Arthur Morgan
John Marston
Dutch van der Linde
Hosea Matthews
Sadie Adler
Kratos God of War
Atreus
Freya God of War
Baldur God of War
Ellie Last of Us
Abby Anderson
Joel Miller TLOU
Aloy Horizon
Rost Horizon
Sylens Horizon
Erend Horizon
Varl Horizon
Zo Horizon
Kratos Spartan
Bayonetta
Jeanne Bayonetta
2B Nier
9S Nier
A2 Nier
Doom Eternal Slayer
Isaac Clarke
Ellie Clarke Dead Space""",
    'Mythology': """Zeus
Odin
Thor
Loki
Athena
Apollo
Artemis
Hercules
Achilles
Medusa
Anubis
Ra
Isis
Shiva
Vishnu
Lakshmi
Amaterasu
Susanoo
Quetzalcoatl
Anansi
Poseidon
Hades
Demeter
Hera
Aphrodite
Ares
Hermes
Dionysus
Persephone
Perseus
Theseus
Jason Argonauts
Medea
Orpheus
Eurydice
Pandora
Prometheus
Epimetheus
Atlas Titan
Cronus
Rhea Titan
Gaia
Uranus Sky
Nyx Night
Eros Cupid
Pan Satyr
Cerberus
Minotaur
Centaur Chiron
Sphinx Giza
Hydra Lernaean
Cerberus Hound
Fenrir Wolf
Jormungandr
Hel Norse
Baldr
Frigg
Freya
Tyr
Heimdall
Valkyrie Brynhildr
Sigurd Dragon
Beowulf Hero
Gilgamesh King
Enkidu Companion
Ishtar Goddess
Marduk Babylon
Tiamat Dragon
Horus Falcon
Osiris Lord
Set Egyptian
Thoth Ibis
Bastet Cat
Sekhmet Lioness
Anubis Jackal
Ptah Creator
Khnum Ram
Amun Ra
Nut Sky Goddess
Geb Earth God
Anubis Guide
Rama Avatar
Krishna Deity
Hanuman Monkey
Garuda Bird
Kali Goddess
Ganesha Elephant
Durga Warrior
Indra King
Agni Fire
Varuna Water
Yama Death
Garuda Myth
Amaterasu Sun
Tsukuyomi Moon
Susanoo Storm
Izanagi Creator
Izanami Death
Kagutsuchi Fire
Raijin Thunder
Fujin Wind
Inari Fox
Susanoo Slayer
Quetzalcoatl Feathered
Tezcatlipoca Smoking Mirror
Huitzilopochtli War
Coatlicue Mother
Xolotl Dog
Mictlantecuhtli Death""",
    'Literature': """Elizabeth Bennet
Jay Gatsby
Holden Caulfield
Atticus Finch
Huckleberry Finn
Jane Eyre
Don Quixote
Odysseus
Anna Karenina
Heathcliff
Dorian Gray
Lisbeth Salander
Ender Wiggin
Paul Atreides
Tyrion Lannister
Bilbo Baggins
Scout Finch
Pip
Ahab
Harry Dresden
Sherlock Holmes Book
Dr Watson
Professor Moriarty
Irene Adler
Hercule Poirot
Miss Marple
Jane Marple
Philip Marlowe
Sam Spade
Nick Carraway
Daisy Buchanan
Tom Buchanan
Jordan Baker
George Wilson
Myrtle Wilson
Rhett Butler Lit
Scarlett O'Hara Lit
Atticus Finch Mockingbird
Jean Louise Finch
Jem Finch
Boo Radley
Tom Robinson
Calpurnia Mockingbird
Hamlet Prince
Ophelia
Claudius King
Gertrude Queen
Macbeth Thane
Lady Macbeth
Banquo Ghost
Othello Moor
Desdemona
Iago Villain
King Lear
Cordelia
Edmund Bastard
Prospero Tempest
Ariel Spirit
Caliban Monster
Victor Frankenstein
Creature Frankenstein
Robert Walton
Elizabeth Lavenza
Dr Jekyll
Mr Hyde
Count Dracula
Van Helsing
Jonathan Harker
Mina Harker
Lucy Westenra
Renfield Patient
Captain Nemo
Professor Aronnax
Conseil Servant
Ned Land Harpooner
Jean Valjean
Javert Inspector
Cosette Fauchelevent
Fantine Mother
Marius Pontmercy
Enjolras Leader
Gandalf Literature
Frodo Literature
Sam Gamgee
Aragorn Ranger
Legolas Elf
Gimli Dwarf
Boromir Man
Faramir Captain
Eowyn Shieldmaiden
Galadriel Lady
Elrond Half-elven
Sauron Dark Lord
Gollum Sméagol
Smaug Dragon
Beorn Skin-changer
Bard Bowman
Thorin Oakenshield
Balin Dwarf
Dwalin Dwarf
Hermione Literature
Harry Potter Book
Ron Weasley
Albus Dumbledore
Severus Snape
Voldemort Dark Lord
Dobby House Elf
Hagrid Keeper""",
}


def _build_curated_core() -> dict[str, list[tuple[str, list[str]]]]:
    core: dict[str, list[tuple[str, list[str]]]] = {}
    for cat in CATEGORIES:
        core[cat] = _parse_block(_BLOCKS[cat], _OVERRIDES.get(cat))
    return core


CURATED_CORE: dict[str, list[tuple[str, list[str]]]] = _build_curated_core()
