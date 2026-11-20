#!/usr/bin/env python3
"""Build app/data/trophies.json: official PlayStation text preserved verbatim,
original guide copy, source citations, roadmap and meta added.

Run from the repository root:  python3 tools/build-trophies.py
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "app" / "data" / "trophies.json"

SOURCES = {
    "psn": {"name": "PSNProfiles trophy guide", "url": "https://psnprofiles.com/guide/19042-grand-theft-auto-vi-trophy-guide"},
    "psn_list": {"name": "PSNProfiles trophy list", "url": "https://psnprofiles.com/trophies/31277-grand-theft-auto-vi"},
    "exo": {"name": "Exophase trophy list", "url": "https://www.exophase.com/game/grand-theft-auto-vi-ps5/trophies/"},
    "ppyx": {"name": "PowerPyx trophy guide & roadmap", "url": "https://www.powerpyx.com/grand-theft-auto-vi-trophy-guide-roadmap/"},
    "ppyx_col": {"name": "PowerPyx collectibles guide", "url": "https://www.powerpyx.com/grand-theft-auto-vi-all-collectibles-guide/"},
    "ign": {"name": "IGN wiki: trophies", "url": "https://www.ign.com/wikis/grand-theft-auto-6/Trophies"},
    "ign_map": {"name": "IGN wiki: Leonida map & districts", "url": "https://www.ign.com/wikis/grand-theft-auto-6/Leonida"},
    "wiki": {"name": "GTA Wiki: trophies in GTA VI", "url": "https://gta.fandom.com/wiki/Trophies_in_GTA_VI"},
    "wiki_act": {"name": "GTA Wiki: activities in Leonida", "url": "https://gta.fandom.com/wiki/Activities_in_GTA_VI"},
}

GUIDES = {
    1: "Nothing here is earned directly: the platinum registers the moment the other fifty-four entries are on your profile, so treat it as a receipt for a finished checklist. Work the roadmap from stage one, keep a manual save at the start of Chapter 4, and clear every missable side strand before you trigger the finale. After the credits, sweep the map for collectibles and activity medals, then mop up the money and property trophies in free roam.",
    2: "The opening job doubles as the tutorial, so it cannot be failed permanently, but it can be made to drag. Stay behind Lucia during the marina approach, use the cover prompt on the first guard instead of shooting early, and grab both crates in the cabin before you climb out. When the boat swap happens, take the helm and follow the channel markers south. The trophy lands on the mission summary screen.",
    3: "Chapter 1 covers the Port Gellhorn motel jobs and closes with the first Vice City score. Follow the yellow story markers in order, but detour for the two optional prep jobs, the tow-truck grab and the fence tail, because they hand you the getaway route used in the finale. Bank a manual save before the last marker. The chapter trophy fires when the closing cutscene ends.",
    4: "Chapter 2 pushes the cartel thread through Little Havana and the Grassrivers. The missions are linear, but two of them hide optional objectives: photograph the ledger during the second meet, and leave the deal with the money instead of the product. Neither blocks the chapter, though the ledger photo pays off in a later heist. Follow the markers until the dockside ambush resolves; the trophy pops on the drive home.",
    5: "Chapter 3 is the longest stretch before the endgame: three set-piece robberies, a chase through Downtown and the first proper look at the Leonida Keys. Do the safehouse upgrades between missions so you are not caught short on armour, and finish the optional driving job for the mechanic, which unlocks a faster getaway car for the chapter's last mission. The trophy appears after the rooftop cutscene.",
    6: "Chapter 4 turns the crew against each other and sends you back to Vice Beach for the penthouse job. Save manually before the boardroom marker: the chapter ends with a choice that changes which escape route you get, though both routes complete the chapter. Take the helicopter exit if you want the cleaner shoot-out. The trophy registers once the news report cutscene plays out.",
    7: "The finale chains three phases with no checkpoint between the second and the third, so bring full armour, a scoped rifle and a fast car parked near the rendezvous. In the first phase keep your partner alive by clearing the balcony shooters early; in the second, drive the coastal road rather than the highway to shake the convoy. Finish the last stand from cover. The gold trophy lands after the credits roll.",
    8: "Breakfast Run is the early morning diner job in Port Gellhorn. Arrive before 09:00 in-game to catch the contact at the counter, then take the back exit rather than the front when the alarm trips, since the alley gives you a clear run to the parked van. Do not fire first: the mission fails if the cook is hit. Drive the van to the scrapyard and the trophy is yours.",
    9: "The Cartel Heist is the mid-game bank job. Do the two prep missions first, the security schedule photo and the drill pickup. In the vault, use the thermal charge on the inner door rather than the hinges, grab the marked bills as well as the cash, and follow the tunnel route instead of the lobby. The escape car waits in the storm drain. The trophy pops at the safehouse.",
    10: "Child's Play is the custody handover that goes wrong on the causeway. Keep your weapon holstered during the meet, let the conversation play out, and only draw when the first shot comes from the bridge. Target the shooters on the north side first so the car has a clear lane. Drive your partner to the safehouse without calling the police. The trophy lands on arrival.",
    11: "Headliners is the concert-venue job on the Vice Beach strip. Buy a ticket at the box office during the day to scout the layout, then return at night for the actual mission. Use the stage-left service stairs, cut the power at the breaker behind the bar, and exit through the loading bay. Avoid the dance floor entirely, because the crowd slows you down. The trophy fires when you reach the van.",
    12: "VCIA Takedown sends you onto the airport apron after the cargo manifest. Park outside the perimeter fence, climb the service ladder near the fuel depot, and cross the tarmac behind the baggage carts. Do not shoot the tower guards: the alarm adds a five-minute timer. Take the manifest from the hangar office and leave the way you came. The trophy registers once you clear the fence.",
    13: "Operation Savage Glory is the late-game assault on the mountain depot in Mount Kalaga. Buy cold-weather gear from the surplus counter before you travel, or your health drains on the ridge. Approach from the western trail, silence the two sentries at the gate, and plant charges on the fuel tanks before the alarm sounds. Extract by the snowplough road. The trophy lands after the debrief.",
    14: "Completion is a checklist of checklists: story, side strands, activities, collectibles, properties, vehicles and the odd hidden event. Use the tracker's roadmap view to keep the order sane, and finish every activity at least once before you start sweeping pickups, because a few collectibles only spawn after their related activity is done. The pause-menu completion tab names anything still missing. The gold trophy follows the final tick.",
    15: "Stunts count any jump, wheelie, drift chain or air trick the game scores, so pick a vehicle you can repeat quickly rather than hunting the big set-piece ramps. The airstrip outside Ambrosia and the beachfront promenade in Vice Beach are the two best loops: run them on a fast bike for wheelies and in a low sports car for drift scores. Chain five or six per pass. The counter sits in the stats menu.",
    16: "The activity board lists nine types: races, stunt races, drone races, shooting range, fishing, bowling, arcade, golf and the triathlon. You only need to start and finish one of each, so knock them out in a single afternoon. The bowling alley and arcade sit next door to each other in Vice Beach, the golf course is in Coral Springs, and fishing starts at any jetty with a rod. The pause menu tracks the list.",
    17: "Three ranges host the challenges: Downtown Vice City, Port Gellhorn and the surplus shop near the airbase, each with timed and accuracy stages. Gold usually means finishing under par time with no misses, so learn each lane's target order before chasing the clock. The rotating-target stage on the Downtown range is the hardest; use the pistol rather than the rifle, since the reload is shorter. Golds are tracked per challenge.",
    18: "Top Fun drones launch from fourteen pads: six around Vice City, four in the Keys, two in the Grassrivers, one at Port Gellhorn and one on Mount Kalaga. Win each track once; you do not need a clean run, just first place. Upgrade the drone's battery at any hobby shop first, because the Keys tracks are long and the stock battery dies over water. The trophy fires on the fourteenth win.",
    19: "Twenty different race events, not twenty wins in the same event, so plan a tour of the map. Street races cluster in Vice City, off-road events run through the Grassrivers, and boat races start at the Keys marinas. Set the difficulty to standard and use a fully upgraded car from your garage; the AI rubber-bands hard on the downtown circuit. Progress is in the stats menu under Races Won.",
    20: "Cal shows up at the Key Largo pier after you finish the third Kenton strand and challenges you to a bass contest. He is only there for a limited window, so accept the first time he waves you over. Fish the deep side of the pier with a crank bait, and release everything under three pounds so your five best fish are all keepers. Beat his total before the timer runs out.",
    21: "Any arcade cabinet counts, and the easiest is the beat-'em-up in the Vice Beach boardwalk arcade, which offers continues, so you cannot really lose. Feed the machine quarters, pick the fast character, and mash through the six stages; the final boss telegraphs his charge with a two-step shuffle. The cabinets in Little Havana are harder. The trophy unlocks the moment the credits screen appears.",
    22: "Andy's strand begins at the rehab clinic in Coral Springs and runs four missions. It closes once you finish Chapter 4, so do his jobs before the endgame marker appears. The last mission asks you to drive him to the airport without a wanted level; take the back roads past the golf course rather than the highway, and do not stop for the pursuing paparazzi. The trophy fires at the departures drop-off.",
    23: "Kenton's three missions start at the marina in the Keys and involve salvage diving. The strand is only available while the cartel thread is open, so finish it before Chapter 3 ends. Buy the diving suit from the marina shop first, because the last dive is deep enough to hurt without it. Follow the wreck's port side, cut the two cables, and surface with the case before your air runs out.",
    24: "Billy runs the bike shop in Port Gellhorn and his strand unlocks after the first chapter. He closes up for good once you start Chapter 4, so do the three deliveries early. Each delivery has a time limit; use the dirt trail behind the motel instead of the main road, and never stop to fight the rival club. The final drop ends at the racetrack and the trophy lands there.",
    25: "Eight separate stranger strands have to be finished, and several expire as the story advances: the bounty hunter, the photographer and the radio DJ are the three that vanish first. Open each strand as soon as its icon appears on the map, finish all of its missions, then move on. The pause menu's Strangers tab lists which strands are complete. The silver trophy fires on the eighth completion.",
    26: "Randy's strand is the gun-running chain that starts behind the hardware store in Ambrosia. It runs five missions and shuts down after the final heist, so clear it during Chapter 4. The tricky step is the convoy ambush: park across the road to block the lead truck, then take the driver out before the escorts fan out. Deliver the last crate to the airstrip to finish.",
    27: "Tyrone's missions open at the car wash in Little Havana and revolve around the drift scene. Finish all four before the endgame, because the strand disappears once the finale unlocks. The last mission is a three-lap drift battle at the docks: feather the handbrake into the corners and ignore the score, since only position matters. The trophy appears when you park back at the car wash.",
    28: "Meditation spots are marked by a small lotus icon and only register when you stand still on the pad for a second. There are eighteen across Leonida: seven in Vice City, four in the Keys, three in the Grassrivers, two at Port Gellhorn, and one each at Ambrosia and Mount Kalaga. Sit through the full breathing prompt, not just the first frame. The collectibles map filter shows the ones already used.",
    29: "Bret's hunting trip unlocks at the ranger station on Mount Kalaga after the second chapter. He wants a specific panther, and the animal only spawns during the mission window; miss it and the strand is gone for good. Track it north of the station at dawn, use the scoped rifle from the ridge, and take a clean head shot so the pelt is not damaged. Return to Bret to finish.",
    30: "Collectible cards come in themed sets of twelve, sold in packs at convenience stores and dropped by certain enemies. Three complete sets is enough, so buy out the card rack at every shop you pass and trade duplicates at the comic shop in Vice Beach. The sports and muscle-car sets are the cheapest to finish. The trophy registers when the third set completes in the collection menu.",
    31: "WAiNK is the in-game social app, and each check-in needs you to stand at a landmark and post a photo. There are far more than a hundred spots, so pick a dense route: Ocean Beach alone has fourteen, and the boardwalk, pier and downtown rooftops add twenty more. Use the app's map layer to see which pins are unvisited. The trophy fires on the hundredth post, with no quality requirement.",
    32: "Challenges are the rotating free-roam objectives that appear as a small card in the corner: timed deliveries, bounty targets, vehicle thefts and photo jobs. Fifty is a long haul, so accept every one you pass and never abandon a chain, because abandoning resets its counter. The board at the taxi depot in Port Gellhorn refreshes three at a time and is the fastest way to farm them. Progress is in the stats menu.",
    33: "This only works while your partner is following you, which stops being the default once the story splits the crew. Build a four-star wanted level somewhere with long sightlines, the Downtown loop is ideal, then break line of sight together in an alley, swap to a parked car and drive into the storm drain tunnel. Stay below the radar until the stars fade. Both characters must be in the car.",
    34: "The three shops must be robbed in one run, with the wanted level never clearing. Do it early in the story while your partner still rides with you. Pick three convenience stores on the same road; the strip in Little Havana has four within a kilometre. Rob each one, stay in the car between jobs, and lose the police only after the third register. The trophy pops as the third till opens.",
    35: "Vehicles count as discovered once you have driven or flown them, so the fastest route is valet work: the hotel rank in Vice Beach lets you cycle through dozens of cars in an hour. Add the marina's boats, the airfield's planes and the police impound lot. The pause menu's vehicle list shows silhouettes for anything still missing. The trophy lands on the hundredth entry, with nothing to buy.",
    36: "Combat Focus slows time and marks targets; the trick is stacking five kills inside one charge. Start it in a crowded gang hideout rather than the street, since the illegal operation in the Grassrivers has six guards in one room. Use a pistol for the accuracy bonus and chain head shots without leaving the ability. Upgrading the Focus duration at the skill menu makes this much easier. The trophy fires on the fifth kill.",
    37: "You need a plane and an open runway. Steal a Dodo from the flight-school apron, taxi to the active runway and take off without clearance; the tower will scramble two cruisers, but they cannot follow you airborne. A cargo plane at the far hangar works too, though it needs a longer roll. Any successful unauthorised take-off counts. The trophy unlocks as the wheels leave the tarmac.",
    38: "Rhinos are the army's tracked vehicles, and they appear at a five-star wanted level or during the Fort Thompson convoy event. The easier path is the convoy: steal the tank from the flatbed on the highway north of the airbase while it is stopped at the checkpoint, then drive it into the sea before the army responds. Survive the resulting chase and the trophy is yours.",
    39: "Pick the jewellery store on the Vice Beach promenade rather than the downtown branch: it has one guard, a rear service door and no camera in the alley. Go in after midnight, disable the alarm box by the staff entrance, and use a silenced pistol on the single camera. Fill the bag and leave through the back before the patrol returns. Any detection voids the attempt, so quicksave first.",
    40: "Five separate bank vaults, each a small free-roam robbery rather than a story heist. The branches in Port Gellhorn, Ambrosia, Coral Springs and the two in Vice City share a layout: drill the inner door, bag the cash, then exit through the sewer grate in the car park. Buy the thermal drill from the electronics shop to halve the time. Escape without dying and the trophy counts on the fifth getaway.",
    41: "Armoured trucks run scheduled routes along the highway and stop at three depots. The cleanest hit is the bridge approach north of Vice City, where the truck slows to a crawl: block it with a stolen van, shoot the rear escort first, then use the shaped charge on the door. Grab the cash and drive into the storm drain before the second escort arrives. Escape to complete it.",
    42: "Exploration counts districts, not roads: fifty-two named areas across the state, from the Keys to Mount Kalaga. Drive a loop that touches every town, and use the map's fog-of-war layer to spot the gaps; the north-west swamp and the eastern islands are the two everyone misses. Entering an area on foot, by boat or by plane all count. The trophy fires when the last district name appears.",
    43: "Nine gangs run illegal operations, from distilleries and chop shops to grow houses and a counterfeit print works, and you need to hit one of each. They only appear on the map after you photograph a gang stash during a random encounter, so watch for the blue dot. Bring a suppressed weapon: the operations hold four to six guards and a safe that needs drilling. The trophy lands after the ninth robbery.",
    44: "Book a table at the rooftop bar on the south end of Ocean Beach, the one with the neon flamingo, and order the house cocktail from the menu rather than the bar rail. You have to sit at a sea-facing table for the animation to trigger, and it only works after sunset. Bring your partner along if the story still allows it. The trophy pops on the first sip.",
    45: "The vehicle showroom on the Downtown strip has a floor-to-ceiling window and a row of sports cars. Walk in during opening hours, take any car on the floor, and drive straight through the glass instead of reversing out the service lane. A fast car is better than a heavy one: the window breaks either way, but you need speed to clear the forecourt. Lose the police afterwards.",
    46: "Kolt & Associates keeps a two-lane alley in the basement of its Downtown office. You do not need a score, just a full game, so book a lane at the counter, pick the lightest ball and finish ten frames. The lane oil is fast, so aim for the second arrow and keep the throw straight. The trophy registers when the final frame is scored.",
    47: "This is a story beat rather than a task: it triggers during the television interview in Chapter 3 if you let your partner answer the ratings question instead of interrupting. The prompt only appears for a few seconds and the scene does not repeat, so save before the studio mission and reload if you talk over them. The trophy appears at the end of the broadcast.",
    48: "The game tracks every dialogue choice, from story decisions to whether you help a stranger at a bus stop, and the trophy fires on the five-hundredth recorded choice. There is no shortcut: pick an option in every conversation wheel you see, including the small-talk prompts with your partner in the car. Reloading a save does not reset the counter. Progress sits in the stats menu under Choices Made.",
    49: "This one wants a failure followed by a success. The easiest setup is the shooting range: deliberately miss every shot on your first attempt, then score clean on the retry without leaving the menu. Any activity with a retry option works, including fishing, drone racing and even a stunt jump. Do not quit to free roam between the two attempts or the counter resets.",
    50: "A stranger in the Grassrivers hands you a map to a light in the sky, and the encounter only appears during the chapter where the swamp is accessible. Follow the marker north at night, park at the end of the dirt track and walk the last hundred metres, because driving closer scares it off. Look up when the radio cuts out. The trophy lands after the cutscene, and the event never repeats.",
    51: "Any vehicle works, but a motorcycle makes the swing easier to time. Ride alongside a pedestrian on a quiet road, hold the melee button as you pass and clip them with the swing rather than the bike itself; hitting them with the vehicle does not count. The beachfront promenade at night has plenty of slow-moving targets and no traffic. The trophy fires on the first clean hit.",
    52: "Marked bills come from robberies and heists, and they are worthless until laundered. Your contacts take a cut and clean them in batches; the barber in Little Havana, the boat dealer in the Keys and the pawn shop in Port Gellhorn all run laundering fronts. Spread the work across all three so none of them gets heat, and keep robbing stores between batches. The trophy fires on the quarter-million total.",
    53: "Shops means anywhere with a till: clothes, weapons, vehicle mods, property deposits and even hot dogs count. The quickest route is a full upgrade pass on two cars at the customs shop, which clears most of the total in one visit. Property deposits count too, so buying a garage kills two trophies at once. Spending on ammo is slow but reliable. The trophy fires on the hundred-thousandth dollar.",
    54: "There are eight garages for sale, and the expensive ones sit in Vice Beach and Downtown; the cheap ones are in Port Gellhorn, Ambrosia and the Keys. Buy them through the property app on your phone rather than visiting in person, and remember that the two on Mount Kalaga only appear on the list after you finish the ranger strand. Total outlay is roughly $1.4 million. The trophy fires on the eighth purchase.",
    55: "Scooter Bros is the rental app; registering a vehicle means adding any scooter, bike or compact car to your account through the app's garage tab. Buy the cheapest scooter ten times, or register ten different vehicles you already own, since duplicates are allowed as long as each registration is a separate purchase. The app's counter shows progress. The trophy fires on the tenth confirmation.",
}

KIND = {1: "platinum"}
for i in range(2, 14):
    KIND[i] = "story"
for i in (28, 30, 31, 35, 42):
    KIND[i] = "collectibles"
for i in range(14, 56):
    KIND.setdefault(i, "activities")

STAGE = {
    1: 8,
    2: 1, 21: 1, 44: 1, 46: 1, 51: 1,
    3: 2, 8: 2, 48: 2, 49: 2,
    4: 3, 9: 3, 10: 3, 5: 3, 11: 3, 12: 3, 33: 3, 34: 3,
    6: 4, 13: 4, 7: 4,
    22: 5, 23: 5, 24: 5, 25: 5, 26: 5, 27: 5, 20: 5, 29: 5, 47: 5, 50: 5,
    39: 6, 40: 6, 41: 6, 43: 6, 37: 6, 38: 6, 45: 6, 52: 6, 53: 6, 54: 6, 55: 6,
    28: 7, 30: 7, 31: 7, 32: 7, 35: 7, 36: 7, 42: 7, 14: 7, 15: 7, 16: 7, 17: 7, 18: 7, 19: 7,
}

MISSABLE = {
    20: "Cal's contest is only offered during a short window in Kenton's strand; once the strand closes the pier is empty.",
    22: "Andy's strand disappears when Chapter 4 ends: the airport drop-off is his final mission.",
    23: "Kenton's salvage chain closes with the cartel thread at the end of Chapter 3.",
    24: "Billy shuts the shop for good when Chapter 4 begins.",
    25: "Three of the eight strands expire as the story advances; leave them too long and the silver is gone.",
    26: "Randy's gun-running chain is removed after the final heist unlocks.",
    27: "Tyrone's drift strand vanishes when the endgame marker appears.",
    29: "The panther only spawns during Bret's mission; abandoning it ends the strand permanently.",
    33: "Needs your partner following you, which ends once the story splits the crew.",
    34: "The partner ride-along ends after Chapter 3, and all three robberies must happen in one run.",
    47: "A one-off interview prompt in Chapter 3; the scene never repeats.",
    50: "The swamp encounter is chapter-gated and cannot be replayed after the finale.",
}

HIDDEN = {i: True for i in range(2, 14)}

SOURCES_FOR = {
    1: ["psn", "ppyx", "exo"],
    2: ["psn", "ppyx", "ign"],
    3: ["psn", "ign", "wiki"],
    4: ["psn", "ign"],
    5: ["psn", "ppyx"],
    6: ["psn", "ign"],
    7: ["ppyx", "psn", "wiki"],
    8: ["psn", "ign"],
    9: ["psn", "ppyx"],
    10: ["psn", "ign"],
    11: ["psn", "wiki"],
    12: ["psn", "ign"],
    13: ["ppyx", "psn"],
    14: ["ppyx", "psn", "ign"],
    15: ["ppyx", "wiki_act"],
    16: ["wiki_act", "psn"],
    17: ["ppyx", "wiki_act"],
    18: ["wiki_act", "ppyx"],
    19: ["wiki_act", "psn"],
    20: ["psn", "wiki_act"],
    21: ["wiki_act", "psn"],
    22: ["psn", "wiki"],
    23: ["psn", "wiki"],
    24: ["psn", "wiki"],
    25: ["psn", "ign", "wiki"],
    26: ["psn", "wiki"],
    27: ["psn", "wiki"],
    28: ["ppyx_col", "ign_map"],
    29: ["psn", "wiki_act"],
    30: ["ppyx_col", "psn"],
    31: ["ppyx_col", "wiki_act"],
    32: ["wiki_act", "psn"],
    33: ["psn", "ppyx"],
    34: ["psn", "ppyx"],
    35: ["ppyx", "wiki"],
    36: ["psn", "wiki_act"],
    37: ["psn", "wiki"],
    38: ["psn", "wiki"],
    39: ["psn", "ppyx"],
    40: ["psn", "ppyx", "wiki"],
    41: ["psn", "wiki"],
    42: ["ign_map", "ppyx_col"],
    43: ["psn", "wiki_act"],
    44: ["psn", "wiki"],
    45: ["psn", "wiki"],
    46: ["psn", "wiki_act"],
    47: ["psn", "ign"],
    48: ["psn", "ign"],
    49: ["psn", "wiki"],
    50: ["psn", "wiki"],
    51: ["psn", "wiki_act"],
    52: ["psn", "ppyx"],
    53: ["psn", "wiki"],
    54: ["psn", "ppyx"],
    55: ["psn", "wiki_act"],
}

ROADMAP = [
    {"stage": 1, "title": "Arrival: the first night in Vice City",
     "detail": "Gone Fishing, the boardwalk arcade, the Ocean Beach bar, the bowling alley and a melee drive-by are all reachable before the first story marker. Clear them in one pass so the early map is already paying out."},
    {"stage": 2, "title": "Chapter 1: Port Gellhorn and the first score",
     "detail": "Push the chapter, do the two optional prep jobs, and use the quiet stretches to bank the choice and retry trophies. Nothing here can be missed yet."},
    {"stage": 3, "title": "Chapters 2 and 3: cartel money and headlines",
     "detail": "The two partner trophies, Hot Together and Retail Therapy, have to be finished while your partner still rides with you. Do them early in the chapter, before the crew splits."},
    {"stage": 4, "title": "Chapter 4 and the road to the finale",
     "detail": "Save manually before the boardroom marker. Finish every side strand you have opened before the finale unlocks, because this is the last safe point."},
    {"stage": 5, "title": "Side strands before the point of no return",
     "detail": "Ten of the twelve missables live here: Andy, Kenton, Billy, Randy, Tyrone, the eight stranger strands, Bret's hunt, Cal's fishing contest, the interview and the swamp encounter."},
    {"stage": 6, "title": "Heists, robberies and the money game",
     "detail": "Free-roam robberies, the five bank vaults, the armoured truck, the gang operations and the property purchases. Bring a thermal drill and a fast car."},
    {"stage": 7, "title": "Collectibles, exploration and 100% cleanup",
     "detail": "Meditation spots, card sets, WAiNK posts, vehicles, districts, challenges and the 250 stunts. Use the map filters and finish activities before sweeping pickups."},
    {"stage": 8, "title": "The platinum",
     "detail": "Vice Got a Price! registers automatically when the other fifty-four trophies are on your profile. There is no extra step and no way to rush it."},
]


def main() -> None:
    doc = json.loads(DATA.read_text(encoding="utf-8"))
    items = doc["trophies"]
    assert len(items) == 55, len(items)
    assert [t["id"] for t in items] == list(range(1, 56))

    out = []
    for t in items:
        i = t["id"]
        guide = GUIDES[i]
        words = len(guide.split())
        assert 40 <= words <= 110, (i, words)
        entry = {
            "id": i,
            "name": t["name"],
            "description": t["description"],
            "grade": t["grade"],
            "guide": guide,
            "sources": [SOURCES[k] for k in SOURCES_FOR[i]],
            "kind": KIND[i],
            "missable": i in MISSABLE,
            "stage": STAGE[i],
            "hidden": HIDDEN.get(i, False),
        }
        if i in MISSABLE:
            entry["missable_note"] = MISSABLE[i]
        out.append(entry)

    assert len({t["id"] for t in out}) == 55
    assert sum(1 for t in out if t["missable"]) == len(MISSABLE)
    assert len({t["stage"] for t in out}) == 8

    doc["trophies"] = out
    doc["roadmap"] = ROADMAP
    doc["meta"] = {
        "missable_count": sum(1 for t in out if t["missable"]),
        "source_note": (
            "Trophy names and descriptions are the official PlayStation 5 list for Grand Theft Auto VI "
            "(55 trophies, captured 18 November 2026) and are reproduced verbatim. Guides, roadmap, missable "
            "warnings and stage order are original write-ups for this tracker. The linked PSNProfiles, Exophase, "
            "PowerPyx, IGN and GTA Wiki pages are reference reading only: the app renders them as links and never "
            "fetches them."
        ),
    }
    DATA.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", DATA, "trophies:", len(out), "missable:", doc["meta"]["missable_count"])


if __name__ == "__main__":
    main()
