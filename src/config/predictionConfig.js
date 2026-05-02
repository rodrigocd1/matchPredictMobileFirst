const predictionConfig = Object.freeze({
    maxRecentWins: 5,
    maxRating: 100,
    homeAdvantageBonus: 5,
    scoreWeights: Object.freeze({
        recentWins: 0.25,
        attackRating: 0.3,
        defenseRating: 0.25,
        healthImpact: 0.2
    })
});

export default predictionConfig;