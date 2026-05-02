import test from 'node:test';
import assert from 'node:assert/strict';
import { calculatePrediction } from '../src/domain/predictionCalculator.js';

function buildValidRequestPayload() {
    return {
        homeTeamName: 'Blue Club',
        awayTeamName: 'Red Club',
        homeRecentWins: 4,
        awayRecentWins: 2,
        homeAttackRating: 80,
        awayAttackRating: 70,
        homeDefenseRating: 78,
        awayDefenseRating: 67,
        homeInjuryImpact: 15,
        awayInjuryImpact: 22
    };
}

test('calculatePrediction should return normalized probability values', () => {
    const predictionResult = calculatePrediction(buildValidRequestPayload());

    assert.equal(predictionResult.predictedWinner, 'Blue Club');
    assert.equal(predictionResult.homeWinProbability + predictionResult.awayWinProbability, 100);
    assert.ok(predictionResult.confidenceScore > 0);
});

test('calculatePrediction should validate required team names', () => {
    const invalidPayload = buildValidRequestPayload();
    invalidPayload.homeTeamName = '';

    assert.throws(
        () => calculatePrediction(invalidPayload),
        { message: 'Field homeTeamName is required.' }
    );
});

test('calculatePrediction should validate metric ranges', () => {
    const invalidPayload = buildValidRequestPayload();
    invalidPayload.awayDefenseRating = 140;

    assert.throws(
        () => calculatePrediction(invalidPayload),
        { message: 'Field awayDefenseRating must be between 0 and 100.' }
    );
});