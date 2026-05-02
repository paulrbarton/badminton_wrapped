/**
 * Award type metadata: display names, emoji, descriptions, and value units.
 */
const AWARDS_CONFIG = {
    most_comebacks: {
        emoji: "💪",
        title: "Comeback King",
        description: "Lost game 1 but fought back to win the rubber",
        unit: "comebacks",
    },
    club_stalwart: {
        emoji: "🛡️",
        title: "Club Stalwart",
        description: "Most matches played for the club this season",
        unit: "matches",
    },
    no_mercy: {
        emoji: "🔥",
        title: "No Mercy",
        description: "Largest winning margin in a 2-game rubber",
        unit: "point margin",
        isPartnership: true,
    },
    performs_under_pressure: {
        emoji: "🎯",
        title: "Ice Cold",
        description: "Most games won by exactly 2 points (21-19, 22-20, etc.)",
        unit: "clutch wins",
    },
    longest_winning_streak: {
        emoji: "⚡",
        title: "On Fire",
        description: "Most consecutive rubbers won",
        unit: "consecutive wins",
    },
    defensive_wall: {
        emoji: "🧱",
        title: "Defensive Wall",
        description: "Fewest average points conceded per rubber (min. 10 rubbers)",
        unit: "avg pts conceded",
    },
    giant_killing: {
        emoji: "🗡️",
        title: "Giant Killer",
        description: "Defeated opponents from the highest divisions above their own",
        unit: "divisions higher",
    },
    epic_win: {
        emoji: "🎆",
        title: "Epic Win",
        description: "Most total points scored in a 3-game rubber",
        unit: "total points",
        isPartnership: true,
    },
    clean_sweep_specialist: {
        emoji: "🧹",
        title: "Clean Sweep",
        description: "Most 2-0 rubber wins (min. 3 clean sweeps)",
        unit: "clean sweeps",
    },
    perfect_partnership: {
        emoji: "🤝",
        title: "Perfect Partners",
        description: "Most 2-0 wins together as a pair (min. 5 rubbers)",
        unit: "wins together",
        isPartnership: true,
    },
    home_fortress: {
        emoji: "🏰",
        title: "Home Fortress",
        description: "Most rubbers won at the home venue",
        unit: "home wins",
    },
    most_improved_player: {
        emoji: "📈",
        title: "Most Improved",
        description: "Greatest improvement in win rate across the season",
        unit: "% improvement",
    },
    mvp: {
        emoji: "🏆",
        title: "MVP",
        description: "Composite score: win rate, point diff, clutch performance, participation",
        unit: "MVP score",
    },
};

// Ordered display: individual awards first, then partnership awards
const AWARD_ORDER = [
    "mvp",
    "club_stalwart",
    "longest_winning_streak",
    "most_comebacks",
    "performs_under_pressure",
    "defensive_wall",
    "giant_killing",
    "clean_sweep_specialist",
    "home_fortress",
    "most_improved_player",
    "no_mercy",
    "epic_win",
    "perfect_partnership",
];

/**
 * Get config for an award type, with a sensible fallback for unknown types.
 */
function getAwardConfig(awardType) {
    return AWARDS_CONFIG[awardType] || {
        emoji: "🏅",
        title: awardType.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()),
        description: "",
        unit: "",
    };
}
