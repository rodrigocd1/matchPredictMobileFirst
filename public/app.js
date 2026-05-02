const matchesListElement = document.querySelector('#matchesList');
const matchSearchInputElement = document.querySelector('#matchSearchInput');
const leagueChipsElement = document.querySelector('#leagueChips');
const analysisOverlayElement = document.querySelector('#analysisOverlay');
const analysisCloseButtonElement = document.querySelector('#analysisCloseButton');
const analysisSubtitleElement = document.querySelector('#analysisSubtitle');
const gamesBaseContainerElement = document.querySelector('#gamesBaseContainer');
const teamSummaryContainerElement = document.querySelector('#teamSummaryContainer');

const teamPalettes = {
    'flamengo': ['#C52613', '#000000'],
    'palmeiras': ['#006437', '#FFFFFF'],
    'real madrid': ['#FEBE10', '#00529F'],
    'barcelona': ['#004D98', '#DB0030'],
    'botafogo': ['#000000', '#FFFFFF'],
    'vasco da gama': ['#000000', '#E2231A'],
    'fluminense': ['#870A28', '#00613C'],
    'sao paulo': ['#FE0000', '#000000'],
    'sao paulo fc': ['#FE0000', '#000000'],
    'atletico madrid': ['#272E61', '#CB3524'],
    'athletic bilbao': ['#EE2523', '#FFFFFF'],
    'valencia': ['#FFDF1C', '#EE3524'],
    'valencia cf': ['#FFDF1C', '#EE3524'],
    'sevilla': ['#F43333', '#FFFFFF'],
    'sevilla fc': ['#F43333', '#FFFFFF'],
    'villarreal': ['#FFE667', '#005187'],
    'villarreal cf': ['#FFE667', '#005187'],
    'real sociedad': ['#0067B1', '#E4B630'],
    'gremio': ['#0D80BF', '#000000'],
    'cruzeiro': ['#2F529E', '#FFFFFF'],
    'corinthians': ['#000000', '#FFFFFF'],
    'atletico mineiro': ['#FFD503', '#000000'],
    'bahia': ['#006CB5', '#ED3237'],
    'athletico paranaense': ['#CE181E', '#010101'],
    'atletico paranaense': ['#CE181E', '#010101'],
    'real betis': ['#0BB363', '#E7A614'],
    'celta vigo': ['#8AC3EE', '#E5254E'],
    'osasuna': ['#0A346F', '#D91A21'],
    'getafe': ['#005999', '#C43A2F']
};

const matchFixtures = [
    {
        id: 'br-01',
        league: 'Brasileirao',
        date: '01/05/2026',
        time: '16:00',
        homeTeamName: 'Flamengo',
        awayTeamName: 'Palmeiras',
        metrics: {
            homeRecentWins: 4,
            awayRecentWins: 3,
            homeAttackRating: 77,
            awayAttackRating: 74,
            homeDefenseRating: 70,
            awayDefenseRating: 72,
            homeInjuryImpact: 22,
            awayInjuryImpact: 20
        }
    },
    {
        id: 'es-01',
        league: 'La Liga',
        date: '02/05/2026',
        time: '17:00',
        homeTeamName: 'Real Madrid',
        awayTeamName: 'Barcelona',
        metrics: {
            homeRecentWins: 4,
            awayRecentWins: 4,
            homeAttackRating: 79,
            awayAttackRating: 78,
            homeDefenseRating: 73,
            awayDefenseRating: 71,
            homeInjuryImpact: 16,
            awayInjuryImpact: 19
        }
    },
    {
        id: 'br-02',
        league: 'Brasileirao',
        date: '03/05/2026',
        time: '19:00',
        homeTeamName: 'Botafogo',
        awayTeamName: 'Fluminense',
        metrics: {
            homeRecentWins: 3,
            awayRecentWins: 3,
            homeAttackRating: 68,
            awayAttackRating: 69,
            homeDefenseRating: 71,
            awayDefenseRating: 67,
            homeInjuryImpact: 24,
            awayInjuryImpact: 23
        }
    },
    {
        id: 'br-03',
        league: 'Brasileirao',
        date: '04/05/2026',
        time: '20:30',
        homeTeamName: 'Sao Paulo',
        awayTeamName: 'Corinthians',
        metrics: {
            homeRecentWins: 2,
            awayRecentWins: 2,
            homeAttackRating: 67,
            awayAttackRating: 65,
            homeDefenseRating: 72,
            awayDefenseRating: 69,
            homeInjuryImpact: 27,
            awayInjuryImpact: 25
        }
    },
    {
        id: 'br-04',
        league: 'Brasileirao',
        date: '05/05/2026',
        time: '21:00',
        homeTeamName: 'Atletico Mineiro',
        awayTeamName: 'Cruzeiro',
        metrics: {
            homeRecentWins: 3,
            awayRecentWins: 4,
            homeAttackRating: 70,
            awayAttackRating: 73,
            homeDefenseRating: 70,
            awayDefenseRating: 71,
            homeInjuryImpact: 21,
            awayInjuryImpact: 19
        }
    },
    {
        id: 'es-02',
        league: 'La Liga',
        date: '06/05/2026',
        time: '16:15',
        homeTeamName: 'Atletico Madrid',
        awayTeamName: 'Sevilla',
        metrics: {
            homeRecentWins: 3,
            awayRecentWins: 2,
            homeAttackRating: 73,
            awayAttackRating: 66,
            homeDefenseRating: 76,
            awayDefenseRating: 68,
            homeInjuryImpact: 18,
            awayInjuryImpact: 29
        }
    },
    {
        id: 'es-03',
        league: 'La Liga',
        date: '07/05/2026',
        time: '17:30',
        homeTeamName: 'Athletic Bilbao',
        awayTeamName: 'Valencia',
        metrics: {
            homeRecentWins: 2,
            awayRecentWins: 2,
            homeAttackRating: 67,
            awayAttackRating: 64,
            homeDefenseRating: 70,
            awayDefenseRating: 66,
            homeInjuryImpact: 25,
            awayInjuryImpact: 23
        }
    },
    {
        id: 'es-04',
        league: 'La Liga',
        date: '08/05/2026',
        time: '18:00',
        homeTeamName: 'Real Sociedad',
        awayTeamName: 'Villarreal',
        metrics: {
            homeRecentWins: 3,
            awayRecentWins: 2,
            homeAttackRating: 72,
            awayAttackRating: 69,
            homeDefenseRating: 70,
            awayDefenseRating: 67,
            homeInjuryImpact: 20,
            awayInjuryImpact: 21
        }
    },
    {
        id: 'br-05',
        league: 'Brasileirao',
        date: '09/05/2026',
        time: '16:00',
        homeTeamName: 'Bahia',
        awayTeamName: 'Athletico Paranaense',
        metrics: {
            homeRecentWins: 2,
            awayRecentWins: 3,
            homeAttackRating: 63,
            awayAttackRating: 67,
            homeDefenseRating: 65,
            awayDefenseRating: 68,
            homeInjuryImpact: 28,
            awayInjuryImpact: 22
        }
    },
    {
        id: 'br-06',
        league: 'Brasileirao',
        date: '10/05/2026',
        time: '18:30',
        homeTeamName: 'Gremio',
        awayTeamName: 'Vasco da Gama',
        metrics: {
            homeRecentWins: 3,
            awayRecentWins: 1,
            homeAttackRating: 68,
            awayAttackRating: 61,
            homeDefenseRating: 72,
            awayDefenseRating: 64,
            homeInjuryImpact: 21,
            awayInjuryImpact: 30
        }
    },
    {
        id: 'es-05',
        league: 'La Liga',
        date: '10/05/2026',
        time: '21:15',
        homeTeamName: 'Real Betis',
        awayTeamName: 'Getafe',
        metrics: {
            homeRecentWins: 3,
            awayRecentWins: 1,
            homeAttackRating: 71,
            awayAttackRating: 60,
            homeDefenseRating: 69,
            awayDefenseRating: 63,
            homeInjuryImpact: 22,
            awayInjuryImpact: 31
        }
    }
];

const availableLeagues = ['Todos', ...new Set(matchFixtures.map((match) => match.league))];
const predictionsByMatchId = new Map();

let selectedLeague = 'Todos';
let activeSearchText = '';
let hasFinishedLoading = false;
let isLoadingPredictions = false;
let activePredictionLoadPromise = null;
let activeAnalysisMatchId = null;
const predictionRequestTimeoutInMs = 8000;

function normalizeText(text) {
    return text
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .trim();
}

function escapeHtml(unsafeText) {
    return String(unsafeText)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

function blendWithWhite(hexColor, blendRatio = 0.45) {
    const red = Number.parseInt(hexColor.slice(1, 3), 16);
    const green = Number.parseInt(hexColor.slice(3, 5), 16);
    const blue = Number.parseInt(hexColor.slice(5, 7), 16);

    const mixedRed = Math.round(red + (255 - red) * blendRatio);
    const mixedGreen = Math.round(green + (255 - green) * blendRatio);
    const mixedBlue = Math.round(blue + (255 - blue) * blendRatio);

    return `rgb(${mixedRed}, ${mixedGreen}, ${mixedBlue})`;
}

function clamp(value, minimum, maximum) {
    return Math.min(Math.max(value, minimum), maximum);
}

function getTeamPalette(teamName) {
    const normalizedTeamName = normalizeText(teamName);
    const fallbackPalette = ['#6376A6', '#C7D2E9'];

    return teamPalettes[normalizedTeamName] || fallbackPalette;
}

function calculateThreeWayProbabilities(homeWinProbability, confidenceScore) {
    const drawProbability = clamp(34 - (confidenceScore * 0.22), 18, 33);
    const remainingProbability = 100 - drawProbability;

    const homeProbability = Math.round((homeWinProbability / 100) * remainingProbability);
    const drawRounded = Math.round(drawProbability);
    const awayProbability = 100 - homeProbability - drawRounded;

    return {
        home: clamp(homeProbability, 0, 100),
        draw: clamp(drawRounded, 0, 100),
        away: clamp(awayProbability, 0, 100)
    };
}

function classifyRisk(confidenceScore) {
    if (confidenceScore >= 65) {
        return { label: 'Alta', tone: 'high' };
    }

    if (confidenceScore >= 40) {
        return { label: 'Media', tone: 'medium' };
    }

    return { label: 'Baixa', tone: 'low' };
}

function getGainPotential(prediction) {
    if (!prediction) {
        return 0;
    }

    if (prediction.predictedWinner === prediction.homeTeamName) {
        return prediction.probabilities.home;
    }

    return prediction.probabilities.away;
}

function formatPercentage(value) {
    return `${Math.round(value)}%`;
}

async function fetchPredictionForMatch(match) {
    const requestBody = {
        homeTeamName: match.homeTeamName,
        awayTeamName: match.awayTeamName,
        homeRecentWins: match.metrics.homeRecentWins,
        awayRecentWins: match.metrics.awayRecentWins,
        homeAttackRating: match.metrics.homeAttackRating,
        awayAttackRating: match.metrics.awayAttackRating,
        homeDefenseRating: match.metrics.homeDefenseRating,
        awayDefenseRating: match.metrics.awayDefenseRating,
        homeInjuryImpact: match.metrics.homeInjuryImpact,
        awayInjuryImpact: match.metrics.awayInjuryImpact
    };

    const abortController = new AbortController();
    const requestTimeoutId = setTimeout(() => {
        abortController.abort();
    }, predictionRequestTimeoutInMs);

    let response;
    try {
        response = await fetch('/api/predictions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody),
            signal: abortController.signal
        });
    } finally {
        clearTimeout(requestTimeoutId);
    }

    const responseBody = await response.json();
    if (!response.ok) {
        throw new Error(responseBody.message || 'Falha ao calcular previsao.');
    }

    const confidence = Number(responseBody.confidenceScore) || 0;
    const homeWinProbability = Number(responseBody.homeWinProbability) || 0;
    const awayWinProbability = Number(responseBody.awayWinProbability) || 0;
    const threeWay = calculateThreeWayProbabilities(homeWinProbability, confidence);
    const risk = classifyRisk(confidence);

    return {
        confidence,
        homeTeamName: responseBody.homeTeamName || match.homeTeamName,
        awayTeamName: responseBody.awayTeamName || match.awayTeamName,
        homeWinProbability,
        awayWinProbability,
        predictedWinner: responseBody.predictedWinner || match.homeTeamName,
        risk,
        probabilities: threeWay
    };
}

function renderLeagueChips() {
    leagueChipsElement.innerHTML = '';

    availableLeagues.forEach((leagueName) => {
        const chipElement = document.createElement('button');
        chipElement.type = 'button';
        chipElement.className = `chip${leagueName === selectedLeague ? ' active' : ''}`;
        chipElement.textContent = leagueName;
        chipElement.addEventListener('click', () => {
            selectedLeague = leagueName;
            renderLeagueChips();
            renderMatches();
        });

        leagueChipsElement.appendChild(chipElement);
    });
}

function getFilteredMatches() {
    const normalizedSearch = normalizeText(activeSearchText);

    return matchFixtures.filter((match) => {
        const leagueMatches = selectedLeague === 'Todos' || match.league === selectedLeague;
        if (!leagueMatches) {
            return false;
        }

        if (!normalizedSearch) {
            return true;
        }

        const searchableText = normalizeText([
            match.homeTeamName,
            match.awayTeamName,
            match.league,
            match.date
        ].join(' '));

        return searchableText.includes(normalizedSearch);
    });
}

function buildCardMarkup(match) {
    const prediction = predictionsByMatchId.get(match.id);

    const homePalette = getTeamPalette(match.homeTeamName);
    const awayPalette = getTeamPalette(match.awayTeamName);

    const homePrimary = homePalette[0];
    const homeSecondary = homePalette[1] || '#FFFFFF';
    const awayPrimary = awayPalette[0];
    const awaySecondary = awayPalette[1] || '#FFFFFF';

    const riskLabel = prediction ? prediction.risk.label : '...';
    const riskTone = prediction ? prediction.risk.tone : 'medium';

    const homeProbability = prediction ? `${prediction.probabilities.home}%` : '--';
    const drawProbability = prediction ? `${prediction.probabilities.draw}%` : '--';
    const awayProbability = prediction ? `${prediction.probabilities.away}%` : '--';

    return `
        <article class="match-card" data-match-id="${match.id}">
            <div class="meta-row">
                <div class="meta-line">
                    <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4.5" width="18" height="16" rx="2"></rect><path d="M16 3v3M8 3v3M3 9.5h18"></path></svg>
                    <span>${match.date}</span>
                    <span>&bull;</span>
                    <span>${match.time}</span>
                </div>
                <span class="risk-pill ${riskTone}">${riskLabel}</span>
            </div>

            <div class="league-line">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s7-5.2 7-11a7 7 0 1 0-14 0c0 5.8 7 11 7 11Z"></path><circle cx="12" cy="10" r="2.25"></circle></svg>
                <span>${match.league}</span>
            </div>

            <div class="clubs-row">
                <div class="club-side home">
                    <span class="color-pair" aria-hidden="true">
                        <span class="team-dot" style="--dot-color:${homePrimary};--dot-light:${blendWithWhite(homePrimary)}"></span>
                        <span class="team-dot" style="--dot-color:${homeSecondary};--dot-light:${blendWithWhite(homeSecondary)}"></span>
                    </span>
                    <span class="club-name">${match.homeTeamName}</span>
                </div>

                <span class="vs-label">VS</span>

                <div class="club-side away">
                    <span class="club-name">${match.awayTeamName}</span>
                    <span class="color-pair" aria-hidden="true">
                        <span class="team-dot" style="--dot-color:${awayPrimary};--dot-light:${blendWithWhite(awayPrimary)}"></span>
                        <span class="team-dot" style="--dot-color:${awaySecondary};--dot-light:${blendWithWhite(awaySecondary)}"></span>
                    </span>
                </div>
            </div>

            <div class="prediction-grid">
                <div class="prediction-box">
                    <div class="prediction-value">${homeProbability}</div>
                    <div class="prediction-label">Casa</div>
                </div>
                <div class="prediction-box draw">
                    <div class="prediction-value">${drawProbability}</div>
                    <div class="prediction-label">Empate</div>
                </div>
                <div class="prediction-box">
                    <div class="prediction-value">${awayProbability}</div>
                    <div class="prediction-label">Fora</div>
                </div>
            </div>

            <button class="full-analysis" type="button">Ver analise completa</button>
        </article>
    `;
}

function renderMatches() {
    const filteredMatches = getFilteredMatches();

    if (!hasFinishedLoading) {
        matchesListElement.innerHTML = '<div class="loading-state">Calculando previsoes das partidas...</div>';
        return;
    }

    if (filteredMatches.length === 0) {
        matchesListElement.innerHTML = '<div class="empty-state">Nenhuma partida encontrada para este filtro.</div>';
        return;
    }

    matchesListElement.innerHTML = filteredMatches.map((match) => buildCardMarkup(match)).join('');
}

function renderGamesBase(matchId) {
    return matchFixtures.map((match) => {
        const prediction = predictionsByMatchId.get(match.id);
        const isSelectedMatch = match.id === matchId;

        if (!prediction) {
            return `
                <article class="analysis-item${isSelectedMatch ? ' selected-match' : ''}">
                    <div class="analysis-line">
                        <span class="analysis-label">${escapeHtml(match.homeTeamName)} x ${escapeHtml(match.awayTeamName)}</span>
                        <span class="analysis-value">${escapeHtml(match.league)}</span>
                    </div>
                    <div class="analysis-line">
                        <span class="analysis-label">Resultado da API</span>
                        <span class="analysis-value">Indisponivel</span>
                    </div>
                </article>
            `;
        }

        const gainPotential = getGainPotential(prediction);

        return `
            <article class="analysis-item${isSelectedMatch ? ' selected-match' : ''}">
                <div class="analysis-line">
                    <span class="analysis-label">${escapeHtml(match.homeTeamName)} x ${escapeHtml(match.awayTeamName)}</span>
                    <span class="analysis-value">${escapeHtml(match.date)} ${escapeHtml(match.time)}</span>
                </div>
                <div class="analysis-line">
                    <span class="analysis-label">Resultado previsto</span>
                    <span class="analysis-value">${escapeHtml(prediction.predictedWinner)}</span>
                </div>
                <div class="analysis-line">
                    <span class="analysis-label">Ganho potencial</span>
                    <span class="analysis-value emphasis">${formatPercentage(gainPotential)}</span>
                </div>
            </article>
        `;
    }).join('');
}

function computeGroupedTeamSummary() {
    const groupedByTeam = new Map();

    const addTeamEntry = (teamName, teamProbability, wonPrediction, confidence) => {
        const existingTeam = groupedByTeam.get(teamName) || {
            teamName,
            games: 0,
            predictedWins: 0,
            totalGain: 0,
            totalConfidence: 0
        };

        existingTeam.games += 1;
        existingTeam.predictedWins += wonPrediction ? 1 : 0;
        existingTeam.totalGain += teamProbability;
        existingTeam.totalConfidence += confidence;

        groupedByTeam.set(teamName, existingTeam);
    };

    matchFixtures.forEach((match) => {
        const prediction = predictionsByMatchId.get(match.id);
        if (!prediction) {
            return;
        }

        addTeamEntry(
            match.homeTeamName,
            prediction.probabilities.home,
            prediction.predictedWinner === match.homeTeamName,
            prediction.confidence
        );

        addTeamEntry(
            match.awayTeamName,
            prediction.probabilities.away,
            prediction.predictedWinner === match.awayTeamName,
            prediction.confidence
        );
    });

    return [...groupedByTeam.values()]
        .map((teamSummary) => {
            const averageGain = teamSummary.totalGain / teamSummary.games;
            const averageConfidence = teamSummary.totalConfidence / teamSummary.games;

            return {
                ...teamSummary,
                averageGain,
                averageConfidence
            };
        })
        .sort((teamA, teamB) => teamB.averageGain - teamA.averageGain);
}

function renderTeamSummary() {
    const groupedSummary = computeGroupedTeamSummary();
    if (groupedSummary.length === 0) {
        return `
            <article class="analysis-item">
                <div class="analysis-line">
                    <span class="analysis-label">Sem base da API para agrupar times.</span>
                    <span class="analysis-value">--</span>
                </div>
            </article>
        `;
    }

    return groupedSummary.map((teamSummary, index) => `
        <article class="analysis-item${index < 3 ? ' top-team' : ''}">
            <div class="analysis-line">
                <span class="analysis-label">Time</span>
                <span class="analysis-value">${escapeHtml(teamSummary.teamName)}</span>
            </div>
            <div class="analysis-line">
                <span class="analysis-label">Jogos na base</span>
                <span class="analysis-value">${teamSummary.games}</span>
            </div>
            <div class="analysis-line">
                <span class="analysis-label">Resultados previstos favoraveis</span>
                <span class="analysis-value">${teamSummary.predictedWins}</span>
            </div>
            <div class="analysis-line">
                <span class="analysis-label">Media de ganho</span>
                <span class="analysis-value emphasis">${formatPercentage(teamSummary.averageGain)}</span>
            </div>
            <div class="analysis-line">
                <span class="analysis-label">Media de confianca</span>
                <span class="analysis-value">${formatPercentage(teamSummary.averageConfidence)}</span>
            </div>
        </article>
    `).join('');
}

function renderAnalysisContent(matchId) {
    const selectedMatch = matchFixtures.find((match) => match.id === matchId);
    const generatedAt = new Date().toLocaleString('pt-BR');

    if (selectedMatch) {
        analysisSubtitleElement.textContent = `Analise iniciada por ${selectedMatch.homeTeamName} x ${selectedMatch.awayTeamName} | Base atualizada em ${generatedAt}`;
    } else {
        analysisSubtitleElement.textContent = `Base atualizada em ${generatedAt}`;
    }

    gamesBaseContainerElement.innerHTML = renderGamesBase(matchId);
    teamSummaryContainerElement.innerHTML = renderTeamSummary();
}

function showAnalysisLoadingState() {
    analysisSubtitleElement.textContent = 'Consultando API para atualizar toda a base de jogos...';
    gamesBaseContainerElement.innerHTML = '<div class="loading-state">Atualizando jogos e resultados...</div>';
    teamSummaryContainerElement.innerHTML = '<div class="loading-state">Agrupando dados por time...</div>';
}

function openAnalysisOverlay(matchId) {
    activeAnalysisMatchId = matchId;
    analysisOverlayElement.hidden = false;
    document.body.style.overflow = 'hidden';

    if (predictionsByMatchId.size > 0) {
        renderAnalysisContent(matchId);
    } else {
        showAnalysisLoadingState();
    }

    loadPredictions(true)
        .then(() => {
            if (!analysisOverlayElement.hidden && activeAnalysisMatchId === matchId) {
                renderAnalysisContent(matchId);
            }
        })
        .catch(() => {
            if (!analysisOverlayElement.hidden && activeAnalysisMatchId === matchId) {
                renderAnalysisContent(matchId);
            }
        });
}

function closeAnalysisOverlay() {
    analysisOverlayElement.hidden = true;
    document.body.style.overflow = '';
    activeAnalysisMatchId = null;
}

async function loadPredictions(forceRefresh = false) {
    if (!forceRefresh && hasFinishedLoading && predictionsByMatchId.size === matchFixtures.length) {
        return;
    }

    if (isLoadingPredictions) {
        return activePredictionLoadPromise;
    }

    isLoadingPredictions = true;

    activePredictionLoadPromise = (async () => {
        if (forceRefresh) {
            predictionsByMatchId.clear();
        }

        const predictionPromises = matchFixtures.map(async (match) => {
            try {
                const prediction = await fetchPredictionForMatch(match);
                predictionsByMatchId.set(match.id, prediction);
            } catch {
                predictionsByMatchId.set(match.id, null);
            }
        });

        await Promise.all(predictionPromises);
        hasFinishedLoading = true;
        renderMatches();

        if (!analysisOverlayElement.hidden && activeAnalysisMatchId) {
            renderAnalysisContent(activeAnalysisMatchId);
        }
    })()
        .catch(() => {
            hasFinishedLoading = true;
            renderMatches();

            if (!analysisOverlayElement.hidden && activeAnalysisMatchId) {
                renderAnalysisContent(activeAnalysisMatchId);
            }
        })
        .finally(() => {
            isLoadingPredictions = false;
            activePredictionLoadPromise = null;
        });

    return activePredictionLoadPromise;
}

function initializeSearch() {
    matchSearchInputElement.addEventListener('input', (inputEvent) => {
        activeSearchText = inputEvent.target.value;
        renderMatches();
    });
}

function initializeAnalysisInteractions() {
    matchesListElement.addEventListener('click', (clickEvent) => {
        const analysisButtonElement = clickEvent.target.closest('.full-analysis');
        if (!analysisButtonElement) {
            return;
        }

        const matchCardElement = analysisButtonElement.closest('.match-card');
        const matchId = matchCardElement ? matchCardElement.dataset.matchId : null;

        if (!matchId) {
            return;
        }

        openAnalysisOverlay(matchId);
    });

    analysisCloseButtonElement.addEventListener('click', closeAnalysisOverlay);

    analysisOverlayElement.addEventListener('click', (clickEvent) => {
        if (clickEvent.target === analysisOverlayElement) {
            closeAnalysisOverlay();
        }
    });

    document.addEventListener('keydown', (keyboardEvent) => {
        if (keyboardEvent.key === 'Escape' && !analysisOverlayElement.hidden) {
            closeAnalysisOverlay();
        }
    });
}

function initialize() {
    renderLeagueChips();
    renderMatches();
    initializeSearch();
    initializeAnalysisInteractions();
    loadPredictions();
}

initialize();

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js').catch(() => {
        // intentionally ignored
    });
}
