function normalizeTeamName(teamName, fieldName) {
    if (typeof teamName !== 'string' || teamName.trim().length === 0) {
        throw new Error(`Field ${fieldName} is required.`);
    }

    return teamName.trim();
}

function normalizeMetricValue(metricValue, fieldName, minimumValue, maximumValue) {
    const parsedMetricValue = Number(metricValue);
    const isMetricValueFinite = Number.isFinite(parsedMetricValue);

    if (!isMetricValueFinite) {
        throw new Error(`Field ${fieldName} must be a valid number.`);
    }

    const isMetricValueOutOfRange = parsedMetricValue < minimumValue || parsedMetricValue > maximumValue;
    if (isMetricValueOutOfRange) {
        throw new Error(`Field ${fieldName} must be between ${minimumValue} and ${maximumValue}.`);
    }

    return parsedMetricValue;
}

export function normalizePredictionRequest(rawRequest, predictionConfig) {
    const hasInvalidRequestPayload = !rawRequest || typeof rawRequest !== 'object';
    if (hasInvalidRequestPayload) {
        throw new Error('Request payload must be an object.');
    }

    const { maxRecentWins, maxRating } = predictionConfig;
    return {
        homeTeamName: normalizeTeamName(rawRequest.homeTeamName, 'homeTeamName'),
        awayTeamName: normalizeTeamName(rawRequest.awayTeamName, 'awayTeamName'),
        homeRecentWins: normalizeMetricValue(rawRequest.homeRecentWins, 'homeRecentWins', 0, maxRecentWins),
        awayRecentWins: normalizeMetricValue(rawRequest.awayRecentWins, 'awayRecentWins', 0, maxRecentWins),
        homeAttackRating: normalizeMetricValue(rawRequest.homeAttackRating, 'homeAttackRating', 0, maxRating),
        awayAttackRating: normalizeMetricValue(rawRequest.awayAttackRating, 'awayAttackRating', 0, maxRating),
        homeDefenseRating: normalizeMetricValue(rawRequest.homeDefenseRating, 'homeDefenseRating', 0, maxRating),
        awayDefenseRating: normalizeMetricValue(rawRequest.awayDefenseRating, 'awayDefenseRating', 0, maxRating),
        homeInjuryImpact: normalizeMetricValue(rawRequest.homeInjuryImpact, 'homeInjuryImpact', 0, maxRating),
        awayInjuryImpact: normalizeMetricValue(rawRequest.awayInjuryImpact, 'awayInjuryImpact', 0, maxRating)
    };
}