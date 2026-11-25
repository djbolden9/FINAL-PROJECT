import pygame, pygame_widgets, sys, json, random
from pathlib import Path
from pygame_widgets.button import Button

pygame.init()
width, height = 1000, 500
screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()

budget = 100
teamcap = 6

root = Path(__file__).resolve().parent
datafile = root / "pokemon_data.json"
spritesdir = root / "sprites"

matrix = {"normal": {"rock": 0.5, "ghost": 0.0, "steel": 0.5}, "fire": {"fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 2.0, "bug": 2.0, "rock": 0.5, "dragon": 0.5, "steel": 2.0}, "water": {"fire": 2.0, "water": 0.5, "grass": 0.5, "ground": 2.0, "rock": 2.0, "dragon": 0.5}, "electric": {"water": 2.0, "electric": 0.5, "grass": 0.5, "ground": 0.0, "flying": 2.0, "dragon": 0.5}, "grass": {"fire": 0.5, "water": 2.0, "grass": 0.5, "poison": 0.5, "ground": 2.0, "flying": 0.5, "bug": 0.5, "rock": 2.0, "dragon": 0.5, "steel": 0.5}, "ice": {"fire": 0.5, "water": 0.5, "grass": 2.0, "ice": 0.5, "ground": 2.0, "flying": 2.0, "dragon": 2.0, "steel": 0.5}, "fighting": {"normal": 2.0, "ice": 2.0, "poison": 0.5, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "rock": 2.0, "ghost": 0.0, "dark": 2.0, "steel": 2.0, "fairy": 0.5}, "poison": {"grass": 2.0, "poison": 0.5, "ground": 0.5, "rock": 0.5, "ghost": 0.5, "steel": 0.0, "fairy": 2.0}, "ground": {"fire": 2.0, "electric": 2.0, "grass": 0.5, "poison": 2.0, "flying": 0.0, "bug": 0.5, "rock": 2.0, "steel": 2.0}, "flying": {"electric": 0.5, "grass": 2.0, "fighting": 2.0, "bug": 2.0, "rock": 0.5, "steel": 0.5}, "psychic": {"fighting": 2.0, "poison": 2.0, "psychic": 0.5, "dark": 0.0, "steel": 0.5}, "bug": {"fire": 0.5, "grass": 2.0, "fighting": 0.5, "poison": 0.5, "flying": 0.5, "psychic": 2.0, "ghost": 0.5, "dark": 2.0, "steel": 0.5, "fairy": 0.5}, "rock": {"fire": 2.0, "ice": 2.0, "fighting": 0.5, "ground": 0.5, "flying": 2.0, "bug": 2.0, "steel": 0.5}, "ghost": {"normal": 0.0, "psychic": 2.0, "ghost": 2.0, "dark": 0.5}, "dragon": {"dragon": 2.0, "steel": 0.5, "fairy": 0.0}, "dark": {"fighting": 0.5, "psychic": 2.0, "ghost": 0.5, "dark": 0.5, "fairy": 0.5}, "steel": {"fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2.0, "rock": 2.0, "steel": 0.5, "fairy": 2.0}, "fairy": {"fire": 0.5, "fighting": 2.0, "poison": 0.5, "dragon": 2.0, "dark": 2.0, "steel": 0.5}}

tiers = ["Easy", "Medium", "Hard", "Extreme"]

scales = {"Easy": 0.85, "Medium": 1.00, "Hard": 1.15, "Extreme": 1.30}

state = "menu"

def torules():
    global state
    state = "rules"

def tomenu():
    global state
    state = "menu"

def toplay():
    global state
    state = "play"

def tocreate():
    global state
    state = "create"

def toopponent():
    global state
    state = "opponent"

def bybst(mon):
    return mon.get("bst", 0)

def effectiveness(attack, defenders):
    mode = attack.strip().lower()
    row = matrix.get(mode, {})
    factor = 1.0
    for item in defenders:
        target = item.strip().lower()
        factor *= row.get(target, 1.0)
    return factor

def difficulty(mode, stage):
    if mode == "elite":
        idx = min(stage, len(tiers) - 1)
        return tiers[idx]
    idx = min(stage // 2, len(tiers) - 1)
    return tiers[idx]

def enemyteam(pool, level, count=teamcap):
    if not pool:
        return []
    ordered = sorted(pool, key=bybst)
    total = len(ordered)

    if level == "Easy":
        subset = ordered[: max(count, total // 2)]
    elif level == "Medium":
        start = max(0, total // 4)
        stop = min(total, max(start + count, (3 * total) // 4))
        subset = ordered[start:stop]
    elif level == "Hard":
        subset = ordered[max(0, total // 3) :]
    else:
        subset = ordered[max(0, (2 * total) // 5) :]

    if len(subset) < count:
        subset = ordered
    if len(subset) >= count:
        return random.sample(subset, k=count)
    return [random.choice(subset) for _ in range(count)]

def matchup(offense, defense):
    if not offense or not defense:
        return 0.0
    score = 0.0
    for attacker in offense:
        atypes = attacker.get("types", []) or ["normal"]
        for defender in defense:
            dtypes = defender.get("types", []) or ["normal"]
            best = max(effectiveness(t, dtypes) for t in atypes)
            if best >= 2.0:
                score += 18.0
            elif best == 0.0:
                score -= 12.0
            elif best < 1.0:
                score -= 6.0
    return score

def evaluate(yours, foes, level):
    ystats = sum(p.get("bst", 0) for p in yours)
    fstats = sum(p.get("bst", 0) for p in foes)
    ybonus = matchup(yours, foes)
    fbonus = matchup(foes, yours)
    mult = scales.get(level, 1.0)
    ytotal = round(ystats + ybonus, 1)
    ftotal = round((fstats + fbonus) * mult, 1)
    return {"won": ytotal >= ftotal, "yscore": ytotal, "fscore": ftotal, "ystats": ystats, "fstats": fstats, "ybonus": round(ybonus, 1), "fbonus": round(fbonus, 1), "level": level}

def loadpool(size=(56, 56)):
    pool = []
    if not datafile.exists():
        return pool
    with open(datafile, "r", encoding="utf-8") as handle:
        raw = json.load(handle)
    for key, info in raw.items():
        file = info.get("sprite_file", f"{key}.png")
        path = root / file
        if path.exists():
            loaded = pygame.image.load(path).convert_alpha()
            sprite = pygame.transform.scale(loaded, size)
        else:
            sprite = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(sprite, (245, 205, 95), sprite.get_rect(), border_radius=6)
        pool.append({"key": key, "name": info.get("name", key.capitalize()), "value": info.get("value", info.get("cost", 10)), "types": info.get("types", []), "stats": info.get("stats", {}), "bst": info.get("bst", 0), "sprite": sprite})
    return pool

def gridboxes():
    boxes = []
    cols, rows = 3, 3
    x0, y0 = 18, 68
    cw, ch = 170, 130
    gx, gy = 10, 10
    for r in range(rows):
        for c in range(cols):
            x = x0 + c * (cw + gx)
            y = y0 + r * (ch + gy)
            boxes.append(pygame.Rect(x, y, cw, ch))
    return boxes

def slotboxes():
    boxes = []
    x = 788
    w, h = 194, 42
    y0 = 92
    gap = 5
    for i in range(teamcap):
        y = y0 + i * (h + gap)
        boxes.append(pygame.Rect(x, y, w, h))
    return boxes

def drawlines(surface, lines, font, color, pos, gap=8):
    x, y = pos
    for line in lines:
        surf = font.render(line, True, color)
        surface.blit(surf, (x, y))
        y += surf.get_height() + gap

def drawinspector(surface, mon, box, fonts):
    pygame.draw.rect(surface, (26, 30, 38), box, border_radius=8)
    pygame.draw.rect(surface, (245, 205, 95), box, width=2, border_radius=8)

    if not mon:
        msg = fonts["small"].render("Click a Pokémon card", True, (150, 160, 175))
        surface.blit(msg, (box.x + 25, box.y + 150))
        return

    big = pygame.transform.scale(mon["sprite"], (92, 92))
    surface.blit(big, (box.centerx - 46, box.y + 40))

    title = fonts["card"].render(f"{mon['name']} (Cost: {mon['value']})", True, (255, 255, 255))
    surface.blit(title, title.get_rect(centerx=box.centerx, top=box.y + 138))

    types = fonts["small"].render(" / ".join(mon["types"]), True, (155, 200, 255))
    surface.blit(types, types.get_rect(centerx=box.centerx, top=box.y + 158))

    stats = mon["stats"]
    rows = [("HP", stats.get("hp", 0)), ("Atk", stats.get("attack", 0)), ("Def", stats.get("defense", 0)), ("SpA", stats.get("sp_attack", 0)), ("SpD", stats.get("sp_defense", 0)), ("Spe", stats.get("speed", 0)), ("BST", mon["bst"])]

    y = box.y + 180
    barw = 78
    for label, val in rows:
        lbl = fonts["stat"].render(f"{label}: {val}", True, ("white"))
        surface.blit(lbl, (box.x + 14, y))

        fill = max(2, min(barw, int((val / 200) * barw)))
        bg = pygame.Rect(box.right - barw - 14, y + 3, barw, 10)
        fg = pygame.Rect(bg.x, bg.y, fill, bg.height)
        pygame.draw.rect(surface, (50, 56, 68), bg, border_radius=3)
        pygame.draw.rect(surface, (245, 205, 95), fg, border_radius=3)
        y += 20

def togglewidgets(widgets, active):
    for btn in widgets:
        if active:
            btn.show()
            btn.enable()
        else:
            btn.hide()
            btn.disable()

def main():
    global state

    fonts = {"title": pygame.font.SysFont("ravie", 20, bold=True), "card": pygame.font.SysFont("ravie", 10, bold=True), "small": pygame.font.SysFont("ravie", 12), "stat": pygame.font.SysFont("ravie", 13)}

    rulesbtn = Button(screen, 600, 250, 300, 150, text="Rules", font=pygame.font.SysFont("ravie", 50), textColour="white", inactiveColour=(246, 148, 0), hoverColour=(179, 109, 4), pressedColour=(235, 190, 124), radius=50, onClick=torules,)

    playbtn = Button(screen, 100, 250, 300, 150, text="Play", font=pygame.font.SysFont("ravie", 50), textColour="white", inactiveColour=(246, 148, 0), hoverColour=(179, 109, 4), pressedColour=(235, 190, 124), radius=50, onClick=toplay,)

    backbtn = Button(screen, 450, 420, 100, 50, text="Back", font=pygame.font.SysFont("ravie", 20), textColour="white", inactiveColour=(246, 148, 0), hoverColour=(179, 109, 4), pressedColour=(235, 190, 124), radius=50, onClick=tomenu,)

    createbtn = Button(screen, 395, 270, 210, 65, text="Create A Team", font=pygame.font.SysFont("ravie", 18), textColour="white", inactiveColour=(246, 148, 0), hoverColour=(179, 109, 4), pressedColour=(235, 190, 124), radius=25, onClick=tocreate,)

    bannerfont = pygame.font.SysFont("ravie", 75)
    bannertxt = bannerfont.render("PokeParty", True, (255, 255, 255))
    bannerbox = bannertxt.get_rect(center=(500, 100))

    rulefont = pygame.font.SysFont("ravie", 18)
    rules = ["1. Create A Team Within Points Or Draft 6 Rounds (1 Of 3)", "2. Face Random Teams Scaling From Easy To Harder", "3. Choose Elite Four (4 Battles) Or Endless Mode", "4. Teams Are Evaluated By Stats, Types & Difficulty", "5. Have Fun!"]

    modefont = pygame.font.SysFont("ravie", 75)
    modetxt = modefont.render("Mode", True, (255, 255, 255))
    modebox = modetxt.get_rect(center=(500, 100))

    pool = loadpool()
    page = 0
    picked = pool[0] if pool else None
    roster = []
    notice = ""
    squad = []

    roundnum = 0
    choices = []
    choice = None
    drafted = []
    prompt = ""

    series = "elite"
    stage = 0
    wins = 0
    foes = []
    level = "Easy"
    report = None
    finished = False
    summary = ""

    leftpanel = pygame.Rect(10, 10, 562, 480)
    midpanel = pygame.Rect(580, 10, 192, 480)
    rightpanel = pygame.Rect(780, 10, 210, 480)

    cards = gridboxes()
    slots = slotboxes()
    draftcards = [pygame.Rect(24, 130, 170, 250), pygame.Rect(203, 130, 170, 250), pygame.Rect(382, 130, 170, 250)]

    def setstage(mode, idx):
        nonlocal series, stage, level, foes, report, finished, summary
        series = mode
        stage = idx
        level = difficulty(mode, idx)
        foes = enemyteam(pool, level, teamcap)
        report = None
        finished = False
        summary = ""

    def startelite():
        global state
        nonlocal wins
        wins = 0
        setstage("elite", 0)
        state = "evaluate"

    def startendless():
        global state
        nonlocal wins
        wins = 0
        setstage("endless", 0)
        state = "evaluate"

    def scorematch():
        nonlocal report, wins, finished, summary
        if report is not None:
            return
        res = evaluate(squad, foes, level)
        report = res
        if res["won"]:
            wins += 1
            if series == "elite" and stage + 1 >= len(tiers):
                finished = True
                summary = f"Elite Four Champion! Won {wins}/4 battles!"
            else:
                summary = f"Victory! Ready for Battle {stage + 2}."
        else:
            finished = True
            if series == "elite":
                summary = f"Defeated in Elite Four Battle {stage + 1}/4."
            else:
                summary = f"Endless Run ended after {wins} win(s)!"

    def nextbattle():
        if not report or not report["won"] or finished:
            return
        setstage(series, stage + 1)

    def prevpage():
        nonlocal page
        if page > 0:
            page -= 1

    def nextpage():
        nonlocal page
        last = max(0, (len(pool) - 1) // 9)
        if page < last:
            page += 1

    def addmon():
        nonlocal notice
        if not picked:
            return
        spent = sum(p["value"] for p in roster)
        if len(roster) >= teamcap:
            notice = "Team full (6/6)!"
            return
        if any(p["key"] == picked["key"] for p in roster):
            notice = "Already on team!"
            return
        if spent + picked["value"] > budget:
            notice = "Not enough points!"
            return
        roster.append(picked)
        notice = f"Added {picked['name']}"

    def lockcustom():
        nonlocal notice, squad
        if len(roster) < teamcap:
            notice = f"Pick {teamcap} Pokémon first!"
        else:
            squad = list(roster)
            notice = "Team ready!"
            toopponent()

    def deal():
        nonlocal choices, choice
        taken = {p["key"] for p in drafted}
        openpool = [p for p in pool if p["key"] not in taken]
        source = openpool if len(openpool) >= 3 else pool
        k = min(3, len(source))
        choices = random.sample(source, k=k) if k > 0 else []
        choice = choices[0] if choices else None

    def startdraft():
        global state
        nonlocal roundnum, drafted, prompt
        roundnum = 0
        drafted = []
        prompt = "Round 1 of 6: Choose 1"
        deal()
        state = "draft"

    def pickdraft():
        nonlocal roundnum, choice, prompt
        if roundnum >= teamcap:
            prompt = "Draft complete! Continue."
            return
        if not choice:
            prompt = "Click a choice first!"
            return
        drafted.append(choice)
        roundnum += 1
        if roundnum < teamcap:
            deal()
            prompt = f"Round {roundnum + 1} of 6: Choose 1"
        else:
            choices = []
            choice = None
            prompt = "All 6 rounds drafted!"

    def lockdraft():
        nonlocal squad, prompt
        if len(drafted) < teamcap:
            prompt = f"Complete all {teamcap} rounds first!"
            return
        squad = list(drafted)
        toopponent()

    draftbtn = Button(screen, 395, 185, 210, 65, text="Draft Mode", font=pygame.font.SysFont("ravie", 18), textColour="white", inactiveColour=(246, 148, 0), hoverColour=(179, 109, 4), pressedColour=(235, 190, 124), radius=25, onClick=startdraft,)

    modeback = Button(screen, 450, 385, 100, 50, text="Back", font=pygame.font.SysFont("ravie", 20), textColour="white", inactiveColour=(246, 148, 0), hoverColour=(179, 109, 4), pressedColour=(235, 190, 124), radius=50, onClick=tomenu,)

    prevbtn = Button(screen, 415, 18, 68, 36, text="< Prev", font=fonts["small"], onClick=prevpage)
    nextbtn = Button(screen, 490, 18, 68, 36, text="Next >", font=fonts["small"], onClick=nextpage)

    addbtn = Button(screen, midpanel.x + 16, midpanel.bottom - 46, midpanel.width - 32, 34, text="Add to Team", font=fonts["card"], inactiveColour=(45, 130, 85), hoverColour=(60, 160, 105), pressedColour=(30, 100, 65), textColour=(255, 255, 255), onClick=addmon,)

    createback = Button(screen, rightpanel.x + 12, rightpanel.bottom - 44, 88, 34, text="Back", font=fonts["card"], inactiveColour=(95, 105, 125), hoverColour=(115, 125, 145), pressedColour=(75, 85, 105), textColour=(255, 255, 255), onClick=toplay,)

    createnext = Button(screen, rightpanel.x + 108, rightpanel.bottom - 44, 90, 34, text="NEXT", font=fonts["card"], inactiveColour=(210, 110, 20), hoverColour=(235, 130, 35), pressedColour=(40, 180, 60), textColour=(255, 255, 255), onClick=lockcustom,)

    draftpick = Button(screen, midpanel.x + 16, midpanel.bottom - 46, midpanel.width - 32, 34, text="Draft Pick", font=fonts["card"], inactiveColour=(45, 130, 85), hoverColour=(60, 160, 105), pressedColour=(30, 100, 65), textColour=(255, 255, 255), onClick=pickdraft,)

    draftback = Button(screen, rightpanel.x + 12, rightpanel.bottom - 44, 84, 34, text="Back", font=fonts["card"], inactiveColour=(95, 105, 125), hoverColour=(115, 125, 145), pressedColour=(75, 85, 105), textColour=(255, 255, 255), onClick=toplay,)

    draftnext = Button(screen, rightpanel.x + 102, rightpanel.bottom - 44, 96, 34, text="NEXT", font=fonts["card"], inactiveColour=(210, 110, 20), hoverColour=(235, 130, 35), pressedColour=(40, 180, 60), textColour=(255, 255, 255), onClick=lockdraft,)

    elitebtn = Button(screen, 220, 230, 250, 85, text="Elite Four (4)", font=pygame.font.SysFont("ravie", 18), textColour="white", inactiveColour=(210, 110, 20), hoverColour=(235, 130, 35), pressedColour=(245, 180, 90), radius=20, onClick=startelite,)

    endlessbtn = Button(screen, 530, 230, 250, 85, text="Endless Run", font=pygame.font.SysFont("ravie", 18), textColour="white", inactiveColour=(55, 135, 210), hoverColour=(40, 105, 170), pressedColour=(120, 180, 235), radius=20, onClick=startendless,)

    oppback = Button(screen, 450, 415, 100, 50, text="Back", font=pygame.font.SysFont("ravie", 20), textColour="white", inactiveColour=(95, 105, 125), hoverColour=(115, 125, 145), pressedColour=(75, 85, 105), radius=25, onClick=toplay,)

    evalbtn = Button(screen, 240, 425, 210, 48, text="Evaluate Match", font=fonts["small"], textColour="white", inactiveColour=(45, 130, 85), hoverColour=(60, 160, 105), pressedColour=(30, 100, 65), radius=12, onClick=scorematch,)

    stepbtn = Button(screen, 470, 425, 210, 48, text="Next Battle >", font=fonts["small"], textColour="white", inactiveColour=(210, 110, 20), hoverColour=(235, 130, 35), pressedColour=(245, 180, 90), radius=12, onClick=nextbattle,)

    switchbtn = Button(screen, 700, 425, 220, 48, text="Change Series", font=fonts["small"], textColour="white", inactiveColour=(95, 105, 125), hoverColour=(115, 125, 145), pressedColour=(75, 85, 105), radius=12, onClick=toopponent,)

    createui = [prevbtn, nextbtn, addbtn, createback, createnext]
    draftui = [draftpick, draftback, draftnext]
    modeui = [createbtn, draftbtn, modeback]
    oppui = [elitebtn, endlessbtn, oppback]
    evalui = [evalbtn, stepbtn, switchbtn]

    running = True
    while running:
        events = pygame.event.get()
        pointer = pygame.mouse.get_pos()

        start = page * 9
        shown = pool[start:start + 9]

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == "create":
                    for idx, box in enumerate(cards):
                        if idx < len(shown) and box.collidepoint(event.pos):
                            picked = shown[idx]
                            notice = ""

                    for idx, box in enumerate(slots):
                        if idx < len(roster) and box.collidepoint(event.pos):
                            drop = roster.pop(idx)
                            notice = f"Removed {drop['name']}"

                elif state == "draft":
                    for idx, box in enumerate(draftcards):
                        if idx < len(choices) and box.collidepoint(event.pos):
                            choice = choices[idx]

        rulesbtn.hide()
        rulesbtn.disable()
        playbtn.hide()
        playbtn.disable()
        backbtn.hide()
        backbtn.disable()
        togglewidgets(modeui, False)
        togglewidgets(createui, False)
        togglewidgets(draftui, False)
        togglewidgets(oppui, False)
        togglewidgets(evalui, False)

        if state == "menu":
            pygame.display.set_caption("Main Menu")
            screen.fill((20, 20, 20))
            screen.blit(bannertxt, bannerbox)
            rulesbtn.show()
            rulesbtn.enable()
            playbtn.show()
            playbtn.enable()

        elif state == "rules":
            pygame.display.set_caption("Rules")
            screen.fill("black")
            drawlines(screen, rules, rulefont, (255, 255, 255), (60, 90), gap=18)
            backbtn.show()
            backbtn.enable()

        elif state == "play":
            pygame.display.set_caption("Play")
            screen.fill("black")
            screen.blit(modetxt, modebox)
            togglewidgets(modeui, True)

        elif state == "create":
            pygame.display.set_caption("Create A Team")
            screen.fill((16, 18, 24))
            togglewidgets(createui, True)

            for panel in (leftpanel, midpanel, rightpanel):
                pygame.draw.rect(screen, (24, 27, 34), panel, border_radius=8)
                pygame.draw.rect(screen, (245, 205, 95), panel, width=2, border_radius=8)

            heading = fonts["title"].render("All Pokémon", True, (235, 240, 248))
            screen.blit(heading, (22, 24))

            pages = max(1, (len(pool) + 8) // 9)
            pagelbl = fonts["small"].render(f"Page {page + 1}/{pages}", True, (180, 190, 205))
            screen.blit(pagelbl, (335, 28))

            used = {p["key"] for p in roster}
            for idx, box in enumerate(cards):
                if idx >= len(shown):
                    break
                mon = shown[idx]
                selected = picked and mon["key"] == picked["key"]
                onroster = mon["key"] in used
                hovered = box.collidepoint(pointer)

                fill = (44, 52, 68) if selected else ((36, 42, 54) if hovered else (30, 34, 43))
                edge = (250, 190, 50) if selected else ((90, 170, 120) if onroster else (60, 70, 88))

                pygame.draw.rect(screen, fill, box, border_radius=6)
                pygame.draw.rect(screen, edge, box, width=2, border_radius=6)

                costlbl = fonts["small"].render(f"Cost: {mon['value']}", True, (245, 205, 95))
                screen.blit(costlbl, (box.right - costlbl.get_width() - 8, box.y + 6))

                iconbox = mon["sprite"].get_rect(center=(box.centerx, box.y + 62))
                screen.blit(mon["sprite"], iconbox)

                namelbl = fonts["card"].render(mon["name"], True, (240, 244, 250))
                screen.blit(namelbl, namelbl.get_rect(centerx=box.centerx, bottom=box.bottom - 8))

            drawinspector(screen, picked, midpanel, fonts)

            left = budget - sum(p["value"] for p in roster)
            rosterlbl = fonts["title"].render("Roster", True, (235, 240, 248))
            screen.blit(rosterlbl, (rightpanel.x + 14, rightpanel.y + 10))

            pointcol = (110, 225, 140) if left >= 0 else (235, 90, 90)
            pointlbl = fonts["card"].render(f"Points Left: {left} / {budget}  ({len(roster)}/{teamcap})", True, pointcol)
            screen.blit(pointlbl, (rightpanel.x + 14, rightpanel.y + 38))

            noticelbl = fonts["small"].render(notice, True, (250, 185, 85))
            screen.blit(noticelbl, (rightpanel.x + 14, rightpanel.y + 62))

            for idx, box in enumerate(slots):
                pygame.draw.rect(screen, (32, 37, 47), box, border_radius=6)
                pygame.draw.rect(screen, (70, 80, 98), box, width=1, border_radius=6)

                if idx < len(roster):
                    member = roster[idx]
                    mini = pygame.transform.scale(member["sprite"], (32, 32))
                    screen.blit(mini, (box.x + 5, box.y + 5))
                    entry = fonts["small"].render(f"{member['name']} ({member['value']}pt)", True, (240, 244, 250))
                    screen.blit(entry, (box.x + 43, box.y + 13))
                else:
                    empty = fonts["small"].render(f"Slot {idx + 1}", True, (245, 205, 95))
                    screen.blit(empty, (box.x + 12, box.y + 13))

        elif state == "draft":
            pygame.display.set_caption("Draft Mode")
            screen.fill((16, 18, 24))
            togglewidgets(draftui, True)

            if not choices and len(drafted) < teamcap and pool:
                deal()

            for panel in (leftpanel, midpanel, rightpanel):
                pygame.draw.rect(screen, (24, 27, 34), panel, border_radius=8)
                pygame.draw.rect(screen, (245, 205, 95), panel, width=2, border_radius=8)

            cur = min(roundnum + 1, teamcap)
            head = fonts["title"].render(f"Draft - Round {cur}/{teamcap}", True, (235, 240, 248))
            screen.blit(head, (22, 24))

            sub = fonts["small"].render("Pick 1 of 3 random Pokémon each round", True, (170, 185, 205))
            screen.blit(sub, (22, 56))

            if choices:
                for idx, box in enumerate(draftcards):
                    if idx >= len(choices):
                        break
                    mon = choices[idx]
                    selected = choice and mon["key"] == choice["key"]
                    hovered = box.collidepoint(pointer)

                    fill = (44, 52, 68) if selected else ((36, 42, 54) if hovered else (30, 34, 43))
                    edge = (250, 190, 50) if selected else (65, 80, 105)

                    pygame.draw.rect(screen, fill, box, border_radius=8)
                    pygame.draw.rect(screen, edge, box, width=2, border_radius=8)

                    art = pygame.transform.scale(mon["sprite"], (84, 84))
                    screen.blit(art, art.get_rect(center=(box.centerx, box.y + 85)))

                    namelbl = fonts["card"].render(mon["name"], True, (240, 244, 250))
                    screen.blit(namelbl, namelbl.get_rect(centerx=box.centerx, top=box.y + 140))

                    typelbl = fonts["small"].render(" / ".join(mon["types"]), True, (245, 205, 95))
                    screen.blit(typelbl, typelbl.get_rect(centerx=box.centerx, top=box.y + 165))

                    bstlbl = fonts["small"].render(f"BST: {mon['bst']}", True, (245, 205, 95))
                    screen.blit(bstlbl, bstlbl.get_rect(centerx=box.centerx, top=box.y + 195))
            elif len(drafted) >= teamcap:
                donelbl = fonts["small"].render("Draft complete! Click NEXT to choose a series.", True, (110, 225, 140))
                screen.blit(donelbl, (26, 220))
            else:
                errlbl = fonts["small"].render("No Pokémon found in pokemon_data.json!", True, (235, 90, 90))
                screen.blit(errlbl, (26, 220))

            drawinspector(screen, choice, midpanel, fonts)

            totalbst = sum(p["bst"] for p in drafted)
            draftlbl = fonts["title"].render("Drafted", True, (235, 240, 248))
            screen.blit(draftlbl, (rightpanel.x + 14, rightpanel.y + 10))

            countlbl = fonts["card"].render(f"Picks: {len(drafted)}/{teamcap}  |  BST: {totalbst}", True, (110, 225, 140))
            screen.blit(countlbl, (rightpanel.x + 14, rightpanel.y + 38))

            promptlbl = fonts["small"].render(prompt, True, (250, 185, 85))
            screen.blit(promptlbl, (rightpanel.x + 14, rightpanel.y + 62))

            for idx, box in enumerate(slots):
                pygame.draw.rect(screen, (32, 37, 47), box, border_radius=6)
                pygame.draw.rect(screen, (70, 80, 98), box, width=1, border_radius=6)

                if idx < len(drafted):
                    member = drafted[idx]
                    mini = pygame.transform.scale(member["sprite"], (32, 32))
                    screen.blit(mini, (box.x + 5, box.y + 5))
                    entry = fonts["small"].render(f"{member['name']} ({member['bst']})", True, (240, 244, 250))
                    screen.blit(entry, (box.x + 43, box.y + 13))
                else:
                    empty = fonts["small"].render(f"Round {idx + 1} Pick", True, (120, 130, 148))
                    screen.blit(empty, (box.x + 12, box.y + 13))

        elif state == "opponent":
            pygame.display.set_caption("Choose Series")
            screen.fill((16, 18, 24))
            togglewidgets(oppui, True)

            head = fonts["title"].render("Choose Random Battle Series", True, (240, 244, 250))
            screen.blit(head, head.get_rect(centerx=width // 2, top=42))

            names = ", ".join(p["name"] for p in squad)
            teamline = fonts["small"].render(f"Your Team: {names}", True, (155, 200, 255))
            screen.blit(teamline, teamline.get_rect(centerx=width // 2, top=86))

            info = ["All enemy teams are randomly generated and scale from Easy to Harder.", "Elite Four: 4 progressive battles (Easy -> Medium -> Hard -> Extreme).", "Endless Run: Keep battling random teams as difficulty scales up until defeat."]
            drawlines(screen, info, fonts["small"], (195, 205, 220), (130, 132), gap=10)

        elif state == "evaluate":
            pygame.display.set_caption("Battle Evaluation")
            screen.fill((16, 18, 24))
            togglewidgets(evalui, True)

            ready = bool(report and report["won"] and not finished)
            if ready:
                stepbtn.enable()
            else:
                stepbtn.disable()

            mode = "Elite Four" if series == "elite" else "Endless"
            label = f"Battle {stage + 1}/4" if series == "elite" else f"Battle {stage + 1}"
            head = fonts["title"].render(f"{mode} - {label}  |  Difficulty: {level}", True, (240, 244, 250))
            screen.blit(head, head.get_rect(centerx=width // 2, top=22))

            ybox = pygame.Rect(24, 65, 465, 210)
            fbox = pygame.Rect(511, 65, 465, 210)
            rbox = pygame.Rect(24, 285, 952, 128)

            for box in (ybox, fbox, rbox):
                pygame.draw.rect(screen, (24, 27, 34), box, border_radius=8)
                pygame.draw.rect(screen, (65, 75, 92), box, width=2, border_radius=8)

            screen.blit(fonts["small"].render("Your Team", True, (110, 225, 140)), (ybox.x + 14, ybox.y + 10))
            screen.blit(fonts["small"].render(f"Random Opponent ({level})", True, (245, 165, 85)), (fbox.x + 14, fbox.y + 10))

            for idx, mon in enumerate(squad[:teamcap]):
                cx = ybox.x + 42 + idx * 72
                cy = ybox.y + 88
                screen.blit(mon["sprite"], mon["sprite"].get_rect(center=(cx, cy)))
                lbl = fonts["card"].render(mon["name"][:9], True, (235, 240, 248))
                screen.blit(lbl, lbl.get_rect(centerx=cx, top=cy + 34))

            for idx, mon in enumerate(foes[:teamcap]):
                cx = fbox.x + 42 + idx * 72
                cy = fbox.y + 88
                screen.blit(mon["sprite"], mon["sprite"].get_rect(center=(cx, cy)))
                lbl = fonts["card"].render(mon["name"][:9], True, (235, 240, 248))
                screen.blit(lbl, lbl.get_rect(centerx=cx, top=cy + 34))

            if report is None:
                tip = fonts["small"].render("Click 'Evaluate Match' to compare stats, types, and difficulty.", True, (200, 210, 225))
                screen.blit(tip, (rbox.x + 18, rbox.y + 18))
            else:
                verdictcol = (110, 225, 140) if report["won"] else (235, 90, 90)
                verdict = "YOU WIN!" if report["won"] else "YOU LOSE!"
                screen.blit(fonts["title"].render(verdict, True, verdictcol), (rbox.x + 18, rbox.y + 12))

                scores = (
                    f"Your Score: {report['yscore']} (BST {report['ystats']} + Type {report['ybonus']})   |   "
                    f"Enemy Score: {report['fscore']} (BST {report['fstats']} + Type {report['fbonus']}, x{scales[level]})"
                )
                screen.blit(fonts["card"].render(scores, True, (230, 235, 245)), (rbox.x + 18, rbox.y + 48))

                streak = f"{summary}  Total Wins This Run: {wins}"
                screen.blit(fonts["small"].render(streak, True, (250, 205, 95)), (rbox.x + 18, rbox.y + 76))

        pygame_widgets.update(events)
        pygame.display.update()

        clock.tick(60)

main()
