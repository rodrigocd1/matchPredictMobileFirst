import predictionConfig from '../config/predictionConfig.js';
import { normalizePredictionRequest } from './predictionRequestValidator.js';

function calculateCompositeScore(teamMetrics, activeConfig) {
    const { scoreWeights, maxRecentWins, maxRating } = activeConfig;
    const normalizedRecentWins = (teamMetrics.recentWins / maxRecentWins) * maxRating;
    const healthScore = maxRating - teamMetrics.injuryImpact;

    return (normalizedRecentWins * scoreWeights.recentWins)
        + (teamMetrics.attackRating * scoreWeights.attackRating)
        + (teamMetrics.defenseRating * scoreWeights.defenseRating)
        + (healthScore * scoreWeights.healthImpact);
}

function roundToTwoDecimals(numericValue) {
    return Number(numericValue.toFixed(2));
}

function calculateProbability(teamScore, scoreTotal) {
    return (teamScore / scoreTotal) * 100;
}

function buildPredictionResult(normalizedRequest, homeScore, awayScore) {
    const scoreTotal = homeScore + awayScore;
    const homeWinProbability = calculateProbability(homeScore, scoreTotal);
    const awayWinProbability = 100 - homeWinProbability;

    return {
        homeTeamName: normalizedRequest.homeTeamName,
        awayTeamName: normalizedRequest.awayTeamName,
        homeWinProbability: roundToTwoDecimals(homeWinProbability),
        awayWinProbability: roundToTwoDecimals(awayWinProbability),
        confidenceScore: roundToTwoDecimals(Math.abs(homeWinProbability - 50) * 2),
        predictedWinner: homeWinProbability >= 50
            ? normalizedRequest.homeTeamName
            : normalizedRequest.awayTeamName
    };
}

export function calculatePrediction(rawRequest, customConfig = predictionConfig) {
    const normalizedRequest = normalizePredictionRequest(rawRequest, customConfig);
    const homeScore = calculateCompositeScore({
        recentWins: normalizedRequest.homeRecentWins,
        attackRating: normalizedRequest.homeAttackRating,
        defenseRating: normalizedRequest.homeDefenseRating,
        injuryImpact: normalizedRequest.homeInjuryImpact
    }, customConfig) + customConfig.homeAdvantageBonus;

    const awayScore = calculateCompositeScore({
        recentWins: normalizedRequest.awayRecentWins,
        attackRating: normalizedRequest.awayAttackRating,
        defenseRating: normalizedRequest.awayDefenseRating,
        injuryImpact: normalizedRequest.awayInjuryImpact
    }, customConfig);

    return buildPredictionResult(normalizedRequest, homeScore, awayScore);
}