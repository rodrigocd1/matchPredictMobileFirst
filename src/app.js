import express from 'express';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { calculatePrediction } from './domain/predictionCalculator.js';

const currentFilePath = fileURLToPath(import.meta.url);
const currentDirectoryPath = path.dirname(currentFilePath);
const publicDirectoryPath = path.resolve(currentDirectoryPath, '../public');

function handlePredictionRequest(request, response, next) {
    try {
        const predictionResult = calculatePrediction(request.body);
        response.status(200).json(predictionResult);
    } catch (error) {
        next(error);
    }
}

function handleNotFound(request, response) {
    response.status(404).json({ message: 'Resource not found.' });
}

function handleApplicationError(error, request, response, next) {
    const hasValidationError = error instanceof Error;
    if (hasValidationError) {
        response.status(400).json({ message: error.message });
        return;
    }

    response.status(500).json({ message: 'Unexpected server error.' });
    next(error);
}

export function createWebApplication() {
    const webApplication = express();
    webApplication.use(express.json({ limit: '100kb' }));
    webApplication.use(express.static(publicDirectoryPath));

    webApplication.get('/api/health', (request, response) => {
        response.status(200).json({ status: 'ok' });
    });

    webApplication.post('/api/predictions', handlePredictionRequest);
    webApplication.use(handleNotFound);
    webApplication.use(handleApplicationError);
    return webApplication;
}